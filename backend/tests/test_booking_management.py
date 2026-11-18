import asyncio
import uuid
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.base_entities import Booking, Pitch, User, Venue
from app.models.enums import BookingStatus, SurfaceType, UserRole


pytestmark = pytest.mark.asyncio
BOOKINGS = "/api/v1/bookings"
MATCHES = "/api/v1/matches"
TODAY = datetime.now(timezone.utc).date()


@pytest.fixture
async def reservation_pitch(db_session: AsyncSession):
    roles = [UserRole.VENUE_OWNER, UserRole.PLAYER, UserRole.PLAYER, UserRole.PLAYER]
    users = [
        User(
            email=f"reservation_{uuid.uuid4().hex}@test.com",
            hashed_password="unused-in-this-test",
            full_name=f"Reservation User {index}",
            phone="+40700112233",
            role=role,
        )
        for index, role in enumerate(roles)
    ]
    db_session.add_all(users)
    await db_session.flush()

    venue = Venue(
        owner_id=users[0].id,
        name="Reservation Test Venue",
        address="Strada Sportului 1",
        city="Timisoara",
        phone="+40700112233",
        latitude=Decimal("45.7537"),
        longitude=Decimal("21.2257"),
        opening_hour=8,
        closing_hour=23,
    )
    db_session.add(venue)
    await db_session.flush()

    pitch = Pitch(
        venue_id=venue.id,
        name="Reservation Test Pitch",
        surface_type=SurfaceType.SYNTHETIC_3G,
        team_size_capacity=5,
        hourly_rate=Decimal("120.00"),
        is_active=True,
    )
    db_session.add(pitch)
    await db_session.commit()
    headers = [{"Authorization": f"Bearer {create_access_token(subject=str(user.id))}"} for user in users]
    return pitch.id, headers


def _time(hour: int, minute: int = 0, *, days: int = 3) -> datetime:
    day = TODAY + timedelta(days=days)
    return datetime.combine(day, time(hour, minute), tzinfo=timezone.utc)


async def _book(
    client: AsyncClient,
    pitch_id: uuid.UUID,
    headers: dict[str, str],
    start: datetime,
    *,
    hours: int = 1,
    lobby_capacity: int | None = None,
) -> dict:
    payload = {
        "pitch_id": str(pitch_id),
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(hours=hours)).isoformat(),
    }
    if lobby_capacity is not None:
        payload.update(create_open_lobby=True, target_players=lobby_capacity)
    response = await client.post(BOOKINGS, headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def _join(client: AsyncClient, match_path: str, headers: dict[str, str]):
    return await client.post(
        f"{match_path}/join",
        headers=headers,
        json={"team_side": "B", "role": "PLAYER"},
    )


def _roster(match: dict) -> dict:
    return {participant["id"]: participant for participant in match["participants"]}


async def _slots(
    client: AsyncClient, path: str, start: datetime, headers: dict[str, str] | None = None
) -> dict[int, dict]:
    response = await client.get(path, headers=headers, params={"target_date": start.date().isoformat()})
    assert response.status_code == 200, response.text
    return {datetime.fromisoformat(slot["start_time"]).hour: slot for slot in response.json()}


async def test_booker_can_move_time_without_changing_duration_price_or_roster(
    client: AsyncClient, reservation_pitch
) -> None:
    pitch_id, (_, booker, participant, _) = reservation_pitch
    original_start = _time(18)
    booking = await _book(client, pitch_id, booker, original_start, hours=2, lobby_capacity=2)
    booking_path = f"{BOOKINGS}/{booking['id']}"
    match_path = f"{MATCHES}/{booking['open_match_id']}"
    joined = await _join(client, match_path, participant)
    assert joined.status_code == 200, joined.text
    assert joined.json()["status"] == "FULL"

    # The new interval overlaps the booking's own old interval by one hour.
    new_start = original_start + timedelta(hours=1)
    requested_start = new_start.astimezone(timezone(timedelta(hours=2)))
    response = await client.patch(
        booking_path, headers=booker, json={"start_time": requested_start.isoformat()}
    )
    assert response.status_code == 200, response.text
    moved = response.json()
    for field in ("id", "pitch_id", "total_price", "status", "created_at", "open_match_id"):
        assert moved[field] == booking[field], field
    assert datetime.fromisoformat(moved["start_time"]) == new_start
    assert datetime.fromisoformat(moved["end_time"]) == new_start + timedelta(hours=2)
    assert datetime.fromisoformat(moved["match"]["scheduled_at"]) == new_start
    assert moved["match"]["status"] == "FULL"
    assert _roster(moved["match"]) == _roster(joined.json())

    match = await client.get(match_path)
    assert match.status_code == 200, match.text
    assert datetime.fromisoformat(match.json()["scheduled_at"]) == new_start
    assert _roster(match.json()) == _roster(joined.json())
    slots = await _slots(client, f"/api/v1/pitches/{pitch_id}/availability", original_start)
    assert [slots[hour]["status"] for hour in (18, 19, 20, 21)] == [
        "AVAILABLE", "OCCUPIED", "OCCUPIED", "AVAILABLE",
    ]


async def test_only_booker_can_manage_reservation_and_see_its_excluded_availability(
    client: AsyncClient, reservation_pitch
) -> None:
    pitch_id, (venue_owner, booker, other, _) = reservation_pitch
    original_start = _time(17, 30)
    booking = await _book(client, pitch_id, booker, original_start, hours=2)
    await _book(client, pitch_id, other, _time(19, 30))
    booking_path = f"{BOOKINGS}/{booking['id']}"
    availability_path = f"{booking_path}/availability"
    params = {"target_date": original_start.date().isoformat()}
    new_start = {"start_time": _time(21).isoformat()}

    for headers, expected in ((None, 401), (other, 403), (venue_owner, 403)):
        responses = (
            await client.get(availability_path, headers=headers, params=params),
            await client.patch(booking_path, headers=headers, json=new_start),
            await client.delete(booking_path, headers=headers),
        )
        assert [response.status_code for response in responses] == [expected] * 3

    scoped_slots = await _slots(client, availability_path, original_start, booker)
    assert [scoped_slots[hour]["status"] for hour in (17, 18, 19, 20)] == [
        "AVAILABLE", "AVAILABLE", "OCCUPIED", "OCCUPIED",
    ]
    public_slots = await _slots(client, f"/api/v1/pitches/{pitch_id}/availability", original_start)
    assert [public_slots[hour]["status"] for hour in (17, 18, 19, 20)] == ["OCCUPIED"] * 4
    current = await client.get(booking_path, headers=booker)
    assert current.status_code == 200, current.text
    assert current.json() == booking


async def test_rejected_move_preserves_the_original_booking_and_lobby(
    client: AsyncClient, reservation_pitch
) -> None:
    pitch_id, (_, booker, other, _) = reservation_pitch
    original_start = _time(17)
    booking = await _book(client, pitch_id, booker, original_start, hours=2, lobby_capacity=4)
    await _book(client, pitch_id, other, _time(21))
    path = f"{BOOKINGS}/{booking['id']}"

    for request_start, expected_status in ((_time(20), 409), (_time(22), 400), (_time(17, days=-1), 400)):
        response = await client.patch(
            path, headers=booker, json={"start_time": request_start.isoformat()}
        )
        assert response.status_code == expected_status, response.text

    current = await client.get(path, headers=booker)
    assert current.status_code == 200, current.text
    assert current.json() == booking
    public_slots = await _slots(client, f"/api/v1/pitches/{pitch_id}/availability", original_start)
    assert public_slots[17]["open_match_id"] == booking["open_match_id"]
    assert public_slots[18]["open_match_id"] == booking["open_match_id"]
    assert public_slots[20]["status"] == "AVAILABLE"
    assert public_slots[21]["status"] == "OCCUPIED"


async def test_cancellation_releases_slot_and_keeps_booking_and_match_history(
    client: AsyncClient, reservation_pitch
) -> None:
    pitch_id, (_, booker, participant, other) = reservation_pitch
    start = _time(17)
    booking = await _book(client, pitch_id, booker, start, lobby_capacity=3)
    path = f"{BOOKINGS}/{booking['id']}"
    match_path = f"{MATCHES}/{booking['open_match_id']}"
    joined = await _join(client, match_path, participant)
    assert joined.status_code == 200, joined.text

    cancelled = await client.delete(path, headers=booker)
    assert cancelled.status_code == 200, cancelled.text
    history_item = cancelled.json()
    assert history_item["status"] == "CANCELLED"
    assert history_item["id"] == booking["id"]
    assert history_item["match"]["status"] == "CANCELLED"
    assert _roster(history_item["match"]) == _roster(joined.json())

    available = await _slots(client, f"/api/v1/pitches/{pitch_id}/availability", start)
    assert available[17]["status"] == "AVAILABLE"
    matches = await client.get(MATCHES)
    assert matches.status_code == 200, matches.text
    assert booking["open_match_id"] not in {match["id"] for match in matches.json()}
    rejected_join = await _join(client, match_path, other)
    assert rejected_join.status_code == 409, rejected_join.text

    replacement = await _book(client, pitch_id, other, start)
    assert replacement["id"] != booking["id"]
    repeated = await client.delete(path, headers=booker)
    assert repeated.status_code == 200, repeated.text
    assert repeated.json() == history_item
    replacement_current = await client.get(f"{BOOKINGS}/{replacement['id']}", headers=other)
    assert replacement_current.status_code == 200, replacement_current.text
    assert replacement_current.json()["status"] == "CONFIRMED"
    history = await client.get(f"{BOOKINGS}/me", headers=booker)
    assert history.status_code == 200, history.text
    assert history.json() == [history_item]
    rejected_move = await client.patch(
        path, headers=booker, json={"start_time": _time(19).isoformat()}
    )
    assert rejected_move.status_code == 409, rejected_move.text
    rejected_availability = await client.get(
        f"{path}/availability", headers=booker, params={"target_date": start.date().isoformat()}
    )
    assert rejected_availability.status_code == 409, rejected_availability.text


async def test_started_reservation_cannot_be_managed(
    client: AsyncClient, db_session: AsyncSession, reservation_pitch
) -> None:
    pitch_id, (_, booker, _, _) = reservation_pitch
    original = await _book(client, pitch_id, booker, _time(10))
    booking = await db_session.get(Booking, uuid.UUID(original["id"]))
    assert booking is not None
    past_start = _time(12, days=-1)
    booking.start_time = past_start
    booking.end_time = past_start + timedelta(hours=1)
    await db_session.commit()
    path = f"{BOOKINGS}/{original['id']}"
    new_start = _time(15)

    responses = (
        await client.patch(path, headers=booker, json={"start_time": new_start.isoformat()}),
        await client.delete(path, headers=booker),
        await client.get(f"{path}/availability", headers=booker, params={"target_date": new_start.date().isoformat()}),
    )
    assert [response.status_code for response in responses] == [409, 409, 409]
    current = await client.get(path, headers=booker)
    assert current.status_code == 200, current.text
    assert current.json()["status"] == BookingStatus.CONFIRMED.value
    assert datetime.fromisoformat(current.json()["start_time"]) == past_start


async def test_concurrent_moves_to_same_slot_leave_losing_booking_unchanged(
    client: AsyncClient, reservation_pitch
) -> None:
    pitch_id, (_, first_booker, second_booker, _) = reservation_pitch
    owners = (first_booker, second_booker)
    original_times = (_time(10), _time(12))
    bookings = [
        await _book(client, pitch_id, headers, start)
        for headers, start in zip(owners, original_times)
    ]
    target = _time(14)
    responses = await asyncio.wait_for(
        asyncio.gather(
            *(
                client.patch(
                    f"{BOOKINGS}/{booking['id']}",
                    headers=headers,
                    json={"start_time": target.isoformat()},
                )
                for booking, headers in zip(bookings, owners)
            )
        ),
        timeout=20,
    )
    assert sorted(response.status_code for response in responses) == [200, 409]

    for booking, headers, original_start, response in zip(bookings, owners, original_times, responses):
        current = await client.get(f"{BOOKINGS}/{booking['id']}", headers=headers)
        assert current.status_code == 200, current.text
        expected_start = target if response.status_code == 200 else original_start
        assert datetime.fromisoformat(current.json()["start_time"]) == expected_start
        assert current.json()["status"] == "CONFIRMED"


async def test_cancel_and_lobby_creation_cannot_leave_an_open_lobby(
    client: AsyncClient, reservation_pitch
) -> None:
    pitch_id, (_, booker, _, _) = reservation_pitch
    booking = await _book(client, pitch_id, booker, _time(17))
    cancel, create = await asyncio.wait_for(
        asyncio.gather(
            client.delete(f"{BOOKINGS}/{booking['id']}", headers=booker),
            client.post(
                MATCHES,
                headers=booker,
                json={
                    "booking_id": booking["id"],
                    "match_type": "OPEN_LOBBY",
                    "target_players": 4,
                },
            ),
        ),
        timeout=20,
    )
    assert cancel.status_code == 200, cancel.text
    assert create.status_code in (201, 400), create.text

    history = await client.get(f"{BOOKINGS}/{booking['id']}", headers=booker)
    assert history.status_code == 200, history.text
    assert history.json()["status"] == "CANCELLED"
    if create.status_code == 201:
        assert history.json()["match"]["id"] == create.json()["id"]
        assert history.json()["match"]["status"] == "CANCELLED"
    else:
        assert history.json()["match"] is None

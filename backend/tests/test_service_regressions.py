import asyncio
import uuid
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.base_entities import Pitch, User, Venue
from app.models.enums import SurfaceType, UserRole
from app.services.ai_tools import AITools


def _authorization(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(user.id))}"}


def _user(role: UserRole) -> User:
    return User(
        email=f"regression_{uuid.uuid4().hex}@test.com",
        hashed_password="not-used-in-this-test",
        full_name="Service Regression User",
        phone="+40700112233",
        role=role,
    )


@pytest.fixture
async def venue_setup(db_session: AsyncSession) -> tuple[User, Venue, Pitch]:
    owner = _user(UserRole.VENUE_OWNER)
    db_session.add(owner)
    await db_session.flush()

    venue = Venue(
        owner_id=owner.id,
        name="Service Regression Venue",
        address="Strada Sportului 1",
        city="Timișoara",
        phone="+40700112234",
        latitude=Decimal("45.7537"),
        longitude=Decimal("21.2257"),
        opening_hour=8,
        closing_hour=23,
    )
    db_session.add(venue)
    await db_session.flush()

    pitch = Pitch(
        venue_id=venue.id,
        name="Service Regression Pitch",
        surface_type=SurfaceType.SYNTHETIC_3G,
        team_size_capacity=5,
        hourly_rate=Decimal("120.00"),
        is_active=True,
    )
    db_session.add(pitch)
    await db_session.commit()
    return owner, venue, pitch


@pytest.mark.asyncio
async def test_tournament_serializes_registration_for_the_last_spot(
    client: AsyncClient,
    db_session: AsyncSession,
    venue_setup: tuple[User, Venue, Pitch],
) -> None:
    owner, venue, _ = venue_setup
    captains = [_user(UserRole.PLAYER) for _ in range(5)]
    db_session.add_all(captains)
    await db_session.commit()

    start_date = datetime.now(timezone.utc).date() + timedelta(days=7)
    created = await client.post(
        "/api/v1/tournaments",
        headers=_authorization(owner),
        json={
            "venue_id": str(venue.id),
            "name": "Registration Race",
            "max_teams": 4,
            "start_date": start_date.isoformat(),
            "end_date": start_date.isoformat(),
        },
    )
    assert created.status_code == 201, created.text
    tournament_path = f"/api/v1/tournaments/{created.json()['id']}"

    for index, captain in enumerate(captains[:3], start=1):
        response = await client.post(
            f"{tournament_path}/teams",
            headers=_authorization(captain),
            json={"team_name": f"Team {index}"},
        )
        assert response.status_code == 201, response.text

    contenders = await asyncio.gather(
        *(
            client.post(
                f"{tournament_path}/teams",
                headers=_authorization(captain),
                json={"team_name": f"Team {index}"},
            )
            for index, captain in enumerate(captains[3:], start=4)
        )
    )
    assert sorted(response.status_code for response in contenders) == [201, 409]
    winner = next(response.json() for response in contenders if response.status_code == 201)
    assert winner["seed_number"] == 4

    response = await client.get(tournament_path)
    assert response.status_code == 200
    tournament = response.json()
    assert tournament["teams_count"] == tournament["max_teams"] == 4
    assert sorted(team["seed_number"] for team in tournament["teams"]) == [1, 2, 3, 4]


@pytest.mark.asyncio
async def test_venue_partial_update_validates_effective_operating_hours(
    client: AsyncClient, venue_setup: tuple[User, Venue, Pitch]
) -> None:
    owner, venue, _ = venue_setup
    path = f"/api/v1/venues/{venue.id}"
    headers = _authorization(owner)

    rejected = await client.patch(path, headers=headers, json={"closing_hour": 7})
    assert rejected.status_code == 422, rejected.text

    updated = await client.patch(path, headers=headers, json={"opening_hour": 0})
    assert updated.status_code == 200, updated.text
    assert updated.json()["opening_hour"] == 0
    assert updated.json()["closing_hour"] == 23


@pytest.mark.asyncio
async def test_venue_concurrent_partial_updates_validate_persisted_hours(
    client: AsyncClient, venue_setup: tuple[User, Venue, Pitch]
) -> None:
    owner, venue, _ = venue_setup
    path = f"/api/v1/venues/{venue.id}"
    headers = _authorization(owner)
    responses = await asyncio.gather(
        client.patch(path, headers=headers, json={"opening_hour": 20}),
        client.patch(path, headers=headers, json={"closing_hour": 12}),
    )
    assert sorted(response.status_code for response in responses) == [200, 422]

    response = await client.get(path)
    assert response.status_code == 200
    updated = response.json()
    assert (updated["opening_hour"], updated["closing_hour"]) in {(20, 23), (8, 12)}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("days", "start_hour", "start_minute", "expected_status"),
    [(-1, 17, 0, "PAST"), (1, 22, 30, "OUTSIDE_OPERATING_HOURS")],
)
async def test_ai_draft_and_checkout_reject_the_same_unbookable_times(
    client: AsyncClient,
    db_session: AsyncSession,
    venue_setup: tuple[User, Venue, Pitch],
    days: int,
    start_hour: int,
    start_minute: int,
    expected_status: str,
) -> None:
    owner, _, pitch = venue_setup
    day = datetime.now(timezone.utc).date() + timedelta(days=days)
    start = datetime.combine(day, time(start_hour, start_minute), tzinfo=timezone.utc)
    end = start + timedelta(hours=1)

    quote = await AITools(db_session).draft_booking(pitch.id, start, end)
    assert quote["is_available"] is False
    assert quote["status"] == expected_status

    checkout = await client.post(
        "/api/v1/bookings",
        headers=_authorization(owner),
        json={
            "pitch_id": str(pitch.id),
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
    )
    assert checkout.status_code == 400, checkout.text
    assert checkout.json()["detail"] == quote["message"]

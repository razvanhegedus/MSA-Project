import asyncio
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.base_entities import Pitch, User, Venue
from app.models.enums import SurfaceType, UserRole


@pytest.fixture
async def setup_venue_and_pitch(db_session: AsyncSession):
    """Seed a VENUE_OWNER, Venue (08:00 - 23:00), and an active Pitch."""
    uid = uuid.uuid4().hex[:8]
    owner = User(
        id=uuid.uuid4(),
        email=f"owner_{uid}@example.com",
        hashed_password="$2b$12$e80yqX3tS73x9BwNlI6X9e3E52z8x6YF2sU5kH5E4g8x2q9w8e7yK",
        full_name="Arena Manager",
        phone="+40711223344",
        role=UserRole.VENUE_OWNER,
    )
    db_session.add(owner)
    await db_session.flush()

    venue = Venue(
        id=uuid.uuid4(),
        owner_id=owner.id,
        name=f"Camp Nou {uid}",
        address="Strada Sportului 10",
        city="Reșița",
        phone="+40711223344",
        latitude=Decimal("45.297700"),
        longitude=Decimal("21.884500"),
        opening_hour=8,
        closing_hour=23,
    )
    db_session.add(venue)
    await db_session.flush()

    pitch = Pitch(
        id=uuid.uuid4(),
        venue_id=venue.id,
        name="Pitch 1 - Synth Pro",
        surface_type=SurfaceType.SYNTHETIC_3G,
        team_size_capacity=6,
        hourly_rate=Decimal("150.00"),
        is_active=True,
    )
    db_session.add(pitch)
    await db_session.commit()
    await db_session.refresh(venue)
    await db_session.refresh(pitch)

    return owner, venue, pitch


@pytest.fixture
async def setup_10_players(db_session: AsyncSession):
    """Seed 10 distinct PLAYER accounts and return their JWT access tokens."""
    uid = uuid.uuid4().hex[:8]
    players = []
    tokens = []

    for i in range(10):
        player_id = uuid.uuid4()
        player = User(
            id=player_id,
            email=f"player_{i}_{uid}@example.com",
            hashed_password="$2b$12$e80yqX3tS73x9BwNlI6X9e3E52z8x6YF2sU5kH5E4g8x2q9w8e7yK",
            full_name=f"Player Number {i}",
            phone=f"+407990011{i:02d}",
            role=UserRole.PLAYER,
        )
        db_session.add(player)
        players.append(player)
        tokens.append(create_access_token(subject=str(player_id)))

    await db_session.commit()
    return players, tokens


@pytest.mark.asyncio
async def test_booking_concurrency_race_condition(
    client: AsyncClient, setup_venue_and_pitch, setup_10_players
):
    """
    Test 1 (Hardware Race Condition):
    Fire 10 concurrent POST /api/v1/bookings requests via asyncio.gather for the exact same
    pitch_id and 18:00-19:00 window.
    Assert that exactly 1 response returns 201 Created and exactly 9 return 409 Conflict.
    """
    owner, venue, pitch = setup_venue_and_pitch
    players, tokens = setup_10_players

    target_date = date.today() + timedelta(days=5)
    start_time = datetime.combine(target_date, time(18, 0), tzinfo=timezone.utc)
    end_time = datetime.combine(target_date, time(19, 0), tzinfo=timezone.utc)

    payload = {
        "pitch_id": str(pitch.id),
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "create_open_lobby": False,
    }

    # Fire 10 concurrent booking requests simultaneously
    tasks = [
        client.post(
            "/api/v1/bookings",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        for token in tokens
    ]
    responses = await asyncio.gather(*tasks)

    status_codes = [r.status_code for r in responses]
    assert status_codes.count(201) == 1, f"Expected 1 Created, got {status_codes}"
    assert status_codes.count(409) == 9, f"Expected 9 Conflicts, got {status_codes}"

    # Verify that the 409 error response returns the SlotAlreadyBookedError detail
    conflict_responses = [r for r in responses if r.status_code == 409]
    for resp in conflict_responses:
        error_detail = resp.json()["detail"].lower()
        assert "already booked" in error_detail


@pytest.mark.asyncio
async def test_booking_half_open_interval_boundary(
    client: AsyncClient, setup_venue_and_pitch, setup_10_players
):
    """
    Test 2 (Half-Open Interval [) Boundary):
    Verify that booking the immediate next hour (19:00 to 20:00 UTC) on the same pitch
    succeeds with 201 Created, confirming the exclusion constraint allows back-to-back reservations.
    """
    owner, venue, pitch = setup_venue_and_pitch
    players, tokens = setup_10_players

    target_date = date.today() + timedelta(days=6)
    # First booking: 18:00 - 19:00
    first_start = datetime.combine(target_date, time(18, 0), tzinfo=timezone.utc)
    first_end = datetime.combine(target_date, time(19, 0), tzinfo=timezone.utc)

    resp1 = await client.post(
        "/api/v1/bookings",
        json={
            "pitch_id": str(pitch.id),
            "start_time": first_start.isoformat(),
            "end_time": first_end.isoformat(),
            "create_open_lobby": False,
        },
        headers={"Authorization": f"Bearer {tokens[0]}"},
    )
    assert resp1.status_code == 201, resp1.text

    # Back-to-back booking: 19:00 - 20:00 (exact boundary touch [18:00, 19:00) and [19:00, 20:00))
    second_start = datetime.combine(target_date, time(19, 0), tzinfo=timezone.utc)
    second_end = datetime.combine(target_date, time(20, 0), tzinfo=timezone.utc)

    resp2 = await client.post(
        "/api/v1/bookings",
        json={
            "pitch_id": str(pitch.id),
            "start_time": second_start.isoformat(),
            "end_time": second_end.isoformat(),
            "create_open_lobby": False,
        },
        headers={"Authorization": f"Bearer {tokens[1]}"},
    )
    assert resp2.status_code == 201, resp2.text
    booking_data = resp2.json()
    assert booking_data["status"] == "CONFIRMED"
    assert booking_data["pitch_id"] == str(pitch.id)


@pytest.mark.asyncio
async def test_availability_matrix_and_open_lobby(
    client: AsyncClient, setup_venue_and_pitch, setup_10_players
):
    """
    Test 3 (Availability Matrix States):
    Book a slot with create_open_lobby=True, query GET /api/v1/pitches/{pitch_id}/availability,
    and assert the 18:00-19:00 slot is OCCUPIED, open-lobby slot (20:00-21:00) is OPEN_LOBBY
    with spots_left, and unbooked hours are AVAILABLE.
    """
    owner, venue, pitch = setup_venue_and_pitch
    players, tokens = setup_10_players

    target_date = date.today() + timedelta(days=7)

    # 1. Standard booking at 18:00 - 19:00
    slot1_start = datetime.combine(target_date, time(18, 0), tzinfo=timezone.utc)
    slot1_end = datetime.combine(target_date, time(19, 0), tzinfo=timezone.utc)
    r1 = await client.post(
        "/api/v1/bookings",
        json={
            "pitch_id": str(pitch.id),
            "start_time": slot1_start.isoformat(),
            "end_time": slot1_end.isoformat(),
            "create_open_lobby": False,
        },
        headers={"Authorization": f"Bearer {tokens[0]}"},
    )
    assert r1.status_code == 201

    # 2. Open Lobby booking at 20:00 - 21:00 (capacity 10, organizer confirmed -> 9 spots left)
    slot2_start = datetime.combine(target_date, time(20, 0), tzinfo=timezone.utc)
    slot2_end = datetime.combine(target_date, time(21, 0), tzinfo=timezone.utc)
    r2 = await client.post(
        "/api/v1/bookings",
        json={
            "pitch_id": str(pitch.id),
            "start_time": slot2_start.isoformat(),
            "end_time": slot2_end.isoformat(),
            "create_open_lobby": True,
            "target_players": 10,
            "lobby_description": "Friday Night 5v5 Casual Match",
        },
        headers={"Authorization": f"Bearer {tokens[1]}"},
    )
    assert r2.status_code == 201

    # 3. Query availability matrix for target_date
    avail_resp = await client.get(
        f"/api/v1/pitches/{pitch.id}/availability?target_date={target_date.isoformat()}"
    )
    assert avail_resp.status_code == 200, avail_resp.text
    slots = avail_resp.json()

    # Operating hours: 8 to 23 -> 15 slots
    assert len(slots) == (venue.closing_hour - venue.opening_hour)

    slots_by_hour = {}
    for slot in slots:
        slot_dt = datetime.fromisoformat(slot["start_time"])
        slots_by_hour[slot_dt.hour] = slot

    # Verify 18:00 - 19:00 is OCCUPIED
    assert slots_by_hour[18]["status"] == "OCCUPIED"
    assert slots_by_hour[18]["booking_id"] is not None

    # Verify 20:00 - 21:00 is OPEN_LOBBY with spots_left == 9
    assert slots_by_hour[20]["status"] == "OPEN_LOBBY"
    assert slots_by_hour[20]["booking_id"] is not None
    assert slots_by_hour[20]["open_match_id"] is not None
    assert slots_by_hour[20]["spots_left"] == 9

    # Verify unbooked hours (e.g. 08:00, 12:00, 19:00, 21:00) are AVAILABLE
    assert slots_by_hour[8]["status"] == "AVAILABLE"
    assert slots_by_hour[12]["status"] == "AVAILABLE"
    assert slots_by_hour[19]["status"] == "AVAILABLE"
    assert slots_by_hour[21]["status"] == "AVAILABLE"
    assert slots_by_hour[22]["status"] == "AVAILABLE"


@pytest.mark.asyncio
async def test_venues_and_bookings_api_flow(client: AsyncClient, setup_10_players):
    """
    Test full REST flow:
    - Create venue as VENUE_OWNER
    - List venues by city
    - Create pitch in venue
    - Retrieve pitch details
    - Create booking and list user's bookings via /bookings/me
    """
    players, tokens = setup_10_players
    owner_token = create_access_token(
        subject=str(players[0].id),
        claims={"role": UserRole.VENUE_OWNER.value},
    )

    # Make player 0 a VENUE_OWNER in database
    from app.core.database import async_session_maker
    async with async_session_maker() as session:
        p0 = await session.get(User, players[0].id)
        p0.role = UserRole.VENUE_OWNER
        await session.commit()

    # 1. Create Venue
    uid = uuid.uuid4().hex[:6]
    venue_payload = {
        "name": f"Timisoara Soccer Park {uid}",
        "address": "Bulevardul Eroilor 22",
        "city": "Timișoara",
        "phone": "+40722334455",
        "latitude": 45.7537,
        "longitude": 21.2257,
        "opening_hour": 9,
        "closing_hour": 22,
    }
    create_v_resp = await client.post(
        "/api/v1/venues",
        json=venue_payload,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert create_v_resp.status_code == 201, create_v_resp.text
    venue_data = create_v_resp.json()
    venue_id = venue_data["id"]
    assert venue_data["city"] == "Timișoara"

    # 2. List Venues
    list_resp = await client.get("/api/v1/venues?city=Timișoara")
    assert list_resp.status_code == 200
    assert any(v["id"] == venue_id for v in list_resp.json())

    # 3. Create Pitch
    pitch_payload = {
        "name": "Arena 1 Indoor",
        "surface_type": SurfaceType.INDOOR_TARAFLEX.value,
        "team_size_capacity": 5,
        "hourly_rate": 180.00,
        "is_active": True,
    }
    create_p_resp = await client.post(
        f"/api/v1/venues/{venue_id}/pitches",
        json=pitch_payload,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert create_p_resp.status_code == 201, create_p_resp.text
    pitch_data = create_p_resp.json()
    pitch_id = pitch_data["id"]

    # 4. Get Pitch by ID
    get_p_resp = await client.get(f"/api/v1/pitches/{pitch_id}")
    assert get_p_resp.status_code == 200
    assert get_p_resp.json()["name"] == "Arena 1 Indoor"

    # 5. Non-owner cannot create pitch
    unauth_p_resp = await client.post(
        f"/api/v1/venues/{venue_id}/pitches",
        json=pitch_payload,
        headers={"Authorization": f"Bearer {tokens[1]}"},
    )
    assert unauth_p_resp.status_code == 403

    # 6. Booking outside operating hours rejected
    target_date = date.today() + timedelta(days=10)
    outside_hours_resp = await client.post(
        "/api/v1/bookings",
        json={
            "pitch_id": pitch_id,
            "start_time": datetime.combine(target_date, time(7, 0), tzinfo=timezone.utc).isoformat(),
            "end_time": datetime.combine(target_date, time(8, 0), tzinfo=timezone.utc).isoformat(),
            "create_open_lobby": False,
        },
        headers={"Authorization": f"Bearer {tokens[1]}"},
    )
    assert outside_hours_resp.status_code == 400

    # 7. Valid Booking and /bookings/me
    valid_booking_resp = await client.post(
        "/api/v1/bookings",
        json={
            "pitch_id": pitch_id,
            "start_time": datetime.combine(target_date, time(10, 0), tzinfo=timezone.utc).isoformat(),
            "end_time": datetime.combine(target_date, time(11, 0), tzinfo=timezone.utc).isoformat(),
            "create_open_lobby": False,
        },
        headers={"Authorization": f"Bearer {tokens[1]}"},
    )
    assert valid_booking_resp.status_code == 201

    me_resp = await client.get(
        "/api/v1/bookings/me",
        headers={"Authorization": f"Bearer {tokens[1]}"},
    )
    assert me_resp.status_code == 200
    my_bookings = me_resp.json()
    assert any(b["id"] == valid_booking_resp.json()["id"] for b in my_bookings)

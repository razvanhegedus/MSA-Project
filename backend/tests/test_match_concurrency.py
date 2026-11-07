import asyncio
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.main import app
from app.models.base_entities import (
    Booking,
    Match,
    MatchParticipant,
    Pitch,
    Tournament,
    TournamentTeam,
    User,
    Venue,
)
from app.models.enums import (
    BookingStatus,
    MatchStatus,
    MatchType,
    ParticipantRole,
    ParticipantStatus,
    SurfaceType,
    TeamSide,
    TournamentFormat,
    TournamentStatus,
    UserRole,
)


@pytest.fixture
async def setup_match_with_1_slot_left(db_session: AsyncSession):
    """
    Seed a Venue, Pitch, confirmed Booking, and Match with target_players=2.
    Organizer is participant #1, leaving exactly 1 open slot.
    """
    uid = uuid.uuid4().hex[:8]

    # Organizer
    organizer = User(
        id=uuid.uuid4(),
        email=f"org_{uid}@example.com",
        hashed_password="$2b$12$e80yqX3tS73x9BwNlI6X9e3E52z8x6YF2sU5kH5E4g8x2q9w8e7yK",
        full_name="Match Organizer",
        phone="+40700112233",
        role=UserRole.PLAYER,
    )
    db_session.add(organizer)

    # Venue Owner
    owner = User(
        id=uuid.uuid4(),
        email=f"owner_{uid}@example.com",
        hashed_password="$2b$12$e80yqX3tS73x9BwNlI6X9e3E52z8x6YF2sU5kH5E4g8x2q9w8e7yK",
        full_name="Venue Boss",
        phone="+40700112244",
        role=UserRole.VENUE_OWNER,
    )
    db_session.add(owner)
    await db_session.flush()

    venue = Venue(
        id=uuid.uuid4(),
        owner_id=owner.id,
        name=f"Arena Central {uid}",
        address="Strada Victoriei 1",
        city="Timișoara",
        phone="+40700112244",
        latitude=Decimal("45.753700"),
        longitude=Decimal("21.225700"),
        opening_hour=8,
        closing_hour=23,
    )
    db_session.add(venue)
    await db_session.flush()

    pitch = Pitch(
        id=uuid.uuid4(),
        venue_id=venue.id,
        name="Pitch Alpha",
        surface_type=SurfaceType.SYNTHETIC_3G,
        team_size_capacity=5,
        hourly_rate=Decimal("120.00"),
        is_active=True,
    )
    db_session.add(pitch)
    await db_session.flush()

    target_date = date.today() + timedelta(days=3)
    start_time = datetime.combine(target_date, time(19, 0), tzinfo=timezone.utc)
    end_time = datetime.combine(target_date, time(20, 0), tzinfo=timezone.utc)

    booking = Booking(
        id=uuid.uuid4(),
        pitch_id=pitch.id,
        booked_by_user_id=organizer.id,
        start_time=start_time,
        end_time=end_time,
        total_price=Decimal("120.00"),
        status=BookingStatus.CONFIRMED,
    )
    db_session.add(booking)
    await db_session.flush()

    # Match with capacity of 2 players
    match = Match(
        id=uuid.uuid4(),
        booking_id=booking.id,
        organizer_id=organizer.id,
        match_type=MatchType.OPEN_LOBBY,
        target_players=2,
        needed_positions=["MIDFIELDER"],
        description="Fast 1v1 showdown or last spot duel",
        status=MatchStatus.OPEN,
        scheduled_at=start_time,
    )
    db_session.add(match)
    await db_session.flush()

    organizer_participant = MatchParticipant(
        id=uuid.uuid4(),
        match_id=match.id,
        user_id=organizer.id,
        team_side=TeamSide.A,
        role=ParticipantRole.ORGANIZER,
        status=ParticipantStatus.CONFIRMED,
    )
    db_session.add(organizer_participant)
    await db_session.commit()

    return organizer, venue, pitch, booking, match


@pytest.fixture
async def setup_5_joiners(db_session: AsyncSession):
    """Seed 5 distinct users wanting to join the same match."""
    uid = uuid.uuid4().hex[:8]
    users = []
    tokens = []

    for i in range(5):
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email=f"joiner_{i}_{uid}@example.com",
            hashed_password="$2b$12$e80yqX3tS73x9BwNlI6X9e3E52z8x6YF2sU5kH5E4g8x2q9w8e7yK",
            full_name=f"Joiner {i}",
            phone=f"+407334455{i:02d}",
            role=UserRole.PLAYER,
        )
        db_session.add(user)
        users.append(user)
        tokens.append(create_access_token(subject=str(user_id)))

    await db_session.commit()
    return users, tokens


@pytest.mark.asyncio
async def test_match_join_concurrency_capacity_lock(
    setup_match_with_1_slot_left, setup_5_joiners, db_session: AsyncSession
):
    """
    Test Phase 5 Concurrency Verification Gate:
    1 match with target_players=2, 1 slot already occupied by organizer (1 spot left).
    5 parallel POST /api/v1/matches/{match_id}/join requests are fired concurrently.
    Assert:
    - Exactly 1 request succeeds with 200 OK and match status == "FULL".
    - Exactly 4 requests fail with 409 Conflict (LobbyFullError).
    - Database row count in match_participants is strictly 2.
    """
    organizer, venue, pitch, booking, match = setup_match_with_1_slot_left
    users, tokens = setup_5_joiners

    async def send_join_request(token: str):
        # Create an independent AsyncClient for each concurrent task
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            return await client.post(
                f"/api/v1/matches/{match.id}/join",
                json={"team_side": "B", "role": "PLAYER"},
                headers={"Authorization": f"Bearer {token}"},
            )

    tasks = [send_join_request(token) for token in tokens]
    responses = await asyncio.gather(*tasks)

    status_codes = [r.status_code for r in responses]
    assert status_codes.count(200) == 1, f"Expected exactly 1 200 OK, got: {status_codes}"
    assert status_codes.count(409) == 4, f"Expected exactly 4 409 Conflict, got: {status_codes}"

    # Verify winning response
    winner_resp = next(r for r in responses if r.status_code == 200)
    winner_data = winner_resp.json()
    assert winner_data["status"] == "FULL"
    assert winner_data["current_players_count"] == 2
    assert len(winner_data["participants"]) == 2

    # Verify database state has strictly 2 participants
    count_stmt = select(func.count(MatchParticipant.id)).where(
        MatchParticipant.match_id == match.id
    )
    count_result = await db_session.execute(count_stmt)
    total_participants = count_result.scalar_one()
    assert total_participants == 2, f"Database corruption: expected 2 participants, found {total_participants}"


@pytest.mark.asyncio
async def test_match_already_joined_error(
    client: AsyncClient, setup_match_with_1_slot_left
):
    """Verify that an already registered player cannot join the match again."""
    organizer, venue, pitch, booking, match = setup_match_with_1_slot_left
    org_token = create_access_token(subject=str(organizer.id))

    # Organizer attempts to join their own match again
    resp = await client.post(
        f"/api/v1/matches/{match.id}/join",
        json={"team_side": "A", "role": "PLAYER"},
        headers={"Authorization": f"Bearer {org_token}"},
    )
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_tournament_lifecycle_and_team_registration(
    client: AsyncClient, setup_match_with_1_slot_left, setup_5_joiners
):
    """
    Test Tournament creation by venue owner, listing, and team registration capacity.
    """
    organizer, venue, pitch, booking, match = setup_match_with_1_slot_left
    users, tokens = setup_5_joiners

    owner_token = create_access_token(
        subject=str(venue.owner_id),
        claims={"role": UserRole.VENUE_OWNER.value},
    )

    start_d = date.today() + timedelta(days=14)
    end_d = date.today() + timedelta(days=16)

    # 1. Create Tournament (4 teams max)
    t_payload = {
        "venue_id": str(venue.id),
        "name": "Banat Championship Cup",
        "format": TournamentFormat.SINGLE_ELIMINATION.value,
        "max_teams": 4,
        "entry_fee": 100.00,
        "start_date": start_d.isoformat(),
        "end_date": end_d.isoformat(),
    }
    create_t_resp = await client.post(
        "/api/v1/tournaments",
        json=t_payload,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert create_t_resp.status_code == 201, create_t_resp.text
    tournament_data = create_t_resp.json()
    t_id = tournament_data["id"]
    assert tournament_data["status"] == TournamentStatus.REGISTRATION_OPEN.value
    assert tournament_data["max_teams"] == 4

    # 2. Register 4 teams (filling up tournament)
    for i in range(4):
        reg_resp = await client.post(
            f"/api/v1/tournaments/{t_id}/teams",
            json={"team_name": f"FC Stars {i}"},
            headers={"Authorization": f"Bearer {tokens[i]}"},
        )
        assert reg_resp.status_code == 201, reg_resp.text
        team_data = reg_resp.json()
        assert team_data["seed_number"] == i + 1

    # 3. 5th team registration rejected (exceeds max_teams=4)
    overflow_resp = await client.post(
        f"/api/v1/tournaments/{t_id}/teams",
        json={"team_name": "FC Overflow"},
        headers={"Authorization": f"Bearer {tokens[4]}"},
    )
    assert overflow_resp.status_code == 409
    assert "maximum capacity" in overflow_resp.json()["detail"].lower()

    # 4. Get Tournament Details
    get_t_resp = await client.get(f"/api/v1/tournaments/{t_id}")
    assert get_t_resp.status_code == 200
    t_details = get_t_resp.json()
    assert t_details["teams_count"] == 4
    assert len(t_details["teams"]) == 4


@pytest.mark.asyncio
async def test_match_list_position_filter(
    client: AsyncClient, setup_match_with_1_slot_left
) -> None:
    """Verify listing matches allows filtering by string position tags."""
    _, _, _, _, match = setup_match_with_1_slot_left

    # Match has needed_positions=["MIDFIELDER"]
    resp_match = await client.get("/api/v1/matches?needed_role=Midfielder")
    assert resp_match.status_code == 200
    data = resp_match.json()
    assert any(m["id"] == str(match.id) for m in data)

    # Filter by non-matching position returns empty list
    resp_nomatch = await client.get("/api/v1/matches?needed_role=Goalkeeper")
    assert resp_nomatch.status_code == 200
    data_nomatch = resp_nomatch.json()
    assert not any(m["id"] == str(match.id) for m in data_nomatch)


@pytest.mark.asyncio
async def test_user_matches_and_update_lobby(
    client: AsyncClient, setup_match_with_1_slot_left, setup_5_joiners
) -> None:
    """Verify GET /api/v1/matches/me, PATCH /api/v1/matches/{id}, and enriched booking responses."""
    organizer, venue, pitch, booking, match = setup_match_with_1_slot_left
    players, tokens = setup_5_joiners

    org_token = create_access_token(subject=str(organizer.id))
    p1_token = tokens[0]

    # 1. Organizer sees their organized match in /matches/me
    my_matches_resp = await client.get(
        "/api/v1/matches/me", headers={"Authorization": f"Bearer {org_token}"}
    )
    assert my_matches_resp.status_code == 200
    my_matches = my_matches_resp.json()
    assert any(m["id"] == str(match.id) for m in my_matches)

    # 2. Player joins the match
    join_resp = await client.post(
        f"/api/v1/matches/{match.id}/join",
        json={"team_side": "B", "role": "PLAYER"},
        headers={"Authorization": f"Bearer {p1_token}"},
    )
    assert join_resp.status_code == 200

    # 3. Player now also sees the match in their /matches/me
    p1_matches_resp = await client.get(
        "/api/v1/matches/me", headers={"Authorization": f"Bearer {p1_token}"}
    )
    assert p1_matches_resp.status_code == 200
    assert any(m["id"] == str(match.id) for m in p1_matches_resp.json())

    # 4. Non-organizer attempts to PATCH the lobby -> 403 Forbidden
    unauth_patch = await client.patch(
        f"/api/v1/matches/{match.id}",
        json={"spots_needed": 3},
        headers={"Authorization": f"Bearer {p1_token}"},
    )
    assert unauth_patch.status_code == 403

    # 5. Organizer updates lobby with spots_needed=3 (confirmed_count=2, so target_players becomes 5)
    patch_resp = await client.patch(
        f"/api/v1/matches/{match.id}",
        json={
            "spots_needed": 3,
            "needed_positions": ["Goalkeeper", "Forward"],
            "description": "Updated: Need 3 more players!",
        },
        headers={"Authorization": f"Bearer {org_token}"},
    )
    assert patch_resp.status_code == 200
    patched = patch_resp.json()
    assert patched["target_players"] == 5
    assert patched["current_players_count"] == 2
    assert patched["status"] == "OPEN"
    assert patched["description"] == "Updated: Need 3 more players!"
    assert patched["needed_positions"] == ["Goalkeeper", "Forward"]

    # 6. Check enriched Booking response via /bookings/me
    bookings_resp = await client.get(
        "/api/v1/bookings/me", headers={"Authorization": f"Bearer {org_token}"}
    )
    assert bookings_resp.status_code == 200
    b_data = bookings_resp.json()
    assert len(b_data) > 0
    my_b = next((b for b in b_data if b["id"] == str(match.booking_id)), None)
    assert my_b is not None
    assert my_b["pitch_name"] == pitch.name
    assert my_b["venue_name"] == venue.name
    assert my_b["city"] == venue.city
    assert my_b["match"] is not None
    assert my_b["open_match_id"] == str(match.id)
    assert my_b["spots_left"] == 3

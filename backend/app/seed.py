"""
Database seed & cleanup script for Pitch Platform.
Can be executed as a module: `python -m app.seed` (from the backend directory).

Capabilities:
1. Delete leftover test artifacts (venues matching test patterns, test users matching %@example.com or %@test.com,
   and cascading bookings/matches/pitches/tournaments).
2. Idempotently seed realistic venues and diverse pitches across Cluj-Napoca, Timișoara, București, Iași, and Brașov.
3. Seed active OPEN_LOBBY and SQUAD_CHALLENGE matches scheduled for upcoming hours/days.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.core.security import get_password_hash
from app.models.base_entities import Booking, Match, MatchParticipant, Pitch, User, Venue
from app.models.enums import (
    BookingStatus,
    MatchStatus,
    MatchType,
    ParticipantRole,
    ParticipantStatus,
    SurfaceType,
    TeamSide,
    UserRole,
)

logger = logging.getLogger("seed")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ──────────────────────────────────────────────────────────────────────────────
# 1. Cleanup Test Artifacts
# ──────────────────────────────────────────────────────────────────────────────

async def _execute_clean_test_artifacts(session: AsyncSession) -> None:
    """Execute raw SQL statements to cascade-delete all test artifacts without violating foreign key constraints."""
    test_users_subquery = """
        SELECT id FROM users
        WHERE email LIKE '%@example.com' OR email LIKE '%@test.com'
    """

    test_venues_subquery = f"""
        SELECT id FROM venues
        WHERE name LIKE 'Timisoara Soccer Park%'
           OR name LIKE 'Camp Nou%'
           OR name LIKE 'Arena Central%'
           OR name LIKE 'AI Arena%'
           OR owner_id IN ({test_users_subquery})
    """

    test_pitches_subquery = f"""
        SELECT id FROM pitches
        WHERE venue_id IN ({test_venues_subquery})
    """

    test_bookings_subquery = f"""
        SELECT id FROM bookings
        WHERE booked_by_user_id IN ({test_users_subquery})
           OR pitch_id IN ({test_pitches_subquery})
    """

    test_matches_subquery = f"""
        SELECT id FROM matches
        WHERE organizer_id IN ({test_users_subquery})
           OR booking_id IN ({test_bookings_subquery})
    """

    test_tournaments_subquery = f"""
        SELECT id FROM tournaments
        WHERE organizer_id IN ({test_users_subquery})
           OR venue_id IN ({test_venues_subquery})
    """

    # 1. match_participants
    await session.execute(text(f"""
        DELETE FROM match_participants
        WHERE user_id IN ({test_users_subquery})
           OR match_id IN ({test_matches_subquery});
    """))

    # 2. matches
    await session.execute(text(f"""
        DELETE FROM matches
        WHERE id IN ({test_matches_subquery});
    """))

    # 3. tournament_teams
    await session.execute(text(f"""
        DELETE FROM tournament_teams
        WHERE captain_id IN ({test_users_subquery})
           OR tournament_id IN ({test_tournaments_subquery});
    """))

    # 4. tournaments
    await session.execute(text(f"""
        DELETE FROM tournaments
        WHERE id IN ({test_tournaments_subquery});
    """))

    # 5. bookings
    await session.execute(text(f"""
        DELETE FROM bookings
        WHERE id IN ({test_bookings_subquery});
    """))

    # 6. pitches
    await session.execute(text(f"""
        DELETE FROM pitches
        WHERE id IN ({test_pitches_subquery});
    """))

    # 7. venues
    await session.execute(text(f"""
        DELETE FROM venues
        WHERE id IN ({test_venues_subquery});
    """))

    # 8. refresh_tokens
    await session.execute(text(f"""
        DELETE FROM refresh_tokens
        WHERE user_id IN ({test_users_subquery});
    """))

    # 9. users
    await session.execute(text(f"""
        DELETE FROM users
        WHERE id IN ({test_users_subquery});
    """))


async def clean_test_artifacts(session: Optional[AsyncSession] = None) -> None:
    """Delete leftover test artifacts from pytest concurrency & LLM runs."""
    if session is None:
        async with async_session_maker() as new_session:
            async with new_session.begin():
                await _execute_clean_test_artifacts(new_session)
    else:
        await _execute_clean_test_artifacts(session)
    logger.info("Test artifacts cleaned up successfully.")


# ──────────────────────────────────────────────────────────────────────────────
# 2. Seed Data Definitions
# ──────────────────────────────────────────────────────────────────────────────

SEED_USERS = [
    # Venue Owners
    {
        "email": "owner.cluj@pitchup.ro",
        "full_name": "Radu Mureșan",
        "phone": "+40721111001",
        "role": UserRole.VENUE_OWNER,
    },
    {
        "email": "owner.timis@pitchup.ro",
        "full_name": "Sorin Bănățean",
        "phone": "+40721111002",
        "role": UserRole.VENUE_OWNER,
    },
    {
        "email": "owner.bucuresti@pitchup.ro",
        "full_name": "Cristian Ionescu",
        "phone": "+40721111003",
        "role": UserRole.VENUE_OWNER,
    },
    {
        "email": "owner.iasi@pitchup.ro",
        "full_name": "Vasile Vasiliu",
        "phone": "+40721111004",
        "role": UserRole.VENUE_OWNER,
    },
    {
        "email": "owner.brasov@pitchup.ro",
        "full_name": "Dan Brașoveanu",
        "phone": "+40721111005",
        "role": UserRole.VENUE_OWNER,
    },
    # Players
    {
        "email": "andrei.popa@pitchup.ro",
        "full_name": "Andrei Popa",
        "phone": "+40730000001",
        "role": UserRole.PLAYER,
    },
    {
        "email": "marian.radu@pitchup.ro",
        "full_name": "Marian Radu",
        "phone": "+40730000002",
        "role": UserRole.PLAYER,
    },
    {
        "email": "bogdan.stan@pitchup.ro",
        "full_name": "Bogdan Stan",
        "phone": "+40730000003",
        "role": UserRole.PLAYER,
    },
    {
        "email": "florin.dumitru@pitchup.ro",
        "full_name": "Florin Dumitru",
        "phone": "+40730000004",
        "role": UserRole.PLAYER,
    },
    {
        "email": "alex.constantin@pitchup.ro",
        "full_name": "Alex Constantin",
        "phone": "+40730000005",
        "role": UserRole.PLAYER,
    },
    {
        "email": "vlad.georgescu@pitchup.ro",
        "full_name": "Vlad Georgescu",
        "phone": "+40730000006",
        "role": UserRole.PLAYER,
    },
]

SEED_VENUES = [
    # ── Cluj-Napoca (3 Venues) ──
    {
        "owner_email": "owner.cluj@pitchup.ro",
        "name": "Baza Sportivă Gheorgheni",
        "address": "Strada Alexandru Vaida Voevod F.N.",
        "city": "Cluj-Napoca",
        "phone": "+40264405300",
        "latitude": Decimal("46.771200"),
        "longitude": Decimal("23.630500"),
        "opening_hour": 8,
        "closing_hour": 23,
        "pitches": [
            {
                "name": "Teren 1 Sintetic Pro",
                "surface_type": SurfaceType.SYNTHETIC_3G,
                "team_size_capacity": 6,
                "hourly_rate": Decimal("160.00"),
            },
            {
                "name": "Sala Gheorgheni Taraflex",
                "surface_type": SurfaceType.INDOOR_TARAFLEX,
                "team_size_capacity": 5,
                "hourly_rate": Decimal("200.00"),
            },
            {
                "name": "Teren Central Gazon Natural",
                "surface_type": SurfaceType.NATURAL_GRASS,
                "team_size_capacity": 11,
                "hourly_rate": Decimal("280.00"),
            },
        ],
    },
    {
        "owner_email": "owner.cluj@pitchup.ro",
        "name": "Winners Sports Club Cluj",
        "address": "Parcul Rozelor, Strada Plopilor",
        "city": "Cluj-Napoca",
        "phone": "+40755740407",
        "latitude": Decimal("46.762100"),
        "longitude": Decimal("23.568900"),
        "opening_hour": 8,
        "closing_hour": 23,
        "pitches": [
            {
                "name": "Teren Hibrid Rozelor",
                "surface_type": SurfaceType.HYBRID,
                "team_size_capacity": 7,
                "hourly_rate": Decimal("240.00"),
            },
            {
                "name": "Teren Sintetic Mini",
                "surface_type": SurfaceType.SYNTHETIC_3G,
                "team_size_capacity": 5,
                "hourly_rate": Decimal("150.00"),
            },
        ],
    },
    {
        "owner_email": "owner.cluj@pitchup.ro",
        "name": "Baza Sportivă Transilvania",
        "address": "Bulevardul Muncii 18",
        "city": "Cluj-Napoca",
        "phone": "+40742100200",
        "latitude": Decimal("46.790500"),
        "longitude": Decimal("23.621000"),
        "opening_hour": 9,
        "closing_hour": 23,
        "pitches": [
            {
                "name": "Arena Transilvania Indoor",
                "surface_type": SurfaceType.INDOOR_TARAFLEX,
                "team_size_capacity": 6,
                "hourly_rate": Decimal("190.00"),
            },
            {
                "name": "Teren Sintetic Nocturnă",
                "surface_type": SurfaceType.SYNTHETIC_3G,
                "team_size_capacity": 8,
                "hourly_rate": Decimal("210.00"),
            },
        ],
    },
    # ── Timișoara (3 Venues) ──
    {
        "owner_email": "owner.timis@pitchup.ro",
        "name": "Baza Sportivă Banat Arena",
        "address": "Bulevardul Vasile Pârvan 5",
        "city": "Timișoara",
        "phone": "+40256403000",
        "latitude": Decimal("45.748900"),
        "longitude": Decimal("21.231400"),
        "opening_hour": 8,
        "closing_hour": 23,
        "pitches": [
            {
                "name": "Teren Gazon Bega",
                "surface_type": SurfaceType.NATURAL_GRASS,
                "team_size_capacity": 8,
                "hourly_rate": Decimal("220.00"),
            },
            {
                "name": "Teren Sintetic Banat",
                "surface_type": SurfaceType.SYNTHETIC_3G,
                "team_size_capacity": 6,
                "hourly_rate": Decimal("170.00"),
            },
        ],
    },
    {
        "owner_email": "owner.timis@pitchup.ro",
        "name": "Timișoara Indoor Sports Hub",
        "address": "Calea Sever Bocu 42",
        "city": "Timișoara",
        "phone": "+40723890123",
        "latitude": Decimal("45.772500"),
        "longitude": Decimal("21.229100"),
        "opening_hour": 8,
        "closing_hour": 23,
        "pitches": [
            {
                "name": "Taraflex Dome A",
                "surface_type": SurfaceType.INDOOR_TARAFLEX,
                "team_size_capacity": 5,
                "hourly_rate": Decimal("180.00"),
            },
            {
                "name": "Teren Hibrid Sever Bocu",
                "surface_type": SurfaceType.HYBRID,
                "team_size_capacity": 7,
                "hourly_rate": Decimal("230.00"),
            },
        ],
    },
    {
        "owner_email": "owner.timis@pitchup.ro",
        "name": "Complex Sportiv Tivoli",
        "address": "Strada Renașterii 24",
        "city": "Timișoara",
        "phone": "+40729345678",
        "latitude": Decimal("45.761200"),
        "longitude": Decimal("21.248300"),
        "opening_hour": 9,
        "closing_hour": 22,
        "pitches": [
            {
                "name": "Tivoli Sintetic 1",
                "surface_type": SurfaceType.SYNTHETIC_3G,
                "team_size_capacity": 5,
                "hourly_rate": Decimal("140.00"),
            },
            {
                "name": "Tivoli Mare 11v11",
                "surface_type": SurfaceType.SYNTHETIC_3G,
                "team_size_capacity": 11,
                "hourly_rate": Decimal("270.00"),
            },
        ],
    },
    # ── București (3 Venues) ──
    {
        "owner_email": "owner.bucuresti@pitchup.ro",
        "name": "Arena Națională Sports Park",
        "address": "Bulevardul Basarabia 37-39, Sector 2",
        "city": "București",
        "phone": "+40213123456",
        "latitude": Decimal("44.437200"),
        "longitude": Decimal("26.152800"),
        "opening_hour": 8,
        "closing_hour": 23,
        "pitches": [
            {
                "name": "Teren Hibrid Elite",
                "surface_type": SurfaceType.HYBRID,
                "team_size_capacity": 11,
                "hourly_rate": Decimal("300.00"),
            },
            {
                "name": "Teren Sintetic Champions",
                "surface_type": SurfaceType.SYNTHETIC_3G,
                "team_size_capacity": 6,
                "hourly_rate": Decimal("220.00"),
            },
            {
                "name": "Teren Mini Sintetic",
                "surface_type": SurfaceType.SYNTHETIC_3G,
                "team_size_capacity": 5,
                "hourly_rate": Decimal("180.00"),
            },
        ],
    },
    {
        "owner_email": "owner.bucuresti@pitchup.ro",
        "name": "Sud Arena București",
        "address": "Șoseaua Vitan-Bârzești 7D, Sector 4",
        "city": "București",
        "phone": "+40744555666",
        "latitude": Decimal("44.398500"),
        "longitude": Decimal("26.136200"),
        "opening_hour": 8,
        "closing_hour": 23,
        "pitches": [
            {
                "name": "Sud Taraflex Hall",
                "surface_type": SurfaceType.INDOOR_TARAFLEX,
                "team_size_capacity": 6,
                "hourly_rate": Decimal("210.00"),
            },
            {
                "name": "Sud Synthetic Park",
                "surface_type": SurfaceType.SYNTHETIC_3G,
                "team_size_capacity": 7,
                "hourly_rate": Decimal("190.00"),
            },
        ],
    },
    {
        "owner_email": "owner.bucuresti@pitchup.ro",
        "name": "Agronomia Sports Center",
        "address": "Bulevardul Mărăști 59, Sector 1",
        "city": "București",
        "phone": "+40212240100",
        "latitude": Decimal("44.471500"),
        "longitude": Decimal("26.071200"),
        "opening_hour": 8,
        "closing_hour": 22,
        "pitches": [
            {
                "name": "Agronomia Gazon Natural",
                "surface_type": SurfaceType.NATURAL_GRASS,
                "team_size_capacity": 8,
                "hourly_rate": Decimal("250.00"),
            },
            {
                "name": "Agronomia Sintetic A",
                "surface_type": SurfaceType.SYNTHETIC_3G,
                "team_size_capacity": 6,
                "hourly_rate": Decimal("175.00"),
            },
        ],
    },
    # ── Iași (3 Venues) ──
    {
        "owner_email": "owner.iasi@pitchup.ro",
        "name": "Baza Sportivă Ciric",
        "address": "Șoseaua Ciric 1",
        "city": "Iași",
        "phone": "+40232210340",
        "latitude": Decimal("47.175600"),
        "longitude": Decimal("27.608300"),
        "opening_hour": 8,
        "closing_hour": 23,
        "pitches": [
            {
                "name": "Ciric Pădure Gazon",
                "surface_type": SurfaceType.NATURAL_GRASS,
                "team_size_capacity": 8,
                "hourly_rate": Decimal("190.00"),
            },
            {
                "name": "Ciric Sintetic 1",
                "surface_type": SurfaceType.SYNTHETIC_3G,
                "team_size_capacity": 6,
                "hourly_rate": Decimal("150.00"),
            },
        ],
    },
    {
        "owner_email": "owner.iasi@pitchup.ro",
        "name": "Tudor Arena Iași",
        "address": "Bulevardul Tudor Vladimirescu 32",
        "city": "Iași",
        "phone": "+40740112233",
        "latitude": Decimal("47.159200"),
        "longitude": Decimal("27.601500"),
        "opening_hour": 9,
        "closing_hour": 23,
        "pitches": [
            {
                "name": "Tudor Indoor Taraflex",
                "surface_type": SurfaceType.INDOOR_TARAFLEX,
                "team_size_capacity": 5,
                "hourly_rate": Decimal("185.00"),
            },
            {
                "name": "Tudor Hibrid Pro",
                "surface_type": SurfaceType.HYBRID,
                "team_size_capacity": 6,
                "hourly_rate": Decimal("210.00"),
            },
        ],
    },
    {
        "owner_email": "owner.iasi@pitchup.ro",
        "name": "Baza Copou Sport",
        "address": "Aleea Sadoveanu 12",
        "city": "Iași",
        "phone": "+40741223344",
        "latitude": Decimal("47.191500"),
        "longitude": Decimal("27.558200"),
        "opening_hour": 8,
        "closing_hour": 22,
        "pitches": [
            {
                "name": "Copou Green 11v11",
                "surface_type": SurfaceType.NATURAL_GRASS,
                "team_size_capacity": 11,
                "hourly_rate": Decimal("260.00"),
            },
            {
                "name": "Copou Sintetic Nocturnă",
                "surface_type": SurfaceType.SYNTHETIC_3G,
                "team_size_capacity": 5,
                "hourly_rate": Decimal("140.00"),
            },
        ],
    },
    # ── Brașov (3 Venues) ──
    {
        "owner_email": "owner.brasov@pitchup.ro",
        "name": "Colina Arena Brașov",
        "address": "Strada Universității 1",
        "city": "Brașov",
        "phone": "+40268410500",
        "latitude": Decimal("45.658200"),
        "longitude": Decimal("25.589100"),
        "opening_hour": 8,
        "closing_hour": 23,
        "pitches": [
            {
                "name": "Colina Sintetic 1",
                "surface_type": SurfaceType.SYNTHETIC_3G,
                "team_size_capacity": 6,
                "hourly_rate": Decimal("170.00"),
            },
            {
                "name": "Colina Taraflex Hall",
                "surface_type": SurfaceType.INDOOR_TARAFLEX,
                "team_size_capacity": 5,
                "hourly_rate": Decimal("200.00"),
            },
        ],
    },
    {
        "owner_email": "owner.brasov@pitchup.ro",
        "name": "Baza Sportivă Forex",
        "address": "Strada Hărmanului 49",
        "city": "Brașov",
        "phone": "+40268310200",
        "latitude": Decimal("45.667200"),
        "longitude": Decimal("25.632400"),
        "opening_hour": 8,
        "closing_hour": 23,
        "pitches": [
            {
                "name": "Forex Natural Pitch",
                "surface_type": SurfaceType.NATURAL_GRASS,
                "team_size_capacity": 11,
                "hourly_rate": Decimal("280.00"),
            },
            {
                "name": "Forex Hibrid Mini",
                "surface_type": SurfaceType.HYBRID,
                "team_size_capacity": 6,
                "hourly_rate": Decimal("220.00"),
            },
        ],
    },
    {
        "owner_email": "owner.brasov@pitchup.ro",
        "name": "Brașov Sports Park Bartolomeu",
        "address": "Strada Gospodarilor 15",
        "city": "Brașov",
        "phone": "+40751998877",
        "latitude": Decimal("45.663500"),
        "longitude": Decimal("25.567000"),
        "opening_hour": 9,
        "closing_hour": 23,
        "pitches": [
            {
                "name": "Bartolomeu Sintetic Pro",
                "surface_type": SurfaceType.SYNTHETIC_3G,
                "team_size_capacity": 7,
                "hourly_rate": Decimal("180.00"),
            },
            {
                "name": "Bartolomeu Indoor Taraflex",
                "surface_type": SurfaceType.INDOOR_TARAFLEX,
                "team_size_capacity": 5,
                "hourly_rate": Decimal("195.00"),
            },
        ],
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# 3. Seeding Execution Logic
# ──────────────────────────────────────────────────────────────────────────────

async def seed_users(session: AsyncSession) -> Dict[str, User]:
    """Idempotently seed user accounts."""
    user_map: Dict[str, User] = {}
    default_hash = get_password_hash("Password123!")

    for u_data in SEED_USERS:
        result = await session.execute(
            select(User).where(User.email == u_data["email"])
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                email=u_data["email"],
                hashed_password=default_hash,
                full_name=u_data["full_name"],
                phone=u_data["phone"],
                role=u_data["role"],
            )
            session.add(user)
            await session.flush()
            logger.info("Created user %s (%s)", user.email, user.role.value)
        user_map[u_data["email"]] = user

    return user_map


async def seed_venues_and_pitches(
    session: AsyncSession, user_map: Dict[str, User]
) -> Dict[Tuple[str, str], Pitch]:
    """Idempotently seed venues and their pitches."""
    pitch_map: Dict[Tuple[str, str], Pitch] = {}

    for v_data in SEED_VENUES:
        owner = user_map[v_data["owner_email"]]

        # Find or create Venue
        v_result = await session.execute(
            select(Venue).where(
                Venue.name == v_data["name"],
                Venue.city == v_data["city"],
            )
        )
        venue = v_result.scalar_one_or_none()
        if not venue:
            venue = Venue(
                owner_id=owner.id,
                name=v_data["name"],
                address=v_data["address"],
                city=v_data["city"],
                phone=v_data["phone"],
                latitude=v_data["latitude"],
                longitude=v_data["longitude"],
                opening_hour=v_data["opening_hour"],
                closing_hour=v_data["closing_hour"],
            )
            session.add(venue)
            await session.flush()
            logger.info("Created venue '%s' in %s", venue.name, venue.city)

        # Find or create Pitches
        for p_data in v_data["pitches"]:
            p_result = await session.execute(
                select(Pitch).where(
                    Pitch.venue_id == venue.id,
                    Pitch.name == p_data["name"],
                )
            )
            pitch = p_result.scalar_one_or_none()
            if not pitch:
                pitch = Pitch(
                    venue_id=venue.id,
                    name=p_data["name"],
                    surface_type=p_data["surface_type"],
                    team_size_capacity=p_data["team_size_capacity"],
                    hourly_rate=p_data["hourly_rate"],
                    is_active=True,
                )
                session.add(pitch)
                await session.flush()
                logger.info(
                    "  Added pitch '%s' (%s, %dv%d, %s RON)",
                    pitch.name,
                    pitch.surface_type.value,
                    pitch.team_size_capacity,
                    pitch.team_size_capacity,
                    pitch.hourly_rate,
                )
            pitch_map[(venue.name, pitch.name)] = pitch

    return pitch_map


async def seed_matches(
    session: AsyncSession,
    user_map: Dict[str, User],
    pitch_map: Dict[Tuple[str, str], Pitch],
) -> None:
    """Idempotently seed 4 active OPEN_LOBBY and SQUAD_CHALLENGE matches for upcoming days."""
    now = datetime.now(timezone.utc)

    matches_spec = [
        # Match 1: OPEN_LOBBY in Cluj-Napoca tomorrow 18:00
        {
            "venue_name": "Baza Sportivă Gheorgheni",
            "pitch_name": "Teren 1 Sintetic Pro",
            "organizer_email": "andrei.popa@pitchup.ro",
            "match_type": MatchType.OPEN_LOBBY,
            "target_players": 12,
            "needed_positions": ["Goalkeeper", "Midfielder"],
            "description": "Meci amical 6v6 pe sintetic pro. Căutăm portar și mijlocaș central!",
            "start_time": (now + timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0),
            "participants": [
                ("andrei.popa@pitchup.ro", ParticipantRole.ORGANIZER, TeamSide.A),
                ("marian.radu@pitchup.ro", ParticipantRole.PLAYER, TeamSide.A),
                ("bogdan.stan@pitchup.ro", ParticipantRole.PLAYER, TeamSide.B),
            ],
        },
        # Match 2: OPEN_LOBBY in Timișoara in 2 days 19:00
        {
            "venue_name": "Baza Sportivă Banat Arena",
            "pitch_name": "Teren Sintetic Banat",
            "organizer_email": "marian.radu@pitchup.ro",
            "match_type": MatchType.OPEN_LOBBY,
            "target_players": 10,
            "needed_positions": ["Defender", "Forward"],
            "description": "Fotbal de seară 5v5 la Banat Arena. Căutăm fundaș și atacant dornici de joc!",
            "start_time": (now + timedelta(days=2)).replace(hour=19, minute=0, second=0, microsecond=0),
            "participants": [
                ("marian.radu@pitchup.ro", ParticipantRole.ORGANIZER, TeamSide.A),
                ("florin.dumitru@pitchup.ro", ParticipantRole.PLAYER, TeamSide.B),
            ],
        },
        # Match 3: SQUAD_CHALLENGE in București in 3 days 20:00
        {
            "venue_name": "Arena Națională Sports Park",
            "pitch_name": "Teren Sintetic Champions",
            "organizer_email": "florin.dumitru@pitchup.ro",
            "match_type": MatchType.SQUAD_CHALLENGE,
            "target_players": 12,
            "needed_positions": ["Defender"],
            "description": "Squad Challenge 6v6! Echipa Lupii București caută adversari puternici.",
            "start_time": (now + timedelta(days=3)).replace(hour=20, minute=0, second=0, microsecond=0),
            "participants": [
                ("florin.dumitru@pitchup.ro", ParticipantRole.ORGANIZER, TeamSide.A),
                ("alex.constantin@pitchup.ro", ParticipantRole.PLAYER, TeamSide.A),
            ],
        },
        # Match 4: OPEN_LOBBY in Brașov in 1 day 20:00
        {
            "venue_name": "Colina Arena Brașov",
            "pitch_name": "Colina Taraflex Hall",
            "organizer_email": "vlad.georgescu@pitchup.ro",
            "match_type": MatchType.OPEN_LOBBY,
            "target_players": 10,
            "needed_positions": ["Goalkeeper"],
            "description": "Meci pe taraflex indoor 5v5. Avem ambele echipe aproape gata, lipsește doar un portar!",
            "start_time": (now + timedelta(days=1)).replace(hour=20, minute=0, second=0, microsecond=0),
            "participants": [
                ("vlad.georgescu@pitchup.ro", ParticipantRole.ORGANIZER, TeamSide.A),
                ("bogdan.stan@pitchup.ro", ParticipantRole.PLAYER, TeamSide.B),
                ("alex.constantin@pitchup.ro", ParticipantRole.PLAYER, TeamSide.A),
            ],
        },
    ]

    for m_spec in matches_spec:
        # Check if match already exists by description
        m_result = await session.execute(
            select(Match).where(Match.description == m_spec["description"])
        )
        existing_match = m_result.scalar_one_or_none()
        if existing_match:
            logger.info("Match already exists: '%s'", m_spec["description"][:40])
            continue

        pitch = pitch_map[(m_spec["venue_name"], m_spec["pitch_name"])]
        organizer = user_map[m_spec["organizer_email"]]
        start_time = m_spec["start_time"]
        end_time = start_time + timedelta(hours=1)

        # Create confirmed Booking for the match
        booking = Booking(
            pitch_id=pitch.id,
            booked_by_user_id=organizer.id,
            start_time=start_time,
            end_time=end_time,
            total_price=pitch.hourly_rate,
            status=BookingStatus.CONFIRMED,
        )
        session.add(booking)
        await session.flush()

        # Create Match
        match = Match(
            booking_id=booking.id,
            organizer_id=organizer.id,
            match_type=m_spec["match_type"],
            target_players=m_spec["target_players"],
            needed_positions=m_spec["needed_positions"],
            description=m_spec["description"],
            status=MatchStatus.OPEN,
            scheduled_at=start_time,
        )
        session.add(match)
        await session.flush()

        # Add participants
        for p_email, p_role, p_side in m_spec["participants"]:
            part_user = user_map[p_email]
            participant = MatchParticipant(
                match_id=match.id,
                user_id=part_user.id,
                team_side=p_side,
                role=p_role,
                status=ParticipantStatus.CONFIRMED,
            )
            session.add(participant)

        await session.flush()
        logger.info(
            "Created %s match (%s) at %s (%s)",
            match.match_type.value,
            match.scheduled_at.isoformat(),
            m_spec["venue_name"],
            m_spec["pitch_name"],
        )


async def seed_data(session: Optional[AsyncSession] = None) -> None:
    """Run full idempotent seeding of users, venues, pitches, and matches."""
    async def _do_seed(s: AsyncSession) -> None:
        user_map = await seed_users(s)
        pitch_map = await seed_venues_and_pitches(s, user_map)
        await seed_matches(s, user_map, pitch_map)

    if session is None:
        async with async_session_maker() as new_session:
            async with new_session.begin():
                await _do_seed(new_session)
    else:
        await _do_seed(session)

    logger.info("Database seeding completed successfully.")


async def main() -> None:
    """Entrypoint: Clean leftover test artifacts, then seed realistic venues/pitches/matches."""
    logger.info("Starting database cleanup & seed...")
    await clean_test_artifacts()
    await seed_data()
    logger.info("Done!")


if __name__ == "__main__":
    asyncio.run(main())


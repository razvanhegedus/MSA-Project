# Pitch Platform — Complete Architecture & Implementation Blueprint

## Section A: Complete Monorepo Directory Layout

```text
pitch-platform/
├── .cursorrules                        # AI Agent architectural rules & constraints
├── .gitignore                          # Git exclusion rules (Python, Node, Env)
├── docker-compose.yml                  # PostgreSQL 16 (with btree_gist), Backend, Frontend
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml                  # Poetry/Pip dependencies (FastAPI, SQLAlchemy[asyncio], asyncpg, pydantic, alembic, passlib, pyjwt, openai)
│   ├── alembic.ini                     # Alembic configuration
│   ├── .env.example
│   ├── alembic/
│   │   ├── env.py                      # Async SQLAlchemy Alembic migration runner
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 0001_initial_schema.py  # Contains CREATE EXTENSION btree_gist & initial DDL
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI app instantiation, CORS, Exception Handlers, Router mounting
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # Pydantic BaseSettings (Database URL, JWT secrets, LLM API keys)
│   │   │   ├── database.py             # create_async_engine, async_sessionmaker, Base declarative class
│   │   │   ├── security.py             # Bcrypt hashing, JWT encoding/decoding, SHA-256 refresh token hashing
│   │   │   └── exceptions.py           # Custom domain exceptions (SlotAlreadyBookedError, LobbyFullError, etc.)
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── dependencies.py         # get_db, get_current_user, require_role(RoleEnum)
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py           # Master API v1 router aggregator
│   │   │       ├── auth.py             # /auth/register, /auth/login, /auth/refresh, /auth/logout
│   │   │       ├── venues.py           # /venues CRUD, /venues/{id}/pitches
│   │   │       ├── bookings.py         # /pitches/{id}/availability, /bookings
│   │   │       ├── matches.py          # /matches (Open lobbies & Squad challenges), /matches/{id}/join
│   │   │       ├── tournaments.py      # /tournaments CRUD, team registration, bracket generation
│   │   │       └── ai_assistant.py     # /ai/chat (Conversational tool-calling endpoint)
│   │   │
│   │   ├── models/                     # Tier 4: SQLAlchemy 2.0 Declarative Entities
│   │   │   ├── __init__.py             # Exports all models for Alembic autogenerate
│   │   │   ├── enums.py                # Shared Python Enums mapped to PG ENUMs
│   │   │   ├── user.py                 # User, RefreshToken
│   │   │   ├── venue.py                # Venue, Pitch
│   │   │   ├── booking.py              # Booking (with GiST ExclusionConstraint)
│   │   │   ├── match.py                # Match, MatchParticipant
│   │   │   └── tournament.py           # Tournament, TournamentTeam
│   │   │
│   │   ├── schemas/                    # DTOs: Strict Pydantic v2 Request/Response Models
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── venue.py
│   │   │   ├── booking.py
│   │   │   ├── match.py
│   │   │   ├── tournament.py
│   │   │   └── ai.py
│   │   │
│   │   ├── repositories/               # Tier 3: Data Access Layer (Pure Async SQLAlchemy Queries)
│   │   │   ├── __init__.py
│   │   │   ├── user_repo.py
│   │   │   ├── venue_repo.py
│   │   │   ├── booking_repo.py
│   │   │   ├── match_repo.py
│   │   │   └── tournament_repo.py
│   │   │
│   │   └── services/                   # Tier 2: Business Logic & Transaction Orchestration
│   │       ├── __init__.py
│   │       ├── auth_service.py
│   │       ├── venue_service.py
│   │       ├── booking_service.py
│   │       ├── match_service.py
│   │       ├── tournament_service.py
│   │       └── ai_service.py           # LLM Tool Registry & Execution Loop
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                 # Async test database fixtures, test client
│       ├── test_booking_concurrency.py # Parallel asyncio.gather tests verifying GiST exclusion
│       └── test_match_concurrency.py   # Parallel tests verifying SELECT FOR UPDATE on lobby join
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.tsx                    # React 19 entry point, QueryClientProvider, RouterProvider
        ├── App.tsx                     # Root mobile-first shell, Bottom Navigation Bar, AI Floating Drawer
        ├── index.css                   # Tailwind directives
        ├── types/
        │   └── api.ts                  # TypeScript interfaces matching Pydantic v2 DTOs
        ├── api/
        │   ├── client.ts               # Axios/Fetch wrapper with automatic JWT refresh interceptor
        │   ├── bookings.ts             # React Query hooks: usePitchAvailability, useCreateBooking
        │   ├── matches.ts              # React Query hooks: useOpenMatches, useJoinMatch
        │   └── ai.ts                   # React Query mutation: useAIChat
        ├── context/
        │   └── AuthContext.tsx         # User session state & token storage
        ├── components/
        │   ├── layout/
        │   │   ├── MobileHeader.tsx
        │   │   └── BottomNav.tsx
        │   ├── pitches/
        │   │   ├── PitchCard.tsx
        │   │   └── TimeSlotSelector.tsx # Dynamic Green/Grey/Orange slot matrix
        │   ├── matches/
        │   │   ├── LobbyCard.tsx
        │   │   └── JoinMatchModal.tsx
        │   └── ai/
        │       └── AIChatDrawer.tsx    # Mobile slide-up conversational drawer
        └── pages/
            ├── HomePage.tsx            # Route: / (Venue discovery & quick filters)
            ├── PitchDetailPage.tsx     # Route: /pitches/:id (Slot selector & booking flow)
            ├── MatchesPage.tsx         # Route: /matches (Open Lobbies & Squad Challenges)
            ├── ProfilePage.tsx         # Route: /profile (User bookings & hosted matches)
            └── AIAssistantPage.tsx     # Route: /ai-assistant (Full-screen AI experience)
```

---

## Section B: Production PostgreSQL Schema (Complete DDL & SQLAlchemy 2.0 Mapping)

### B.1: Raw PostgreSQL 16+ DDL (`0001_initial_schema.sql`)

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Enum Types
CREATE TYPE user_role AS ENUM ('PLAYER', 'VENUE_OWNER', 'ADMIN');
CREATE TYPE surface_type AS ENUM ('SYNTHETIC_3G', 'INDOOR_TARAFLEX', 'NATURAL_GRASS', 'HYBRID');
CREATE TYPE booking_status AS ENUM ('PENDING', 'CONFIRMED', 'CANCELLED');
CREATE TYPE match_type AS ENUM ('OPEN_LOBBY', 'SQUAD_CHALLENGE', 'TOURNAMENT_MATCH');
CREATE TYPE match_status AS ENUM ('OPEN', 'FULL', 'CANCELLED', 'COMPLETED');
CREATE TYPE team_side AS ENUM ('A', 'B');
CREATE TYPE participant_role AS ENUM ('ORGANIZER', 'PLAYER', 'GOALKEEPER');
CREATE TYPE participant_status AS ENUM ('CONFIRMED', 'PENDING');
CREATE TYPE tournament_format AS ENUM ('SINGLE_ELIMINATION', 'GROUP_AND_KNOCKOUT');
CREATE TYPE tournament_status AS ENUM ('REGISTRATION_OPEN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');

-- 1. Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    role user_role NOT NULL DEFAULT 'PLAYER',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_users_email ON users(email);

-- 2. Refresh Tokens Table
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX ix_refresh_tokens_token_hash ON refresh_tokens(token_hash);

-- 3. Venues Table
CREATE TABLE venues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    name VARCHAR(150) NOT NULL,
    address VARCHAR(300) NOT NULL,
    city VARCHAR(100) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    latitude NUMERIC(9, 6) NOT NULL,
    longitude NUMERIC(9, 6) NOT NULL,
    opening_hour SMALLINT NOT NULL DEFAULT 8 CHECK (opening_hour >= 0 AND opening_hour <= 23),
    closing_hour SMALLINT NOT NULL DEFAULT 23 CHECK (closing_hour > opening_hour AND closing_hour <= 24),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_venues_city ON venues(city);
CREATE INDEX ix_venues_owner_id ON venues(owner_id);

-- 4. Pitches Table
CREATE TABLE pitches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    surface_type surface_type NOT NULL,
    team_size_capacity SMALLINT NOT NULL CHECK (team_size_capacity BETWEEN 4 AND 11),
    hourly_rate NUMERIC(10, 2) NOT NULL CHECK (hourly_rate >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX ix_pitches_venue_id ON pitches(venue_id);

-- 5. Bookings Table (WITH HARDWARE-LEVEL DOUBLE-BOOKING PREVENTION)
CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pitch_id UUID NOT NULL REFERENCES pitches(id) ON DELETE RESTRICT,
    booked_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    total_price NUMERIC(10, 2) NOT NULL CHECK (total_price >= 0),
    status booking_status NOT NULL DEFAULT 'CONFIRMED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_booking_valid_time_range CHECK (end_time > start_time),
    -- Half-open interval '[)' allows back-to-back bookings (e.g. 18:00-19:00 and 19:00-20:00)
    -- Partial WHERE clause ensures CANCELLED bookings do not block future reservations
    CONSTRAINT excl_bookings_no_overlap EXCLUDE USING gist (
        pitch_id WITH =,
        tstzrange(start_time, end_time, '[)') WITH &&
    ) WHERE (status != 'CANCELLED')
);
CREATE INDEX ix_bookings_pitch_time ON bookings(pitch_id, start_time, end_time);
CREATE INDEX ix_bookings_user_id ON bookings(booked_by_user_id);

-- 6. Tournaments Table
CREATE TABLE tournaments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE RESTRICT,
    organizer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    name VARCHAR(150) NOT NULL,
    format tournament_format NOT NULL DEFAULT 'SINGLE_ELIMINATION',
    max_teams SMALLINT NOT NULL CHECK (max_teams IN (4, 8, 16, 32)),
    entry_fee NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status tournament_status NOT NULL DEFAULT 'REGISTRATION_OPEN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_tournament_dates CHECK (end_date >= start_date)
);

-- 7. Tournament Teams Table
CREATE TABLE tournament_teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tournament_id UUID NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    captain_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    team_name VARCHAR(100) NOT NULL,
    seed_number SMALLINT,
    is_approved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tournament_id, team_name),
    UNIQUE (tournament_id, captain_id)
);

-- 8. Matches Table
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_id UUID NOT NULL UNIQUE REFERENCES bookings(id) ON DELETE CASCADE,
    organizer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    tournament_id UUID REFERENCES tournaments(id) ON DELETE SET NULL,
    match_type match_type NOT NULL DEFAULT 'OPEN_LOBBY',
    target_players SMALLINT NOT NULL CHECK (target_players BETWEEN 2 AND 22),
    needed_positions VARCHAR(100)[],
    description TEXT,
    status match_status NOT NULL DEFAULT 'OPEN',
    scheduled_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_matches_status_scheduled ON matches(status, scheduled_at);

-- 9. Match Participants Table
CREATE TABLE match_participants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_side team_side NOT NULL DEFAULT 'A',
    role participant_role NOT NULL DEFAULT 'PLAYER',
    status participant_status NOT NULL DEFAULT 'CONFIRMED',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (match_id, user_id)
);
CREATE INDEX ix_match_participants_match_id ON match_participants(match_id);
```

### B.2: SQLAlchemy 2.0 Declarative Models

#### `backend/app/models/enums.py`

```python
import enum

class UserRole(str, enum.Enum):
    PLAYER = "PLAYER"
    VENUE_OWNER = "VENUE_OWNER"
    ADMIN = "ADMIN"

class SurfaceType(str, enum.Enum):
    SYNTHETIC_3G = "SYNTHETIC_3G"
    INDOOR_TARAFLEX = "INDOOR_TARAFLEX"
    NATURAL_GRASS = "NATURAL_GRASS"
    HYBRID = "HYBRID"

class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"

class MatchType(str, enum.Enum):
    OPEN_LOBBY = "OPEN_LOBBY"
    SQUAD_CHALLENGE = "SQUAD_CHALLENGE"
    TOURNAMENT_MATCH = "TOURNAMENT_MATCH"

class MatchStatus(str, enum.Enum):
    OPEN = "OPEN"
    FULL = "FULL"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class TeamSide(str, enum.Enum):
    A = "A"
    B = "B"

class ParticipantRole(str, enum.Enum):
    ORGANIZER = "ORGANIZER"
    PLAYER = "PLAYER"
    GOALKEEPER = "GOALKEEPER"

class ParticipantStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    PENDING = "PENDING"

class TournamentFormat(str, enum.Enum):
    SINGLE_ELIMINATION = "SINGLE_ELIMINATION"
    GROUP_AND_KNOCKOUT = "GROUP_AND_KNOCKOUT"

class TournamentStatus(str, enum.Enum):
    REGISTRATION_OPEN = "REGISTRATION_OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
```

#### `backend/app/models/base_entities.py` (Consolidated Models File for Reference)

```python
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    String, Boolean, SmallInteger, Numeric, Text, Date, ForeignKey,
    CheckConstraint, UniqueConstraint, Index, func, text, column
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMPTZ, ARRAY, ExcludeConstraint, ENUM
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.models.enums import (
    UserRole, SurfaceType, BookingStatus, MatchType, MatchStatus,
    TeamSide, ParticipantRole, ParticipantStatus, TournamentFormat, TournamentStatus
)

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        ENUM(UserRole, name="user_role", create_type=True),
        default=UserRole.PLAYER,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), server_default=func.now(), nullable=False)

    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    venues: Mapped[List["Venue"]] = relationship(back_populates="owner")
    bookings: Mapped[List["Booking"]] = relationship(back_populates="booked_by_user")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    city: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    opening_hour: Mapped[int] = mapped_column(SmallInteger, default=8, nullable=False)
    closing_hour: Mapped[int] = mapped_column(SmallInteger, default=23, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), server_default=func.now(), nullable=False)

    owner: Mapped["User"] = relationship(back_populates="venues")
    pitches: Mapped[List["Pitch"]] = relationship(back_populates="venue", cascade="all, delete-orphan")


class Pitch(Base):
    __tablename__ = "pitches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("venues.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    surface_type: Mapped[SurfaceType] = mapped_column(
        ENUM(SurfaceType, name="surface_type", create_type=True),
        nullable=False
    )
    team_size_capacity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    venue: Mapped["Venue"] = relationship(back_populates="pitches")
    bookings: Mapped[List["Booking"]] = relationship(back_populates="pitch")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pitch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pitches.id", ondelete="RESTRICT"), nullable=False)
    booked_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    start_time: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        ENUM(BookingStatus, name="booking_status", create_type=True),
        default=BookingStatus.CONFIRMED,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), server_default=func.now(), nullable=False)

    pitch: Mapped["Pitch"] = relationship(back_populates="bookings")
    booked_by_user: Mapped["User"] = relationship(back_populates="bookings")
    match: Mapped[Optional["Match"]] = relationship(back_populates="booking", uselist=False)

    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_booking_valid_time_range"),
        ExcludeConstraint(
            (column("pitch_id"), "="),
            (func.tstzrange(column("start_time"), column("end_time"), text("'[)'")), "&&"),
            name="excl_bookings_no_overlap",
            using="gist",
            where=text("status != 'CANCELLED'")
        ),
        Index("ix_bookings_pitch_time", "pitch_id", "start_time", "end_time"),
    )


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("venues.id", ondelete="RESTRICT"), nullable=False)
    organizer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    format: Mapped[TournamentFormat] = mapped_column(
        ENUM(TournamentFormat, name="tournament_format", create_type=True),
        default=TournamentFormat.SINGLE_ELIMINATION,
        nullable=False
    )
    max_teams: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    entry_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[TournamentStatus] = mapped_column(
        ENUM(TournamentStatus, name="tournament_status", create_type=True),
        default=TournamentStatus.REGISTRATION_OPEN,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), server_default=func.now(), nullable=False)

    teams: Mapped[List["TournamentTeam"]] = relationship(back_populates="tournament", cascade="all, delete-orphan")
    matches: Mapped[List["Match"]] = relationship(back_populates="tournament")


class TournamentTeam(Base):
    __tablename__ = "tournament_teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    captain_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    team_name: Mapped[str] = mapped_column(String(100), nullable=False)
    seed_number: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), server_default=func.now(), nullable=False)

    tournament: Mapped["Tournament"] = relationship(back_populates="teams")

    __table_args__ = (
        UniqueConstraint("tournament_id", "team_name", name="uq_tournament_team_name"),
        UniqueConstraint("tournament_id", "captain_id", name="uq_tournament_captain"),
    )


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False)
    organizer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    tournament_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("tournaments.id", ondelete="SET NULL"), nullable=True)
    match_type: Mapped[MatchType] = mapped_column(
        ENUM(MatchType, name="match_type", create_type=True),
        default=MatchType.OPEN_LOBBY,
        nullable=False
    )
    target_players: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    needed_positions: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(100)), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[MatchStatus] = mapped_column(
        ENUM(MatchStatus, name="match_status", create_type=True),
        default=MatchStatus.OPEN,
        nullable=False
    )
    scheduled_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), server_default=func.now(), nullable=False)

    booking: Mapped["Booking"] = relationship(back_populates="match")
    tournament: Mapped[Optional["Tournament"]] = relationship(back_populates="matches")
    participants: Mapped[List["MatchParticipant"]] = relationship(
        back_populates="match", cascade="all, delete-orphan", lazy="selectin"
    )


class MatchParticipant(Base):
    __tablename__ = "match_participants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    team_side: Mapped[TeamSide] = mapped_column(
        ENUM(TeamSide, name="team_side", create_type=True),
        default=TeamSide.A,
        nullable=False
    )
    role: Mapped[ParticipantRole] = mapped_column(
        ENUM(ParticipantRole, name="participant_role", create_type=True),
        default=ParticipantRole.PLAYER,
        nullable=False
    )
    status: Mapped[ParticipantStatus] = mapped_column(
        ENUM(ParticipantStatus, name="participant_status", create_type=True),
        default=ParticipantStatus.CONFIRMED,
        nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), server_default=func.now(), nullable=False)

    match: Mapped["Match"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship(lazy="joined")

    __table_args__ = (
        UniqueConstraint("match_id", "user_id", name="uq_match_participant_user"),
    )
```

---

## Section C: Pydantic v2 DTO Schemas (Request / Response Contracts)

### C.1: Authentication Schemas (`backend/app/schemas/auth.py`)

```python
import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.enums import UserRole

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=150)
    phone: str = Field(..., pattern=r"^\+?[0-9\s\-]{7,20}$")
    role: UserRole = Field(default=UserRole.PLAYER)

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes in seconds

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    phone: str
    role: UserRole
    created_at: datetime
```

### C.2: Booking & Availability Schemas (`backend/app/schemas/booking.py`)

```python
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.models.enums import BookingStatus, MatchType

class PitchAvailabilityQuery(BaseModel):
    target_date: date

class TimeSlotResponse(BaseModel):
    start_time: datetime
    end_time: datetime
    status: Literal["AVAILABLE", "OCCUPIED", "OPEN_LOBBY"]
    price: Decimal
    booking_id: Optional[uuid.UUID] = None
    open_match_id: Optional[uuid.UUID] = None
    spots_left: Optional[int] = None

class BookingCreateRequest(BaseModel):
    pitch_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    # Optional inline lobby creation during checkout
    create_open_lobby: bool = False
    match_type: MatchType = MatchType.OPEN_LOBBY
    target_players: Optional[int] = Field(default=12, ge=2, le=22)
    needed_positions: Optional[list[str]] = None
    lobby_description: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_time_window(self) -> "BookingCreateRequest":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly greater than start_time")
        duration_seconds = (self.end_time - self.start_time).total_seconds()
        if duration_seconds % 3600 != 0:
            raise ValueError("Bookings must be in exact 1-hour increments")
        if duration_seconds > 14400:
            raise ValueError("Maximum single booking duration is 4 hours")
        return self

class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pitch_id: uuid.UUID
    booked_by_user_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    total_price: Decimal
    status: BookingStatus
    created_at: datetime
```

### C.3: Match Schemas (`backend/app/schemas/match.py`)

```python
import uuid
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import (
    MatchType, MatchStatus, TeamSide, ParticipantRole, ParticipantStatus
)

class MatchCreateRequest(BaseModel):
    booking_id: uuid.UUID
    match_type: MatchType = MatchType.OPEN_LOBBY
    target_players: int = Field(..., ge=2, le=22)
    needed_positions: Optional[List[str]] = Field(default_factory=list)
    description: Optional[str] = Field(default=None, max_length=500)

class MatchFilterQuery(BaseModel):
    city: Optional[str] = None
    match_type: Optional[MatchType] = None
    target_date: Optional[date] = None
    needed_role: Optional[ParticipantRole] = None

class MatchJoinRequest(BaseModel):
    team_side: TeamSide = TeamSide.A
    role: ParticipantRole = ParticipantRole.PLAYER

class MatchParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    team_side: TeamSide
    role: ParticipantRole
    status: ParticipantStatus
    joined_at: datetime

class MatchDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_id: uuid.UUID
    organizer_id: uuid.UUID
    match_type: MatchType
    target_players: int
    current_players_count: int
    needed_positions: Optional[List[str]]
    description: Optional[str]
    status: MatchStatus
    scheduled_at: datetime
    venue_name: str
    pitch_name: str
    city: str
    participants: List[MatchParticipantResponse]
```

### C.4: AI Assistant Schemas (`backend/app/schemas/ai.py`)

```python
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    history: List[ChatMessage] = Field(default_factory=list, max_length=15)
    default_city: Optional[str] = "Reșița"

class ToolCallPayload(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result_summary: List[Dict[str, Any]]

class AIChatResponse(BaseModel):
    reply: str
    invoked_tools: List[ToolCallPayload] = Field(default_factory=list)
```

---

## Section D: Core Service & Repository Business Logic

### D.1: Custom Domain Exceptions (`backend/app/core/exceptions.py`)

```python
from fastapi import HTTPException, status

class DomainError(HTTPException):
    pass

class SlotAlreadyBookedError(DomainError):
    def __init__(self, detail: str = "This pitch is already booked for the requested time window."):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class LobbyFullError(DomainError):
    def __init__(self, detail: str = "This match lobby has reached maximum player capacity."):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class AlreadyJoinedError(DomainError):
    def __init__(self, detail: str = "User is already registered in this match lobby."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class ResourceNotFoundError(DomainError):
    def __init__(self, resource: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found.")
```

### D.2: Slot Availability & Atomic Booking

#### `backend/app/repositories/booking_repo.py`

```python
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base_entities import Booking, Pitch, Venue, Match
from app.models.enums import BookingStatus, SurfaceType

class BookingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_pitch_with_venue(self, pitch_id: uuid.UUID) -> Optional[Pitch]:
        stmt = (
            select(Pitch)
            .options(selectinload(Pitch.venue))
            .where(Pitch.id == pitch_id, Pitch.is_active.is_(True))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_overlapping_bookings(
        self, pitch_id: uuid.UUID, window_start: datetime, window_end: datetime
    ) -> List[Booking]:
        """
        Uses PostgreSQL tstzrange overlap operator (&&) to fetch all active bookings
        intersecting the requested day or window.
        """
        requested_range = func.tstzrange(window_start, window_end, text("'[)'"))
        booking_range = func.tstzrange(Booking.start_time, Booking.end_time, text("'[)'"))

        stmt = (
            select(Booking)
            .options(selectinload(Booking.match).selectinload(Match.participants))
            .where(
                and_(
                    Booking.pitch_id == pitch_id,
                    Booking.status != BookingStatus.CANCELLED,
                    booking_range.op("&&")(requested_range)
                )
            )
            .order_by(Booking.start_time.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_booking(self, booking: Booking) -> Booking:
        self.session.add(booking)
        await self.session.flush()
        return booking

    async def search_available_pitches(
        self,
        city: str,
        slot_start: datetime,
        slot_end: datetime,
        surface_type: Optional[SurfaceType] = None
    ) -> List[Pitch]:
        """
        Finds all active pitches in a city that do NOT have an overlapping confirmed/pending booking
        for [slot_start, slot_end).
        """
        requested_range = func.tstzrange(slot_start, slot_end, text("'[)'"))
        booking_range = func.tstzrange(Booking.start_time, Booking.end_time, text("'[)'"))

        overlapping_subquery = (
            select(Booking.id)
            .where(
                and_(
                    Booking.pitch_id == Pitch.id,
                    Booking.status != BookingStatus.CANCELLED,
                    booking_range.op("&&")(requested_range)
                )
            )
            .exists()
        )

        conditions = [
            func.lower(Venue.city) == city.lower(),
            Pitch.is_active.is_(True),
            ~overlapping_subquery
        ]
        if surface_type:
            conditions.append(Pitch.surface_type == surface_type)

        stmt = (
            select(Pitch)
            .join(Pitch.venue)
            .options(selectinload(Pitch.venue))
            .where(and_(*conditions))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
```

#### `backend/app/services/booking_service.py`

```python
import uuid
from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import SlotAlreadyBookedError, ResourceNotFoundError
from app.models.base_entities import Booking, Match, MatchParticipant
from app.models.enums import BookingStatus, MatchStatus, ParticipantRole, ParticipantStatus, TeamSide
from app.repositories.booking_repo import BookingRepository
from app.schemas.booking import BookingCreateRequest, BookingResponse, TimeSlotResponse

class BookingService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BookingRepository(session)

    async def get_daily_availability(
        self, pitch_id: uuid.UUID, target_date: date
    ) -> List[TimeSlotResponse]:
        pitch = await self.repo.get_pitch_with_venue(pitch_id)
        if not pitch:
            raise ResourceNotFoundError("Pitch")

        venue = pitch.venue
        day_start = datetime.combine(target_date, time(hour=venue.opening_hour, minute=0), tzinfo=timezone.utc)
        if venue.closing_hour == 24:
            day_end = datetime.combine(target_date + timedelta(days=1), time(0, 0), tzinfo=timezone.utc)
        else:
            day_end = datetime.combine(target_date, time(hour=venue.closing_hour, minute=0), tzinfo=timezone.utc)

        existing_bookings = await self.repo.get_overlapping_bookings(pitch_id, day_start, day_end)

        slots: List[TimeSlotResponse] = []
        cursor = day_start
        while cursor < day_end:
            next_hour = cursor + timedelta(hours=1)
            matching_booking = next(
                (b for b in existing_bookings if b.start_time <= cursor and b.end_time >= next_hour),
                None
            )

            if not matching_booking:
                slots.append(
                    TimeSlotResponse(
                        start_time=cursor,
                        end_time=next_hour,
                        status="AVAILABLE",
                        price=pitch.hourly_rate,
                    )
                )
            elif matching_booking.match and matching_booking.match.status == MatchStatus.OPEN:
                match = matching_booking.match
                confirmed_count = sum(
                    1 for p in match.participants if p.status == ParticipantStatus.CONFIRMED
                )
                slots.append(
                    TimeSlotResponse(
                        start_time=cursor,
                        end_time=next_hour,
                        status="OPEN_LOBBY",
                        price=pitch.hourly_rate,
                        booking_id=matching_booking.id,
                        open_match_id=match.id,
                        spots_left=max(0, match.target_players - confirmed_count),
                    )
                )
            else:
                slots.append(
                    TimeSlotResponse(
                        start_time=cursor,
                        end_time=next_hour,
                        status="OCCUPIED",
                        price=pitch.hourly_rate,
                        booking_id=matching_booking.id,
                    )
                )
            cursor = next_hour

        return slots

    async def create_booking(
        self, user_id: uuid.UUID, payload: BookingCreateRequest
    ) -> BookingResponse:
        pitch = await self.repo.get_pitch_with_venue(payload.pitch_id)
        if not pitch:
            raise ResourceNotFoundError("Pitch")

        venue = pitch.venue
        start_hour = payload.start_time.hour
        end_hour = 24 if (payload.end_time.hour == 0 and payload.end_time.day > payload.start_time.day) else payload.end_time.hour

        if start_hour < venue.opening_hour or end_hour > venue.closing_hour:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Booking outside venue operating hours ({venue.opening_hour}:00 - {venue.closing_hour}:00)."
            )

        hours = Decimal(str((payload.end_time - payload.start_time).total_seconds() / 3600))
        total_price = (pitch.hourly_rate * hours).quantize(Decimal("0.01"))

        new_booking = Booking(
            pitch_id=pitch.id,
            booked_by_user_id=user_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            total_price=total_price,
            status=BookingStatus.CONFIRMED,
        )

        try:
            await self.repo.create_booking(new_booking)

            if payload.create_open_lobby:
                new_match = Match(
                    booking_id=new_booking.id,
                    organizer_id=user_id,
                    match_type=payload.match_type,
                    target_players=payload.target_players or (pitch.team_size_capacity * 2),
                    needed_positions=payload.needed_positions or [],
                    description=payload.lobby_description,
                    status=MatchStatus.OPEN,
                    scheduled_at=payload.start_time,
                )
                self.session.add(new_match)
                await self.session.flush()

                organizer_participant = MatchParticipant(
                    match_id=new_match.id,
                    user_id=user_id,
                    team_side=TeamSide.A,
                    role=ParticipantRole.ORGANIZER,
                    status=ParticipantStatus.CONFIRMED,
                )
                self.session.add(organizer_participant)

            await self.session.commit()
            await self.session.refresh(new_booking)
            return BookingResponse.model_validate(new_booking)

        except IntegrityError as exc:
            await self.session.rollback()
            orig_msg = str(exc.orig).lower() if exc.orig else ""
            # PostgreSQL SQLSTATE 23P01 = exclusion_violation
            if "excl_bookings_no_overlap" in orig_msg or "23p01" in orig_msg:
                raise SlotAlreadyBookedError() from exc
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error during booking creation."
            ) from exc
```

### D.3: Match Join / Player Capacity Locking (`SELECT ... FOR UPDATE`)

#### `backend/app/repositories/match_repo.py`

```python
import uuid
from datetime import date, datetime, time, timezone
from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base_entities import Match, MatchParticipant, Booking, Pitch, Venue
from app.models.enums import MatchStatus, ParticipantRole

class MatchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_match_for_update(self, match_id: uuid.UUID) -> Optional[Match]:
        """
        Acquires a row-level write lock (SELECT ... FOR UPDATE) on the Match row
        to serialize concurrent player join requests and prevent capacity overflow.
        """
        stmt = (
            select(Match)
            .options(
                selectinload(Match.participants).selectinload(MatchParticipant.user),
                selectinload(Match.booking).selectinload(Booking.pitch).selectinload(Pitch.venue),
            )
            .where(Match.id == match_id)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_open_lobbies(
        self,
        city: Optional[str] = None,
        needed_role: Optional[ParticipantRole] = None,
        target_date: Optional[date] = None,
    ) -> List[Match]:
        conditions = [Match.status == MatchStatus.OPEN]

        if city:
            conditions.append(func.lower(Venue.city) == city.lower())

        if target_date:
            day_start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
            day_end = datetime.combine(target_date, time.max, tzinfo=timezone.utc)
            conditions.append(and_(Match.scheduled_at >= day_start, Match.scheduled_at <= day_end))

        if needed_role:
            conditions.append(Match.needed_positions.any(needed_role.value))

        stmt = (
            select(Match)
            .join(Match.booking)
            .join(Booking.pitch)
            .join(Pitch.venue)
            .options(
                selectinload(Match.participants).selectinload(MatchParticipant.user),
                selectinload(Match.booking).selectinload(Booking.pitch).selectinload(Pitch.venue),
            )
            .where(and_(*conditions))
            .order_by(Match.scheduled_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
```

#### `backend/app/services/match_service.py`

```python
import uuid
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import LobbyFullError, AlreadyJoinedError, ResourceNotFoundError
from app.models.base_entities import Match, MatchParticipant
from app.models.enums import MatchStatus, ParticipantStatus
from app.repositories.match_repo import MatchRepository
from app.schemas.match import MatchJoinRequest, MatchDetailResponse, MatchParticipantResponse

class MatchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MatchRepository(session)

    async def join_match(
        self, match_id: uuid.UUID, user_id: uuid.UUID, payload: MatchJoinRequest
    ) -> MatchDetailResponse:
        # Step 1: Lock the match row using SELECT ... FOR UPDATE
        match = await self.repo.get_match_for_update(match_id)
        if not match:
            raise ResourceNotFoundError("Match")

        if match.status != MatchStatus.OPEN:
            raise LobbyFullError(f"Cannot join match with status {match.status.value}.")

        # Step 2: Check if user is already a participant
        if any(p.user_id == user_id for p in match.participants):
            raise AlreadyJoinedError()

        # Step 3: Count confirmed players while holding the row lock
        confirmed_players = [
            p for p in match.participants if p.status == ParticipantStatus.CONFIRMED
        ]
        if len(confirmed_players) >= match.target_players:
            match.status = MatchStatus.FULL
            await self.session.commit()
            raise LobbyFullError()

        # Step 4: Insert participant & transition lobby status if last slot was claimed
        new_participant = MatchParticipant(
            match_id=match.id,
            user_id=user_id,
            team_side=payload.team_side,
            role=payload.role,
            status=ParticipantStatus.CONFIRMED,
        )
        self.session.add(new_participant)

        if len(confirmed_players) + 1 >= match.target_players:
            match.status = MatchStatus.FULL

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AlreadyJoinedError() from exc

        # Re-fetch updated state for response serialization
        updated_match = await self.repo.get_match_for_update(match_id)
        return self._to_detail_response(updated_match)

    @staticmethod
    def _to_detail_response(match: Match) -> MatchDetailResponse:
        pitch = match.booking.pitch
        venue = pitch.venue
        confirmed_count = sum(
            1 for p in match.participants if p.status == ParticipantStatus.CONFIRMED
        )
        participants_dto = [
            MatchParticipantResponse(
                id=p.id,
                user_id=p.user_id,
                full_name=p.user.full_name if p.user else "Player",
                team_side=p.team_side,
                role=p.role,
                status=p.status,
                joined_at=p.joined_at,
            )
            for p in match.participants
        ]
        return MatchDetailResponse(
            id=match.id,
            booking_id=match.booking_id,
            organizer_id=match.organizer_id,
            match_type=match.match_type,
            target_players=match.target_players,
            current_players_count=confirmed_count,
            needed_positions=match.needed_positions,
            description=match.description,
            status=match.status,
            scheduled_at=match.scheduled_at,
            venue_name=venue.name,
            pitch_name=pitch.name,
            city=venue.city,
            participants=participants_dto,
        )
```

---

## Section E: AI Assistant Tool-Calling Architecture

### `backend/app/services/ai_service.py`

```python
import json
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, Any, List
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enums import SurfaceType, ParticipantRole
from app.repositories.booking_repo import BookingRepository
from app.repositories.match_repo import MatchRepository
from app.schemas.ai import AIChatRequest, AIChatResponse, ToolCallPayload

AI_TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_pitches",
            "description": "Search available mini-football pitches for rent in a specific city, date, and starting hour.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name (e.g., 'Reșița', 'Timișoara', 'București')"
                    },
                    "date": {
                        "type": "string",
                        "description": "Target date in ISO format YYYY-MM-DD"
                    },
                    "start_hour": {
                        "type": "integer",
                        "description": "24-hour starting hour (0-23), e.g., 20 for 20:00"
                    },
                    "surface_type": {
                        "type": "string",
                        "enum": ["SYNTHETIC_3G", "INDOOR_TARAFLEX", "NATURAL_GRASS", "HYBRID"],
                        "description": "Optional pitch surface filter"
                    }
                },
                "required": ["city", "date", "start_hour"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_open_lobbies",
            "description": "Search open mini-football match lobbies looking for extra players (+1 announcements) or goalkeepers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name where the match takes place"
                    },
                    "needed_role": {
                        "type": "string",
                        "enum": ["PLAYER", "GOALKEEPER"],
                        "description": "Optional role needed by the lobby"
                    },
                    "date": {
                        "type": "string",
                        "description": "Optional date in ISO format YYYY-MM-DD"
                    }
                },
                "required": ["city"]
            }
        }
    }
]


class AIService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.booking_repo = BookingRepository(session)
        self.match_repo = MatchRepository(session)
        # Supports OpenAI or Gemini OpenAI-compatible endpoint via base_url
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )

    async def _execute_search_pitches(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        city = args["city"]
        target_date = date.fromisoformat(args["date"])
        start_hour = int(args["start_hour"])
        surface_str = args.get("surface_type")
        surface = SurfaceType(surface_str) if surface_str else None

        slot_start = datetime.combine(target_date, time(hour=start_hour), tzinfo=timezone.utc)
        slot_end = slot_start + timedelta(hours=1)

        pitches = await self.booking_repo.search_available_pitches(
            city=city,
            slot_start=slot_start,
            slot_end=slot_end,
            surface_type=surface,
        )

        return [
            {
                "pitch_id": str(p.id),
                "pitch_name": p.name,
                "venue_name": p.venue.name,
                "address": p.venue.address,
                "surface_type": p.surface_type.value,
                "team_size": f"{p.team_size_capacity}v{p.team_size_capacity}",
                "hourly_rate": float(p.hourly_rate),
                "slot": f"{slot_start.strftime('%Y-%m-%d %H:%M')} - {slot_end.strftime('%H:%M')} UTC"
            }
            for p in pitches
        ]

    async def _execute_find_open_lobbies(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        city = args.get("city")
        role_str = args.get("needed_role")
        needed_role = ParticipantRole(role_str) if role_str else None
        date_str = args.get("date")
        target_date = date.fromisoformat(date_str) if date_str else None

        matches = await self.match_repo.find_open_lobbies(
            city=city,
            needed_role=needed_role,
            target_date=target_date,
        )

        results = []
        for m in matches:
            confirmed = sum(1 for p in m.participants if p.status.value == "CONFIRMED")
            results.append({
                "match_id": str(m.id),
                "venue_name": m.booking.pitch.venue.name,
                "pitch_name": m.booking.pitch.name,
                "scheduled_at": m.scheduled_at.isoformat(),
                "spots_left": max(0, m.target_players - confirmed),
                "needed_positions": m.needed_positions or [],
                "description": m.description or ""
            })
        return results

    async def handle_chat(self, payload: AIChatRequest) -> AIChatResponse:
        system_prompt = (
            "You are the AI Matchmaking Concierge for a mini-football booking platform. "
            f"Today's date is {date.today().isoformat()}. Default city if unspecified: {payload.default_city}. "
            "Always call the provided tools to check real-time pitch availability or open lobbies before answering. "
            "Can also help players draft catchy '+1 / Need Players' announcements."
        )

        messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        for msg in payload.history:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": payload.message})

        response = await self.client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=messages,
            tools=AI_TOOLS_SCHEMA,
            tool_choice="auto",
        )

        assistant_msg = response.choices[0].message
        invoked_tools: List[ToolCallPayload] = []

        if assistant_msg.tool_calls:
            messages.append(assistant_msg.model_dump(exclude_none=True))

            for tool_call in assistant_msg.tool_calls:
                fn_name = tool_call.function.name
                raw_args = json.loads(tool_call.function.arguments)

                if fn_name == "search_pitches":
                    tool_result = await self._execute_search_pitches(raw_args)
                elif fn_name == "find_open_lobbies":
                    tool_result = await self._execute_find_open_lobbies(raw_args)
                else:
                    tool_result = [{"error": f"Unknown tool {fn_name}"}]

                invoked_tools.append(
                    ToolCallPayload(
                        tool_name=fn_name,
                        arguments=raw_args,
                        result_summary=tool_result,
                    )
                )

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": json.dumps(tool_result),
                })

            final_response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL_NAME,
                messages=messages,
            )
            reply_text = final_response.choices[0].message.content or ""
        else:
            reply_text = assistant_msg.content or ""

        return AIChatResponse(reply=reply_text, invoked_tools=invoked_tools)
```

---

## Section F: Mobile-First React UI Architecture & Booking Flow

### F.1: Frontend Route Map (`frontend/src/App.tsx`)

| Route Path | Component | Mobile-First Purpose |
| :--- | :--- | :--- |
| `/` | `HomePage.tsx` | Geolocation/city filter bar, horizontal surface-type pills (3G, Taraflex, Grass), vertical feed of `PitchCard` items. |
| `/pitches/:id` | `PitchDetailPage.tsx` | Horizontal 7-day date strip, interactive `TimeSlotSelector` matrix (Green/Grey/Orange), sticky bottom checkout sheet with "Open Lobby (+1)" toggle. |
| `/matches` | `MatchesPage.tsx` | Segmented toggle (Need Players (+1) vs Squad vs Squad), role filter (Goalkeeper Needed), 1-tap Join Match action cards. |
| `/profile` | `ProfilePage.tsx` | Upcoming reservations, QR check-in pass, hosted lobbies management, logout. |
| `/ai-assistant` | `AIAssistantPage.tsx` | Dedicated full-screen conversational view (complementing the global floating `AIChatDrawer`). |

### F.2: TypeScript State Interfaces & TanStack Query Integration

#### `frontend/src/types/api.ts`

```typescript
export type SlotStatus = 'AVAILABLE' | 'OCCUPIED' | 'OPEN_LOBBY';

export interface TimeSlot {
  start_time: string;
  end_time: string;
  status: SlotStatus;
  price: number;
  booking_id?: string | null;
  open_match_id?: string | null;
  spots_left?: number | null;
}

export interface BookingCreatePayload {
  pitch_id: string;
  start_time: string;
  end_time: string;
  create_open_lobby: boolean;
  target_players?: number;
  needed_positions?: string[];
  lobby_description?: string;
}

export interface ToolCallPayload {
  tool_name: string;
  arguments: Record<string, unknown>;
  result_summary: Array<Record<string, any>>;
}

export interface AIChatResponse {
  reply: string;
  invoked_tools: ToolCallPayload[];
}
```

#### `frontend/src/api/bookings.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import { TimeSlot, BookingCreatePayload } from '../types/api';

export const usePitchAvailability = (pitchId: string, targetDate: string) => {
  return useQuery<TimeSlot[]>({
    queryKey: ['pitch-availability', pitchId, targetDate],
    queryFn: async () => {
      const { data } = await apiClient.get<TimeSlot[]>(
        `/v1/pitches/${pitchId}/availability`,
        { params: { target_date: targetDate } }
      );
      return data;
    },
    staleTime: 15_000,
    refetchInterval: 30_000,
  });
};

export const useCreateBooking = (pitchId: string, targetDate: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: BookingCreatePayload) => {
      const { data } = await apiClient.post('/v1/bookings', payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['pitch-availability', pitchId, targetDate],
      });
    },
  });
};
```

### F.3: Dynamic Pitch Time Slot Selector (`frontend/src/components/pitches/TimeSlotSelector.tsx`)

```tsx
import React, { useState } from 'react';
import { Users, Lock, CheckCircle2 } from 'lucide-react';
import { TimeSlot } from '../../types/api';

interface TimeSlotSelectorProps {
  slots: TimeSlot[];
  onSelectAvailableSlot: (slot: TimeSlot) => void;
  onSelectOpenLobby: (matchId: string) => void;
}

export const TimeSlotSelector: React.FC<TimeSlotSelectorProps> = ({
  slots,
  onSelectAvailableSlot,
  onSelectOpenLobby,
}) => {
  const [selectedStart, setSelectedStart] = useState<string | null>(null);

  const formatHour = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  };

  return (
    <div className="space-y-4">
      {/* Legend */}
      <div className="flex items-center justify-between text-xs font-medium text-slate-600 bg-slate-100 p-2.5 rounded-xl">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" /> Available
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-amber-500 inline-block" /> Open Lobby (+1)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-slate-300 inline-block" /> Occupied
        </span>
      </div>

      {/* 3-Column Mobile Grid */}
      <div className="grid grid-cols-3 gap-2.5">
        {slots.map((slot) => {
          const isSelected = selectedStart === slot.start_time;
          const timeLabel = `${formatHour(slot.start_time)} -${formatHour(slot.end_time)}`;

          if (slot.status === 'OCCUPIED') {
            return (
              <button
                key={slot.start_time}
                disabled
                className="flex flex-col items-center justify-center p-3 rounded-xl border border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed opacity-75"
              >
                <span className="text-xs font-semibold line-through">{timeLabel}</span>
                <span className="mt-1 flex items-center gap-1 text-[11px]">
                  <Lock className="w-3 h-3"/> Booked
                </span>
              </button>
            );
          }

          if (slot.status === 'OPEN_LOBBY') {
            return (
              <button
                key={slot.start_time}
                onClick={() => slot.open_match_id && onSelectOpenLobby(slot.open_match_id)}
                className="flex flex-col items-center justify-center p-3 rounded-xl border-2 border-amber-400 bg-amber-50 text-amber-900 active:scale-95 transition-transform"
              >
                <span className="text-xs font-bold">{timeLabel}</span>
                <span className="mt-1 flex items-center gap-1 text-[11px] font-semibold text-amber-700">
                  <Users className="w-3.5 h-3.5"/> +{slot.spots_left} needed
                </span>
              </button>
            );
          }

          // AVAILABLE
          return (
            <button
              key={slot.start_time}
              onClick={() => {
                setSelectedStart(slot.start_time);
                onSelectAvailableSlot(slot);
              }}
              className={`flex flex-col items-center justify-center p-3 rounded-xl border-2 transition-all active:scale-95 ${
                isSelected
                  ? 'border-emerald-600 bg-emerald-600 text-white shadow-md'
                  : 'border-emerald-200 bg-emerald-50/70 text-emerald-950 hover:border-emerald-400'
              }`}
            >
              <span className="text-xs font-bold">{timeLabel}</span>
              <span
                className={`mt-1 flex items-center gap-1 text-[11px] font-medium ${
                  isSelected ? 'text-emerald-100' : 'text-emerald-700'
                }`}
              >
                {isSelected && <CheckCircle2 className="w-3 h-3"/>}
                {slot.price} RON
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
```

### F.4: Floating Mobile AI Chat Drawer (`frontend/src/components/ai/AIChatDrawer.tsx`)

```tsx
import React, { useState } from 'react';
import { Sparkles, X, Send, Calendar, Users, ArrowRight } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../api/client';
import { AIChatResponse, ToolCallPayload } from '../../types/api';

interface ChatTurn {
  role: 'user' | 'assistant';
  content: string;
  tools?: ToolCallPayload[];
}

export const AIChatDrawer: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatTurn[]>([
    {
      role: 'assistant',
      content: 'Salut! Looking for a free pitch tonight or need an extra player (+1) for your squad?',
    },
  ]);
  const navigate = useNavigate();

  const chatMutation = useMutation({
    mutationFn: async (userMessage: string) => {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const { data } = await apiClient.post<AIChatResponse>('/v1/ai/chat', {
        message: userMessage,
        history,
      });
      return data;
    },
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.reply, tools: data.invoked_tools },
      ]);
    },
  });

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || chatMutation.isPending) return;
    const text = input.trim();
    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setInput('');
    chatMutation.mutate(text);
  };

  return (
    <>
      {/* Floating Action Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          aria-label="Open AI Football Concierge"
          className="fixed bottom-20 right-4 z-40 flex items-center gap-2 rounded-full bg-emerald-600 px-4 py-3.5 text-white shadow-xl hover:bg-emerald-700 active:scale-95 transition-all"
        >
          <Sparkles className="w-5 h-5"/>
          <span className="text-sm font-semibold">AI Scout</span>
        </button>
      )}

      {/* Mobile Slide-Up Bottom Sheet */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex flex-col justify-end bg-black/50 backdrop-blur-xs">
          <div className="flex h-[82vh] w-full flex-col rounded-t-3xl bg-white shadow-2xl">
            {/* Drawer Header */}
            <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700">
                  <Sparkles className="h-5 w-5"/>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">AI Matchmaking Assistant</h3>
                  <p className="text-xs text-slate-500">Live pitch & lobby search</p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              >
                <X className="h-5 w-5"/>
              </button>
            </div>

            {/* Conversation Stream */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex flex-col ${
                    msg.role === 'user' ? 'items-end' : 'items-start'
                  }`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-emerald-600 text-white rounded-br-xs'
                        : 'bg-slate-100 text-slate-800 rounded-bl-xs'
                    }`}
                  >
                    {msg.content}
                  </div>

                  {/* Interactive Tool Result Cards */}
                  {msg.tools?.map((tool, tIdx) => (
                    <div key={tIdx} className="mt-2 w-full max-w-[90%] space-y-2">
                      {tool.tool_name === 'search_pitches' &&
                        tool.result_summary.map((pitch: any) => (
                          <div
                            key={pitch.pitch_id}
                            onClick={() => {
                              setIsOpen(false);
                              navigate(`/pitches/${pitch.pitch_id}`);
                            }}
                            className="flex items-center justify-between rounded-xl border border-emerald-200 bg-emerald-50/60 p-3 cursor-pointer hover:bg-emerald-100/60"
                          >
                            <div>
                              <p className="text-xs font-bold text-emerald-950">
                                {pitch.venue_name} — {pitch.pitch_name}
                              </p>
                              <p className="text-[11px] text-emerald-700 flex items-center gap-1 mt-0.5">
                                <Calendar className="w-3 h-3"/> {pitch.slot} • {pitch.hourly_rate} RON/h
                              </p>
                            </div>
                            <ArrowRight className="w-4 h-4 text-emerald-600"/>
                          </div>
                        ))}

                      {tool.tool_name === 'find_open_lobbies' &&
                        tool.result_summary.map((lobby: any) => (
                          <div
                            key={lobby.match_id}
                            onClick={() => {
                              setIsOpen(false);
                              navigate(`/matches?highlight=${lobby.match_id}`);
                            }}
                            className="flex items-center justify-between rounded-xl border border-amber-200 bg-amber-50 p-3 cursor-pointer hover:bg-amber-100/60"
                          >
                            <div>
                              <p className="text-xs font-bold text-amber-950">
                                {lobby.venue_name} ({lobby.spots_left} spots left)
                              </p>
                              <p className="text-[11px] text-amber-800 flex items-center gap-1 mt-0.5">
                                <Users className="w-3 h-3"/> Needed:{' '}
                                {lobby.needed_positions?.join(', ') || 'Any Player'}
                              </p>
                            </div>
                            <ArrowRight className="w-4 h-4 text-amber-600"/>
                          </div>
                        ))}
                    </div>
                  ))}
                </div>
              ))}

              {chatMutation.isPending && (
                <div className="flex items-center gap-2 text-xs text-slate-400 pl-2">
                  <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
                  Checking live database slots...
                </div>
              )}
            </div>

            {/* Quick Prompt Chips */}
            <div className="flex gap-2 overflow-x-auto px-4 py-2 border-t border-slate-100 no-scrollbar">
              {[
                'Free 3G pitches tonight at 20:00',
                'Lobbies needing a Goalkeeper',
                'Write a +1 announcement for 6v6',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => setInput(suggestion)}
                  className="whitespace-nowrap rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-emerald-50 hover:text-emerald-700"
                >
                  {suggestion}
                </button>
              ))}
            </div>

            {/* Input Form */}
            <form
              onSubmit={handleSend}
              className="flex items-center gap-2 border-t border-slate-200 p-3 pb-6"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask for pitches, open lobbies, or announcements..."
                className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm focus:border-emerald-500 focus:bg-white focus:outline-none"
              />
              <button
                type="submit"
                disabled={chatMutation.isPending || !input.trim()}
                className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-white disabled:opacity-40"
              >
                <Send className="h-4 w-4"/>
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
};
```

---

## Section G: Step-by-Step Cursor Scaffolding Sequence

Follow this exact execution order when building the repository. Do not advance to the next phase until the verification gate passes.

### Phase 1: Infrastructure, Docker & Core Settings

* **Generate Files:**
  * `docker-compose.yml` (PostgreSQL 16 container on port 5432, healthcheck via `pg_isready`).
  * `backend/pyproject.toml` and `backend/.env.example`.
  * `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/exceptions.py`.
* **Verification Gate:**
  * Run `docker compose up -d db`.
  * Verify connection: `docker compose exec db psql -U postgres -c "SELECT version();"`.

### Phase 2: SQLAlchemy 2.0 Entities & Alembic GiST Migration

* **Generate Files:**
  * `backend/app/models/enums.py` and `backend/app/models/base_entities.py` (or split into `user.py`, `venue.py`, `booking.py`, `match.py`, `tournament.py` and export in `backend/app/models/__init__.py`).
  * `backend/alembic.ini`, `backend/alembic/env.py`, and `backend/alembic/versions/0001_initial_schema.py`.
  * Ensure `op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')` and `op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gist";')` are at the top of `upgrade()`.
* **Verification Gate:**
  * Run `alembic upgrade head`.
  * Verify exclusion constraint in PostgreSQL:
    `docker compose exec db psql -U postgres -d pitch_db -c "\d bookings"` — confirm `excl_bookings_no_overlap EXCLUDE USING gist (pitch_id WITH =, tstzrange(start_time, end_time, '[)'::text) WITH &&) WHERE (status <> 'CANCELLED'::booking_status)` is present.

### Phase 3: Authentication & Role-Based Security

* **Generate Files:**
  * `backend/app/core/security.py` (bcrypt password hashing, 15-min JWT access token, SHA-256 refresh token persisted in `refresh_tokens`).
  * `backend/app/schemas/auth.py`, `backend/app/repositories/user_repo.py`, `backend/app/services/auth_service.py`.
  * `backend/app/api/dependencies.py` and `backend/app/api/v1/auth.py`.
* **Verification Gate:**
  * Start FastAPI (`uvicorn app.main:app --reload`).
  * Register a `VENUE_OWNER` and a `PLAYER` via `curl -X POST http://localhost:8000/api/v1/auth/register` and verify JWT pair issuance on `/api/v1/auth/login`.

### Phase 4: Venues, Pitches & Atomic Booking Engine

* **Generate Files:**
  * `backend/app/schemas/venue.py`, `backend/app/schemas/booking.py`.
  * `backend/app/repositories/venue_repo.py`, `backend/app/repositories/booking_repo.py`.
  * `backend/app/services/venue_service.py`, `backend/app/services/booking_service.py`.
  * `backend/app/api/v1/venues.py`, `backend/app/api/v1/bookings.py`.
  * `backend/tests/test_booking_concurrency.py`.
* **Verification Gate (Hardware Race Condition Test):**
  * Run `pytest backend/tests/test_booking_concurrency.py`. The test must fire 10 concurrent `asyncio.gather` POST requests for the exact same `pitch_id` and `start_time`/`end_time` window and assert that 1 succeeds (`HTTP 201`) and 9 fail with `HTTP 409 Conflict` (`SlotAlreadyBookedError`).

### Phase 5: Matchmaking Lobbies (+1), Squad Challenges & Tournaments

* **Generate Files:**
  * `backend/app/schemas/match.py`, `backend/app/schemas/tournament.py`.
  * `backend/app/repositories/match_repo.py`, `backend/app/repositories/tournament_repo.py`.
  * `backend/app/services/match_service.py`, `backend/app/services/tournament_service.py`.
  * `backend/app/api/v1/matches.py`, `backend/app/api/v1/tournaments.py`.
  * `backend/tests/test_match_concurrency.py`.
* **Verification Gate (Lobby Capacity Lock Test):**
  * Run `pytest backend/tests/test_match_concurrency.py`. Create a match with `target_players=2` (1 organizer already confirmed = 1 spot remaining). Fire 5 concurrent join requests from 5 distinct user IDs via `asyncio.gather` and assert 1 succeeds (`HTTP 200`, match transitions to `FULL`) and 4 fail with `HTTP 409` (`LobbyFullError`).

### Phase 6: AI Assistant Tool-Calling Endpoint

* **Generate Files:**
  * `backend/app/schemas/ai.py`, `backend/app/services/ai_service.py`, `backend/app/api/v1/ai_assistant.py`.
* **Verification Gate:**
  * Execute `curl -X POST http://localhost:8000/api/v1/ai/chat -H "Content-Type: application/json" -d '{"message": "Find me a synthetic pitch in Reșița tomorrow at 20:00"}'`.
  * Verify the JSON response contains `"invoked_tools": [{"tool_name": "search_pitches", ...}]` and a natural-language summary of matching pitches.

### Phase 7: Mobile-First React 19 Frontend & End-to-End Integration

* **Generate Files:**
  * Scaffold Vite React-TS app in `frontend/`, configure Tailwind CSS & Lucide icons.
  * `frontend/src/types/api.ts`, `frontend/src/api/client.ts`, `frontend/src/api/bookings.ts`, `frontend/src/api/matches.ts`.
  * `frontend/src/components/pitches/TimeSlotSelector.tsx`, `frontend/src/components/ai/AIChatDrawer.tsx`.
  * All pages in `frontend/src/pages/` and route wiring in `frontend/src/App.tsx`.
* **Verification Gate:**
  * Run `npm run build` inside `frontend/` to verify zero TypeScript compilation errors.
  * Launch full stack via `docker compose up --build`, open `http://localhost:5173` in mobile viewport (`390x844`), book a slot with "Create Open Lobby" enabled, verify the slot turns Orange (`OPEN_LOBBY`), and query the AI Drawer for open lobbies.
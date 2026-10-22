"""0001_initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable required PostgreSQL extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gist";')

    # 2. Create Enum Types
    op.execute("CREATE TYPE user_role AS ENUM ('PLAYER', 'VENUE_OWNER', 'ADMIN');")
    op.execute("CREATE TYPE surface_type AS ENUM ('SYNTHETIC_3G', 'INDOOR_TARAFLEX', 'NATURAL_GRASS', 'HYBRID');")
    op.execute("CREATE TYPE booking_status AS ENUM ('PENDING', 'CONFIRMED', 'CANCELLED');")
    op.execute("CREATE TYPE match_type AS ENUM ('OPEN_LOBBY', 'SQUAD_CHALLENGE', 'TOURNAMENT_MATCH');")
    op.execute("CREATE TYPE match_status AS ENUM ('OPEN', 'FULL', 'CANCELLED', 'COMPLETED');")
    op.execute("CREATE TYPE team_side AS ENUM ('A', 'B');")
    op.execute("CREATE TYPE participant_role AS ENUM ('ORGANIZER', 'PLAYER', 'GOALKEEPER');")
    op.execute("CREATE TYPE participant_status AS ENUM ('CONFIRMED', 'PENDING');")
    op.execute("CREATE TYPE tournament_format AS ENUM ('SINGLE_ELIMINATION', 'GROUP_AND_KNOCKOUT');")
    op.execute("CREATE TYPE tournament_status AS ENUM ('REGISTRATION_OPEN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');")

    # 3. Users Table & Index
    op.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email VARCHAR(255) NOT NULL UNIQUE,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(150) NOT NULL,
            phone VARCHAR(30) NOT NULL,
            role user_role NOT NULL DEFAULT 'PLAYER',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX ix_users_email ON users(email);")

    # 4. Refresh Tokens Table & Indexes
    op.execute("""
        CREATE TABLE refresh_tokens (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash VARCHAR(64) NOT NULL UNIQUE,
            is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens(user_id);")
    op.execute("CREATE INDEX ix_refresh_tokens_token_hash ON refresh_tokens(token_hash);")

    # 5. Venues Table & Indexes
    op.execute("""
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
    """)
    op.execute("CREATE INDEX ix_venues_city ON venues(city);")
    op.execute("CREATE INDEX ix_venues_owner_id ON venues(owner_id);")

    # 6. Pitches Table & Index
    op.execute("""
        CREATE TABLE pitches (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            surface_type surface_type NOT NULL,
            team_size_capacity SMALLINT NOT NULL CHECK (team_size_capacity BETWEEN 4 AND 11),
            hourly_rate NUMERIC(10, 2) NOT NULL CHECK (hourly_rate >= 0),
            is_active BOOLEAN NOT NULL DEFAULT TRUE
        );
    """)
    op.execute("CREATE INDEX ix_pitches_venue_id ON pitches(venue_id);")

    # 7. Bookings Table (with PostgreSQL GiST Hardware-Level Double-Booking Prevention) & Indexes
    op.execute("""
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
            CONSTRAINT excl_bookings_no_overlap EXCLUDE USING gist (
                pitch_id WITH =,
                tstzrange(start_time, end_time, '[)') WITH &&
            ) WHERE (status != 'CANCELLED')
        );
    """)
    op.execute("CREATE INDEX ix_bookings_pitch_time ON bookings(pitch_id, start_time, end_time);")
    op.execute("CREATE INDEX ix_bookings_user_id ON bookings(booked_by_user_id);")

    # 8. Tournaments Table
    op.execute("""
        CREATE TABLE tournaments (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE RESTRICT,
            organizer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            name VARCHAR(150) NOT NULL,
            format tournament_format NOT NULL DEFAULT 'SINGLE_ELIMINATION',
            max_teams SMALLINT NOT NULL CHECK (max_teams IN (4, 8, 16, 32)),
            entry_fee NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (entry_fee >= 0),
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            status tournament_status NOT NULL DEFAULT 'REGISTRATION_OPEN',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_tournament_dates CHECK (end_date >= start_date)
        );
    """)

    # 9. Tournament Teams Table
    op.execute("""
        CREATE TABLE tournament_teams (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tournament_id UUID NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
            captain_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            team_name VARCHAR(100) NOT NULL,
            seed_number SMALLINT,
            is_approved BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_tournament_team_name UNIQUE (tournament_id, team_name),
            CONSTRAINT uq_tournament_captain UNIQUE (tournament_id, captain_id)
        );
    """)

    # 10. Matches Table & Index
    op.execute("""
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
    """)
    op.execute("CREATE INDEX ix_matches_status_scheduled ON matches(status, scheduled_at);")

    # 11. Match Participants Table & Index
    op.execute("""
        CREATE TABLE match_participants (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            match_id UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            team_side team_side NOT NULL DEFAULT 'A',
            role participant_role NOT NULL DEFAULT 'PLAYER',
            status participant_status NOT NULL DEFAULT 'CONFIRMED',
            joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_match_participant_user UNIQUE (match_id, user_id)
        );
    """)
    op.execute("CREATE INDEX ix_match_participants_match_id ON match_participants(match_id);")


def downgrade() -> None:
    # Drop tables in reverse order of foreign key dependencies
    op.execute("DROP TABLE IF EXISTS match_participants CASCADE;")
    op.execute("DROP TABLE IF EXISTS matches CASCADE;")
    op.execute("DROP TABLE IF EXISTS tournament_teams CASCADE;")
    op.execute("DROP TABLE IF EXISTS tournaments CASCADE;")
    op.execute("DROP TABLE IF EXISTS bookings CASCADE;")
    op.execute("DROP TABLE IF EXISTS pitches CASCADE;")
    op.execute("DROP TABLE IF EXISTS venues CASCADE;")
    op.execute("DROP TABLE IF EXISTS refresh_tokens CASCADE;")
    op.execute("DROP TABLE IF EXISTS users CASCADE;")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS tournament_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS tournament_format CASCADE;")
    op.execute("DROP TYPE IF EXISTS participant_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS participant_role CASCADE;")
    op.execute("DROP TYPE IF EXISTS team_side CASCADE;")
    op.execute("DROP TYPE IF EXISTS match_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS match_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS booking_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS surface_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS user_role CASCADE;")

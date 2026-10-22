import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    String, Boolean, SmallInteger, Numeric, Text, Date, ForeignKey,
    CheckConstraint, UniqueConstraint, Index, func, text, column
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP as TIMESTAMPTZ, ARRAY, ExcludeConstraint, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import (
    UserRole, SurfaceType, BookingStatus, MatchType, MatchStatus,
    TeamSide, ParticipantRole, ParticipantStatus, TournamentFormat, TournamentStatus
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        ENUM(UserRole, name="user_role", create_type=False),
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

    __table_args__ = (
        CheckConstraint("opening_hour >= 0 AND opening_hour <= 23", name="ck_venue_opening_hour"),
        CheckConstraint("closing_hour > opening_hour AND closing_hour <= 24", name="ck_venue_closing_hour"),
    )


class Pitch(Base):
    __tablename__ = "pitches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("venues.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    surface_type: Mapped[SurfaceType] = mapped_column(
        ENUM(SurfaceType, name="surface_type", create_type=False),
        nullable=False
    )
    team_size_capacity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    venue: Mapped["Venue"] = relationship(back_populates="pitches")
    bookings: Mapped[List["Booking"]] = relationship(back_populates="pitch")

    __table_args__ = (
        CheckConstraint("team_size_capacity BETWEEN 4 AND 11", name="ck_pitch_team_size_capacity"),
        CheckConstraint("hourly_rate >= 0", name="ck_pitch_hourly_rate"),
    )


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pitch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pitches.id", ondelete="RESTRICT"), nullable=False)
    booked_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    start_time: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        ENUM(BookingStatus, name="booking_status", create_type=False),
        default=BookingStatus.CONFIRMED,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), server_default=func.now(), nullable=False)

    pitch: Mapped["Pitch"] = relationship(back_populates="bookings")
    booked_by_user: Mapped["User"] = relationship(back_populates="bookings")
    match: Mapped[Optional["Match"]] = relationship(back_populates="booking", uselist=False)

    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_booking_valid_time_range"),
        CheckConstraint("total_price >= 0", name="ck_booking_total_price"),
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
        ENUM(TournamentFormat, name="tournament_format", create_type=False),
        default=TournamentFormat.SINGLE_ELIMINATION,
        nullable=False
    )
    max_teams: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    entry_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[TournamentStatus] = mapped_column(
        ENUM(TournamentStatus, name="tournament_status", create_type=False),
        default=TournamentStatus.REGISTRATION_OPEN,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), server_default=func.now(), nullable=False)

    teams: Mapped[List["TournamentTeam"]] = relationship(back_populates="tournament", cascade="all, delete-orphan")
    matches: Mapped[List["Match"]] = relationship(back_populates="tournament")

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_tournament_dates"),
        CheckConstraint("max_teams IN (4, 8, 16, 32)", name="ck_tournament_max_teams"),
        CheckConstraint("entry_fee >= 0", name="ck_tournament_entry_fee"),
    )


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
        ENUM(MatchType, name="match_type", create_type=False),
        default=MatchType.OPEN_LOBBY,
        nullable=False
    )
    target_players: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    needed_positions: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(100)), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[MatchStatus] = mapped_column(
        ENUM(MatchStatus, name="match_status", create_type=False),
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

    __table_args__ = (
        CheckConstraint("target_players BETWEEN 2 AND 22", name="ck_match_target_players"),
        Index("ix_matches_status_scheduled", "status", "scheduled_at"),
    )


class MatchParticipant(Base):
    __tablename__ = "match_participants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    team_side: Mapped[TeamSide] = mapped_column(
        ENUM(TeamSide, name="team_side", create_type=False),
        default=TeamSide.A,
        nullable=False
    )
    role: Mapped[ParticipantRole] = mapped_column(
        ENUM(ParticipantRole, name="participant_role", create_type=False),
        default=ParticipantRole.PLAYER,
        nullable=False
    )
    status: Mapped[ParticipantStatus] = mapped_column(
        ENUM(ParticipantStatus, name="participant_status", create_type=False),
        default=ParticipantStatus.CONFIRMED,
        nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ(timezone=True), server_default=func.now(), nullable=False)

    match: Mapped["Match"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship(lazy="joined")

    __table_args__ = (
        UniqueConstraint("match_id", "user_id", name="uq_match_participant_user"),
        Index("ix_match_participants_match_id", "match_id"),
    )

import uuid
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.booking_rules import BookingTimeError, get_venue_booking_window, validate_booking_time
from app.core.exceptions import SlotAlreadyBookedError, ResourceNotFoundError
from app.models.base_entities import Booking, Match, MatchParticipant, Pitch, User
from app.models.enums import (
    BookingStatus, MatchStatus, ParticipantRole, ParticipantStatus, TeamSide, UserRole
)
from app.repositories.booking_repo import BookingRepository
from app.repositories.match_repo import MatchRepository
from app.schemas.booking import BookingCreateRequest, BookingResponse, TimeSlotResponse
from app.schemas.match import MatchDetailResponse, MatchParticipantResponse


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

        return await self._daily_availability(pitch, target_date)

    async def get_move_availability(
        self, booking_id: uuid.UUID, user_id: uuid.UUID, target_date: date
    ) -> List[TimeSlotResponse]:
        booking = await self._get_owned_booking(booking_id, user_id)
        self._require_upcoming(booking)
        self._require_active_pitch(booking)
        return await self._daily_availability(
            booking.pitch, target_date, exclude_booking_id=booking.id
        )

    async def _daily_availability(
        self,
        pitch: Pitch,
        target_date: date,
        *,
        exclude_booking_id: uuid.UUID | None = None,
    ) -> List[TimeSlotResponse]:
        venue = pitch.venue
        day_start, day_end = get_venue_booking_window(
            target_date, venue.opening_hour, venue.closing_hour
        )

        existing_bookings = await self.repo.get_overlapping_bookings(
            pitch.id, day_start, day_end, exclude_booking_id=exclude_booking_id
        )

        now = datetime.now(timezone.utc)
        slots: List[TimeSlotResponse] = []
        cursor = day_start
        while cursor < day_end:
            next_hour = cursor + timedelta(hours=1)
            matching_booking = next(
                (b for b in existing_bookings if b.start_time < next_hour and b.end_time > cursor),
                None,
            )

            if cursor <= now:
                slots.append(
                    TimeSlotResponse(
                        start_time=cursor,
                        end_time=next_hour,
                        status="PAST",
                        price=pitch.hourly_rate,
                        booking_id=matching_booking.id if matching_booking else None,
                    )
                )
            elif not matching_booking:
                slots.append(
                    TimeSlotResponse(
                        start_time=cursor,
                        end_time=next_hour,
                        status="AVAILABLE",
                        price=pitch.hourly_rate,
                    )
                )
            elif (
                matching_booking.start_time <= cursor
                and matching_booking.end_time >= next_hour
                and matching_booking.match
                and matching_booking.match.status == MatchStatus.OPEN
                and matching_booking.match.scheduled_at > now
            ):
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

        try:
            start_time, end_time = validate_booking_time(
                payload.start_time, payload.end_time, venue.opening_hour, venue.closing_hour
            )
        except BookingTimeError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        hours = Decimal(str((end_time - start_time).total_seconds() / 3600))
        total_price = (pitch.hourly_rate * hours).quantize(Decimal("0.01"))

        new_booking = Booking(
            pitch_id=pitch.id,
            booked_by_user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            total_price=total_price,
            status=BookingStatus.CONFIRMED,
        )

        try:
            await self.repo.create_booking(new_booking)

            if payload.create_open_lobby:
                target_players = payload.target_players or (pitch.team_size_capacity * 2)
                new_match = Match(
                    booking_id=new_booking.id,
                    organizer_id=user_id,
                    match_type=payload.match_type,
                    target_players=target_players,
                    needed_positions=payload.needed_positions or [],
                    description=payload.lobby_description,
                    status=MatchStatus.OPEN,
                    scheduled_at=start_time,
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
            fresh_booking = await self.repo.get_booking_by_id(new_booking.id)
            return self._to_response(fresh_booking) if fresh_booking else BookingResponse.model_validate(new_booking)

        except IntegrityError as exc:
            await self.session.rollback()
            exc_str = f"{str(exc)} {str(exc.orig)}".lower()
            # PostgreSQL SQLSTATE 23P01 = exclusion_violation
            if "excl_bookings_no_overlap" in exc_str or "23p01" in exc_str or "exclusion" in exc_str:
                raise SlotAlreadyBookedError() from exc
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error during booking creation.",
            ) from exc

    async def move_booking(
        self, booking_id: uuid.UUID, user_id: uuid.UUID, requested_start: datetime
    ) -> BookingResponse:
        booking = await self._get_owned_booking(booking_id, user_id, for_update=True)
        self._require_upcoming(booking)
        self._require_active_pitch(booking)
        match = await self._lock_linked_match(booking)
        self._require_upcoming(booking)

        venue = booking.pitch.venue
        duration = booking.end_time - booking.start_time
        try:
            start_time, end_time = validate_booking_time(
                requested_start, requested_start + duration, venue.opening_hour, venue.closing_hour
            )
        except (BookingTimeError, OverflowError) as exc:
            detail = str(exc) if isinstance(exc, BookingTimeError) else "The requested time is out of range."
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc

        if start_time == booking.start_time:
            return self._to_response(booking)

        conflicts = await self.repo.get_overlapping_bookings(
            booking.pitch_id, start_time, end_time, exclude_booking_id=booking.id
        )
        if conflicts:
            raise SlotAlreadyBookedError()

        booking.start_time = start_time
        booking.end_time = end_time
        if match and match.status in (MatchStatus.OPEN, MatchStatus.FULL):
            match.scheduled_at = start_time

        try:
            await self.session.commit()
        except DBAPIError as exc:
            await self.session.rollback()
            if (
                getattr(exc.orig, "sqlstate", None) in ("23P01", "40P01")
                or "excl_bookings_no_overlap" in str(exc.orig)
            ):
                raise SlotAlreadyBookedError() from exc
            raise

        return self._to_response(booking)

    async def cancel_booking(self, booking_id: uuid.UUID, user_id: uuid.UUID) -> BookingResponse:
        booking = await self._get_owned_booking(booking_id, user_id, for_update=True)
        if booking.status == BookingStatus.CANCELLED:
            return self._to_response(booking)

        self._require_upcoming(booking)
        match = await self._lock_linked_match(booking)
        self._require_upcoming(booking)
        booking.status = BookingStatus.CANCELLED
        if match:
            match.status = MatchStatus.CANCELLED
        await self.session.commit()

        return self._to_response(booking)

    async def _get_owned_booking(
        self, booking_id: uuid.UUID, user_id: uuid.UUID, *, for_update: bool = False
    ) -> Booking:
        booking = await self.repo.get_booking_by_id(booking_id, for_update=for_update)
        if not booking:
            raise ResourceNotFoundError("Booking")
        if booking.booked_by_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the person who made this reservation can manage it.",
            )
        return booking

    async def _lock_linked_match(self, booking: Booking) -> Match | None:
        if booking.match:
            return await MatchRepository(self.session).get_match_by_booking_id(
                booking.id, for_update=True
            )
        return None

    @staticmethod
    def _require_upcoming(booking: Booking) -> None:
        if booking.status == BookingStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="This reservation is already cancelled."
            )
        if booking.start_time <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="This reservation has already started."
            )

    @staticmethod
    def _require_active_pitch(booking: Booking) -> None:
        if not booking.pitch.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This pitch is no longer accepting reservations.",
            )

    def _to_response(self, booking: Booking) -> BookingResponse:
        pitch = booking.pitch
        venue = pitch.venue if pitch else None
        match_dto = None
        open_match_id = None
        target_players = None
        current_players_count = None
        spots_left = None
        needed_positions = None
        lobby_description = None

        if booking.match:
            m = booking.match
            open_match_id = m.id
            target_players = m.target_players
            confirmed = [
                p for p in m.participants if p.status == ParticipantStatus.CONFIRMED
            ]
            current_players_count = len(confirmed)
            spots_left = max(0, m.target_players - current_players_count)
            needed_positions = m.needed_positions
            lobby_description = m.description

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
                for p in m.participants
            ]
            match_dto = MatchDetailResponse(
                id=m.id,
                booking_id=m.booking_id,
                organizer_id=m.organizer_id,
                match_type=m.match_type,
                target_players=m.target_players,
                current_players_count=current_players_count,
                needed_positions=m.needed_positions,
                description=m.description,
                status=m.status,
                scheduled_at=m.scheduled_at,
                venue_name=venue.name if venue else "",
                pitch_name=pitch.name if pitch else "",
                city=venue.city if venue else "",
                participants=participants_dto,
            )

        return BookingResponse(
            id=booking.id,
            pitch_id=booking.pitch_id,
            booked_by_user_id=booking.booked_by_user_id,
            start_time=booking.start_time,
            end_time=booking.end_time,
            total_price=booking.total_price,
            status=booking.status,
            created_at=booking.created_at,
            pitch_name=pitch.name if pitch else None,
            venue_name=venue.name if venue else None,
            city=venue.city if venue else None,
            match=match_dto,
            open_match_id=open_match_id,
            target_players=target_players,
            current_players_count=current_players_count,
            spots_left=spots_left,
            needed_positions=needed_positions,
            lobby_description=lobby_description,
        )

    async def list_user_bookings(self, user_id: uuid.UUID) -> List[BookingResponse]:
        bookings = await self.repo.list_user_bookings(user_id)
        return [self._to_response(b) for b in bookings]

    async def get_booking(self, booking_id: uuid.UUID, user: User) -> BookingResponse:
        booking = await self.repo.get_booking_by_id(booking_id)
        if not booking:
            raise ResourceNotFoundError("Booking")
        if user.role != UserRole.ADMIN and user.id not in (
            booking.booked_by_user_id, booking.pitch.venue.owner_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the booker, venue owner, or admin can view this reservation.",
            )
        return self._to_response(booking)

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
                None,
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

        start_time = payload.start_time
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        else:
            start_time = start_time.astimezone(timezone.utc)

        end_time = payload.end_time
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
        else:
            end_time = end_time.astimezone(timezone.utc)

        start_hour = start_time.hour
        end_hour = 24 if (end_time.hour == 0 and end_time.day > start_time.day) else end_time.hour

        if start_hour < venue.opening_hour or end_hour > venue.closing_hour:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Booking outside venue operating hours ({venue.opening_hour}:00 - {venue.closing_hour}:00).",
            )

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
            await self.session.refresh(new_booking)
            return BookingResponse.model_validate(new_booking)

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

    async def list_user_bookings(self, user_id: uuid.UUID) -> List[BookingResponse]:
        bookings = await self.repo.list_user_bookings(user_id)
        return [BookingResponse.model_validate(b) for b in bookings]

    async def get_booking(self, booking_id: uuid.UUID) -> BookingResponse:
        booking = await self.repo.get_booking_by_id(booking_id)
        if not booking:
            raise ResourceNotFoundError("Booking")
        return BookingResponse.model_validate(booking)

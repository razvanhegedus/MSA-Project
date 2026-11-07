import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base_entities import Booking, Pitch, Venue, Match, MatchParticipant
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
                    booking_range.op("&&")(requested_range),
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

    async def get_booking_by_id(self, booking_id: uuid.UUID) -> Optional[Booking]:
        stmt = (
            select(Booking)
            .options(
                selectinload(Booking.pitch).selectinload(Pitch.venue),
                selectinload(Booking.match).selectinload(Match.participants).selectinload(MatchParticipant.user),
            )
            .where(Booking.id == booking_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_user_bookings(self, user_id: uuid.UUID) -> List[Booking]:
        stmt = (
            select(Booking)
            .options(
                selectinload(Booking.pitch).selectinload(Pitch.venue),
                selectinload(Booking.match).selectinload(Match.participants).selectinload(MatchParticipant.user),
            )
            .where(Booking.booked_by_user_id == user_id)
            .order_by(Booking.start_time.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_available_pitches(
        self,
        city: str,
        slot_start: datetime,
        slot_end: datetime,
        surface_type: Optional[SurfaceType] = None,
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
                    booking_range.op("&&")(requested_range),
                )
            )
            .exists()
        )

        conditions = [
            func.lower(Venue.city) == city.strip().lower(),
            Pitch.is_active.is_(True),
            ~overlapping_subquery,
        ]
        if surface_type:
            conditions.append(Pitch.surface_type == surface_type)

        stmt = (
            select(Pitch)
            .join(Pitch.venue)
            .options(selectinload(Pitch.venue))
            .where(and_(*conditions))
            .order_by(Pitch.name.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

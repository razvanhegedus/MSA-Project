import uuid
from datetime import date, datetime, time, timezone
from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base_entities import Match, MatchParticipant, Booking, Pitch, Venue
from app.models.enums import MatchStatus, MatchType, ParticipantRole


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

    async def get_match_by_id(self, match_id: uuid.UUID) -> Optional[Match]:
        """
        Read-only match lookup with full relationship eager loading.
        """
        stmt = (
            select(Match)
            .options(
                selectinload(Match.participants).selectinload(MatchParticipant.user),
                selectinload(Match.booking).selectinload(Booking.pitch).selectinload(Pitch.venue),
            )
            .where(Match.id == match_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_match_by_booking_id(self, booking_id: uuid.UUID) -> Optional[Match]:
        stmt = select(Match).where(Match.booking_id == booking_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_open_lobbies(
        self,
        city: Optional[str] = None,
        needed_role: Optional[ParticipantRole] = None,
        target_date: Optional[date] = None,
        match_type: Optional[MatchType] = None,
    ) -> List[Match]:
        conditions = [Match.status == MatchStatus.OPEN]

        if city:
            conditions.append(func.lower(Venue.city) == city.strip().lower())

        if target_date:
            day_start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
            day_end = datetime.combine(target_date, time.max, tzinfo=timezone.utc)
            conditions.append(and_(Match.scheduled_at >= day_start, Match.scheduled_at <= day_end))

        if needed_role:
            conditions.append(Match.needed_positions.any(needed_role.value))

        if match_type:
            conditions.append(Match.match_type == match_type)

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

    async def create_match(self, match: Match) -> Match:
        self.session.add(match)
        await self.session.flush()
        return match

    async def add_participant(self, participant: MatchParticipant) -> MatchParticipant:
        self.session.add(participant)
        await self.session.flush()
        return participant

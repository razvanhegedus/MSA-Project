import uuid
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base_entities import Venue, Pitch


class VenueRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_venue(self, venue: Venue) -> Venue:
        self.session.add(venue)
        await self.session.flush()
        return venue

    async def get_venue_by_id(self, venue_id: uuid.UUID) -> Optional[Venue]:
        stmt = (
            select(Venue)
            .options(selectinload(Venue.pitches))
            .where(Venue.id == venue_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_venues(self, city: Optional[str] = None) -> List[Venue]:
        stmt = select(Venue).options(selectinload(Venue.pitches))
        if city:
            stmt = stmt.where(func.lower(Venue.city) == city.strip().lower())
        stmt = stmt.order_by(Venue.name.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_pitch(self, pitch: Pitch) -> Pitch:
        self.session.add(pitch)
        await self.session.flush()
        return pitch

    async def get_pitch_by_id(self, pitch_id: uuid.UUID) -> Optional[Pitch]:
        stmt = (
            select(Pitch)
            .options(selectinload(Pitch.venue))
            .where(Pitch.id == pitch_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_pitches_by_venue(self, venue_id: uuid.UUID) -> List[Pitch]:
        stmt = (
            select(Pitch)
            .where(Pitch.venue_id == venue_id)
            .order_by(Pitch.name.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

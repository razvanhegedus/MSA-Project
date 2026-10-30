import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.models.base_entities import User, Venue, Pitch
from app.models.enums import UserRole
from app.repositories.venue_repo import VenueRepository
from app.schemas.venue import VenueCreateRequest, VenueUpdateRequest, PitchCreateRequest, PitchUpdateRequest


class VenueService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = VenueRepository(session)

    async def create_venue(self, owner_id: uuid.UUID, payload: VenueCreateRequest) -> Venue:
        venue = Venue(
            owner_id=owner_id,
            name=payload.name.strip(),
            address=payload.address.strip(),
            city=payload.city.strip(),
            phone=payload.phone.strip(),
            latitude=payload.latitude,
            longitude=payload.longitude,
            opening_hour=payload.opening_hour,
            closing_hour=payload.closing_hour,
        )
        await self.repo.create_venue(venue)
        await self.session.commit()
        return await self.get_venue(venue.id)

    async def get_venue(self, venue_id: uuid.UUID) -> Venue:
        venue = await self.repo.get_venue_by_id(venue_id)
        if not venue:
            raise ResourceNotFoundError("Venue")
        return venue

    async def list_venues(self, city: Optional[str] = None) -> List[Venue]:
        return await self.repo.list_venues(city)

    async def update_venue(
        self, venue_id: uuid.UUID, user: User, payload: VenueUpdateRequest
    ) -> Venue:
        venue = await self.get_venue(venue_id)
        if venue.owner_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the venue owner or admin can update this venue.",
            )

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(venue, key, value.strip() if isinstance(value, str) else value)

        await self.session.commit()
        return await self.get_venue(venue.id)

    async def create_pitch(
        self, venue_id: uuid.UUID, user: User, payload: PitchCreateRequest
    ) -> Pitch:
        venue = await self.get_venue(venue_id)
        if venue.owner_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the venue owner or admin can add pitches to this venue.",
            )

        pitch = Pitch(
            venue_id=venue_id,
            name=payload.name.strip(),
            surface_type=payload.surface_type,
            team_size_capacity=payload.team_size_capacity,
            hourly_rate=payload.hourly_rate,
            is_active=payload.is_active,
        )
        await self.repo.create_pitch(pitch)
        await self.session.commit()
        await self.session.refresh(pitch)
        return pitch

    async def list_pitches_by_venue(self, venue_id: uuid.UUID) -> List[Pitch]:
        await self.get_venue(venue_id)
        return await self.repo.list_pitches_by_venue(venue_id)

    async def get_pitch(self, pitch_id: uuid.UUID) -> Pitch:
        pitch = await self.repo.get_pitch_by_id(pitch_id)
        if not pitch:
            raise ResourceNotFoundError("Pitch")
        return pitch

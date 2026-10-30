import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db, require_role
from app.models.base_entities import User
from app.models.enums import UserRole
from app.schemas.venue import (
    PitchCreateRequest,
    PitchResponse,
    VenueCreateRequest,
    VenueResponse,
    VenueUpdateRequest,
)
from app.services.venue_service import VenueService

router = APIRouter()


@router.post(
    "",
    response_model=VenueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new football venue",
)
async def create_venue(
    payload: VenueCreateRequest,
    current_user: User = Depends(require_role(UserRole.VENUE_OWNER, UserRole.ADMIN)),
    session: AsyncSession = Depends(get_db),
) -> VenueResponse:
    """Create a new venue belonging to the authenticated venue owner or admin."""
    service = VenueService(session)
    venue = await service.create_venue(owner_id=current_user.id, payload=payload)
    return VenueResponse.model_validate(venue)


@router.get(
    "",
    response_model=List[VenueResponse],
    status_code=status.HTTP_200_OK,
    summary="List all venues with optional city filter",
)
async def list_venues(
    city: Optional[str] = Query(default=None, description="Filter venues by city name"),
    session: AsyncSession = Depends(get_db),
) -> List[VenueResponse]:
    """Retrieve all venues, optionally filtered by city."""
    service = VenueService(session)
    venues = await service.list_venues(city=city)
    return [VenueResponse.model_validate(v) for v in venues]


@router.get(
    "/{venue_id}",
    response_model=VenueResponse,
    status_code=status.HTTP_200_OK,
    summary="Get venue details by ID",
)
async def get_venue(
    venue_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> VenueResponse:
    """Retrieve detailed information for a single venue, including all pitches."""
    service = VenueService(session)
    venue = await service.get_venue(venue_id=venue_id)
    return VenueResponse.model_validate(venue)


@router.patch(
    "/{venue_id}",
    response_model=VenueResponse,
    status_code=status.HTTP_200_OK,
    summary="Update venue details",
)
async def update_venue(
    venue_id: uuid.UUID,
    payload: VenueUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> VenueResponse:
    """Update venue parameters. Allowed only for the venue owner or admin."""
    service = VenueService(session)
    venue = await service.update_venue(venue_id=venue_id, user=current_user, payload=payload)
    return VenueResponse.model_validate(venue)


@router.post(
    "/{venue_id}/pitches",
    response_model=PitchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a pitch inside a venue",
)
async def create_pitch(
    venue_id: uuid.UUID,
    payload: PitchCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PitchResponse:
    """Add a new pitch to a venue. Allowed only for the venue owner or admin."""
    service = VenueService(session)
    pitch = await service.create_pitch(venue_id=venue_id, user=current_user, payload=payload)
    return PitchResponse.model_validate(pitch)


@router.get(
    "/{venue_id}/pitches",
    response_model=List[PitchResponse],
    status_code=status.HTTP_200_OK,
    summary="List all pitches for a venue",
)
async def list_pitches_for_venue(
    venue_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> List[PitchResponse]:
    """Retrieve all pitches associated with a specific venue."""
    service = VenueService(session)
    pitches = await service.list_pitches_by_venue(venue_id=venue_id)
    return [PitchResponse.model_validate(p) for p in pitches]


@router.get(
    "/pitches/{pitch_id}",
    response_model=PitchResponse,
    status_code=status.HTTP_200_OK,
    summary="Get pitch details by ID",
)
async def get_pitch_by_id(
    pitch_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> PitchResponse:
    """Retrieve details of a single pitch."""
    service = VenueService(session)
    pitch = await service.get_pitch(pitch_id=pitch_id)
    return PitchResponse.model_validate(pitch)

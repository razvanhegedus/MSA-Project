import uuid
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.base_entities import User
from app.core.exceptions import ResourceNotFoundError
from app.schemas.venue import PitchResponse
from app.schemas.booking import (
    BookingCreateRequest,
    BookingResponse,
    TimeSlotResponse,
)
from app.services.booking_service import BookingService

router = APIRouter()


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
    service = BookingService(session)
    pitch = await service.repo.get_pitch_with_venue(pitch_id)
    if not pitch:
        raise ResourceNotFoundError("Pitch")
    return PitchResponse.model_validate(pitch)


@router.get(
    "/pitches/{pitch_id}/availability",
    response_model=List[TimeSlotResponse],
    status_code=status.HTTP_200_OK,
    summary="Get 1-hour availability matrix for a pitch on a target date",
)
async def get_pitch_availability(
    pitch_id: uuid.UUID,
    target_date: date = Query(..., description="Target date in YYYY-MM-DD format"),
    session: AsyncSession = Depends(get_db),
) -> List[TimeSlotResponse]:
    """
    Returns the hourly slot matrix for a pitch across the venue's operating hours.
    Each slot indicates AVAILABLE, OCCUPIED, or OPEN_LOBBY (with remaining spots).
    """
    service = BookingService(session)
    return await service.get_daily_availability(pitch_id=pitch_id, target_date=target_date)


@router.post(
    "/bookings",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an atomic pitch reservation",
)
async def create_booking(
    payload: BookingCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> BookingResponse:
    """
    Creates an atomic booking protected by PostgreSQL GiST exclusion constraints.
    Supports optional inline open lobby matchmaking creation.
    """
    service = BookingService(session)
    return await service.create_booking(user_id=current_user.id, payload=payload)


@router.get(
    "/bookings/me",
    response_model=List[BookingResponse],
    status_code=status.HTTP_200_OK,
    summary="List all bookings for the authenticated user",
)
@router.get(
    "/bookings/my",
    response_model=List[BookingResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def list_my_bookings(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[BookingResponse]:
    """Retrieve all bookings reserved by the current authenticated user."""
    service = BookingService(session)
    return await service.list_user_bookings(user_id=current_user.id)


@router.get(
    "/bookings/{booking_id}",
    response_model=BookingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get details of a specific booking",
)
async def get_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> BookingResponse:
    """Retrieve details of a single booking reservation."""
    service = BookingService(session)
    return await service.get_booking(booking_id=booking_id)

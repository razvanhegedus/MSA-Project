import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.base_entities import User
from app.models.enums import MatchType, ParticipantRole
from app.schemas.match import (
    MatchCreateRequest,
    MatchDetailResponse,
    MatchJoinRequest,
    MatchUpdateRequest,
)
from app.services.match_service import MatchService

router = APIRouter()


@router.get(
    "",
    response_model=List[MatchDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Search open match lobbies",
)
async def list_matches(
    city: Optional[str] = Query(default=None, description="Filter by venue city"),
    needed_role: Optional[str] = Query(default=None, description="Filter by needed player role"),
    target_date: Optional[date] = Query(default=None, description="Filter by scheduled match date"),
    match_type: Optional[MatchType] = Query(default=None, description="Filter by match type"),
    session: AsyncSession = Depends(get_db),
) -> List[MatchDetailResponse]:
    """Retrieve open matchmaking lobbies matching the requested query filters."""
    service = MatchService(session)
    return await service.find_open_lobbies(
        city=city,
        needed_role=needed_role,
        target_date=target_date,
        match_type=match_type,
    )


@router.post(
    "",
    response_model=MatchDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a matchmaking lobby for a confirmed booking",
)
async def create_match(
    payload: MatchCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MatchDetailResponse:
    """Create a new open match lobby linked to a pitch reservation."""
    service = MatchService(session)
    return await service.create_match(user_id=current_user.id, payload=payload)


@router.get(
    "/me",
    response_model=List[MatchDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="List all matches joined or organized by the current user",
)
async def list_my_matches(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[MatchDetailResponse]:
    """Retrieve all match lobbies the authenticated user is currently participating in or organizing."""
    service = MatchService(session)
    return await service.list_user_joined_matches(user_id=current_user.id)


@router.get(
    "/{match_id}",
    response_model=MatchDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get match lobby details",
)
async def get_match_details(
    match_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> MatchDetailResponse:
    """Retrieve match lobby roster, participants, and pitch details."""
    service = MatchService(session)
    return await service.get_match(match_id=match_id)


@router.post(
    "/{match_id}/join",
    response_model=MatchDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Join an open match lobby with row-level locking",
)
async def join_match(
    match_id: uuid.UUID,
    payload: MatchJoinRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MatchDetailResponse:
    """
    Join an open matchmaking lobby.
    Serialized via PostgreSQL SELECT ... FOR UPDATE row-level locking to prevent capacity races.
    """
    service = MatchService(session)
    return await service.join_match(
        match_id=match_id, user_id=current_user.id, payload=payload
    )


@router.patch(
    "/{match_id}",
    response_model=MatchDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Update match lobby details or player requirements",
)
async def update_match(
    match_id: uuid.UUID,
    payload: MatchUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MatchDetailResponse:
    """Modify required positions, target players, or description for an organized lobby."""
    service = MatchService(session)
    return await service.update_match(
        match_id=match_id, user_id=current_user.id, payload=payload
    )

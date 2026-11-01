import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db, require_role
from app.models.base_entities import User
from app.models.enums import TournamentStatus, UserRole
from app.schemas.tournament import (
    TournamentCreateRequest,
    TournamentResponse,
    TournamentTeamRegisterRequest,
    TournamentTeamResponse,
)
from app.services.tournament_service import TournamentService

router = APIRouter()


@router.post(
    "",
    response_model=TournamentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tournament",
)
async def create_tournament(
    payload: TournamentCreateRequest,
    current_user: User = Depends(require_role(UserRole.VENUE_OWNER, UserRole.ADMIN)),
    session: AsyncSession = Depends(get_db),
) -> TournamentResponse:
    """Create a tournament hosted at a venue. Restricted to venue owners and admins."""
    service = TournamentService(session)
    return await service.create_tournament(
        organizer_id=current_user.id, user=current_user, payload=payload
    )


@router.get(
    "",
    response_model=List[TournamentResponse],
    status_code=status.HTTP_200_OK,
    summary="List all tournaments",
)
async def list_tournaments(
    venue_id: Optional[uuid.UUID] = Query(default=None, description="Filter by venue ID"),
    tournament_status: Optional[TournamentStatus] = Query(
        default=None, alias="status", description="Filter by tournament status"
    ),
    session: AsyncSession = Depends(get_db),
) -> List[TournamentResponse]:
    """List tournaments optionally filtered by venue and status."""
    service = TournamentService(session)
    return await service.list_tournaments(venue_id=venue_id, status_filter=tournament_status)


@router.get(
    "/{tournament_id}",
    response_model=TournamentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tournament details and teams",
)
async def get_tournament(
    tournament_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> TournamentResponse:
    """Retrieve details of a tournament and its registered teams."""
    service = TournamentService(session)
    return await service.get_tournament(tournament_id=tournament_id)


@router.post(
    "/{tournament_id}/teams",
    response_model=TournamentTeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a team into a tournament",
)
async def register_team(
    tournament_id: uuid.UUID,
    payload: TournamentTeamRegisterRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TournamentTeamResponse:
    """Register a team into an open tournament with current user as captain."""
    service = TournamentService(session)
    return await service.register_team(
        tournament_id=tournament_id, captain_id=current_user.id, payload=payload
    )

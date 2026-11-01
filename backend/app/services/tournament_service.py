import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.models.base_entities import Tournament, TournamentTeam, User
from app.models.enums import TournamentStatus, UserRole
from app.repositories.tournament_repo import TournamentRepository
from app.repositories.venue_repo import VenueRepository
from app.schemas.tournament import (
    TournamentCreateRequest,
    TournamentResponse,
    TournamentTeamRegisterRequest,
    TournamentTeamResponse,
)


class TournamentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TournamentRepository(session)
        self.venue_repo = VenueRepository(session)

    async def create_tournament(
        self, organizer_id: uuid.UUID, user: User, payload: TournamentCreateRequest
    ) -> TournamentResponse:
        venue = await self.venue_repo.get_venue_by_id(payload.venue_id)
        if not venue:
            raise ResourceNotFoundError("Venue")

        if user.role != UserRole.ADMIN and venue.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the venue owner or admin can create tournaments for this venue.",
            )

        tournament = Tournament(
            venue_id=payload.venue_id,
            organizer_id=organizer_id,
            name=payload.name.strip(),
            format=payload.format,
            max_teams=payload.max_teams,
            entry_fee=payload.entry_fee,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status=TournamentStatus.REGISTRATION_OPEN,
        )
        await self.repo.create_tournament(tournament)
        await self.session.commit()
        return await self.get_tournament(tournament.id)

    async def get_tournament(self, tournament_id: uuid.UUID) -> TournamentResponse:
        tournament = await self.repo.get_tournament_by_id(tournament_id)
        if not tournament:
            raise ResourceNotFoundError("Tournament")
        return self._to_response(tournament)

    async def list_tournaments(
        self,
        venue_id: Optional[uuid.UUID] = None,
        status_filter: Optional[TournamentStatus] = None,
    ) -> List[TournamentResponse]:
        tournaments = await self.repo.list_tournaments(
            venue_id=venue_id, status=status_filter
        )
        return [self._to_response(t) for t in tournaments]

    async def register_team(
        self,
        tournament_id: uuid.UUID,
        captain_id: uuid.UUID,
        payload: TournamentTeamRegisterRequest,
    ) -> TournamentTeamResponse:
        tournament = await self.repo.get_tournament_by_id(tournament_id)
        if not tournament:
            raise ResourceNotFoundError("Tournament")

        if tournament.status != TournamentStatus.REGISTRATION_OPEN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot register team: tournament status is {tournament.status.value}.",
            )

        if len(tournament.teams) >= tournament.max_teams:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tournament has reached maximum capacity of {tournament.max_teams} teams.",
            )

        existing_name = await self.repo.get_team_by_name(tournament_id, payload.team_name)
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A team with this name is already registered in this tournament.",
            )

        existing_captain = await self.repo.get_team_by_captain(tournament_id, captain_id)
        if existing_captain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already captain of a team registered in this tournament.",
            )

        seed = len(tournament.teams) + 1
        team = TournamentTeam(
            tournament_id=tournament_id,
            captain_id=captain_id,
            team_name=payload.team_name.strip(),
            seed_number=seed,
            is_approved=True,
        )
        await self.repo.register_team(team)
        await self.session.commit()
        await self.session.refresh(team)
        return TournamentTeamResponse.model_validate(team)

    @staticmethod
    def _to_response(tournament: Tournament) -> TournamentResponse:
        teams_dto = [TournamentTeamResponse.model_validate(t) for t in tournament.teams]
        return TournamentResponse(
            id=tournament.id,
            venue_id=tournament.venue_id,
            organizer_id=tournament.organizer_id,
            name=tournament.name,
            format=tournament.format,
            max_teams=tournament.max_teams,
            entry_fee=tournament.entry_fee,
            start_date=tournament.start_date,
            end_date=tournament.end_date,
            status=tournament.status,
            created_at=tournament.created_at,
            teams_count=len(tournament.teams),
            teams=teams_dto,
        )

import uuid
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base_entities import Tournament, TournamentTeam
from app.models.enums import TournamentStatus


class TournamentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_tournament(self, tournament: Tournament) -> Tournament:
        self.session.add(tournament)
        await self.session.flush()
        return tournament

    async def get_tournament_by_id(self, tournament_id: uuid.UUID) -> Optional[Tournament]:
        stmt = (
            select(Tournament)
            .options(selectinload(Tournament.teams))
            .where(Tournament.id == tournament_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_tournaments(
        self,
        venue_id: Optional[uuid.UUID] = None,
        status: Optional[TournamentStatus] = None,
    ) -> List[Tournament]:
        stmt = select(Tournament).options(selectinload(Tournament.teams))
        if venue_id:
            stmt = stmt.where(Tournament.venue_id == venue_id)
        if status:
            stmt = stmt.where(Tournament.status == status)
        stmt = stmt.order_by(Tournament.start_date.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def register_team(self, team: TournamentTeam) -> TournamentTeam:
        self.session.add(team)
        await self.session.flush()
        return team

    async def get_teams_by_tournament(self, tournament_id: uuid.UUID) -> List[TournamentTeam]:
        stmt = (
            select(TournamentTeam)
            .where(TournamentTeam.tournament_id == tournament_id)
            .order_by(TournamentTeam.seed_number.asc().nulls_last(), TournamentTeam.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_team_by_name(
        self, tournament_id: uuid.UUID, team_name: str
    ) -> Optional[TournamentTeam]:
        stmt = select(TournamentTeam).where(
            TournamentTeam.tournament_id == tournament_id,
            func.lower(TournamentTeam.team_name) == team_name.strip().lower(),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_team_by_captain(
        self, tournament_id: uuid.UUID, captain_id: uuid.UUID
    ) -> Optional[TournamentTeam]:
        stmt = select(TournamentTeam).where(
            TournamentTeam.tournament_id == tournament_id,
            TournamentTeam.captain_id == captain_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

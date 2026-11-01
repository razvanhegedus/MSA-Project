import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.models.enums import TournamentFormat, TournamentStatus


class TournamentCreateRequest(BaseModel):
    venue_id: uuid.UUID
    name: str = Field(..., min_length=2, max_length=150)
    format: TournamentFormat = TournamentFormat.SINGLE_ELIMINATION
    max_teams: int = Field(..., description="Allowed team capacities: 4, 8, 16, 32")
    entry_fee: Decimal = Field(default=Decimal("0.00"), ge=0)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_tournament_config(self) -> "TournamentCreateRequest":
        if self.max_teams not in (4, 8, 16, 32):
            raise ValueError("max_teams must be one of: 4, 8, 16, 32")
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class TournamentTeamRegisterRequest(BaseModel):
    team_name: str = Field(..., min_length=2, max_length=100)


class TournamentTeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tournament_id: uuid.UUID
    captain_id: uuid.UUID
    team_name: str
    seed_number: Optional[int] = None
    is_approved: bool
    created_at: datetime


class TournamentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    venue_id: uuid.UUID
    organizer_id: uuid.UUID
    name: str
    format: TournamentFormat
    max_teams: int
    entry_fee: Decimal
    start_date: date
    end_date: date
    status: TournamentStatus
    created_at: datetime
    teams_count: int = 0
    teams: List[TournamentTeamResponse] = Field(default_factory=list)

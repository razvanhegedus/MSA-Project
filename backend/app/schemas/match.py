import uuid
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import (
    MatchType, MatchStatus, TeamSide, ParticipantRole, ParticipantStatus
)


class MatchCreateRequest(BaseModel):
    booking_id: uuid.UUID
    match_type: MatchType = MatchType.OPEN_LOBBY
    target_players: int = Field(..., ge=2, le=22)
    needed_positions: Optional[List[str]] = Field(default_factory=list)
    description: Optional[str] = Field(default=None, max_length=500)


class MatchUpdateRequest(BaseModel):
    target_players: Optional[int] = Field(default=None, ge=2, le=22)
    needed_positions: Optional[List[str]] = None
    description: Optional[str] = Field(default=None, max_length=500)
    spots_needed: Optional[int] = Field(default=None, ge=1, le=21)


class MatchFilterQuery(BaseModel):
    city: Optional[str] = None
    match_type: Optional[MatchType] = None
    target_date: Optional[date] = None
    needed_role: Optional[ParticipantRole] = None


class MatchJoinRequest(BaseModel):
    team_side: TeamSide = TeamSide.A
    role: ParticipantRole = ParticipantRole.PLAYER


class MatchParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    team_side: TeamSide
    role: ParticipantRole
    status: ParticipantStatus
    joined_at: datetime


class MatchDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_id: uuid.UUID
    organizer_id: uuid.UUID
    match_type: MatchType
    target_players: int
    current_players_count: int
    needed_positions: Optional[List[str]] = None
    description: Optional[str] = None
    status: MatchStatus
    scheduled_at: datetime
    venue_name: str
    pitch_name: str
    city: str
    participants: List[MatchParticipantResponse] = Field(default_factory=list)

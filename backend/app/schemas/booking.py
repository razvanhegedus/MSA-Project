import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal, List
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.core.booking_rules import validate_booking_interval
from app.models.enums import BookingStatus, MatchType
from app.schemas.match import MatchDetailResponse


class PitchAvailabilityQuery(BaseModel):
    target_date: date


class TimeSlotResponse(BaseModel):
    start_time: datetime
    end_time: datetime
    status: Literal["AVAILABLE", "OCCUPIED", "OPEN_LOBBY", "PAST"]
    price: Decimal
    booking_id: Optional[uuid.UUID] = None
    open_match_id: Optional[uuid.UUID] = None
    spots_left: Optional[int] = None


class BookingCreateRequest(BaseModel):
    pitch_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    # Optional inline lobby creation during checkout
    create_open_lobby: bool = False
    match_type: MatchType = MatchType.OPEN_LOBBY
    target_players: Optional[int] = Field(default=12, ge=2, le=22)
    needed_positions: Optional[List[str]] = None
    lobby_description: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_time_window(self) -> "BookingCreateRequest":
        self.start_time, self.end_time = validate_booking_interval(self.start_time, self.end_time)
        return self


class BookingMoveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_time: datetime


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pitch_id: uuid.UUID
    booked_by_user_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    total_price: Decimal
    status: BookingStatus
    created_at: datetime

    pitch_name: Optional[str] = None
    venue_name: Optional[str] = None
    city: Optional[str] = None
    match: Optional[MatchDetailResponse] = None
    open_match_id: Optional[uuid.UUID] = None
    target_players: Optional[int] = None
    current_players_count: Optional[int] = None
    spots_left: Optional[int] = None
    needed_positions: Optional[List[str]] = None
    lobby_description: Optional[str] = None

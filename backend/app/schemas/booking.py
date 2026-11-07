import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal, List
from pydantic import BaseModel, Field, ConfigDict, model_validator
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
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly greater than start_time")
        duration_seconds = (self.end_time - self.start_time).total_seconds()
        if duration_seconds % 3600 != 0:
            raise ValueError("Bookings must be in exact 1-hour increments")
        if duration_seconds > 14400:
            raise ValueError("Maximum single booking duration is 4 hours")
        return self


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

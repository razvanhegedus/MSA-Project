import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.models.enums import SurfaceType


class VenueCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    address: str = Field(..., min_length=5, max_length=300)
    city: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., pattern=r"^\+?[0-9\s\-]{7,20}$")
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    opening_hour: int = Field(default=8, ge=0, le=23)
    closing_hour: int = Field(default=23, ge=1, le=24)

    @model_validator(mode="after")
    def validate_operating_hours(self) -> "VenueCreateRequest":
        if self.opening_hour >= self.closing_hour:
            raise ValueError("closing_hour must be strictly greater than opening_hour")
        return self


class VenueUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    address: Optional[str] = Field(default=None, min_length=5, max_length=300)
    city: Optional[str] = Field(default=None, min_length=2, max_length=100)
    phone: Optional[str] = Field(default=None, pattern=r"^\+?[0-9\s\-]{7,20}$")
    latitude: Optional[Decimal] = Field(default=None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(default=None, ge=-180, le=180)
    opening_hour: Optional[int] = Field(default=None, ge=0, le=23)
    closing_hour: Optional[int] = Field(default=None, ge=1, le=24)

    @model_validator(mode="after")
    def validate_operating_hours(self) -> "VenueUpdateRequest":
        if self.opening_hour is not None and self.closing_hour is not None:
            if self.opening_hour >= self.closing_hour:
                raise ValueError("closing_hour must be strictly greater than opening_hour")
        return self


class PitchCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    surface_type: SurfaceType
    team_size_capacity: int = Field(..., ge=4, le=11)
    hourly_rate: Decimal = Field(..., ge=0)
    is_active: bool = Field(default=True)


class PitchUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    surface_type: Optional[SurfaceType] = None
    team_size_capacity: Optional[int] = Field(default=None, ge=4, le=11)
    hourly_rate: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class PitchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    venue_id: uuid.UUID
    name: str
    surface_type: SurfaceType
    team_size_capacity: int
    hourly_rate: Decimal
    is_active: bool


class VenueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    address: str
    city: str
    phone: str
    latitude: Decimal
    longitude: Decimal
    opening_hour: int
    closing_hour: int
    created_at: datetime
    pitches: List[PitchResponse] = Field(default_factory=list)

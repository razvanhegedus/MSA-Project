import uuid
from datetime import date as dt_date, datetime as dt_datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    """A single turn in the conversation history sent by the client."""

    model_config = ConfigDict(from_attributes=True)

    role: Literal["user", "assistant", "system"]
    content: str


class AIChatRequest(BaseModel):
    """Inbound payload for the AI concierge chat endpoint."""

    model_config = ConfigDict(from_attributes=True)

    message: str = Field(..., min_length=1, max_length=1000)
    history: List[ChatMessage] = Field(default_factory=list, max_length=15)
    default_city: Optional[str] = Field(default="Reșița")


class ToolCallRecord(BaseModel):
    """Records one structured tool invocation made during the assistant's reasoning loop."""

    model_config = ConfigDict(from_attributes=True)

    tool_name: str
    arguments: Dict[str, Any]
    result_summary: Any


# Backward-compatibility alias
ToolCallPayload = ToolCallRecord


class AIChatResponse(BaseModel):
    """Outbound payload returned by the AI concierge chat endpoint."""

    model_config = ConfigDict(from_attributes=True)

    reply: str
    invoked_tools: List[ToolCallRecord] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Tool Argument & Result DTOs
# ──────────────────────────────────────────────────────────────────────────────


class SearchPitchesArgs(BaseModel):
    """Arguments for the search_pitches tool."""

    model_config = ConfigDict(from_attributes=True)

    city: str = Field(..., description="City name to search pitches in")
    surface: Optional[str] = Field(default=None, description="Optional surface filter, e.g. SYNTHETIC_3G")
    has_lights: Optional[bool] = Field(default=None, description="Optional filter for lighting availability")


class CheckSlotAvailabilityArgs(BaseModel):
    """Arguments for the check_slot_availability tool."""

    model_config = ConfigDict(from_attributes=True)

    pitch_id: uuid.UUID = Field(..., description="UUID of the pitch")
    query_date: dt_date = Field(..., description="Target date in ISO format YYYY-MM-DD")


class DraftBookingArgs(BaseModel):
    """Arguments for the draft_booking pre-validation tool."""

    model_config = ConfigDict(from_attributes=True)

    pitch_id: uuid.UUID = Field(..., description="UUID of the pitch to reserve")
    start_time: dt_datetime = Field(..., description="Desired booking start time (ISO 8601 UTC)")
    end_time: dt_datetime = Field(..., description="Desired booking end time (ISO 8601 UTC)")


class DraftBookingQuote(BaseModel):
    """Calculated non-persisted quotation for a potential booking reservation."""

    model_config = ConfigDict(from_attributes=True)

    pitch_id: uuid.UUID
    pitch_name: str
    venue_name: str
    city: str
    start_time: dt_datetime
    end_time: dt_datetime
    duration_hours: Decimal
    hourly_rate: Decimal
    total_price: Decimal
    is_available: bool
    status: str = Field(description="'AVAILABLE' if slot can be booked, or error reason")
    message: str


class FindOpenLobbiesArgs(BaseModel):
    """Arguments for the find_open_lobbies tool."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    city: str = Field(..., description="City where the match takes place")
    needed_role: Optional[str] = Field(default=None, description="Optional role needed, e.g. PLAYER, GOALKEEPER")
    date: Optional[dt_date] = Field(default=None, description="Optional target date in ISO format YYYY-MM-DD")

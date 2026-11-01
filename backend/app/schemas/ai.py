from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single turn in the conversation history sent by the client."""

    role: Literal["user", "assistant", "system"]
    content: str


class AIChatRequest(BaseModel):
    """Inbound payload for the AI concierge chat endpoint."""

    message: str = Field(..., min_length=1, max_length=1000)
    history: List[ChatMessage] = Field(default_factory=list, max_length=15)
    default_city: Optional[str] = Field(default="Reșița")


class ToolCallPayload(BaseModel):
    """Records one tool invocation made during the assistant's reasoning loop."""

    tool_name: str
    arguments: Dict[str, Any]
    result_summary: List[Dict[str, Any]]


class AIChatResponse(BaseModel):
    """Outbound payload returned by the AI concierge chat endpoint."""

    reply: str
    invoked_tools: List[ToolCallPayload] = Field(default_factory=list)

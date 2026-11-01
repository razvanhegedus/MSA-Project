"""
Tests for the AI Concierge Service (Phase 6).

All OpenAI / Gemini network calls are mocked via ``unittest.mock.AsyncMock``
so the test suite runs without a live LLM API key.

Test coverage:
  1. ``test_ai_chat_no_tool_call``       — assistant replies immediately, no tools invoked.
  2. ``test_ai_chat_search_pitches``     — assistant requests ``search_pitches`` tool;
                                           dispatcher queries DB and returns structured results.
  3. ``test_ai_chat_find_open_lobbies``  — assistant requests ``find_open_lobbies`` tool.
  4. ``test_ai_chat_check_slot_tool``    — assistant requests ``check_slot_availability`` tool.
  5. ``test_ai_chat_draft_booking_tool`` — assistant requests ``draft_booking`` tool.
  6. ``test_ai_tools_draft_booking_available`` — direct tool test: verifies price & availability.
  7. ``test_ai_tools_draft_booking_occupied``  — direct tool test: verifies overlap detection.
  8. ``test_ai_chat_unknown_tool``       — graceful handling of an unknown tool name.
  9. ``test_ai_chat_tool_loop_cap``      — loop is capped at MAX_TOOL_CYCLES.
  10. ``test_ai_chat_endpoint_requires_auth`` — POST /api/v1/ai/chat returns 401 without JWT.
  11. ``test_ai_chat_endpoint_with_auth``     — POST /api/v1/ai/chat returns 200 with valid JWT.
"""

import json
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.base_entities import (
    Booking,
    Pitch,
    User,
    Venue,
)
from app.models.enums import BookingStatus, SurfaceType, UserRole
from app.schemas.ai import AIChatRequest, AIChatResponse, ToolCallRecord
from app.services.ai_concierge_service import AIConciergeService, MAX_TOOL_CYCLES
from app.services.ai_tools import AITools


# ──────────────────────────────────────────────────────────────────────────────
# Helpers: mock OpenAI response objects
# ──────────────────────────────────────────────────────────────────────────────


def _make_openai_response(
    content: str | None = None,
    tool_calls: List[Any] | None = None,
) -> MagicMock:
    """Build a minimal mock that mimics ``openai.types.chat.ChatCompletion``."""
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls or []
    msg.model_dump.return_value = {
        "role": "assistant",
        "content": content,
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in (tool_calls or [])
        ],
    }
    response = MagicMock()
    response.choices = [MagicMock(message=msg)]
    return response


def _make_tool_call(name: str, arguments: Dict[str, Any]) -> MagicMock:
    """Build a mock tool-call object."""
    tc = MagicMock()
    tc.id = f"call_{uuid.uuid4().hex[:8]}"
    tc.function = MagicMock()
    tc.function.name = name
    tc.function.arguments = json.dumps(arguments)
    return tc


# ──────────────────────────────────────────────────────────────────────────────
# DB seed fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
async def player_user(db_session: AsyncSession) -> User:
    """Seed a PLAYER user and return the ORM object."""
    uid = uuid.uuid4().hex[:8]
    user = User(
        id=uuid.uuid4(),
        email=f"ai_player_{uid}@test.com",
        hashed_password="$2b$12$e80yqX3tS73x9BwNlI6X9e3E52z8x6YF2sU5kH5E4g8x2q9w8e7yK",
        full_name="AI Test Player",
        phone="+40700010203",
        role=UserRole.PLAYER,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def seeded_pitch(db_session: AsyncSession) -> Pitch:
    """Seed a venue owner, venue, and pitch so search and availability return results."""
    uid = uuid.uuid4().hex[:8]
    owner = User(
        id=uuid.uuid4(),
        email=f"owner_{uid}@test.com",
        hashed_password="$2b$12$e80yqX3tS73x9BwNlI6X9e3E52z8x6YF2sU5kH5E4g8x2q9w8e7yK",
        full_name="Pitch Owner",
        phone="+40711223344",
        role=UserRole.VENUE_OWNER,
    )
    db_session.add(owner)
    await db_session.flush()

    venue = Venue(
        id=uuid.uuid4(),
        owner_id=owner.id,
        name=f"AI Arena {uid}",
        address="Str. Sportului 1",
        city="Reșița",
        phone="+40711223344",
        latitude=Decimal("45.2977"),
        longitude=Decimal("21.8845"),
        opening_hour=8,
        closing_hour=23,
    )
    db_session.add(venue)
    await db_session.flush()

    pitch = Pitch(
        id=uuid.uuid4(),
        venue_id=venue.id,
        name="Pitch AI-1",
        surface_type=SurfaceType.SYNTHETIC_3G,
        team_size_capacity=6,
        hourly_rate=Decimal("150.00"),
        is_active=True,
    )
    db_session.add(pitch)
    await db_session.commit()
    await db_session.refresh(pitch)
    await db_session.refresh(venue)
    pitch.venue = venue
    return pitch


# ──────────────────────────────────────────────────────────────────────────────
# Unit tests — Direct AITools execution
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ai_tools_draft_booking_available(
    db_session: AsyncSession, seeded_pitch: Pitch
) -> None:
    """Draft booking pre-validates availability and prices without creating a DB row."""
    tools = AITools(db_session)
    target_date = date.today() + timedelta(days=2)
    start_dt = datetime.combine(target_date, time(18, 0), tzinfo=timezone.utc)
    end_dt = datetime.combine(target_date, time(20, 0), tzinfo=timezone.utc)

    quote = await tools.draft_booking(
        pitch_id=seeded_pitch.id,
        start_time=start_dt,
        end_time=end_dt,
    )

    assert quote["is_available"] is True
    assert quote["status"] == "AVAILABLE"
    assert quote["duration_hours"] == "2" or quote["duration_hours"] == 2.0 or Decimal(str(quote["duration_hours"])) == Decimal("2")
    # 2 hours * 150.00 = 300.00
    assert Decimal(str(quote["total_price"])) == Decimal("300.00")


@pytest.mark.asyncio
async def test_ai_tools_draft_booking_occupied(
    db_session: AsyncSession, seeded_pitch: Pitch, player_user: User
) -> None:
    """Draft booking detects overlapping bookings using [) half-open intervals."""
    target_date = date.today() + timedelta(days=3)
    start_dt = datetime.combine(target_date, time(19, 0), tzinfo=timezone.utc)
    end_dt = datetime.combine(target_date, time(20, 0), tzinfo=timezone.utc)

    existing_booking = Booking(
        id=uuid.uuid4(),
        pitch_id=seeded_pitch.id,
        booked_by_user_id=player_user.id,
        start_time=start_dt,
        end_time=end_dt,
        total_price=Decimal("150.00"),
        status=BookingStatus.CONFIRMED,
    )
    db_session.add(existing_booking)
    await db_session.commit()

    tools = AITools(db_session)
    quote = await tools.draft_booking(
        pitch_id=seeded_pitch.id,
        start_time=start_dt,
        end_time=end_dt,
    )

    assert quote["is_available"] is False
    assert quote["status"] == "SLOT_OCCUPIED"


# ──────────────────────────────────────────────────────────────────────────────
# Unit tests — AIConciergeService conversational turns
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ai_chat_no_tool_call(db_session: AsyncSession) -> None:
    """When the LLM returns a direct answer (no tool_calls), reply is passed through."""
    service = AIConciergeService(db_session)
    reply_text = "There are 3 pitches available in Reșița tomorrow."

    mock_create = AsyncMock(
        return_value=_make_openai_response(content=reply_text, tool_calls=[])
    )
    with patch.object(service.client.chat.completions, "create", mock_create):
        payload = AIChatRequest(message="Any pitches in Reșița tomorrow?")
        result: AIChatResponse = await service.handle_chat(payload)

    assert result.reply == reply_text
    assert result.invoked_tools == []
    assert mock_create.call_count == 1


@pytest.mark.asyncio
async def test_ai_chat_search_pitches(
    db_session: AsyncSession, seeded_pitch: Pitch
) -> None:
    """Simulates LLM requesting search_pitches tool."""
    tool_args = {
        "city": "Reșița",
        "surface": "SYNTHETIC_3G",
    }
    tool_call = _make_tool_call("search_pitches", tool_args)

    first_response = _make_openai_response(tool_calls=[tool_call])
    second_response = _make_openai_response(
        content="I found 1 synthetic pitch available in Reșița."
    )

    call_count = 0

    async def side_effect(*args: Any, **kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        return first_response if call_count == 1 else second_response

    service = AIConciergeService(db_session)
    with patch.object(service.client.chat.completions, "create", side_effect=side_effect):
        payload = AIChatRequest(message="Find me synthetic pitches in Reșița")
        result: AIChatResponse = await service.handle_chat(payload)

    assert result.reply
    assert len(result.invoked_tools) == 1
    invoked = result.invoked_tools[0]
    assert invoked.tool_name == "search_pitches"
    assert invoked.arguments["city"] == "Reșița"
    assert isinstance(invoked.result_summary, list)


@pytest.mark.asyncio
async def test_ai_chat_check_slot_tool(
    db_session: AsyncSession, seeded_pitch: Pitch
) -> None:
    """Simulates LLM requesting check_slot_availability tool."""
    tomorrow = date.today() + timedelta(days=1)
    tool_args = {
        "pitch_id": str(seeded_pitch.id),
        "query_date": tomorrow.isoformat(),
    }
    tool_call = _make_tool_call("check_slot_availability", tool_args)

    first_response = _make_openai_response(tool_calls=[tool_call])
    second_response = _make_openai_response(
        content="Slots are available throughout tomorrow afternoon."
    )

    call_count = 0

    async def side_effect(*args: Any, **kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        return first_response if call_count == 1 else second_response

    service = AIConciergeService(db_session)
    with patch.object(service.client.chat.completions, "create", side_effect=side_effect):
        payload = AIChatRequest(message="Is pitch AI-1 free tomorrow?")
        result: AIChatResponse = await service.handle_chat(payload)

    assert len(result.invoked_tools) == 1
    assert result.invoked_tools[0].tool_name == "check_slot_availability"
    assert isinstance(result.invoked_tools[0].result_summary, list)


@pytest.mark.asyncio
async def test_ai_chat_draft_booking_tool(
    db_session: AsyncSession, seeded_pitch: Pitch
) -> None:
    """Simulates LLM requesting draft_booking tool."""
    target_date = date.today() + timedelta(days=4)
    start_iso = datetime.combine(target_date, time(20, 0), tzinfo=timezone.utc).isoformat()
    end_iso = datetime.combine(target_date, time(21, 0), tzinfo=timezone.utc).isoformat()

    tool_args = {
        "pitch_id": str(seeded_pitch.id),
        "start_time": start_iso,
        "end_time": end_iso,
    }
    tool_call = _make_tool_call("draft_booking", tool_args)

    first_response = _make_openai_response(tool_calls=[tool_call])
    second_response = _make_openai_response(
        content="The total quote for this reservation is 150.00 RON."
    )

    call_count = 0

    async def side_effect(*args: Any, **kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        return first_response if call_count == 1 else second_response

    service = AIConciergeService(db_session)
    with patch.object(service.client.chat.completions, "create", side_effect=side_effect):
        payload = AIChatRequest(message="Can you draft a quote for tomorrow at 20:00?")
        result: AIChatResponse = await service.handle_chat(payload)

    assert len(result.invoked_tools) == 1
    assert result.invoked_tools[0].tool_name == "draft_booking"
    summary = result.invoked_tools[0].result_summary
    assert summary["is_available"] is True
    assert Decimal(str(summary["total_price"])) == Decimal("150.00")


@pytest.mark.asyncio
async def test_ai_chat_find_open_lobbies(db_session: AsyncSession) -> None:
    """Simulates LLM requesting find_open_lobbies tool."""
    tool_args = {"city": "Reșița"}
    tool_call = _make_tool_call("find_open_lobbies", tool_args)

    first_response = _make_openai_response(tool_calls=[tool_call])
    second_response = _make_openai_response(
        content="Checked for open lobbies in Reșița."
    )

    call_count = 0

    async def side_effect(*args: Any, **kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        return first_response if call_count == 1 else second_response

    service = AIConciergeService(db_session)
    with patch.object(service.client.chat.completions, "create", side_effect=side_effect):
        payload = AIChatRequest(message="Any open lobbies in Reșița today?")
        result: AIChatResponse = await service.handle_chat(payload)

    assert len(result.invoked_tools) == 1
    assert result.invoked_tools[0].tool_name == "find_open_lobbies"
    assert isinstance(result.invoked_tools[0].result_summary, list)


@pytest.mark.asyncio
async def test_ai_chat_unknown_tool(db_session: AsyncSession) -> None:
    """Unknown tool name returns error dict, gracefully handled."""
    tool_call = _make_tool_call("book_a_flight", {"destination": "Paris"})

    first_response = _make_openai_response(tool_calls=[tool_call])
    second_response = _make_openai_response(content="I cannot do that.")

    call_count = 0

    async def side_effect(*args: Any, **kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        return first_response if call_count == 1 else second_response

    service = AIConciergeService(db_session)
    with patch.object(service.client.chat.completions, "create", side_effect=side_effect):
        payload = AIChatRequest(message="Book me a flight to Paris")
        result: AIChatResponse = await service.handle_chat(payload)

    assert len(result.invoked_tools) == 1
    assert result.invoked_tools[0].tool_name == "book_a_flight"
    assert "error" in result.invoked_tools[0].result_summary[0]


@pytest.mark.asyncio
async def test_ai_chat_tool_loop_cap(db_session: AsyncSession) -> None:
    """Loop terminates after MAX_TOOL_CYCLES turns without infinite looping."""
    tool_call = _make_tool_call("find_open_lobbies", {"city": "Timișoara"})
    tool_response = _make_openai_response(tool_calls=[tool_call])
    final_response = _make_openai_response(content="Here are the lobbies.")

    call_count = 0

    async def side_effect(*args: Any, **kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        if "tools" not in kwargs:
            return final_response
        return tool_response

    service = AIConciergeService(db_session)
    with patch.object(service.client.chat.completions, "create", side_effect=side_effect):
        payload = AIChatRequest(message="Show me all lobbies in Timișoara")
        result: AIChatResponse = await service.handle_chat(payload)

    assert len(result.invoked_tools) == MAX_TOOL_CYCLES
    assert result.reply == "Here are the lobbies."
    assert call_count == MAX_TOOL_CYCLES + 1


# ──────────────────────────────────────────────────────────────────────────────
# Integration tests — HTTP endpoint via ASGI test client
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ai_chat_endpoint_requires_auth(client: AsyncClient) -> None:
    """POST /api/v1/ai/chat returns 401 when no token is provided."""
    response = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Any pitches available?"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ai_chat_endpoint_with_auth(
    client: AsyncClient, db_session: AsyncSession, player_user: User
) -> None:
    """POST /api/v1/ai/chat with valid JWT returns 200 and AIChatResponse."""
    token = create_access_token(subject=str(player_user.id))
    reply_text = "No pitches found for your query."

    mock_create = AsyncMock(
        return_value=_make_openai_response(content=reply_text, tool_calls=[])
    )

    with patch(
        "app.services.ai_concierge_service.AsyncOpenAI"
    ) as mock_openai_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create = mock_create
        mock_openai_cls.return_value = mock_instance

        response = await client.post(
            "/api/v1/ai/chat",
            json={"message": "Any pitches in Reșița tomorrow?"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    body = response.json()
    assert "reply" in body
    assert "invoked_tools" in body
    assert body["reply"] == reply_text
    assert body["invoked_tools"] == []

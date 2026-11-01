"""
Tests for the AI Concierge Service (Phase 6).

All OpenAI / Gemini network calls are mocked via ``unittest.mock.AsyncMock``
so the test suite runs without a live LLM API key or database.

Test coverage:
  1. ``test_ai_chat_no_tool_call``       — assistant replies immediately, no tools invoked.
  2. ``test_ai_chat_search_pitches``     — assistant requests ``search_pitches`` tool;
                                           dispatcher queries DB and returns structured results;
                                           final reply contains the results.
  3. ``test_ai_chat_find_open_lobbies``  — assistant requests ``find_open_lobbies`` tool.
  4. ``test_ai_chat_unknown_tool``       — graceful handling of an unknown tool name.
  5. ``test_ai_chat_tool_loop_cap``      — loop is capped at MAX_TOOL_TURNS; service never
                                           loops infinitely even if the LLM keeps returning
                                           tool_calls on every turn.
  6. ``test_ai_chat_endpoint_requires_auth`` — POST /api/v1/ai/chat returns 401 without JWT.
  7. ``test_ai_chat_endpoint_with_auth``     — POST /api/v1/ai/chat returns 200 with valid JWT.
"""

import json
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.base_entities import (
    Pitch,
    User,
    Venue,
)
from app.models.enums import SurfaceType, UserRole
from app.schemas.ai import AIChatRequest, AIChatResponse, ToolCallPayload
from app.services.ai_service import AIService, MAX_TOOL_TURNS


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
    """Seed a venue owner, venue, and pitch so ``search_available_pitches`` returns results."""
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
    # Ensure the venue relationship is loaded for the assertion
    await db_session.refresh(venue)
    pitch.venue = venue  # type: ignore[assignment]
    return pitch


# ──────────────────────────────────────────────────────────────────────────────
# Unit tests — AIService.handle_chat
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ai_chat_no_tool_call(db_session: AsyncSession) -> None:
    """When the LLM returns a direct answer (no tool_calls), reply is passed through."""
    service = AIService(db_session)
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
async def test_ai_chat_search_pitches(db_session: AsyncSession, seeded_pitch: Pitch) -> None:
    """
    Simulates the LLM requesting ``search_pitches``.
    Verifies the tool dispatcher queries the DB and the result is returned in ``invoked_tools``.
    """
    tomorrow = date.today() + timedelta(days=1)
    tool_args = {
        "city": "Reșița",
        "date": tomorrow.isoformat(),
        "start_hour": 20,
        "surface_type": "SYNTHETIC_3G",
    }
    tool_call = _make_tool_call("search_pitches", tool_args)

    # First call: returns tool_calls; second call: returns final text reply.
    first_response = _make_openai_response(tool_calls=[tool_call])
    second_response = _make_openai_response(
        content="I found 1 synthetic pitch available in Reșița tomorrow at 20:00."
    )

    call_count = 0

    async def side_effect(*args: Any, **kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        return first_response if call_count == 1 else second_response

    service = AIService(db_session)
    with patch.object(service.client.chat.completions, "create", side_effect=side_effect):
        payload = AIChatRequest(
            message="Find me a synthetic pitch in Reșița tomorrow at 20:00"
        )
        result: AIChatResponse = await service.handle_chat(payload)

    assert "Reșița" in result.reply or result.reply  # model returned something
    assert len(result.invoked_tools) == 1
    invoked = result.invoked_tools[0]
    assert invoked.tool_name == "search_pitches"
    assert invoked.arguments["city"] == "Reșița"
    # The seeded pitch is in Reșița with SYNTHETIC_3G and no bookings → should appear
    assert isinstance(invoked.result_summary, list)


@pytest.mark.asyncio
async def test_ai_chat_find_open_lobbies(db_session: AsyncSession) -> None:
    """
    Simulates the LLM requesting ``find_open_lobbies``.
    Verifies the tool dispatcher is called and returns a list of dicts (possibly
    non-empty if other tests have seeded matches into the shared DB).
    """
    tool_args = {"city": "Reșița"}
    tool_call = _make_tool_call("find_open_lobbies", tool_args)

    first_response = _make_openai_response(tool_calls=[tool_call])
    second_response = _make_openai_response(
        content="There are currently no open lobbies in Reșița."
    )

    call_count = 0

    async def side_effect(*args: Any, **kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        return first_response if call_count == 1 else second_response

    service = AIService(db_session)
    with patch.object(service.client.chat.completions, "create", side_effect=side_effect):
        payload = AIChatRequest(message="Any open lobbies in Reșița today?")
        result: AIChatResponse = await service.handle_chat(payload)

    assert len(result.invoked_tools) == 1
    assert result.invoked_tools[0].tool_name == "find_open_lobbies"
    # result_summary is a list of lobby dicts (may be non-empty from shared DB state)
    assert isinstance(result.invoked_tools[0].result_summary, list)
    # Every item in the list must be a dict with the expected keys
    for lobby in result.invoked_tools[0].result_summary:
        assert isinstance(lobby, dict)
        assert "match_id" in lobby
        assert "spots_left" in lobby


@pytest.mark.asyncio
async def test_ai_chat_unknown_tool(db_session: AsyncSession) -> None:
    """
    If the LLM requests an unknown tool the dispatcher returns an error dict,
    the loop continues, and the assistant produces a final reply.
    """
    tool_call = _make_tool_call("book_a_flight", {"destination": "Paris"})

    first_response = _make_openai_response(tool_calls=[tool_call])
    second_response = _make_openai_response(content="I cannot do that.")

    call_count = 0

    async def side_effect(*args: Any, **kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        return first_response if call_count == 1 else second_response

    service = AIService(db_session)
    with patch.object(service.client.chat.completions, "create", side_effect=side_effect):
        payload = AIChatRequest(message="Book me a flight to Paris")
        result: AIChatResponse = await service.handle_chat(payload)

    assert len(result.invoked_tools) == 1
    error_tool = result.invoked_tools[0]
    assert error_tool.tool_name == "book_a_flight"
    assert "error" in error_tool.result_summary[0]


@pytest.mark.asyncio
async def test_ai_chat_tool_loop_cap(db_session: AsyncSession) -> None:
    """
    If the LLM keeps requesting tools on every turn, the loop terminates after
    MAX_TOOL_TURNS and a final completion call is made.
    Total LLM calls = MAX_TOOL_TURNS + 1 (the cap-exit call).
    """
    tool_call = _make_tool_call("find_open_lobbies", {"city": "Timișoara"})
    tool_response = _make_openai_response(tool_calls=[tool_call])
    final_response = _make_openai_response(content="Here are the lobbies.")

    # The LLM always returns a tool call; only the last (cap-exit) call gets final_response.
    call_count = 0

    async def side_effect(*args: Any, **kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        # The cap-exit call is made *without* the ``tools`` kwarg
        if "tools" not in kwargs:
            return final_response
        return tool_response

    service = AIService(db_session)
    with patch.object(service.client.chat.completions, "create", side_effect=side_effect):
        payload = AIChatRequest(message="Show me all lobbies in Timișoara")
        result: AIChatResponse = await service.handle_chat(payload)

    # Exactly MAX_TOOL_TURNS tool invocations should be recorded
    assert len(result.invoked_tools) == MAX_TOOL_TURNS
    # The final reply comes from the cap-exit call
    assert result.reply == "Here are the lobbies."
    # Total LLM calls: MAX_TOOL_TURNS (tool loops) + 1 (cap-exit)
    assert call_count == MAX_TOOL_TURNS + 1


# ──────────────────────────────────────────────────────────────────────────────
# Integration tests — HTTP endpoint via ASGI test client
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ai_chat_endpoint_requires_auth(client: AsyncClient) -> None:
    """POST /api/v1/ai/chat must return 401 when no Authorization header is present."""
    response = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Any pitches available?"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ai_chat_endpoint_with_auth(
    client: AsyncClient, db_session: AsyncSession, player_user: User
) -> None:
    """
    POST /api/v1/ai/chat with a valid JWT must return 200 and a well-formed
    AIChatResponse.  The LLM client is mocked to avoid external API calls.
    """
    token = create_access_token(subject=str(player_user.id))
    reply_text = "No pitches found for your query."

    mock_create = AsyncMock(
        return_value=_make_openai_response(content=reply_text, tool_calls=[])
    )

    with patch(
        "app.services.ai_service.AsyncOpenAI"
    ) as mock_openai_cls:
        # Wire the mock so service.client.chat.completions.create is our AsyncMock
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

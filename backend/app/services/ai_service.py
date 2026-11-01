"""
AI Concierge Service — Orchestrates the OpenAI-compatible tool-calling loop.

Uses the ``openai`` Python SDK with a configurable ``base_url`` so the same
code works against OpenAI *or* Google Gemini's OpenAI-compatibility layer
(https://generativelanguage.googleapis.com/v1beta/openai/).

Tool loop is capped at MAX_TOOL_TURNS (5) to prevent infinite cycles.
"""

import json
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enums import ParticipantRole, SurfaceType
from app.repositories.booking_repo import BookingRepository
from app.repositories.match_repo import MatchRepository
from app.schemas.ai import AIChatRequest, AIChatResponse, ToolCallPayload

# ──────────────────────────────────────────────────────────────────────────────
# Tool schema definitions (OpenAI function-calling format, also Gemini-compatible)
# ──────────────────────────────────────────────────────────────────────────────

AI_TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_pitches",
            "description": (
                "Search available mini-football pitches for rent in a specific city, "
                "date, and starting hour.  Returns pitches that have no overlapping "
                "confirmed booking for the requested one-hour window [start, start+1h)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name (e.g. 'Reșița', 'Timișoara', 'București').",
                    },
                    "date": {
                        "type": "string",
                        "description": "Target date in ISO format YYYY-MM-DD.",
                    },
                    "start_hour": {
                        "type": "integer",
                        "description": "24-hour starting hour (0-23), e.g. 20 for 20:00.",
                    },
                    "surface_type": {
                        "type": "string",
                        "enum": [
                            "SYNTHETIC_3G",
                            "INDOOR_TARAFLEX",
                            "NATURAL_GRASS",
                            "HYBRID",
                        ],
                        "description": "Optional pitch surface filter.",
                    },
                },
                "required": ["city", "date", "start_hour"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_open_lobbies",
            "description": (
                "Search open mini-football match lobbies that still need extra players "
                "(+1 / need players announcements).  Returns lobbies with status OPEN."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City where the match takes place.",
                    },
                    "needed_role": {
                        "type": "string",
                        "enum": ["PLAYER", "GOALKEEPER"],
                        "description": "Optional role needed by the lobby.",
                    },
                    "date": {
                        "type": "string",
                        "description": "Optional date in ISO format YYYY-MM-DD.",
                    },
                },
                "required": ["city"],
            },
        },
    },
]

# Maximum number of tool-calling turns before the loop is forcibly terminated.
MAX_TOOL_TURNS: int = 5


class AIService:
    """Stateless per-request AI concierge orchestrator.

    Instantiate once per FastAPI request (receives the async SQLAlchemy
    session from the dependency-injection layer) and call ``handle_chat``.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.booking_repo = BookingRepository(session)
        self.match_repo = MatchRepository(session)
        # Supports OpenAI *and* Gemini OpenAI-compatible endpoint via base_url.
        self.client = AsyncOpenAI(
            api_key=settings.effective_llm_api_key,
            base_url=settings.LLM_BASE_URL,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Private tool dispatchers
    # ──────────────────────────────────────────────────────────────────────

    async def _execute_search_pitches(
        self, args: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Resolve ``search_pitches`` tool arguments and query the DB."""
        city: str = args["city"]
        target_date: date = date.fromisoformat(args["date"])
        start_hour: int = int(args["start_hour"])
        surface_str: str | None = args.get("surface_type")
        surface: SurfaceType | None = SurfaceType(surface_str) if surface_str else None

        slot_start = datetime.combine(
            target_date, time(hour=start_hour), tzinfo=timezone.utc
        )
        slot_end = slot_start + timedelta(hours=1)

        pitches = await self.booking_repo.search_available_pitches(
            city=city,
            slot_start=slot_start,
            slot_end=slot_end,
            surface_type=surface,
        )

        return [
            {
                "pitch_id": str(p.id),
                "pitch_name": p.name,
                "venue_name": p.venue.name,
                "address": p.venue.address,
                "surface_type": p.surface_type.value,
                "team_size": f"{p.team_size_capacity}v{p.team_size_capacity}",
                "hourly_rate": float(p.hourly_rate),
                "slot": (
                    f"{slot_start.strftime('%Y-%m-%d %H:%M')}"
                    f" – {slot_end.strftime('%H:%M')} UTC"
                ),
            }
            for p in pitches
        ]

    async def _execute_find_open_lobbies(
        self, args: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Resolve ``find_open_lobbies`` tool arguments and query the DB."""
        city: str = args.get("city", "")
        role_str: str | None = args.get("needed_role")
        needed_role: ParticipantRole | None = (
            ParticipantRole(role_str) if role_str else None
        )
        date_str: str | None = args.get("date")
        target_date: date | None = (
            date.fromisoformat(date_str) if date_str else None
        )

        matches = await self.match_repo.find_open_lobbies(
            city=city,
            needed_role=needed_role,
            target_date=target_date,
        )

        results: List[Dict[str, Any]] = []
        for m in matches:
            confirmed = sum(
                1 for p in m.participants if p.status.value == "CONFIRMED"
            )
            results.append(
                {
                    "match_id": str(m.id),
                    "venue_name": m.booking.pitch.venue.name,
                    "pitch_name": m.booking.pitch.name,
                    "city": m.booking.pitch.venue.city,
                    "scheduled_at": m.scheduled_at.isoformat(),
                    "spots_left": max(0, m.target_players - confirmed),
                    "needed_positions": m.needed_positions or [],
                    "description": m.description or "",
                }
            )
        return results

    # ──────────────────────────────────────────────────────────────────────
    # Public interface
    # ──────────────────────────────────────────────────────────────────────

    async def handle_chat(self, payload: AIChatRequest) -> AIChatResponse:
        """Run the full tool-calling conversation loop and return the final reply.

        The loop is guarded at ``MAX_TOOL_TURNS`` iterations to prevent runaway
        token consumption in adversarial or degenerate LLM behaviour.
        """
        system_prompt = (
            "You are the AI Matchmaking Concierge for a mini-football booking platform. "
            f"Today's date is {date.today().isoformat()}. "
            f"Default city if unspecified: {payload.default_city}. "
            "Always call the provided tools to check real-time pitch availability "
            "or open lobbies before answering. "
            "You can also help players draft catchy '+1 / Need Players' announcements."
        )

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]
        for msg in payload.history:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": payload.message})

        invoked_tools: List[ToolCallPayload] = []

        for _turn in range(MAX_TOOL_TURNS):
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL_NAME,
                messages=messages,  # type: ignore[arg-type]
                tools=AI_TOOLS_SCHEMA,  # type: ignore[arg-type]
                tool_choice="auto",
            )

            assistant_msg = response.choices[0].message

            if not assistant_msg.tool_calls:
                # No tool invocations — return the final text reply.
                return AIChatResponse(
                    reply=assistant_msg.content or "",
                    invoked_tools=invoked_tools,
                )

            # Append the assistant's tool-call request to the message thread.
            messages.append(assistant_msg.model_dump(exclude_none=True))

            # Dispatch each requested tool and append its result.
            for tool_call in assistant_msg.tool_calls:
                fn_name: str = tool_call.function.name
                raw_args: Dict[str, Any] = json.loads(tool_call.function.arguments)

                if fn_name == "search_pitches":
                    tool_result = await self._execute_search_pitches(raw_args)
                elif fn_name == "find_open_lobbies":
                    tool_result = await self._execute_find_open_lobbies(raw_args)
                else:
                    tool_result = [{"error": f"Unknown tool: {fn_name}"}]

                invoked_tools.append(
                    ToolCallPayload(
                        tool_name=fn_name,
                        arguments=raw_args,
                        result_summary=tool_result,
                    )
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": fn_name,
                        "content": json.dumps(tool_result, default=str),
                    }
                )

        # ── Loop cap reached: request a final summary without tools ─────────
        final_response = await self.client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=messages,  # type: ignore[arg-type]
        )
        reply_text: str = final_response.choices[0].message.content or ""
        return AIChatResponse(reply=reply_text, invoked_tools=invoked_tools)

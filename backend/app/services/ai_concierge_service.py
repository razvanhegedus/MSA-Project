"""
AI Concierge Service (Phase 6).

Orchestrates multi-turn conversational tool calling with Google Gemini Flash
(or OpenAI-compatible LLMs) using function definitions.
Guarded by a strict MAX_TOOL_CYCLES loop cap (5 iterations).
"""

import json
import logging
import uuid
from datetime import date
from typing import Any, Dict, List

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.ai import AIChatRequest, AIChatResponse, ToolCallRecord
from app.services.ai_tools import AI_TOOLS_DEFINITIONS, AITools

logger = logging.getLogger(__name__)

MAX_TOOL_CYCLES: int = 5


class AIConciergeService:
    """Manages the LLM interaction loop and tool execution for the AI Concierge."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tools = AITools(session)
        self.client = AsyncOpenAI(
            api_key=settings.effective_llm_api_key,
            base_url=settings.LLM_BASE_URL,
        )

    def _build_system_prompt(self, default_city: str | None) -> str:
        """Construct the system instructions grounding the concierge model."""
        city_ctx = default_city or "Reșița"
        return (
            "You are the AI Concierge for Pitchup, a high-concurrency mini-football pitch booking "
            "and matchmaking platform. "
            f"Today's date is {date.today().isoformat()}. Default city if unspecified: {city_ctx}. "
            "You have direct access to database tools for checking pitches, checking slot availability, "
            "drafting booking quotes, and finding open matchmaking lobbies (+1 extra players). "
            "Always call the appropriate tool when the user asks about availability, pitches, pricing, "
            "or open matches before replying. Provide clear, concise, and helpful football concierge responses."
        )

    async def handle_chat(self, payload: AIChatRequest) -> AIChatResponse:
        """
        Execute the conversation turn with structured tool calling.
        Limits tool invocations to MAX_TOOL_CYCLES to prevent infinite loops.
        Falls back to local database search on LLM failures or unconfigured keys.
        """
        try:
            system_prompt = self._build_system_prompt(payload.default_city)

            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": system_prompt}
            ]
            for msg in payload.history:
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": payload.message})

            invoked_tools: List[ToolCallRecord] = []

            for _cycle in range(MAX_TOOL_CYCLES):
                response = await self.client.chat.completions.create(
                    model=settings.LLM_MODEL_NAME,
                    messages=messages,  # type: ignore[arg-type]
                    tools=AI_TOOLS_DEFINITIONS,  # type: ignore[arg-type]
                    tool_choice="auto",
                )

                assistant_msg = response.choices[0].message

                if not assistant_msg.tool_calls:
                    return AIChatResponse(
                        reply=assistant_msg.content or "",
                        invoked_tools=invoked_tools,
                    )

                # Clean assistant message tool_calls structure for Gemini OpenAI compatibility
                cleaned_tool_calls = [
                    {
                        "id": getattr(tc, "id", None) or f"call_{uuid.uuid4().hex[:8]}",
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in assistant_msg.tool_calls
                ]
                messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_msg.content or "",
                        "tool_calls": cleaned_tool_calls,
                    }
                )

                for tool_call in assistant_msg.tool_calls:
                    fn_name: str = tool_call.function.name
                    try:
                        raw_args: Dict[str, Any] = json.loads(tool_call.function.arguments)
                    except Exception:
                        raw_args = {}

                    tool_result = await self.tools.dispatch_tool(fn_name, raw_args)

                    invoked_tools.append(
                        ToolCallRecord(
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

            # ── Cap reached: request final synthesis without tool definitions ──
            final_response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL_NAME,
                messages=messages,  # type: ignore[arg-type]
            )
            reply_text = final_response.choices[0].message.content or ""
            return AIChatResponse(reply=reply_text, invoked_tools=invoked_tools)
        except Exception as exc:
            logger.warning("LLM API call failed; falling back to local database query: %s", exc)
            return await self._handle_local_fallback(payload)

    async def _handle_local_fallback(self, payload: AIChatRequest) -> AIChatResponse:
        """
        Deterministic local query fallback when third-party LLM APIs fail or credentials are missing.
        Directly checks database using existing AITools handlers based on user message keywords.
        """
        try:
            msg_lower = payload.message.lower()
            city = payload.default_city
            for c in [
                "cluj-napoca", "cluj", "timișoara", "timisoara",
                "bucurești", "bucuresti", "iași", "iasi",
                "brașov", "brasov", "reșița", "resita"
            ]:
                if c in msg_lower:
                    if "cluj" in c:
                        city = "Cluj-Napoca"
                    elif "timi" in c:
                        city = "Timișoara"
                    elif "bucu" in c:
                        city = "București"
                    elif "ia" in c:
                        city = "Iași"
                    elif "bra" in c:
                        city = "Brașov"
                    elif "re" in c:
                        city = "Reșița"
                    break
            if not city:
                city = "Cluj-Napoca"

            is_match_query = any(k in msg_lower for k in ["lobb", "player", "goalkeeper", "gk", "match"])
            needed_role = "GOALKEEPER" if ("goalkeeper" in msg_lower or "gk" in msg_lower) else None

            if is_match_query:
                lobbies = await self.tools.find_open_lobbies(city=city, needed_role=needed_role)
                if lobbies:
                    lines = [f"Found {len(lobbies)} open match lobb{'y' if len(lobbies) == 1 else 'ies'} in {city}:"]
                    for l in lobbies:
                        spots = l.get("spots_left", 0)
                        pos = ", ".join(l.get("needed_positions", [])) or "Any"
                        lines.append(f"• {l.get('pitch_name', 'Pitch')} at {l.get('venue_name', 'Venue')} - {spots} spot{'s' if spots != 1 else ''} left (Positions: {pos})")
                    reply = "\n".join(lines)
                else:
                    reply = f"No open match lobbies currently found in {city}. You can reserve a pitch and start your own open lobby!"
                return AIChatResponse(
                    reply=reply,
                    invoked_tools=[
                        ToolCallRecord(
                            tool_name="find_open_lobbies",
                            arguments={"city": city, "needed_role": needed_role},
                            result_summary=lobbies,
                        )
                    ],
                )
            else:
                pitches = await self.tools.search_pitches(city=city)
                if pitches:
                    lines = [f"Found {len(pitches)} pitch{'es' if len(pitches) != 1 else ''} in {city}:"]
                    for p in pitches:
                        rate = p.get('hourly_rate', '')
                        surface = p.get('surface_type', '').replace('_', ' ')
                        lines.append(f"• {p.get('pitch_name', 'Pitch')} at {p.get('venue_name', 'Venue')} ({surface}, {rate} RON/h)")
                    reply = "\n".join(lines)
                else:
                    reply = f"No pitches found in {city}. Try checking other available cities like Cluj-Napoca, Timișoara, or București."
                return AIChatResponse(
                    reply=reply,
                    invoked_tools=[
                        ToolCallRecord(
                            tool_name="search_pitches",
                            arguments={"city": city},
                            result_summary=pitches,
                        )
                    ],
                )
        except Exception as exc:
            logger.error("Local fallback query failed: %s", exc)
            return AIChatResponse(
                reply="I'm currently unable to retrieve pitch or lobby data. Please browse the pitches and matches tabs directly.",
                invoked_tools=[],
            )


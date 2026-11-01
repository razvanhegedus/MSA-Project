"""
AI Concierge Service (Phase 6).

Orchestrates multi-turn conversational tool calling with Google Gemini Flash
(or OpenAI-compatible LLMs) using function definitions.
Guarded by a strict MAX_TOOL_CYCLES loop cap (5 iterations).
"""

import json
from datetime import date
from typing import Any, Dict, List

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.ai import AIChatRequest, AIChatResponse, ToolCallRecord
from app.services.ai_tools import AI_TOOLS_DEFINITIONS, AITools

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
        """
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

            messages.append(assistant_msg.model_dump(exclude_none=True))

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

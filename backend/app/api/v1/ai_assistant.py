from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.base_entities import User
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.services.ai_service import AIService

router = APIRouter()


@router.post(
    "/chat",
    response_model=AIChatResponse,
    status_code=status.HTTP_200_OK,
    summary="AI Concierge — conversational pitch search & lobby assistant",
)
async def ai_chat(
    payload: AIChatRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AIChatResponse:
    """
    Send a natural-language message to the AI Matchmaking Concierge.

    The assistant will call ``search_pitches`` and/or ``find_open_lobbies``
    tools against the live database to answer questions about availability,
    open lobbies, and booking options.

    The tool-calling loop is capped at 5 turns per request to prevent
    runaway LLM behaviour.
    """
    service = AIService(session)
    return await service.handle_chat(payload)

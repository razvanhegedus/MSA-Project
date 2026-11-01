from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.base_entities import User
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.services.ai_concierge_service import AIConciergeService

router = APIRouter()


@router.post(
    "/chat",
    response_model=AIChatResponse,
    status_code=status.HTTP_200_OK,
    summary="AI Concierge — conversational pitch search, slot availability & draft booking",
)
async def chat_with_concierge(
    payload: AIChatRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AIChatResponse:
    """
    Send conversational inquiries to the AI Concierge.

    Protected endpoint requiring a valid JWT bearer token.
    Dispatches tool calls (search_pitches, check_slot_availability, draft_booking, find_open_lobbies)
    directly through pure backend services within transaction boundaries.
    """
    service = AIConciergeService(session)
    return await service.handle_chat(payload)


"""
Backward-compatibility bridge for AI Assistant Router.
Re-exports the router from app.api.v1.ai.
"""

from app.api.v1.ai import router, chat_with_concierge as ai_chat

__all__ = ["router", "ai_chat"]

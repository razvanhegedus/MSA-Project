"""
Backward-compatibility bridge for AI Concierge Service (Phase 6).

Re-exports AIService as an alias of AIConciergeService, along with
AI_TOOLS_SCHEMA pointing to AI_TOOLS_DEFINITIONS.
"""

from app.services.ai_concierge_service import AIConciergeService, MAX_TOOL_CYCLES
from app.services.ai_tools import AI_TOOLS_DEFINITIONS, AITools

# Backward compatibility aliases
AIService = AIConciergeService
AI_TOOLS_SCHEMA = AI_TOOLS_DEFINITIONS
MAX_TOOL_TURNS = MAX_TOOL_CYCLES

__all__ = [
    "AIConciergeService",
    "AIService",
    "AITools",
    "AI_TOOLS_DEFINITIONS",
    "AI_TOOLS_SCHEMA",
    "MAX_TOOL_CYCLES",
    "MAX_TOOL_TURNS",
]

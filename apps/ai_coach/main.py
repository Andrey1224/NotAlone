"""AI coach service main module."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from apps.ai_coach.anonymize import anonymize_chat_context
from apps.ai_coach.provider import get_coaching_hint
from core.config import settings

app = FastAPI(title="AI Coach Service", version="0.1.0")


class HintRequest(BaseModel):
    """Request for AI coaching hint."""

    chat_session_id: int
    user_id: int
    context: str
    hint_type: str = "empathy"  # empathy, question, boundary


class HintResponse(BaseModel):
    """Response with AI coaching hint."""

    hint: str
    hint_type: str


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "ai_enabled": str(settings.ai_enabled)}


@app.post("/hint", response_model=HintResponse)
async def get_hint(request: HintRequest) -> HintResponse:
    """Get AI coaching hint."""
    if not settings.ai_enabled:
        raise HTTPException(status_code=503, detail="AI coach is disabled")

    # Anonymize context
    anonymized_context = anonymize_chat_context(request.context, request.user_id)

    # Get hint from AI provider
    hint = await get_coaching_hint(anonymized_context, request.hint_type)

    return HintResponse(hint=hint, hint_type=request.hint_type)

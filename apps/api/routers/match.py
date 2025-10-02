"""Match endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_db

router = APIRouter()


class MatchFindRequest(BaseModel):
    """Request to find a match."""

    user_id: int
    topics: list[str]
    timezone: str


class MatchConfirmRequest(BaseModel):
    """Request to confirm a match."""

    match_id: int
    user_id: int
    accepted: bool


@router.post("/find")
async def find_match(request: MatchFindRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Find a match for user."""
    # TODO: Implement match finding logic
    # 1. Add user to match queue (Redis)
    # 2. Return queue position or immediate match if available
    return {"status": "queued", "user_id": str(request.user_id)}


@router.post("/confirm")
async def confirm_match(request: MatchConfirmRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Confirm or decline a match."""
    # TODO: Implement match confirmation logic
    # 1. Update match status based on acceptance
    # 2. If both users accepted, create chat session
    return {"status": "confirmed" if request.accepted else "declined", "match_id": str(request.match_id)}

"""Payment endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_db

router = APIRouter()


class CreateTipRequest(BaseModel):
    """Request to create a tip."""

    from_user_id: int
    to_user_id: int
    match_id: int
    amount: int  # in XTR (Telegram Stars)


class TipWebhookPayload(BaseModel):
    """Webhook payload for tip status updates."""

    tip_id: int
    status: str  # paid, failed
    provider_transaction_id: str | None = None


@router.post("/tips/create")
async def create_tip(request: CreateTipRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str | int]:
    """Create a tip invoice."""
    # TODO: Implement tip creation logic
    # 1. Create tip record in database
    # 2. Generate Telegram Stars invoice
    # 3. Return invoice URL
    return {
        "status": "created",
        "tip_id": 1,
        "invoice_url": "https://t.me/invoice/placeholder",
        "amount": request.amount,
    }


@router.post("/webhook/telegram-stars")
async def telegram_stars_webhook(payload: TipWebhookPayload, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Handle Telegram Stars payment webhook."""
    # TODO: Implement webhook handler
    # 1. Verify webhook signature
    # 2. Update tip status in database
    # 3. Notify users
    return {"status": "processed"}

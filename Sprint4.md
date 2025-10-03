Sprint 4 — Tips через Telegram Stars (XTR) — финальный план
Скоуп

Инвойсы XTR (Stars) без provider_token; только currency="XTR" + prices. Это требование для цифровых товаров.
Telegram Core
+1

Доступность: в активной сессии и 24 часа после /end (eligibility на бэке).

Пресеты: 5 / 10 / 25 / 50 XTR.

Показ кнопок: после /end (CTA) + команда /tips, опционально в активном чате (feature flag).

Идемпотентность:

callback → Redis SETNX tips:cb:<callback_query.id> EX 60;

оплата → уникальность по telegram_payment_charge_id. Поле приходит в successful_payment.
Telegram Core
+1

Подписанный invoice_payload (HMAC-SHA256) → сверка в webhook.

Чек: сумма, наша комиссия 10%, provider_fee (для XTR = 0).

Вебхук на поддерживаемых портах 443/80/88/8443 (иначе не примут).
Telegram Core

Уведомления: Redis-дедупликация notif:tip:<telegram_payment_charge_id> EX 86400 для предотвращения повторных уведомлений при retry webhook.

БД (дельты)
ALTER TABLE tips
  ADD COLUMN IF NOT EXISTS telegram_payment_id TEXT,
  ADD COLUMN IF NOT EXISTS invoice_payload TEXT,
  ADD CONSTRAINT uq_tips_payment UNIQUE (telegram_payment_id);

API контракты

GET /tips/eligibility?match_id&from&to → 200 {"ok":true} или 403.

POST /payments/record → принимает данные из successful_payment:

currency (ожидаем "XTR"), total_amount, invoice_payload,

telegram_payment_charge_id (ключ идемпотентности).
Telegram Core

Внутренний endpoint — вызывается ботом после получения successful_payment в /telegram/webhook.

Бот (aiogram 3)

Архитектура webhook:

successful_payment обрабатывается в существующем /telegram/webhook через aiogram handler.

Handler бота пробрасывает данные на POST /payments/record (внутренний API endpoint).

После успешной записи (200) бот отправляет уведомления обеим сторонам.

Инлайн-кнопки пресетов → send_invoice(currency="XTR", prices=[...]).
Aiogram Documentation
+1

HMAC в invoice_payload для защиты от подделки (core/security.py).

Мини-код (готов к вставке)

HMAC функции (core/security.py)

import hmac
import hashlib
import base64
from core.config import settings

def _b64u(data: bytes) -> str:
    """Base64url без padding."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def sign_tips_payload(payload: str) -> str:
    """Подписать payload HMAC-SHA256."""
    secret = settings.tips_hmac_secret.encode()
    mac = hmac.new(secret, payload.encode(), hashlib.sha256).digest()
    return f"{payload}.{_b64u(mac)}"

def verify_tips_payload(signed: str) -> tuple[bool, str]:
    """Проверить HMAC подпись. Возвращает (valid, original_payload)."""
    try:
        payload, sig = signed.rsplit('.', 1)
        secret = settings.tips_hmac_secret.encode()
        mac = hmac.new(secret, payload.encode(), hashlib.sha256).digest()
        valid = hmac.compare_digest(_b64u(mac), sig)
        return (valid, payload if valid else "")
    except Exception:
        return (False, "")

Бот: пресеты → invoice

# apps/bot/handlers/tips.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, LabeledPrice
from apps.bot.api_client import api_client
from core.security import sign_tips_payload

router = Router(name="tips")
PRESETS = [5, 10, 25, 50]  # XTR

@router.callback_query(F.data.startswith("tip:"))
async def on_tip(cb: CallbackQuery):
    # tip:<matchId>:<toUserId>:<amount>
    _, match_id, to_user_id, amount = cb.data.split(":")
    if str(cb.from_user.id) == to_user_id:
        return await cb.answer("Нельзя отправить чаевые самому себе", show_alert=True)

    r = await api_client.get(
        f"/tips/eligibility?match_id={match_id}&from={cb.from_user.id}&to={to_user_id}"
    )
    if r.status != 200:
        return await cb.answer("Сессия неактивна или истёк срок", show_alert=True)

    payload = sign_payload(f"{match_id}:{cb.from_user.id}:{to_user_id}:{amount}")
    await cb.message.bot.send_invoice(
        chat_id=cb.from_user.id,
        title="Чаевые собеседнику",
        description="Спасибо за разговор! Комиссия платформы 10%.",
        payload=payload,               # вернётся в successful_payment
        currency="XTR",                # Stars требуют XTR
        prices=[LabeledPrice(label=f"{amount} XTR", amount=int(amount))],
    )
    await cb.answer()


(aiogram send_invoice берёт типы прямо из Bot API; XTR валюта задокументирована на core.telegram.org.
Aiogram Documentation
+1
)

API: eligibility (≤24ч после /end)

# apps/api/routers/tips.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.deps import get_db

router = APIRouter(prefix="/tips", tags=["tips"])

@router.get("/eligibility")
async def eligibility(match_id: int, from_: int, to: int, db: AsyncSession = Depends(get_db)):
    q = text("""
      SELECT 1
      FROM matches m
      JOIN chat_sessions cs ON cs.match_id = m.id
      JOIN users ua ON ua.id = m.user_a
      JOIN users ub ON ub.id = m.user_b
      WHERE m.id=:m
        AND ((ua.tg_id=:from AND ub.tg_id=:to) OR (ua.tg_id=:to AND ub.tg_id=:from))
        AND (m.status='active' OR (m.status='completed' AND cs.ended_at >= now() - interval '24 hours'))
    """)
    ok = (await db.execute(q, {"m": match_id, "from": from_, "to": to})).first()
    if not ok:
        raise HTTPException(403, "not_eligible")
    return {"ok": True}


API: запись платежа (внутренний endpoint)

# apps/api/routers/payments.py
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.deps import get_db
from core.security import verify_tips_payload
import logging

router = APIRouter(prefix="/payments", tags=["payments"])
logger = logging.getLogger(__name__)

@router.post("/record")
async def record_payment(req: Request, db: AsyncSession = Depends(get_db)):
    """Внутренний endpoint для записи successful_payment от бота."""
    body = await req.json()

    # Извлекаем данные successful_payment
    sp = body.get("successful_payment") or {}
    if not sp:
        raise HTTPException(400, "missing_successful_payment")

    # Bot API: XTR валюта и идентификатор оплаты
    currency = sp.get("currency")  # "XTR"
    total_amount = sp.get("total_amount")  # минорные единицы
    tpid = sp.get("telegram_payment_charge_id")  # идемпотентность
    signed_payload = sp.get("invoice_payload", "")

    # Проверка HMAC подписи
    valid, payload = verify_tips_payload(signed_payload)
    if not valid or currency != "XTR":
        logger.warning(f"Invalid payment: valid={valid}, currency={currency}")
        raise HTTPException(400, "invalid_payment")

    # Парсим payload: match_id:from_tg:to_tg:amount
    try:
        match_id, from_tg, to_tg, amount = payload.split(":")
    except ValueError:
        raise HTTPException(400, "malformed_payload")
    # Расчёт комиссии 10%
    commission = int(round(int(amount) * 0.10))

    # Upsert по уникальному tpid (ON CONFLICT DO NOTHING для идемпотентности)
    result = await db.execute(text("""
      INSERT INTO tips(match_id, from_user, to_user, amount_minor, currency, provider,
                       provider_fee_minor, our_commission_minor, status, created_at,
                       telegram_payment_id, invoice_payload)
      SELECT m.id, ua.id, ub.id,
             :amt, :cur, 'telegram-stars',
             0, :commission, 'paid', now(), :tpid, :signed_payload
      FROM matches m
      JOIN users ua ON ua.tg_id = :from_tg
      JOIN users ub ON ub.tg_id = :to_tg
      WHERE m.id = :m
      ON CONFLICT (telegram_payment_id) DO NOTHING
      RETURNING id
    """), {
        "amt": int(amount),
        "cur": currency,
        "tpid": tpid or "",
        "signed_payload": signed_payload,
        "from_tg": int(from_tg),
        "to_tg": int(to_tg),
        "m": int(match_id),
        "commission": commission,
    })
    await db.commit()

    # Проверяем, была ли создана новая запись (для логирования)
    inserted = result.first()
    if inserted:
        logger.info(f"Payment recorded: tip_id={inserted[0]}, amount={amount} XTR")

    return {"status": "ok", "from_tg": int(from_tg), "to_tg": int(to_tg)}

Тест-план (ручной)

T1: активная сессия → «10 XTR» → оплата → 1 запись tips(paid); чек двум пользователям.

T2: двойной клик → без дублей (уникальный telegram_payment_charge_id).
Telegram Core

T3: сам себе → отказ.

T4: через 24ч после /end → отказ по eligibility.

T5: повтор доставки webhook → запись не дублируется.

Нюансы и best practices

Для Stars цифровых товаров всегда ставь currency="XTR"; это явно прописано в официальной странице «Payments for digital goods & services».
Telegram Core

sendInvoice/createInvoiceLink доступны в aiogram 3.x; они маппятся на Bot API методы.
Aiogram Documentation
+1

Вебхуки Telegram принимаются только на 443/80/88/8443 — это официальная страница webhooks.
Telegram Core

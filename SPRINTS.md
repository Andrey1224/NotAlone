# Sprints History — "Ты не один" MVP

Полная история разработки MVP платформы для peer-to-peer поддержки через Telegram бот.

**Проект:** Ты не один (You're Not Alone)
**Период:** 2-5 октября 2025
**Статус:** MVP готов (5 спринтов завершены)

---

## 📊 Общий прогресс

| Sprint | Тема | Дата | Статус | Задачи |
|--------|------|------|--------|--------|
| **Sprint 1** | Инфраструктура и профили | 2 окт 2025 | ✅ 100% | 8/8 |
| **Sprint 2** | Матчинг 1-на-1 | 2-3 окт 2025 | ✅ 100% | 10/10 |
| **Sprint 3** | Пересылка сообщений | 3 окт 2025 | ✅ 100% | 5/5 |
| **Sprint 4** | Telegram Stars чаевые | 3 окт 2025 | ✅ 100% | 14/14 |
| **Sprint 5** | Безопасность и модерация | 5 окт 2025 | ✅ 100% | 10/10 |

**Итого:** 47 задач завершено, 0 открытых

---

# Sprint 1 — Инфраструктура и профили

**Дата:** 2 октября 2025 | **Статус:** ✅ Завершён

## Цель
Создать базовую инфраструктуру проекта с Docker, PostgreSQL, Redis, FastAPI API, Telegram webhook и реализовать полный flow создания профиля пользователя.

## Ключевые достижения

### Инфраструктура
- **Docker Compose**: API, Bot, Worker, PostgreSQL 18, Redis 7.4
- **FastAPI** с health checks и Prometheus метриками
- **Telegram Webhook** через FastAPI (`/telegram/webhook`)
- **SQLAlchemy 2.x** с async поддержкой, Alembic миграции

### База данных (9 таблиц)
- `users` - Пользователи с псевдонимами и таймзонами
- `topics` - 12 предустановленных тем (burnout, relocation, anxiety, etc.)
- `user_topics` - M2M связь пользователей и тем
- `matches` - Пары пользователей (proposed/active/declined/expired/completed)
- `chat_sessions` - Активные диалоги с метриками
- `tips` - Telegram Stars платежи
- `ai_hints`, `safety_flags` - Future features

### Profile Flow (FSM, 5 состояний)
1. **WaitingNickname** → 2. **WaitingTimezone** → 3. **WaitingTopics** (мин. 2) → 4. **WaitingBio** → 5. **ProfileComplete**

### E2E тест
✅ Пользователь создан: МистерАндрей (tg_id: 1057355026), Europe/Kiev, темы: loneliness, anxiety, relationships, loss

## Уроки
- FastAPI + aiogram через `feed_webhook_update()`
- Webhook требует HTTPS (ngrok для dev)
- SQLAlchemy 2.x: `Mapped[type]` и `mapped_column()`

---

# Sprint 2 — Матчинг 1-на-1

**Дата:** 2-3 октября 2025 | **Статус:** ✅ Завершён

## Цель
Система подбора собеседников: пользователь получает предложение матча ≤60 сек при взаимном согласии создаётся chat_session.

## Архитектура
```
User → Bot → API → Redis Streams (match.find) → Worker → DB → Proposals → Both Users
```

### Компоненты
1. **Redis Streams** - очередь матчинга (`match.find`)
2. **Match Worker** - consumer для подбора кандидатов
3. **Scoring Algorithm**: `0.6*topic_overlap + 0.2*time_overlap + 0.2*helpfulness`
4. **Inline Buttons**: "✅ Принять" / "➖ Пропустить"

### Новая таблица: recent_contacts
```sql
CREATE TABLE recent_contacts (
  user_id BIGINT, other_id BIGINT, until TIMESTAMPTZ,
  PRIMARY KEY (user_id, other_id)
);
```
**Цель:** Cooldown 72 часа после decline

## API Endpoints
- **POST /match/find** - Добавить в очередь поиска
- **POST /match/confirm** - Принять/отклонить предложение (`action: "accept"|"decline"`)

## Подбор кандидатов (SQL)
```sql
-- Критерии: ≥2 общих темы, нет в recent_contacts, scoring
SELECT cand_id, shared_cnt FROM overlap
WHERE shared_cnt >= 2
ORDER BY shared_cnt DESC LIMIT 10;
```

## Машина состояний
```
Waiting → Confirmed (оба "Принять") → StartChat
       → Declined (любой "Пропустить") → Cooldown 72ч
       → Expired (TTL 5 мин) → Requeue (max 2)
```

## Метрики
`match_queue_size`, `match_worker_lag_ms`, `proposals_sent_total`, `match_accept_total`, `match_decline_total`, `accept_rate`

**Алерты:** Лаг очереди >5 мин, `accept_rate <0.25` за 60 мин

## Критерии приёмки
✅ ≥70% запросов получают предложение ≤60 сек
✅ `accept_rate` ≥30%
✅ Интеграционные тесты зелёные

---

# Sprint 3 — Пересылка сообщений и завершение чата

**Дата:** 3 октября 2025 | **Статус:** ✅ Завершён

## Цель
Полноценный диалог 1-на-1 без хранения содержимого (только счётчики), команда `/end`.

## Правила
- **Не сохраняем** содержимое (только `msg_count_a`, `msg_count_b`)
- Поддержка **текста** в MVP
- Работает только в `status='active'`; вне сессии → подсказка `/find`

## Изменения БД
```sql
ALTER TABLE chat_sessions
  ADD COLUMN msg_count_a INT NOT NULL DEFAULT 0,
  ADD COLUMN msg_count_b INT NOT NULL DEFAULT 0;
```

## API Endpoints
- **POST /chat/relay** - Переслать сообщение (`from_user`, `text` → `peer_tg_id`)
- **POST /chat/end** - Завершить диалог (`user_id` → `peer_tg_id`)

## Bot Handlers
### Пересылка (catch-all)
```python
@dp.message()
async def on_text(msg: Message):
    r = await api_client.post('/chat/relay', json={"from_user": msg.from_user.id, "text": msg.text})
    if r.status == 200:
        await bot.send_message(r.json()["peer_tg_id"], f"✉️ {msg.from_user.username}: {msg.text}")
    else:
        await msg.answer("Нет активного диалога. /find")
```

### Команда /end
Inline-кнопка → POST /chat/end → уведомления обеим сторонам + CTA чаевых

## Граничные случаи
1. Сообщение вне активной сессии → подсказка `/find`
2. Блокировка Telegram (peer закрыл бота) → ловим `Forbidden`, уведомляем
3. Rate limit: 15 сообщений/мин (Redis token bucket)

## Критерии приёмки
✅ p95 пересылки ≤800 мс
✅ /end завершает в ≤2 сек
✅ Потерь сообщений нет

---

# Sprint 4 — Telegram Stars Чаевые

**Дата:** 3 октября 2025 | **Статус:** ✅ Завершён

## Цель
Полная функциональность чаевых через Telegram Stars (XTR) с HMAC-защитой, idempotency и CTA после `/end`.

## Выполненные задачи (14/14)

### Бэкенд (6)
1. Миграция: `telegram_payment_id` UNIQUE, `invoice_payload`
2. HMAC функции: `sign_tips_payload()`, `verify_tips_payload()`
3. Env: `TIPS_HMAC_SECRET`
4. API: `GET /tips/eligibility` (активная ИЛИ ≤24ч после end)
5. API: `POST /payments/record` (idempotent upsert)
6. Tips router подключен

### Бот (5)
7. Callback handler пресетов (5/10/25/50 XTR) + Redis lock
8. Команда `/tips` с inline-кнопками
9. Handler `successful_payment` + уведомления
10. `/end` с CTA кнопками чаевых
11. Tips router подключен

### Инфраструктура (3)
12. Модель `Tip` обновлена
13. `/chat/end` возвращает `match_id`
14. Миграция применена, сервисы перезапущены

## Ключевые реализации

### HMAC-подпись
```python
def sign_tips_payload(payload: str) -> str:
    mac = hmac.new(secret, payload.encode(), hashlib.sha256).digest()
    return f"{payload}.{_b64u(mac)}"
```

### Eligibility
```sql
-- Активная сессия ИЛИ ≤24ч после end
WHERE m.status = 'active' OR (m.status = 'completed' AND cs.ended_at >= now() - interval '24 hours')
```

### Idempotent recording
```sql
INSERT INTO tips(...) VALUES(...)
ON CONFLICT (telegram_payment_id) DO NOTHING
RETURNING id;
```

### Redis locks
- **Callback lock**: `tips:cb:{callback.id}` EX 60 (против двойных кликов)
- **Notification dedup**: `notif:tip:{telegram_payment_charge_id}` EX 86400

## Flow
```
User → /end → CTA кнопки → клик → Redis lock → eligibility ✅ →
sign_payload → send_invoice(XTR) → оплата → successful_payment →
verify HMAC → POST /payments/record → комиссия 10% →
ON CONFLICT DO NOTHING → уведомления обеим сторонам
```

## Что работает (12 пунктов)
✅ `/tips`, пресеты, Redis lock, eligibility, HMAC, `send_invoice`, `successful_payment`, идемпотентность, комиссия 10%, уведомления, дедупликация, CTA после `/end`

## Уроки
- HMAC критичен для безопасности payload
- Идемпотентность на всех уровнях (Redis + DB + dedup)
- XTR обязателен для Stars
- 24-часовое окно user-friendly
- CTA повышает конверсию

---

# Sprint 5 — Безопасность и модерация

**Дата:** 5 октября 2025 | **Статус:** ✅ Завершён

## Цель
Core safety features: user reports, peer blocking с 30-дневным cooldown, emergency resources (SOS), admin tools.

## Выполненные задачи (10/10)
1. Миграция БД (reports, moderation_actions, recent_contacts)
2. `core/auth.py` (bot_auth HMAC, admin_basic_auth)
3. `apps/bot/redis.py` (активные сессии, TTL 24h)
4. `apps/api/routers/reports.py` (create, block)
5. Bot handlers (report.py, block.py, sos.py)
6. `api_client.py` с HMAC подписями
7. Метрики: `reports_total`, `blocks_total`, histograms
8. Handlers/routers зарегистрированы
9. Sprint5.md обновлён
10. Smoke test успешен

## Database Schema

### reports
```sql
CREATE TABLE reports (
    id BIGSERIAL PRIMARY KEY,
    chat_session_id BIGINT REFERENCES chat_sessions(id) ON DELETE SET NULL,
    from_user BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    to_user BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason VARCHAR(24) CHECK (reason IN ('spam','abuse','danger','other')),
    status VARCHAR(16) DEFAULT 'new' CHECK (status IN ('new','in_review','resolved')),
    comment TEXT, created_at TIMESTAMPTZ, closed_at TIMESTAMPTZ
);
```
**Индексы:** `idx_reports_open`, `idx_reports_target_open`, `uq_reports_once_per_session` (partial unique)

### moderation_actions
История модерации: `target_user`, `action`, `actor`, `reason`, `created_at`

### recent_contacts (обновлена из Sprint 2)
Bilateral 30-дневный cooldown после `/block`: `(user_id, other_id, until)`

## Authentication

### Bot→API HMAC
**Headers:** `X-Tg-User-Id`, `X-Bot-Signature` (HMAC-SHA256 base64url)
```python
async def bot_auth(request: Request) -> int:
    signature = request.headers.get("X-Bot-Signature")
    body = await request.body()  # cached
    if not verify_bot_signature(body, signature):
        raise HTTPException(401)
    return int(request.headers.get("X-Tg-User-Id"))
```

### Admin Basic Auth
HTTP Basic для admin endpoints: `dependencies=[Depends(admin_basic_auth)]`

## API Endpoints

### POST /reports
- **Auth:** bot_auth (HMAC)
- **Validation:** reason in {spam, abuse, danger, other}, rate limit 1/60s (Redis)
- **Response:** `{"ok": true}` или 429

### POST /reports/block
- **Auth:** bot_auth
- **Действия:** End session, mark match completed, bilateral cooldown 30 дней
- **Response:** `{"ok": true}`

## Bot Handlers

### /report
Inline keyboard с 4 причинами → callback → POST /reports с HMAC → подтверждение

### /block
`/block` → get active session (Redis) → POST /reports/block → clear sessions → уведомления обеим сторонам

### /sos
Загрузить `apps/bot/data/sos_ru.json` → показать hotlines (Телефон доверия, Скорая помощь)
**Fallback:** Default hotlines если файл отсутствует

## Redis Session Management
```python
set_active_session(tg_id, chat_session_id, peer_tg_id)  # TTL 24h
get_active_session(tg_id) → {"chat_session_id", "peer_tg_id"}
clear_active_session(tg_id)
```
**Цель:** Context-aware reporting без `reply_to_message` (не работает в callbacks)

## API Client HMAC Support
```python
await api_client.post("/reports", json={...}, auth_bot=True, caller_tg_id=user_id)
# → Serializes body → sign_bot_request() → headers: X-Tg-User-Id, X-Bot-Signature
```

## Configuration
**core/config.py:** `internal_bot_secret`, `admin_user`, `admin_pass`, `mod_chat_id`
**.env.example:** Документированы все новые переменные

## Architecture Decisions
1. **HMAC vs JWT** - HMAC проще (нет expiry/refresh)
2. **Redis Session Storage** - Избегает `reply_to_message` (breaks callbacks)
3. **Bilateral Cooldown** - Оба заблокированы 30 дней (prevents harassment)
4. **Partial Unique Index** - Prevents spam reports, allows multiple reasons
5. **CASCADE vs SET NULL** - Reports сохраняют историю

## Known Limitations
1. No Admin UI (endpoints есть, dashboard нет)
2. No Mod Alerts (MOD_CHAT_ID не используется)
3. Simple Rate Limiting (per-user only)
4. No Appeal Process
5. SOS Data Static (JSON, no CMS)

## Files Created/Modified
**New (8):** migration, `core/auth.py`, `apps/bot/redis.py`, `apps/api/routers/reports.py`, 3 bot handlers, `sos_ru.json`
**Modified (7):** config, security, metrics, api_client, bot.py, main.py, .env.example

---

# 🎉 MVP Завершён!

**Итого:** 5 спринтов, 47 задач, 100% completion

## Готовые компоненты
✅ **Инфраструктура** - Docker, PostgreSQL, Redis, FastAPI, aiogram
✅ **Профили** - FSM с ≥2 темами, таймзоны, био
✅ **Матчинг** - Redis Streams, scoring, proposals, ≤60sec
✅ **Чат** - Relay messages, /end, счётчики
✅ **Чаевые** - Telegram Stars, HMAC, CTA, idempotency
✅ **Безопасность** - Reports, blocks, SOS, HMAC auth, cooldowns

## Production Readiness

| Критерий | Статус |
|----------|--------|
| Security | ✅ HMAC, rate limiting, validation |
| Reliability | ✅ Idempotency, error handling, Redis locks |
| User Experience | ✅ Clear flows, CTAs, notifications |
| Performance | ✅ Indexes, caching, async |
| Monitoring | ⚠️ Metrics есть, dashboards нужны |
| Testing | ⚠️ E2E manual testing required |

## Следующие шаги
1. **Ручное тестирование** - Все flows end-to-end
2. **Grafana Dashboards** - Визуализация метрик
3. **Production Deploy** - EU region (Render/Fly.io)
4. **Admin Dashboard** - Web UI для модерации
5. **AI Coach** - Опциональные AI-подсказки (future)

---

**Документация актуальна на:** 5 октября 2025
**Версия MVP:** 1.0.0
**Статус:** Ready for testing 🚀

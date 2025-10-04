# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

### What is "Ты не один" (You're Not Alone)?

**"Ты не один"** is a **peer-to-peer emotional support platform** delivered through a Telegram bot. The platform connects people experiencing similar life challenges (burnout, relocation, loss, anxiety, parenting stress, etc.) for **anonymous 1-on-1 conversations**.

**Key Philosophy:**
- **Peer support, not therapy** - Users help each other based on shared experiences
- **Anonymity first** - No PII collection, pseudonyms only
- **Safe & respectful** - Community guidelines, reporting, blocking, emergency resources
- **Voluntary appreciation** - Telegram Stars tipping system (no forced payments)

**Target Audience:** Russian-speaking users (RU/CIS) experiencing life challenges, seeking emotional support from peers

**Business Model:**
- Free to use (matching, chat)
- Optional tips (Telegram Stars) with 10% platform commission
- No subscriptions, no ads, no data selling

### Project Status (October 2025)

**MVP Completed:** 5 sprints, 47 tasks, 100% completion
- ✅ Sprint 1: Infrastructure & Profiles
- ✅ Sprint 2: 1-on-1 Matching
- ✅ Sprint 3: Message Relay & Chat Ending
- ✅ Sprint 4: Telegram Stars Tips
- ✅ Sprint 5: Safety & Moderation

**Current Phase:** Manual testing & production deployment preparation

**See:** [SPRINTS.md](SPRINTS.md) for complete development history

---

## MCP Tool Usage Guidelines

**Reference Architecture:** Always check [Arhitecture1.md](Arhitecture1.md) for architectural context before making changes.

### When to Use Each MCP Tool

**Context7 MCP** - For library/API documentation:
- Use automatically when generating code using external libraries
- Setup/configuration steps requiring official docs
- API integration (Telegram Bot API, payment providers)
- Example: "How do I send Telegram invoice with XTR currency?" → Context7

**Serena MCP** - For all code navigation and edits:
- Finding symbols, functions, classes
- Reading/editing existing code
- Understanding code structure
- Example: "Update the matching algorithm" → Serena

**Playwright MCP** - For browser/UI actions:
- Testing web interfaces
- Scraping documentation
- Visual testing
- Example: "Test the admin dashboard" → Playwright (when implemented)

**Default (no MCP)** - For pure code/logic:
- Writing new functions without external dependencies
- Refactoring internal logic
- Example: "Refactor this scoring function" → No MCP needed

---

## Technical Stack

### Core Technologies
- **Python 3.12** - Async/await throughout, type hints everywhere
- **FastAPI** - REST API with automatic OpenAPI docs
- **aiogram 3.x** - Telegram Bot framework (webhook mode)
- **PostgreSQL 18** - Primary datastore with full-text search
- **Redis 7.4** - Caching, rate limiting, match queue (Streams)
- **SQLAlchemy 2.x** - Async ORM with Alembic migrations
- **Prometheus** - Metrics export for monitoring

### Infrastructure (Docker Compose)
```yaml
services:
  api        # FastAPI REST API + webhook receiver
  bot        # Telegram bot (aiogram 3.x)
  worker     # Match queue consumer (Redis Streams)
  db         # PostgreSQL 18
  redis      # Redis 7.4
```

### Development Tools
- **ruff** - Fast Python linter
- **black** - Code formatter
- **mypy** - Static type checker
- **pytest** - Testing framework
- **pre-commit** - Git hooks for quality checks

---

## Architecture Overview

### Service Structure

```
┌─────────────┐
│   Telegram  │
│   (Users)   │
└──────┬──────┘
       │ HTTPS Webhook
       ▼
┌─────────────┐      ┌─────────────┐
│  FastAPI    │◄────►│   Redis     │
│  (API)      │      │  (Streams)  │
└──────┬──────┘      └──────┬──────┘
       │                    │
       │ Internal HTTP      │ Consumer
       ▼                    ▼
┌─────────────┐      ┌─────────────┐
│  aiogram    │      │   Worker    │
│  (Bot)      │      │  (Matcher)  │
└─────────────┘      └─────────────┘
       │                    │
       └────────┬───────────┘
                ▼
         ┌─────────────┐
         │ PostgreSQL  │
         │  (Data)     │
         └─────────────┘
```

### Key Flows

**1. User Profile Creation (FSM)**
```
/start → WaitingNickname → WaitingTimezone → WaitingTopics → WaitingBio → Complete
```

**2. Matching Flow**
```
/find → API → Redis Stream → Worker → SQL (≥2 shared topics) →
Scoring → Proposals → Both accept → Chat Session
```

**3. Chat Flow**
```
User A message → Bot → API /chat/relay → Find active session →
User B (peer_tg_id) → Bot sends to User B
```

**4. Tips Flow**
```
/end → CTA buttons → Eligibility check (active OR ≤24h) →
HMAC sign payload → send_invoice(XTR) → successful_payment →
Record (idempotent) → Notify both (10% commission)
```

**5. Safety Flow**
```
/report → Redis active_session → Inline keyboard (4 reasons) →
POST /reports (HMAC auth, rate limit) → Store report

/block → End session → Mark completed → Bilateral cooldown 30 days
```

---

## Directory Structure

```
NotAlone/
├── apps/
│   ├── api/               # FastAPI REST API
│   │   ├── routers/       # API endpoints (chat, match, reports, tips)
│   │   ├── deps.py        # Dependency injection (DB, Redis)
│   │   └── main.py        # FastAPI app entry point
│   │
│   ├── bot/               # Telegram bot (aiogram)
│   │   ├── handlers/      # Command handlers (start, profile, find, chat, tips, report, block, sos)
│   │   ├── middlewares/   # Rate limiting, database injection
│   │   ├── data/          # Static data (sos_ru.json for emergency hotlines)
│   │   ├── redis.py       # Active session management (TTL 24h)
│   │   ├── api_client.py  # HTTP client with HMAC signing
│   │   └── bot.py         # Bot entry point (webhook setup)
│   │
│   ├── workers/           # Background workers
│   │   └── match_worker.py  # Redis Streams consumer for matching
│   │
│   └── ai_coach/          # Optional AI features (future)
│       ├── anonymize.py   # PII removal before LLM
│       └── provider.py    # Prompt templates
│
├── core/
│   ├── config.py          # Pydantic settings (env vars)
│   ├── db.py              # SQLAlchemy async engine
│   ├── redis.py           # Redis async client
│   ├── security.py        # HMAC, password hashing, anonymization
│   ├── auth.py            # bot_auth (HMAC), admin_basic_auth
│   └── metrics.py         # Prometheus metrics
│
├── models/
│   ├── user.py            # User, Topic, UserTopic
│   ├── match.py           # Match, ChatSession
│   ├── tip.py             # Tip (Telegram Stars)
│   └── safety.py          # Report, ModerationAction (Sprint 5)
│
├── migrations/            # Alembic database migrations
│   └── versions/          # Migration files (timestamped)
│
├── tests/
│   ├── unit/              # Unit tests (business logic)
│   └── integration/       # Integration tests (API endpoints)
│
├── deploy/
│   └── compose.yml        # Docker Compose for all services
│
├── .env.example           # Environment variables template
├── pyproject.toml         # Python dependencies & config
├── Makefile               # Common commands (up, down, migrate, fmt, lint)
│
├── CLAUDE.md              # This file - AI assistant guidance
├── SPRINTS.md             # Complete development history (5 sprints)
└── Arhitecture1.md        # Detailed technical specification
```

---

## Data Models (Key Tables)

### users
- `id` (PK), `tg_id` (Telegram ID, unique), `nickname`, `tz` (timezone), `bio_short`, `safety_ack`, `created_at`

### topics
- 12 predefined: loneliness, burnout, anxiety, relocation, divorce, loss, illness, parenting, relationships, career, finance, identity

### user_topics (M2M)
- `user_id`, `topic_id`, `weight` (0.0-1.0 for future scoring)

### matches
- `id`, `user_a`, `user_b`, `u_lo`/`u_hi` (ordering for uniqueness), `status` (proposed/active/declined/expired/completed), `created_at`, `expires_at`

### chat_sessions
- `id`, `match_id`, `started_at`, `ended_at`, `msg_count_a`, `msg_count_b`, `rating_a`, `rating_b`

### tips
- `id`, `match_id`, `from_user`, `to_user`, `amount_minor` (stars), `currency` (XTR), `provider` (telegram-stars), `provider_fee_minor`, `our_commission_minor` (10%), `status`, `telegram_payment_id` (unique), `invoice_payload` (HMAC signed)

### reports (Sprint 5)
- `id`, `chat_session_id`, `from_user`, `to_user`, `reason` (spam/abuse/danger/other), `comment`, `status` (new/in_review/resolved), `created_at`, `closed_at`

### recent_contacts (Sprints 2 & 5)
- `user_id`, `other_id`, `until` (cooldown expiry)
- **Usage:** 72h after decline (Sprint 2), 30 days after block (Sprint 5)

---

## Development Commands

### Setup
```bash
make install              # Install dependencies
cp .env.example .env      # Create .env file (edit with real values)
```

### Running Services
```bash
make up                   # Start all services (Docker)
make down                 # Stop all services
make restart              # Restart everything

# Local development (DB/Redis in Docker, API/Bot local)
docker compose -f deploy/compose.yml up db redis -d
make dev-api              # Terminal 1: API with hot reload
make dev-bot              # Terminal 2: Bot
```

### Database
```bash
make migrate              # Apply migrations
make migrate-create       # Create new migration (autogenerate)
alembic history           # View migration history
alembic downgrade -1      # Rollback last migration
```

### Code Quality
```bash
make fmt                  # Format code (ruff, black, isort)
make lint                 # Lint & type check (mypy, ruff)
make test                 # Run tests with coverage
```

### Logs
```bash
make logs                 # All services
make logs-api             # API only
make logs-bot             # Bot only
make logs-worker          # Worker only
```

---

## Key Architectural Patterns

### 1. Async Throughout
**All I/O is async:** DB, Redis, HTTP, Telegram API
```python
# Good
async with AsyncSessionLocal() as db:
    result = await db.execute(select(User).where(User.tg_id == tg_id))

# Bad - don't use sync operations
session = Session()  # ❌
```

### 2. Dependency Injection (FastAPI)
```python
from apps.api.deps import get_db, get_redis_client

@router.post("/endpoint")
async def endpoint(
    db: AsyncSession = Depends(get_db),
    redis: redis.Redis = Depends(get_redis_client),
    caller_tg: int = Depends(bot_auth)  # HMAC auth
):
    ...
```

### 3. HMAC Authentication (Bot→API)
**All sensitive endpoints require HMAC signature:**
```python
# Bot side (apps/bot/api_client.py)
await api_client.post(
    "/reports",
    json={"to_user_tg": 123, "reason": "spam"},
    auth_bot=True,
    caller_tg_id=message.from_user.id
)

# API side (apps/api/routers/reports.py)
@router.post("", status_code=200)
async def create_report(
    body: ReportIn,
    db: AsyncSession = Depends(get_db),
    caller_tg: int = Depends(bot_auth)  # Validates HMAC signature
):
    ...
```

### 4. Redis Session Management
**Context-aware bot commands without reply_to_message:**
```python
# Store active session when chat starts
await set_active_session(tg_id, chat_session_id, peer_tg_id)

# Retrieve in /report or /block handlers
session = await get_active_session(tg_id)
if session:
    peer_tg_id = session["peer_tg_id"]
    chat_session_id = session["chat_session_id"]
```

### 5. Idempotency (Critical for Payments)
**Multiple layers:**
- **Redis locks:** `tips:cb:{callback.id}` EX 60 (prevent double-clicks)
- **DB unique constraints:** `UNIQUE(telegram_payment_id)`
- **Redis dedup:** `notif:tip:{charge_id}` EX 86400 (prevent duplicate notifications)

### 6. SQLAlchemy 2.x Syntax
```python
# ✅ Correct (SQLAlchemy 2.x)
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    nickname: Mapped[str] = mapped_column(String(64))

# ❌ Wrong (old syntax)
class User(Base):
    id = Column(BigInteger, primary_key=True)  # Don't use this
```

---

## Security & Privacy

### Authentication Methods
1. **Bot→API:** HMAC-SHA256 (headers: `X-Tg-User-Id`, `X-Bot-Signature`)
2. **Admin→API:** HTTP Basic Auth (`ADMIN_USER`, `ADMIN_PASS`)
3. **Tips Payload:** HMAC-signed invoice payload

### Rate Limiting
- **Reports:** 1 per 60 seconds (Redis: `rl:report:{tg_id}`)
- **Messages:** 15 per minute (Redis token bucket)
- **API:** Middleware-based rate limiting

### Privacy Measures
- ❌ No phone numbers collected
- ❌ No email addresses collected
- ❌ No geolocation data
- ❌ Messages NOT stored (only counters)
- ✅ Pseudonyms only
- ✅ PII anonymization before AI (if enabled)

### Safety Features (Sprint 5)
- `/report` - User-generated reports (4 reasons: spam/abuse/danger/other)
- `/block` - Immediate session termination + 30-day bilateral cooldown
- `/sos` - Emergency hotlines (Телефон доверия, Скорая помощь)
- Admin endpoints for moderation (future: web dashboard)

---

## Common Gotchas & Best Practices

### 1. SQLAlchemy 2.x
✅ Use `Mapped[type]` and `mapped_column()`
❌ Don't use old `Column()` syntax

### 2. Alembic Migrations
✅ Import all models in `migrations/env.py` for autogenerate
✅ Always review autogenerated migrations before applying
❌ Don't edit applied migrations (create new one instead)

### 3. Webhook vs Polling
✅ Bot uses webhooks (requires HTTPS)
❌ No long-polling mode supported

### 4. Async Sessions
✅ Always use `async with AsyncSessionLocal() as session`
❌ Don't reuse sessions across requests

### 5. Redis Streams
✅ Create consumer group before `XREADGROUP`: `XGROUP CREATE stream group $ MKSTREAM`
❌ Don't use same consumer ID across workers (use unique IDs)

### 6. Telegram Limits
- **Messages:** 30 per second per bot
- **Webhooks:** Must respond within 60 seconds
- **Rate limits:** Implement exponential backoff

### 7. Environment Variables
✅ All secrets in `.env` (never commit!)
✅ Use `.env.example` as template
❌ Never hardcode secrets in code

---

## Testing Strategy

### Unit Tests (`tests/unit/`)
- **Scoring algorithm** - matching logic
- **HMAC functions** - sign/verify
- **Anonymization** - PII removal
- **Business logic** - isolated from I/O

### Integration Tests (`tests/integration/`)
- **API endpoints** - with test DB
- **Bot handlers** - with mocked Telegram API
- **Worker** - with test Redis

### Manual Testing (Current Phase)
See [SPRINTS.md](SPRINTS.md) Sprint 5 section for testing checklist

**Target Coverage:** ≥70% on critical paths

---

## Production Deployment

### Recommended Infrastructure (EU Region)
- **API/Bot:** Render.com / Fly.io / Railway (EU location)
- **PostgreSQL:** Neon / Supabase (EU-West + pgBouncer)
- **Redis:** Upstash / Redis Cloud (EU region)
- **Monitoring:** Grafana Cloud + Sentry (EU)

### Health Checks
- `GET /health` - Basic status
- `GET /health/db` - PostgreSQL connection
- `GET /health/redis` - Redis connection
- `GET /metrics` - Prometheus metrics

### Pre-Deployment Checklist
- [ ] Set `INTERNAL_BOT_SECRET` (32+ bytes, random)
- [ ] Change `ADMIN_USER`/`ADMIN_PASS` from defaults
- [ ] Set `TIPS_HMAC_SECRET` (32+ bytes, random)
- [ ] Configure `PUBLIC_BASE_URL` for webhooks (HTTPS)
- [ ] Apply all migrations: `alembic upgrade head`
- [ ] Set up Grafana dashboards for metrics
- [ ] Configure Sentry for error tracking
- [ ] Test webhook with real Telegram Bot API

---

## Next Steps & Roadmap

### Immediate (Manual Testing)
- [ ] Test all flows end-to-end
- [ ] Verify HMAC authentication works
- [ ] Test rate limiting (reports, messages)
- [ ] Verify Telegram Stars payments (requires production bot)
- [ ] Test blocking flow (30-day cooldown)

### Short Term (Production Launch)
- [ ] Grafana dashboards for metrics
- [ ] Deploy to EU infrastructure
- [ ] Set up monitoring alerts
- [ ] Create admin web dashboard (review reports)
- [ ] User documentation (Russian)

### Medium Term (Post-Launch)
- [ ] AI Coach integration (empathy hints, safety suggestions)
- [ ] User rating system (1-5 stars post-chat)
- [ ] Advanced moderation (auto-flags based on reports)
- [ ] Match quality improvements (better scoring)
- [ ] Availability windows (timezone-aware scheduling)

### Future
- [ ] Mobile app (React Native?)
- [ ] Group chat support (3-5 people)
- [ ] Volunteer professional listeners
- [ ] Integration with mental health resources
- [ ] Multilingual support (English, Ukrainian)

---

## Additional Resources

- **[SPRINTS.md](SPRINTS.md)** - Complete development history (398 lines, concise)
- **[Arhitecture1.md](Arhitecture1.md)** - Detailed technical specification
- **[.env.example](.env.example)** - All environment variables with descriptions
- **[Makefile](Makefile)** - All common commands

---

## important-instruction-reminders

**When working on this codebase:**

1. **Do what has been asked; nothing more, nothing less.**
2. **NEVER create files unless absolutely necessary** - prefer editing existing files
3. **ALWAYS prefer editing existing files to creating new ones**
4. **NEVER proactively create documentation (*.md) or README files** - only if explicitly requested
5. **Use Serena MCP for code navigation/edits** - it's faster and more accurate
6. **Use Context7 MCP for library docs** - don't guess API usage
7. **Check [SPRINTS.md](SPRINTS.md) for context** - understand what's already built
8. **Async everywhere** - this is an async-first codebase
9. **HMAC for security** - all bot→API requests must be signed
10. **Privacy first** - no PII, anonymity by design

---

**Last Updated:** October 5, 2025
**MVP Status:** ✅ Complete (5 sprints, 47 tasks)
**Current Phase:** Manual testing & production deployment prep

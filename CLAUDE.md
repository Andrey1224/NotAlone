# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## MCP Tool Usage

the context in Arhitecture1.md

Always use context7 when I need code generation, setup or configuration steps, or
library/API documentation. This means you should automatically use the Context7 MCP
tools to resolve library id and get library docs without me having to explicitly ask.

Use Serena MCP for all code navigation and edits.

Если нужен браузер / UI‑действия → Playwright MCP.
Если нужен контекст из документов/кода/БД → Context7 MCP.
Если можно решить чистым кодом/локально → не трогай MCP.

## Project Overview

**"Ты не один" (You're Not Alone)** is a Telegram bot for peer-to-peer support matching. The platform connects users for anonymous 1-on-1 conversations based on shared life experiences and interests (e.g., burnout, relocation, loss).

The system is built with:
- **Python 3.12** with async/await patterns throughout
- **FastAPI** for REST API with ASGI deployment
- **aiogram 3.x** for Telegram Bot API integration (webhooks)
- **PostgreSQL 18** with SQLAlchemy 2.x ORM + Alembic migrations
- **Redis 7.4** for caching, rate limiting, and match queue (Redis Streams)
- **Telegram Stars (XTR)** for digital tipping system

## Architecture & Service Structure

The codebase follows a **microservices architecture** with 4 main services:

### 1. **API Service** (`apps/api/`)
- FastAPI application serving REST endpoints
- Webhook receiver for Telegram bot updates
- Health checks, match coordination, payment processing
- Entry point: `apps/api/main.py`

### 2. **Bot Service** (`apps/bot/`)
- Telegram bot using aiogram 3.x with webhook delivery
- Command handlers in `handlers/` (start, profile, find, tips)
- Inline/reply keyboards in `keyboards/`
- Rate limiting middleware in `middlewares/`
- Entry point: `apps/bot/bot.py`

### 3. **AI Coach Service** (`apps/ai_coach/`)
- Optional AI-powered conversation hints (empathy, questions, boundaries)
- Text anonymization before sending to LLM (`anonymize.py`)
- Prompt templates for sensitive topics (`provider.py`)
- Feature-flagged via `AI_ENABLED` env var
- Entry point: `apps/ai_coach/main.py`

### 4. **Match Worker** (`apps/workers/`)
- Background worker consuming Redis Streams for match queue
- Scoring algorithm: `0.6*tag_overlap + 0.2*time_overlap + 0.2*helpfulness_score`
- Finds candidates with ≥2 overlapping topics and timezone compatibility
- Entry point: `apps/workers/match_worker.py`

### Core Modules (`core/`)
- **config.py**: Pydantic Settings for environment variables
- **db.py**: Async SQLAlchemy engine, session factory, Base declarative class
- **redis.py**: Async Redis client singleton
- **security.py**: Token generation, password hashing, PII anonymization utilities

### Data Models (`models/`)
All models use SQLAlchemy 2.x mapped_column syntax:
- **User**: Telegram users with pseudonyms, timezone, bio
- **Topic/UserTopic**: Interest tags with weighted relationships
- **Match**: User pairings with status (proposed/active/declined/expired/completed)
- **ChatSession**: Dialog sessions with ratings
- **Tip**: Telegram Stars payments with commission tracking
- **AiHint/SafetyFlag**: AI coaching and moderation flags

## Development Commands

### Setup & Dependencies
```bash
# Install dependencies (includes dev tools)
pip install -e ".[dev]"

# Or use make
make install
```

### Running Services

**Full stack with Docker:**
```bash
make up          # Start all services (API, bot, worker, DB, Redis)
make down        # Stop all services
make restart     # Restart everything
```

**Local development (without Docker):**
```bash
# 1. Start only DB and Redis
docker compose -f deploy/compose.yml up db redis -d

# 2. Run API (in one terminal)
make dev-api     # uvicorn with --reload

# 3. Run bot (in another terminal)
make dev-bot     # python -m apps.bot.bot
```

### Database Migrations

```bash
# Apply all migrations
make migrate
# or: alembic upgrade head

# Create new migration (interactive)
make migrate-create
# or: alembic revision --autogenerate -m "description"

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

### Code Quality

```bash
# Auto-format code
make fmt         # Runs: ruff --fix, black, isort

# Lint/type check
make lint        # Runs: mypy, ruff check

# Run tests
make test        # pytest with coverage
pytest tests/unit            # Unit tests only
pytest tests/integration     # Integration tests only
```

### Logs & Monitoring

```bash
make logs          # All service logs
make logs-api      # API logs only
make logs-bot      # Bot logs only
make logs-worker   # Worker logs only
```

## Key Architectural Patterns

### Async Throughout
- All database operations use `AsyncSession`
- Redis operations use `redis.asyncio`
- Bot handlers are async functions
- Use `async with` for context managers

### Dependency Injection (FastAPI)
```python
from apps.api.deps import get_db, get_redis_client

@router.get("/endpoint")
async def endpoint(
    db: AsyncSession = Depends(get_db),
    redis: redis.Redis = Depends(get_redis_client)
):
    ...
```

### Environment Configuration
- All config via `core.config.Settings` (Pydantic)
- Load from `.env` file (see `.env.example`)
- Access via `from core.config import settings`

### Telegram Bot Webhooks
- Bot runs via webhooks, NOT polling
- Webhook URL: `{PUBLIC_BASE_URL}/telegram/webhook`
- Requires HTTPS with valid certificate
- Setup in `apps/bot/bot.py` on_startup hook

### Match Queue (Redis Streams)
- User requests written to Redis Stream on `/find`
- Worker consumes via consumer group
- TTL for queue entries (24h default)
- Anti-repeat table prevents duplicate recent matches

### Anonymity & Privacy
- No PII collection (phone/email/location)
- Pseudonyms only in User.nickname
- AI coach anonymizes text before LLM (removes IDs, emails, phones)
- See `apps/ai_coach/anonymize.py` for PII removal patterns

## Critical Implementation Notes

### Telegram Stars Payments
- Use Bot API 9.x methods for XTR currency
- Record `provider_fee_minor` and `our_commission_minor` in `Tip` model
- Webhook handler at `/payments/webhook/telegram-stars`
- Transparency: show itemized receipt in chat

### AI Coach Boundaries
- **NOT a therapist** - only coaching hints
- Suggestions shown only to sender (inline, private)
- Disabled by default (`AI_ENABLED=false`)
- Safety filters for toxicity, self-harm, etc.
- Always include disclaimers and crisis hotline links

### Database Indexes
- `user_topics.topic_id` indexed for match lookups
- `matches(user_a, user_b)` unique constraint
- GIN indexes planned for JSONB fields (availability windows)

### Testing Strategy
- Unit tests for business logic (scoring, anonymization)
- Integration tests for API endpoints with test DB
- Target: ≥70% coverage on critical paths
- Use pytest fixtures for DB/Redis setup

## Security Checklist

- ✅ Secrets in environment variables (never in code)
- ✅ Rate limiting via middleware (`RateLimitMiddleware`)
- ✅ HTTPS required for webhooks
- ✅ PII minimization and anonymization
- ✅ User consent flow (`safety_ack` field)
- ✅ Complaint/block system planned
- ✅ TLS 1.3 for production deployments

## Production Deployment

**Recommended infrastructure (EU region for RU/CIS users):**
- API/Bot: Render/Fly.io/Railway (EU location)
- PostgreSQL: Neon/Supabase (EU-West with pgBouncer)
- Redis: Upstash/Redis Cloud (EU region)
- Monitoring: Grafana Cloud + Sentry (EU)
- Object storage: Cloudflare R2 (EU)

**Health check endpoints:**
- `GET /health` - basic status
- `GET /health/db` - PostgreSQL connection
- `GET /health/redis` - Redis connection

## Common Gotchas

1. **SQLAlchemy 2.x syntax**: Use `Mapped[type]` and `mapped_column()`, not old `Column()` style
2. **Alembic imports**: Ensure all models imported in `migrations/env.py` for autogenerate
3. **Webhook vs Polling**: Bot uses webhooks only; no long-polling mode
4. **Async sessions**: Always use `async with AsyncSessionLocal() as session` pattern
5. **Redis Streams**: Consumer groups require `XGROUP CREATE` before `XREADGROUP`
6. **Telegram limits**: Bot API has rate limits; implement exponential backoff

## Next Steps (from TODO)

High-priority items from spec:
- [ ] Implement match queue consumer in `match_worker.py`
- [ ] Complete AI coach LLM integration (OpenAI/Anthropic)
- [ ] Telegram Stars payment webhook handler
- [ ] User rating system (1-5 stars post-chat)
- [ ] Moderation dashboard and safety flags
- [ ] Metrics export (Prometheus format)

---

For questions about architecture or implementation details, refer to [Arhitecture1.md](Arhitecture1.md) for the complete technical specification.

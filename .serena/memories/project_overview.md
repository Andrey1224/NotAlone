# NotAlone Project Overview

## Purpose
Telegram bot for peer-to-peer support matching. Anonymous communication platform for people who experienced similar life situations.

## Tech Stack
- **Backend:** Python 3.12, FastAPI, aiogram 3.x
- **Database:** PostgreSQL 18
- **Cache/Queue:** Redis 7.4
- **ORM:** SQLAlchemy 2.x + Alembic
- **Payments:** Telegram Stars (XTR)
- **AI:** OpenAI API (optional)
- **Deploy:** Docker, Docker Compose

## Main Features
- Smart matching by topics and timezone
- Anonymous communication with pseudonyms
- AI coaching hints (optional)
- Tipping system via Telegram Stars
- Safety system with reporting and moderation

## Project Structure
```
├── apps/
│   ├── api/              # FastAPI application
│   ├── bot/              # Telegram bot
│   ├── ai_coach/         # AI service for hints
│   └── workers/          # Background workers
├── core/                 # Base modules
├── models/               # SQLAlchemy models
├── migrations/           # Alembic migrations
├── deploy/               # Docker files
└── tests/                # Tests
```

## Entry Points
- **API:** FastAPI app in `apps/api/main.py`
- **Bot:** Telegram bot in `apps/bot/bot.py`
- **AI Coach:** AI service in `apps/ai_coach/main.py`
- **Workers:** Background workers in `apps/workers/`

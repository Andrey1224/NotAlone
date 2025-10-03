# Development Commands

## Main Commands
```bash
make help          # Show all available commands
make up            # Start all services (Docker)
make down          # Stop all services
make restart       # Restart all services (down + up)
make logs          # Show logs from all services
make logs-api      # Show API logs
make logs-bot      # Show bot logs
make logs-worker   # Show worker logs
make clean         # Clean up containers and volumes
```

## Database Commands
```bash
make migrate       # Apply database migrations
make migrate-create # Create new migration
alembic upgrade head      # Apply all migrations
alembic downgrade -1      # Rollback last migration
```

## Development Commands
```bash
make install       # Install dependencies
make dev-api       # Run API locally
make dev-bot       # Run bot locally
```

## Code Quality Commands
```bash
make fmt           # Format code (ruff, black, isort)
make lint          # Lint code (mypy, ruff)
make test          # Run tests with coverage
```

## Local Development
1. Start PostgreSQL and Redis: `docker compose -f deploy/compose.yml up db redis -d`
2. Run API: `make dev-api`
3. Run bot: `make dev-bot`

## System Commands (macOS)
- `ls` - list files
- `cd` - change directory
- `grep` - search text
- `find` - find files
- `git` - version control

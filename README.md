# Sigmatic

Signal aggregation, quality scoring & routing infrastructure for traders.

## Quickstart

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15 + Redis 7 (or use Docker)

### Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

The server starts at `http://localhost:8000`.

### Run locally

```bash
# Install
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Start dependencies
docker compose up -d postgres redis

# Run database migrations
export DATABASE_URL_SYNC=postgresql://sigmatic:sigmatic@localhost:5432/sigmatic
alembic upgrade head

# Start server
sigmatic serve
```

### Verify

```bash
curl http://localhost:8000/v1/health
# {"status":"healthy","database":"connected","redis":"connected","version":"0.1.0"}
```

API docs: http://localhost:8000/docs

### CLI

```bash
sigmatic --help
sigmatic serve --port 8000
```

## Project Structure

```
sigmatic/
├── sigmatic/          # Python package
│   ├── server/        # FastAPI application
│   │   ├── models/    # SQLAlchemy ORM models
│   │   ├── routes/    # API endpoints
│   │   ├── services/  # Business logic
│   │   └── adapters/  # Signal schema adapters
│   ├── cli/           # Click CLI
│   └── monitor/       # Static monitoring dashboard
├── migrations/        # Alembic migrations
└── tests/             # pytest tests
```

## Development

```bash
# Lint
ruff check sigmatic/

# Type check
mypy sigmatic/ --ignore-missing-imports

# Tests
pytest tests/ -v
```

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| P0 | Setup & Foundation | ✅ Complete |
| P1 | Core Pipeline | 🔜 Next |
| P2 | Quality & Routing | ⏳ Planned |
| P3 | Observability | ⏳ Planned |
| P4 | Internal Strategies | ⏳ Planned |
| P5 | Beta | ⏳ Planned |

# Predicta - Backend

FastAPI backend for the Predicta sales analytics platform.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Set up environment
cp .env.example .env
# Edit .env with your DATABASE_URL and SECRET_KEY

# Apply database migrations
alembic upgrade head

# Run the server
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000.

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Module Structure

```
app/
├── api/            # HTTP route handlers
│   ├── user_routes.py
│   ├── etl_routes.py
│   └── analytics_routes.py
├── core/           # Cross-cutting concerns
│   ├── database.py
│   └── security.py
├── models/         # SQLAlchemy ORM
├── schemas/        # Pydantic validation
├── services/       # Business logic
├── ml_models/      # Machine learning
└── main.py         # FastAPI application factory
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `SECRET_KEY` | Yes | - | JWT signing key (use `openssl rand -hex 32`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | JWT lifetime |
| `CORS_ORIGINS` | No | `*` | Comma-separated allowed origins |

## Database Migrations

This project uses [Alembic](https://alembic.sqlalchemy.org/) for schema versioning.

```bash
# Apply migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Testing

```bash
pytest                              # Run all tests
pytest --cov=app                    # With coverage
pytest tests/test_auth.py           # Single file
pytest -k test_register             # Single test by name
```

## Code Quality

```bash
ruff check app/                     # Lint
ruff check --fix app/               # Auto-fix lint issues
ruff format app/                    # Format
mypy app/                           # Static type check
```

## Generating Sample Data

```bash
python scripts/generate_dataset.py
```

Output: `ventas_3_anios_predicta.csv` (3 years of synthetic sales data).

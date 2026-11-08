# Predicta

> **Motor de análisis y predicción de ventas para PyMEs**
> Sales analytics and forecasting platform built with FastAPI, statsmodels, PostgreSQL, and React.

[![CI](https://github.com/StanleyRodr/Predicta/actions/workflows/ci.yml/badge.svg)](https://github.com/StanleyRodr/Predicta/actions/workflows/ci.yml)
[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Predicta helps small and medium retail businesses ingest their sales data, visualize trends, and forecast demand. Built as a thesis project focused on accessible data science for non-technical users.

---

## Features

- **Multi-format ETL** - CSV (`,` `;` or tab; UTF-8 or cp1252), XLSX, and `.sql` files with `INSERT ... VALUES` (parsed, never executed). Rows are validated one by one, the load is transactional, and an identical file is rejected.
- **Authentication** - OAuth2 password flow with JWT (PyJWT) and bcrypt hashes; roles Administrador / Usuario.
- **Dashboard** - Global KPIs and monthly series in general, by category, by month (with daily detail), and for the whole history, measured in amount or units.
- **Forecasting** - Monthly projection of up to 12 months, general or by category, with 95 % intervals, extrapolation marks, and metrics explained in plain Spanish; next-day projection. See [docs/ml-models.md](./docs/ml-models.md).
- **Reports** - Excel and PDF exports (history, annual projection, monthly, and by category).
- **Multi-tenant** - Every query is filtered by user; tests check each private endpoint.
- **Accessibility** - Keyboard-friendly dialogs and menus, and a text table behind every chart.

## Architecture

```
┌─────────────────┐      HTTP + JWT      ┌─────────────────┐
│  Frontend       │ ◀──────────────────▶ │  FastAPI        │
│  React 19 +     │                      │  Backend        │
│  Vite + TS      │                      │  (Python 3.14)  │
└─────────────────┘                      └────────┬────────┘
                                                  │
                                                  ▼
                                        ┌─────────────────┐
                                        │  PostgreSQL     │
                                        │  (SQLAlchemy +  │
                                        │   Alembic)      │
                                        └─────────────────┘
```

**Backend modules:**

| Module | Purpose |
|---|---|
| `app/api/` | HTTP route handlers (users, ETL, analytics) |
| `app/core/` | Settings, database session, security, rate limiting |
| `app/models/` | SQLAlchemy ORM models |
| `app/schemas/` | Pydantic validation schemas |
| `app/services/` | Business logic: ETL, analytics, reports, saved predictions |
| `app/ml_models/` | Regression forecasts and their evaluation |
| `alembic/` | Database migrations (the only schema source) |

## Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [SQLAlchemy 2](https://www.sqlalchemy.org/) + [Alembic](https://alembic.sqlalchemy.org/) - ORM and migrations
- [PostgreSQL 17](https://www.postgresql.org/) - Database
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Configuration
- [statsmodels](https://www.statsmodels.org/) + [pandas](https://pandas.pydata.org/) - Forecasting and data processing
- [Matplotlib](https://matplotlib.org/) + [FPDF2](https://py-pdf.github.io/fpdf2/) + [openpyxl](https://openpyxl.readthedocs.io/) - Reports
- [PyJWT](https://pyjwt.readthedocs.io/) + [bcrypt](https://github.com/pyca/bcrypt) - Auth

**Frontend**
- React 19 + TypeScript + Vite
- Tailwind CSS v4 + Chart.js (react-chartjs-2)
- TanStack Query + Axios + Zustand + React Router
- React Hook Form + Zod

**Tooling**
- [Ruff](https://github.com/astral-sh/ruff), [mypy](https://mypy-lang.org/), [pytest](https://docs.pytest.org/) - Backend quality
- ESLint, `tsc`, Vitest + React Testing Library - Frontend quality
- GitHub Actions and pre-commit

## Project Structure

```
Predicta/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── api/              # Route handlers
│   │   ├── core/             # Settings, DB, security
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── ml_models/        # Forecasting and evaluation
│   │   └── main.py
│   ├── alembic/              # DB migrations
│   ├── scripts/              # Dataset generator, model evaluation
│   ├── tests/                # Test suite
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
├── frontend/                 # React SPA
├── docs/                     # ML docs, evaluation, planning
├── .github/                  # CI workflow and templates
├── AGENTS.md / CLAUDE.md     # Instructions for coding agents
├── CHANGELOG.md
├── Makefile
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.14 (the CI version; the code needs 3.12 or later)
- PostgreSQL 17
- Node.js 24 (the CI version)

### 1. Clone the repository

```bash
git clone https://github.com/StanleyRodr/Predicta.git
cd Predicta
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Linux/Mac
# .\venv\Scripts\Activate.ps1   # Windows PowerShell

pip install -r requirements.txt -r requirements-dev.txt

# Create your local .env from the template, then set DATABASE_URL and SECRET_KEY
cp .env.example .env

# Generate a secure SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

`CORS_ORIGINS` defaults to the Vite dev server (`http://localhost:5173`). `*` is accepted only with `ENVIRONMENT=development`.

### 3. Database setup

```bash
createdb predicta_db
alembic upgrade head
```

### 4. Run the backend

```bash
# From backend/
uvicorn app.main:app --reload
```

The API checks the database on startup and serves its reference at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### 5. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

The app opens at http://localhost:5173. Set `VITE_API_URL` in `frontend/.env` when the API does not run at `http://localhost:8000`.

### 6. (Optional) Generate sample data

```bash
cd backend
python scripts/generate_dataset.py
```

This writes a `ventas_*.csv` file in `backend/` (ignored by git) that you can upload from the **Cargar ventas** page.

## Available Commands

The root `Makefile` wraps the backend commands. On Windows without GNU Make, run the command after `cd backend &&` in each target.

```bash
make help         # List all available commands
make install      # Install production deps
make install-dev  # Install dev + test deps
make run          # Run dev server
make test         # Run tests with coverage
make lint         # Run linter
make format       # Auto-format code
make typecheck    # Run mypy
make migrate      # Apply DB migrations
make migration msg="description"  # Create new migration
make seed         # Generate sample dataset
make clean        # Remove cache files
```

## Testing

```bash
# Backend, from backend/: in-memory SQLite, no PostgreSQL needed
pytest --cov=app --cov-report=term-missing

# Same suite on a disposable PostgreSQL database
TEST_DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/predicta_test pytest

# Frontend, from frontend/
npm run lint && npm run typecheck && npm test -- --run && npm run build
```

CI runs all of them on every push.

## Development Workflow

This project uses [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow):

1. Create a feature branch: `git checkout -b feat/short-description`
2. Commit following [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat(auth): add password reset endpoint
   fix(etl): handle malformed CSV rows gracefully
   docs: update setup instructions in README
   ```
3. Push and open a Pull Request
4. After review and CI passing, merge into `main`

## Roadmap

See [TASKS.md](./docs/planning/TASKS.md) for the task history, [CHANGELOG.md](./CHANGELOG.md) for changes, and [docs/](./docs/) for the ML documentation and evaluation. The API reference is generated at `/docs`.

- [x] Phase 1 (tasks 001-009): test baseline, safe errors, robust ETL, categories, ML extraction, schema, regression and metrics, date filters, PyJWT
- [x] Phase 1 frontend (tasks 010-014): foundation, auth and layout, upload and history, dashboard, predictions and reports
- [x] Phase 2 (tasks 015-031): CI, migrations, hardened ETL, number format, reports as services, 12-month model with baselines, forecast contract, dashboard views, projection charts, plain-language metrics, accessibility, settings and auth, isolation tests on SQLite and PostgreSQL, cleanup

## Acknowledgments

Built as a thesis project demonstrating practical data science for retail SMEs.

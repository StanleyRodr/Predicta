# Predicta

> **Motor de análisis y predicción de ventas para PyMEs**
> Data Science & Retail platform built with FastAPI, scikit-learn, and PostgreSQL.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Predicta helps small and medium retail businesses ingest their sales data, visualize trends, and forecast demand using machine learning. Built as a thesis project focused on accessible data science for non-technical users.

---

## Features

- **Multi-format ETL** - Ingest sales data from CSV, Excel, or SQL files
- **Authentication** - JWT-based auth with role-based access control (Admin / User)
- **Analytics dashboard** - Global metrics, category breakdown, temporal evolution
- **Demand forecasting** - Linear regression with monthly seasonality (12-month horizon)
- **Reports** - Excel and PDF exports with charts and projections
- **Multi-tenant** - Data isolation per user

## Architecture

```
┌─────────────────┐      HTTPS/JWT       ┌─────────────────┐
│  Frontend       │ ◀──────────────────▶ │  FastAPI        │
│  (React +       │                      │  Backend        │
│   TailwindCSS)  │                      │  (Python)       │
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
| `app/core/` | Database session, security utilities |
| `app/models/` | SQLAlchemy ORM models |
| `app/schemas/` | Pydantic validation schemas |
| `app/services/` | Business logic layer |
| `app/ml_models/` | Machine learning predictors |
| `app/utils/` | Shared helpers |
| `alembic/` | Database migrations |

## Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [SQLAlchemy 2.0](https://www.sqlalchemy.org/) - ORM
- [Alembic](https://alembic.sqlalchemy.org/) - Migrations
- [PostgreSQL 16](https://www.postgresql.org/) - Database
- [scikit-learn](https://scikit-learn.org/) - ML
- [pandas](https://pandas.pydata.org/) - Data processing
- [Matplotlib](https://matplotlib.org/) + [FPDF2](https://py-pdf.github.io/fpdf2/) - Reports
- [python-jose](https://github.com/mpdavis/python-jose) + [passlib](https://passlib.readthedocs.io/) - Auth

**Frontend** (planned)
- React 18 + TypeScript + Vite
- TailwindCSS + Chart.js
- TanStack Query + React Hook Form + Zod

**Tooling**
- [Ruff](https://github.com/astral-sh/ruff) - Linter and formatter
- [pytest](https://docs.pytest.org/) - Testing
- [mypy](https://mypy-lang.org/) - Type checking
- [slowapi](https://github.com/laurentS/slowapi) - Rate limiting
- [loguru](https://github.com/Delgan/loguru) - Logging

## Project Structure

```
Predicta/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── api/              # Route handlers
│   │   ├── core/             # DB & security
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── ml_models/        # ML predictors
│   │   └── main.py
│   ├── alembic/              # DB migrations
│   ├── scripts/              # Utility scripts
│   ├── tests/                # Test suite
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
├── frontend/                 # React frontend (planned)
├── database/                 # Schema reference
├── data/                     # Generated datasets
├── docs/                     # Extended documentation
├── .github/                  # GitHub templates & CI
├── .editorconfig
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── Makefile
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 16 (or Docker)
- Node.js 18+ (for the frontend, once implemented)

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/predicta.git
cd predicta
```

### 2. Backend setup

```bash
# Create and activate virtual environment
cd backend
python -m venv venv
source venv/bin/activate        # Linux/Mac
# .\venv\Scripts\Activate.ps1   # Windows PowerShell

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Create your local .env from the template
cp .env.example .env
# Edit .env and set DATABASE_URL and SECRET_KEY

# Generate a secure SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Database setup

Make sure PostgreSQL is running and the database exists:

```bash
createdb predicta_db
```

Apply the schema. **Recommended (Alembic):**
```bash
alembic upgrade head
```

**Or apply the seed file directly (development only):**
```bash
psql -U postgres -d predicta_db -f ../database/seed.sql
```

### 4. Run the backend

```bash
# From backend/ directory
uvicorn app.main:app --reload
```

The API will be available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### 5. (Optional) Generate sample data

```bash
cd backend
python scripts/generate_dataset.py
```

This creates `ventas_3_anios_predicta.csv` in `backend/`, which you can upload via `POST /etl/upload-ventas`.

## Available Commands

The project includes a `Makefile` for common tasks:

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

## Development Workflow

This project uses [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow):

1. Create a feature branch: `git checkout -b feature/short-description`
2. Make your changes following [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat(auth): add password reset endpoint
   fix(etl): handle malformed CSV rows gracefully
   docs: update setup instructions in README
   ```
3. Push and open a Pull Request
4. After review and CI passing, squash-merge into `main`
5. Tag releases: `git tag -a v0.2.0 -m "Release 0.2.0"`

## Testing

```bash
make test
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/users/register` | Create new account |
| `POST` | `/users/login` | Get JWT token |
| `GET` | `/users/me` | Get current user |
| `PUT` | `/users/me` | Update current user |
| `POST` | `/etl/upload-ventas` | Upload CSV/Excel/SQL |
| `DELETE` | `/etl/clear-history` | Purge all sales for current user |
| `GET` | `/analytics/stats` | Global metrics |
| `GET` | `/analytics/stats/categories` | By-category breakdown |
| `GET` | `/analytics/stats/temporal` | Daily evolution |
| `GET` | `/analytics/ventas` | Paginated sales history |
| `GET` | `/analytics/predict` | Next-day forecast |
| `GET` | `/analytics/export/excel` | Download Excel report |
| `GET` | `/analytics/export/pdf` | Download PDF report |
| `GET` | `/analytics/reporte-predictivo-anual-pdf` | Annual forecast PDF |
| `GET` | `/analytics/reporte-mensual/{mes}` | Monthly report PDF |
| `GET` | `/analytics/prediccion-categorias/{categoria}` | Category forecast PDF |
| `GET` | `/health` | Health check |

## Roadmap

See [CHANGELOG.md](./CHANGELOG.md) for current progress and [docs/](./docs/) for detailed documentation.

- [x] Sprint 1+2: Security hardening, schema unification, Alembic, project structure
- [ ] Sprint 3: ML refactor (extract predictors to `ml_models/`)
- [ ] Sprint 4: Test suite (≥60% coverage), Docker setup
- [ ] Sprint 5: Frontend auth + dashboard
- [ ] Sprint 6: Frontend upload + analytics + reports
- [ ] Sprint 7: Model upgrade (Prophet/SARIMA), CI/CD, full docs

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Acknowledgments

Built as a thesis project demonstrating practical data science for retail SMEs.

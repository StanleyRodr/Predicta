# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Predicta is a thesis project: a sales analytics and forecasting platform for retail SMEs. `backend/` is a FastAPI + SQLAlchemy 2.0 + PostgreSQL API; `frontend/` is a React 19 + TypeScript + Vite SPA that consumes it. `AGENTS.md` holds additional agent rules (note: its claim that `frontend/` is planning-only is outdated — the frontend is implemented).

## Commands

The host is Windows and GNU Make may be unavailable; each `make` target is a thin wrapper, so run the underlying command from `backend/` when needed.

Backend (from `backend/`):

```bash
pip install -r requirements.txt -r requirements-dev.txt   # make install-dev
uvicorn app.main:app --reload                             # make run (port 8000)
alembic upgrade head                                      # make migrate
alembic revision --autogenerate -m "description"          # make migration msg="..."
python scripts/generate_dataset.py                        # make seed -> backend/ventas_*.csv (gitignored)
ruff check app/                                           # make lint
ruff check --fix app/ && ruff format app/                 # make format (only when intentionally reformatting)
mypy app/                                                 # make typecheck
pytest --cov=app --cov-report=term-missing                # make test
pytest tests/test_auth.py                                 # single file
pytest -k test_register                                   # single test by name
```

Frontend (from `frontend/`):

```bash
npm install
npm run dev                          # Vite on http://localhost:5173
npm run lint                         # eslint .
npm run typecheck                    # tsc --noEmit
npm test -- --run                    # Vitest, single run (plain `npm test` watches)
npx vitest run src/api/auth.test.ts  # single test file
npm run build                        # tsc -b && vite build
```

Before submitting: backend `make lint`, `make typecheck`, `make test`; frontend `npm run lint`, `npm run typecheck`, `npm test -- --run`, `npm run build`.

## Environment

- `backend/.env` (from `.env.example`) must define `DATABASE_URL` (`postgresql+psycopg2://...`) and `SECRET_KEY`. `app/core/database.py` reads `os.environ["DATABASE_URL"]` at import time, so importing the app without it fails. `CORS_ORIGINS` (comma-separated, default `*`) and `LOG_LEVEL` are optional.
- App startup (`lifespan` in `app/main.py`) runs `SELECT 1` and aborts if the database is unreachable.
- `tests/conftest.py` sets `DATABASE_URL=sqlite:///:memory:` *before* importing the app, overrides `get_db` with a fresh in-memory SQLite DB per test (built via `Base.metadata.create_all`, test-only), and disables the slowapi rate limiter. Use the `client`, `user_credentials`, and `auth_headers` fixtures for authenticated requests.
- Frontend reads `VITE_API_URL` (default `http://localhost:8000`).

## Backend architecture

- `app/main.py` wires CORS, slowapi rate limiting (login), loguru logging, health probes (`/health`, `/health/db`), and three routers: `user_routes` (`/users`), `etl_routes` (`/etl`), `analytics_routes` (`/analytics`).
- **Auth:** OAuth2 password flow at `POST /users/login` (form field `username` is the email) returns a PyJWT token whose `sub` is the user id. `app/api/deps.py::get_current_user` resolves it; `require_role("Administrador")` gates by role. Do not reintroduce `python-jose`.
- **Multi-tenancy:** every `Venta`/`Prediccion` query must be filtered by the current user's `id_usuario`; tests assert per-user isolation.
- **ETL** (`etl_routes.py`): parses CSV (auto-detects `,` `;` tab; UTF-8 with cp1252 fallback), XLSX, and `.sql` files (only `INSERT ... VALUES` is parsed — SQL is never executed). Rows are validated before building `Venta` (no silent `0.0` amounts or "today" dates; `cantidad` defaults to 1, negatives rejected); insertion is transactional; the response reports read/inserted/rejected counts with bounded per-row errors.
- **Categories:** `services/category_service.normalize_category` is the single canonicalization point (case/whitespace/accents) used both on ingest and on report filters; unknown categories are preserved, not mapped to "General".
- **ML** (`app/ml_models/forecast.py`, documented in `docs/ml-models.md`): multiple linear regression with separate targets for `monto` and `cantidad` over the same features — monthly model `mes_indice` + 12 month dummies, daily model `dia_indice` + 7 weekday dummies, in a fixed column order. R²/MAPE/RMSE come from a chronological last-20% holdout; intervals are ±1.96·σ of residuals clipped at zero. Months/days without data are absent, never zero-filled. Routes call this module rather than training models inline.
- **Analytics** (`analytics_routes.py`): stats/categories/temporal endpoints share `_apply_date_range` (`fecha_desde`/`fecha_hasta`, inverted range → 422); `/predict` persists a `Prediccion`; Excel and PDF exports (Matplotlib + FPDF2) are generated in the same module.
- **Errors:** 500 responses and `/health/db` return generic Spanish messages; full exceptions go only to logs. Never put `str(exc)` in a response body.
- **Schema:** Alembic-only (`backend/alembic/versions/`). Never add runtime `create_all()`. After model changes, autogenerate a migration, review it manually, and check that it downgrades.

## Frontend architecture

- `src/api/http.ts` is the shared Axios instance: it injects the Bearer token from the Zustand `authStore` (persisted to localStorage) and, on any 401, clears the session and dispatches a `predicta:unauthorized` window event that `App.tsx` turns into a redirect to `/login`.
- `src/api/*.ts` hold one typed client per backend area (auth, etl, analytics, forecast, reports) with matching types in `src/types/`; server state goes through TanStack Query. Forecasts are fetched only on explicit user action (no auto-fetch or refetch-on-focus), and report downloads are handled as blobs.
- Routing (`App.tsx`): public `/`, `/login`, `/register`; everything else sits behind `ProtectedRoute` + `AppShell`, with Dashboard/Predictions/Reports lazy-loaded.
- Forms use React Hook Form + Zod (`src/lib/authSchemas.ts`); styling is Tailwind CSS v4 with hand-written primitives in `src/components/ui/`; charts use Chart.js via react-chartjs-2.
- Tests (Vitest + React Testing Library, jsdom, setup in `src/test/setup.ts`) sit next to the code as `*.test.ts(x)`.

## Conventions and workflow

- Code, docstrings, and comments are in English; user-facing API messages and UI text are in Spanish.
- Work is planned in `docs/planning/TASKS.md` (status table) with one detailed plan per task in `docs/planning/plans/NNN-*.md`. When executing a task, read its plan fully, run each listed verification, stop and report on any STOP condition, and update the task status in `docs/planning/TASKS.md`. Do not edit the root `README.md` as part of these tasks, and do not add an index inside `docs/planning/plans/`.
- Commits follow Conventional Commits on feature branches (GitHub Flow).
- Project skills: `.agents/skills/` is the source of truth (opencode, tracked by `skills-lock.json`); `.claude/skills/` is a copy for Claude Code (without the opencode-only `agents/` subfolders). `code-review` is copied as `code-review-spec` to avoid shadowing Claude Code's built-in `/code-review`. After adding or updating a skill in `.agents/skills/`, re-copy it to `.claude/skills/`.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Predicta is a thesis project: a sales analytics and forecasting platform for retail SMEs. `backend/` is a FastAPI + SQLAlchemy 2.0 + PostgreSQL API; `frontend/` is a React 19 + TypeScript + Vite SPA that consumes it. `AGENTS.md` holds the same rules for other agents; keep both files consistent when changing a rule. Python 3.14 in CI (code needs 3.12+), Node 24.

## Commands

Backend (from `backend/`, with `venv` active):

```bash
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload                             # port 8000
alembic upgrade head
alembic revision --autogenerate -m "description"
python scripts/generate_dataset.py                        # -> backend/ventas_*.csv (gitignored)
ruff check app/                                           # lint
ruff check --fix app/ && ruff format app/                 # only when intentionally reformatting
mypy                                                      # typecheck (pyproject sets files = app)
python scripts/evaluate_models.py                         # regenerate docs/evaluacion/
pytest --cov=app --cov-report=term-missing                # full suite
pytest tests/test_auth.py                                 # single file
pytest -k test_register                                   # single test by name
```

Frontend (from `frontend/`):

```bash
npm install
npm run dev                          # Vite on http://localhost:5173
npm run lint                         # eslint .
npm run typecheck                    # tsc -b
npm test -- --run                    # Vitest, single run (plain `npm test` watches)
npx vitest run src/api/auth.test.ts  # single test file
npm run build                        # tsc -b && vite build
```

Before submitting: backend `ruff check app/`, `mypy`, `pytest --cov=app`; frontend `npm run lint`, `npm run typecheck`, `npm test -- --run`, `npm run build`. CI (`.github/workflows/ci.yml`, every push) also runs `alembic upgrade head`, `alembic check`, `alembic downgrade -1`, `alembic upgrade head` against PostgreSQL 17, so a model change without a matching migration fails CI.

## Environment

- `app/core/config.py` (`pydantic-settings`) is the only place that reads the environment and `backend/.env`; declare every new variable there and in `.env.example`. `DATABASE_URL` (`postgresql+psycopg2://...`) and `SECRET_KEY` are required, so importing the app without them fails. Optional: `ENVIRONMENT` (`development`/`test`/`production`, unset means production), `CORS_ORIGINS` (comma-separated, default `http://localhost:5173`; `*` only with `ENVIRONMENT=development`), `ACCESS_TOKEN_EXPIRE_MINUTES`, `LOG_LEVEL`, `MAX_UPLOAD_ROWS`.
- Passwords are hashed with `bcrypt` directly (no `passlib`) and limited to 72 bytes; new users get the `Usuario` role looked up by name.
- App startup (`lifespan` in `app/main.py`) runs `SELECT 1` and aborts if the database is unreachable.
- `tests/conftest.py` sets `DATABASE_URL=sqlite:///:memory:` *before* importing the app, overrides `get_db` with a fresh in-memory SQLite DB per test (built via `Base.metadata.create_all`, test-only), and disables the slowapi rate limiter. With `TEST_DATABASE_URL` set to a disposable PostgreSQL database, the same suite runs on PostgreSQL instead (tables are truncated before each test); CI runs both. Use the `client`, `user_credentials`, and `auth_headers` fixtures for authenticated requests, and `second_user` for another user's headers. Every private endpoint must be listed in `tests/test_isolation.py::PRIVATE_CASES`.
- Frontend reads `VITE_API_URL` (default `http://localhost:8000`).

## Backend architecture

- `app/main.py` wires CORS, slowapi rate limiting (login), loguru logging, health probes (`/health`, `/health/db`), and three routers: `user_routes` (`/users`), `etl_routes` (`/etl`), `analytics_routes` (`/analytics`).
- **Auth:** OAuth2 password flow at `POST /users/login` (form field `username` is the email) returns a PyJWT token whose `sub` is the user id. `app/api/deps.py::get_current_user` resolves it; `require_role("Administrador")` gates by role. Do not reintroduce `python-jose`.
- **Multi-tenancy:** every `Venta`/`Prediccion` query must be filtered by the current user's `id_usuario`; tests assert per-user isolation.
- **ETL** (`etl_routes.py` maps errors to HTTP; parsing/validation/loading live in `services/etl_service.py`): uploads are size-limited and SHA-256 hashed — re-uploading the same file for the same user is rejected via `CargaArchivo` (`DELETE /etl/clear-history` removes sales and hashes). Parses CSV (auto-detects `,` `;` tab; UTF-8 with cp1252 fallback), XLSX, and `.sql` files (only `INSERT ... VALUES` is parsed — SQL is never executed). Rows are validated before building `Venta` (no silent `0.0` amounts or "today" dates; `cantidad` defaults to 1, negatives rejected); insertion is transactional; the response reports read/inserted/rejected counts with bounded per-row errors.
- **Categories:** `services/category_service.normalize_category` is the single canonicalization point (case/whitespace/accents) used both on ingest and on report filters; unknown categories are preserved, not mapped to "General".
- **ML** (`app/ml_models/forecast.py`, documented in `docs/ml-models.md`): `statsmodels.OLS` with an intercept and separate targets for `monto` and `cantidad` over the same features. `monthly_forecast_series` is the single monthly path: an incomplete last month is left out of the fit and projected first; fewer than 6 complete months raises `InsufficientHistoryError`; 6–23 months fit trend only (`mes_indice` = calendar months elapsed) with a horizon of half the months; 24–35 months fit trend only with a 12-month horizon; 36+ months with every calendar month observed add `mes_2`…`mes_12` (January is the reference). Seasonality starts at 36 because with 24 it lost to the same-month-last-year baseline in the backtest. Points from month 7 are flagged `extrapolacion`. The daily model grows from mean (2 days) to trend (3+) to trend + `dia_2`…`dia_7` (14+ days, Monday reference). Intervals are 95 % observation intervals from `get_prediction`, clipped at zero. Monthly metrics (R², MAPE, MAE, RMSE, WAPE, MASE, improvement over the best baseline; MAE and RMSE via `sklearn.metrics`) come from refitting at each of the last 6 months and predicting the next one unseen (`app/ml_models/evaluation.py`); unavailable metrics stay `null`. Daily metrics use a chronological last-20% holdout. `scripts/evaluate_models.py` regenerates `docs/evaluacion/`; rerun it whenever model features change. Months/days without data are absent, never zero-filled. Routes call this module rather than training models inline.
- **Analytics** (`analytics_routes.py`, a thin layer over `services/analytics_service.py`, `report_service.py`, and `prediction_service.py`): stats/categories/temporal/series endpoints share the inclusive `fecha_desde`/`fecha_hasta` range (inverted range → 422). No GET writes: `/predict` (next day) and `/forecast?categoria=` (monthly series) only read, and history too short to project answers 422 with a Spanish `detail`. `POST /predicciones` recomputes on the server and saves one row per projected month under one `lote`; `GET /predicciones` pages saved batches. Every JSON route declares `response_model`. Excel and PDF exports (Matplotlib `Figure` objects + FPDF2) live in `report_service`.
- **Errors:** 500 responses and `/health/db` return generic Spanish messages; full exceptions go only to logs. Never put `str(exc)` in a response body.
- **Schema:** Alembic-only (`backend/alembic/versions/`). Never add runtime `create_all()`. After model changes, autogenerate a migration, review it manually, and check that it downgrades.

## Frontend architecture

- `src/api/http.ts` is the shared Axios instance: it injects the Bearer token from the Zustand `authStore` (persisted to localStorage) and, on any 401, clears the session and dispatches a `predicta:unauthorized` window event that `App.tsx` turns into a redirect to `/login`.
- `src/api/*.ts` hold one typed client per backend area (auth, etl, analytics, forecast, reports) with matching types in `src/types/`; server state goes through TanStack Query. Forecasts are fetched only on explicit user action (no auto-fetch or refetch-on-focus), and report downloads are handled as blobs.
- Routing (`App.tsx`): public `/`, `/login`, `/register`; everything else sits behind `ProtectedRoute` + `AppShell`, with Dashboard/Predictions/Reports lazy-loaded.
- Forms use React Hook Form + Zod (`src/lib/authSchemas.ts`); styling is Tailwind CSS v4 with hand-written primitives in `src/components/ui/`; charts use Chart.js via react-chartjs-2, wrapped in the accessible `ChartFrame`.
- Tests (Vitest + React Testing Library, jsdom, setup in `src/test/setup.ts`) sit next to the code as `*.test.ts(x)`.

## Conventions and workflow

- Code, docstrings, and comments are in English; user-facing API messages and UI text are in Spanish.
- Work is planned in `docs/planning/TASKS.md` (status table) with one detailed plan per task in `docs/planning/plans/NNN-*.md`. When executing a task, read its plan fully, run each listed verification, stop and report on any STOP condition, and update the task status in `docs/planning/TASKS.md`. Do not edit the root `README.md` as part of these tasks, and do not add an index inside `docs/planning/plans/`.
- Commits follow Conventional Commits on feature branches (GitHub Flow).
- Project skills: `.agents/skills/` is the source of truth (opencode, tracked by `skills-lock.json`); `.claude/skills/` is a copy for Claude Code (without the opencode-only `agents/` subfolders). `code-review` is copied as `code-review-spec` to avoid shadowing Claude Code's built-in `/code-review`. After adding or updating a skill in `.agents/skills/`, re-copy it to `.claude/skills/`.

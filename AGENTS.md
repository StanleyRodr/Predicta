# Agent Instructions

## Repository Shape

- `backend/` is the implemented application: a FastAPI service with routes in `app/api/`, cross-cutting setup in `app/core/`, SQLAlchemy models in `app/models/`, Pydantic schemas in `app/schemas/`, business logic in `app/services/`, and migrations in `alembic/`.
- `frontend/` is the implemented React 19 + TypeScript + Vite SPA that consumes the API: typed clients in `src/api/`, TanStack Query for server state, Tailwind CSS v4 primitives in `src/components/ui/`, Chart.js charts wrapped in the accessible `ChartFrame`, and Vitest tests next to the code.
- Treat `backend/alembic/` as the authoritative schema history; do not maintain a second SQL schema copy.

## Setup And Runtime

- Use Python 3.14 (the CI version; the code needs 3.12+) and install from `backend/`: `pip install -r requirements.txt -r requirements-dev.txt`.
- Copy `backend/.env.example` to `backend/.env` and set `DATABASE_URL` and a real `SECRET_KEY` before importing or running the app. `app/core/config.py` is the only module that reads the environment; importing the app without both values fails. `CORS_ORIGINS` defaults to `http://localhost:5173`, and `*` is accepted only with `ENVIRONMENT=development`. Unset `ENVIRONMENT` means production, which requires a `SECRET_KEY` of 32+ characters and `sslmode=require` (or `verify-ca`/`verify-full`) in `DATABASE_URL`, so a local `.env` sets `ENVIRONMENT=development`. `TRUSTED_PROXIES` (default `127.0.0.1`) lists the proxies whose `X-Forwarded-For` is believed for rate limits. Mail uses `EMAIL_BACKEND` (`console` logs messages; production requires `smtp` with `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, or `brevo_api` with `BREVO_API_KEY` (Railway Hobby blocks SMTP), plus `EMAIL_FROM` and an `https://` `FRONTEND_URL`). Loguru sinks are added only through `app.main.add_log_sink`, with `diagnose` and `backtrace` off.
- PostgreSQL is required for normal runtime and migrations. Apply pending migrations from `backend/` with `alembic upgrade head` before starting the API.
- Start the development server from `backend/` with `uvicorn app.main:app --reload`. Startup performs a live database connectivity check.

## Verification

- Run focused tests from `backend/`, for example `pytest tests/test_auth.py` or `pytest -k test_register`; run the full suite with `pytest --cov=app --cov-report=term-missing`.
- Tests do not need PostgreSQL: `backend/tests/conftest.py` sets `DATABASE_URL=sqlite:///:memory:` before importing the app and gives each test a fresh in-memory SQLite database. Set `TEST_DATABASE_URL` to a disposable PostgreSQL database to run the same suite on PostgreSQL.
- Every private endpoint must appear in `backend/tests/test_isolation.py::PRIVATE_CASES`; a test fails when a route is missing.
- Before submitting backend changes, run from `backend/`: `ruff check app/`, `mypy app/`, and `pytest --cov=app --cov-report=term-missing`; run `ruff check --fix app/ && ruff format app/` only when intentionally applying Ruff fixes/formatting. Ruff includes the security rules (`S`, flake8-bandit); every `noqa: S...` states its reason.
- Before submitting frontend changes, run from `frontend/`: `npm run lint`, `npm run typecheck`, `npm test -- --run`, and `npm run build`.
- `.github/workflows/ci.yml` runs lint, types, migrations (`upgrade`, `check`, `downgrade`), the backend suite on SQLite and PostgreSQL, the frontend checks, and the security scanners on every push: `pip-audit` and `npm audit --omit=dev --audit-level=high` fail on high or critical vulnerabilities in production dependencies, and the `secrets` job runs gitleaks over the full history. Every ignored advisory carries its reason in `ci.yml`.

## Data And Schema Changes

- Do not restore runtime `Base.metadata.create_all()`: schema management is intentionally Alembic-only.
- After changing SQLAlchemy models, create a migration from `backend/` with `alembic revision --autogenerate -m "description"`, review it, then apply it with `alembic upgrade head`.
- Generate synthetic data with `python scripts/generate_dataset.py` from `backend/` (seed 2026 and a fixed start date by default); it writes the ignored `backend/ventas_*.csv` artifact. The thesis dataset comes from `DatosDePrueba/ventas_fabricadas/generar_ventas.py`.
- Run the thesis experiment with `python scripts/run_experiment.py` from `backend/`: it generates the dataset, loads it through the ETL on in-memory SQLite (the only place `create_all` is allowed, inside that throwaway database), fits the model, and writes `docs/resultados/metricas_<date>.json`. Regenerate `docs/evaluacion/` with `python scripts/evaluate_models.py` whenever model features change.
- Never commit `.env`, credentials, generated datasets, coverage/cache directories, or saved model artifacts; the root `.gitignore` excludes them.

## Code Conventions

- Ruff is the configured linter and formatter; mypy is the configured type checker. Keep four-space Python indentation and follow `.editorconfig`.
- Keep docstrings/comments in English and user-facing API messages in Spanish, matching the existing backend convention.
- Field limits and patterns live in `backend/app/schemas/schemas.py` and are repeated in `frontend/src/lib/fieldLimits.ts`; change both, or `backend/tests/test_field_limits_contract.py` fails. Emails are stored lowercase, 422 responses never echo the submitted value, and Excel exports pass text through `neutralize_formula`.
- Deployment is documented in `docs/despliegue.md` (Vercel, Railway with `backend/railway.json`, Neon, Brevo). The frontend CSP lives in `frontend/csp.ts` and is repeated in `frontend/vercel.json`; a new external origin goes in both, or `src/test/csp.test.ts` fails.
- API documentation is generated by FastAPI at `/docs`, `/redoc`, and `/openapi.json` (hidden with `ENVIRONMENT=production`); update route/schema code rather than maintaining a separate endpoint list.
- Rate limits are constants in `backend/app/core/rate_limit.py` (login 5/min, register 3/min, uploads 10/min, forecasts and reports 20/min, any other route 120/min). A new costly route declares one with `@limiter.limit(...)` and a `request: Request` parameter. Request bodies are capped at 26 MB on `/etl/*` and 1 MB elsewhere (`app/core/middleware.py`).
- Login requires a confirmed e-mail (403 otherwise). E-mails go only through `backend/app/services/email_service.py` and single-use tokens only through `token_service.py` (SHA-256 stored, never the token). Backend tests capture mail with the autouse `outbox` fixture; `auth_headers` and `second_user` users are already confirmed.
- Every JWT carries `ver`, checked against `usuarios.version_token`; raising it (password change or reset) is the only way to close sessions. Ten wrong passwords in a row lock an account for 15 minutes (423). Lockout and link timings live in `backend/app/core/security.py`, with `security.utcnow` as the single clock (`clock` fixture in tests).

## Project-Local Skills

- Skills for this repository live under `.agents/skills/` and are tracked by `skills-lock.json`; use them before installing global alternatives.
- Keep future skill installations project-local: run `npx skills add ... --agent opencode --copy -y` from the repository root and do not use `-g`.

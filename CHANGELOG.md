# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Task numbers refer to [docs/planning/TASKS.md](./docs/planning/TASKS.md).

## [Unreleased]

### Phase 4 - product forecasts (task 034)

#### Added
- Monthly projections of amount and quantity for one product within its category: `producto` on `GET /analytics/forecast` and `POST /analytics/predicciones`, saved in the new `predicciones.producto` column (034).
- `GET /analytics/productos?categoria=` lists a category's products; `GET /analytics/ventas` filters by `producto` (034).
- A product select on /predictions and on the sales history that is enabled only after choosing a category; a product is compared with its category when their models differ, and saved batches read "Bebidas · Coca Cola" (034).

#### Changed
- Product names are stored with single spaces and each word capitalized; migration `0006` rewrites existing sales and cannot restore the original spelling on downgrade (034).

### Phase 3 - user review (tasks 032-033)

#### Fixed
- Info panels float on the page body next to their button, so opening one inside a table no longer adds scrollbars; they open above when there is no room below and stay inside the screen (033).
- Saved projections explain the 95 % range and extrapolation once above the list instead of inside every batch table (033).

#### Added
- Info buttons on /predictions for the 95 % interval, extrapolation, the caution notice, the month in progress, the model type, the next-day range, and saved projections (032).
- A label per forecast metric (error, typical margin against an average month, explained pattern, and improvement over a simple calculation), with its ranges in its info button; missing metrics show "Sin dato" (032).
- `advertencias` on `GET /analytics/forecast`: each reason that limits the projection, one per item; `advertencia` keeps the joined text (032).

#### Changed
- The label next to Monto and Cantidad is the average of the metric labels, rounded down, and the summary says how many indicators support it (032).
- "Confiabilidad limitada" is now "Toma esta proyección con cautela", with its reasons as a list (032).
- The next-day card says "Rango probable" instead of "Rango operativo" (032).

### Phase 2 - feedback 01 and user requests (tasks 015-031)

#### Added
- CI workflow with backend (ruff, mypy, Alembic `upgrade`/`check`/`downgrade`, pytest) and frontend (lint, types, tests, build) jobs, plus pre-commit hooks (015).
- Sales series endpoint `GET /analytics/stats/series` by month, day, and category, and date and category filters on `/analytics/ventas` (024).
- Dashboard views: overlaid years with a year selector, by category, by month with daily detail, and the whole history, in amount or units (025).
- Monthly forecast of up to 12 months, general or by category, with 95 % prediction intervals from `statsmodels` and an incomplete last month left out of the fit (021).
- Rolling-origin evaluation against three baselines with WAPE, MASE, and improvement over the best baseline; `scripts/evaluate_models.py` and `docs/evaluacion/` (022).
- `GET /analytics/forecast`, `POST /analytics/predicciones`, and `GET /analytics/predicciones`; `response_model` on every JSON route (023).
- Projection chart with history, dashed projection, 95 % band, extrapolation marks, monthly table, and saved projections (026).
- Plain-language metrics with info hints, a quality label, and a folded technical detail (027).
- Accessible `ChartFrame` with a data table behind every chart, marker shapes per series, and a focus-trapping modal (028).
- `app/core/config.py` with `pydantic-settings` as the only reader of the environment (029).
- `second_user` fixture, an isolation test per private endpoint checked against OpenAPI, and the suite on PostgreSQL through `TEST_DATABASE_URL`, also in CI (030).
- Category select fed by `/analytics/stats/categories` in the reports page (031).

#### Changed
- **BREAKING**: `GET /analytics/predict` no longer writes; a history too short to project answers 422. Saving is explicit through `POST /analytics/predicciones` (023).
- Numbers use the `0,000.00` convention in the UI, PDF, and Excel; money uses `$` with 2 decimals (018).
- ETL runs in the threadpool, limits bytes, rows (200,000), and decompressed XLSX size, applies the comma-by-digits rule, validates ranges per row, rewrites the SQL parser, and rejects identical files with 409 (017).
- Report logic moved into thread-safe services without global Matplotlib state; the PDF summarizes and lists the top 20 sales (020).
- Models and migrations aligned (`Mapped[date]`, redundant indexes) with migration `0003` (016).
- Session cache cleared on logout and on 401, private query keys include the user id, report errors are read from the Blob, and uploads and purges invalidate the cached analytics (019).
- CORS defaults to the Vite origin and rejects `*` outside development (029).
- New users get the `Usuario` role by name instead of a fixed id (029).
- The connection error message names `VITE_API_URL` instead of a fixed URL (031).
- `AGENTS.md`, `README.md`, and the frontend README describe the current system and list the commands directly (031).

#### Fixed
- Concurrent duplicate registrations or profile changes answer 400 instead of 500 (029).
- `Content-Disposition` carries an ASCII and a UTF-8 file name, so accented user names no longer break downloads (029).
- The monthly report shows the real year (020).
- The purge test now creates two users and fails if the user filter is removed (030).

#### Removed
- `passlib`: passwords use `bcrypt` directly and existing hashes keep validating (029).
- The text-date patch of the daily forecast, unused `app/utils/`, and `SectionPlaceholder.tsx` (030, 031).
- The `Makefile` and the pre-commit configuration: `make` was not available on the development machine and the hook was never installed; CI runs the same checks.
- The license file.

#### Security
- Passwords are limited to 72 bytes, counted in UTF-8 (029).

### Phase 1 frontend (tasks 010-014)

#### Added
- React 19 + TypeScript + Vite foundation with Tailwind CSS v4, Axios, TanStack Query, React Router, Zustand, and Vitest (010).
- Registration and login with React Hook Form + Zod, persisted JWT session with a 401 interceptor, profile page, `ProtectedRoute`, and the responsive layout (011).
- File upload with a 25 MB limit, load summary with per-row errors, paged sales history, and purge with confirmation (012).
- Dashboard with inclusive date filters, KPIs, and category and temporal Chart.js charts (013).
- Predictions page with amount, units, and intervals fetched only on request, and Excel/PDF downloads as blobs (014).

### Phase 1 backend (tasks 001-009)

#### Added
- Isolated test baseline on in-memory SQLite with auth, ETL, analytics, and ML tests (001).
- `cantidad` on sales and projected amount and quantity on predictions, with their migration (006).
- Inclusive `fecha_desde` / `fecha_hasta` filters on the stats endpoints, with 422 on an inverted range (008).
- `docs/ml-models.md` describing features, metrics, minimum data, and limits (007).

#### Changed
- ETL detects the delimiter and encoding, validates rows before building sales, reports read/inserted/rejected counts, and inserts in one transaction (003).
- Categories are canonicalized in one function for ingestion and report filters; unknown categories are kept (004).
- ML logic moved from the routes into `app/ml_models/forecast.py`; months without sales stay absent (005).
- Separate regressions for amount and quantity with trend and seasonal dummies, temporal validation, and prediction intervals (007).
- JWT moved from `python-jose` to `PyJWT` (009).

#### Security
- 500 responses and `/health/db` return generic Spanish messages; exception details go only to the logs (002).

### Repository refactor (before task 001)

#### Added
- `.gitignore`, `.env.example`, `Makefile`, `.editorconfig`, and a pull request template.
- Alembic configuration for database migrations.
- `requirements-dev.txt` and the `backend/tests/` scaffolding.
- CORS middleware, `GET /health`, password strength validation, login rate limiting (slowapi), `loguru` logging, and the `require_role` dependency.

#### Changed
- **BREAKING**: Unified sales schema (removed the `ventas_procesadas` table).
- Moved from `Base.metadata.create_all()` to Alembic migrations.
- Removed the insecure `SECRET_KEY` fallback and the deprecated `datetime.utcnow` usage.
- Fixed `UserUpdate.nombre_completo`, renamed to `nombre_usuario` to match the model.
- Docstrings in English and user-facing messages in Spanish.

#### Security
- Removed hardcoded credentials from `.env`; `.env.example` holds placeholders only.
- JWT validation guarded against malformed tokens, and size and type checks on uploads.

## [0.1.0] - 2025-XX-XX

### Added
- Initial release (pre-refactor)
- FastAPI backend with user authentication (JWT)
- ETL endpoints supporting CSV, Excel, and SQL ingestion
- Analytics: global stats, category breakdown, temporal evolution
- Linear regression predictor with monthly seasonality
- PDF and Excel report generation
- Synthetic dataset generator for testing

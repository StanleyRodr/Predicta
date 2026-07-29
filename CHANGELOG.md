# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- MIT License file
- Comprehensive `.gitignore` and `.env.example`
- `Makefile` with common development tasks
- `.editorconfig` for consistent code style
- GitHub Pull Request template
- Alembic configuration for database migrations
- `database/seed.sql` with unified schema
- Placeholder `frontend/` directory with README
- `data/` directory for generated datasets
- `docs/` directory for extended documentation
- `backend/tests/` directory with test scaffolding
- `requirements-dev.txt` for development dependencies
- CORS middleware in FastAPI application
- `GET /health` endpoint for monitoring
- Password strength validation on user registration
- Rate limiting on authentication endpoints (slowapi)
- Structured logging with `loguru`
- `require_role` decorator for role-based access control

### Changed
- **BREAKING**: Unified sales schema (removed `ventas_procesadas` table)
- **BREAKING**: Renamed `query_db/` to `database/`
- Removed insecure `SECRET_KEY` fallback
- Migrated from `Base.metadata.create_all()` to Alembic migrations
- Refactored `security.py` with proper docstrings and type hints
- Refactored `models.py` removing deprecated `datetime.utcnow` usage
- Cleaned verbose comments from `etl_routes.py` and `analytics_routes.py`
- Fixed bug: `UserUpdate.nombre_completo` renamed to `nombre_usuario` (matches model)
- Standardized documentation: docstrings in English, user-facing messages in Spanish

### Security
- Removed hardcoded credentials from `.env` (now `.env.example` template only)
- Rotated example `SECRET_KEY` to require explicit generation
- Added JWT validation with try/except guards against malformed tokens
- Added file size and MIME type validation for upload endpoints

## [0.1.0] - 2025-XX-XX

### Added
- Initial release (pre-refactor)
- FastAPI backend with user authentication (JWT)
- ETL endpoints supporting CSV, Excel, and SQL ingestion
- Analytics: global stats, category breakdown, temporal evolution
- Linear regression predictor with monthly seasonality
- PDF and Excel report generation
- Synthetic dataset generator for testing

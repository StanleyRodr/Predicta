# GitHub Workflows

This directory contains CI/CD pipeline definitions.

## Planned workflows

- `ci.yml` - Lint (ruff), type-check (mypy), tests (pytest) on every PR and push to `main`
- `docker-publish.yml` - Build and push Docker images on tagged releases
- `dependency-review.yml` - Review dependency changes in PRs

Workflows will be added in Phase 6 of the project roadmap.

# Plan 015: CI y calidad automática

## Estado

- **Estado:** HECHO
- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** LOW
- **Depende de:** ninguna
- **Categoría:** herramientas
- **Origen:** `docs/feedback/feedback-01.md` F-05, F-20
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Hacer que lint, tipos, tests y build se ejecuten solos en cada push y pull
request, para que las tareas siguientes avancen con una red de seguridad.

## Alcance

- `.github/workflows/ci.yml`
- `backend/pyproject.toml`
- `frontend/eslint.config.js`, `frontend/package.json`
- `.pre-commit-config.yaml`

## Pasos

1. Crear `backend/pyproject.toml` con la configuración de ruff y mypy. Ignorar
   `B008` solo por el uso de `Depends` y `Query` de FastAPI.
   - **Verificar:** `ruff check app/` y `mypy app/` terminan sin errores nuevos.
2. Crear `frontend/eslint.config.js` y el script `lint`.
   - **Verificar:** `npm run lint` termina con código 0.
3. Crear `.pre-commit-config.yaml` con ruff y comprobaciones básicas.
   - **Verificar:** `pre-commit run --all-files` termina con código 0.
4. Crear el job de backend: `ruff check`, `mypy` y `pytest --cov`.
   - **Verificar:** el job pasa en una rama de prueba.
5. Agregar al job de backend un servicio PostgreSQL que ejecute
   `alembic upgrade head`. El paso `alembic check` se activa en el plan 016.
   - **Verificar:** la migración corre contra PostgreSQL en CI.
6. Crear el job de frontend: `npm ci`, `lint`, `typecheck`, `test -- --run` y
   `build`.
   - **Verificar:** el job pasa en una rama de prueba.

## Criterios de terminado

- Un push a una rama ejecuta ambos jobs.
- Un error de tipos o un test roto dejan el workflow en rojo.
- CI no usa secretos reales: `SECRET_KEY` y `DATABASE_URL` son de prueba.

## STOP

- Detenerse si activar ESLint o mypy revela tantos errores que corregirlos
  cambiaría comportamiento. Reportar el conteo y acordar un alcance.
- No desactivar reglas de forma global para dejar el workflow en verde.

## Mantenimiento

Toda herramienta nueva se agrega también a CI. Mantener las versiones de Python
y Node del workflow alineadas con las del proyecto.

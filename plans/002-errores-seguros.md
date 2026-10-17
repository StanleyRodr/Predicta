# Plan 002: Ocultar detalles internos en errores

## Estado

- **Prioridad:** P2
- **Esfuerzo:** S
- **Riesgo:** LOW
- **Depende de:** `plans/001-baseline-pruebas.md`
- **Categoría:** seguridad
- **Planificado en:** commit `adcb0a4`, 2026-10-17

## Objetivo

Evitar que errores de PostgreSQL, rutas internas o drivers lleguen al cliente HTTP. Conservar detalle en logs del servidor.

## Estado actual

- `backend/app/api/etl_routes.py:135-140` incluye `str(exc)` en respuesta 500.
- `backend/app/main.py:106-117` devuelve `str(exc)` desde `/health/db`.
- La app usa `loguru` en `backend/app/main.py`.

## Alcance

- `backend/app/api/etl_routes.py`
- `backend/app/main.py`
- Tests de regresión necesarios en `backend/tests/`

No cambiar códigos HTTP ni formato de éxito.

## Pasos

1. Registrar excepción completa con `logger.exception` o equivalente en `clear_history`.
   - **Verificar:** el endpoint conserva HTTP 500, pero no contiene texto del driver.
2. Cambiar el detalle público por mensaje genérico en español.
   - **Verificar:** test de error confirma ausencia de credenciales, SQL, host y stack trace.
3. Mantener `/health/db` con estado 503 y respuesta genérica; dejar diagnóstico en logs.
   - **Verificar:** test confirma `status=503` y solo campos públicos esperados.

## Criterios de terminado

- Ninguna respuesta pública contiene `str(exc)` en estas rutas.
- Logs conservan contexto suficiente para diagnóstico.
- `pytest tests/test_auth.py tests/test_etl.py -q` pasa.
- `ruff check app/` pasa.

## STOP

- Detenerse si cambiar el formato requiere modificar clientes no documentados.

## Mantenimiento

No devolver excepciones internas en nuevos endpoints. Usar mensajes públicos estables y logs privados.

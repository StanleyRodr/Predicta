# Plan 004: Normalizar categorías con catálogo canónico

## Estado

- **Prioridad:** P2
- **Esfuerzo:** S
- **Riesgo:** LOW
- **Depende de:** `plans/003-etl-robusto.md`
- **Categoría:** bug
- **Planificado en:** commit `adcb0a4`, 2026-10-17

## Objetivo

Usar el mismo nombre de categoría durante carga, filtros, reportes y predicciones. Evitar que diferencias de mayúsculas o acentos produzcan 404 o datos no encontrados.

## Estado actual

- `backend/app/api/etl_routes.py:48` usa `.capitalize()`.
- `backend/app/api/analytics_routes.py:175-183` define `CATEGORY_ALIASES` con nombres canónicos.
- `Cuidado personal` y `Cuidado Personal` no son iguales para el filtro SQL.

## Alcance

- `backend/app/api/etl_routes.py`
- `backend/app/api/analytics_routes.py` o un módulo compartido bajo `backend/app/`
- `backend/tests/test_etl.py` y `backend/tests/test_analytics.py`

No inventar categorías nuevas ni convertir categorías desconocidas en otra categoría.

## Pasos

1. Definir una función de normalización que quite espacios, compare sin distinguir mayúsculas y preserve acentos.
   - **Verificar:** entradas equivalentes devuelven el mismo valor canónico.
2. Aplicar función al cargar ventas y al resolver parámetros de reportes.
   - **Verificar:** CSV con `cuidado personal`, `CUIDADO PERSONAL` y `Cuidado Personal` permite el mismo filtro.
3. Dejar categorías desconocidas como valores válidos, pero devolver 404 solo cuando no existan registros para esa categoría.
   - **Verificar:** categoría nueva del usuario no se convierte en `General` ni se pierde.

## Criterios de terminado

- No queda `.capitalize()` como normalización de categoría.
- Las categorías canónicas coinciden entre ETL y analytics.
- Tests cubren mayúsculas, espacios, acentos y categoría desconocida.

## STOP

- Detenerse si el catálogo de negocio requiere aprobación para agregar o renombrar categorías.

## Mantenimiento

Mantener catálogo y aliases en una sola fuente. No duplicar listas en rutas distintas.

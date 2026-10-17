# Plan 008: Agregar filtros de fecha a analytics

## Estado

- **Prioridad:** P2
- **Esfuerzo:** S
- **Riesgo:** LOW
- **Depende de:** `plans/001-baseline-pruebas.md`
- **Categoría:** feature
- **Planificado en:** commit `adcb0a4`, 2026-10-17

## Objetivo

Permitir comparar periodos para toma de decisiones: mes actual contra anterior, temporada y rango personalizado. Filtrar en PostgreSQL, no después en pandas.

## Estado actual

- `/analytics/stats`, `/stats/categories` y `/stats/temporal` no reciben fechas.
- `Venta.fecha_venta` tiene índice y participa en índice compuesto por usuario.
- Rutas ya filtran por `current_user.id_usuario`.

## Alcance

- `backend/app/api/analytics_routes.py`
- Schemas compartidos solo si son necesarios
- `backend/tests/test_analytics.py`
- `docs/api.md` si cambia contrato documentado

## Contrato propuesto

- Parámetros opcionales `fecha_desde` y `fecha_hasta` como fechas ISO `YYYY-MM-DD`.
- Inclusión de ambos extremos.
- Sin parámetros: conservar comportamiento actual.
- Rango invertido: HTTP 422 con mensaje en español.

## Pasos

1. Crear dependencia o helper para validar y aplicar rango junto con filtro de usuario.
   - **Verificar:** consulta SQL contiene usuario y fechas, sin filtrar resultados en memoria.
2. Aplicar helper a estadísticas globales, categorías y temporal.
   - **Verificar:** cada endpoint devuelve solo registros dentro del rango.
3. Añadir tests sin rango, rango válido, rango de un día y rango invertido.
   - **Verificar:** `pytest tests/test_analytics.py -q` pasa.
4. Documentar parámetros en OpenAPI mediante `Query` y actualizar `docs/api.md` si es necesario.
   - **Verificar:** `/docs` muestra parámetros y límites.

## Criterios de terminado

- Las tres rutas aceptan rango opcional.
- Aislamiento por usuario se mantiene.
- PostgreSQL ejecuta filtro antes de agregación.
- No cambia respuesta cuando no se envían fechas.

## STOP

- Detenerse si el tipo actual de `fecha_venta` no coincide con `date` en la base.
- Detenerse si el cambio exige paginación o rediseño no incluido.

## Mantenimiento

Usar el mismo rango en dashboard y reportes futuros. Añadir pruebas cuando cualquier endpoint analítico agregue filtros nuevos.

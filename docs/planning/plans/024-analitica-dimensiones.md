# Plan 024: Series de analítica por dimensión

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** LOW
- **Depende de:** `docs/planning/plans/020-reportes-servicios.md`
- **Categoría:** backend / API
- **Origen:** pedidos 2 y 4 del usuario, `docs/feedback/feedback-01.md` F-33
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Entregar las series que necesita el dashboard: por mes o por día, generales o
por categoría, agrupadas en SQL.

## Contrato

`GET /analytics/stats/series` con estos parámetros:

- `granularidad`: `mes` (por defecto) o `dia`.
- `categoria`: opcional, normalizada con `normalize_category`.
- `fecha_desde` y `fecha_hasta`: inclusivos, mediante `_apply_date_range`.

Cada punto trae `periodo`, `anio`, `mes`, `dia` (nulo en `granularidad=mes`),
`ingresos`, `cantidad` y `ventas_realizadas`. `/stats/temporal` no cambia.

## Alcance

- `backend/app/api/analytics_routes.py`
- `backend/app/services/analytics_service.py`
- `backend/app/schemas/`, `backend/tests/test_analytics.py`

## Pasos

1. Implementar la agrupación mensual con `extract` de año y mes. No usar
   `date_trunc`, que no existe en SQLite.
   - **Verificar:** los tests pasan en SQLite y en PostgreSQL en CI.
2. Implementar `granularidad=dia`, para el detalle de un mes concreto.
   - **Verificar:** test de un mes con sus días observados.
3. Agregar el filtro `categoria`, sin distinguir mayúsculas ni acentos.
   - **Verificar:** `lacteos` y `Lácteos` devuelven lo mismo.
4. Omitir los periodos sin ventas.
   - **Verificar:** test con enero y marzo: febrero no aparece.
5. Validar la entrada: granularidad inválida y rango invertido devuelven 422.
   - **Verificar:** tests de ambos casos.
6. Agregar `fecha_desde`, `fecha_hasta` y `categoria` a `/ventas` (F-33).
   - **Verificar:** test de paginación con filtro.
7. Declarar `response_model`.
   - **Verificar:** `/docs` documenta la respuesta.
8. Probar el aislamiento entre dos usuarios.
   - **Verificar:** un usuario nunca recibe datos del otro.

## Criterios de terminado

- Todas las vistas del dashboard se resuelven con este endpoint.
- La suma mensual coincide con `/stats` en el mismo rango.

## STOP

- Detenerse si la agrupación da resultados distintos entre SQLite y PostgreSQL.

## Mantenimiento

No agregar ceros de relleno en el backend. La ausencia de datos se representa
en el cliente como hueco.

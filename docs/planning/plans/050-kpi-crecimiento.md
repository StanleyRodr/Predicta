# Plan 050: KPI de crecimiento mensual

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** M
- **Depende de:** —
- **Origen:** decisión del autor del 2026-11-14 (pendiente #16a, REQ-56); tarea C8 de `docs/reportes/verificacion_2026-11-14.md`
- **Planificado en:** commit `5dbd03d`, 2026-11-14

## Objetivo

El dashboard no tiene un KPI de crecimiento, uno de los más pedidos por las PyMEs retail. El autor decidió agregarlo como tarjeta.

## Decisiones

- **Mes de referencia:** el último mes completo del rango filtrado. Un mes está completo cuando el final del rango (`fecha_hasta`, o la última venta si no hay filtro) llega a su último día.
- **Comparaciones:** variación % de los ingresos frente al mes anterior y frente al mismo mes del año anterior. Cada una es `null` si falta el otro mes o si sus ingresos son 0.
- **Sin un mes completo con ventas:** la tarjeta dice «Sin datos suficientes».

## Alcance

- `backend/app/services/analytics_service.py`: el campo `crecimiento_mensual` (`periodo`, `vs_mes_anterior`, `vs_anio_anterior`, o `null`) en la respuesta de `GET /analytics/stats`.
- `backend/app/schemas/schemas.py`: el esquema de esa respuesta.
- `frontend/src/types/analytics.ts` y `frontend/src/pages/DashboardPage.tsx`: una quinta tarjeta, «Crecimiento mensual».
- Pruebas: `backend/tests/test_analytics.py` y `frontend/src/pages/DashboardPage.test.tsx`.

## Pasos

1. Calcular el crecimiento en el backend.
   - **Verificar:** pruebas con meses conocidos (+10 %, −20 %), con el último mes incompleto excluido, sin año anterior (`null`) y con un solo mes.
2. Mostrar la tarjeta.
   - **Verificar:** la prueba del dashboard muestra la variación y «Sin datos suficientes» según el caso; `npm run lint`, `typecheck`, `test` y `build` pasan.
3. Actualizar la fila REQ-56 de la §10.

# Plan 013: Dashboard y analytics

## Estado

- **Estado:** HECHO
- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** MED
- **Depende de:** `docs/planning/plans/011-frontend-auth-layout.md`, `docs/planning/plans/012-frontend-carga-historial.md`
- **Categoria:** frontend / analytics
- **Planificado en:** commit `96e38cc`, 2026-10-18

## Objetivo

Crear dashboard responsive para decisiones de PyMEs: KPIs, categorias,
evolucion temporal y comparacion por rango de fechas.

## Contrato backend

- `GET /analytics/stats`
- `GET /analytics/stats/categories`
- `GET /analytics/stats/temporal`
- Query opcional inclusiva: `fecha_desde=YYYY-MM-DD` y
  `fecha_hasta=YYYY-MM-DD`.
- Rango invertido: HTTP 422.
- Los tres endpoints ya aplican aislamiento por usuario en SQL.

## Pasos

1. Crear tipos para `metricas_globales`, `analisis_por_categoria` y
   `evolucion_diaria`; no usar `any` para respuestas.
   - **Verificar:** `npx tsc --noEmit` pasa.
2. Crear `DateRangeFilter` con fechas ISO, limites inclusivos y accion limpiar.
   - **Verificar:** tests cubren sin rango, un dia, rango valido, rango vacio e invertido.
3. Crear queries TanStack Query para los tres endpoints. La key debe incluir
   usuario y fechas para no mezclar cache entre rangos.
   - **Verificar:** test confirma tres rutas y query keys distintas por rango.
4. Crear `MetricCard` para ingresos, operaciones, ticket promedio y venta maxima.
   - **Verificar:** RTL cubre loading, datos, cero y error.
5. Crear `CategoryBarChart` con Chart.js: ingresos por categoria, tooltip en
   moneda y leyenda accesible.
   - **Verificar:** test valida labels y datasets recibidos.
6. Crear `TemporalLineChart` con fechas ordenadas, tooltip monetario y estado
   sin observaciones.
   - **Verificar:** test valida labels, datos y rango vacio.
7. Crear `DashboardPage` con layout de paneles: resumen arriba, filtros debajo,
   grafico temporal principal y categorias lateral en desktop; una columna en mobile.
   - **Verificar:** RTL confirma que cambio de rango actualiza los tres queries.
8. Manejar errores 422, 401 y 5xx con `Alert`; no mostrar stack traces ni
   respuestas internas.
   - **Verificar:** mocks de error muestran mensaje publico y no rompen graficos.

## Diseño

Fondo grafito. Paneles con bordes finos, no sombras blancas. Acento ambar para
montos, cyan tenue para series, verde solo para mejora. Chart.js debe respetar
contraste y no depender solo de color.

## Criterios de terminado

- Dashboard funciona con datos reales y sin datos.
- Filtros afectan tres endpoints con mismos limites.
- Graficos no se recrean innecesariamente durante input de formulario.
- Responsive desde 360 px hasta desktop.

## STOP

- Detenerse si respuestas backend no coinciden con schemas documentados.
- No agregar agregaciones frontend que dupliquen `/analytics/stats`.
- No introducir otra libreria de charts.

## Mantenimiento

Todo nuevo filtro analitico debe entrar en la query key y en el contrato TypeScript.

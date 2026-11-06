# Plan 025: Dashboard con vistas general, categoría y mes

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** L
- **Riesgo:** MED
- **Depende de:** `docs/planning/plans/018-convencion-numerica.md`, `docs/planning/plans/019-frontend-sesion-descargas.md`, `docs/planning/plans/024-analitica-dimensiones.md`
- **Categoría:** frontend
- **Origen:** pedidos 2 y 4 del usuario
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Reemplazar la línea diaria de todo el historial, donde no se leen altos ni bajos,
por vistas que el usuario elige.

## Decisiones tomadas

- **Gráfica inicial:** años superpuestos, con eje de enero a diciembre y una
  línea por año, más un selector para aislar un año.
- **Por mes:** totales mensuales en la vista principal, y al elegir un mes se
  ve su detalle diario. El filtro de categoría aplica en todas las vistas.
- **Medida:** selector Monto / Cantidad, con Monto por defecto. Nunca se mezclan
  dinero y unidades en un mismo eje.

## Diseño

- **General:** años superpuestos. Es la vista inicial.
- **Por categoría:** las mismas líneas para una categoría elegida, más la
  comparación entre categorías por mes.
- **Por mes:** selector de año y mes con el detalle diario de ese mes.
- **Historial completo:** línea mensual continua, como vista secundaria.

## Alcance

- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/components/analytics/`
- `frontend/src/api/analytics.ts`, `frontend/src/types/analytics.ts`

## Pasos

1. Crear el cliente y los tipos de `/analytics/stats/series`.
   - **Verificar:** `npm run typecheck` y test del cliente.
2. Crear `SeriesViewSelector` con Vista, Medida, Categoría, Año y Mes. Alimentar
   las categorías desde `/analytics/stats/categories`.
   - **Verificar:** RTL del cambio de vista, de la medida y de la categoría
     codificada. Ejes y tooltips usan `$` en Monto y unidades en Cantidad.
3. Crear `yearOverlayData`, que convierte puntos mensuales en una serie por año.
   Los meses sin datos quedan en `null`, con `spanGaps: false`.
   - **Verificar:** test con 2024 parcial: enero a octubre quedan en `null`,
     nunca en cero.
4. Crear `YearOverlayChart`, con color fijo por año y leyenda clicable.
   - **Verificar:** RTL del selector que aísla un año.
5. Crear la vista por categoría y `MonthDetailChart` para el detalle diario.
   - **Verificar:** cada vista llama al endpoint con los parámetros correctos.
6. Mantener la línea mensual como "Historial completo".
   - **Verificar:** RTL de la vista secundaria.
7. Definir la relación con `DateRangeFilter`: el rango aplica a tarjetas y
   gráficos, y el rango activo se muestra en pantalla.
   - **Verificar:** los endpoints reciben los mismos límites.
8. Incluir `userId` y todos los filtros en las claves de consulta.
   - **Verificar:** test de que cambiar un filtro no reutiliza datos de otro.
9. Adaptar la vista a móvil.
   - **Verificar:** sin desbordamiento horizontal a 375 px.

## Criterios de terminado

- Se puede elegir entre general, categoría y mes.
- La vista inicial permite ver altos y bajos sin ajustar nada.
- Los gráficos usan los formatos del plan 018.
- Todo texto nuevo lleva acentos correctos.

## STOP

- Detenerse si una vista requiere datos que `/stats/series` no entrega: ampliar
  primero el contrato del plan 024.
- No fabricar meses ni rellenar con ceros.

## Mantenimiento

Toda vista nueva declara sus filtros en la clave de consulta.

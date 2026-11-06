# Plan 018: Convención numérica 0,000.00

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** S-M
- **Riesgo:** LOW
- **Depende de:** ninguna
- **Categoría:** frontend / reportes
- **Origen:** pedido 1 del usuario
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Mostrar todos los números con coma para miles y punto para decimales, por
ejemplo `$1,234.56`, desde un único punto de formato por capa.

## Decisiones tomadas

- La moneda se muestra como `$`, sin código de país.
- Los montos llevan siempre 2 decimales.
- Las fechas siguen en español. Solo cambia el formato de los números.
- La interpretación de números en archivos cargados está en el plan 017.

## Estado actual

- `frontend/src/lib/formatters.ts:1` usa `es-CO` con moneda `COP`.
- `MetricCard.tsx:19` y `ForecastMetricCard.tsx:13` llaman a
  `toLocaleString("es-CO")`.
- `SalesHistoryTable.tsx:36` y `ForecastQuality.tsx:13` usan `toFixed`, sin
  separador de miles.
- `analytics_routes.py:442` usa `:.2f`, sin separador de miles.

## Alcance

- `frontend/src/lib/formatters.ts` y sus consumidores
- `backend/app/api/analytics_routes.py`, o su servicio tras el plan 020

## Pasos

1. Crear en `formatters.ts` las funciones `formatCurrency`, `formatNumber`,
   `formatPercent` y `formatAxisCurrency`, con locale numérico fijo `en-US`.
   Mantener `formatDate` en español.
   - **Verificar:** tests con `0`, `1234.5`, `1234567.891` y un negativo. El
     resultado para `1234.5` es `$1,234.50` y el negativo es `-$1,234.50`.
2. Reemplazar todo uso directo de `toLocaleString` y `toFixed` en componentes.
   - **Verificar:** una búsqueda de `toLocaleString`, `toFixed` y `es-CO` solo
     encuentra `formatters.ts`, y `es-CO` solo en `formatDate`.
3. Usar `formatAxisCurrency` en los ejes: separador de miles y sin decimales
   para no saturarlos. Los tooltips muestran el valor exacto.
   - **Verificar:** test de los callbacks de eje y tooltip.
4. Crear en backend un helper `format_money` y usarlo en PDF y en las etiquetas
   de Matplotlib.
   - **Verificar:** test del helper; ningún `:.2f` de dinero queda sin coma.
5. Aplicar `#,##0.00` a las columnas de monto del Excel exportado.
   - **Verificar:** test que abre el archivo con openpyxl y lee `number_format`.

## Criterios de terminado

- Dashboard, predicciones, historial, PDF y Excel usan la misma convención.
- La suite de frontend y la de backend pasan.

## Limitaciones

Excel muestra los separadores según la configuración regional del equipo. El
archivo guarda el formato correcto, pero un equipo en español puede mostrarlo
como `1.234,56`. No se debe convertir el monto a texto para evitarlo, porque
dejaría de ser sumable.

## STOP

- Detenerse si algún cambio altera un valor en lugar de su presentación.

## Mantenimiento

Ningún componente formatea números por su cuenta. Todo nuevo formato se agrega
a `formatters.ts`.

# Plan 014: Predicciones y reportes

## Estado

- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** MED
- **Depende de:** `plans/013-frontend-dashboard.md`
- **Categoria:** frontend / ML / reportes
- **Planificado en:** commit `96e38cc`, 2026-10-18

## Objetivo

Exponer prediccion de monto y cantidad, metricas e intervalos sin prometer
precision que backend no garantiza. Permitir descarga de reportes existentes.

## Contrato backend

`GET /analytics/predict` responde usuario, proxima fecha, monto, cantidad,
`intervalos_prediccion` y `metricas`. Con datos insuficientes puede responder
HTTP 200 con propiedad `error`.

Reportes descargables:

- `GET /analytics/export/excel`
- `GET /analytics/export/pdf`
- `GET /analytics/reporte-predictivo-anual-pdf`
- `GET /analytics/reporte-mensual/{mes}`
- `GET /analytics/prediccion-categorias/{categoria}`

## Pasos

1. Crear tipos `ForecastResponse`, `ForecastMetrics` e `Interval` con metricas
   nullable y union para respuesta insuficiente.
   - **Verificar:** `npx tsc --noEmit` pasa sin casts inseguros.
2. Crear query manual `useForecast` con boton explicito `Calcular prediccion`.
   Desactivar refetch automatico de esta query para evitar peticiones no
   intencionadas y respetar el comportamiento persistente del backend.
   - **Verificar:** test confirma que no solicita hasta hacer click.
3. Crear tarjetas de monto y cantidad con valor, fecha proyectada y limites
   inferior/superior. Valores `null` muestran "No disponible".
   - **Verificar:** RTL cubre valores normales, cero, null y error.
4. Crear panel de calidad con R², MAPE y RMSE, incluyendo explicacion corta:
   metricas provienen de validacion temporal y pueden faltar con pocos datos.
   - **Verificar:** test confirma que `null` no se muestra como cero.
5. Crear vista grafica opcional de historico y proyeccion con Chart.js usando
   colores y leyenda accesibles; no fabricar meses faltantes en frontend.
   - **Verificar:** test valida series y ausencia de puntos inventados.
6. Crear cliente de descargas Axios con `responseType: blob`, lectura segura
   de `Content-Disposition` y nombre fallback local.
   - **Verificar:** test descarga blob, conserva extension y revoca object URL.
7. Crear `ReportsPage` con botones separados para reportes globales, mensual y
   por categoria. Deshabilitar boton durante descarga y mostrar error publico.
   - **Verificar:** mock confirma rutas, parametro mensual y categoria codificada.
8. Integrar rutas `/predictions` y `/reports` en `AppShell`.
   - **Verificar:** usuario autenticado navega por ambas rutas y el build pasa.

## Criterios de terminado

- Monto y cantidad siempre aparecen como valores separados.
- Intervalo nunca presenta limite inferior mayor que superior.
- No se muestra `NaN`, `Infinity`, stack trace ni error crudo.
- Descargas funcionan en Chrome, Firefox y Edge mediante blob.
- Mobile mantiene botones accionables y tablas sin overflow horizontal accidental.

## STOP

- Detenerse si backend cambia `/analytics/predict` de GET a POST: actualizar
  contrato antes de implementar.
- No llamar prediccion en cada render ni con refetch al enfocar ventana.
- No etiquetar intervalo como "confianza estadistica"; documentacion backend
  lo define como aproximacion operativa.

## Mantenimiento

Si backend agrega horizonte configurable, extender primero tipos y tests; no
inferir fechas futuras desde datos del navegador.

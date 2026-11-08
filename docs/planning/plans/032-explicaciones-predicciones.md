# Plan 032: Explicaciones claras en predicciones

## Estado

- **Estado:** HECHO
- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** LOW
- **Depende de:** `docs/planning/plans/027-metricas-comprensibles.md`, `docs/planning/plans/028-accesibilidad.md`
- **Categoría:** frontend / UX, con un cambio pequeño de backend
- **Origen:** revisión del usuario de `/predictions` y entrevista de diseño, 2026-11-08
- **Planificado en:** commit `39d3d7a`, 2026-11-08

## Objetivo

Que un dueño de tienda entienda cada concepto de `/predictions` sin saber
estadística, y que vea de un vistazo si cada métrica salió bien o mal.

Hoy pasa esto:

- "Intervalo del 95 %", "Confiabilidad limitada" y "Extrapolación" no se explican en ningún lugar.
- Cada métrica de "¿Qué tan confiable es?" tiene una frase, pero no una etiqueta propia.
- La etiqueta junto a Monto/Cantidad solo depende del error promedio.

## Diseño

### Botón "i" en cada concepto

Se reutiliza `InfoHint` (`frontend/src/components/ui/InfoHint.tsx`) en cada
aparición de estos conceptos. El gráfico es un canvas, así que su leyenda y su
tooltip no admiten botones; el "i" va junto al gráfico.

| Concepto | Dónde aparece | Explicación |
|---|---|---|
| Intervalo del 95 % | Subtítulo del gráfico, "Rango 95 %" de la tabla, "(95 %)" del detalle del mes | "Es el rango donde casi seguro caerá la venta real: de cada 100 meses, unos 95 quedarían dentro de la zona sombreada. Una zona ancha significa más incertidumbre." |
| Extrapolación | Nota bajo el gráfico, etiqueta de la tabla, aviso del detalle del mes | "Meses más lejanos que los que se pudieron comprobar con tu historial. Son una estimación más arriesgada: úsalos como orientación, no como cifra segura." |
| Toma esta proyección con cautela | Aviso, antes "Confiabilidad limitada" | "La proyección sigue siendo útil, pero algo de tu historial limita su precisión. Abajo están los motivos; cargar más meses de ventas suele resolverlos." |
| Mes en curso (parcial) | Nota junto al gráfico cuando hay `mes_parcial` | "El mes actual todavía no termina, así que no se usa para calcular la tendencia: se proyecta como si fuera futuro." |
| Tipo de modelo | Subtítulo de la proyección | "Solo tendencia: sigue la dirección general de tus ventas. Tendencia y temporada: además repite los altibajos de cada mes del año; se usa desde 36 meses con todos los meses del año." |
| Rango del día siguiente | Tarjetas "Mañana, todas las categorías" | "Igual que en la proyección mensual: la venta de mañana probablemente caerá entre estos dos valores." |
| Proyecciones guardadas | Título de la sección | "Calcular una proyección no guarda nada. Al guardarla queda una copia con fecha para compararla después con lo que realmente vendiste." |

El aviso muestra cada motivo del backend como un punto de una lista.

### Etiqueta por métrica

Cada métrica muestra un badge junto a su título, con los tonos de la etiqueta
general. Los rangos son orientativos y aparecen al final del "i" de cada métrica.

| Métrica | Muy buena | Buena | Aceptable | Baja |
|---|---|---|---|---|
| Error promedio (MAPE) | < 10 % | 10 % a < 20 % | 20 % a 50 % | > 50 % |
| Margen típico (RMSE ÷ mes promedio) | < 10 % | 10 % a < 20 % | 20 % a 50 % | > 50 % |
| Patrón explicado (R²) | ≥ 0.6 | 0.3 a < 0.6 | 0 a < 0.3 | < 0 |
| Frente a un cálculo simple | ≥ 20 % | 5 % a < 20 % | −5 % a < 5 % | < −5 % |

- **El RMSE se compara con el mes promedio:** el promedio de `monto` o `cantidad` de los últimos `origenes` meses de `historial`, que son los meses evaluados.
- **Sin valor:** una métrica `null` muestra un badge gris "Sin dato" y no cuenta para la etiqueta general.

### Etiqueta general y resumen

- **Etiqueta general:** se promedian las etiquetas disponibles (Muy buena = 4, Buena = 3, Aceptable = 2, Baja = 1) y se redondea hacia abajo. Sin ninguna disponible, no hay etiqueta.
- **Resumen:** dice la etiqueta, qué la sostiene y el error promedio. Por ejemplo: "Calidad buena según 4 indicadores, medida en los últimos 6 meses. En promedio se desvió un 12.50% del valor real."

### Motivos como lista

- **Backend:** `/analytics/forecast` agrega `advertencias: list[str]`, la lista de motivos que hoy se une en un solo texto.
- **Compatibilidad:** `advertencia` se conserva igual, porque la usan los PDF y las proyecciones guardadas.

## Alcance

- `backend/app/ml_models/forecast.py`, `backend/app/schemas/schemas.py`, el servicio que arma la respuesta de `/analytics/forecast`
- `backend/tests/test_forecast_api.py`
- `frontend/src/types/forecast.ts`
- `frontend/src/lib/metricExplanations.ts`
- `frontend/src/lib/conceptExplanations.ts` (nuevo)
- `frontend/src/components/forecast/ForecastQuality.tsx`, `ForecastTable.tsx`, `MonthDetail.tsx`, `ForecastMetricCard.tsx`
- `frontend/src/pages/PredictionsPage.tsx`

## Pasos

1. Agregar `advertencias` en el backend sin cambiar `advertencia`.
   - **Verificar:** con 12 meses llega la lista de motivos y `" ".join(advertencias) == advertencia`; sin motivos llega `[]`.
2. Centralizar los textos de los conceptos en `conceptExplanations.ts`.
   - **Verificar:** test de que cada concepto tiene título y explicación con acentos correctos.
3. Calcular la etiqueta de cada métrica y la general en `metricExplanations.ts`.
   - **Verificar:** tests de cada rango con sus límites, del RMSE relativo, de `null` como "Sin dato" y del promedio redondeado hacia abajo.
4. Mostrar un badge por métrica, la etiqueta general nueva y el resumen en `ForecastQuality`.
   - **Verificar:** RTL de un badge por métrica, de "Sin dato" y de la frase de resumen.
5. Agregar el "i" en cada concepto de la tabla de diseño.
   - **Verificar:** RTL abre cada "i" con clic o Enter y lo cierra con Escape.
6. Cambiar el aviso a "Toma esta proyección con cautela", con los motivos en lista.
   - **Verificar:** RTL de un punto por motivo; sin motivos no hay aviso.

## Criterios de terminado

- Cada concepto de la página tiene su explicación a un clic.
- Cada métrica muestra si salió bien o mal, con sus rangos explicados.
- Los textos son correctos en español, con acentos.

## STOP

- Detenerse si un texto promete más de lo que mide la métrica o el intervalo.
- No usar la palabra "precisión" para el R².
- Detenerse si el cambio del backend rompe los PDF o las proyecciones guardadas.

## Mantenimiento

- Cada concepto nuevo de la página entra en `conceptExplanations.ts`.
- Cada métrica nueva entra en `metricExplanations.ts`, con sus rangos.

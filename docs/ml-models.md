# Modelos de Machine Learning

Predicta usa regresión lineal por mínimos cuadrados ordinarios
(`statsmodels.OLS`, con intercepto) para producir proyecciones interpretables de
monto y cantidad. Los dos objetivos se ajustan por separado con la misma matriz
de predictores; sus unidades y errores no se mezclan. El código está en
`backend/app/ml_models/forecast.py`.

## Proyección mensual

`monthly_forecast_series(monthly, last_sale, max_horizon=12)` es el único camino
de ajuste. La usan los reportes general, mensual y por categoría.

### Mes incompleto

Si la última venta es anterior al último día de su mes, ese mes está incompleto:
se excluye del ajuste, se devuelve aparte como `mes_parcial` y es el primer mes
proyectado. Los gráficos lo muestran como un punto hueco, separado de la línea.

### Modelo y horizonte

El modelo se elige para cada serie, general o por categoría, según sus meses
completos observados:

| Meses completos | Modelo | Horizonte |
|---|---|---|
| Menos de 6 | Sin proyección (`InsufficientHistoryError`) | — |
| 6 a 23 | Tendencia | La mitad de los meses: de 3 a 11 |
| 24 o más, con los 12 meses del calendario | Tendencia y estacionalidad | 12 |
| 24 o más, con algún mes del calendario sin ventas | Tendencia | 12 |

Bajo 24 meses no se usa estacionalidad: el historial no alcanza para separar una
temporada de un cambio real del negocio. Si algún mes del calendario nunca tuvo
ventas, no hay base para estimar su nivel, así que también se usa solo la
tendencia. En ambos casos `advertencia` lo explica al usuario.

### Variables

- `mes_indice`: meses transcurridos desde el primer mes,
  `(año − año₀)·12 + (mes − mes₀)`. Cuenta meses del calendario, no filas: de
  enero a marzo hay 2 aunque falte febrero.
- `mes_2` … `mes_12`: dummies de febrero a diciembre. Enero es la referencia y
  queda absorbido por el intercepto, para evitar la colinealidad perfecta de
  12 dummies más intercepto.

Los meses sin ventas no se rellenan con cero: simplemente no están en los datos.

### Intervalo de predicción

Los límites salen de `get_prediction().summary_frame(alpha=0.05)`, con el
intervalo de observación al 95 % (`obs_ci_lower`, `obs_ci_upper`). Incluye la
varianza residual y la incertidumbre de los coeficientes, por lo que se ensancha
al alejarse de los datos, en lugar de usar un margen fijo. El punto y los límites
se recortan a cero, porque monto y cantidad no pueden ser negativos.

### Resultado

Por cada objetivo (`monto`, `cantidad`) se devuelven las métricas y, por mes,
`fecha`, `prediccion`, `inferior`, `superior` y `extrapolacion`. `extrapolacion`
es verdadero desde el mes 7 del horizonte, que se presenta como menos confiable.
También se devuelven `modelo`, `horizonte`, `meses_observados`, `advertencia`,
`historial` (los meses ajustados) y `mes_parcial`.

## Proyección diaria

`daily_predictions` proyecta el día siguiente a la última venta para
`/analytics/predict`. Los predictores crecen con el historial, para que el
intervalo siempre tenga grados de libertad:

| Días observados | Modelo |
|---|---|
| 2 | Promedio de los días (solo intercepto) |
| 3 o más | Tendencia `dia_indice` (días transcurridos) |
| 14 o más, con los 7 días de la semana | Tendencia y `dia_2` … `dia_7` (martes a domingo; lunes es la referencia) |

El intervalo es el mismo intervalo de observación al 95 % del modelo mensual.

## Métricas

`R²`, `MAPE` y `RMSE` se calculan sobre un holdout cronológico: se reserva el
último 20 % de las observaciones (al menos una y nunca todas), se ajusta el mismo
modelo con las anteriores y se evalúa sobre las reservadas. Nunca se usan
observaciones futuras. Con una sola observación de validación, `R²` es `null`
porque no está definido.

La respuesta de `/analytics/predict` incluye `monto_predicho`,
`cantidad_predicha`, `intervalos_prediccion` y `metricas`. La columna
`predicciones.precision_estimada` conserva el `R²` temporal del monto cuando
está definido.

## Limitaciones

- Con 24 meses hay solo 2 observaciones por mes del calendario. La estacionalidad
  es débil y debe declararse en la tesis.
- En el holdout de una serie de 24 meses, los meses evaluados aparecen una sola
  vez en el ajuste. Con tan pocos puntos el `R²` puede ser muy negativo aunque el
  `MAPE` sea moderado. La evaluación por horizonte contra modelos de referencia
  está en el plan 022.
- Bajo 24 meses la proyección es una recta: no anticipa picos de temporada.
- Las proyecciones de las categorías suman la general cuando todas usan el mismo
  modelo y ningún punto se recorta a cero. Los intervalos no son aditivos: el
  intervalo general se calcula sobre su propia serie.
- La tendencia es lineal y no se modelan feriados, promociones, precios, clima ni
  otras variables externas. Los resultados sirven como apoyo operativo, no como
  garantía de demanda futura.

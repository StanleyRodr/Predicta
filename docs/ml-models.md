# Modelos de Machine Learning

Predicta usa regresión lineal por mínimos cuadrados ordinarios
(`statsmodels.OLS`, con intercepto) para producir proyecciones interpretables de
monto y cantidad. Los dos objetivos se ajustan por separado con la misma matriz
de predictores; sus unidades y errores no se mezclan. El código está en
`backend/app/ml_models/forecast.py`, y la evaluación en
`backend/app/ml_models/evaluation.py` y `backend/scripts/evaluate_models.py`.

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
| 24 a 35 | Tendencia | 12 |
| 36 o más, con los 12 meses del calendario | Tendencia y estacionalidad | 12 |
| 36 o más, con algún mes del calendario sin ventas | Tendencia | 12 |

La estacionalidad empieza en 36 meses, con 3 observaciones por mes del
calendario. Al principio empezaba en 24, pero en la evaluación (más abajo) la
especificación estacional perdía contra "el mismo mes del año anterior" en 4 de
6 horizontes, y su intervalo del 95 % cubría solo entre 50 % y 67 % de los meses
reales. Con 2 observaciones por mes no se puede separar una temporada de un
cambio real del negocio. Si algún mes del calendario nunca tuvo ventas, no hay
base para estimar su nivel, y también se usa solo la tendencia. En todos estos
casos `advertencia` lo explica al usuario.

### Variables

- `mes_indice`: meses transcurridos desde el primer mes,
  `(año − año₀)·12 + (mes − mes₀)`. Cuenta meses del calendario, no filas: de
  enero a marzo hay 2 aunque falte febrero.
- `mes_2` … `mes_12` (solo con estacionalidad): dummies de febrero a diciembre.
  Enero es la referencia y queda absorbido por el intercepto, para evitar la
  colinealidad perfecta de 12 dummies más intercepto.

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
es verdadero desde el mes 7 del horizonte: esos meses son extrapolación sin
validar. También se devuelven `modelo`, `horizonte`, `meses_observados`,
`advertencia`, `historial` (los meses ajustados) y `mes_parcial`.

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
Sus métricas (`R²`, `MAPE`, `RMSE`) salen de un holdout cronológico del último
20 % de los días.

## Métricas de la proyección mensual

En cada serie, el mismo modelo se reajusta en cada uno de los últimos 6 meses
(origen móvil) y predice el mes siguiente sin verlo. Nunca se usan observaciones
futuras. Sobre esos errores se calculan:

- `wape`: error absoluto total sobre las ventas reales totales, en %.
- `mase`: error absoluto medio dividido por el error del "último valor" dentro
  del entrenamiento. Menor que 1 es mejor que ese modelo ingenuo.
- `mape`, `rmse` y `r2`. Con un solo mes evaluado, `r2` es `null`.
- `referencia`: el mejor de los modelos simples sobre los mismos meses, por WAPE:
  `ultimo_valor`, `mismo_mes_anio_anterior` o `promedio_movil_3`.
- `mejora_vs_referencia`: reducción porcentual del WAPE frente a esa referencia.
  Es negativa cuando la regresión pierde.
- `origenes`: cuántos meses se evaluaron.

Si el historial no deja ningún mes para evaluar (6 meses), todas las métricas
son `null` y `origenes` es 0. Una métrica que no se puede calcular nunca se
muestra como cero.

## Evaluación para la tesis

`backend/scripts/evaluate_models.py` genera
[`docs/evaluacion/resultados.md`](evaluacion/resultados.md), con sus tablas CSV
y gráficos, a partir de `DatosDePrueba/ventas_fabricadas/ventas_tienda_2_anios.xlsx`
(24 meses, de 2024-11 a 2026-10). Dos ejecuciones dan archivos idénticos.

- **Backtest con origen móvil:** 18 meses iniciales y horizontes de 1 a 6. Con
  24 meses no se pueden validar los meses 7 a 12.
- **Modelos:** la regresión con la regla aplicada, la regresión estacional
  forzada, ETS con tendencia amortiguada (solo en el script) y los tres modelos
  simples. ETS estacional no se usa: necesita 2 ciclos completos para
  inicializarse y el entrenamiento tiene 18 meses.
- **Métricas:** WAPE, MASE, MAPE, RMSE, R² y cobertura real del intervalo del
  95 %, más Ljung–Box y Breusch–Pagan sobre los residuos del modelo final.

Resultados principales:

- La regresión con la regla aplicada (tendencia) gana al "mismo mes del año
  anterior" en 5 de 6 horizontes. Le gana al mejor modelo simple en los
  horizontes 1 y 2 (alrededor de 10 %), y **pierde del 3 al 6**.
- La especificación estacional pierde contra el mismo mes del año anterior en
  4 de 6 horizontes. Por eso la estacionalidad empieza ahora en 36 meses.
- **ETS amortiguado es el mejor modelo en casi todos los horizontes.** Se
  mantiene la regresión en runtime por interpretabilidad, y esta diferencia se
  declara.
- La cobertura del intervalo de la tendencia es del 100 %: el intervalo es más
  ancho de lo necesario, es decir, conservador.
- Los residuos del modelo final no muestran autocorrelación ni varianza no
  constante (todos los valores p son mayores que 0.05).
- **Cortando el historial a 6 y 12 meses,** la regla pierde contra el "último
  valor" (WAPE de 29 % frente a 12 %, y de 28 % frente a 22 %). Con 18 meses
  queda cerca (8.0 % frente a 6.9 %).
- **Por categoría,** la regla mejora al mejor modelo simple en Abarrotes, Bebidas,
  Cuidado Personal y Lácteos, y **pierde en Limpieza**, donde el promedio móvil es
  mucho mejor.

## Limitaciones

- Los datos de prueba son fabricados: los resultados muestran que el método
  funciona, no su desempeño en una tienda real.
- La evaluación por horizonte tiene pocos puntos: el horizonte 1 se mide con 6
  meses y el 6, con uno solo. Las diferencias pequeñas no son concluyentes.
- Los meses 7 a 12 del horizonte no están validados.
- Bajo 36 meses la proyección es una recta: no anticipa picos de temporada.
- Las proyecciones de las categorías suman la general cuando todas usan el mismo
  modelo y ningún punto se recorta a cero. Los intervalos no son aditivos: el
  intervalo general se calcula sobre su propia serie.
- La tendencia es lineal y no se modelan feriados, promociones, precios, clima ni
  otras variables externas. Los resultados sirven como apoyo operativo, no como
  garantía de demanda futura.

# Modelos de Machine Learning

Predicta usa Regresion Lineal Multiple (`LinearRegression`) para producir
proyecciones interpretables de monto y cantidad. Los dos objetivos se entrenan
por separado con la misma matriz de predictores; sus unidades y errores no se
mezclan.

## Features

Las columnas se generan siempre en este orden:

- Modelo mensual: `mes_indice`, `mes_1` ... `mes_12`.
- Modelo diario: `dia_indice`, `dia_1` ... `dia_7`, donde `dia_1` es lunes y
  `dia_7` es domingo.

`*_indice` es una tendencia secuencial desde cero. Las variables restantes son
dummies de calendario. Solo se usan fechas y ventas disponibles; no se
fabrican meses o dias sin observaciones.

## Metricas e incertidumbre

Antes de entrenar el modelo final se reserva cronologicamente el ultimo 20 %
de observaciones (al menos una y nunca todo el dataset). `R2`, `MAPE` y `RMSE`
se calculan exclusivamente sobre ese holdout temporal. Con una sola
observacion de validacion, `R2` es `null` porque no esta definido.

El intervalo se calcula como `prediccion +/- 1.96 * desviacion` de los
residuales del modelo final. Los limites se recortan a cero porque monto y
cantidad no pueden ser negativos. El intervalo es una aproximacion operativa,
no un intervalo estadistico calibrado.

La respuesta de `/analytics/predict` incluye `monto_predicho`,
`cantidad_predicha`, `intervalos_prediccion` y `metricas`. La columna
`predicciones.precision_estimada` conserva el `R2` temporal del monto cuando
esta definido.

## Datos minimos y limitaciones

Se necesitan al menos dos observaciones temporales para ejecutar una
proyeccion. Con historiales muy cortos las dummies estacionales pueden quedar
subidentificadas y las metricas ser inestables. La tendencia es lineal y no se
modelan feriados, promociones, precios, clima ni otras variables externas.
Por ello, los resultados sirven como apoyo operativo y no como garantia de
demanda futura.

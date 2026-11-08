# Plan 021: Corregir el modelo y proyectar 12 meses

## Estado

- **Estado:** HECHO
- **Prioridad:** P1
- **Esfuerzo:** L
- **Riesgo:** HIGH
- **Depende de:** `docs/planning/plans/020-reportes-servicios.md`
- **Categoría:** ML
- **Origen:** `docs/feedback/feedback-01.md` F-21, F-22, F-24, F-25 y pedido 3 del usuario
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Producir una curva mensual de hasta 12 meses, general o por categoría, con un
intervalo de predicción real. Corregir el modelo antes de graficarlo, porque un
gráfico hace visibles sus errores.

## Decisiones tomadas

- Se agrega `statsmodels` como dependencia.
- El horizonte es la mitad de los meses observados, con un máximo de 12.
- El modelo se escoge según los meses observados de cada serie:

| Meses observados | Modelo | Horizonte |
|---|---|---|
| Menos de 6 | Sin proyección mensual | — |
| 6 a 23 | Solo tendencia, sin estacionalidad | La mitad de los meses: de 3 a 11 |
| 24 o más | Tendencia y estacionalidad mensual | 12 meses |

Bajo 24 meses no se usa estacionalidad: el historial no alcanza para separar una
temporada de un cambio real del negocio.
- El mes incompleto se excluye del ajuste y es el primer mes proyectado. En los
  gráficos se muestra aparte, como punto hueco.
- La estacionalidad exige además que los 12 meses del calendario tengan ventas.
  Si falta alguno, se usa solo la tendencia y `advertencia` lo explica.
- La proyección diaria también usa `statsmodels.OLS` con intervalo de
  observación: promedio con 2 días, tendencia desde 3 y tendencia más día de la
  semana desde 14 días con los 7 días observados. Lunes y enero son las
  referencias.
- Los reportes PDF responden 400 con el mensaje nuevo cuando faltan meses; el
  422 de la tarea 023 aplica al endpoint `/forecast`.
- Con el archivo de prueba (24 meses), la banda del 95 % mide de 38 % a 65 % de
  la predicción general y conserva la forma de la temporada, así que no se
  activó la condición STOP. El `R²` del holdout es negativo (de −1.9 a −15.8,
  con `MAPE` de 13 % a 29 %), igual que con el modelo anterior: es un efecto del
  holdout de 5 meses, que evalúa el plan 022.

## Estado actual

- `_forecast_target` usa solo `predictions[0]` y descarta el resto del horizonte.
- `monthly_forecast` reentrena un segundo modelo sin intervalos ni métricas.
- La tendencia usa `np.arange(len(monthly))`, que cuenta filas y no meses.
- 12 dummies más intercepto son perfectamente colineales.
- El margen es el mismo ±1.96·σ en todos los meses.

## Alcance

- `backend/app/ml_models/forecast.py`
- `backend/app/services/report_service.py`
- `backend/requirements.txt`, `backend/tests/test_ml.py`
- `docs/ml-models.md`, `CLAUDE.md` (sección ML)

## Pasos

1. Calcular la tendencia con
   `meses_transcurridos = (año − año₀)·12 + (mes − mes₀)`.
   - **Verificar:** test con enero y marzo: la distancia es 2, y no se crea
     febrero.
2. Quitar una dummy de referencia en el modelo mensual y en el diario.
   - **Verificar:** test del número y el orden de columnas: tendencia más 11
     dummies mensuales, y tendencia más 6 diarias.
3. Excluir del ajuste el último mes si está incompleto, es decir, si la última
   venta es anterior al último día de ese mes.
   - **Verificar:** test con historial cortado a mitad de mes.
4. Crear la regla de selección de modelo y horizonte de la tabla de decisiones,
   aplicada a cada serie. Con menos de 6 meses, lanzar un error de dominio en
   español que indique cuántos meses faltan.
   - **Verificar:** tests con 5, 6, 23 y 24 meses: error, 3 meses de tendencia,
     11 meses de tendencia y 12 meses con estacionalidad.
5. Ajustar con `statsmodels.OLS` y obtener los límites con
   `get_prediction().summary_frame(alpha=0.05)`, usando el intervalo de
   observación. Recortar a cero el punto y los límites.
   - **Verificar:** en cada mes, `inferior ≤ prediccion ≤ superior` y ningún
     valor es negativo.
6. Crear una única función `monthly_forecast_series(monthly, max_horizon=12)`
   que devuelva el modelo usado, el horizonte aplicado, una advertencia cuando
   corresponda y, por mes, `fecha`, `prediccion`, `inferior`, `superior` y
   `extrapolacion`, para `monto` y `cantidad`. `extrapolacion` es verdadero
   desde el mes 7.
   - **Verificar:** test de puntos consecutivos con fechas correctas, y de
     `extrapolacion` en los meses 6 y 7.
7. Eliminar el reentrenamiento duplicado y migrar los reportes a esa función.
   Los textos del PDF usan el horizonte aplicado, no "12 meses" fijo.
   - **Verificar:** una búsqueda de `monthly_forecast(` no encuentra usos, y los
     tests de exportación pasan con 24 y con 12 meses de datos.
8. Aceptar una serie filtrada por categoría usando la misma función.
   - **Verificar:** con categorías que comparten los mismos meses, el mismo
     modelo y sin recorte a cero, las proyecciones suman la proyección general.
9. Actualizar `docs/ml-models.md` y la sección ML de `CLAUDE.md`.
   - **Verificar:** ambos describen las variables y el intervalo reales.

## Criterios de terminado

- Un solo camino de ajuste por horizonte.
- Las proyecciones por categoría y la general son coherentes.
- Los meses sin datos siguen ausentes, nunca en cero.

## Limitaciones

- Con 24 meses hay solo 2 observaciones por mes del calendario. La estacionalidad
  es débil y debe declararse en la tesis.
- Los puntos suman el total, pero los intervalos no son aditivos. El intervalo
  general se calcula sobre su propia serie.
- El recorte a cero puede romper levemente la suma de categorías.
- Bajo 24 meses la proyección es una recta: no anticipa picos de temporada.
- Si una categoría usa otro modelo que el total, las proyecciones no suman exacto.

## STOP

- Detenerse si el intervalo de 95% queda tan amplio que el gráfico no aporta
  información. Reportar los valores antes de cambiar de método.
- No usar observaciones futuras al calcular métricas.

## Mantenimiento

Toda variable nueva necesita justificación de negocio y una comparación contra
los modelos de referencia del plan 022.

# Plan 034: Métrica MAE

## Estado

- **Estado:** HECHO
- **Prioridad:** P1
- **Esfuerzo:** S-M
- **Riesgo:** LOW
- **Depende de:** `docs/planning/plans/022-evaluacion-baselines.md`, `docs/planning/plans/032-explicaciones-predicciones.md`
- **Categoría:** backend / ML, con un cambio pequeño de frontend
- **Origen:** discrepancia REQ-37 de `docs/checking/VERIFICACION_TESIS.md`, 2026-11-08
- **Planificado en:** commit `a734296`, 2026-11-08

## Objetivo

Que el sistema calcule y muestre el MAE, como promete la tesis.

La tesis (REQ-37, OE5) dice que el MAE y el RMSE se calculan con `sklearn.metrics`
sobre datos no vistos. Hoy no hay MAE, y el RMSE sale de una fórmula propia: desde
la tarea 021, scikit-learn ya no se usa en ningún lugar del sistema.

## Diseño

- **Cálculo:** el MAE y el RMSE se calculan con `sklearn.metrics`, usando `mean_absolute_error` y `root_mean_squared_error`. El modelo sigue siendo `statsmodels`.
- **Coherencia:** el RMSE debe dar el mismo valor que antes.
- **Dónde se agrega `mae`:**
  - En `point_metrics`.
  - En las métricas mensuales de `/analytics/forecast`.
  - En las diarias de `/analytics/predict`.
- **Sin MAE:** si no hay meses evaluados, el MAE es `null`, nunca cero.
- **Frontend:** una fila "MAE" en "Detalle técnico", en dinero o unidades. Las cuatro tarjetas en lenguaje simple y la etiqueta general no cambian, porque el MAE diría casi lo mismo que "Margen típico".
- **Proyecciones guardadas:** no guardan el MAE, así que no hay migración.
- **Evaluación:** el MAE se agrega para el modelo y para los tres cálculos simples, que dan el "Baseline MAE". Luego se regenera `docs/evaluacion/` con la misma semilla.

## Alcance

- `backend/app/ml_models/evaluation.py`, `backend/app/ml_models/forecast.py`
- `backend/app/schemas/schemas.py`, `backend/scripts/evaluate_models.py`
- `backend/tests/test_evaluation.py`, `backend/tests/test_ml.py`, `backend/tests/test_forecast_api.py`
- `frontend/src/types/forecast.ts`, `frontend/src/lib/metricExplanations.ts`
- `docs/evaluacion/`, `docs/ml-models.md`, `CLAUDE.md`, `docs/checking/VERIFICACION_TESIS.md`

## Pasos

1. Calcular el MAE y el RMSE con `sklearn.metrics` en `point_metrics`.
   - **Verificar:** un test con valores calculados a mano usando `MAE = (1/n)Σ|yᵢ − ŷᵢ|`, y el RMSE igual que antes.
2. Exponer `mae` en las métricas mensuales y diarias.
   - **Verificar:** tests de la API con `mae` presente, y `null` cuando no hay meses evaluados.
3. Mostrar el MAE en "Detalle técnico".
   - **Verificar:** RTL con la unidad correcta y "No disponible" cuando es `null`.
4. Agregar el MAE a la evaluación y regenerarla.
   - **Verificar:** `resultados.md` tiene la columna MAE para el modelo y las referencias, y dos ejecuciones dan lo mismo.
5. Actualizar la documentación y marcar REQ-37 como resuelta.
   - **Verificar:** `docs/ml-models.md` y `CLAUDE.md` listan el MAE.

## Criterios de terminado

- La API devuelve el MAE de ambos modelos, medido en datos no vistos.
- El MAE y el RMSE salen de `sklearn.metrics`.
- La evaluación reporta el MAE del modelo y de las referencias.

## STOP

- Detenerse si el RMSE de `sklearn` difiere del valor actual.
- Detenerse si alguna métrica pasa a calcularse con datos de entrenamiento.

## Mantenimiento

Cada métrica nueva entra en `point_metrics`, en los esquemas, en "Detalle técnico" y en la evaluación.

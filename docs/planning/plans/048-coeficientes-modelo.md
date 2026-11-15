# Plan 048: Exponer los coeficientes del modelo

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** S-M
- **Depende de:** —
- **Origen:** REQ-32; tarea C1 de `docs/reportes/verificacion_2026-11-14.md`
- **Planificado en:** commit `5dbd03d`, 2026-11-14

## Objetivo

La tesis presenta la ecuación `Y = β0 + β1X1 + … + βnXn + ε`, pero el sistema no muestra β0 ni βn. Los coeficientes existen en `fitted.params` de `statsmodels`, pero se descartan.

## Alcance

- `backend/app/ml_models/forecast.py`: guardar en `TargetForecast` los coeficientes del ajuste final de cada objetivo (`const`, `mes_indice`, `mes_2`…`mes_12`).
- `backend/app/services/prediction_service.py` y `backend/app/schemas/schemas.py`: campo `coeficientes` por objetivo en `MonthlyForecastResponse`, con la forma `{"monto": {"const": …, "mes_indice": …}, "cantidad": {…}}`.
- `frontend/src/types/forecast.ts`: el tipo nuevo. La UI no lo muestra.
- `backend/scripts/evaluate_models.py`: sección «Coeficientes del modelo final» en `docs/evaluacion/resultados.md`.
- Pruebas en `tests/test_ml.py` y `tests/test_forecast_api.py`.

## Pasos

1. Devolver los coeficientes desde `monthly_forecast_series`.
   - **Verificar:** con una serie lineal exacta, `const` y `mes_indice` coinciden con la recta que la genera.
2. Exponerlos en la API.
   - **Verificar:** `GET /analytics/forecast` incluye `coeficientes.monto.const` y `coeficientes.monto.mes_indice`, y `test_every_json_route_documents_its_response` pasa.
3. Agregarlos a la evaluación y volver a ejecutar `scripts/evaluate_models.py`.
   - **Verificar:** `resultados.md` muestra β0 y β1 iguales a los del reporte de verificación: 76,512.5860 y 1,429.4629 para el monto.
4. Cerrar la fila REQ-32 de la §10.

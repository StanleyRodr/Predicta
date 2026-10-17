# Plan 005: Extraer el procesamiento ML a `app/ml_models/`

## Estado

- **Prioridad:** P2
- **Esfuerzo:** M
- **Riesgo:** MED
- **Depende de:** `plans/001-baseline-pruebas.md`
- **Categoría:** deuda técnica
- **Planificado en:** commit `adcb0a4`, 2026-10-17

## Objetivo

Separar regresión, features y preparación de datos de HTTP, PDF y gráficos. Dejar rutas delgadas y permitir pruebas unitarias de la Regresión Lineal Múltiple.

## Estado actual

- `backend/app/api/analytics_routes.py` tiene 710 líneas.
- `_build_seasonal_features` y `_monthly_aggregates` viven en ese archivo.
- Tres reportes repiten entrenamiento y predicción estacional.
- `backend/app/ml_models/` está vacío.
- `resample("ME")` puede convertir meses ausentes en ingresos cero.

## Alcance

- `backend/app/ml_models/forecast.py` nuevo
- `backend/app/api/analytics_routes.py`
- `backend/tests/test_ml.py` y tests de analytics

No cambiar aún el stack de modelo: usar `sklearn.linear_model.LinearRegression`.

## Pasos

1. Crear funciones o clase para features, agregación mensual y predicción, con entradas y salidas tipadas.
   - **Verificar:** tests unitarios ejecutan sin importar `TestClient` ni generar PDF.
2. Mover la lógica diaria y mensual desde analytics a `ml_models/`.
   - **Verificar:** rutas llaman al módulo y no contienen entrenamiento duplicado.
3. Tratar meses sin observaciones como datos ausentes, no como ventas cero fabricadas; documentar la decisión.
   - **Verificar:** fixture con meses separados no crea filas cero intermedias en el entrenamiento.
4. Mantener respuestas y archivos PDF compatibles con el contrato actual.
   - **Verificar:** tests existentes de analytics y exportación pasan.

## Criterios de terminado

- `ml_models/` contiene lógica testeable de RLM.
- `analytics_routes.py` conserva HTTP y presentación, no entrenamiento duplicado.
- `pytest tests/test_ml.py tests/test_analytics.py -q` pasa.

## STOP

- Detenerse si preservar respuesta requiere cambiar contrato público.
- Detenerse si la decisión sobre meses faltantes exige datos que no existen en `ventas`.

## Mantenimiento

Nuevos predictores deben entrar por el módulo ML y tener tests unitarios antes de usarse en rutas.

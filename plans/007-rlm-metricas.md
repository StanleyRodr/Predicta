# Plan 007: Formalizar RLM para monto y cantidad

## Estado

- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** MED
- **Depende de:** `plans/005-extraer-ml.md`, `plans/006-schema-predicciones.md`
- **Categoría:** dirección / ML
- **Planificado en:** commit `adcb0a4`, 2026-10-17

## Objetivo

Usar Regresión Lineal Múltiple interpretable para predecir ingresos y unidades. Incluir estacionalidad mensual y día de semana. Exponer calidad e incertidumbre para apoyar decisiones de PyMEs retail.

## Estado actual

- `analytics_routes.py:186-191` ya crea tendencia y 12 indicadores mensuales.
- `/analytics/predict` usa solo índice de día (`analytics_routes.py:228-239`).
- `docs/ml-models.md` promete R², MAPE, RMSE e intervalos.
- El schema preparado por plan 006 guarda monto y cantidad.

## Diseño de features

- Modelo mensual: tendencia + 12 dummies de mes.
- Modelo diario: tendencia + 7 dummies de día de semana.
- Targets separados: `monto` y `cantidad`; entrenar un modelo por target o una interfaz común clara.
- No agregar feriados ni promociones en esta fase: requieren fuentes de datos nuevas.

## Alcance

- `backend/app/ml_models/forecast.py`
- `backend/app/api/analytics_routes.py`
- `backend/app/schemas/` si se agregan schemas de respuesta
- `backend/tests/test_ml.py` y tests de analytics
- `docs/ml-models.md`

## Pasos

1. Definir matriz de features y documentar nombres, tipos y orden estable.
   - **Verificar:** tests comprueban número y valores de features.
2. Entrenar dos targets con el mismo conjunto de predictores; evitar mezclar pesos monetarios con unidades.
   - **Verificar:** predicción devuelve campos separados para monto y cantidad.
3. Calcular R², MAPE y RMSE con validación temporal; no presentar R² como precisión universal.
   - **Verificar:** métricas se calculan sin fuga de datos futuros y tienen tests con dataset conocido.
4. Calcular intervalo de predicción usando residuales y devolver límites inferior/superior junto al punto estimado.
   - **Verificar:** límite inferior no es mayor que superior; valores monetarios y unidades no son negativos.
5. Persistir resultado y métricas en `predicciones` mediante la interfaz del plan 006.
   - **Verificar:** una petición guarda monto, cantidad, fecha y métrica asociada.
6. Documentar limitaciones: datos históricos mínimos, tendencia lineal y ausencia de variables externas.
   - **Verificar:** `docs/ml-models.md` describe features, métricas y límites reales.

## Criterios de terminado

- RLM mensual y diario usan múltiples predictores definidos.
- Monto y cantidad tienen predicciones separadas.
- API devuelve punto estimado, intervalo y métricas.
- Tests cubren tendencia, estacionalidad, día de semana, clipping y datos insuficientes.

## STOP

- Detenerse si el dataset no contiene `cantidad` después de migration.
- Detenerse si las métricas se calculan con datos usados para entrenamiento sin separación temporal.

## Mantenimiento

Toda nueva feature necesita justificación de negocio, datos disponibles y prueba de impacto. No agregar complejidad de modelo sin baseline comparativo.

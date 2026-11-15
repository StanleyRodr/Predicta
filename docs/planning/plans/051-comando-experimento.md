# Plan 051: Comando único del experimento

## Estado

- **Estado:** HECHO el 2026-11-14.
- **Prioridad:** P1
- **Esfuerzo:** M
- **Depende de:** 048
- **Origen:** §7 y REQ-61 de `docs/checking/VERIFICACION_TESIS.md`; decisiones del autor del 2026-11-14 (baseline y umbral); tarea C2 de `docs/reportes/verificacion_2026-11-14.md`
- **Planificado en:** commit `5dbd03d`, 2026-11-14

## Objetivo

La §7 pide ejecutar las fases del experimento en orden con un solo comando y registrar las métricas en un archivo con fecha, junto con el commit, la semilla y los parámetros del dataset.

## Decisiones

- **Entorno:** SQLite en memoria con los servicios reales del backend (`etl_service.load_sales`, `analytics_service.monthly_projection`), sin servidor ni base externa (decisión del autor).
- **Salida:** `docs/resultados/metricas_AAAA-MM-DD.json` (decisión del autor).
- **Criterio:** la hipótesis se cumple si el WAPE del monto en el horizonte 1 es menor que el de la mejor de las tres referencias. El MAPE se clasifica con la escala de Lewis (1982).
- **Fase 4 (frontend):** la cubren las E2E de la tarea 053.
- **Generador versionado (decisión del autor del 2026-11-14):** `DatosDePrueba/` estaba completo en `.gitignore`, así que `generar_ventas.py` solo existía en la máquina del autor. Ahora `.gitignore` versiona únicamente ese script; el XLSX sigue ignorado y se regenera idéntico con la semilla 2026. `generar_ventas.py` expone `build_sales(seed)` sin cambiar la secuencia aleatoria: el resultado se comparó fila por fila con el XLSX existente (28,667 filas idénticas).

## Alcance

- `backend/scripts/run_experiment.py` (nuevo), con estas fases:
  1. genera el dataset con `generar_ventas.py` (semilla 2026) en un directorio temporal;
  2. lo carga por el ETL con el mapeo;
  3. ajusta el modelo;
  4. escribe el JSON con la fecha, el commit, la semilla, los parámetros, las filas leídas, cargadas y rechazadas, las métricas por objetivo, el MAE de cada referencia, los coeficientes, el resultado de la hipótesis y la clasificación de Lewis.
- `backend/tests/test_run_experiment.py` (nuevo): ejecuta el experimento sobre un dataset pequeño y valida el JSON.
- `docs/resultados/metricas_2026-11-14.json`: la primera corrida.

## Pasos

1. Escribir el script y su prueba.
   - **Verificar:** la prueba pasa y dos corridas seguidas dan las mismas métricas.
2. Ejecutarlo con el dataset completo.
   - **Verificar:** el MAE y el RMSE del monto coinciden con los del horizonte 1 en `docs/evaluacion/resultados.md`.
3. Cerrar las filas §7 y REQ-61 de la §10.

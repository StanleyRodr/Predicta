# Reporte de verificación — 2026-11-14
Commit: `8dd376012927405a8917df274aa11a7c17069e5c` (verificación inicial); `cc8e9dd43d23856d2b2724037f802d4bd1843984` (después de las tareas 046 a 054)   Semilla del dataset: `2026` (`generar_ventas.py`, XLSX); evaluación con semilla `20261108`; el generador CSV alternativo no tiene semilla   Registros: `28,667`

Este reporte reemplaza a `verificacion_2026-11-08.md`. Verifica el sistema completo (tareas 001 a 045 en estado `HECHO` en `docs/planning/TASKS.md`) contra `docs/checking/VERIFICACION_TESIS.md`. La sección «Funciones del sistema fuera de VERIFICACION_TESIS.md» enumera lo que el sistema hace y la tesis todavía no describe. Las secciones «Decisiones del autor (2026-11-14)» y «Trabajo pendiente priorizado» son la entrada para el siguiente agente.

Dataset usado: `DatosDePrueba/ventas_fabricadas/ventas_tienda_2_anios.xlsx`. Tiene 28,667 filas, columnas `producto, monto, cantidad, categoria, fecha`, fechas de 2024-11-01 a 2026-10-31 (24 meses completos), 5 categorías (`Abarrotes`, `Bebidas`, `Cuidado Personal`, `Limpieza`, `Lácteos`), 0 nulos y 0 filas duplicadas.

## Actualización tras las tareas 046 a 054 (2026-11-14)

Las tareas de código C1 a C8 y D1 se ejecutaron como las tareas 046 a 054 de `docs/planning/TASKS.md`, en la rama `feat/046-cierre-verificacion`, con un commit por tarea. Todas tienen su plan en `docs/planning/plans/` y están cerradas. La CI de la rama pasó en la ejecución [`43678072381`](https://github.com/StanleyRodr/Predicta/actions/runs/43678072381), incluido el job nuevo `e2e`.

Los requisitos cuyo cambio pendiente es solo de la tesis conservan su estado: el código ya no cambiará, y el estado mejora cuando la tesis refleje la decisión del autor (§10 de `VERIFICACION_TESIS.md`). El documento `docs/reportes/correcciones_tesis_2026-11-14.md` reúne esos cambios para quien edite el LaTeX.

### Resumen actualizado

CUMPLE: 29 | NO CUMPLE: 6 | PARCIAL: 10 | NO VERIFICABLE: 0 | PENDIENTE: 2

- Los 6 NO CUMPLE (REQ-13, 23, 25, 30, 33 y 36) y los 10 PARCIAL (REQ-04, 05, 21, 22, 24, 26, 27, 29, 40 y 52) tienen decidida una corrección de la tesis, no del código.
- Los 2 PENDIENTE son REQ-43 (`SIN UMBRAL`) y REQ-56: los KPI están decididos e implementados, pero la tesis aún no los lista.

### Requisitos que cambiaron de estado

| REQ | Antes | Ahora | Evidencia |
|---|---|---|---|
| REQ-02 | PARCIAL | CUMPLE (interpretación aprobada por el autor el 2026-11-15) | Las rutas `def` del ETL y del modelo se delegan al *threadpool* (executor) de FastAPI. Medición: `backend/scripts/measure_concurrency.py` → `docs/evaluacion/concurrencia.md`. |
| REQ-11 | PARCIAL | CUMPLE | `backend/scripts/generate_dataset.py` con semilla 2026 y fecha fija; `tests/test_generate_dataset.py`. `generar_ventas.py` (semilla 2026) ya está versionado. |
| REQ-32 | PARCIAL | CUMPLE | `forecast.fitted_coefficients`; `GET /analytics/forecast` › `coeficientes`; `docs/evaluacion/resultados.md` › «Coeficientes del modelo final»; `tests/test_ml.py::test_coefficients_recover_the_line_that_generated_the_series`. |
| REQ-42 | NO CUMPLE | CUMPLE (ídem) | Igual que REQ-02. Durante la carga del XLSX completo (12.5 s), otro usuario recibió respuesta en 365.8 ms de mediana (máximo 536.5 ms), sin bloqueo. |
| REQ-50 | PARCIAL | CUMPLE | `frontend/e2e/predictions.spec.ts` › «REQ-50…»: 24 meses de historial + 12 proyectados desde la API, lienzo pintado. |
| REQ-51 | PARCIAL | CUMPLE | `frontend/e2e/dashboard.spec.ts` › «REQ-51…»: barras con las 5 categorías. |
| REQ-53 | NO VERIFICABLE | CUMPLE | `dashboard.spec.ts` y `predictions.spec.ts` › «REQ-53…» a 375 y 1440 px; capturas en `docs/evaluacion/capturas/`. La prueba encontró *scroll* horizontal a 375 px y se corrigió en `ChartFrame.tsx` y `PredictionsPage.tsx`. |
| REQ-54 | PARCIAL | CUMPLE | `dashboard.spec.ts` › «REQ-54…»: ningún evento `load` al cambiar de vista y de filtro. |
| REQ-60 | PARCIAL | CUMPLE | `backend/tests/test_serializacion_json.py::test_serializacion_json` y `::test_serializacion_json_through_the_api`. |
| REQ-61 | PARCIAL | CUMPLE | `python scripts/run_experiment.py` → `docs/resultados/metricas_2026-11-14.json` (commit `cc8e9dd`, sin cambios pendientes, semilla 2026). |
| REQ-62 | NO CUMPLE | CUMPLE | `frontend/e2e/fixtures.ts`: cada escenario falla ante cualquier error de consola. Detectó un 404 del `favicon.ico`, corregido con `public/favicon.svg`. |

Sin cambio de estado, pero con evidencia nueva: REQ-09 (`LICENSE` MIT; `license-checker --production --excludePrivatePackages` → `MIT: 46`), REQ-43 (latencia en reposo y bajo carga en `concurrencia.md`) y REQ-56 (tarjeta «Crecimiento mensual»: `analytics_service.monthly_growth`, `GrowthCard.tsx`).

### Comandos de la verificación final (commit `cc8e9dd`)

- `python scripts/run_experiment.py` → WAPE del monto 9.32 % frente a 10.41 % del promedio móvil de 3 meses: la hipótesis se cumple; MAPE 9.29 %, «muy precisa» según Lewis.
- `pytest --cov=app` → `501 passed`; cobertura TOTAL 97 % (2,314 sentencias, 79 sin cubrir).
- `ruff check app/ scripts/` → `All checks passed!`; `mypy` → `Success: no issues found in 32 source files`.
- `alembic check` → `No new upgrade operations detected.`; `pip-audit` → `No known vulnerabilities found`.
- `python scripts/evaluate_models.py` → sin cambios en `docs/evaluacion/`.
- Frontend: `npm run lint` y `typecheck` → exit 0; `npm test -- --run` → `270 passed`; `npm run build` → correcto; `npm audit --omit=dev --audit-level=high` → `found 0 vulnerabilities`; `npm run e2e` → `8 passed`.
- `python scripts/measure_concurrency.py` → `docs/evaluacion/concurrencia.md`.

## Resumen (verificación inicial)
CUMPLE: 18 | NO CUMPLE: 8 | PARCIAL: 18 | NO VERIFICABLE: 1 | PENDIENTE: 2

Cambios frente al reporte del 2026-11-08 (CUMPLE 15, NO CUMPLE 14, PARCIAL 16, NO VERIFICABLE 1, PENDIENTE 1):

- Mejoran: REQ-07, REQ-09, REQ-28, REQ-37, REQ-41 (a CUMPLE); REQ-20 se mantiene; REQ-21, REQ-22, REQ-24, REQ-26, REQ-29, REQ-52, REQ-60 (de NO CUMPLE a PARCIAL).
- Empeoran: REQ-30 (de CUMPLE a NO CUMPLE) y REQ-05 (de CUMPLE a PARCIAL). El modelo de producción ahora se ajusta con `statsmodels.OLS`, no con `sklearn.linear_model.LinearRegression`.
- REQ-43 pasa a `PENDIENTE DE DEFINIR`: la latencia ya está medida, pero la tesis no fija un umbral.

## Detalle
| REQ | Estado | Evidencia (archivo/prueba/salida) | Nota |
|---|---|---|---|
| REQ-01 | CUMPLE | `backend/requirements.txt` · `fastapi==0.143.3`; `backend/app/main.py` · `create_app`; routers `/users`, `/etl`, `/analytics`; `backend/tests/test_forecast_api.py::test_every_json_route_documents_its_response` | API REST con GET/POST/PUT/DELETE y `response_model` en cada ruta JSON. |
| REQ-02 | PARCIAL | `backend/app/main.py` · `lifespan`, middlewares `async`; `backend/app/api/*.py` (todas las rutas son `def`) | Las rutas de ETL y modelo son síncronas: FastAPI las ejecuta en su *threadpool*. Solo el correo usa `BackgroundTasks` (`email_service.send_in_background`). No hay `async def` en ETL ni en el modelo. |
| REQ-03 | CUMPLE | `backend/requirements.txt` · `psycopg2-binary`; `backend/app/core/config.py` (`postgresql+psycopg2://`); `alembic current` → `0008_contrasenas_bloqueo (head)`; `alembic check` → `No new upgrade operations detected.`; CI con PostgreSQL 17 | 8 migraciones en `backend/alembic/versions/`. La suite también corre sobre PostgreSQL con `TEST_DATABASE_URL`. |
| REQ-04 | PARCIAL | `etl_service.py` · `_parse_xlsx` (`pd.read_excel`); `forecast.py` · `monthly_aggregates` (`pd.to_datetime`, `groupby`) | Pandas lee el XLSX y agrega por mes para el modelo. CSV usa `csv.DictReader`, SQL usa un parser propio y la validación se hace fila por fila en Python, no con `DataFrame`. |
| REQ-05 | PARCIAL | `backend/app/ml_models/evaluation.py` · `point_metrics` (`mean_absolute_error`, `root_mean_squared_error`); `forecast.py` · `sm.OLS` | Scikit-Learn solo calcula las métricas. El entrenamiento usa `statsmodels.OLS` (ver REQ-30). |
| REQ-06 | CUMPLE | `frontend/package.json` · `react ^19.1.1`; `frontend/src/App.tsx`; `npm test -- --run` → 43 archivos, 268 pruebas correctas | SPA React 19 + TypeScript + Vite. |
| REQ-07 | CUMPLE | `frontend/package.json` · `@tailwindcss/vite ^4.1.14`; `frontend/node_modules/tailwindcss` 4.3.3 (instalado por el plugin); `frontend/vite.config.ts` · `tailwindcss()`; `frontend/src/index.css` · `@import "tailwindcss"`; primitivas en `src/components/ui/` | Tailwind v4 se configura con el plugin oficial de Vite, que instala `tailwindcss`. Los componentes usan clases de utilidad. |
| REQ-08 | CUMPLE | `frontend/package.json` · `chart.js ^4.5.0`, `react-chartjs-2 ^5.3.0`; `components/forecast/ForecastChart.tsx`, `components/analytics/HistoryLineChart.tsx`, `CategoryBarChart.tsx`, `CategoryComparisonChart.tsx`, `YearOverlayChart.tsx`, `MonthDetailChart.tsx`; `chartsAccessibility.test.tsx` | Todas las gráficas usan Chart.js dentro de `ChartFrame`. |
| REQ-09 | CUMPLE | `pip-licenses --summary` (117 paquetes del venv, ninguno privativo); `pip-licenses --packages` sobre `requirements.txt` (ver tabla abajo); `npx license-checker --summary` → MIT 248, Apache-2.0 19, ISC 13, BSD-2-Clause 8, BSD-3-Clause 3, MIT-0 2, MPL-2.0 2, BlueOak-1.0.0 2, Python-2.0 1, CC-BY-4.0 1, CC0-1.0 1, UNLICENSED 1; `--production` → MIT 46, UNLICENSED 1 | Todas las dependencias son de código abierto. El único `UNLICENSED` es el propio `predicta-frontend@0.1.0` (`"private": true` y sin campo `license`), no una dependencia. El repositorio no tiene archivo `LICENSE`: el reporte anterior citaba un `LICENSE` MIT que no existe (nueva discrepancia en la §10). `fpdf2` (LGPL-3.0) y `psycopg2-binary` (LGPL) son copyleft débil y se usan como bibliotecas sin modificar. |
| REQ-10 | CUMPLE | `DatosDePrueba/ventas_fabricadas/generar_ventas.py` · `main` (`SEED = 2026`, `START = 2024-11-01`, `END = 2026-10-31`, 5 categorías con pesos y factor mensual); XLSX de 28,667 filas | Dataset sintético generado con un script en Python. |
| REQ-11 | PARCIAL | `generar_ventas.py` · `np.random.default_rng(SEED)`; `backend/scripts/generate_dataset.py` · `random` sin semilla, `start_date = datetime.now() - timedelta(days=days)` | El generador XLSX es reproducible. El CSV alternativo no lo es: no tiene semilla y su fecha de inicio depende del día en que se ejecuta. |
| REQ-12 | CUMPLE | `etl_service.py` · `load_sales`; `etl_routes.py` · `upload_ventas`; `tests/test_etl.py::test_upload_csv_returns_success`; medición local: XLSX completo → `registros_cargados: 28667`, `filas_rechazadas: 0` | El sistema usa archivos (CSV, XLSX o `.sql` con `INSERT ... VALUES`) que se cargan a la tabla `ventas` de PostgreSQL. |
| REQ-13 | NO CUMPLE | `backend/app/models/models.py` · `Venta` (`id_venta`, `id_usuario`, `producto`, `monto`, `cantidad` DECIMAL(10,2), `categoria`, `fecha_venta`); XLSX `producto, monto, cantidad, categoria, fecha` | No existen `precio_unitario` ni `total`, y la tabla tiene `producto` e `id_usuario`, que la tesis no menciona. `cantidad` es decimal, no entero. Avance: el ETL acepta una columna `precio_unitario` y deriva `monto = round(precio_unitario × cantidad, 2)` (`etl_service._derive_amount`), pero no la guarda. |
| REQ-20 | CUMPLE | `forecast.py` · `monthly_aggregates` (filas de PostgreSQL → `pd.DataFrame`); `etl_service._parse_xlsx` (`pd.read_excel`); `tests/test_ml.py::test_monthly_aggregates_sums_sales_by_month` | La tesis dice «PostgreSQL o archivos planos». Los registros de PostgreSQL llegan a un DataFrame para el modelo, y el XLSX se lee con Pandas. |
| REQ-21 | PARCIAL | `services/column_mapping.py` · `propose_mapping`, `validate_mapping`, `apply_mapping`; `POST /etl/analizar-columnas`; `tests/test_column_mapping.py::test_generated_dataset_is_proposed_as_exact`, `::test_real_dataset_headers_are_proposed` | Los encabezados se asignan a roles (`producto`, `categoria`, `monto`, `precio_unitario`, `cantidad`, `fecha`) por nombre exacto o sinónimo, y el usuario revisa la propuesta. Los roles no coinciden con el esquema de REQ-13. |
| REQ-22 | PARCIAL | `etl_service.py` · `build_venta`, `_is_missing`, `_parse_date`, `_parse_amount`; `tests/test_etl.py::test_upload_rejects_invalid_rows_without_silent_defaults` | Las filas con fecha o monto nulos se rechazan, no se cargan y se reportan con su número de fila. El resultado coincide con la tesis, pero el mecanismo es una validación por fila, no `dropna` sobre un DataFrame. |
| REQ-23 | NO CUMPLE | Búsqueda de `outlier`, `atipic`, `quantile`, `zscore` en `backend/app/` sin resultados | No hay filtro de atípicos. Los únicos límites son de formato: monto > 0, ≤ 99,999,999.99 y cantidad ≥ 0. |
| REQ-24 | PARCIAL | `forecast.py` · `monthly_aggregates` (`df["fecha"] = pd.to_datetime(df["fecha"])`); `etl_service._parse_date` → `datetime.date` | La conversión a `datetime64[ns]` ocurre al agregar para el modelo, no en el ETL de carga. En la base de datos la fecha es `DATE`. |
| REQ-25 | NO CUMPLE | `forecast.py` · `build_weekly_features` (día de la semana, solo modelo diario), `build_seasonal_features` (mes, solo con 36+ meses) | No se generan las tres columnas día de la semana, mes y semana ISO. La semana del año no se usa en ningún lugar. |
| REQ-26 | PARCIAL | `analytics_service.py` · `daily_sales`, `daily_revenue` (`GROUP BY fecha_venta`), `category_breakdown`, `sales_series(por_categoria=True)`; `forecast.py` · `monthly_aggregates` (`groupby` mensual); `tests/test_series.py::test_series_by_category_returns_one_point_per_month_and_category`, `::test_monthly_series_total_matches_global_stats_in_the_same_range` | Hay sumas por día, por mes y por categoría, verificadas con pruebas. Se hacen en SQL; el único `groupby` de Pandas es mensual. No hay un `groupby` por día y categoría en Pandas. |
| REQ-27 | PARCIAL | `category_service.py` · `normalize_category` (mayúsculas, espacios, acentos; 5 categorías canónicas; las desconocidas se conservan en *Title Case*), `normalize_product` (`string.capwords`: espacios simples y cada palabra con mayúscula inicial, conserva acentos); migración `0006_producto_normalizado`; `tests/test_categories.py`, `tests/test_products.py` | Las categorías se normalizan por completo. Los productos conservan los acentos a propósito, así que «Café» y «Cafe» quedan como dos productos distintos. |
| REQ-28 | CUMPLE | `forecast.py` · `monthly_aggregates`, `_split_partial_month` (`sort_values("fecha")`), `_monthly_design` (`mes_indice` float, `mes_2..mes_12` int); `tests/test_ml.py::test_seasonal_features_use_trend_and_eleven_month_dummies` | La serie mensual está ordenada cronológicamente y la matriz `X` es completamente numérica. |
| REQ-29 | PARCIAL | `analytics_service.py` · `monthly_projection` → `daily_sales` → `forecast_from_sales`; `daily_revenue`, `global_metrics`, `category_breakdown` | Las consultas descriptivas y el modelo leen la misma tabla `ventas` que carga el único ETL. No hay una salida transformada común: el modelo se alimenta de `daily_sales` y lo descriptivo de otras consultas SQL. |
| REQ-30 | NO CUMPLE | `backend/app/ml_models/forecast.py` · `sm.OLS(...).fit()` (docstring: «Every model is ordinary least squares (`statsmodels.OLS`)»); búsqueda de `LinearRegression` y `RandomForest` sin resultados | El algoritmo sí es Regresión Lineal Múltiple por OLS, pero con `statsmodels`, no con `sklearn.linear_model`. Se usa `statsmodels` por los intervalos de predicción del 95 % (`get_prediction`). Otros modelos: ETS con tendencia amortiguada (`statsmodels ETSModel`) solo en `backend/scripts/evaluate_models.py`, como comparación y nunca en producción. No hay Random Forest. |
| REQ-31 | CUMPLE | `forecast.py` · `sm.OLS` con `sm.add_constant` | OLS con intercepto; no hay Ridge ni Lasso. |
| REQ-32 | PARCIAL | `forecast.py` · `monthly_regression`, `_fit_and_project` (el resultado de `sm.OLS().fit()` tiene `.params`) | El intercepto y los coeficientes existen en `fitted.params`, pero no se registran en logs ni se exponen en la API, en los PDF ni en `docs/evaluacion/`. Los valores de abajo se calcularon con un script del *scratchpad*. |
| REQ-33 | NO CUMPLE | `forecast.py` · `_monthly_design`, `applied_model`; `tests/test_ml.py::test_model_and_horizon_follow_observed_months` | X1 (`mes_indice`, meses de calendario transcurridos) sí existe. X2 (11 *dummies* de mes) solo entra con 36 meses o más y todos los meses del calendario observados. Con el dataset de la tesis (24 meses) el modelo usa solo la tendencia. X3 (*lag*) no existe. |
| REQ-34 | CUMPLE | `forecast.py` · `build_seasonal_features` (`mes_2`…`mes_12`, enero como referencia) | One-hot del mes cuando aplica la estacionalidad (ver REQ-33). |
| REQ-35 | CUMPLE | `forecast.py` · `TARGETS = ("monto", "cantidad")`; `prediction_service.forecast_payload` | Se ajustan dos modelos separados, uno para el monto y otro para la cantidad. P-05 sigue pendiente en la tesis. |
| REQ-36 | NO CUMPLE | `evaluation.py` · `one_step_metrics`, `rolling_origin`; `forecast.py` · `_holdout_metrics` | No se usa `train_test_split`. Mensual: el modelo se reajusta en cada uno de los últimos 6 meses y predice el siguiente sin verlo (origen móvil, 6 orígenes). Diario: el último 20 % se reserva en orden cronológico (*holdout*). No hay `shuffle`. |
| REQ-37 | CUMPLE | `evaluation.py` · `point_metrics`; `tests/test_evaluation.py::test_mae_and_rmse_follow_the_thesis_formulas`, `::test_rolling_origin_never_lets_a_model_see_the_month_it_predicts`; `tests/test_ml.py::test_metrics_come_from_one_month_ahead_predictions_of_the_last_months` | MAE y RMSE con `sklearn.metrics`, solo sobre meses no vistos. También calcula R², MAPE, WAPE y MASE. |
| REQ-38 | CUMPLE | `GET /analytics/forecast`, `GET /analytics/predict`, `POST /analytics/predicciones` → `analytics_service.monthly_projection` / `predict_next_day` | El modelo se reajusta en cada solicitud con los datos actuales del usuario, sin intervención manual. |
| REQ-40 | PARCIAL | `prediction_service.forecast_payload` (`forecast.historial`, DataFrame → lista de dicts → `MonthlyForecastResponse`); `schemas.py` · `MonthTotals.periodo` `YYYY-MM`, `DailyForecastResponse.proxima_fecha` `YYYY-MM-DD`; `analytics_service.daily_revenue` (`str(date)` → `YYYY-MM-DD`) | El histórico del pronóstico sale de un DataFrame y se serializa con el esquema de Pydantic. Las fechas ahora son ISO (el problema de la hora en el reporte anterior quedó corregido). Las estadísticas descriptivas salen de SQL, no de un DataFrame. |
| REQ-41 | CUMPLE | `GET /analytics/forecast` → `historial`, `mes_parcial`, `proyeccion` (con `inferior`/`superior` y `extrapolacion`), `metricas`; `tests/test_forecast_api.py::test_forecast_returns_history_projection_and_metrics_without_writing`; `frontend/src/components/forecast/forecastChartData.ts` | Una sola respuesta lleva el histórico y la proyección por separado. |
| REQ-42 | NO CUMPLE | `etl_routes.py` · `upload_ventas` (`def`); `analytics_routes.py` · `monthly_forecast`, `predict_next_day` (`def`) | El ETL y el ajuste son síncronos, ejecutados en el *threadpool*. La carga completa del XLSX tardó 14,862 ms en una sola solicitud. |
| REQ-43 | PENDIENTE DE DEFINIR | Medición local (ver «Latencia») | `SIN UMBRAL`: valores medidos y reportados sin aprobar ni reprobar. |
| REQ-44 | CUMPLE | `frontend/src/api/http.ts` (Axios, `VITE_API_URL`); `backend/app/main.py` (CORS); despliegue separado Vercel/Railway (`docs/despliegue.md`) | El frontend y el backend son aplicaciones separadas y se comunican solo por HTTP/JSON. |
| REQ-50 | PARCIAL | `components/forecast/ForecastChart.tsx` + `forecastChartData.ts` (línea continua para el histórico, discontinua para la proyección, banda del 95 %); `HistoryLineChart.tsx`; `components/forecast/forecast.test.tsx` | La gráfica combinada de histórico y proyección ya existe. Falta la prueba E2E con datos de la API (solo hay pruebas unitarias con jsdom). |
| REQ-51 | PARCIAL | `CategoryBarChart.tsx` («Ingresos por categoría»), `CategoryComparisonChart.tsx`; `chartsAccessibility.test.tsx::names the category bar chart and lists its values` | Hay barras por categoría, pero no gráfico de sectores y no hay prueba E2E. |
| REQ-52 | PARCIAL | `pages/PredictionsPage.tsx` (`<h1>` «Siguiente movimiento», proyección global, por categoría o por producto); `components/analytics/SeriesViewSelector.tsx` · `VIEW_LABELS` = «General», «Por categoría», «Por mes», «Historial completo» | Las dos vistas existen en la práctica. Ningún título dice «Proyección Global» ni «Análisis por Categoría». |
| REQ-53 | NO VERIFICABLE | No hay Playwright ni capturas. Hay 20 usos de prefijos `sm:`/`md:`/`lg:` en `frontend/src` | Por decisión del autor en esta corrida no se tomaron capturas a 375 px ni a 1440 px. |
| REQ-54 | PARCIAL | TanStack Query en `DashboardPage.tsx`/`PredictionsPage.tsx`; React Router (SPA); `pages/DashboardPage.test.tsx` | Los filtros actualizan los datos sin navegación completa. Falta la prueba E2E que demuestre que no se dispara `load`. |
| REQ-55 | CUMPLE | `DashboardPage.tsx` · `MetricCard` («Ingresos totales», «Operaciones», «Ticket promedio», «Venta más alta») + gráficas históricas; `PredictionsPage.tsx` · `ForecastChart`, `ForecastTable`, `ForecastQuality` | Las capas descriptiva y predictiva están visibles. |
| REQ-56 | PENDIENTE DE DEFINIR | `DashboardPage.tsx` (4 KPI) | La tesis no lista los KPI (P-06). El sistema muestra ingresos totales, operaciones, ticket promedio y venta más alta, más series por mes, día y categoría. |
| REQ-60 | PARCIAL | `tests/test_forecast_api.py::test_forecast_returns_history_projection_and_metrics_without_writing`, `::test_every_json_route_documents_its_response`; `tests/test_series.py::test_openapi_documents_series_and_sales_responses` | Hay pruebas de contrato JSON. No existe `test_serializacion_json` ni una prueba que compare un DataFrame con el JSON resultante valor por valor («sin pérdida»). |
| REQ-61 | PARCIAL | `backend/scripts/evaluate_models.py` → `docs/evaluacion/resultados.md` + 5 CSV + 2 PNG (semilla 20261108); la reejecución del 2026-11-14 no produjo cambios en `git status` (reproducible) | Las métricas quedan registradas y son reproducibles, pero no en un archivo fechado con el commit (`resultados/metricas_AAAA-MM-DD.json`). Sin umbral (P-02). |
| REQ-62 | NO CUMPLE | `chartsAccessibility.test.tsx`, `chartFormats.test.tsx` (unitarias, jsdom) | No hay prueba E2E de Chart.js en un navegador real ni revisión de la consola. |

### Licencias de las dependencias de producción de Python (`requirements.txt`)

| Paquete | Versión | Licencia |
|---|---|---|
| fastapi | 0.143.3 | MIT |
| uvicorn | 0.54.0 | BSD-3-Clause |
| SQLAlchemy | 2.1.5 | MIT |
| psycopg2-binary | 2.9.13 | LGPL |
| alembic | 1.20.0 | MIT |
| pydantic / pydantic-settings | 2.14.1 / 2.16.2 | MIT |
| email-validator | 2.3.0 | Unlicense |
| PyJWT | 2.15.1 | MIT |
| bcrypt | 5.0.0 | Apache-2.0 |
| python-multipart | 0.0.32 | Apache-2.0 |
| pandas | 3.0.6 | BSD-3-Clause |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| scikit-learn | 1.9.1 | BSD-3-Clause |
| statsmodels | 0.15.0 | BSD-3-Clause |
| matplotlib | 3.11.2 | PSF |
| fpdf2 | 2.8.9 | LGPL-3.0-only |
| openpyxl | 3.1.5 | MIT |
| python-dotenv | 1.2.4 | BSD-3-Clause |
| slowapi | 0.1.10 | MIT |
| loguru | 0.7.3 | MIT |

Auditoría de vulnerabilidades: `pip-audit -r requirements.txt --ignore-vuln PYSEC-2025-183` → `No known vulnerabilities found`; `npm audit --omit=dev --audit-level=high` → `found 0 vulnerabilities`.

### Latencia (REQ-43, `SIN UMBRAL`)

Medición local con `TestClient` sobre SQLite en memoria, con las 28,667 ventas del XLSX cargadas y 30 solicitudes por endpoint. No incluye red ni PostgreSQL, así que es tiempo de la aplicación, no de producción. Script: `latency.py`, en el *scratchpad* de esta sesión, fuera del repositorio.

| Endpoint | n | p50 (ms) | p95 (ms) | Estado |
|---|---|---|---|---|
| `POST /etl/upload-ventas` (XLSX completo) | 1 | 14,862 | — | 200 |
| `GET /analytics/stats` | 30 | 12.1 | 15.8 | 200 |
| `GET /analytics/stats/categories` | 30 | 16.8 | 17.8 | 200 |
| `GET /analytics/stats/temporal` | 30 | 13.3 | 14.8 | 200 |
| `GET /analytics/stats/series` | 30 | 33.6 | 36.4 | 200 |
| `GET /analytics/predict` | 30 | 29.3 | 34.7 | 200 |
| `GET /analytics/forecast` | 30 | 82.3 | 105.6 | 200 |
| `GET /analytics/forecast?categoria=Bebidas` | 30 | 84.3 | 95.3 | 200 |

### Experimento de validación: comando único (§7)

No existe un comando que ejecute en orden las cuatro fases (ingesta, ETL y ajuste, métricas en un archivo fechado, frontend). Hoy las fases están separadas: `generar_ventas.py` → carga por la UI o `POST /etl/upload-ventas` → `python scripts/evaluate_models.py` → `npm run dev`.

## Métricas del modelo (para el Capítulo 4)

Fuente: `monthly_forecast_series` sobre el XLSX completo (24 meses completos, de 2024-11 a 2026-10). Con ese historial el modelo aplicado es `tendencia`, con un horizonte de 12 meses (de 2026-11 a 2027-10). Las métricas son el promedio de 6 predicciones a un mes, cada una sobre un mes no visto (origen móvil). Coinciden con la fila «Regresión (regla aplicada), horizonte 1» de `docs/evaluacion/resultados.md`.

**Monto (pesos)**
MAE: 9,987.74 | RMSE: 13,418.30 | Baseline MAE: 11,150.85 (promedio móvil de 3 meses, la mejor referencia en el horizonte 1); otras referencias en h=1: último valor 14,402.71 y mismo mes del año anterior 12,472.57
MAPE 9.29 % · WAPE 9.32 % · MASE 0.49 · R² −0.67 · mejora del WAPE frente a la mejor referencia: +10.43 %

**Cantidad (unidades)**
MAE: 281.29 | RMSE: 368.23 | mejor referencia: mismo mes del año anterior · MAPE 9.72 % · WAPE 9.70 % · MASE 0.53 · R² −0.56 · mejora frente a la referencia: −8.68 % (la regresión pierde)

**Coeficientes del modelo final** (ajuste con los 24 meses; `Y = β0 + β1·mes_indice`)
- Monto: β0 = 76,512.5860, β1 = 1,429.4629 (R² en la muestra 0.2326)
- Cantidad: β0 = 2,277.9367, β1 = 29.1613 (R² en la muestra 0.1452)
- β2…β12 (estacionalidad) no se estiman con 24 meses, y β3 de la tesis (*lag*) no existe.

Resultado del backtest frente a las referencias (WAPE, horizontes 1 a 6): la regla aplicada gana a la mejor referencia en los horizontes 1 y 2 y pierde en los horizontes 3 a 6. Pierde contra el mismo mes del año anterior solo en 1 de 6 horizontes. El ETS amortiguado, que es solo de comparación, tiene un WAPE menor en los 6 horizontes. Diagnóstico de residuos del modelo final: Ljung–Box p = 0.3455 (3 rezagos) y 0.4476 (6 rezagos); Breusch–Pagan p = 0.2701. Ninguna prueba es significativa al 5 %.

## Pendientes de la §9: estado real en el código

La §9 no se modificó. Esta tabla dice qué eligió el código antes de las decisiones del autor; lo que el autor resolvió está en «Decisiones del autor (2026-11-14)».

| ID | Qué hace hoy el código | Evidencia | Lo que falta |
|---|---|---|---|
| P-01 | Tres referencias: último valor, mismo mes del año anterior y promedio móvil de 3 meses. La API reporta `referencia` y `mejora_vs_referencia` frente a la mejor de las tres. | `evaluation.py` · `naive_last`, `seasonal_naive`, `moving_average`, `improvement`; `tests/test_evaluation.py::test_baselines_are_named_for_the_report` | Elegir en la tesis cuál es el «método empírico tradicional» de la hipótesis. |
| P-02 | No hay umbral. La UI muestra la calidad con `ForecastQuality` y el texto de `metricExplanations.ts`. | `frontend/src/components/forecast/ForecastQuality.tsx` | Fijar el umbral (por ejemplo, «WAPE menor que la mejor referencia»). |
| P-03 | División temporal: origen móvil en el modelo mensual y *holdout* cronológico del 20 % en el diario. No se usa `train_test_split`. | `evaluation.py` · `rolling_origin`, `one_step_metrics`; `forecast.py` · `_holdout_metrics` | Actualizar `metodos.tex` (ver REQ-36). |
| P-04 | One-hot de mes (`mes_2`…`mes_12`), pero solo con 36 meses o más. | `forecast.py` · `build_seasonal_features`, `SEASONAL_MONTHS = 36` | Explicar en la tesis la regla escalonada y por qué no se aplica con el dataset de 24 meses. |
| P-05 | Ambas variables, con un modelo cada una: `monto` y `cantidad`. | `forecast.py` · `TARGETS` | Precisarlo en la tesis. |
| P-06 | KPI del dashboard: ingresos totales, operaciones, ticket promedio y venta más alta. | `DashboardPage.tsx` | Listarlos en el OE1. |
| P-07 | Sin cambios en el código: todas las licencias son abiertas (REQ-09). Existe un despliegue documentado en Vercel, Railway, Neon y Brevo. | `docs/despliegue.md` | Tabla de costos frente a Power BI y Tableau. |
| P-08 | Sin criterio y sin filtro. | — | Decidir el criterio o retirar la afirmación (REQ-23). |

## Funciones del sistema fuera de VERIFICACION_TESIS.md

Funciones implementadas y probadas que la tesis no describe. La última columna propone dónde podría mencionarlas la tesis; la decisión es del autor.

### Ingesta y calidad de datos

| Función | Evidencia | Pruebas | Dónde encaja en la tesis |
|---|---|---|---|
| **Mapeo de columnas** (tarea 035): `POST /etl/analizar-columnas` devuelve los encabezados, una muestra de 5 filas y una propuesta por rol (`exacto` o `sinonimo`, sin coincidencia difusa). El usuario la revisa en la UI y se envía como `mapeo` a `/etl/upload-ventas`. | `services/column_mapping.py` (`SYNONYMS`, `propose_mapping`, `validate_mapping`, `apply_mapping`); `frontend/src/components/etl/ColumnMappingPanel.tsx` | `tests/test_column_mapping.py` | ETL › Extracción (REQ-21); PE1 |
| **Sinónimos de datasets reales** (tarea 036): encabezados en inglés de Online Retail II (UCI), Iowa Liquor Sales y Open e-commerce 1.0. | `column_mapping.SYNONYMS` (grupos `# 036`); `backend/scripts/prepare_real_dataset.py`; `docs/pruebas/036-datos-reales.md` | `tests/test_column_mapping.py::test_real_dataset_headers_are_proposed` | Validación con datos reales; limitaciones del dataset sintético |
| **Monto derivado del precio unitario**: si falta `monto`, se calcula `round(precio_unitario × cantidad, 2)`. | `etl_service._derive_amount` | `tests/test_etl.py` | Esquema (REQ-13, `total` derivado) |
| **Tres formatos de archivo**: CSV (detecta `,`, `;` o tabulador; UTF-8 con respaldo cp1252), XLSX (solo la primera hoja, con control de tamaño descomprimido) y `.sql` (solo analiza `INSERT ... VALUES`, nunca ejecuta SQL). | `etl_service._parse_csv`, `_parse_xlsx`, `_check_xlsx_size`, `_parse_sql` | `tests/test_etl.py`, `tests/test_etl_hardening.py` | ETL › Extracción (REQ-20) |
| **Validación por fila sin valores inventados**: no rellena montos con 0.0 ni fechas con «hoy»; `cantidad` vale 1 por defecto; rechaza negativos, números de solo dígitos como fecha y caracteres de control. Inserción transaccional; responde con filas leídas, cargadas y rechazadas, y hasta 20 errores con su número de fila. | `etl_service.build_venta`, `load_sales`, `MAX_REPORTED_ERRORS` | `tests/test_etl.py::test_upload_rejects_invalid_rows_without_silent_defaults` | ETL › Limpieza (REQ-22); métricas de calidad para la PE1 |
| **Rechazo de archivos duplicados**: guarda el SHA-256 del archivo por usuario (`cargas_archivo`). Repetir la carga responde 409. | `models.CargaArchivo`; `etl_service.read_limited`, `DuplicateUploadError` | `tests/test_etl.py` | Integridad de datos (PE1) |
| **Límites de carga**: 25 MB por archivo, 200 MB descomprimido en XLSX, `MAX_UPLOAD_ROWS` filas, 413 por encima de 26 MB en `/etl/*`. | `etl_service.MAX_UPLOAD_BYTES`; `core/middleware.BodySizeLimitMiddleware` | `tests/test_body_limit.py`, `tests/test_etl_hardening.py` | Seguridad / robustez |
| **Carga de varios archivos a la vez** (tarea 038): hasta 50 por selección, en orden natural por nombre. Los archivos con los mismos encabezados comparten un mapeo revisado, y un fallo o un 409 no detiene el resto. | `frontend/src/lib/uploadBatch.ts`; `components/etl/UploadBatchTable.tsx`; `pages/UploadPage.tsx` | `UploadPage.batch.test.tsx`, `components/etl/batch.test.tsx`, `lib/uploadBatch.test.ts` | Dashboard › Carga de datos |
| **Purga del historial**: `DELETE /etl/clear-history` borra las ventas y los *hashes* del usuario. | `etl_service.clear_sales`; modal «Purgar historial» en `UploadPage.tsx` | `tests/test_etl.py` | Gestión de datos |
| **Normalización de productos** y migración de datos existentes. | `category_service.normalize_product`; `alembic/versions/0006_producto_normalizado.py` | `tests/test_products.py` | ETL › Estandarización (REQ-27) |

### Analítica descriptiva

| Función | Evidencia | Pruebas | Dónde encaja en la tesis |
|---|---|---|---|
| **Filtros de fecha** inclusivos `fecha_desde`/`fecha_hasta`; un rango invertido responde 422. | `analytics_service._check_date_range`, `_apply_date_range` | `tests/test_analytics.py`, `tests/test_series.py::test_sales_page_rejects_inverted_range` | Dashboard (REQ-54) |
| **Series por dimensión**: `GET /analytics/stats/series` por mes o día, global, por categoría o separada por categoría; no rellena con ceros los periodos sin ventas. | `analytics_service.sales_series` | `tests/test_series.py` | Analítica descriptiva (REQ-26, REQ-55) |
| **Explorador del dashboard**: vistas «General», «Por categoría», «Por mes» e «Historial completo»; años superpuestos, comparación entre categorías, totales mensuales y detalle diario. | `pages/DashboardPage.tsx`; `components/analytics/*` | `DashboardPage.test.tsx`, `analytics.test.tsx` | REQ-52 (nombres de vistas) |
| **Historial de ventas paginado** con filtro por categoría y producto (`GET /analytics/ventas`) y **lista de productos por categoría** (`GET /analytics/productos`) para selectores dependientes. | `analytics_service.sales_page`, `category_products`; `components/etl/SalesHistoryTable.tsx`, `components/analytics/CategoryProductFilter.tsx` | `tests/test_series.py::test_sales_page_filters_by_date_range_and_category`, `tests/test_products.py` | Analítica descriptiva |
| **Convención numérica `0,000.00`** en la API, la UI y los reportes. | `services/formatting.py`; `frontend/src/lib/formatters.ts` | `tests/test_formatting.py`, `lib/formatters.test.ts` | Presentación de resultados |

### Analítica predictiva

| Función | Evidencia | Pruebas | Dónde encaja en la tesis |
|---|---|---|---|
| **Modelo escalonado según el historial**: menos de 6 meses → 422; de 6 a 23, tendencia con horizonte de la mitad de los meses; de 24 a 35, tendencia a 12 meses; 36 o más con los 12 meses observados, tendencia + estacionalidad. | `forecast.applied_model`, `monthly_forecast_series` | `tests/test_ml.py::test_model_and_horizon_follow_observed_months` | Modelado predictivo (REQ-33) |
| **Intervalos de predicción del 95 %**, que se ensanchan con la distancia y se recortan en cero. | `forecast.monthly_regression` (`get_prediction`, `obs_ci_*`) | `tests/test_ml.py::test_intervals_contain_the_point_and_are_never_negative`, `::test_interval_widens_further_from_the_data` | Modelado predictivo; motivo del uso de `statsmodels` (REQ-30) |
| **Mes parcial**: el último mes incompleto no entra en el ajuste y se proyecta primero. | `forecast._split_partial_month` | `tests/test_ml.py::test_incomplete_last_month_is_left_out_of_the_fit_and_projected_first` | Preprocesamiento |
| **Avisos de extrapolación**: los meses 7 en adelante se marcan `extrapolacion`, y se explica cada límite de la proyección. | `forecast.RELIABLE_MONTHS`, `advertencias` | `tests/test_ml.py::test_points_are_consecutive_months_flagging_extrapolation_from_month_seven` | Limitaciones |
| **Predicción por categoría y por producto** (tarea 034b): `producto` exige `categoria`; si falta, responde 422. | `analytics_routes._require_category`; `analytics_service.monthly_projection` | `tests/test_forecast_api.py::test_forecast_for_a_category_ignores_accents`, `tests/test_products.py` | Vista «Análisis por Categoría» (REQ-52) |
| **Predicción del día siguiente**: modelo diario de media (2 días), de tendencia (3 o más) o de tendencia + día de la semana (14 o más). | `forecast.daily_predictions`; `GET /analytics/predict` | `tests/test_ml.py` | Modelado predictivo |
| **Métricas adicionales**: R², MAPE, WAPE, MASE, mejora frente a la mejor referencia y cobertura del intervalo. | `evaluation.py` · `point_metrics`, `wape`, `mase`, `improvement`, `interval_coverage` | `tests/test_evaluation.py` | OE5; PE2 |
| **Evaluación reproducible**: backtest por horizonte, ETS como comparación, diagnóstico de residuos (Ljung–Box, Breusch–Pagan), niveles a 6, 12 y 18 meses y resultados por categoría. | `backend/scripts/evaluate_models.py` → `docs/evaluacion/` | Reejecución sin diferencias en `git status` | Capítulo 4 |
| **Predicciones guardadas**: `POST /analytics/predicciones` recalcula en el servidor y guarda un lote; `GET /analytics/predicciones` lista los lotes paginados. Ningún GET escribe. | `prediction_service.save_projection`, `list_batches`; `components/forecast/SavedPredictions.tsx` | `tests/test_forecast_api.py::test_saving_stores_one_row_per_projected_month_in_one_batch`, `::test_saved_batches_are_paginated_newest_first` | Persistencia de resultados |
| **Explicaciones comprensibles** de métricas y conceptos (panel «i»). | `lib/metricExplanations.ts`, `lib/conceptExplanations.ts`; `components/ui/InfoHint.tsx`, `components/forecast/ConceptHint.tsx` | `metricExplanations.test.ts`, `conceptExplanations.test.ts`, `InfoHint.test.tsx` | Usabilidad para las PyMEs |

### Reportes

| Función | Evidencia | Pruebas | Dónde encaja en la tesis |
|---|---|---|---|
| **Excel** del historial con neutralización de fórmulas. | `report_service.sales_excel`, `neutralize_formula`; `GET /analytics/export/excel` | `tests/test_reports.py` | Entregables para el usuario |
| **PDF**: historial (`/export/pdf`), proyección anual (`/reporte-predictivo-anual-pdf`), mes futuro frente a su historial (`/reporte-mensual/{mes}`) y proyección por categoría (`/prediccion-categorias/{categoria}`). Usa Matplotlib y FPDF2. | `report_service.history_pdf`, `annual_forecast_pdf`, `monthly_report_pdf`, `category_forecast_pdf`; `pages/ReportsPage.tsx` | `tests/test_reports.py`, `ReportsPage.test.tsx` | Entregables; stack (Matplotlib y FPDF2 no aparecen en la tesis) |

### Usuarios, seguridad y operación

| Función | Evidencia | Pruebas | Dónde encaja en la tesis |
|---|---|---|---|
| **Autenticación JWT** (PyJWT, OAuth2 *password flow*) y roles `Administrador`/`Usuario`. | `api/deps.get_current_user`, `require_role`; `core/security.py` | `tests/test_auth.py`, `tests/test_config_auth.py` | Arquitectura (no descrita) |
| **Aislamiento por usuario (multi-tenant)**: cada consulta de ventas y predicciones se filtra por `id_usuario`. | `analytics_service._user_sales` | `tests/test_isolation.py::PRIVATE_CASES` | Arquitectura / seguridad |
| **Verificación de correo** (tarea 042): enlace de un solo uso válido 24 h y cambio de correo pendiente hasta confirmarlo. | `services/token_service.py` (solo guarda el SHA-256), `email_service.py`; `pages/VerifyEmailPage.tsx` | `tests/test_email_verification.py` | Seguridad |
| **Contraseñas** (tarea 043): bcrypt, cambio con la contraseña actual, recuperación con enlace de 30 min, bloqueo de 15 min tras 10 fallos y revocación de sesiones con `version_token`. | `user_routes.py`; `user_service.py` | `tests/test_passwords.py`, `tests/test_lockout.py` | Seguridad |
| **Endurecimiento de la API** (tareas 039 a 041): *rate limit* por IP, cabeceras de seguridad, CSP, `ProxyHeadersMiddleware`, límite de cuerpo, errores 500 genéricos, logs sin valores locales y 422 sin `input`. | `core/rate_limit.py`, `core/middleware.py`, `main.py`; `docs/security.md`, `docs/seguridad/auditoria-039.md`, `zap-baseline-045.md` | `tests/test_rate_limit.py`, `test_security_headers.py`, `test_errors.py`, `test_logging.py`, `test_field_validation.py`, `test_field_limits_contract.py` | Seguridad / calidad |
| **Perfil de usuario** (`GET/PUT /users/me`) y página de perfil. | `user_routes.update_my_profile`; `pages/ProfilePage.tsx` | `ProfilePage.test.tsx` | Funcionalidad general |
| **Accesibilidad de las gráficas**: `ChartFrame` da a cada gráfica un nombre accesible y una lista de sus valores. | `components/ui/ChartFrame.tsx` | `chartsAccessibility.test.tsx` | Dashboard (REQ-53/62) |
| **CI en cada push**: ruff, mypy, migraciones (`upgrade`/`check`/`downgrade`), suite en SQLite y PostgreSQL 17, pip-audit, npm audit y gitleaks. | `.github/workflows/ci.yml` | — | Metodología / validación |
| **Despliegue en producción**: Vercel (frontend), Railway (API), Neon (PostgreSQL) y Brevo (correo); sondas `/health` y `/health/db`. | `docs/despliegue.md`, `backend/railway.json`, `frontend/vercel.json` | `src/test/csp.test.ts` | PE3 (costos de hosting, P-07) |

## Discrepancias nuevas
Copiadas a `docs/checking/VERIFICACION_TESIS.md`, sección 10:

| REQ | Discrepancia |
|---|---|
| REQ-30 / REQ-05 | El modelo se ajusta con `statsmodels.OLS`, no con `sklearn.linear_model.LinearRegression`. Scikit-Learn solo calcula MAE y RMSE. |
| REQ-32 | Los coeficientes no se registran ni se exponen. |
| REQ-33 / REQ-34 | La estacionalidad solo se usa con 36 meses o más: con el dataset de la tesis (24 meses) el modelo es solo de tendencia. |
| REQ-09 | El repositorio no tiene archivo `LICENSE` y `frontend/package.json` no declara `license`. |
| §7 | No hay un comando único para las cuatro fases del experimento. |

Estado actualizado de filas anteriores: «Frontend» (planning-only) queda resuelta: `AGENTS.md` ya describe la SPA implementada. REQ-50..52 avanza: la gráfica combinada existe y faltan los nombres de las vistas. REQ-09 se reduce: la auditoría Python se completó y el `UNLICENSED` es el propio proyecto.

## Decisiones del autor (2026-11-14)

El autor resolvió todos los pendientes que requerían su decisión. Cada decisión, con su redacción recomendada para la tesis y el archivo y la sección donde va, está en la fila correspondiente de la §10 de `docs/checking/VERIFICACION_TESIS.md`. La §9 no se modificó: cada `P-xx` se cierra cuando la tesis refleje la decisión.

| # | Pendiente | Decisión | Fila de la §10 | ¿Cambia el código? |
|---|---|---|---|---|
| 1 | Biblioteca del modelo (REQ-30, REQ-05) | La tesis dice RLM por OLS con `statsmodels` (intervalos del 95 %); MAE y RMSE con `sklearn.metrics` | REQ-30, REQ-05 (2026-11-14) | No |
| 2 | Características (REQ-33, REQ-34, P-04) | X1 tendencia + X2 estacionalidad desde 36 meses; se retira X3 (*lag*) explicando por qué | REQ-33, REQ-34 (2026-11-14) | No |
| 3 | División de datos (REQ-36, P-03) | Origen móvil y *holdout* cronológico, citando `TimeSeriesSplit` | REQ-36 | No |
| 4 | Baseline y umbral (P-01, P-02) | Gana a la mejor de 3 referencias en el horizonte 1 (WAPE) + escala de Lewis sobre el MAPE | REQ-37, REQ-61, Hipótesis | No |
| 5 | Esquema (REQ-13, REQ-21) | La tesis documenta el esquema real y remite al mapeo de columnas (con los 3 datasets reales) | REQ-13 | No |
| 10 | ETL con Pandas (REQ-04, 22, 24–26, 29) | La tesis describe la arquitectura real (validación por fila → PostgreSQL → Pandas para el modelo, SQL para lo descriptivo) | REQ-24..26, REQ-29 | No |
| 11 | Atípicos (REQ-23, P-08) | Se retira la afirmación, con justificación | REQ-23 | No |
| 12 | Nombres de las vistas (REQ-52) | Se cambia la figura `fig:arquitectura_resultados` con los nombres actuales | REQ-50..52 | No |
| 13 | Asíncrono (REQ-02, REQ-42) | Redacción precisa (ASGI + hilos de trabajo + correo en segundo plano), sin mencionar los *workers* | REQ-42 | Sí: C6 |
| 15 | Licencia (REQ-09) | MIT | REQ-09 (2026-11-14) | Sí: C7 |
| 16a | KPI (REQ-56, P-06) | Ingresos totales, operaciones, ticket promedio (por operación) + crecimiento; venta más alta como indicador complementario | REQ-56 | Sí: C8 |
| 16b | Funciones extra | Solo lo esencial: el mapeo de columnas (con los datasets reales) y los intervalos de predicción | Alcance | No |
| P-05 | Variable Y (REQ-35) | `monto` es la Y principal; `cantidad`, la secundaria | REQ-35 | No |
| P-07 | Costos (PE3) | Tabla con 1, 5 y 10 usuarios, los planes actuales con una nota sobre Vercel Hobby, en USD y MXN | PE3 | Documento: D1 |

## Trabajo pendiente priorizado

### Tareas de código y documentación

**Todas hechas el 2026-11-14** como las tareas 046 a 054 (C7 = 046, C5 = 047, C1 = 048, C3 = 049, C8 = 050, C2 = 051, C6 = 052, C4 = 053, D1 = 054). Ver «Actualización tras las tareas 046 a 054».

No requerían más decisiones. Cada tarea cita su fila de la §10. Al terminar una tarea, cambia el estado de su fila en la §10 a «Resuelta» con la evidencia (archivo, función y prueba), sin borrar filas.

1. **C1. Exponer los coeficientes (REQ-32).** Agregar `coeficientes` (β0…βn con el nombre de cada variable, por objetivo) a `MonthlyForecastResponse` y a `docs/evaluacion/resultados.md` (`scripts/evaluate_models.py`). Prueba de contrato en `tests/test_forecast_api.py`.
2. **C2. Comando único del experimento y métricas fechadas (§7, REQ-61).** Un script que genere el dataset (`generar_ventas.py`, semilla 2026), lo cargue, ejecute la evaluación y escriba `resultados/metricas_AAAA-MM-DD.json` con el commit, la semilla, los parámetros del dataset, el MAE y el RMSE, el baseline y la clasificación de Lewis decididos en el #4.
3. **C3. Prueba `test_serializacion_json` (REQ-60).** Convertir un DataFrame mensual a la respuesta JSON de `/analytics/forecast` y compararlo valor por valor (periodos ISO, montos redondeados a 2 decimales, sin filas perdidas).
4. **C4. E2E con Playwright (REQ-50, 51, 53, 54, 62).** Gráficas con datos de la API, capturas a 375 y 1440 px sin *scroll* horizontal, sin evento `load` al cambiar un filtro y sin errores en la consola.
5. **C5. Generador CSV (REQ-10/11).** Agregar una semilla fija y una fecha de inicio fija a `backend/scripts/generate_dataset.py`, y documentar `generar_ventas.py` como el generador autoritativo.
6. **C6. Medición de concurrencia (REQ-02, REQ-42).** Script versionado en `backend/scripts/` que, con `uvicorn` y PostgreSQL local, mida el p50 y el p95 de `GET /analytics/stats` en reposo y durante la carga del XLSX completo (por otro usuario), y registre el resultado en `docs/evaluacion/`.
7. **C7. Licencia MIT (REQ-09).** Agregar `LICENSE` (MIT, con el nombre del autor y 2026) en la raíz y `"license": "MIT"` en `frontend/package.json`. Verificar que `npx license-checker --production --summary` ya no muestre `UNLICENSED`.
8. **C8. Tarjeta de crecimiento (REQ-56).** Backend: en `/analytics/stats`, la variación % de los ingresos del último mes completo del rango filtrado frente al mes anterior y frente al mismo mes del año anterior cuando exista; `null` sin dos meses completos. Frontend: una `MetricCard` en `DashboardPage.tsx` que muestre «Sin datos suficientes» cuando el valor es `null`. Pruebas en ambos lados.
9. **D1. Comparación de costos (PE3, P-07).** Crear `docs/costos/comparacion.md` según la fila PE3 de la §10. Requiere buscar los precios oficiales actuales en internet y citar la URL y la fecha de cada precio.

### Cambios en la tesis (para el autor)

Están desarrollados, con la redacción propuesta y los datos finales, en `docs/reportes/correcciones_tesis_2026-11-14.md`. El código no cambia en estos puntos. La redacción recomendada está en la fila de la §10 que se indica.

| Archivo › Sección de la tesis | Qué cambiar | Fila de la §10 |
|---|---|---|
| `metodos.tex › Scikit-Learn`, `› Modelado Predictivo`; stack en `intro.tex` y `arte.tex` | `statsmodels.OLS` para el ajuste; `sklearn.metrics` para MAE y RMSE | REQ-30, REQ-05 |
| `metodos.tex › Modelado Predictivo`; `arte.tex › 2.1.3.4` | X1, X2 desde 36 meses, sin *lag*; intervalos del 95 % | REQ-33, REQ-34; Alcance |
| `metodos.tex › Modelado Predictivo`, `› Definición del Experimento` | Origen móvil y *holdout* cronológico | REQ-36 |
| `metodos.tex › Modelado Predictivo` | `monto` como Y principal; `cantidad`, secundaria | REQ-35 |
| `intro.tex › Hipótesis`, `› Objetivos › Específico 5`; `metodos.tex › Definición del Experimento` | Baseline (mejor de 3 referencias, horizonte 1) y escala de Lewis | REQ-37, REQ-61, Hipótesis |
| `metodos.tex › Selección y Estructura de Datos` | Esquema real y referencia al mapeo | REQ-13 |
| `metodos.tex › Pandas (Ingeniería de Datos y Tubería ETL)`, `› Preprocesamiento…` | Mapeo de columnas con los datasets reales; ETL real; sin atípicos | REQ-13, REQ-24..26, REQ-29, REQ-23 |
| `intro.tex › Justificación`; `arte.tex › 2.1.4`; `metodos.tex › Validación e Integración del Sistema` | Redacción precisa de lo asíncrono | REQ-42 |
| Figura `fig:arquitectura_resultados` | Nombres actuales de las vistas | REQ-50..52 |
| `intro.tex › Objetivos › Específico 1`; diseño del dashboard | Lista de KPI | REQ-56 |
| Capítulo que responde la PE3 | Tabla de costos (después de D1) | PE3 |

Cuando la tesis refleje un cambio, actualiza en `VERIFICACION_TESIS.md` la afirmación del REQ correspondiente (§1 a §7), cierra su fila en la §10 y el `P-xx` de la §9 si aplica (regla de la §12).

## Comandos ejecutados

Backend (venv con Python 3.14.4; se instalaron `requirements.txt`, `requirements-dev.txt` y `pip-licenses`):

- `pytest --cov=app --cov-report=term -q` → `484 passed, 213 warnings in 261.85s`; cobertura TOTAL 96 % (2,277 sentencias, 83 sin cubrir).
- `ruff check app/` → `All checks passed!`
- `mypy` → `Success: no issues found in 32 source files`
- `alembic current` → `0008_contrasenas_bloqueo (head)`; `alembic check` → `No new upgrade operations detected.` (PostgreSQL local)
- `pip-audit -r requirements.txt --ignore-vuln PYSEC-2025-183` → `No known vulnerabilities found`
- `pip-licenses --summary` y `pip-licenses --packages <requirements.txt>` (tablas arriba)
- `python scripts/evaluate_models.py` → exit 0; `git status --porcelain docs/evaluacion` sin cambios
- Script de latencia y script de coeficientes en el *scratchpad* (no versionados)

Frontend (Node 24):

- `npm run lint` → exit 0
- `npm run typecheck` → exit 0
- `npm test -- --run` → `Test Files 43 passed (43)`, `Tests 268 passed (268)`
- `npm run build` → `built in 4.08s` (aviso de tamaño de *chunk*, sin errores)
- `npx license-checker --summary` y `--production --summary` (resultados en REQ-09)
- `npm audit --omit=dev --audit-level=high` → `found 0 vulnerabilities`

No ejecutados por decisión del autor: capturas responsive y E2E en el navegador (REQ-53, REQ-62).

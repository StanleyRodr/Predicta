# Reporte de verificación — 2026-11-08
Commit: `7d2bfe5d8d4bb2efad831ed718ce6d5697a55e6b`   Semilla del dataset: `2026` en el generador XLSX; sin semilla en el generador CSV alternativo   Registros: `28.667`

## Resumen
CUMPLE: 15 | NO CUMPLE: 14 | PARCIAL: 16 | NO VERIFICABLE: 1 | PENDIENTE: 1

## Detalle
| REQ | Estado | Evidencia (archivo/prueba/salida) | Nota |
|---|---|---|---|
| REQ-01 | CUMPLE | `backend/requirements.txt` · `fastapi`; `backend/app/main.py` · `app`; `backend/tests/test_auth.py` | FastAPI expone rutas HTTP REST. |
| REQ-02 | PARCIAL | `backend/app/main.py` · `lifespan`; `backend/app/api/etl_routes.py` · `upload_ventas`; `backend/app/api/analytics_routes.py` · `predict_next_day` | `lifespan` es async; ETL y modelo son funciones síncronas. ETL corre en threadpool de FastAPI. |
| REQ-03 | CUMPLE | `backend/requirements.txt` · `psycopg2-binary`; `backend/app/core/database.py`; `alembic check` | PostgreSQL configurado; no hay operaciones Alembic pendientes. |
| REQ-04 | PARCIAL | `backend/app/services/etl_service.py` · `_parse_xlsx`, `read_rows`; `backend/app/ml_models/forecast.py` · `monthly_aggregates` | Pandas sí se usa, pero no están todas las transformaciones REQ-20..27. |
| REQ-05 | CUMPLE | `backend/requirements.txt` · `scikit-learn`; `backend/app/ml_models/forecast.py` · `LinearRegression` | Scikit-Learn se usa en entrenamiento. |
| REQ-06 | CUMPLE | `frontend/package.json` · `react`; `frontend/src/App.tsx` · `App` | React implementado; contradice la declaración planning-only de `AGENTS.md`. |
| REQ-07 | PARCIAL | `frontend/vite.config.ts` · `tailwindcss()`; `frontend/src/index.css` · `@import "tailwindcss"` | Tailwind funciona con plugin, pero no figura como dependencia directa. |
| REQ-08 | CUMPLE | `frontend/package.json` · `chart.js`, `react-chartjs-2`; `frontend/src/components/analytics/TemporalLineChart.tsx`; `CategoryBarChart.tsx` | Chart.js renderiza gráfica lineal y barras. |
| REQ-09 | NO VERIFICABLE | `LICENSE` · MIT; `pip-licenses --format=markdown`; `npm exec license-checker -- --summary` | `pip-licenses` no está instalado. NPM reporta 1 dependencia `UNLICENSED`; no se pudo completar la auditoría. |
| REQ-10 | CUMPLE | `DatosDePrueba/ventas_fabricadas/generar_ventas.py` · `main`; XLSX existente | Dataset sintético generado en Python. |
| REQ-11 | PARCIAL | `generar_ventas.py` · `SEED = 2026`; `backend/scripts/generate_dataset.py` | Un generador es reproducible; el generador CSV alternativo usa aleatoriedad sin semilla. |
| REQ-12 | CUMPLE | `backend/app/services/etl_service.py` · `load_sales`; `backend/app/api/etl_routes.py` · `upload_ventas`; `backend/tests/test_etl.py::test_upload_csv_returns_success` | Se cargan archivos CSV/XLSX a PostgreSQL/SQLAlchemy; el test usa SQLite. |
| REQ-13 | NO CUMPLE | `backend/app/models/models.py` · `Venta`; `generar_ventas.py` | Usa `id_venta`, `fecha_venta`, `monto`; faltan `precio_unitario` y `total`. |
| REQ-20 | CUMPLE | `backend/app/services/etl_service.py` · `_parse_csv`, `_parse_xlsx`, `read_rows`; `backend/tests/test_etl.py::test_upload_csv_returns_success` | Los archivos se convierten y procesan mediante estructuras tabulares. |
| REQ-21 | NO CUMPLE | `etl_service.py` · `REQUIRED_COLUMNS`; `generar_ventas.py` | Encabezados reales: `producto,monto,cantidad,categoria,fecha`, no los de REQ-13. |
| REQ-22 | NO CUMPLE | `etl_service.py` · `build_venta`, `_is_missing`; `backend/tests/test_etl.py::test_upload_rejects_invalid_rows_without_silent_defaults` | Rechaza filas inválidas; no elimina NaN mediante limpieza de DataFrame. |
| REQ-23 | NO CUMPLE | Búsqueda en `backend/app/**/*.py` | No existe filtro IQR, z-score ni máscara de outliers. |
| REQ-24 | NO CUMPLE | `etl_service.py` · `_parse_date`; `models.py` · `fecha_venta: Date` | Convierte a `datetime.date`, no a `datetime64[ns]` en el DataFrame ETL. |
| REQ-25 | NO CUMPLE | `forecast.py` · `build_seasonal_features` | Usa mes/weekday para ML, pero no genera las tres columnas ETL requeridas. |
| REQ-26 | NO CUMPLE | `forecast.py` · `monthly_aggregates`, `daily_aggregates`; `analytics_service.py` | Hay agregaciones, pero no `groupby` ETL por día y categoría sumando `total`. |
| REQ-27 | PARCIAL | `etl_service.py` · `build_venta`; `category_service.py` · `normalize_category` | Categorías se normalizan; producto solo se recorta, sin normalización completa. |
| REQ-28 | PARCIAL | `generar_ventas.py` · `sort_values("fecha")`; `forecast.py` · matrices numéricas | Dataset/features cumplen parcialmente; no existe una salida homogénea común del ETL. |
| REQ-29 | NO CUMPLE | `analytics_service.py` · `daily_revenue`, `daily_sales`; `forecast.py` · `monthly_aggregates` | Consultas usan SQL y ML reconstruye/agrega sus propios datos. |
| REQ-30 | CUMPLE | `forecast.py` · `LinearRegression`; `backend/tests/test_ml.py` | Regresión lineal; no se encontró Random Forest en producción. |
| REQ-31 | CUMPLE | `forecast.py` · `LinearRegression().fit` | `LinearRegression` implementa OLS. |
| REQ-32 | PARCIAL | `forecast.py` · `_fit_and_evaluate`; `analytics_service.py` · `/analytics/predict` | Intercepto/coefs existen internamente, pero no se registran ni exponen. |
| REQ-33 | NO CUMPLE | `forecast.py` · `build_seasonal_features`, `build_weekly_features` | Usa tendencia y dummies; falta el lag y hay características adicionales. |
| REQ-34 | CUMPLE | `forecast.py` · `build_seasonal_features` | El mes se codifica mediante variables one-hot. |
| REQ-35 | CUMPLE | `forecast.py` · `monthly_predictions`, `daily_predictions`; `analytics_service.py` | Predice `monto` y `cantidad`, satisfaciendo la alternativa de la tesis. |
| REQ-36 | NO CUMPLE | `forecast.py` · `_fit_and_evaluate` | No usa `train_test_split`; reserva el último 20% temporal. |
| REQ-37 | PARCIAL | `forecast.py` · `_metrics`; `backend/tests/test_ml.py::test_daily_prediction_returns_metrics_and_non_negative_interval` | Calcula RMSE/R²/MAPE sobre holdout, no MAE ni `sklearn.metrics`. |
| REQ-38 | CUMPLE | `backend/app/api/analytics_routes.py` · `predict_next_day`; `analytics_service.py` | El endpoint ajusta automáticamente el modelo. |
| REQ-40 | PARCIAL | `analytics_routes.py` · `temporal_stats`, `predict_next_day`; `frontend/src/api/analytics.ts` | Hay JSON estructurado, pero no serialización explícita de DataFrame y una fecha histórica incluye hora. |
| REQ-41 | PARCIAL | `analytics_routes.py` · `/analytics/stats/temporal`, `/analytics/predict`; `PredictionsPage.tsx` | Histórico y proyección están en endpoints/vistas separadas, no en un vector combinado. |
| REQ-42 | NO CUMPLE | `etl_routes.py` · `upload_ventas`; `analytics_routes.py` · `predict_next_day` | ETL y ajuste son síncronos. |
| REQ-43 | PARCIAL | No existe benchmark p50/p95 | `SIN UMBRAL`: no se aprueba/reprueba; la latencia no está medida. |
| REQ-44 | CUMPLE | `README.md` · arquitectura; `frontend/src/api/http.ts`; `backend/app/main.py` | Frontend y backend separados por HTTP/JSON. |
| REQ-50 | PARCIAL | `TemporalLineChart.tsx`; `DashboardPage.tsx`; `chartFormats.test.tsx` | Existe línea histórica; no hay E2E ni gráfica única histórico+proyección. |
| REQ-51 | PARCIAL | `CategoryBarChart.tsx`; `analytics.test.tsx` | Existe gráfica de barras; solo hay tests unitarios, no E2E. |
| REQ-52 | NO CUMPLE | `frontend/src/pages/DashboardPage.tsx`; `frontend/src/App.tsx` | No aparecen las vistas exactas requeridas. |
| REQ-53 | NO VERIFICABLE | No hay Playwright ni capturas responsive | No se verificaron anchos 375/1440 ni scroll horizontal. |
| REQ-54 | PARCIAL | `DashboardPage.tsx` · `useQuery`; `analytics.test.tsx` | React Query actualiza sin navegación; falta E2E que demuestre ausencia de `load`. |
| REQ-55 | CUMPLE | `DashboardPage.tsx` · `MetricCard`, `TemporalLineChart`, `CategoryBarChart`; `PredictionsPage.tsx` | KPIs descriptivos y proyección predictiva visibles. |
| REQ-56 | PENDIENTE DE DEFINIR | `docs/checking/VERIFICACION_TESIS.md` · P-06; `DashboardPage.tsx` | La tesis no define la lista oficial de KPIs. |
| REQ-60 | NO CUMPLE | `backend/tests`; `frontend/src/api/*.test.ts` | No existe `test_serializacion_json` ni prueba explícita DataFrame→JSON sin pérdida. |
| REQ-61 | PARCIAL | `forecast.py` · `_metrics`; `analytics_service.py` · `metricas`; `docs/ml-models.md` | Métricas se devuelven por API, pero no se registran en archivo fechado y no hay umbral. |
| REQ-62 | NO CUMPLE | `chartFormats.test.tsx`, `analytics.test.tsx` | Hay tests unitarios de formato, no E2E Chart.js ni prueba de consola/sincronización. |

## Métricas del modelo (para el Capítulo 4)
MAE: no calculado por el sistema | RMSE monto: `18986.2150` | Baseline MAE: no definido

Coeficientes: existen internamente, pero no se registran ni exponen en la API.

Valores adicionales sobre el XLSX mediante `monthly_predictions`:

- Monto: MAPE `15.6198`, R² `-8.0700`.
- Cantidad: RMSE `560.9945`, MAPE `18.4694`, R² `-9.7671`.
- Filas mensuales: `24`; fecha proyectada: `2026-11-30`.

## Discrepancias nuevas
Se copiaron a `docs/checking/VERIFICACION_TESIS.md`, sección 10:

| REQ | Discrepancia |
|---|---|
| REQ-13 | El esquema del sistema no coincide con el esquema exacto de la tesis. |
| REQ-23 | No existe filtro de outliers. |
| REQ-24..26 | No existe el pipeline ETL único descrito. |
| REQ-29 | Consultas y ML no consumen la misma salida ETL. |
| REQ-33 | Falta el lag y las características no coinciden. |
| REQ-36 | Se usa holdout temporal, no `train_test_split`. |
| REQ-37 | Falta MAE y se usan métricas/cálculo distintos. |
| REQ-42 | ETL y modelo son síncronos. |
| REQ-50..52 | Faltan la vista combinada y los nombres exactos. |
| REQ-53, REQ-62 | No hay evidencia E2E ni capturas responsive. |
| REQ-61 | No existe archivo fechado de métricas con metadatos. |
| REQ-09 | Auditoría completa de licencias no verificable; aparece `UNLICENSED`. |
| REQ-10/11 | Hay dos generadores y uno no fija semilla. |
| Frontend | La documentación declara planning-only aunque hay implementación React funcional. |

## Comandos ejecutados
`pytest -p no:cacheprovider` (bloqueado en colección por `ModuleNotFoundError: No module named 'pypdf'`); `ruff check app/` (correcto); `mypy app/` (correcto); `npm test -- --run` (20 archivos, 48 pruebas correctas); `npm run typecheck` (correcto); `npm run build` (correcto); `alembic check` (sin operaciones pendientes); inspección Pandas y ejecución de `monthly_predictions`; `pip-licenses --format=markdown` (no instalado); `npm exec --yes license-checker -- --summary` (reportó `MIT 248`, `Apache-2.0 19`, `UNLICENSED 1`); `git diff --check`.

# Feedback 01 — Revisión general de Predicta

**Fecha:** 2026-11-02
**Base:** `main` en `367f878` (más cambios locales sin commitear en `backend/alembic/env.py`, `backend/alembic/versions/0002_schema_cantidad_predicciones.py` y `backend/requirements.txt`)
**Alcance:** backend, modelo ML, frontend, pruebas, herramientas e higiene del repositorio.
**Estado:** pendiente de autorización.

> Este documento solo describe los hallazgos y la corrección propuesta.
> Cuando autorices los puntos, cada uno pasará a una tarea en `TASKS.md`
> con su plan en `plans/NNN-*.md`. Ahí irá la justificación: por qué hacerlo,
> riesgos de hacerlo y de no hacerlo, y qué te conviene.

**Leyenda de verificación**

- ✅ Confirmado: revisé el código y el problema existe tal como se describe.
- 🔎 Reportado: lo encontró la exploración automática y no lo revisé línea por línea; se confirma al planificar la tarea.

---

## Resumen

El proyecto está en buen estado para una tesis:

- Aislamiento por usuario consistente en las consultas de `Venta`.
- Secretos obligatorios sin valores por defecto.
- Errores 500 genéricos.
- ETL con validación por fila y transacción única.
- El modelo se evalúa con un holdout temporal honesto.
- Frontend con TypeScript `strict`.
- Flujo de trabajo documentado (`TASKS.md` + `plans/`), con las 14 tareas hechas.

Los problemas se concentran en cuatro frentes:

1. **Robustez del backend:** concurrencia, límites de entrada y migraciones.
2. **Rigor estadístico del modelo:** lo que más pesa en la defensa de la tesis.
3. **Automatización:** no hay CI.
4. **Detalles del frontend:** caché entre usuarios y errores de descarga.

| Prioridad | Cantidad |
|---|---|
| Alta | 7 |
| Media | 13 |
| ML (tesis) | 7 |
| Baja | 7 |

---

## 1. Prioridad alta

### F-01 — La carga de archivos bloquea el servidor ✅

- **Dónde:** `backend/app/api/etl_routes.py:153-154`
- **Problema:** `upload_ventas` está declarado como `async def`, pero adentro hace trabajo bloqueante: sesión síncrona de SQLAlchemy, `pd.read_excel`, el bucle por fila y `db.commit()`. FastAPI corre las funciones `async` directamente en el event loop.
- **Efecto:** mientras se procesa un archivo grande (por ejemplo, las 28.667 filas de `DatosDePrueba`), el servidor no atiende ninguna otra petición: login, dashboard ni health checks.
- **Corrección propuesta:** declararlo como `def`, para que FastAPI lo ejecute en el threadpool, y leer el archivo con `file.file.read()`. Otra opción es mantener `async` y delegar el parseo a `run_in_threadpool`.
- **Verificación sugerida:** test que suba un archivo mientras otra petición a `/health` responde; la suite ETL debe seguir pasando.

### F-02 — El límite de tamaño se valida después de leer todo el archivo ✅

- **Dónde:** `backend/app/api/etl_routes.py:174-179`
- **Problema:** `await file.read()` carga el archivo completo en memoria y recién después compara con `MAX_UPLOAD_BYTES` (25 MB). Tampoco hay un límite de filas, y un `.xlsx` es un ZIP que puede descomprimirse a un tamaño mucho mayor (zip bomb).
- **Efecto:** un archivo enorme puede agotar la memoria del proceso antes de ser rechazado.
- **Corrección propuesta:**
  - Leer en bloques y abortar con 413 al superar el límite.
  - Agregar un `MAX_ROWS` configurable.
  - Para XLSX, revisar el tamaño descomprimido declarado en el ZIP antes de pasarlo a pandas.
- **Verificación sugerida:** tests de archivo sobredimensionado y de exceso de filas.

### F-03 — Un monto fuera de rango hace fallar el archivo completo ✅

- **Dónde:** `backend/app/api/etl_routes.py:42-54` (`_parse_amount`) y `:217-224` (commit)
- **Problema:** la columna `monto` es `DECIMAL(10,2)`, cuyo máximo es 99.999.999,99, pero el parser no valida límites ni signo.
  - Un monto como `1e9` pasa la validación de la fila y rompe en el `commit`: todo el archivo termina en un 500 genérico y no se sabe qué fila falló.
  - Se aceptan montos negativos y en cero. La cantidad sí rechaza negativos (`:62-63`).
- **Corrección propuesta:** validar por fila un rango `0 < monto ≤ 99.999.999,99` (y lo mismo para `cantidad`) y reportar la fila en `errores`. Hay que decidir si se permiten devoluciones (montos negativos); la recomendación es que no, por ahora.
- **Verificación sugerida:** tests con monto negativo, cero y fuera de rango; el resto del archivo debe cargarse.

### F-04 — Los gráficos del PDF no son seguros entre hilos ✅

- **Dónde:** `backend/app/api/analytics_routes.py:421-422, 505-507, 600, 679-681`
- **Problema:** las figuras se crean con `plt.subplots` (`:314`), pero después se usa `plt.xticks` y `plt.tight_layout`. Esas funciones actúan sobre la "figura actual" global de pyplot, y los endpoints síncronos corren en varios hilos a la vez.
- **Efecto:** con dos reportes generándose al mismo tiempo, una petición puede modificar o romper el gráfico de la otra. El error es intermitente y difícil de reproducir.
- **Corrección propuesta:** usar solo la API orientada a objetos (`ax.tick_params`, `fig.tight_layout()`) o `matplotlib.figure.Figure` sin pyplot. Fijar el backend `Agg`.
- **Verificación sugerida:** grep sin `plt.` fuera de la creación y el cierre de figuras; los tests de exportación deben pasar.

### F-05 — No hay integración continua (CI) ✅

- **Dónde:** `.github/` solo contiene `PULL_REQUEST_TEMPLATE.md`. Ya figura como pospuesto en `TASKS.md:216`.
- **Problema:** lint, tipos, tests y build dependen de que alguien los ejecute a mano.
- **Corrección propuesta:** un workflow de GitHub Actions con dos jobs:
  - **Backend:** `ruff check`, `mypy`, `pytest --cov`, más un servicio PostgreSQL que ejecute `alembic upgrade head` y `alembic check` (ver F-06).
  - **Frontend:** `npm ci`, `typecheck`, `test --run` y `build`.
- **Verificación sugerida:** el workflow pasa en verde en una rama de prueba.

### F-06 — Las migraciones de Alembic no coinciden con los modelos ✅

- **Dónde:** `backend/app/models/models.py:80, 89, 96-97, 110` frente a `backend/alembic/versions/0001_initial.py:66-69, 90`
- **Problema:**
  - **Nombres de índices distintos:** el modelo usa `idx_ventas_usuario_fecha` e `idx_ventas_categoria`; la migración crea `ix_ventas_usuario_fecha` e `ix_ventas_categoria`.
  - **Nulabilidad distinta:** en el modelo, `predicciones.id_usuario` es `Mapped[int]`, que implica `NOT NULL`; en la migración es `nullable=True`. Además no tiene índice.
  - **Índices redundantes:** `index=True` en `id_usuario` y en `fecha_venta` duplican lo que ya cubre el índice compuesto.
  - Los tests usan SQLite con `create_all`, así que nunca validan las migraciones reales.
- **Efecto:** el próximo `alembic revision --autogenerate` generará cambios inesperados, y la base de producción no coincide con lo que el código asume.
- **Nota:** hay cambios locales sin commitear en `0002_schema_cantidad_predicciones.py` y `alembic/env.py`. Hay que revisarlos antes de tocar las migraciones.
- **Corrección propuesta:** una migración `0003` que alinee los nombres, la nulabilidad (tras limpiar las filas con `NULL`), el índice de `predicciones.id_usuario` y los índices redundantes, junto con un `alembic check` en CI.
- **Verificación sugerida:** `alembic upgrade head`, `alembic check` sin diferencias y `alembic downgrade -1`, en PostgreSQL.

### F-07 — Datos de un usuario pueden mostrarse a otro en el mismo navegador ✅

- **Dónde:** `frontend/src/components/layout/AppShell.tsx:43-47`, `frontend/src/pages/PredictionsPage.tsx:13`, `frontend/src/pages/UploadPage.tsx:19`
- **Problema:** al cerrar sesión solo se llama a `clearSession()`; la caché de TanStack Query no se vacía. Las claves `["forecast"]` y `["sales-history", page]` no incluyen el id del usuario (el dashboard sí lo incluye).
- **Efecto:** si un usuario cierra sesión y otro entra en la misma pestaña, puede ver la predicción y el historial del anterior. La predicción además tiene `staleTime: Infinity`, así que nunca se refresca sola. Es una fuga de datos entre usuarios en el cliente.
- **Corrección propuesta:** llamar a `queryClient.clear()` al cerrar sesión, tanto en el logout manual como en el evento 401, e incluir `userId` en todas las claves.
- **Verificación sugerida:** test RTL: login A → ver predicción → logout → login B → no aparece el dato de A.

---

## 2. Prioridad media

### F-08 — `/predict` no sigue las convenciones HTTP ✅

- **Dónde:** `backend/app/api/analytics_routes.py:224, 242-243, 257-271`
- **Problema:**
  - Cuando no hay datos suficientes responde **200** con `{"error": ...}` en lugar de un 4xx, y el frontend tiene que tratarlo como caso especial (`frontend/src/types/forecast.ts`).
  - Es un **GET que escribe** un registro `Prediccion` en cada llamada: cada refetch o recarga crea filas nuevas.
  - Ningún endpoint lee la tabla `predicciones`, así que solo se escribe y nunca se consulta.
- **Corrección propuesta:** pasar a `POST /analytics/predict`, devolver 422 con `detail` cuando no hay datos suficientes, y agregar `GET /analytics/predicciones` para el historial, o dejar de persistir. Es una decisión de diseño que te toca a ti.

### F-09 — `analytics_routes.py` es demasiado grande y mezcla responsabilidades 🔎

- **Dónde:** `backend/app/api/analytics_routes.py` tiene 712 líneas; el bloque de exportaciones y PDF está en `:296-712`. El parseo de la ETL está en `etl_routes.py:32-150`.
- **Problema:** las rutas contienen lógica de negocio, generación de PDF y Excel, y gráficos. Solo `user_service` sigue el patrón de servicios.
- **Corrección propuesta:** extraer `services/report_service.py` (PDF, Excel y gráficos), `services/analytics_service.py` (agregaciones) y `services/etl_service.py` (parseo y validación). Las rutas quedan como capa HTTP delgada.

### F-10 — Los endpoints no declaran esquemas de respuesta 🔎

- **Dónde:** rutas de analytics y ETL, que devuelven `-> dict`.
- **Problema:** OpenAPI no documenta qué devuelve cada endpoint, y los tipos de `frontend/src/types/*` se mantienen a mano y pueden desincronizarse.
- **Corrección propuesta:** modelos Pydantic de respuesta y `response_model` en cada ruta. Opcionalmente, generar los tipos TypeScript desde OpenAPI.

### F-11 — La ETL expone texto de excepciones y numera mal las filas ✅

- **Dónde:** `backend/app/api/etl_routes.py:199, 203, 215`
- **Problema:**
  - `:199` incluye `{exc}` en el 400. Si la excepción viene de pandas, openpyxl u `OSError`, puede llevar rutas o detalles internos. Contradice la regla de `CLAUDE.md` de nunca poner `str(exc)` en una respuesta.
  - `:215` incluye `str(exc)` de un `TypeError`, que no es un mensaje controlado.
  - `:203` numera desde la fila 2, lo que es correcto para CSV y XLSX con encabezado, pero no para SQL.
- **Corrección propuesta:** usar una excepción propia (`RowValidationError`) con mensajes en español controlados, devolver un mensaje fijo para los errores de lectura y llevar la numeración según el formato.

### F-12 — El parser SQL es frágil ✅

- **Dónde:** `backend/app/api/etl_routes.py:115-132` y `:67-71, 197`
- **Problema:**
  - Separa los valores con `,`, así que `'Galletas, surtidas'` rompe la fila.
  - Ignora los nombres de columnas del `INSERT` y asume el orden.
  - No lee `cantidad`.
  - Si falta la fecha, usa **la fecha de hoy**, lo que contradice la regla de la ETL de no fabricar fechas.
- **Corrección propuesta:** parsear los valores respetando las comillas (por ejemplo, con `csv.reader` sobre la tupla), mapear por nombre de columna cuando el `INSERT` las declare, leer `cantidad` y rechazar las filas sin fecha.

### F-13 — Subir dos veces el mismo archivo duplica todos los datos 🔎

- **Problema:** no existe ninguna deduplicación, así que una segunda carga duplica todas las métricas y sesga el modelo.
- **Corrección propuesta:** guardar un hash (SHA-256) por archivo cargado y avisar o rechazar si ya existe. Alternativa más simple: solo advertir en la respuesta.

### F-14 — Exportaciones y reportes cargan tablas completas en memoria 🔎

- **Dónde:** `backend/app/api/analytics_routes.py:351-355, 391-395, 463-467`, y `backend/app/ml_models/forecast.py:97-119`
- **Problema:**
  - El PDF imprime una fila por venta sin límite (28 mil filas significan cientos de páginas).
  - Las agregaciones se hacen en pandas en lugar de con `GROUP BY` en SQL.
  - Los PNG temporales solo se borran si todo sale bien.
- **Corrección propuesta:**
  - Agregar en SQL.
  - Que el PDF muestre resúmenes y el top N, no el detalle completo.
  - Generar las imágenes en `BytesIO` (fpdf2 las acepta) para eliminar los temporales.

### F-15 — CORS demasiado permisivo y configuración dispersa ✅

- **Dónde:** `backend/app/main.py:72-83`
- **Problema:**
  - El valor por defecto es `CORS_ORIGINS="*"`, combinado con `allow_credentials=True` y métodos y headers `*`.
  - `os.getenv` y `load_dotenv` están repartidos entre `main.py`, `database.py` y `security.py`.
- **Corrección propuesta:** centralizar en `app/core/config.py` con `pydantic-settings`, usar por defecto el origen de Vite y rechazar `*` fuera del entorno de desarrollo.

### F-16 — Detalles de autenticación ✅ / 🔎

- `passlib 1.7.4` ya no se mantiene. Hoy está fijado con `bcrypt==4.0.1` para que funcione (`backend/requirements.txt`). ✅
- bcrypt ignora todo lo que pasa de 72 bytes en una contraseña y el esquema no valida un máximo. 🔎
- `DEFAULT_USER_ROLE_ID = 2` (`backend/app/services/user_service.py:13`) depende del orden en que se insertaron los roles en la base. ✅
- La verificación de duplicados en registro y edición de perfil consulta y después inserta: si dos peticiones llegan a la vez, salta un `IntegrityError` que termina en 500. 🔎
- El header `Content-Disposition` usa el `nombre_usuario` sin sanitizar, así que los caracteres no ASCII lo rompen. 🔎
- **Corrección propuesta:** usar `bcrypt` directo o `pwdlib`, poner un máximo de 72 bytes, buscar el rol por nombre, capturar el `IntegrityError` y devolver 400, y usar `filename*=UTF-8''...` en el header.

### F-17 — Los tests tienen huecos ✅ / 🔎

- `test_clear_history_deletes_only_current_user_sales` (`backend/tests/test_etl.py:164`) **no crea un segundo usuario**, así que no prueba el aislamiento que promete su nombre. ✅
- Faltan tests de aislamiento entre dos usuarios en analytics y exportaciones. 🔎
- No hay tests para `/reporte-mensual`, `/prediccion-categorias`, la paginación de `/ventas`, archivos sobredimensionados ni carga SQL. 🔎
- El parche `isinstance(r.fecha, str)` en `analytics_routes.py:246` existe porque SQLite devuelve las fechas como texto: los tests no corren sobre el mismo motor que producción. ✅
- **Corrección propuesta:** un fixture `second_user`, tests de aislamiento parametrizados por endpoint y un job de CI con PostgreSQL.

### F-18 — Errores y descargas en el frontend ✅

- **Dónde:** `frontend/src/api/reports.ts:14-30`, `frontend/src/api/http.ts:6`, `frontend/src/pages/UploadPage.tsx:23-27`
- **Problema:**
  - Con `responseType: "blob"`, el cuerpo de un error también llega como Blob. `reportErrorMessage` lee `.detail` directamente y nunca encuentra el mensaje del backend (por ejemplo, "Muestreo insuficiente").
  - `URL.revokeObjectURL` se ejecuta justo después de `click()`, lo que puede cancelar la descarga en Firefox y Safari.
  - El timeout global de 15 s también aplica a la carga de archivos de hasta 25 MB y a la generación de PDF.
  - Después de cargar un archivo no se invalidan las claves `["analytics", ...]`, así que el dashboard muestra datos viejos.
- **Corrección propuesta:**
  - Parsear el Blob con `await data.text()` y `JSON.parse`, y reutilizar `getApiErrorMessage`.
  - Revocar la URL con `setTimeout`.
  - Usar timeouts por petición (por ejemplo, 120 s para cargas y reportes).
  - Invalidar `analytics` y `forecast` después de una carga o una purga.

### F-19 — Accesibilidad 🔎

- `frontend/src/components/ui/Modal.tsx` no cierra con Escape, no mantiene el foco dentro del modal ni lo restaura al cerrar, y tiene el `id="modal-title"` fijo, lo que genera ids duplicados si hay dos modales.
- Los gráficos usan `aria-label` en un `div` sin `role="img"` y sin una tabla alternativa con los datos.
- El menú móvil usa los textos "MENU" y "X" como etiquetas.
- **Corrección propuesta:** foco atrapado y restaurado, cierre con Escape, `useId()`, `role="img"` con una tabla oculta para lectores de pantalla, y etiquetas accesibles.

### F-20 — Linting configurado a medias 🔎

- Los paquetes de ESLint están instalados, pero no hay `eslint.config.js` ni script `lint`.
- ruff y mypy corren sin configuración, así que el aviso `B008` de FastAPI sigue abierto desde `TASKS.md:57`.
- `pre-commit` está en `requirements-dev.txt`, pero no existe `.pre-commit-config.yaml`.
- **Corrección propuesta:** un `pyproject.toml` con la configuración de ruff y mypy (`B008` ignorado para `Depends`), `eslint.config.js` con un script `lint`, y un `.pre-commit-config.yaml`.

---

## 3. Modelo de ML — rigor para la tesis

Contexto: `backend/app/ml_models/forecast.py`. Es una `LinearRegression` con intercepto, tendencia y variables dummy (12 de mes o 7 de día de semana), con objetivos separados para `monto` y `cantidad`. Se evalúa con un holdout del 20% final y después se reentrena con todos los datos. El intervalo es ±1,96·σ de los residuos.

### F-21 — La tendencia mensual cuenta filas, no meses transcurridos ✅ (error)

- **Dónde:** `forecast.py:165, 170, 194, 198`
- **Problema:** la tendencia se calcula con `np.arange(len(monthly))`. Como los meses sin datos se omiten (lo cual es correcto), si falta febrero, enero → marzo cuenta como un solo paso. La pendiente queda mal estimada y las proyecciones futuras se desplazan. El modelo diario sí usa el desfase real en días.
- **Corrección propuesta:** usar `meses_transcurridos = (año − año₀)·12 + (mes − mes₀)`.

### F-22 — Las dummies son colineales y sobra un parámetro para muestras chicas 🔎

- **Problema:** las 12 dummies junto con el intercepto son perfectamente colineales (la trampa de las variables dummy). El modelo mensual queda con 14 parámetros, así que con menos de unos 14 meses ajusta los datos sin error. Los residuos valen 0 y el código usa `std(y)` como reemplazo (`:69-72`), lo que vuelve arbitrario el intervalo.
- **Corrección propuesta:** quitar una dummy de referencia (`drop_first`), fijar un mínimo de datos por modelo (por ejemplo, 24 meses para la estacionalidad mensual y 2 observaciones por día de semana) y devolver 422 si no se cumple.

### F-23 — El holdout evalúa meses que el entrenamiento nunca vio 🔎

- **Problema:** con el 20% final como prueba, los meses de prueba suelen corresponder a dummies que nunca aparecieron en el entrenamiento. Sus coeficientes quedan en 0 y la métrica "fuera de muestra" termina midiendo una extrapolación degenerada.
- **Corrección propuesta:** backtesting con origen móvil (*rolling origin* / `TimeSeriesSplit`) y error reportado por horizonte de pronóstico.

### F-24 — El intervalo no es un intervalo de predicción real ✅

- **Dónde:** `forecast.py:70-74`
- **Problema:** usa ±1,96·σ de los residuos con `ddof=1`. No considera la incertidumbre de los parámetros, los grados de libertad (n − p) ni que el error crece con el horizonte: el mes 1 y el mes 12 tienen el mismo margen.
- **Corrección propuesta:** usar `statsmodels.OLS(...).get_prediction().summary_frame(alpha=0.05)`, o cuantiles empíricos de los residuos del backtest según el horizonte.

### F-25 — Ajuste duplicado y una columna con nombre engañoso 🔎

- `monthly_forecast` (`:185-202`) vuelve a entrenar un modelo para horizontes mayores a 1, duplicando `monthly_predictions`, y no devuelve intervalos ni métricas.
- `precision_estimada` guarda el R² del holdout. El R² no es una "precisión", puede ser negativo, y la columna es `DECIMAL(5,2)`.
- **Corrección propuesta:** un único camino de ajuste por horizonte, y renombrar la columna (o documentarla) como `r2_holdout`.

### F-26 — Faltan modelos de referencia para comparar ⚠️ (lo más importante para la tesis)

- **Problema:** R², MAPE y RMSE por sí solos no demuestran que el modelo aporte algo. Un tribunal preguntará: "¿mejor que qué?".
- **Corrección propuesta:**
  - Comparar contra un pronóstico ingenuo (último valor), uno estacional ingenuo (mismo mes del año anterior) y un promedio móvil.
  - Reportar MASE o un *skill score* frente a esos modelos de referencia.
  - Agregar sMAPE o WAPE, porque MAPE se rompe con días de venta cero.

### F-27 — Faltan diagnóstico y reproducibilidad para el capítulo de la tesis 🔎

- **Corrección propuesta:**
  - Diagnóstico de residuos: autocorrelación (Ljung–Box) y heterocedasticidad.
  - Comparar contra un modelo más fuerte (SARIMA o ETS de statsmodels) para justificar la elección de la regresión lineal.
  - Un script reproducible, por ejemplo `backend/scripts/evaluate_models.py`, que use `DatosDePrueba/ventas_fabricadas/ventas_tienda_2_anios.xlsx` y genere las tablas y gráficos del capítulo.

---

## 4. Prioridad baja

| ID | Hallazgo | Dónde | Verif. |
|---|---|---|---|
| F-28 | Código muerto: `predict_next_day`; `daily_aggregates` (que agrupa por timestamp en vez de por fecha); `app/utils/` vacío; `SectionPlaceholder.tsx` | `forecast.py:122-137, 205-221` | 🔎 |
| F-29 | Columnas `Date` tipadas como `Mapped[datetime]`; deberían ser `Mapped[date]` | `models.py:88, 116` | ✅ |
| F-30 | El mensaje de error de conexión tiene `http://localhost:8000` fijo en lugar de `VITE_API_URL` | `frontend/src/lib/apiErrors.ts:10` | 🔎 |
| F-31 | La categoría del reporte se escribe a mano; debería ser un select alimentado por `/stats/categories` | `frontend/src/pages/ReportsPage.tsx` | 🔎 |
| F-32 | Las barras del reporte mensual dicen "Año 1 Real" en lugar del año real | `analytics_routes.py:579` | 🔎 |
| F-33 | `/ventas` no tiene filtro de fechas, a diferencia de los demás endpoints | `analytics_routes.py` | 🔎 |
| F-34 | Documentación desactualizada:<br>• `AGENTS.md:7` dice que el frontend está "solo en planificación"<br>• `AGENTS.md:18` dice que los tests necesitan PostgreSQL<br>• `README.md` marca sprints de frontend como pendientes<br>• `Makefile:58-66` tiene targets de Docker sin docker-compose<br>• `CHANGELOG.md` no cubre las tareas 001–014<br>• la versión de Python no coincide (el caché es de 3.14 y el README dice 3.11+) | varios | 🔎 |

> F-34 toca el `README.md` raíz, que las reglas de `TASKS.md` excluyen de las tareas.
> Si lo autorizas, iría como una tarea aparte con permiso explícito.

---

## 5. Higiene del repositorio (ya aplicado)

Revisión de archivos sensibles (2026-11-02):

- **Archivos versionados:** no hay `.env`, claves, dumps ni datos reales. Solo están `backend/.env.example` y `frontend/.env.example`, con valores de ejemplo (`CHANGE_ME`).
- **Historial de git:** nunca se commitearon `.env`, claves, `.db`, `.csv`, `.xlsx` ni `.coverage`.
- **Ya ignorados:** `backend/.env`, `venv/`, `node_modules/`, `dist/`, `.coverage` y los cachés.
- **Agregados a `.gitignore`:**
  - `DatosDePrueba/`
  - `.env.*` (con excepción de `!.env.example`)
  - Certificados y claves: `*.pem`, `*.key`, `*.crt`, `*.p12`, `*.pfx`, `id_rsa*`, `*.keystore`
  - JSON de credenciales: `credentials*.json`, `secrets*.json`, `service-account*.json`
  - Bases de datos y dumps: `*.sqlite`, `*.sqlite3`, `*.db`, `*.dump`, `*.bak`, `backups/`
  - Hojas de cálculo: `*.xlsx`, `*.xls`
  - Configuración local: `.claude/settings.local.json`, `*.local.json`
- **Pendiente de tu decisión:** `.claude/` y `CLAUDE.md` siguen sin seguimiento y sin ignorar. No tienen secretos (son skills y documentación). Opciones: commitearlos (recomendado para `CLAUDE.md`) o ignorarlos. `.claude/skills/` es una copia de `.agents/skills/`.

---

## 6. Orden sugerido de ejecución

1. **CI y migraciones:** F-05 y F-06.
2. **Robustez de la ETL:** F-01, F-02, F-03, F-11 y F-12.
3. **Reportes seguros:** F-04 y F-14, y después F-09.
4. **Modelo para la tesis:** F-21 a F-27.
5. **Frontend:** F-07, F-18 y F-19.
6. **Contrato de la API:** F-08 y F-10.
7. **Configuración y autenticación:** F-15 y F-16.
8. **Tests y linting:** F-17 y F-20.
9. **Limpieza y documentación:** F-28 a F-34.

---

## 7. Autorización

Marca lo que autorizas. Lo no marcado queda fuera del plan.

- [ ] Prioridad alta completa (F-01 a F-07)
- [ ] Prioridad media completa (F-08 a F-20)
- [ ] Modelo ML completo (F-21 a F-27)
- [ ] Prioridad baja completa (F-28 a F-33)
- [ ] F-34, documentación incluido `README.md` (excepción a la regla de `TASKS.md`)

**Decisiones de diseño necesarias:**

- [ ] F-03: ¿se permiten montos negativos (devoluciones)? Recomendación: no.
- [ ] F-08: ¿`Prediccion` se persiste con un historial consultable, o se deja de persistir?
- [ ] F-13: ante un archivo duplicado, ¿se rechaza o solo se advierte?
- [ ] F-27: ¿se agrega `statsmodels` como dependencia (para SARIMA/ETS e intervalos)?
- [ ] `.claude/` y `CLAUDE.md`: ¿commitear o ignorar?

**Exclusiones o comentarios:**

_(escribe aquí)_

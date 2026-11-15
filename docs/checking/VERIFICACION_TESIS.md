# Verificación Tesis ↔ Sistema

**Proyecto:** Dashboard web de inteligencia de negocios con analítica descriptiva y predictiva para PyMEs del sector retail
**Autor de la tesis:** Stanley
**Fuente:** proyecto LaTeX de Overleaf (capítulos 1, 2 y 3)
**Última sincronización con la tesis:** 2026-11-08

---

## 0. Instrucciones para los agentes

Este documento enumera **todo lo que la tesis afirma sobre el sistema**. Tu trabajo es comprobar que el código lo cumple y reportar cualquier diferencia.

Reglas:

1. **La tesis describe; el código debe coincidir.** Cada requisito (`REQ-xx`) se basa en una afirmación concreta de la tesis. Si el código hace algo distinto, **no modifiques el código ni la tesis por tu cuenta**: anota la diferencia en el Registro de discrepancias (sección 10) con una propuesta. El autor decide qué se cambia.
2. **No inventes umbrales.** Si la tesis no fija un valor (por ejemplo, la latencia máxima o el MAE aceptable), mide y reporta el valor real, pero no lo marques como aprobado ni reprobado. Esos casos están marcados como `SIN UMBRAL`.
3. **Evidencia obligatoria.** Cada requisito que marques como `CUMPLE` necesita evidencia: la ruta del archivo y la función, el nombre de la prueba automatizada, la salida de un comando o una captura.
4. **Pruebas automatizadas primero.** Siempre que se pueda, la verificación debe ser una prueba que se vuelva a ejecutar (pytest para el backend, Vitest/Jest o Playwright para el frontend). En el estado de cada requisito, indica el nombre de la prueba.
5. **Estados permitidos:** `CUMPLE`, `NO CUMPLE`, `PARCIAL`, `NO VERIFICABLE` (explica por qué) y `PENDIENTE DE DEFINIR` (falta una decisión del autor).
6. Las rutas de la tesis se indican como `archivo.tex › Sección`. Los números de línea cambian, así que no los uses.

---

## 1. Stack tecnológico declarado

Fuente: `intro.tex › Justificación`, `intro.tex › Objetivos › Específicos`, `intro.tex › Preguntas Específicas`, `arte.tex › 2.1.4 y 2.1.5`, `metodos.tex › Herramientas y Bibliotecas Especializadas`

| ID | Afirmación de la tesis | Cómo verificar |
|---|---|---|
| REQ-01 | El backend es una **API RESTful desarrollada con FastAPI (Python)**. | La dependencia `fastapi` está en `requirements.txt`/`pyproject.toml`; la app expone endpoints HTTP con recursos y verbos REST. |
| REQ-02 | FastAPI funciona como **núcleo de procesamiento asíncrono**. | Los endpoints que ejecutan el ETL o el modelo están definidos con `async def` o delegan en tareas en segundo plano o en un *executor*. Reporta cuáles son síncronos. |
| REQ-03 | La base de datos relacional es **PostgreSQL**. | Hay un driver de PostgreSQL (`psycopg`/`asyncpg`/SQLAlchemy con URL `postgresql://`) y se puede crear el esquema en PostgreSQL. |
| REQ-04 | La ingeniería de datos y el ETL usan **Pandas**. | Las transformaciones de REQ-20 a REQ-27 están implementadas con `pandas.DataFrame`. |
| REQ-05 | El motor predictivo usa **Scikit-Learn**. | Se importa `sklearn` y se usa en el entrenamiento y las métricas (REQ-30 a REQ-37). |
| REQ-06 | El frontend usa **React**. | La dependencia `react` está en `package.json` y la UI está hecha con componentes React. |
| REQ-07 | Los estilos usan **Tailwind CSS**. | La dependencia `tailwindcss` está configurada y los componentes usan clases de utilidad. |
| REQ-08 | Las gráficas usan **Chart.js**. | Las dependencias `chart.js` (y opcionalmente `react-chartjs-2`) están instaladas y renderizan las gráficas de REQ-50 a REQ-52. |
| REQ-09 | El ecosistema completo es **de código abierto**, sin software de BI privativo. | Auditoría de licencias de todas las dependencias (`pip-licenses`, `license-checker`): ninguna puede ser privativa ni de pago. Adjunta el reporte. Esto respalda la Pregunta Específica 3. |

---

## 2. Dataset

Fuente: `metodos.tex › Selección y Estructura de Datos`

| ID | Afirmación de la tesis | Cómo verificar |
|---|---|---|
| REQ-10 | El dataset es **sintético** y lo genera un **script en Python** que simula transacciones minoristas. | El script existe, puede ejecutarse y su ruta queda documentada. Registra los parámetros que usa: número de registros, rango de fechas, categorías y semilla aleatoria. |
| REQ-11 | La generación debe ser **reproducible**. | *(Recomendado, no lo dice la tesis.)* Con la misma semilla se obtiene el mismo dataset. Si no hay semilla, anótalo en la sección 10. |
| REQ-12 | Los registros generados se guardan en **archivos CSV o en tablas de PostgreSQL**. | Ambas rutas, o la que se use, funcionan de extremo a extremo. Indica cuál usa el sistema. |
| REQ-13 | El esquema contiene exactamente estos campos: | Prueba de esquema sobre el dataset generado y sobre la tabla de PostgreSQL. |

| Campo | Tipo declarado en la tesis | Validación |
|---|---|---|
| `id` | Clave primaria numérica | Entero, único, no nulo |
| `fecha` | Fecha en formato ISO `AAAA-MM-DD` | Coincide con `^\d{4}-\d{2}-\d{2}$` y es una fecha válida |
| `categoria` | Variable categórica | Texto no vacío, con un conjunto finito de valores |
| `cantidad` | Cuantitativa **discreta** | Entero ≥ 0 |
| `precio_unitario` | Cuantitativa **continua**, en moneda local | Decimal > 0 |
| `total` | Derivada: `cantidad × precio_unitario` | `abs(total − cantidad*precio_unitario) < 0.01` en el 100 % de las filas |

---

## 3. Pipeline ETL

Fuente: `metodos.tex › Pandas (Ingeniería de Datos y Tubería ETL)` y `metodos.tex › Preprocesamiento e Ingeniería de Características (ETL)`

### Extracción
| ID | Afirmación | Cómo verificar |
|---|---|---|
| REQ-20 | Se leen los registros desde PostgreSQL **o** desde archivos planos hacia un DataFrame. | Prueba con ambas fuentes, o con la que aplique (ver REQ-12). |
| REQ-21 | Los encabezados de columna se asignan correctamente. | El DataFrame resultante tiene exactamente las columnas de REQ-13. |

### Transformación y limpieza
| ID | Afirmación | Cómo verificar |
|---|---|---|
| REQ-22 | Se **eliminan** los registros con `NaN` en campos críticos como `fecha` o `total`. | Prueba: un DataFrame con nulos inyectados en `fecha` y en `total` debe salir sin esas filas. |
| REQ-23 | Los **valores atípicos** (*outliers*) se imputan o eliminan mediante **máscaras booleanas**. | Hay un filtro de outliers. Documenta el criterio que usa (IQR, z-score, etc.), porque la tesis no lo especifica. → Si no existe, márcalo `NO CUMPLE`. |
| REQ-24 | `fecha` se convierte a `datetime64`. | `df["fecha"].dtype` es `datetime64[ns]`. |
| REQ-25 | De la fecha se derivan el **día de la semana**, el **mes** y la **semana del año**. | Las tres columnas existen y sus valores son correctos para fechas conocidas (por ejemplo, 2026-01-01 es jueves, mes 1, semana ISO 1). |
| REQ-26 | Se **agrupa** (`groupby`) sumando `total` **por día y por categoría**. | Con un dataset de prueba pequeño, la suma agrupada coincide con un cálculo hecho a mano. |
| REQ-27 | Los identificadores comerciales se limpian y estandarizan. | Se normalizan mayúsculas, espacios y acentos en `categoria` y en los identificadores. Documenta qué reglas se aplican. |

### Carga
| ID | Afirmación | Cómo verificar |
|---|---|---|
| REQ-28 | Los datos transformados se **ordenan cronológicamente** y se estructuran en matrices homogéneas (numéricas) para Scikit-Learn. | La salida está ordenada por fecha (`is_monotonic_increasing`) y la matriz `X` es completamente numérica, sin `object`. |
| REQ-29 | El ETL alimenta tanto las **consultas descriptivas** del backend como el **entrenamiento** del modelo. | Ambos consumidores usan la salida del mismo pipeline, no lógicas duplicadas. |

---

## 4. Modelo predictivo

Fuente: `metodos.tex › Scikit-Learn`, `metodos.tex › Modelado Predictivo`, `arte.tex › 2.1.3.4 Regresión Lineal Múltiple`

| ID | Afirmación | Cómo verificar |
|---|---|---|
| REQ-30 | El algoritmo es **Regresión Lineal Múltiple** de `sklearn.linear_model`. | Se usa `LinearRegression` u otro estimador lineal de ese módulo. **No debe haber Random Forest ni otros modelos** en producción: la tesis los descartó explícitamente. Si existen otros modelos, repórtalos. |
| REQ-31 | El ajuste se hace por **Mínimos Cuadrados Ordinarios (OLS)**. | `LinearRegression` usa OLS. Si se usa Ridge, Lasso u otro, márcalo `NO CUMPLE`. |
| REQ-32 | La ecuación es `Y = β0 + β1X1 + … + βnXn + ε`; el modelo expone el **intercepto (β0)** y los **coeficientes (βn)**. | `model.intercept_` y `model.coef_` están disponibles y se registran en logs o en la API. |
| REQ-33 | Las características son exactamente: **X1** = índice de tendencia temporal (conteo secuencial de periodos), **X2** = estacionalidad (mes o trimestre) y **X3** = promedio de ventas del periodo anterior (*lag*). | Se inspecciona la construcción de `X`. Reporta si hay características extra o si falta alguna. |
| REQ-34 | X2 es un indicador **categórico**. | Comprueba cómo se codifica: one-hot o numérico 1–12. Reporta cuál se usa (ver Pendiente P-04). |
| REQ-35 | La variable objetivo `Y` es "la cantidad **o** el monto total de ventas". | Reporta **cuál de las dos** usa el sistema. La tesis debe precisarlo (ver P-05). |
| REQ-36 | El dataset se divide con `train_test_split`: **70–80 % entrenamiento** y **20–30 % prueba**. | Verifica la proporción real. Reporta también si hay `shuffle=True`, que es el valor por defecto (ver P-03). |
| REQ-37 | Las métricas **MAE** y **RMSE** se calculan con `sklearn.metrics` **sobre el conjunto de prueba**, con datos no vistos en el entrenamiento. | Prueba: las métricas se calculan con `y_test`/`y_pred`, nunca con datos de entrenamiento. Comprueba los valores con las fórmulas de la tesis: `MAE = (1/n)Σ|yᵢ − ŷᵢ|` y `RMSE = √((1/n)Σ(yᵢ − ŷᵢ)²)`. |
| REQ-38 | Los coeficientes se ajustan **automáticamente** en el backend. | Hay un endpoint o proceso que reentrena el modelo sin intervención manual. |

---

## 5. Comunicación cliente-servidor (API)

Fuente: `metodos.tex › Validación e Integración del Sistema`, `metodos.tex › Chart.js`, `arte.tex › 2.1.1`

| ID | Afirmación | Cómo verificar |
|---|---|---|
| REQ-40 | El backend **serializa DataFrames de Pandas a JSON estructurado**. | Prueba de contrato: la respuesta es JSON válido, con el esquema documentado y fechas en ISO. |
| REQ-41 | La API envía al frontend un vector JSON con el **histórico** y la **proyección predictiva**. | Hay un endpoint cuya respuesta incluye ambas series, diferenciadas. |
| REQ-42 | El ETL y el ajuste del modelo se ejecutan de forma **asíncrona** en el backend. | Igual que REQ-02, aplicado específicamente al pipeline. |
| REQ-43 | La comunicación tiene una "latencia mínima". | `SIN UMBRAL`: mide el p50/p95 de los endpoints principales y repórtalo, sin aprobar ni reprobar. |
| REQ-44 | La arquitectura **separa la capa de presentación de la capa de lógica de negocio** (cliente-servidor). | El frontend y el backend son aplicaciones separadas que se comunican solo por HTTP/JSON. |

---

## 6. Dashboard (frontend)

Fuente: `intro.tex › Objetivos › Específico 4`, `metodos.tex › Chart.js`, figura `fig:arquitectura_resultados`

| ID | Afirmación | Cómo verificar |
|---|---|---|
| REQ-50 | Hay **gráficos de líneas** para las series temporales de ventas, con histórico y proyección. | Prueba E2E: la gráfica se renderiza con datos de la API. |
| REQ-51 | Hay **gráficos de sectores o barras** para la distribución por categoría. | Prueba E2E. |
| REQ-52 | Existen las dos vistas de la figura de arquitectura: **"Proyección Global"** y **"Análisis por Categoría"**. | Las dos vistas o secciones están en la UI. |
| REQ-53 | El dashboard es **responsive**. | Captura a 375 px y a 1440 px de ancho sin scroll horizontal. |
| REQ-54 | Las actualizaciones redibujan solo lo que cambia, **sin recargar la página completa**. | Prueba E2E: al cambiar un filtro no hay navegación completa (no se dispara `load`). |
| REQ-55 | Se muestran **analítica descriptiva** (KPIs históricos) y **analítica predictiva** (proyección). | Las dos capas son visibles en la UI. |
| REQ-56 | El dashboard muestra los **KPIs** definidos en el Objetivo Específico 1. | `PENDIENTE DE DEFINIR`: la tesis aún no lista los KPIs (ver P-06). |

---

## 7. Experimento de validación (capítulo 3)

Fuente: `metodos.tex › Definición del Experimento` y `metodos.tex › Ejecución del Experimento`

Los tres escenarios deben existir como **pruebas automatizadas** con nombre propio:

| ID | Escenario | Prueba esperada |
|---|---|---|
| REQ-60 | **Comunicación de datos:** DataFrame → JSON sin pérdida ni errores. | `test_serializacion_json` (o equivalente) |
| REQ-61 | **Precisión algorítmica:** MAE y RMSE "dentro de los márgenes tolerables". | `SIN UMBRAL` (ver P-02): la prueba calcula y registra los valores, pero todavía no compara contra un umbral. |
| REQ-62 | **Renderizado dinámico:** Chart.js dibuja líneas y sectores sin errores de sincronización. | Prueba E2E sin errores en consola. |

Las cuatro fases deben poder ejecutarse en orden con un solo comando (script o `make`):

1. **Ingesta:** cargar el dataset sintético (REQ-10).
2. **Backend:** ETL asíncrono y ajuste del modelo (REQ-20 a REQ-38).
3. **Métricas:** calcular y **registrar** MAE y RMSE en un archivo con fecha, por ejemplo `resultados/metricas_AAAA-MM-DD.json`.
4. **Frontend:** enviar el JSON y renderizar (REQ-41, REQ-50).

> Las métricas registradas en la fase 3 son las que se reportarán en el **Capítulo 4 (Resultados)**. Guarda cada corrida con la versión del código (commit), la semilla y los parámetros del dataset.

---

## 8. Trazabilidad con objetivos, preguntas e hipótesis

| Elemento de la tesis | Requisitos que lo respaldan | Estado de cobertura |
|---|---|---|
| **OE1:** analizar KPIs y requerimientos | REQ-55, REQ-56 | Incompleto (P-06) |
| **OE2:** diseñar la BD (modelo entidad-relación) y la arquitectura cliente-servidor | REQ-03, REQ-13, REQ-44 + **existen el diagrama ER y el de arquitectura** en el repositorio o en la tesis | Verifica que los diagramas coincidan con el esquema real |
| **OE3:** motor predictivo con Python, Scikit-Learn y Pandas | REQ-04, REQ-05, REQ-20 a REQ-38 | Cubierto |
| **OE4:** dashboard con Tailwind, React y Chart.js | REQ-06, REQ-07, REQ-08, REQ-50 a REQ-55 | Cubierto |
| **OE5:** validar la precisión con MAE en conjuntos de prueba | REQ-37, REQ-61 | Falta el umbral (P-02) |
| **PE1:** ¿el ETL mejora la integridad y la calidad de los datos? | REQ-22 a REQ-27 + **métricas de calidad antes y después del ETL** (porcentaje de nulos, duplicados, filas inválidas) | Recomendado: genera ese reporte |
| **PE2:** ¿la Regresión Lineal Múltiple reduce el error en ventas estacionales? | REQ-30 a REQ-37 + comparación con baseline | Falta el baseline (P-01) |
| **PE3:** ¿el código abierto reduce las barreras económicas frente al BI privativo? | REQ-09 | Parcial: falta la comparación de costos (P-07) |
| **Hipótesis:** error menor que los métodos empíricos tradicionales | REQ-37 + baseline | **No demostrable sin P-01** |

---

## 9. Pendientes que debe decidir el autor

Estos puntos los tiene que resolver el autor y luego reflejarlos **en la tesis y en el código al mismo tiempo**. Los agentes no deben resolverlos por su cuenta.

| ID | Pendiente | Por qué importa | Opciones sugeridas |
|---|---|---|---|
| P-01 | **Baseline del "método empírico tradicional"** | La hipótesis compara contra este método, pero la tesis no lo define. | Pronóstico ingenuo (repetir el periodo anterior), promedio móvil de *k* periodos o ingenuo estacional (mismo mes del año anterior). |
| P-02 | **Umbral aceptable de MAE y RMSE** | El OE5 y el REQ-61 dicen "margen tolerable" sin dar un número. | Umbral relativo, por ejemplo un MAPE menor que X %, o simplemente "menor que el baseline de P-01". |
| P-03 | **División temporal en lugar de aleatoria** | `train_test_split` revuelve los datos por defecto, y en series de tiempo eso deja ver el futuro (*data leakage*). | `train_test_split(..., shuffle=False)` o `TimeSeriesSplit`. Si se cambia, hay que actualizar `metodos.tex`. |
| P-04 | **Codificación de X2 (estacionalidad)** | La tesis dice que es "categórico". Si se codifica 1–12 como número, la regresión lo trata como si fuera lineal. | One-hot del mes o trimestre. |
| P-05 | **Variable objetivo Y** | La tesis dice "cantidad **o** monto total". | Elegir una y precisarla en la tesis. |
| P-06 | **Lista de KPIs** | El OE1 promete definirlos, pero no están en la tesis. | Ventas totales, ticket promedio, unidades por categoría, producto de mayor rotación, crecimiento mensual, etc. |
| P-07 | **Comparación de costos frente al BI privativo** | Es necesaria para responder la PE3. | Tabla de costos de licencias (Power BI, Tableau) frente a $0 en licencias más el costo de hosting. |
| P-08 | **Criterio de outliers** | El REQ-23 menciona máscaras booleanas, pero no dice con qué criterio. | IQR (1.5×) o z-score > 3. |

---

## 10. Registro de discrepancias

Los agentes agregan una fila por cada diferencia entre la tesis y el código. **No borres filas**: cuando se resuelvan, cambia el estado.

| Fecha | REQ | Lo que dice la tesis | Lo que hace el sistema | Propuesta (cambiar código / cambiar tesis) | Estado |
|---|---|---|---|---|---|
| | | | | | Abierta |
| 2026-11-08 | REQ-13 | Esquema exacto con `id`, `fecha`, `categoria`, `cantidad`, `precio_unitario`, `total` | Usa `id_venta`, `fecha_venta`, `monto`; no tiene `precio_unitario` ni `total` | Cambiar código o precisar el esquema real en la tesis | Decidida por el autor (2026-11-14): se cambia la tesis y el código no cambia. En `metodos.tex › Selección y Estructura de Datos`, documentar el esquema real de `ventas` (`id_venta`, `id_usuario`, `producto`, `categoria`, `cantidad` DECIMAL, `monto`, `fecha_venta`) con equivalencias: `total` = `monto`, `fecha` = `fecha_venta`, `precio_unitario` es una entrada opcional con la que se deriva `monto = precio_unitario × cantidad`. Explicar `producto`, `id_usuario` (multiusuario) y la cantidad decimal (kg, litros). Agregar la frase: «el esquema interno es fijo; los archivos con otros nombres de columna se adaptan mediante el mapeo de columnas (ver ETL › Extracción)». En `metodos.tex › Pandas (Ingeniería de Datos y Tubería ETL)` (extracción), explicar el mapeo: roles, propuesta por nombre exacto o sinónimo sin coincidencia difusa, revisión del usuario y derivación del monto, con una tabla breve de sinónimos de ejemplo, y citar como evidencia los 3 datasets reales (Online Retail II, Iowa Liquor Sales, Open e-commerce 1.0; `docs/pruebas/036-datos-reales.md`). Al cerrar, actualizar REQ-13 y REQ-21 en la §2 y la §3. |
| 2026-11-08 | REQ-23 | Outliers mediante máscaras booleanas | No hay filtro de outliers | Definir criterio P-08 e implementarlo, o retirar la afirmación | Decidida por el autor (2026-11-14): se retira la afirmación y el código no cambia. Redacción para `metodos.tex › Preprocesamiento e Ingeniería de Características (ETL)`: «No se eliminan ni se imputan valores atípicos: en ventas minoristas un valor extremo suele ser real (temporadas, promociones), y eliminarlo sesgaría la estacionalidad que se busca modelar. La limpieza se limita a rechazar registros inválidos: montos no positivos, cantidades negativas y fechas inválidas». Al cerrar, retirar REQ-23 de la §3 y cerrar P-08. |
| 2026-11-08 | REQ-24..26 | ETL convierte fecha, deriva calendario y agrupa por día/categoría | Esas operaciones no existen como pipeline ETL único | Alinear pipeline o cambiar afirmaciones | Decidida por el autor (2026-11-14): se cambia la tesis y el código no cambia. Aplica también a REQ-04 y REQ-22. Redacción para `metodos.tex › Pandas (Ingeniería de Datos y Tubería ETL)` y `› Preprocesamiento e Ingeniería de Características (ETL)`: «Extracción: el archivo (CSV, XLSX o SQL) se lee y sus columnas se asignan a los roles del sistema mediante el mapeo. Transformación y limpieza: cada registro se valida de forma individual; se rechazan los que tienen fecha o monto ausentes o inválidos, cantidades negativas o caracteres de control, y se informa el número de fila de cada rechazo; las categorías y los productos se estandarizan. Carga: los registros válidos se guardan en PostgreSQL en una sola transacción. Para el modelo, Pandas convierte la fecha a `datetime64`, ordena y agrega las ventas por mes; las consultas descriptivas agregan en SQL». Se retiran `dropna`, la semana del año y el `groupby` por día y categoría con Pandas. Al cerrar, actualizar REQ-04, REQ-22, REQ-24, REQ-25 y REQ-26. |
| 2026-11-08 | REQ-29 | Un ETL alimenta consultas y modelo | Consultas usan SQL; ML agrega sus propios datos | Centralizar la salida ETL o documentar pipelines distintos | Decidida por el autor (2026-11-14): se documentan los dos consumidores y el código no cambia (ver la fila REQ-24..26). Redacción: «El ETL alimenta una única tabla `ventas`; las consultas descriptivas la agregan en SQL y el motor predictivo la agrega por mes con Pandas». Al cerrar, actualizar REQ-29. |
| 2026-11-08 | REQ-33 | Features: tendencia, estacionalidad y lag | Usa tendencia y dummies; no usa lag | Resolver definición de features en tesis/código | Decidida por el autor (2026-11-14): se cambia la tesis y el código no cambia. Ver la fila REQ-33, REQ-34 del 2026-11-14. |
| 2026-11-08 | REQ-36 | `train_test_split`, 70–80/20–30 | Usa holdout temporal propio | Resolver P-03 y sincronizar tesis/código | Decidida por el autor (2026-11-14): se cambia la tesis y el código no cambia. Redacción para `metodos.tex › Modelado Predictivo` y `› Definición del Experimento`: «La validación usa un esquema de origen móvil (*rolling origin*), equivalente a `TimeSeriesSplit` de Scikit-Learn: el modelo se reentrena con los datos hasta cada uno de los últimos 6 meses y predice el mes siguiente, que no vio. El modelo diario reserva el 20 % final de los días en orden cronológico. No se usa una partición aleatoria (`train_test_split`), porque mezclaría observaciones futuras en el entrenamiento». Al cerrar, actualizar REQ-36 y cerrar P-03. |
| 2026-11-08 | REQ-37 | MAE y RMSE con `sklearn.metrics` | Calcula RMSE, MAPE y R² con función propia; no MAE | Alinear métricas y registrar valores | Resuelta (tarea 034): `backend/app/ml_models/evaluation.py` · `point_metrics` usa `mean_absolute_error` y `root_mean_squared_error` sobre meses no vistos; prueba `backend/tests/test_evaluation.py::test_mae_and_rmse_follow_the_thesis_formulas`; MAE del modelo y de las referencias en `docs/evaluacion/resultados.md` |
| 2026-11-08 | REQ-42 | ETL y modelo asíncronos | Rutas y servicios son síncronos | Cambiar implementación o tesis | Decidida por el autor (2026-11-14): se precisa la tesis, se conserva la palabra «asíncrono» y no se menciona el número de *workers*. Aplica también a REQ-02. Redacción para `intro.tex › Justificación`, `arte.tex › 2.1.4` y `metodos.tex › Validación e Integración del Sistema`: «FastAPI, sobre un servidor ASGI asíncrono, atiende las solicitudes de forma concurrente: el ETL y el ajuste del modelo, que son tareas bloqueantes, se ejecutan en hilos de trabajo, y el envío de correos, en segundo plano, de modo que una operación larga no bloquea al resto de usuarios». Código: script versionado que mide la latencia de `GET /analytics/stats` en reposo y durante la carga del XLSX completo, con `uvicorn` y PostgreSQL local, y registra el resultado en `docs/evaluacion/` (tarea C6 del reporte). Al cerrar, cambiar el criterio de REQ-02 y REQ-42 a «una carga larga no bloquea otras solicitudes». Código resuelto (tarea 052, 2026-11-14): `python scripts/measure_concurrency.py` (base desechable `predicta_bench`, `uvicorn` con 1 worker, PostgreSQL local) → `docs/evaluacion/concurrencia.md`: `GET /analytics/stats` de un segundo usuario, p50 6.2 ms y p95 9.1 ms en reposo (n = 30); durante la carga del XLSX completo (12.5 s), p50 365.8 ms, p95 517.0 ms y máximo 536.5 ms (n = 17), sin errores. No hay bloqueo, pero la latencia sube unas 60 veces porque las solicitudes comparten la CPU y el GIL con el ETL. Ajuste recomendado a la redacción: agregar «aunque la latencia de las demás solicitudes aumenta mientras dura la operación (de unos 6 ms a unos 0.4 s en la medición local)». Falta solo el cambio en la tesis. |
| 2026-11-08 | REQ-50..52 | Histórico/proyección y dos vistas arquitectónicas | Línea histórica y barras existen; falta vista combinada y nombres exactos | Completar frontend o precisar alcance | Abierta, parcial (2026-11-14: la vista combinada existe en `ForecastChart.tsx` con `GET /analytics/forecast`; faltan los nombres «Proyección Global» y «Análisis por Categoría»). Decidida por el autor (2026-11-14) para REQ-52: se cambia la figura `fig:arquitectura_resultados` con los nombres actuales (página «Predicciones», titulada «Siguiente movimiento», con proyección global, por categoría o por producto; dashboard con las vistas «General», «Por categoría», «Por mes» e «Historial completo»), y la UI no cambia. Las pruebas E2E de REQ-50 y REQ-51 quedan como tarea C4 del reporte. E2E resueltas (tarea 053, 2026-11-14): `predictions.spec.ts` › «REQ-50: la gráfica de líneas dibuja el historial y la proyección que devuelve la API» (24 meses de historial + 12 proyectados, lienzo pintado, tabla de 36 filas) y `dashboard.spec.ts` › «REQ-51: la gráfica de barras muestra los ingresos de las 5 categorías» y «REQ-54: cambiar la vista y el filtro de fechas no recarga la página» (ningún evento `load`). Falta solo el cambio de la figura en la tesis. |
| 2026-11-08 | REQ-53, REQ-62 | Responsive y renderizado dinámico validado | No hay pruebas E2E ni capturas | Incorporar E2E y evidencia reproducible | Resuelta (tarea 053, 2026-11-14): Playwright en `frontend/e2e/` (`npm run e2e`) contra la API real (uvicorn + PostgreSQL `predicta_e2e` sembrada con el dataset de la tesis por `backend/scripts/e2e_server.py`) y el build de producción; job `e2e` en CI. REQ-53: `dashboard.spec.ts` y `predictions.spec.ts` › «REQ-53: … no tiene scroll horizontal a 375/1440 px», con capturas en `docs/evaluacion/capturas/` (dashboard-375, dashboard-1440, predicciones-375, predicciones-1440). La prueba encontró *scroll* horizontal a 375 px y se corrigió: las tablas `sr-only` de `ChartFrame` (una tabla ignora `width: 1px`) y la tarjeta del detalle mensual sin `min-w-0` en `PredictionsPage.tsx`. REQ-62: el fixture `e2e/fixtures.ts` falla ante cualquier error de consola o excepción; detectó un 404 del `favicon.ico` (también en producción), corregido con `public/favicon.svg`. |
| 2026-11-08 | REQ-61 | Métricas registradas para Capítulo 4 | API devuelve métricas; no hay archivo fechado con commit/semilla/parámetros | Definir comando único y formato de resultados | Resuelta (tarea 051, 2026-11-14): `docs/resultados/metricas_2026-11-14.json` (monto, horizonte 1: WAPE 9.32 % frente a 10.41 % del promedio móvil de 3 meses; hipótesis cumplida; MAPE 9.29 %, «muy precisa» según Lewis). Ver la fila §7 del 2026-11-14. |
| 2026-11-08 | REQ-09 | Ecosistema completamente abierto | Auditoría Python no ejecutable; NPM incluye `UNLICENSED` | Auditar dependencias y resolver licencia | Abierta, reducida (2026-11-14: `pip-licenses` y `license-checker` sin dependencias privativas; el `UNLICENSED` es el propio `predicta-frontend`; ver la fila REQ-09 del 2026-11-14). Resuelta (tarea 046, 2026-11-14). |
| 2026-11-08 | REQ-10/11 | Dataset sintético reproducible | XLSX usa semilla 2026; CSV alternativo usa aleatoriedad sin semilla | Elegir un generador autoritativo y documentarlo | Resuelta (tarea 047, 2026-11-14): `backend/scripts/generate_dataset.py` · `generate_dataset` usa `random.Random(seed)` (semilla 2026) y fecha de inicio fija 2023-11-01, configurables con `--seed`, `--start` y `--days`; su docstring nombra a `DatosDePrueba/ventas_fabricadas/generar_ventas.py` (semilla 2026) como el generador del dataset de la tesis. Pruebas: `backend/tests/test_generate_dataset.py::test_same_seed_gives_the_same_dataset`, `::test_another_seed_gives_another_dataset`, `::test_dates_start_on_the_fixed_day_not_today`. |
| 2026-11-08 | Frontend | El frontend está disponible como parte del sistema | `AGENTS.md` lo declara planning-only, pero existen fuente React, tests y build funcional | Corregir documentación de alcance o declarar el estado real | Resuelta (2026-11-14): `AGENTS.md` describe `frontend/` como la SPA implementada |
| 2026-11-14 | REQ-30, REQ-05 | Regresión Lineal Múltiple con `sklearn.linear_model`; Scikit-Learn en entrenamiento y métricas | `forecast.py` ajusta con `statsmodels.OLS` (intervalos del 95 % con `get_prediction`); Scikit-Learn solo calcula MAE y RMSE; ETS solo en `scripts/evaluate_models.py` | Cambiar la tesis a `statsmodels.OLS` o migrar a `LinearRegression` (se pierden los intervalos) | Decidida por el autor (2026-11-14), opción A: se cambia la tesis y el código no cambia. Falta actualizar `metodos.tex › Scikit-Learn` y `› Modelado Predictivo`, y las menciones del stack en `intro.tex` y `arte.tex`: «RLM estimada por OLS con `statsmodels` (intervalos de predicción del 95 %); MAE y RMSE con `sklearn.metrics`». Al reflejarlo en la tesis, actualizar REQ-05 y REQ-30 en la §1 y la §4 y cerrar esta fila. |
| 2026-11-14 | REQ-32 | El modelo expone β0 y βn | `fitted.params` existe, pero no se registra ni se expone en la API, los logs ni `docs/evaluacion/` | Agregar los coeficientes a la respuesta de `/analytics/forecast` o a la evaluación | Resuelta (tarea 048, 2026-11-14): `backend/app/ml_models/forecast.py` · `fitted_coefficients` (de `fitted.params`); `GET /analytics/forecast` devuelve `coeficientes.monto` y `coeficientes.cantidad` (`schemas.CoefficientsByTarget`); `docs/evaluacion/resultados.md` › «Coeficientes del modelo final» y `coeficientes.csv` con coeficiente, error estándar y valor p. Monto: β0 = 76,512.59 (EE 7,429.93, p < 0.0001), β1 = 1,429.46 (EE 553.54, p = 0.0170); cantidad: β0 = 2,277.94, β1 = 29.16 (p = 0.0662). Pruebas: `tests/test_ml.py::test_coefficients_recover_the_line_that_generated_the_series`, `::test_seasonal_coefficients_name_every_month_dummy`, `tests/test_forecast_api.py::test_forecast_returns_history_projection_and_metrics_without_writing`. |
| 2026-11-14 | REQ-33, REQ-34 | X2 (estacionalidad) es parte del modelo | Las *dummies* de mes solo entran con 36 meses o más; con el dataset de 24 meses el modelo es solo de tendencia | Explicar la regla escalonada en la tesis o cambiar el umbral en el código | Decidida por el autor (2026-11-14): se cambia la tesis y el código no cambia. Cierra también la fila REQ-33 del 2026-11-08. Redacción para `metodos.tex › Modelado Predictivo` y `arte.tex › 2.1.3.4`: «Las variables explicativas son X1, el índice de tendencia (meses de calendario transcurridos desde el primer mes con ventas), y X2, la estacionalidad, codificada como 11 variables indicadoras del mes con enero como referencia. X2 se incorpora solo cuando el historial tiene al menos 36 meses completos con los 12 meses del calendario observados; con menos, el modelo usa solo la tendencia, porque con 24 meses la especificación estacional perdió frente al pronóstico ingenuo estacional en 4 de 6 horizontes del backtest. No se usa un rezago (*lag*), porque proyectar 12 meses con él exige una predicción recursiva que invalida los intervalos de predicción». Al cerrar, actualizar REQ-33 y REQ-34 y cerrar P-04. |
| 2026-11-14 | REQ-09 | Ecosistema completamente de código abierto | El repositorio no tiene `LICENSE` y `frontend/package.json` no declara `license` (el reporte del 2026-11-08 citaba un `LICENSE` MIT inexistente) | Elegir una licencia y agregarla | Resuelta (tarea 046, 2026-11-14): `LICENSE` MIT en la raíz y `"license": "MIT"` en `frontend/package.json` y en `package-lock.json`; `npx license-checker --production --excludePrivatePackages --summary` → `MIT: 46` (sin la opción, la herramienta marca `UNLICENSED` a todo paquete `private`). Decisión del autor (2026-11-14): MIT. Código: agregar `LICENSE` (MIT) en la raíz y `"license": "MIT"` en `frontend/package.json` (tarea C7 del reporte). Al terminar, cerrar esta fila y la de REQ-09 del 2026-11-08. |
| 2026-11-14 | REQ-35 | Y es «la cantidad o el monto total» | Dos modelos con las mismas variables, uno para `monto` y otro para `cantidad`; la API, la UI y los PDF muestran ambos | Precisar la Y en la tesis (P-05) | Decidida por el autor (2026-11-14): `monto` es la Y principal y `cantidad` la secundaria, y el código no cambia. Redacción para `metodos.tex › Modelado Predictivo`: «La variable objetivo principal es el monto total de ventas del mes; con las mismas variables explicativas se ajusta un segundo modelo para la cantidad de unidades. La hipótesis y los resultados del Capítulo 4 se evalúan sobre el monto». Al cerrar, actualizar REQ-35 y cerrar P-05. |
| 2026-11-14 | REQ-37, REQ-61, Hipótesis | La hipótesis compara con «métodos empíricos tradicionales» y el OE5 pide un «margen tolerable» sin definirlos | Hay tres referencias en `evaluation.py` (último valor, mismo mes del año anterior, promedio móvil de 3 meses) y la API reporta `mejora_vs_referencia`; no hay umbral | Definir el baseline (P-01) y el umbral (P-02) | Decidida por el autor (2026-11-14), y el código no cambia. Redacción para `intro.tex › Hipótesis`, `intro.tex › Objetivos › Específico 5` y `metodos.tex › Definición del Experimento`: «Los métodos empíricos de referencia son tres pronósticos simples: último valor, mismo mes del año anterior y promedio móvil de 3 meses. La hipótesis se acepta si el WAPE de la regresión en el horizonte de un mes es menor que el de la mejor de las tres referencias. La precisión se califica además con la escala de Lewis (1982) sobre el MAPE: menor de 10 %, muy precisa; de 10 a 20 %, buena; de 20 a 50 %, razonable; mayor de 50 %, imprecisa. MAE y RMSE se reportan en pesos como magnitud del error». Resultado actual (monto, horizonte 1): WAPE 9.32 % frente a 10.41 % del promedio móvil de 3 meses (+10.43 %) y MAPE 9.29 %, muy precisa. Los horizontes 2 a 6 se reportan como análisis adicional, sin ocultar que pierde en 3, 4, 5 y 6. El autor debe verificar la cita de Lewis (1982). Al cerrar, agregar un REQ con este criterio en la §7 y cerrar P-01 y P-02. |
| 2026-11-14 | REQ-56 | El OE1 promete definir los KPI | El dashboard muestra ingresos totales, operaciones, ticket promedio y venta más alta; no hay KPI de crecimiento | Definir los KPI (P-06) | Decidida por el autor (2026-11-14). KPI oficiales: ingresos totales (`SUM(monto)`), operaciones (número de ventas registradas) y ticket promedio (ingresos ÷ operaciones, aclarando que es el valor promedio por operación, porque los datos no traen un número de ticket que agrupe productos), más un KPI nuevo de crecimiento: variación % de los ingresos del último mes completo del rango filtrado frente al mes anterior y frente al mismo mes del año anterior cuando exista; sin dos meses completos muestra «Sin datos suficientes». «Venta más alta» se presenta como indicador descriptivo complementario. Redacción en `intro.tex › Objetivos › Específico 1` y en el capítulo de diseño del dashboard. Código: tarjeta de crecimiento (tarea C8 del reporte). Al cerrar, actualizar REQ-56 con la lista y cerrar P-06. Código resuelto (tarea 050, 2026-11-14): `backend/app/services/analytics_service.py` · `monthly_growth` y `GET /analytics/stats` › `crecimiento_mensual` (`periodo`, `ingresos`, `vs_mes_anterior`, `vs_anio_anterior`); `frontend/src/components/analytics/GrowthCard.tsx` en `DashboardPage.tsx`. Pruebas: `tests/test_analytics.py::test_growth_compares_the_last_complete_month_with_the_previous_one`, `::test_growth_skips_an_unfinished_last_month`, `::test_growth_follows_the_end_of_the_date_range`, `::test_growth_is_null_without_a_complete_month`; `DashboardPage.test.tsx` › «shows the monthly growth…» y «says when there is not enough history…». Falta solo el cambio en la tesis. |
| 2026-11-14 | PE3 | La PE3 necesita comparar costos con el BI privativo | No existe la comparación | Tabla de costos (P-07) | Decidida por el autor (2026-11-14). Crear `docs/costos/comparacion.md` con los precios oficiales actuales de Power BI y Tableau por usuario al mes (con fecha y fuente) para 1, 5 y 10 usuarios (con 5: 1 que diseña y 4 que consultan), frente a Predicta ($0 en licencias más el hosting de los planes actuales: Vercel Hobby gratis, Railway Hobby unos US$5 al mes, Neon Free y Brevo Free). Precios en USD y en MXN, con el tipo de cambio y su fecha. Nota obligatoria: Vercel Hobby es solo para uso no comercial; una PyME necesitaría Vercel Pro o un hosting estático gratuito que permita uso comercial (por ejemplo, Cloudflare Pages), con su costo. Requiere buscar precios en internet (tarea D1 del reporte). Al cerrar, cerrar P-07 y actualizar la §8. |
| 2026-11-14 | Alcance | La tesis no describe funciones implementadas fuera de este documento | Ver la sección «Funciones del sistema fuera de VERIFICACION_TESIS.md» de `docs/reportes/verificacion_2026-11-14.md` | Decidir qué funciones se describen | Decidida por el autor (2026-11-14): solo lo esencial. Se describen el mapeo de columnas (con los 3 datasets reales como evidencia, ver la fila REQ-13) y los intervalos de predicción del 95 % (en `metodos.tex › Modelado Predictivo`, como motivo del uso de `statsmodels`). No se describen los reportes PDF/Excel, el aislamiento multiusuario, el despliegue, la seguridad, la CI, los límites de campos ni la convención numérica. |
| 2026-11-14 | §7 | Las cuatro fases se ejecutan con un solo comando | No existe ese comando: generación, carga, `evaluate_models.py` y frontend van por separado | Crear el script del experimento con métricas fechadas | Resuelta (tarea 051, 2026-11-14): `python scripts/run_experiment.py` (desde `backend/`) genera el dataset con `generar_ventas.py` (semilla 2026), lo carga por el ETL real con el mapeo sobre SQLite en memoria, ajusta el modelo y escribe `docs/resultados/metricas_AAAA-MM-DD.json` con fecha, commit, semilla, parámetros, conteos del ETL, métricas, MAE de cada referencia, coeficientes, hipótesis y escala de Lewis. La fase 4 (frontend) la cubren las E2E de la tarea 053. Pruebas: `tests/test_run_experiment.py::test_experiment_loads_every_row_and_scores_the_model_against_the_references`, `::test_experiment_is_reproducible`, `::test_lewis_scale_bands`. |

---

## 11. Plantilla del reporte de verificación

Cada corrida de verificación debe producir `reportes/verificacion_AAAA-MM-DD.md` con este formato:

```markdown
# Reporte de verificación — AAAA-MM-DD
Commit: <hash>   Semilla del dataset: <n>   Registros: <n>

## Resumen
CUMPLE: n | NO CUMPLE: n | PARCIAL: n | NO VERIFICABLE: n | PENDIENTE: n

## Detalle
| REQ | Estado | Evidencia (archivo/prueba/salida) | Nota |
|---|---|---|---|
| REQ-01 | CUMPLE | backend/main.py · tests/test_stack.py::test_fastapi | |

## Métricas del modelo (para el Capítulo 4)
MAE: x.xx | RMSE: x.xx | Baseline MAE: x.xx (si P-01 está definido)
Coeficientes: β0=…, β1=…, β2=…, β3=…

## Discrepancias nuevas
(copiar a la sección 10)
```

---

## 12. Cuándo actualizar este documento

- Cada vez que el autor cambie la tesis en algo que afecte al sistema (stack, campos, algoritmo, métricas, objetivos).
- Cada vez que se resuelva un pendiente de la sección 9: se convierte en un `REQ` con su criterio.
- Cada vez que se cierre una discrepancia que cambió la tesis: actualiza aquí la afirmación correspondiente.

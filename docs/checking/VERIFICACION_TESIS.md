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
| 2026-11-08 | REQ-13 | Esquema exacto con `id`, `fecha`, `categoria`, `cantidad`, `precio_unitario`, `total` | Usa `id_venta`, `fecha_venta`, `monto`; no tiene `precio_unitario` ni `total` | Cambiar código o precisar el esquema real en la tesis | Abierta |
| 2026-11-08 | REQ-23 | Outliers mediante máscaras booleanas | No hay filtro de outliers | Definir criterio P-08 e implementarlo, o retirar la afirmación | Abierta |
| 2026-11-08 | REQ-24..26 | ETL convierte fecha, deriva calendario y agrupa por día/categoría | Esas operaciones no existen como pipeline ETL único | Alinear pipeline o cambiar afirmaciones | Abierta |
| 2026-11-08 | REQ-29 | Un ETL alimenta consultas y modelo | Consultas usan SQL; ML agrega sus propios datos | Centralizar la salida ETL o documentar pipelines distintos | Abierta |
| 2026-11-08 | REQ-33 | Features: tendencia, estacionalidad y lag | Usa tendencia y dummies; no usa lag | Resolver definición de features en tesis/código | Abierta |
| 2026-11-08 | REQ-36 | `train_test_split`, 70–80/20–30 | Usa holdout temporal propio | Resolver P-03 y sincronizar tesis/código | Abierta |
| 2026-11-08 | REQ-37 | MAE y RMSE con `sklearn.metrics` | Calcula RMSE, MAPE y R² con función propia; no MAE | Alinear métricas y registrar valores | Resuelta (tarea 034): `backend/app/ml_models/evaluation.py` · `point_metrics` usa `mean_absolute_error` y `root_mean_squared_error` sobre meses no vistos; prueba `backend/tests/test_evaluation.py::test_mae_and_rmse_follow_the_thesis_formulas`; MAE del modelo y de las referencias en `docs/evaluacion/resultados.md` |
| 2026-11-08 | REQ-42 | ETL y modelo asíncronos | Rutas y servicios son síncronos | Cambiar implementación o tesis | Abierta |
| 2026-11-08 | REQ-50..52 | Histórico/proyección y dos vistas arquitectónicas | Línea histórica y barras existen; falta vista combinada y nombres exactos | Completar frontend o precisar alcance | Abierta |
| 2026-11-08 | REQ-53, REQ-62 | Responsive y renderizado dinámico validado | No hay pruebas E2E ni capturas | Incorporar E2E y evidencia reproducible | Abierta |
| 2026-11-08 | REQ-61 | Métricas registradas para Capítulo 4 | API devuelve métricas; no hay archivo fechado con commit/semilla/parámetros | Definir comando único y formato de resultados | Abierta |
| 2026-11-08 | REQ-09 | Ecosistema completamente abierto | Auditoría Python no ejecutable; NPM incluye `UNLICENSED` | Auditar dependencias y resolver licencia | Abierta |
| 2026-11-08 | REQ-10/11 | Dataset sintético reproducible | XLSX usa semilla 2026; CSV alternativo usa aleatoriedad sin semilla | Elegir un generador autoritativo y documentarlo | Abierta |
| 2026-11-08 | Frontend | El frontend está disponible como parte del sistema | `AGENTS.md` lo declara planning-only, pero existen fuente React, tests y build funcional | Corregir documentación de alcance o declarar el estado real | Abierta |

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

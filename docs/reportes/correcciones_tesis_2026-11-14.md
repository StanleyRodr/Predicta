# Correcciones de la tesis — 2026-11-14

**Tesis:** Dashboard web de inteligencia de negocios con analítica descriptiva y predictiva para PyMEs del sector retail (sistema «Predicta»).
**Destino:** el proyecto LaTeX de Overleaf (capítulos 1, 2 y 3, y los datos para el capítulo 4).
**Código verificado:** commit `cc8e9dd` del repositorio de Predicta, con todas sus pruebas en verde.

---

## 0. Cómo usar este documento

Este es el **documento principal**. Llega junto con otros dos que solo sirven como respaldo:

- `VERIFICACION_TESIS.md`: lista cada afirmación de la tesis sobre el sistema (REQ-xx) y registra cada diferencia con el código y la decisión del autor (sección 10).
- `verificacion_2026-11-14.md`: el reporte de verificación, con la evidencia de cada REQ (archivos, pruebas y salidas de comandos).

Reglas para editar el LaTeX:

1. **Este documento manda.** Si un dato de los otros dos no coincide con este, usa el de aquí: es posterior.
2. **El código ya es definitivo.** Cada corrección cambia la tesis para describir lo que hace el sistema. No propongas cambios al sistema.
3. **No inventes datos.** Usa solo las cifras de este documento. Si una sección necesita un dato que no aparece aquí, márcalo con `\todo{}` (o un comentario `% TODO`) en lugar de suponerlo.
4. **Conserva el estilo de la tesis:** tercera persona, tiempo verbal y formato de citas del documento original.
5. Los textos propuestos son una base. Ajústalos al párrafo donde van, pero conserva cada dato y cada matiz técnico.
6. Antes de entregar, revisa la lista de la sección 9 («Puntos que el autor debe confirmar»).

Las ubicaciones se dan como `archivo.tex › Sección`, porque los números de línea cambian.

---

## 1. Stack tecnológico y motor predictivo

### 1.1 Statsmodels ajusta el modelo; Scikit-Learn calcula las métricas

**Ubicación:** `metodos.tex › Herramientas y Bibliotecas Especializadas`, `metodos.tex › Scikit-Learn`, `metodos.tex › Modelado Predictivo`, y cada mención del stack en `intro.tex › Justificación`, `intro.tex › Objetivos › Específicos` y `arte.tex › 2.1.4 y 2.1.5`.

**Dice hoy:** el motor predictivo es la Regresión Lineal Múltiple de `sklearn.linear_model` (Scikit-Learn) y Scikit-Learn se usa para el entrenamiento y las métricas.

**Debe decir:** la Regresión Lineal Múltiple se estima por Mínimos Cuadrados Ordinarios (OLS) con la biblioteca **statsmodels** (`statsmodels.OLS`), porque, además de los coeficientes, entrega **intervalos de predicción del 95 %** que se ensanchan a medida que la proyección se aleja de los datos, junto con los errores estándar y los valores p de cada coeficiente. **Scikit-Learn** se usa para calcular el MAE y el RMSE (`sklearn.metrics.mean_absolute_error` y `root_mean_squared_error`). Pandas agrega los datos y NumPy hace el cálculo numérico.

**Texto propuesto:**

> El modelo de Regresión Lineal Múltiple se estima mediante Mínimos Cuadrados Ordinarios con la biblioteca statsmodels, que, además de los coeficientes, proporciona intervalos de predicción del 95 % para cada mes proyectado, junto con los errores estándar y la significancia de cada coeficiente. Las métricas de error MAE y RMSE se calculan con el módulo `sklearn.metrics` de Scikit-Learn sobre meses que el modelo no utilizó para su ajuste.

**Nota:** el método no cambia. Scikit-Learn (`LinearRegression`) y statsmodels (`OLS`) resuelven el mismo problema de mínimos cuadrados y dan los mismos coeficientes. La diferencia es que statsmodels ofrece la inferencia estadística: los intervalos de predicción.

### 1.2 Procesamiento asíncrono

**Ubicación:** `intro.tex › Justificación`, `arte.tex › 2.1.4` y `metodos.tex › Validación e Integración del Sistema`.

**Dice hoy:** FastAPI funciona como «núcleo de procesamiento asíncrono» y el ETL y el ajuste del modelo se ejecutan de forma asíncrona.

**Debe decir:** FastAPI corre sobre un servidor ASGI asíncrono. Las tareas bloqueantes (el ETL con Pandas, el ajuste del modelo y el acceso a PostgreSQL) se ejecutan en hilos de trabajo, y el envío de correos se hace en segundo plano. Así, una operación larga no bloquea a los demás usuarios, aunque su latencia aumenta mientras dura.

**Texto propuesto:**

> FastAPI, sobre un servidor ASGI asíncrono, atiende las solicitudes de forma concurrente: el ETL y el ajuste del modelo, que son tareas bloqueantes, se ejecutan en hilos de trabajo, y el envío de correos, en segundo plano, de modo que una operación larga no bloquea al resto de usuarios, aunque la latencia de las demás solicitudes aumenta mientras dura la operación.

**Evidencia medida** (sección 8.6): durante la carga de un archivo de 28,667 ventas (12.5 s), otro usuario siguió recibiendo respuestas, con una mediana de 365.8 ms frente a 6.2 ms en reposo, y ninguna solicitud esperó a que terminara la carga.

**No menciones** el número de procesos (*workers*) del servidor: es una decisión del autor.

### 1.3 Licencia del proyecto

**Ubicación:** donde la tesis argumenta que el ecosistema es de código abierto (PE3; `intro.tex › Preguntas Específicas` y la sección que la responda).

**Agregar:** el código de Predicta se publica bajo la **licencia MIT**, y todas sus dependencias son de código abierto: MIT, BSD, Apache-2.0, PSF, MPL-2.0 y LGPL en el caso de `psycopg2` y `fpdf2`, que se usan como bibliotecas sin modificar. No se usa ningún software de BI privativo.

---

## 2. Dataset y esquema de datos

### 2.1 Generación del dataset sintético

**Ubicación:** `metodos.tex › Selección y Estructura de Datos`.

**Datos para la tesis:**

| Parámetro | Valor |
|---|---|
| Script | `DatosDePrueba/ventas_fabricadas/generar_ventas.py` (Python, NumPy y Pandas) |
| Semilla aleatoria | 2026 (la misma semilla reproduce exactamente las mismas filas) |
| Periodo | del 2024-11-01 al 2026-10-31 (24 meses completos) |
| Registros (líneas de venta) | 28,667 |
| Ventas totales | $2,230,833.83 |
| Categorías | Abarrotes, Bebidas, Cuidado Personal, Limpieza, Lácteos |
| Columnas generadas | `producto`, `monto` (total de la línea), `cantidad`, `categoria`, `fecha` (con hora) |
| Patrones simulados | ritmo de la semana, días de pago, estacionalidad mensual y de fiestas por categoría, crecimiento no lineal con una caída intermedia y recuperación, inflación gradual, choques aleatorios y días cerrados |
| Formato | XLSX (una hoja, `ventas`) |

### 2.2 Esquema real

**Dice hoy:** el esquema tiene exactamente `id`, `fecha`, `categoria`, `cantidad` (entero), `precio_unitario` y `total`.

**Debe decir:** el esquema de la tabla `ventas` en PostgreSQL es el siguiente.

| Campo | Tipo | Equivalencia con la versión anterior |
|---|---|---|
| `id_venta` | Entero, clave primaria | `id` |
| `id_usuario` | Entero, clave foránea a `usuarios` | nuevo: cada PyME (usuario) solo ve sus propios datos |
| `producto` | Texto (hasta 150 caracteres) | nuevo |
| `categoria` | Texto (hasta 100 caracteres), categórica | igual |
| `cantidad` | Decimal (10,2), ≥ 0 | era entero; es decimal para admitir kilos o litros |
| `monto` | Decimal (10,2), > 0, en moneda local | `total` |
| `fecha_venta` | Fecha ISO `AAAA-MM-DD` | `fecha` |

`precio_unitario` **no se guarda**: es una entrada opcional. Si el archivo trae precio unitario y cantidad, pero no monto, el sistema calcula `monto = precio_unitario × cantidad`, redondeado a 2 decimales.

**Agregar al final de la sección** una frase que remita al mapeo de columnas:

> El esquema interno es fijo; los archivos con otros nombres de columna se adaptan a él mediante el mapeo de columnas descrito en la sección de extracción del ETL.

---

## 3. Pipeline ETL

### 3.1 Extracción y mapeo de columnas (función nueva)

**Ubicación:** `metodos.tex › Pandas (Ingeniería de Datos y Tubería ETL)`, en la parte de extracción.

**Agregar:**

- El sistema acepta archivos CSV (detecta `,`, `;` o tabulador; UTF-8 con respaldo cp1252), XLSX (primera hoja) y SQL. Del SQL solo analiza las sentencias `INSERT … VALUES`: nunca lo ejecuta.
- **Mapeo de columnas:** antes de cargar, el sistema lee los encabezados y propone a qué rol corresponde cada columna. Los roles son `producto`, `categoria`, `monto`, `precio_unitario`, `cantidad` y `fecha`.
- **Cómo se propone el mapeo:** por nombre exacto o por un diccionario de sinónimos en español e inglés. No usa coincidencias aproximadas: se compara el encabezado sin acentos, mayúsculas ni signos.
- **Revisión:** el usuario revisa la propuesta antes de cargar, viendo una muestra de 5 filas.
- **Sinónimos de ejemplo** (tabla breve para la tesis):

| Rol | Algunos sinónimos aceptados |
|---|---|
| producto | product, item, artículo, descripción, description, title |
| categoría | category, rubro, familia, departamento, category_name |
| monto | total, importe, ventas, amount, sales_dollars |
| precio unitario | precio, pu, valor unitario, unit_price, price |
| cantidad | unidades, qty, quantity, piezas, sales_bottles |
| fecha | fecha de venta, date, fecha de emisión, invoicedate, order_date |

- **Evidencia con datos reales:** el mapeo se probó con los encabezados de tres datasets públicos de comercio: Online Retail II (UCI), Iowa Liquor Sales y Open e-commerce 1.0 (Amazon). Para los tres propone los roles correctos.
- **Carga de varios archivos:** se pueden subir hasta 50 archivos a la vez. Los archivos con los mismos encabezados comparten un único mapeo revisado.

### 3.2 Transformación y limpieza (arquitectura real)

**Ubicación:** `metodos.tex › Pandas (Ingeniería de Datos y Tubería ETL)` y `metodos.tex › Preprocesamiento e Ingeniería de Características (ETL)`.

**Dice hoy:**
- se eliminan los `NaN` con Pandas;
- se derivan el día de la semana, el mes y la semana del año;
- se agrupa por día y categoría con `groupby`;
- un único ETL alimenta las consultas y el modelo.

**Debe decir (texto propuesto):**

> Extracción: el archivo (CSV, XLSX o SQL) se lee y sus columnas se asignan a los roles del sistema mediante el mapeo. Transformación y limpieza: cada registro se valida de forma individual; se rechazan los que tienen la fecha o el monto ausentes o inválidos, cantidades negativas o caracteres de control, y se informa el número de fila de cada rechazo, sin sustituir valores faltantes por ceros ni por la fecha actual. Las categorías se estandarizan sin distinguir mayúsculas, espacios ni acentos, y los nombres de producto se normalizan (espacios simples y mayúscula inicial en cada palabra). Carga: los registros válidos se guardan en PostgreSQL en una sola transacción, y un archivo idéntico ya cargado se rechaza mediante su huella SHA-256. El ETL alimenta una única tabla de ventas: las consultas descriptivas del dashboard la agregan en SQL, y el motor predictivo la agrega por mes con Pandas, que convierte la fecha a `datetime64` y ordena la serie cronológicamente.

**Retirar:** la eliminación de `NaN` con `dropna`, la semana del año y el `groupby` por día y categoría con Pandas.

### 3.3 Valores atípicos

**Ubicación:** `metodos.tex › Preprocesamiento e Ingeniería de Características (ETL)`.

**Dice hoy:** los valores atípicos se imputan o eliminan mediante máscaras booleanas.

**Retirar esa afirmación y poner (texto propuesto):**

> No se eliminan ni se imputan valores atípicos: en ventas minoristas un valor extremo suele ser real (temporadas, promociones), y eliminarlo sesgaría la estacionalidad que se busca modelar. La limpieza se limita a rechazar registros inválidos: montos no positivos, cantidades negativas y fechas inválidas.

---

## 4. Modelo predictivo

### 4.1 Variable objetivo

**Ubicación:** `metodos.tex › Modelado Predictivo`.

**Dice hoy:** Y es «la cantidad o el monto total de ventas».

**Texto propuesto:**

> La variable objetivo principal es el monto total de ventas del mes; con las mismas variables explicativas se ajusta un segundo modelo para la cantidad de unidades. La hipótesis y los resultados se evalúan sobre el monto.

### 4.2 Variables explicativas

**Ubicación:** `metodos.tex › Modelado Predictivo` y `arte.tex › 2.1.3.4 Regresión Lineal Múltiple`.

**Dice hoy:** X1 es la tendencia, X2 la estacionalidad y X3 el promedio de ventas del periodo anterior (*lag*).

**Texto propuesto:**

> Las variables explicativas son X1, el índice de tendencia (meses de calendario transcurridos desde el primer mes con ventas), y X2, la estacionalidad, codificada como 11 variables indicadoras del mes con enero como referencia. X2 se incorpora solo cuando el historial tiene al menos 36 meses completos con los 12 meses del calendario observados; con menos, el modelo usa solo la tendencia, porque con 24 meses la especificación estacional perdió frente al pronóstico ingenuo estacional en 4 de 6 horizontes del backtest. No se usa un rezago (*lag*), porque proyectar 12 meses con él exige una predicción recursiva que invalida los intervalos de predicción.

**Regla escalonada completa** (útil como tabla):

| Meses completos de historial | Especificación | Horizonte proyectado |
|---|---|---|
| Menos de 6 | No se proyecta (se informa cuántos meses faltan) | — |
| De 6 a 23 | Solo tendencia | La mitad de los meses (3 a 11) |
| De 24 a 35 | Solo tendencia | 12 meses |
| 36 o más, con los 12 meses observados | Tendencia + 11 indicadoras de mes | 12 meses |

Otras reglas que conviene mencionar:
- Desde el séptimo mes proyectado, la proyección se marca como **extrapolación sin validar**.
- Un último mes incompleto **no entra en el ajuste**: se proyecta primero.
- Los meses sin ventas **no se rellenan con cero**.

### 4.3 Ecuación con los coeficientes estimados

**Ubicación:** `metodos.tex › Modelado Predictivo` (o el capítulo 4).

Con el dataset de la tesis (24 meses), el modelo aplicado es solo de tendencia:

`Ŷ = β0 + β1·X1`

| Objetivo | Variable | Coeficiente | Error estándar | Valor p |
|---|---|---|---|---|
| Monto | β0 (intercepto) | 76,512.59 | 7,429.93 | < 0.0001 |
| Monto | β1 (`mes_indice`) | 1,429.46 | 553.54 | 0.0170 |
| Cantidad | β0 (intercepto) | 2,277.94 | 202.45 | < 0.0001 |
| Cantidad | β1 (`mes_indice`) | 29.16 | 15.08 | 0.0662 |

R² dentro de la muestra: 0.2326 para el monto y 0.1452 para la cantidad.

**Interpretación:** las ventas crecen en promedio unos $1,429 por mes. La pendiente del monto es significativa al 5 %; la de la cantidad no lo es (p = 0.066). El R² dentro de la muestra es bajo porque la serie tiene estacionalidad y choques que una recta no captura. Lo que mide la precisión es el error fuera de la muestra (sección 8).

### 4.4 División de los datos y validación

**Ubicación:** `metodos.tex › Modelado Predictivo` y `metodos.tex › Definición del Experimento`.

**Dice hoy:** `train_test_split` con 70–80 % de entrenamiento y 20–30 % de prueba.

**Texto propuesto:**

> La validación usa un esquema de origen móvil (*rolling origin*), equivalente a `TimeSeriesSplit` de Scikit-Learn: el modelo se reentrena con los datos hasta cada uno de los últimos 6 meses y predice el mes siguiente, que no vio. El modelo diario reserva el 20 % final de los días en orden cronológico. No se usa una partición aleatoria (`train_test_split`), porque mezclaría observaciones futuras en el entrenamiento.

### 4.5 Métricas, métodos de referencia y umbral

**Ubicación:** `intro.tex › Hipótesis`, `intro.tex › Objetivos › Específico 5` y `metodos.tex › Definición del Experimento`.

**Dice hoy:** la hipótesis compara contra «métodos empíricos tradicionales» sin definirlos, y el OE5 pide un «margen tolerable» sin número.

**Texto propuesto:**

> Los métodos empíricos de referencia son tres pronósticos simples: último valor, mismo mes del año anterior y promedio móvil de 3 meses. La hipótesis se acepta si el WAPE de la regresión en el horizonte de un mes es menor que el de la mejor de las tres referencias. La precisión se califica además con la escala de Lewis (1982) sobre el MAPE: menor de 10 %, muy precisa; de 10 a 20 %, buena; de 20 a 50 %, razonable; mayor de 50 %, imprecisa. MAE y RMSE se reportan en pesos como magnitud del error.

**Fórmulas** (ya están en la tesis; agregar las dos nuevas):
- MAE = (1/n)Σ|yᵢ − ŷᵢ|.
- RMSE = √((1/n)Σ(yᵢ − ŷᵢ)²).
- **WAPE** = Σ|yᵢ − ŷᵢ| / Σ|yᵢ| × 100: error total sobre ventas totales, que no depende del tamaño de la tienda.
- **MAPE** = (100/n)Σ|yᵢ − ŷᵢ|/|yᵢ|.

**Referencia bibliográfica:** Lewis, C. D. (1982). *Industrial and Business Forecasting Methods*. Butterworths. Ver la sección 9.

---

## 5. KPI del dashboard

**Ubicación:** `intro.tex › Objetivos › Específico 1` y la sección de diseño del dashboard.

**Dice hoy:** el OE1 promete analizar los KPI, pero no los lista.

**KPI oficiales:**

| KPI | Definición |
|---|---|
| Ingresos totales | Suma del monto de las ventas del rango de fechas elegido |
| Operaciones | Número de ventas registradas en el rango |
| Ticket promedio | Ingresos totales ÷ operaciones. **Precisión:** es el valor promedio por operación (línea de venta), porque los datos no traen un número de ticket que agrupe varios productos de una misma compra |
| Crecimiento mensual | Variación % de los ingresos del último mes completo del rango frente al mes anterior y frente al mismo mes del año anterior. Sin un mes completo, el tablero muestra «Sin datos suficientes» |

**Indicador descriptivo complementario** (no es KPI): la venta más alta del rango.

Todos los indicadores se recalculan con el filtro de fechas del tablero. Con el dataset completo valen:

| Indicador | Valor |
|---|---|
| Ingresos totales | $2,230,833.83 |
| Operaciones | 28,667 |
| Ticket promedio | $77.82 |
| Venta más alta | $555.67 |
| Crecimiento mensual (octubre 2026) | +14.12 % frente a septiembre y +18.78 % frente a octubre 2025 |

El dashboard tiene además gráficas de años superpuestos, comparación entre categorías, ingresos por categoría (barras), totales mensuales, detalle diario e historial completo.

---

## 6. Vistas del dashboard (figura de arquitectura)

**Ubicación:** la figura `fig:arquitectura_resultados` y su descripción en el texto.

**Dice hoy:** las vistas se llaman «Proyección Global» y «Análisis por Categoría».

**Debe decir:** se cambia la figura para usar los nombres reales de la interfaz.

- **Dashboard («Tu operación en una mirada»):** analítica descriptiva, con las vistas «General», «Por categoría», «Por mes» e «Historial completo» y las tarjetas de KPI.
- **Predicciones («Siguiente movimiento»):** analítica predictiva. Proyecta 12 meses del total de ventas, de una categoría o de un producto, en una gráfica de líneas: historial con línea continua, proyección con línea discontinua y banda del intervalo del 95 %. Muestra también la tabla de meses proyectados, las métricas de calidad y la predicción del día siguiente. Las proyecciones se pueden guardar.
- **Reportes:** descarga en Excel (historial) y en PDF (historial, proyección anual, mes futuro frente a su historial y proyección por categoría).

---

## 7. Experimento de validación (capítulo 3)

**Ubicación:** `metodos.tex › Definición del Experimento` y `metodos.tex › Ejecución del Experimento`.

Cada uno de los tres escenarios ya es una **prueba automatizada** que se puede volver a ejecutar:

| Escenario de la tesis | Prueba que lo valida | Resultado |
|---|---|---|
| Comunicación de datos: DataFrame → JSON sin pérdida ni errores | `test_serializacion_json` (pytest): compara cada periodo, monto, cantidad e intervalo del JSON con el DataFrame de origen, también a través de la API | Aprobada |
| Precisión algorítmica: MAE y RMSE | Comando único del experimento (`run_experiment.py`), que registra los resultados en un archivo JSON con fecha, commit y semilla | Hipótesis cumplida (sección 8.1) |
| Renderizado dinámico con Chart.js | Pruebas E2E con Playwright en Chrome, contra la API real y el build de producción: gráfica de líneas de la proyección, barras por categoría, actualización sin recargar la página, diseño sin *scroll* horizontal a 375 y 1440 px, y ningún error en la consola | 8 de 8 aprobadas |

**Ejecución del experimento** (texto propuesto):

> El experimento se ejecuta con un solo comando que genera el dataset sintético con la semilla 2026, lo carga a través del ETL real del sistema, ajusta el modelo y registra en un archivo con fecha las métricas, los coeficientes, el resultado de la hipótesis y la versión del código. La fase de visualización se valida con pruebas de extremo a extremo en un navegador real.

**Otras cifras de calidad del software** (opcionales):
- 501 pruebas automatizadas del backend, con 97 % de cobertura de código.
- 270 pruebas unitarias del frontend y 8 pruebas de extremo a extremo.
- Integración continua en cada cambio: análisis estático, tipos, migraciones, pruebas sobre SQLite y PostgreSQL 17, auditoría de vulnerabilidades y búsqueda de secretos.

---

## 8. Datos para el capítulo 4 (Resultados)

Fuente: `docs/resultados/metricas_2026-11-14.json` (commit `cc8e9dd`, semilla 2026) y `docs/evaluacion/resultados.md`.

### 8.1 Hipótesis: monto, un mes adelante (6 meses no vistos)

| Método | MAE ($) | RMSE ($) | WAPE (%) | MAPE (%) |
|---|---|---|---|---|
| **Regresión lineal múltiple** | **9,987.74** | **13,418.30** | **9.32** | **9.29** |
| Promedio móvil de 3 meses (mejor referencia) | 11,150.85 | 17,314.60 | 10.41 | 9.90 |
| Mismo mes del año anterior | 12,472.57 | 13,886.06 | 11.64 | 11.56 |
| Último valor | 14,402.71 | 16,350.29 | 13.44 | 13.63 |

- **Resultado: la hipótesis se cumple.** El WAPE de la regresión (9.32 %) es menor que el de la mejor referencia (10.41 %): una mejora del 10.43 %.
- La regresión tiene también el menor MAE y el menor RMSE de los cuatro métodos.
- **Escala de Lewis:** MAPE de 9.29 %, «muy precisa».
- MASE = 0.49: la mitad del error del pronóstico ingenuo.

### 8.2 Cantidad (variable secundaria)

| Método | MAE (unidades) | RMSE | WAPE (%) | MAPE (%) |
|---|---|---|---|---|
| Regresión lineal múltiple | 281.29 | 368.23 | 9.70 | 9.72 |
| Mismo mes del año anterior (mejor referencia) | 258.83 | 297.14 | 8.92 | 8.87 |
| Promedio móvil de 3 meses | 301.00 | 462.07 | 10.38 | 9.84 |
| Último valor | 385.83 | 451.29 | 13.30 | 13.42 |

En cantidad, la regresión **pierde** contra «mismo mes del año anterior»: su WAPE es 8.68 % peor. Sigue siendo «muy precisa» en la escala de Lewis (MAPE de 9.72 %). Reportarlo con honestidad es parte de la validez del resultado.

### 8.3 Error según qué tan lejos se proyecta (backtest, monto)

WAPE (%) de la regresión aplicada por el sistema frente a las referencias, entrenando con los primeros 18 meses:

| Horizonte (meses adelante) | Regresión | Último valor | Mismo mes año anterior | Promedio móvil 3 |
|---|---|---|---|---|
| 1 | 9.32 | 13.44 | 11.64 | 10.41 |
| 2 | 6.54 | 10.27 | 10.38 | 7.23 |
| 3 | 7.37 | 6.34 | 9.04 | 11.47 |
| 4 | 11.58 | 13.93 | 9.60 | 14.82 |
| 5 | 12.95 | 17.64 | 13.46 | 3.76 |
| 6 | 3.40 | 0.46 | 15.81 | 16.91 |

- La regresión gana a la mejor referencia en los horizontes 1 y 2. En los horizontes 3 a 6 alguna referencia la supera.
- Gana al «mismo mes del año anterior» en 5 de 6 horizontes.
- Los horizontes lejanos tienen pocos puntos de evaluación: el horizonte 6 tiene uno solo.
- Desde el mes 7, la proyección es extrapolación sin validar.

### 8.4 Calidad del ajuste

- **Diagnóstico de residuos** del modelo final: Ljung–Box p = 0.3455 (3 rezagos) y p = 0.4476 (6 rezagos), sin autocorrelación; Breusch–Pagan p = 0.2701, varianza constante. Ninguna prueba es significativa al 5 %.
- **Cobertura del intervalo del 95 %** en el backtest: 100 % en los horizontes 1 a 6. Todos los meses reales cayeron dentro del intervalo.

### 8.5 Calidad de los datos (PE1)

- Carga del dataset completo: **28,667 filas leídas, 28,667 cargadas y 0 rechazadas**.
- El dataset no tiene nulos ni filas duplicadas.
- Con archivos que sí traen errores, cada fila inválida se rechaza con su número de fila y su motivo, y no se rellena con valores inventados.

### 8.6 Rendimiento y concurrencia

Medición en local: uvicorn y PostgreSQL en la misma máquina, sin latencia de red. La tesis no fija una latencia máxima, así que estos valores se reportan sin aprobar ni reprobar.

| Situación | Solicitudes | Mediana (ms) | Percentil 95 (ms) | Máximo (ms) |
|---|---|---|---|---|
| Otro usuario consulta los KPI, en reposo | 30 | 6.2 | 9.1 | 9.5 |
| El mismo, mientras se cargan 28,667 ventas (12.5 s) | 17 | 365.8 | 517.0 | 536.5 |

Conclusión: **una carga larga no bloquea a los demás usuarios**. Su latencia sube de milisegundos a décimas de segundo mientras dura la carga, porque comparten la CPU.

### 8.7 Validación visual

Las capturas del dashboard y de las predicciones a 375 px (celular) y 1440 px (escritorio) están en `docs/evaluacion/capturas/`. Se generaron con las pruebas E2E y sirven como figuras de la tesis.

### 8.8 Comparación de costos (PE3)

Costo mensual en USD de licencias y hosting. Precios oficiales consultados el 2026-11-14; tipo de cambio FIX de 18.5525 MXN por USD (Banco de México, 13/11/2026).

| Usuarios | Power BI Pro | Tableau Standard (1 Creator + Viewers) | Predicta (planes actuales) | Predicta (uso comercial) |
|---|---|---|---|---|
| 1 | 14.00 (MXN 259.73) | 75.00 (MXN 1,391.44) | 5.00 (MXN 92.76) | 25.00 (MXN 463.81) |
| 5 | 70.00 (MXN 1,298.67) | 135.00 (MXN 2,504.59) | 5.00 (MXN 92.76) | 25.00 (MXN 463.81) |
| 10 | 140.00 (MXN 2,597.35) | 210.00 (MXN 3,896.02) | 5.00 (MXN 92.76) | 25.00 (MXN 463.81) |

Supuestos de la tabla:
- **Power BI:** Pro cuesta US$14 por usuario al mes con pago anual, y hace falta para publicar y compartir reportes. Power BI Desktop es gratuito, pero sin compartir.
- **Tableau:** Creator US$75 y Viewer US$15 por usuario al mes, con pago anual.
- **Predicta:** $0 en licencias, más el hosting.
  - Con los planes actuales: Railway Hobby (US$5 al mes); Vercel Hobby, Neon Free y Brevo Free son gratuitos.
  - Con uso comercial: Vercel Hobby es solo para uso no comercial, así que una PyME necesitaría Vercel Pro (US$20 al mes) u otro hosting que permita uso comercial.
- El costo de Predicta **no crece con el número de usuarios**.
- No incluye impuestos, implementación ni capacitación.

**Lectura para la PE3:**
- Con 5 usuarios, Power BI cuesta entre 2.8 y 14 veces más que Predicta, y Tableau entre 5.4 y 27 veces más.
- Con 10 usuarios, la diferencia crece, porque las licencias privativas se cobran por persona.

Detalle y fuentes con URL: `docs/costos/comparacion.md` del repositorio.

---

## 9. Puntos que el autor debe confirmar antes de entregar

1. **La cita de Lewis (1982):** verificar en la fuente original la referencia completa y los límites de la escala (10 %, 20 % y 50 %).
2. **El tipo de cambio:** el FIX de 18.5525 se tomó de fuentes de prensa que citan a Banco de México, porque la página de Banxico no devolvió el valor. Confirmarlo en https://www.banxico.org.mx o en el DOF.
3. **Los precios de Power BI, Tableau y Vercel:** cambian con frecuencia y por región. Revisarlos cerca de la fecha de defensa.
4. **Los datos son sintéticos:** las métricas muestran que el método funciona, no su desempeño en una tienda real. Conviene decirlo explícitamente en las limitaciones del capítulo 4.
5. **La latencia es una medición local:** en producción hay que sumar la latencia de red.

---

## 10. Resumen de cambios por archivo

| Archivo › Sección | Cambio | Detalle |
|---|---|---|
| `intro.tex › Justificación` | statsmodels + Scikit-Learn; redacción de lo asíncrono | 1.1, 1.2 |
| `intro.tex › Objetivos › Específico 1` | Lista de KPI | 5 |
| `intro.tex › Objetivos › Específico 5` | Umbral: mejor referencia + escala de Lewis | 4.5 |
| `intro.tex › Hipótesis` | Definir los métodos empíricos de referencia | 4.5 |
| `intro.tex › Preguntas Específicas` (PE3) | Licencia MIT; tabla de costos | 1.3, 8.8 |
| `arte.tex › 2.1.3.4 Regresión Lineal Múltiple` | Variables X1 y X2, sin *lag*; intervalos | 4.2 |
| `arte.tex › 2.1.4 y 2.1.5` | statsmodels; ASGI e hilos de trabajo | 1.1, 1.2 |
| `metodos.tex › Herramientas y Bibliotecas Especializadas` | Agregar statsmodels (y Playwright para la validación) | 1.1, 7 |
| `metodos.tex › Selección y Estructura de Datos` | Parámetros del generador; esquema real; referencia al mapeo | 2.1, 2.2 |
| `metodos.tex › Pandas (Ingeniería de Datos y Tubería ETL)` | Mapeo de columnas con datasets reales; ETL real | 3.1, 3.2 |
| `metodos.tex › Preprocesamiento e Ingeniería de Características (ETL)` | Validación por fila; sin atípicos | 3.2, 3.3 |
| `metodos.tex › Scikit-Learn` | Rol: métricas MAE y RMSE | 1.1 |
| `metodos.tex › Modelado Predictivo` | Y principal; variables; ecuación y coeficientes; origen móvil | 4.1–4.4 |
| `metodos.tex › Validación e Integración del Sistema` | Redacción de lo asíncrono con la medición | 1.2, 8.6 |
| Figura `fig:arquitectura_resultados` | Nombres reales de las vistas | 6 |
| `metodos.tex › Definición del Experimento` y `› Ejecución del Experimento` | Escenarios como pruebas automatizadas; comando único; baseline y umbral | 7, 4.5 |
| Capítulo 4 (Resultados) | Métricas, backtest, residuos, calidad de datos, concurrencia, capturas y costos | 8 |

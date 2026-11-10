# Plan 036: Pruebas con datasets reales de e-commerce

## Estado

- **Estado:** HECHO. Resultados en `docs/pruebas/036-datos-reales.md`.
- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** LOW (cambia solo `SYNONYMS`; el resto son datos locales fuera de git, un script y documentación)
- **Depende de:** `docs/planning/plans/035-mapeo-columnas.md`, que introduce `POST /etl/analizar-columnas` y el `mapeo` en la carga.
- **Categoría:** backend / pruebas / documentación
- **Origen:** pedido del usuario del 2026-11-10
- **Planificado en:** commit `bf0c7c7`, 2026-11-10

## Objetivo

El mapeo de columnas (035) solo se probó con datos generados por
`backend/scripts/generate_dataset.py`. Esta tarea lo prueba con ventas reales
de tiendas en línea y comprueba dos cosas:

1. El mapeo propone las columnas que el sistema necesita: producto,
   categoría, monto o precio unitario, cantidad y fecha.
2. El historial y la proyección continúan cuando se cargan varios archivos de
   la misma empresa, por ejemplo 2024 y después 2025. El dashboard y
   `/analytics/forecast` usan las ventas de todas las cargas, no solo las de
   la última.

**Nada se descarga ni se implementa hasta que el usuario apruebe cada dataset
(paso 1).**

## Decisiones

- **Autorización por dataset:** el usuario marca cada dataset de la tabla como aprobado o rechazado. Solo se descargan los aprobados.
- **Mínimo 1 año:** se descartan los datasets que cubren menos de 12 meses o que no tienen una fecha por venta. Se prefieren los que traen varios años o varios archivos de la misma empresa, para probar la continuación.
- **Sinónimos en esta tarea:** se agregan a `SYNONYMS` (`backend/app/services/column_mapping.py`) los encabezados en inglés de los datasets aprobados que hoy no se proponen. Cada uno lleva su test.
- **Script versionado:** `backend/scripts/prepare_real_dataset.py` convierte los archivos descargados en CSV listos para subir. Se descartaron los comandos sueltos porque no permiten repetir la prueba.
- **Datos fuera de git:** las descargas y los CSV preparados quedan en `backend/temp_data/`, que ya está en `.gitignore`. Nunca se versiona un dato real.
- **Sin datos de personas:** el script quita las columnas que identifican a una persona (`Customer ID` en Online Retail II y `Survey ResponseID` en Amazon). Los demás encabezados se conservan tal como vienen.
- **Sin limpiar filas:** el script divide y une archivos, pero no borra filas inválidas. Las devoluciones, los precios en 0 y las fechas vacías tienen que aparecer como filas rechazadas, porque eso también es parte de la prueba.
- **Una cuenta por empresa:** cada dataset se carga en su propia cuenta de prueba, para que los historiales no se mezclen.
- **Resultados:** van en `docs/pruebas/036-datos-reales.md`, sin datos de clientes.
- **Numeración:** la descarga del XLSX estandarizado, que la 035 había pasado a la 036, pasa a la tarea 037.

## Datasets propuestos

Las cifras salen de las fichas públicas de cada fuente. El paso 1 las vuelve a
comprobar antes de descargar.

### Sin inicio de sesión

| # | Dataset | Fuente y licencia | Tamaño | Periodo | Columnas útiles | Continuación entre archivos |
|---|---|---|---|---|---|---|
| 1 | **Online Retail II**: tienda en línea del Reino Unido que vende regalos | Repositorio UCI, dataset 502 (`archive.ics.uci.edu/dataset/502`). CC BY 4.0. Autor: Daqing Chen. | 1,067,371 filas en un xlsx de 43.5 MB | 2009-12-01 a 2011-12-09 | `Invoice`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `Price`, `Customer ID`, `Country`. No trae categoría. | Dos años de la misma empresa. El libro trae, por confirmar, una hoja por año. Se divide en archivos trimestrales de 200,000 filas o menos. |
| 2 | **Iowa Liquor Sales**: compras de cada tienda con licencia de Iowa a la división estatal de bebidas | Iowa Data Hub (data.iowa.gov) y catalog.data.gov. Hay un dataset por año, por ejemplo el 2024 es el 1261. CC BY 4.0. | 35,287,731 filas en total; 2,590,975 solo en 2024. Se filtra una sola tienda (`store_no`). | 2012-01-03 a 2026-10-30 | `ordered_on`, `im_desc`, `category_name`, `sales_bottles`, `sales_dollars` | Un archivo por año de la misma tienda, por ejemplo 2023, 2024 y 2025. Es el caso "2024 + 2025" del pedido. |
| 3 | **Open e-commerce 1.0**: historiales reales de compras en Amazon EE. UU. | Harvard Dataverse, DOI `10.7910/DVN/YGLYDY`. Artículo: Berke et al., *Scientific Data*, 2024. Se reporta que su gasto se correlaciona con las ventas públicas de Amazon (r = 0.978). | Más de 1.8 millones de compras de 5,027 personas | 2018 a 2022 | `Order Date`, `Title`, `Category`, `Quantity`, `Purchase Price Per Unit`, `ASIN/ISBN (Product Code)` | Un año por archivo, dividido en semestres para respetar el límite de filas |

### Con inicio de sesión (Kaggle)

| # | Dataset | Fuente y licencia | Tamaño | Periodo | Columnas útiles | Continuación entre archivos |
|---|---|---|---|---|---|---|
| 4 | **Olist**: marketplace de Brasil | Kaggle `olistbr/brazilian-ecommerce`. CC BY-NC-SA 4.0, por confirmar. | Unos 100,000 pedidos en 9 CSV relacionados | 2016-09 a 2018-10 | `price` (de `order_items`), `order_purchase_timestamp` (de `orders`), `product_category_name_english` (de la tabla de traducción). El producto es solo `product_id`, sin nombre. | El script une las tablas y divide por año (2017 y 2018; 2016 tiene pocos meses) |
| 5 | **Sales Product Data 2019**: tienda de electrónica de EE. UU. | Kaggle `knightbearr/sales-product-data` | ~186,000 filas en 12 CSV mensuales | 2019 completo | `Product`, `Quantity Ordered`, `Price Each`, `Order Date` | Doce archivos del mismo año: la prueba de continuación más fina. **Advertencia:** viene de un tutorial y puede ser un dataset generado. |
| 6 | **Superstore**: tienda minorista de EE. UU. | Kaggle `vivek468/superstore-dataset-final` | 9,994 filas | 2014 a 2017 | `Order Date`, `Product Name`, `Category`, `Sales`, `Quantity` | Un solo archivo. **Advertencia:** es la muestra de Tableau de una tienda ficticia. |

### Descartados

| Dataset | Motivo |
|---|---|
| Amazon Sale Report (India), Kaggle | Cubre unos 3 meses, del 2022-03-31 al 2022-06-29. No cumple el mínimo de 1 año. Para datos de Amazon se usa el dataset 3. |
| Online Retail (UCI 352) | Es el segundo año de Online Retail II. Cargarlo además del 1 duplicaría filas. |
| Instacart, dunnhumby The Complete Journey | Usan días relativos (día 1, día 2…) en lugar de fechas. |
| REES46 (cosméticos y electrónica), Kaggle | Cubren de 2 a 5 meses. |
| Walmart M5, Corporación Favorita, Rossmann | Formato ancho o decenas de millones de filas, o no tienen producto. La preparación sería otra tarea. |

### Recomendación

Aprobar **1, 2 y 3**: son reales, no piden cuenta y cubren varios años. El 4
es opcional y real. El 5 y el 6 sirven solo como control, porque no se puede
comprobar que sean datos reales.

### Decisión del usuario (2026-11-10)

| # | Dataset | Decisión |
|---|---|---|
| 1 | Online Retail II | **Aprobado** |
| 2 | Iowa Liquor Sales | **Aprobado**. Primero se pidió todo el rango (2012 a hoy). Al ver que eran ~6.3 GB, se redujo a **2012–2016** (5 años), el rango con menos descarga, para la tienda **2633** (HY-VEE #3 / BDI / DES MOINES) |
| 3 | Open e-commerce 1.0 (Amazon) | **Aprobado** |
| 4 | Olist | No aprobado por ahora |
| 5 | Sales Product Data 2019 | No aprobado por ahora |
| 6 | Superstore | No aprobado por ahora |

## Fichas de los datasets aprobados

Datos comprobados en cada fuente el 2026-11-10. Lo que dice "por comprobar
al descargar" se verifica en el paso 2.

### Ficha 1: Online Retail II

- **Fuente:**
  - UCI Machine Learning Repository, dataset 502.
  - Página: `https://archive.ics.uci.edu/dataset/502/online+retail+ii`
  - Descarga directa: `https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip`
  - Autor: Daqing Chen (London South Bank University). Licencia CC BY 4.0, que exige citar al autor.
- **Resumen:**
  - Todas las transacciones de una tienda en línea del Reino Unido, sin local físico, que vende regalos para toda ocasión. Muchos de sus clientes son mayoristas.
  - 1,067,371 filas, del 2009-12-01 al 2011-12-09.
  - Montos en libras esterlinas (GBP).
  - Las facturas que empiezan con `C` son cancelaciones, con cantidad negativa.
  - Hay líneas con precio 0, de ajustes o muestras.
- **Campos:**

  | Campo | Tipo | Rol en Predicta |
  |---|---|---|
  | `Invoice` | texto, 6 dígitos (`C` si es cancelación) | sin rol |
  | `StockCode` | texto | sin rol |
  | `Description` | texto | producto |
  | `Quantity` | entero | cantidad |
  | `InvoiceDate` | fecha y hora | fecha |
  | `Price` | número, precio por unidad en GBP | precio unitario (monto = precio × cantidad) |
  | `Customer ID` | número | no se carga: identifica a una persona |
  | `Country` | texto | sin rol |

  No trae categoría, así que se carga como "General".
- **Continuación:** el xlsx trae, por comprobar al descargar, una hoja por año ("Year 2009-2010" y "Year 2010-2011"). Se dividen en archivos trimestrales de 200,000 filas o menos, y se suben en orden en la misma cuenta.
- **Pasos para descargar e implementar:**
  1. Crear `backend/temp_data/online-retail-ii/`.
  2. Descargar el zip y descomprimirlo ahí. Contiene `online_retail_II.xlsx` (43.5 MB).
  3. `python scripts/prepare_real_dataset.py online-retail-ii`. Lee las dos hojas, quita `Customer ID`, conserva los demás encabezados y escribe un CSV por trimestre en `listos/`.
  4. En la app, crear la cuenta de prueba "online-retail" y subir los CSV en orden. En el mapeo se asigna Description → Producto, Quantity → Cantidad, InvoiceDate → Fecha y Price → Precio unitario.

### Ficha 2: Iowa Liquor Sales

- **Fuente:**
  - Iowa Data Hub (data.iowa.gov), Iowa Alcoholic Beverages Division.
  - Dataset completo: id 1051, "Iowa Liquor Sales, January 2012 - Current".
  - Datasets por año, por ejemplo 2024 = id 1261. Cada uno se descarga en `https://idh-be.iowa.gov/api/v1/datasets/<id>/rows.csv`.
  - Los ids de cada año se toman de su página en catalog.data.gov, por ejemplo `https://catalog.data.gov/dataset/iowa-liquor-sales-2024`.
  - Licencia CC BY 4.0, según la ficha del dataset 1261.
- **Resumen:**
  - Compras de licores de las tiendas con licencia clase E de Iowa (supermercados, licorerías, tiendas de conveniencia) a la división estatal, por producto y por fecha.
  - Es venta mayorista: lo que el estado vende a cada tienda.
  - El dataset 1051 tiene 35,287,731 filas, del 2012-01-03 al 2026-10-30. Solo 2024 tiene 2,590,975 filas.
  - Montos en dólares (USD). Las fechas vienen como `AAAA-MM-DD`, así que no hay ambigüedad de día y mes.
- **Campos** (de `columns.json`; la plataforma cambió los nombres antiguos de Socrata):

  | Campo | Tipo | Rol en Predicta |
  |---|---|---|
  | `invoice_id` | texto | sin rol |
  | `ordered_on` | fecha | fecha |
  | `store_no`, `store_name`, `store_address`, `store_city`, `store_zip_code` | texto | filtro de tienda; sin rol |
  | `county_fips_code`, `county_name` | texto | sin rol |
  | `category_code` | texto | sin rol |
  | `category_name` | texto | categoría |
  | `vendor_number`, `vendor_name` | texto | sin rol |
  | `item_no` | texto | sin rol |
  | `im_desc` | texto | producto |
  | `pack`, `bottle_volume_ml` | número | sin rol |
  | `state_bottle_cost` | número | sin rol: es el costo del estado |
  | `state_bottle_retail` | número | sin rol: se usa el monto |
  | `sales_bottles` | entero | cantidad |
  | `sales_dollars` | número | monto |
  | `sales_liters`, `sales_gallons` | número | sin rol |

- **Continuación:** se elige una tienda que tenga ventas en todos los meses de 2012 a hoy. Se carga un CSV por año en la misma cuenta: 2012, 2013, … hasta el año en curso.
- **Volumen y límite de la fuente:**
  - La API no filtra: cualquier parámetro se ignora y siempre entrega el zip del año completo.
  - Bajar todo el rango son unos 35 millones de filas, del orden de varios GB.
  - Por eso el script baja un año a la vez, guarda solo las filas de la tienda elegida y borra el zip antes del siguiente año.
  - El disco tiene 29 GB libres.
  - Cloudflare limita las consultas seguidas, así que el script espera entre descargas.
- **Pasos para descargar e implementar:**
  1. Crear `backend/temp_data/iowa-liquor/`.
  2. Elegir la tienda:
     - descargar el zip de 2012 y el del año en curso;
     - quedarse con las tiendas presentes en los dos;
     - elegir la que tenga más filas y meses completos;
     - anotar su `store_no` y su nombre en los resultados.
  3. `python scripts/prepare_real_dataset.py iowa-liquor --store <store_no> --years 2012-2026`. Por cada año:
     - descarga el zip;
     - lee el CSV directamente desde el zip, sin descomprimirlo al disco, y filtra la tienda;
     - escribe un CSV en `listos/`;
     - borra el zip.

     Si una tienda grande supera 200,000 filas en un año, ese año se divide en semestres.
  4. En la app, crear la cuenta de prueba "iowa-liquor" y subir los CSV en orden.

### Ficha 3: Open e-commerce 1.0 (Amazon EE. UU.)

- **Fuente:**
  - Harvard Dataverse, DOI `10.7910/DVN/YGLYDY`, versión 1.0: `https://doi.org/10.7910/DVN/YGLYDY`
  - Archivo: `amazon-purchases.csv` (313 MB, id 7616235, público).
  - Descarga: `https://dataverse.harvard.edu/api/access/datafile/7616235`
  - Licencia CC0 1.0.
  - Artículo: Berke, Calacci, Mahari, Yabe, Larson y Pentland, "Open e-commerce 1.0, five years of crowdsourced U.S. Amazon purchase histories with user demographics", *Scientific Data*, 2024, DOI `10.1038/s41597-024-03329-6`.
- **Resumen:**
  - Historiales reales de compras en Amazon de 5,027 personas de EE. UU., que aceptaron compartirlos.
  - Más de 1.8 millones de compras de 2018 a 2022.
  - El artículo reporta que el gasto del dataset sigue al de las ventas públicas de Amazon (r = 0.978).
  - Montos en dólares (USD). Las fechas vienen como `AAAA-MM-DD`.
  - Algunas filas no tienen título ni categoría; se espera que se rechacen o queden en "General".
- **Campos** (encabezado leído del archivo):

  | Campo | Tipo | Rol en Predicta |
  |---|---|---|
  | `Order Date` | fecha | fecha |
  | `Purchase Price Per Unit` | número | precio unitario (monto = precio × cantidad) |
  | `Quantity` | número (`1.0`) | cantidad |
  | `Shipping Address State` | texto | sin rol |
  | `Title` | texto | producto |
  | `ASIN/ISBN (Product Code)` | texto | sin rol |
  | `Category` | texto (`FLASH_MEMORY`, `HEADPHONES`…) | categoría |
  | `Survey ResponseID` | texto | no se carga: enlaza con la encuesta demográfica de una persona |

- **Continuación:** un año por archivo, de 2018 a 2022, dividido en semestres o trimestres hasta quedar en 200,000 filas o menos. Se sube todo en orden en la misma cuenta.
- **Pasos para descargar e implementar:**
  1. Crear `backend/temp_data/amazon-open-ecommerce/`.
  2. Descargar `amazon-purchases.csv` ahí. No hace falta cuenta.
  3. `python scripts/prepare_real_dataset.py amazon-open-ecommerce`. Quita `Survey ResponseID`, conserva los demás encabezados y escribe los archivos por periodo en `listos/`.
  4. En la app, crear la cuenta de prueba "amazon" y subir los archivos en orden.

## Archivos, periodos y pesos

Consultado el 2026-11-10 sin descargar nada, con los metadatos de cada fuente.
El peso de los zips de Iowa es una estimación: el servidor arma cada zip al
pedirlo y no informa su tamaño. La estimación usa unos 175 bytes por fila,
medidos en una fila de muestra, y una compresión de 6 a 1.

### Online Retail II

| Archivo | Periodo | Filas | Peso |
|---|---|---|---|
| `online+retail+ii.zip`, que contiene `online_retail_II.xlsx` | 2009-12-01 a 2011-12-09 | 1,067,371 | ~44 MB. La ficha dice 43.5 MB del xlsx; el servidor no informa el tamaño del zip. |

### Open e-commerce 1.0 (Amazon)

| Archivo | Periodo | Filas | Peso |
|---|---|---|---|
| `amazon-purchases.csv` | 2018 a 2022 | más de 1.8 millones (según el artículo) | 313,070,173 bytes (~299 MB), según la ficha de Dataverse |

### Iowa Liquor Sales

Un archivo por año, cada uno un zip con uno o más CSV (`..._rows_part_0001.csv`).

**Corrección del 2026-11-10:** la estimación de los zips estaba mal. El servidor
casi no comprime. Los zips reales pesan unos 6 veces lo estimado:

- 2012: 431,253,959 bytes (~411 MB);
- 2026: 447,205,733 bytes (~427 MB).

Los 15 años suman entonces unos **6.3 GB de descarga**. En el disco hay como
máximo un zip a la vez, unos 430 MB, que se borra al terminar su año.

| Año | Id | Periodo | Filas | CSV, estimado | Zip, estimado |
|---|---|---|---|---|---|
| 2012 | 1249 | 2012-01-03 a 2012-12-31 | 2,082,059 | ~364 MB | ~61 MB |
| 2013 | 1250 | 2013-01-02 a 2013-12-31 | 2,063,763 | ~361 MB | ~60 MB |
| 2014 | 1251 | 2014-01-02 a 2014-12-31 | 2,097,796 | ~367 MB | ~61 MB |
| 2015 | 1252 | 2015-01-05 a 2015-12-31 | 2,184,483 | ~382 MB | ~64 MB |
| 2016 | 1253 | 2016-01-04 a 2016-12-30 | 2,279,893 | ~399 MB | ~66 MB |
| 2017 | 1254 | 2017-01-03 a 2017-12-29 | 2,291,276 | ~401 MB | ~67 MB |
| 2018 | 1255 | 2018-01-02 a 2018-12-31 | 2,355,558 | ~412 MB | ~69 MB |
| 2019 | 1256 | 2019-01-02 a 2019-12-31 | 2,380,345 | ~417 MB | ~69 MB |
| 2020 | 1257 | 2020-01-02 a 2020-12-31 | 2,614,365 | ~458 MB | ~76 MB |
| 2021 | 1258 | 2021-01-04 a 2021-12-31 | 2,622,712 | ~459 MB | ~76 MB |
| 2022 | 1259 | 2022-01-02 a 2022-12-30 | 2,564,565 | ~449 MB | ~75 MB |
| 2023 | 1260 | 2023-01-02 a 2023-12-30 | 2,639,557 | ~462 MB | ~77 MB |
| 2024 | 1261 | 2024-01-01 a 2024-12-31 | 2,590,975 | ~453 MB | ~76 MB |
| 2025 | 1262 | 2025-01-01 a 2025-12-31 | 2,490,620 | ~436 MB | ~73 MB |
| 2026 | 1263 | 2026-01-01 a 2026-10-30 (se actualiza cada mes) | 2,029,764 | ~355 MB | ~59 MB |
| **Total** | 1051 | 2012-01-03 a 2026-10-30 | **35,287,731** | **~6.2 GB** | **~1.0 GB** |

Con la descarga de un año a la vez, y leyendo el CSV desde el zip sin
descomprimirlo, el disco nunca tiene más de un zip, unos 77 MB. Al final solo
quedan los CSV de la tienda elegida.

### Espacio en disco

Decisión del usuario (2026-11-10): descargar los tres y guardar los originales.

| Dataset | Originales | CSV listos | Total, estimado |
|---|---|---|---|
| Online Retail II | zip ~44 MB y xlsx ~44 MB | ~90 MB | ~178 MB |
| Amazon | CSV ~299 MB | ~270 MB | ~569 MB |
| Iowa | ninguno: cada zip se borra al terminar su año | ~40 MB, una tienda | ~40 MB |
| **Total** | | | **~0.8 GB**, más ~430 MB temporales mientras se procesa Iowa (zip real, ver la corrección) |

## Datasets con inicio de sesión

### Descargar desde Kaggle

1. Crear una cuenta en `kaggle.com`.
2. Abrir la página del dataset, por ejemplo `kaggle.com/datasets/olistbr/brazilian-ecommerce`.
3. Si la página lo pide, aceptar las reglas del dataset.
4. Pulsar "Download". Kaggle entrega un zip.
5. Crear una carpeta propia, por ejemplo `backend/temp_data/olist/`, y dejar el zip ahí sin descomprimirlo.
6. Avisar que el zip está listo. El script lo lee desde esa carpeta.

### Opcional: descargar con la CLI de Kaggle

1. En Kaggle, abrir Settings → API → "Create New Token". Se descarga `kaggle.json`.
2. Guardarlo en `%USERPROFILE%\.kaggle\kaggle.json`. Es una credencial: nunca se sube a git ni se pega en un chat.
3. Con el entorno virtual activo: `pip install kaggle`. No se agrega a `requirements-dev.txt`.
4. `kaggle datasets download -d olistbr/brazilian-ecommerce -p backend/temp_data/olist`

### Buscar otros datasets de Amazon

1. En Kaggle, buscar "amazon sales" y filtrar por archivos CSV.
2. En la pestaña "Data", revisar que haya una columna de fecha por venta y que el rango cubra 12 meses o más.
3. Revisar que traiga un nombre o código de producto y un monto, o un precio y una cantidad.
4. Descartar los que solo traen reseñas, precios de catálogo o rankings: no son ventas.
5. Agregar el candidato a la tabla de este plan antes de descargarlo.

## Riesgos y mitigaciones

- **Fechas con el día primero.** `pd.to_datetime` (`backend/app/services/etl_service.py:146`) lee `03/04/2024` como 4 de marzo. En un dataset `dd/mm/aaaa`, los días mayores a 12 se rechazan y el resto se carga con día y mes invertidos, sin avisar.
  - Mitigación: el paso 1 revisa el formato de fecha de cada dataset aprobado. El script no reformatea fechas, para no esconder el problema.
  - Si aparece, se activa el STOP.
- **Moneda.** Los montos vienen en GBP (1), USD (2, 3, 5 y 6) y BRL (4). La app muestra `$`. No se convierte; se anota en los resultados.
- **Filas duplicadas entre archivos.** El 409 compara el hash del archivo completo, no cada fila.
  - Mitigación: el script divide por rangos de fecha que no se solapan.
  - Online Retail (352) y Online Retail II no se cargan en la misma cuenta.
- **Archivos grandes.** El límite es de 200,000 filas y 25 MB por archivo (`MAX_ROWS`, `MAX_UPLOAD_BYTES`). El script divide antes de esos límites y lo comprueba.
- **Volumen de Iowa.** Todo el rango 2012 a hoy son unos 35 millones de filas y la API no filtra por tienda.
  - Mitigación: bajar un año a la vez, filtrar la tienda y borrar el zip antes del año siguiente.
  - Esperar entre descargas por el límite de Cloudflare.
- **Cambio de plataforma de Iowa.** data.iowa.gov dejó Socrata en 2026. Las URL `resource/m3tr-qhgy.json` ya no responden y los campos cambiaron de nombre, por ejemplo `Sale (Dollars)` pasó a `sales_dollars`. Las fichas usan los nombres nuevos.
- **Empates de sinónimos.** Un sinónimo nuevo puede chocar con otro encabezado del mismo archivo. Por ejemplo, Iowa trae `state_bottle_cost`, `state_bottle_retail` y `sales_dollars`; solo el último se usa como monto.
  - Mitigación: un test por dataset con todos sus encabezados reales.
- **Licencias.** CC BY-NC-SA (Olist) permite el uso académico, no el comercial. La tesis cita cada fuente en los resultados.
- **Iowa es venta mayorista:** registra lo que el estado vende a cada tienda, no lo que la tienda vende al público. Se anota en los resultados.

## Alcance

- `docs/planning/plans/036-datasets-reales.md`: este plan. Se actualiza la tabla de datasets con lo aprobado.
- `backend/scripts/prepare_real_dataset.py` (nuevo):
  - una función por dataset aprobado;
  - entrada: la carpeta de `backend/temp_data/<dataset>/`;
  - salida: CSV en `backend/temp_data/<dataset>/listos/`;
  - usa el mismo estilo CLI con `argparse` que `backend/scripts/generate_dataset.py`;
  - conserva los encabezados originales;
  - divide por rangos de fecha sin solapar y respeta el límite de filas y de bytes;
  - imprime las filas por archivo.
- `backend/app/services/column_mapping.py`: sinónimos nuevos en `SYNONYMS`, solo los que necesiten los datasets aprobados. Candidatos, escritos como quedan después de `header_key`:
  - Producto: `description` (1), `im_desc` (2), `title` (3).
  - Categoría: `category_name` (2). `category` (3) ya existe.
  - Precio unitario: `purchase_price_per_unit` (3). `price` (1) ya existe.
  - Cantidad: `sales_bottles` (2). `quantity` (1 y 3) ya existe.
  - Monto: `sales_dollars` (2).
  - Fecha: `invoicedate` (1), `ordered_on` (2), `order_date` (3).

  Se agregan solo los que el paso 4 confirme que faltan.
- `backend/tests/test_column_mapping.py`: un test por dataset aprobado con su lista completa de encabezados reales y la propuesta esperada.
- `docs/pruebas/036-datos-reales.md` (nuevo): los resultados.
- `CLAUDE.md`: una frase sobre los sinónimos en inglés.
- `CHANGELOG.md`: entrada de la 036.
- `docs/planning/TASKS.md`: estado de la tarea.

## Pasos

1. Pedir la aprobación de cada dataset y confirmar su ficha.
   - Para cada dataset aprobado, comprobar en la fuente: licencia, columnas, número de filas, periodo y formato de fecha.
   - Actualizar la tabla de este plan con lo aprobado y lo confirmado.
   - **Verificar:** la tabla marca cada dataset como aprobado o rechazado y no quedan cifras "por confirmar" en los aprobados.
2. Descargar los datasets aprobados.
   - Los públicos los descarga el agente. Los de Kaggle los descarga el usuario siguiendo "Datasets con inicio de sesión".
   - Cada uno va en su carpeta `backend/temp_data/<dataset>/`.
   - Se leen con Python `-I`, sin ejecutar nada que venga en la descarga.
   - **Verificar:** `git status` no muestra archivos de datos.
3. Crear `backend/scripts/prepare_real_dataset.py`.
   - **Verificar:**
     - Cada CSV de salida tiene 200,000 filas o menos y pesa 25 MB o menos.
     - Los rangos de fecha de los archivos de un mismo dataset no se solapan.
     - La suma de filas de los archivos de salida es igual a las filas del origen, después del filtro de tienda (Iowa) o de la unión (Olist).
     - `ruff check scripts/prepare_real_dataset.py` termina sin errores.
4. Agregar los sinónimos.
   - Subir cada CSV preparado a `POST /etl/analizar-columnas` desde un test o la UI, y anotar los roles sin propuesta.
   - Agregar solo los sinónimos que falten.
   - **Verificar:** `cd backend; pytest tests/test_column_mapping.py`. Debe cubrir, para cada dataset aprobado:
     - Su lista real de encabezados propone producto, monto o precio unitario, y fecha.
     - Propone categoría y cantidad cuando el dataset las trae.
     - No deja ningún rol con `candidatos` empatados.
     - Los tests actuales pasan sin cambios.

     Después, `ruff check app/` y `mypy` sin errores.
5. Probar en la app.
   - Crear una cuenta de prueba por dataset.
   - Subir el primer archivo, revisar la propuesta, cargar y anotar:
     - las filas leídas, cargadas y rechazadas;
     - los motivos de rechazo más frecuentes.
   - Subir los archivos siguientes de la misma empresa, en orden.
   - **Verificar:**
     - El total de ingresos del dashboard es igual a la suma de los montos cargados en todos los archivos.
     - La serie mensual no tiene huecos en las uniones entre archivos.
     - `/analytics/forecast` reporta en `meses_observados` los meses de todos los archivos.
     - El modelo pasa de `tendencia` a `tendencia_estacional` cuando el historial llega a 36 meses con todos los meses del año.
     - Volver a subir un archivo ya cargado responde 409.
6. Documentar los resultados y cerrar.
   - En `docs/pruebas/036-datos-reales.md` va, por dataset y archivo:
     - la fuente y la licencia;
     - el mapeo propuesto y el usado;
     - las filas leídas, cargadas y rechazadas, y los motivos principales;
     - los meses observados, el modelo y el horizonte;
     - las métricas de la proyección.
   - Sin nombres, ids ni direcciones de clientes.
   - Actualizar `CLAUDE.md`, `CHANGELOG.md` y `docs/planning/TASKS.md`.
   - **Verificar:** la verificación global de `docs/planning/TASKS.md` termina con código 0.

## Hallazgos durante la prueba

- **La carga descarta archivos sin avisar** (2026-11-10). Si se arrastran varios archivos a la página de carga, solo se sube el primero y los demás se ignoran en silencio. Ocurre en `frontend/src/components/etl/UploadDropzone.tsx:42` (`event.dataTransfer.files[0]`). El selector tampoco acepta varios archivos.
  - Se vio al cargar Online Retail II: solo entró `online_retail_ii_2010Q3.csv`, con 106,084 filas cargadas y 2,696 rechazadas, que suman las 108,780 del archivo.
  - Decisión del usuario: anotarlo y seguir subiendo de a un archivo. La corrección se planificó como tarea 038 (`docs/planning/plans/038-carga-varios-archivos.md`).

## Criterios de terminado

- Cada dataset aprobado está preparado en CSV que la carga acepta sin superar los límites.
- La propuesta de mapeo de cada dataset aprobado asigna, sin cambios manuales, todos los roles cuya columna trae el dataset.
- Para una misma empresa, el historial y la proyección suman todos sus archivos cargados.
- `docs/pruebas/036-datos-reales.md` registra los conteos de cada carga.
- Ningún dato real ni `kaggle.json` aparece en git.

## Fuera de alcance

- La descarga del XLSX estandarizado (tarea 037).
- Cambiar `_parse_date` para aceptar fechas con el día primero.
- Convertir monedas.
- Detectar filas duplicadas entre cargas distintas.
- Inferir una categoría para los datasets que no la traen. Quedan en "General".
- Datasets en formato ancho o de más de 10 millones de filas: Walmart M5, Corporación Favorita.
- Agregar `kaggle` a las dependencias del proyecto.

## STOP

- No descargar ningún dataset sin la aprobación explícita del usuario.
- Detenerse si un dataset aprobado usa fechas con el día primero. Reportarlo; cambiar el parser es otra tarea.
- Detenerse si un sinónimo nuevo cambia la propuesta de un test existente de `tests/test_column_mapping.py`.
- Detenerse si un dataset aprobado exige credenciales que el usuario no compartió, o si su licencia prohíbe el uso académico.

## Mantenimiento

Para probar un dataset nuevo:

1. Agregarlo a la tabla de este plan con su fuente, tamaño y periodo.
2. Esperar la aprobación del usuario.
3. Sumar su función en `prepare_real_dataset.py`.
4. Sumar su test de encabezados en `tests/test_column_mapping.py`.

Los sinónimos siguen viviendo solo en `column_mapping.py`.

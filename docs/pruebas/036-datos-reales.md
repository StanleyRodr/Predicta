# Pruebas con datasets reales (tarea 036)

Resultados de cargar ventas reales de tiendas en línea en Predicta. Plan:
`docs/planning/plans/036-datasets-reales.md`.

Los datos quedan en `backend/temp_data/`, fuera de git. Se preparan con
`backend/scripts/prepare_real_dataset.py`, que no borra filas inválidas.
Este documento no incluye datos de clientes.

## Cómo se comprobaron los conteos

1. El usuario subió cada archivo desde la página de carga y anotó la respuesta: filas leídas, cargadas y rechazadas.
2. Por separado, los mismos archivos se procesaron con el código del ETL, sin base de datos: `etl_service._mapped_rows` y `build_venta`, con el mismo mapeo. Así se obtienen los motivos de rechazo y el total de ingresos esperado.
3. Las dos cuentas tienen que coincidir archivo por archivo.

## Resumen

| Dataset | Archivos | Periodo | Leídas | Cargadas | Rechazadas | Ingresos |
|---|---|---|---|---|---|---|
| Online Retail II | 9 | 2009-12 a 2011-12 | 1,044,848 | 1,019,637 | 25,211 | 20,534,115.47 GBP |
| Iowa, tienda 2633 | 5 | 2012-01 a 2016-12 | 95,133 | 95,101 | 32 | 46,984,848.31 USD |
| Amazon (Open e-commerce 1.0) | 18 | 2018-01 a 2024-08 | 1,850,717 | 1,304,829 | 545,888 | 29,623,460.93 USD |

- **Coincidencia:** en los 32 archivos, la respuesta de la app es igual a la del ETL sin base de datos. Las proyecciones de Iowa y Amazon que muestra `/predictions` son iguales a las que da `monthly_forecast_series` con las mismas ventas.
- **Continuación:** el historial y la proyección suman todos los archivos de cada empresa, sin huecos entre un archivo y el siguiente.
- **Duplicados:** volver a subir un archivo responde "Ya cargado" (409) y no cambia el historial.
- **Mapeo:** con los sinónimos de la tarea 036, los tres datasets se proponen completos y sin empates. No hubo que corregir el mapeo a mano.

## Hallazgos

| # | Hallazgo | Estado |
|---|---|---|
| 1 | El dropzone subía solo el primer archivo cuando se arrastraban varios y descartaba el resto sin avisar. | Corregido en la tarea 038 (commit `f7e4667`). Iowa y Amazon ya se cargaron con varios archivos a la vez. |
| 2 | El lector CSV leía mal las comillas escapadas (`""`) que venían después de los primeros 8 KB. `csv.Sniffer` decidía `doublequote=False`. Afectó 2,233 productos de Online Retail II y 45 de Iowa (solo el nombre), y en Amazon perdía 200 filas y corría columnas. | Corregido en `8c960ec` con un test. Online Retail II e Iowa se purgaron y se recargaron; todos los conteos de este documento son posteriores al arreglo. |
| 3 | Un mes completo se trata como incompleto si su último día no tiene ventas (`_split_partial_month`). En Iowa, diciembre de 2016 se proyecta en lugar de ajustarse, porque la tienda nunca compra el 31 de diciembre. | Abierto, para otra tarea. |
| 4 | La proyección no avisa de huecos largos ni de una caída abrupta al final del historial. En Amazon, después de marzo de 2023 hay meses con 22 dólares y un hueco de 2023-08 a 2024-07, pero la proyección sigue en ~600,000 por mes y no muestra ningún aviso. | Abierto, para otra tarea. |
| 5 | El 24 % de las filas de Amazon (456,148) se rechaza porque el título supera los 150 caracteres de `ventas.producto`. | Decisión del usuario: se mantiene el rechazo. |
| 6 | El registro rechaza los correos con dominios reservados como `.test` (`email-validator`). | Comportamiento esperado; las cuentas de prueba usan `example.com`. |

## 1. Online Retail II (UCI)

- **Fuente:** UCI Machine Learning Repository, dataset 502. CC BY 4.0. Autor: Daqing Chen.
- **Cuenta de prueba:** `retail@example.com`.
- **Preparación:**
  - Las dos hojas del xlsx comparten del 2010-12-01 al 2010-12-09.
  - Se comprobó que esas 22,523 filas eran idénticas en ambas hojas y se contaron una sola vez.
  - De 1,067,371 filas quedan 1,044,848.
  - Se quitó `Customer ID`.
- **Mapeo propuesto y usado**, sin cambios manuales:

  | Rol | Columna |
  |---|---|
  | Producto | Description |
  | Precio unitario | Price (monto = precio × cantidad) |
  | Cantidad | Quantity |
  | Fecha | InvoiceDate |
  | Categoría | sin asignar, queda "General" |

### Cargas

| Archivo | Periodo | Leídas | Cargadas | Rechazadas | ¿Coincide con el ETL sin base? |
|---|---|---|---|---|---|
| `online_retail_ii_2009.csv` | 2009-12-01 a 2009-12-23 | 45,228 | 43,957 | 1,271 | Sí |
| `online_retail_ii_2010Q1.csv` | 2010-01-04 a 2010-03-31 | 102,454 | 99,275 | 3,179 | Sí |
| `online_retail_ii_2010Q2.csv` | 2010-04-01 a 2010-06-30 | 109,363 | 105,961 | 3,402 | Sí |
| `online_retail_ii_2010Q3.csv` | 2010-07-01 a 2010-09-30 | 108,780 | 106,084 | 2,696 | Sí |
| `online_retail_ii_2010Q4.csv` | 2010-10-01 a 2010-12-23 | 179,594 | 175,739 | 3,855 | Sí |
| `online_retail_ii_2011Q1.csv` | 2011-01-04 a 2011-03-31 | 99,602 | 97,214 | 2,388 | Sí |
| `online_retail_ii_2011Q2.csv` | 2011-04-01 a 2011-06-30 | 103,820 | 101,236 | 2,584 | Sí |
| `online_retail_ii_2011Q3.csv` | 2011-07-01 a 2011-09-30 | 125,028 | 122,386 | 2,642 | Sí |
| `online_retail_ii_2011Q4.csv` | 2011-10-02 a 2011-12-09 | 170,979 | 167,785 | 3,194 | Sí |
| **Total** | 2009-12-01 a 2011-12-09 | **1,044,848** | **1,019,637** | **25,211** | Sí |

### Motivos de rechazo

| Motivo | Filas | Origen en el dataset |
|---|---|---|
| la cantidad no puede ser negativa | 19,924 | Devoluciones y cancelaciones: facturas `C…` con cantidad negativa |
| el producto es obligatorio | 4,275 | Líneas sin `Description`, casi siempre ajustes de inventario con precio 0 |
| el precio unitario por la cantidad debe ser mayor que cero | 1,012 | Precio 0, o un monto que redondea a 0.00 |

### Historial y proyección

- **Ingresos esperados:** 20,534,115.47, que es la suma del monto de las filas cargadas. Están en GBP, y la app los muestra con `$`.
- **Meses con ventas:** 25, de 2009-12 a 2011-12. Diciembre de 2011 está incompleto, porque termina el día 9: el modelo lo deja fuera del ajuste y lo proyecta primero.
- **Continuación:**
  - Los 9 archivos se sumaron en la misma cuenta.
  - El usuario revisó el historial de ventas, `/predictions` y los reportes, y dice que todo funciona.
  - Con un solo archivo cargado (2010Q3), `/predictions` respondía que faltaban meses, como corresponde: "Se necesitan al menos 6 meses completos de ventas para proyectar; hay 3 y faltan 3".
- **Hallazgo:**
  - La página de carga sube solo el primer archivo cuando se arrastran varios, y descarta los demás sin avisar.
  - Ocurre en `frontend/src/components/etl/UploadDropzone.tsx:42`.
  - Se corrige en la tarea 038 (`docs/planning/plans/038-carga-varios-archivos.md`).

## 2. Iowa Liquor Sales, tienda 2633

- **Fuente:** Iowa Data Hub (data.iowa.gov), Iowa Alcoholic Beverages Division. Datasets 1249 a 1253 (2012 a 2016). CC BY 4.0.
- **Qué registra:** venta mayorista, es decir, lo que el estado le vende a la tienda.
- **Tienda:** 2633, HY-VEE #3 / BDI / DES MOINES. Es la más estable de las presentes en 2012 y en 2026.
- **Cuenta de prueba:** `iowa@example.com`.
- **Preparación:**
  - Se descargó un zip por año.
  - El CSV se leyó desde el zip sin descomprimirlo, quedándose solo con la tienda 2633, y después se borró el zip.
  - Pesos reales de los zips: 2012, 431,253,959 bytes; 2013, 407.7 MB; 2014, 414.4 MB; 2015, 431.8 MB; 2016, 448.2 MB.
  - Se usan los cinco años 2012 a 2016 y no todo el rango, porque bajar los 15 años eran ~6.3 GB (decisión del usuario).
- **Carga:** los 5 archivos se soltaron de una vez con la carga de varios archivos de la tarea 038. Hubo un solo mapeo para los cinco.
- **Mapeo propuesto y usado**, sin cambios manuales:

  | Rol | Columna |
  |---|---|
  | Producto | im_desc |
  | Categoría | category_name |
  | Monto | sales_dollars |
  | Cantidad | sales_bottles |
  | Fecha | ordered_on |

### Cargas

| Archivo | Periodo | Leídas | Cargadas | Rechazadas | ¿Coincide con el ETL sin base? |
|---|---|---|---|---|---|
| `iowa_2633_2012.csv` | 2012 | 17,590 | 17,565 | 25 | Sí |
| `iowa_2633_2013.csv` | 2013 | 18,111 | 18,111 | 0 | Sí |
| `iowa_2633_2014.csv` | 2014 | 19,717 | 19,717 | 0 | Sí |
| `iowa_2633_2015.csv` | 2015 | 19,508 | 19,508 | 0 | Sí |
| `iowa_2633_2016.csv` | 2016 | 20,207 | 20,200 | 7 | Sí |
| **Total** | 2012-01 a 2016-12 | **95,133** | **95,101** | **32** | Sí |

### Motivos de rechazo

| Motivo | Filas | Origen en el dataset |
|---|---|---|
| el monto debe ser mayor que cero | 32 | `sales_dollars` en 0. No hay montos ni botellas negativos. |

### Historial y proyección

- **Ingresos esperados:** 46,984,848.31 USD, que es la suma del monto de las filas cargadas.
- **Meses con ventas:** 60, de 2012-01 a 2016-12. Todos los meses del año están observados, así que el modelo esperado es tendencia y temporada, con 12 meses de horizonte.
- **Categorías:** 92 distintas en el archivo original, más 500 filas sin categoría, que quedan en "General".
- **Productos:** 1,759 descripciones distintas.
- **Duplicados:** al volver a soltar los 5 archivos, los 5 quedaron como "Ya cargado", con el mensaje "Este archivo ya fue cargado. Purga el historial si deseas cargarlo de nuevo." El historial no cambió.
- **Proyección general en `/predictions`:**
  - El primer punto proyectado es diciembre de 2016: $944,844.51, entre $778,552.97 y $1,111,136.04 (95 %). En cantidad, 54,109.52 unidades, entre 44,866.92 y 63,352.12.
  - El valor real de diciembre de 2016 es $1,006,825.85 y 58,413 unidades. Los dos quedan dentro del rango del 95 %. El modelo no vio ese mes al ajustar, así que funciona como una prueba fuera de muestra.
- **Hallazgo: un mes completo tratado como incompleto.**
  - `_split_partial_month` (`backend/app/ml_models/forecast.py:255`) considera incompleto el último mes cuando la última venta es anterior a su último día.
  - La tienda 2633 nunca registra compras el 31 de diciembre. Los últimos días de cada año son 2012-12-28, 2013-12-30, 2014-12-30, 2015-12-30 y 2016-12-30.
  - Por eso diciembre de 2016, que está completo, se deja fuera del ajuste y se proyecta. El modelo ajusta con 59 meses en lugar de 60.
  - Con 59 meses y todos los meses del año observados, igual corresponde tendencia y temporada.
  - Afecta a cualquier negocio que no vende el último día del mes (fines de semana, feriados). Queda anotado para otra tarea; no se cambia en la 036.

## 3. Open e-commerce 1.0 (Amazon)

- **Fuente:** Harvard Dataverse, DOI `10.7910/DVN/YGLYDY`, archivo `amazon-purchases.csv` (313,070,173 bytes). CC0 1.0.
- **Artículo:** Berke et al., *Scientific Data*, 2024.
- **Qué registra:** compras reales en Amazon EE. UU. de 5,027 personas que aceptaron compartir su historial.
- **Cuenta de prueba:** `amazon@example.com`.
- **Preparación:**
  - Se quitó `Survey ResponseID`.
  - Se dividió en 18 archivos: semestres en 2018 y 2019, trimestres de 2020 a 2022, y un archivo para 2023 y otro para 2024. Todos quedan bajo 200,000 filas y 25 MB.
- **Carga:** los 18 archivos se soltaron de una vez, con un solo mapeo.
- **Mapeo propuesto y usado**, sin cambios manuales:

  | Rol | Columna |
  |---|---|
  | Producto | title |
  | Categoría | category |
  | Precio unitario | purchase_price_per_unit (monto = precio × cantidad) |
  | Cantidad | quantity |
  | Fecha | order_date |

### Cargas

| Archivo | Leídas | Cargadas | Rechazadas | ¿Coincide con el ETL sin base? |
|---|---|---|---|---|
| `amazon_2018-S1.csv` | 101,779 | 73,540 | 28,239 | Sí |
| `amazon_2018-S2.csv` | 123,686 | 89,614 | 34,072 | Sí |
| `amazon_2019-S1.csv` | 113,615 | 81,759 | 31,856 | Sí |
| `amazon_2019-S2.csv` | 152,401 | 109,012 | 43,389 | Sí |
| `amazon_2020Q1.csv` | 78,094 | 56,729 | 21,365 | Sí |
| `amazon_2020Q2.csv` | 100,673 | 73,244 | 27,429 | Sí |
| `amazon_2020Q3.csv` | 104,707 | 74,475 | 30,232 | Sí |
| `amazon_2020Q4.csv` | 125,738 | 88,312 | 37,426 | Sí |
| `amazon_2021Q1.csv` | 114,508 | 79,987 | 34,521 | Sí |
| `amazon_2021Q2.csv` | 117,507 | 81,500 | 36,007 | Sí |
| `amazon_2021Q3.csv` | 109,638 | 76,579 | 33,059 | Sí |
| `amazon_2021Q4.csv` | 126,217 | 87,607 | 38,610 | Sí |
| `amazon_2022Q1.csv` | 105,201 | 73,204 | 31,997 | Sí |
| `amazon_2022Q2.csv` | 109,222 | 76,281 | 32,941 | Sí |
| `amazon_2022Q3.csv` | 115,728 | 79,913 | 35,815 | Sí |
| `amazon_2022Q4.csv` | 112,079 | 76,299 | 35,780 | Sí |
| `amazon_2023.csv` | 39,923 | 26,773 | 13,150 | Sí |
| `amazon_2024.csv` | 1 | 1 | 0 | Sí |
| **Total** | **1,850,717** | **1,304,829** | **545,888** | Sí |

### Motivos de rechazo

| Motivo | Filas | Origen en el dataset |
|---|---|---|
| el producto supera el largo maximo | 456,148 | Títulos de Amazon de más de 150 caracteres |
| el producto es obligatorio | 89,740 | Compras sin título en el historial exportado |

### Historial y proyección

- **Ingresos esperados:** 29,623,460.93 USD.
- **Meses con ventas:** 66, de 2018-01 a 2024-08.
- **El final de la serie se apaga:** los participantes compartieron su historial entre fines de 2022 y marzo de 2023.
  - Montos: 2022-12, 508,332.32; 2023-01, 258,336.60; 2023-02, 224,205.70; 2023-03, 104,645.48; 2023-06, 21.98; 2023-07, 22.35.
  - Después no hay ventas hasta una compra suelta el 2024-08-15.
- **Proyección general en `/predictions`:**
  - Tendencia y temporada, con 65 meses observados y horizonte de 12.
  - Agosto de 2024 queda como mes parcial y es el primer punto: $593,391.02, entre $228,988.16 y $957,793.88. En cantidad, 30,765.14 unidades, entre 12,273.94 y 49,256.35.
  - Es igual al cálculo de `monthly_forecast_series` con las mismas ventas.
  - La proyección no muestra ningún aviso, aunque el historial termina con meses casi vacíos y un hueco de un año (hallazgo 4).
- **Lectura:** el sistema funcionó como está diseñado, pero la proyección de Amazon después de 2023 no es útil. La fuente deja de registrar compras, no es que Amazon dejara de vender.

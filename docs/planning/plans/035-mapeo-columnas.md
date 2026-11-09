# Plan 035: Mapeo de columnas en la carga de ventas

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** MEDIUM (cambia el código que lee los tres formatos; ver `## Riesgos y mitigaciones`)
- **Depende de:** `docs/planning/plans/034b-prediccion-producto.md`, que introduce `normalize_product`; `build_venta` la sigue aplicando al producto mapeado.
- **Categoría:** backend / frontend
- **Origen:** pedido del usuario, entrevista de diseño y revisión Goldfish del 2026-11-09 (`docs/planning/plans/035.5-correciones.md`)
- **Planificado en:** commit `3e92380`, 2026-11-09

## Objetivo

Hoy `_require_columns` (`backend/app/services/etl_service.py`) rechaza los
CSV y XLSX que no traen los nombres exactos `producto`, `categoria`, `monto`,
`cantidad` y `fecha`. Los usuarios exportan sus ventas desde otros sistemas,
que usan otros nombres (por ejemplo "Item", "Rubro", "Total", "Unidades" o
"Fecha de venta"), y tienen que renombrar las columnas a mano.

Con esta tarea, el sistema propone qué columna del archivo corresponde a cada
rol. El usuario revisa la propuesta y, si hace falta, la corrige antes de
cargar las ventas.

## Decisiones

- **Sin LLM:** el mapeo usa reglas: un diccionario de sinónimos sobre una clave normalizada. No tiene costo por uso, no requiere red y los datos no salen del servidor. El mismo archivo produce siempre la misma propuesta. Se descartaron un LLM en la nube y un modo híbrido por costo, privacidad y resultados no deterministas.
- **Sin coincidencia aproximada:** se descartó `difflib` porque solo cubre errores de tipeo, obliga a verificar tipos de valores en la propuesta y el usuario igual revisa todo en la vista previa.
- **Vista previa y confirmación:** la UI no carga sin mostrar antes la propuesta. Es una garantía de la UI: la API acepta cualquier `mapeo` válido. El servidor no guarda el archivo entre pasos; el cliente lo envía de nuevo en el análisis y en la carga. Se descartaron una caché temporal con token (agrega estado y limpieza) y leer la vista previa en el cliente con SheetJS (duplica los tres lectores en el frontend).
- **Compatibilidad:** `POST /etl/upload-ventas` sin el campo `mapeo` exige los nombres exactos en CSV y XLSX, como hoy. SQL sigue sin exigir columnas: una columna faltante es un error de fila. Los tests actuales no requieren cambios. Hay tres excepciones intencionales:
  1. `_parse_date` rechaza números y textos de solo dígitos. Hoy `pd.to_datetime` toma el entero `15` como nanosegundos desde 1970 y el texto `"15"` como el día 15 del mes en curso, y la fila se carga sin aviso.
  2. Una categoría vacía en XLSX (`NaN`) se guarda como "General". Hoy se guarda como "Nan".
  3. Un XLSX con encabezados y sin filas responde 200 con 0 filas. Hoy responde "faltan columnas requeridas".
- **Monto derivado:** si el mapeo no asigna `monto` y sí `precio_unitario`, `build_venta` calcula `monto = round(precio_unitario * cantidad, 2)`. El precio se lee sin redondear y solo se redondea el producto. Si falta la cantidad, se usa 1, como hoy. Si el mapeo asigna `monto`, solo se usa esa columna: no hay recaída por fila.
- **Descarga estandarizada:** se pasa a la tarea 036. Se descartó incluirla aquí porque era la única causa de la doble carga, del orden de hojas y del escape de fórmulas, y duplicaba el bucle de filas de `load_sales`.

## Reglas del mapeo

### Roles

`producto`, `categoria`, `monto`, `precio_unitario`, `cantidad` y `fecha`.
Son obligatorios `producto` y `fecha`, y al menos uno de `monto` o
`precio_unitario`.

### Tres formas de un encabezado

| Forma | Quién la produce | Ejemplo |
|---|---|---|
| Original | el archivo | `Precio Unit.` |
| API | `_normalize_row`: quita espacios al inicio y al final, pasa a minúsculas y cambia cada espacio por `_` | `precio_unit.` |
| Clave de comparación | `category_service.category_key` (NFKD, sin acentos, casefold) y después cada grupo de caracteres que no sea letra o dígito pasa a `_`, sin `_` al inicio ni al final | `precio_unit` |

La API devuelve y recibe la forma API. La clave solo sirve para buscar en el
diccionario. Los selectores muestran la forma API; no se conserva el texto
original.

### Diccionario

Vive en `backend/app/services/column_mapping.py`. Cada clave se compara con
los sinónimos de cada rol:

| Rol | Sinónimos |
|---|---|
| producto | producto, product, item, articulo, descripcion, nombre_producto, sku_descripcion |
| categoria | categoria, category, rubro, familia, tipo, departamento |
| monto | monto, total, importe, ventas, monto_total, total_venta, amount |
| precio_unitario | precio, precio_unitario, precio_unit, pu, valor_unitario, unit_price, price |
| cantidad | cantidad, unidades, qty, quantity, cant, uds, piezas |
| fecha | fecha, fecha_venta, fecha_de_venta, date, fecha_emision |

Se dejaron fuera `dia`, `linea`, `subtotal` y `venta` porque suelen nombrar
otra cosa (día del mes, número de línea, monto sin impuestos, ID de venta).

### Prioridad

1. `exacto`: la clave es igual al nombre del rol.
2. `sinonimo`: la clave está entre los sinónimos del rol.

La propuesta se resuelve en dos pasadas: primero todos los `exacto`, después
todos los `sinonimo`. Dentro de cada pasada, los roles siguen este orden:
producto, categoria, monto, precio_unitario, cantidad, fecha. Un encabezado
se asigna a un solo rol. Si varios encabezados libres empatan para un rol, el
rol queda sin asignar, todos los empatados van a `candidatos` y quedan tomados
para los roles siguientes.

### Validación del mapeo que envía el cliente

`validate_mapping` lanza `MappingValidationError` y la ruta responde 400 con
`detail` en español si:

- una clave no es un rol: "El rol X no existe.";
- un encabezado no está en el archivo: "La columna X no existe en el archivo.";
- un encabezado se usa en dos roles: "La columna X está asignada a dos roles.";
- falta `producto` o `fecha`: "Falta asignar: Producto." (o "Fecha.");
- faltan a la vez `monto` y `precio_unitario`: "Falta asignar: Monto o Precio unitario.".

Un rol omitido o enviado en `null` queda sin asignar. Las columnas sin rol se
ignoran.

### Archivos SQL

Solo se leen sentencias `INSERT INTO ... VALUES`; el SQL nunca se ejecuta.
Los encabezados salen de las listas de columnas declaradas, unidas en orden de
primera aparición, o de `SQL_DEFAULT_COLUMNS` (`producto, monto, categoria,
fecha, cantidad`) si un `INSERT` no declara lista. Nunca salen de las claves de
las filas. Sin lista declarada, la propuesta es `exacto` en esos cinco roles y
`precio_unitario` queda sin asignar.

## Riesgos y mitigaciones

- **Mapeo equivocado que carga filas:** el reintento responde 409 porque el SHA-256 ya está registrado, y solo queda purgar el historial. Mitigación: la vista previa con 5 filas. Un mapeo que rechaza todas las filas no registra `CargaArchivo` (`etl_service.py:354`), así que se puede reintentar.
- **El archivo viaja dos veces** (análisis y carga). Está acotado por los 25 MB y `MAX_UPLOAD_ROWS`. El análisis reutiliza los mismos lectores y límites.
- **Fechas numéricas que se cargaban en silencio:** se corrigen en `_parse_date` (excepción 1 de "Compatibilidad").

## API

Los dos endpoints exigen autenticación. `analizar-columnas` no lee ni escribe
ventas guardadas.

- `POST /etl/analizar-columnas` (multipart: `file`) responde 200 con `schemas.ColumnAnalysis`:
  - `columnas: list[str]`: encabezados en forma API y en el orden del archivo.
  - `muestra: list[dict[str, str | None]]`: hasta 5 filas. Un valor faltante según `_is_missing` o una clave ausente pasa a `None`; una fecha, a `YYYY-MM-DD`; un float entero, a texto sin `.0`; cualquier otro valor, a `str(v).strip()`.
  - `propuesta: dict[Rol, ColumnProposal]`: columna propuesta para cada rol, siempre con las 6 claves. `ColumnProposal = {columna: str | None, origen: Literal["exacto", "sinonimo"] | None, candidatos: list[str]}`. Un rol vacío es `{columna: null, origen: null, candidatos: []}`.
  - `faltantes: list[str]`: roles obligatorios sin propuesta, en el orden de la lista de roles. Si faltan monto y precio, contiene `"monto"`.
  - Aplica los mismos límites y errores de archivo (400/413) que `POST /etl/upload-ventas`.
- `POST /etl/upload-ventas` recibe además `mapeo: str | None = Form(None)`, un JSON `{rol: encabezado}`. Si se envía, se valida, se renombran las columnas y, si no hay `monto`, `build_venta` lo deriva del precio. La respuesta (`UploadResponse`), el chequeo de duplicado por SHA-256 y la transacción no cambian.
- Orden de los errores en la carga:
  1. nombre y extensión (400);
  2. JSON de `mapeo` mal formado (400, "El mapeo de columnas no es un JSON válido.");
  3. tamaño (413);
  4. duplicado (409);
  5. lectura (400);
  6. `validate_mapping` (400, sin el prefijo "No se pudo leer el archivo: ").

## Alcance

- `backend/app/services/column_mapping.py` (nuevo). Funciones puras, que no acceden a la base de datos ni importan `etl_service`:
  - roles, diccionario y `header_key(header)`, construida sobre `category_key`;
  - `MappingValidationError(UserFacingError)`;
  - `propose_mapping(columnas) -> dict[rol, propuesta]`;
  - `validate_mapping(mapeo, columnas)`;
  - `apply_mapping(filas, mapeo) -> list[dict]`, que arma diccionarios nuevos con solo los roles mapeados.
  - `UserFacingError` sigue en `etl_service`. Si importarla crea un ciclo, se mueve a `backend/app/services/errors.py` y `etl_service` la reexporta.
- `backend/app/services/etl_service.py`:
  - `read_table(extension, contents) -> tuple[list[str], list[dict]]`. Los encabezados salen de `reader.fieldnames` (CSV), `frame.columns` (XLSX) o la regla SQL. `read_rows` queda como envoltorio.
  - `_require_columns` se aplica después de `apply_mapping` con `mapeo`, o sobre los nombres exactos sin `mapeo` (solo CSV y XLSX).
  - Se mantienen los nombres y las firmas `_parse_csv(contents)`, `_parse_amount` y `_parse_quantity`, que usan los tests.
  - `_parse_number` recibe `round_to: int | None = 2`.
  - `_parse_date` rechaza `int`/`float` (excepto `datetime`) y textos de solo dígitos.
  - `build_venta` deriva el monto, con los mensajes "el precio unitario no es numerico" y "el precio unitario por la cantidad debe ser mayor que cero", y pasa `None` a `normalize_category` cuando `_is_missing(categoria)`.
  - `load_sales(db, user_id, extension, contents, file_hash, mapeo: dict[str, str] | None = None)`.
- `backend/app/api/etl_routes.py`:
  - importa `Form`;
  - el helper `_read_upload(file) -> (extension, contents, file_hash)` y una sola traducción de excepciones a HTTP;
  - el parseo del JSON de `mapeo` en un solo lugar;
  - `POST /etl/analizar-columnas` y el campo `mapeo` en la carga.
- `backend/app/schemas/schemas.py`: `ColumnProposal` y `ColumnAnalysis`, con `Literal` en los roles y en `origen`.
- `backend/tests/test_column_mapping.py` (nuevo).
- `backend/tests/test_etl.py` y `backend/tests/test_etl_hardening.py`: solo tests nuevos.
- `backend/tests/test_isolation.py`: `("POST", "/etl/analizar-columnas", {})` en `PRIVATE_CASES`, y `_call` le envía un CSV con `files`.
- `frontend/src/types/etl.ts`:
  - `ColumnRole`, la unión de los 6 roles;
  - `ColumnMapping = Partial<Record<ColumnRole, string>>`;
  - `ColumnProposal` y `ColumnAnalysis`, que replican el schema.
- `frontend/src/api/etl.ts`: `analyzeColumns(file)` y `uploadSales(file, mapeo?)`, que agrega `mapeo` como JSON al `FormData`.
- `frontend/src/api/etl.test.ts`: casos de `analyzeColumns` y de `uploadSales` con `mapeo`.
- `frontend/src/components/etl/ColumnMappingPanel.tsx` (nuevo) y su export en `frontend/src/components/etl/index.ts`.
- `frontend/src/components/etl/etl.test.tsx`: tests del panel.
- `frontend/src/pages/UploadPage.tsx` y `frontend/src/pages/UploadPage.test.tsx`. El `vi.mock("../api/etl")` de la línea 14 se amplía con `analyzeColumns`.
- `CLAUDE.md`: la viñeta **ETL** menciona el mapeo, la vista previa y las tres excepciones de compatibilidad.
- `docs/planning/TASKS.md`.

## Interfaz

1. Al elegir el archivo se llama a `analyzeColumns` con `useMutation` y se muestra un spinner hasta recibir la respuesta. Al cambiar de archivo, se llama a `reset()`, se descarta el mapeo anterior y se ignora la respuesta de un `File` que ya no es el actual (se compara la referencia).
2. Si el análisis falla, se muestra `<Alert tone="error">` con `getApiErrorMessage(error, "No se pudo analizar el archivo.")`, sin panel, y "Cargar ventas" queda deshabilitado.
3. `ColumnMappingPanel` recibe `{analysis, value, onChange}`. El estado del mapeo vive en `UploadPage`.
   - El panel es un `role="group"` con `aria-label="Mapeo de columnas"`.
   - Hay un `<select>` por rol con la etiqueta visible Producto, Categoría, Monto, Precio unitario, Cantidad o Fecha, y con el nombre accesible "Columna para Producto" (y así cada uno), para no chocar con el `CategoryProductFilter` de la misma página.
   - Reutiliza `selectClass` de `CategoryProductFilter.tsx`.
   - Las opciones son los encabezados del archivo más "Sin asignar", que omite la clave en `ColumnMapping`.
   - Junto a cada selector, un `Badge` muestra el origen: "Exacto" (`positive`) o "Sinónimo" (`neutral`). Un rol con `candidatos` muestra "Hay varias columnas posibles".
4. Debajo se muestra una tabla con las filas de `muestra`. Las columnas asignadas muestran el nombre del rol, y las demás conservan su encabezado.
5. El botón "Cargar archivo" pasa a llamarse "Cargar ventas". Queda deshabilitado mientras falte un rol obligatorio o una columna se repita. Un mensaje dice "Falta asignar: Fecha" o "La columna X está asignada a dos roles".
6. La UI siempre envía `mapeo` después de un análisis exitoso. Después de cargar se mantiene el comportamiento actual: `UploadSummary` y `refreshSalesData`.

## Pasos

1. Crear `column_mapping.py`.
   - **Verificar:** `cd backend; pytest tests/test_column_mapping.py`. Debe cubrir:
     - "Fecha de Venta" se propone como `fecha` con origen `sinonimo`, y "Categoría" y "Descripción" se reconocen sin acentos.
     - `total` e `importe` juntos dejan `monto` sin asignar y a los dos en `candidatos`.
     - Un encabezado `exacto` de un rol posterior no se pierde frente a un sinónimo de un rol anterior.
     - Un encabezado no se asigna a dos roles.
     - "Dia" y "Linea" no se proponen para ningún rol.
     - `apply_mapping` con `categoria` en "Sin asignar" no deja pasar la columna `categoria` del archivo.
     - Cada error de la lista de "Validación del mapeo", con su mensaje.
     - Un CSV de `generate_dataset(days=3)`, importado desde `backend/scripts/generate_dataset.py` con `importlib.util.spec_from_file_location`, da `exacto` en los cinco roles y `precio_unitario` sin asignar.
2. Cambiar `etl_service.py`: agregar `read_table`, la regla SQL, `mapeo` en `load_sales`, el monto derivado y las excepciones de fecha, "Nan" y XLSX vacío.
   - **Verificar:** `cd backend; pytest tests/test_etl.py tests/test_etl_hardening.py`. Los tests actuales pasan sin cambios. Tests nuevos:
     - Un CSV `Item;Rubro;Total;Unidades;Fecha de venta` con 3 filas y su `mapeo` inserta 3 ventas con esos productos, categorías, montos y fechas.
     - Un XLSX `Producto, Precio Unit., Cant., Fecha` con precio `0.333` y cantidad `3` carga monto `1.00`. Con cantidad `0` se rechaza con "el precio unitario por la cantidad debe ser mayor que cero".
     - Con `monto` y `precio_unitario` mapeados a la vez, se usa el monto.
     - La fecha `15` (entero) y `"15"` (texto) se rechazan con "la fecha no es valida".
     - Una categoría vacía en XLSX se guarda como "General".
     - Un XLSX con encabezados y sin filas responde 200 con 0 filas.
     - Un SQL con dos `INSERT` de listas distintas expone la unión de columnas en orden.
3. Crear `POST /etl/analizar-columnas` y el campo `mapeo` en la carga.
   - **Verificar:** `cd backend; pytest tests/test_etl.py tests/test_isolation.py`. Debe cubrir:
     - La respuesta de análisis para CSV, XLSX, SQL con lista de columnas y SQL sin ella, con la forma de `muestra` descrita en "API".
     - Que el análisis no crea `Venta` ni `CargaArchivo` (contadas con el fixture `test_db`).
     - 400 por `mapeo` con un JSON mal formado y por un mapeo inválido, sin el prefijo "No se pudo leer el archivo: ".
     - 409 para un archivo duplicado aunque el mapeo sea inválido.
     - 401 sin token.
     - Que la carga sin `mapeo` sigue exigiendo los nombres exactos.
4. Agregar `ColumnMappingPanel` y el flujo en `UploadPage`.
   - **Verificar:** `cd frontend; npm test -- --run src/components/etl src/pages/UploadPage.test.tsx src/api/etl.test.ts`. Debe cubrir:
     - Que el análisis se llama al elegir el archivo.
     - Que los selectores, buscados con `within(getByRole("group", {name: "Mapeo de columnas"}))`, vienen precargados con la propuesta y sus badges.
     - Que "Cargar ventas" queda deshabilitado si falta `fecha` o si una columna se repite, con su mensaje.
     - Que el `FormData` de la carga incluye `mapeo` con la corrección del usuario.
     - Que un error del análisis muestra el `Alert` y deshabilita la carga.
     - Que cambiar de archivo limpia el mapeo e ignora la respuesta anterior.
5. Actualizar `CLAUDE.md` y `docs/planning/TASKS.md`.
   - **Verificar:** la verificación global de `docs/planning/TASKS.md` termina con código 0:
     - backend: `ruff check app/`, `mypy app/` y `pytest --cov=app`;
     - frontend: `npm run lint`, `npm run typecheck`, `npm test -- --run` y `npm run build`.

## Criterios de terminado

- Un CSV con `Item;Rubro;Total;Unidades;Fecha de venta` se carga desde la UI sin editar el archivo ni cambiar la propuesta.
- Un XLSX con `Producto, Precio Unit., Cant., Fecha` carga montos iguales a `round(precio * cantidad, 2)`.
- Un archivo con los nombres exactos produce las mismas filas y la misma `UploadResponse` que hoy, desde la UI y desde la API sin `mapeo`. Las únicas diferencias son las tres excepciones de "Compatibilidad".
- `POST /etl/analizar-columnas` no escribe en la base.

## Fuera de alcance

- La descarga del XLSX estandarizado (tarea 036).
- Un asistente de dudas (un chat que responda sobre conceptos y valores), descartado en la entrevista de diseño.
- La coincidencia aproximada de encabezados.
- Mapear valores, por ejemplo traducir nombres de categoría o códigos de producto.
- Unir varias columnas en una, como fecha y hora o día, mes y año.
- Recordar el mapeo de un usuario entre cargas.
- Mostrar en los selectores el texto original del encabezado.
- Encabezados que colisionan al normalizarse (por ejemplo "Monto" y "monto "). Se mantiene el comportamiento actual: prevalece la última columna.
- Rate limit para los endpoints de ETL.
- El reporte `/analytics/export/excel` exporta como fórmula un producto que empieza con `=` (`report_service.py:188-201`).

## STOP

- Detenerse si un test existente de `test_etl.py` o `test_etl_hardening.py` necesita modificarse. Las tres excepciones de "Compatibilidad" solo llevan tests nuevos.
- Detenerse si el test del dataset de `backend/scripts/generate_dataset.py` da una propuesta distinta de `exacto` en alguno de sus cinco roles.
- Detenerse si importar `UserFacingError` en `column_mapping.py` crea un ciclo que no se resuelve moviéndola a `errors.py`.

## Mantenimiento

`column_mapping.py` es el único lugar con sinónimos y reglas de mapeo. Para
aceptar un encabezado nuevo, se agrega al diccionario y se suma un caso en
`tests/test_column_mapping.py`. La validación de filas sigue solo en
`build_venta`.

# Plan 038: Carga de varios archivos a la vez

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** MEDIUM (rehace el flujo de `UploadPage`; la carga de un solo archivo no puede cambiar)
- **Depende de:** `docs/planning/plans/035-mapeo-columnas.md`, que introduce el análisis de columnas y el `mapeo` en la carga.
- **Categoría:** frontend
- **Origen:** hallazgo de la tarea 036 y pedido del usuario del 2026-11-10
- **Planificado en:** commit `bf0c7c7`, 2026-11-10

## Objetivo

Hoy la página de carga acepta un solo archivo. Si el usuario arrastra varios,
`UploadDropzone` (`frontend/src/components/etl/UploadDropzone.tsx:42`) toma
`event.dataTransfer.files[0]` y descarta los demás sin avisar. El selector de
archivos tampoco tiene `multiple`.

Esto se vio en la tarea 036. Se arrastraron los 9 archivos trimestrales de
Online Retail II, solo se cargó `online_retail_ii_2010Q3.csv` y los otros 8
se perdieron sin ningún mensaje (`docs/pruebas/036-datos-reales.md`).

Con esta tarea, el usuario puede soltar o elegir varios archivos de la misma
empresa:

1. La página analiza todos los archivos.
2. Los que tienen los mismos encabezados comparten un solo mapeo, que se revisa una vez.
3. Los archivos se cargan en orden, uno tras otro.
4. Al final, una tabla muestra el resultado de cada archivo.

## Decisiones

Tomadas por el usuario el 2026-11-10.

- **Solo frontend:** la página llama a los endpoints actuales una vez por archivo: `POST /etl/analizar-columnas` y `POST /etl/upload-ventas`. La API no cambia.
  - Cada archivo conserva su control de duplicado (409 por SHA-256) y sus límites de 25 MB y 200,000 filas.
  - Se descartó un endpoint por lotes: cambiaría la API y una sola petición podría superar los límites actuales.
- **Un mapeo por grupo de encabezados:**
  - Los archivos se agrupan por su lista de `columnas`, tal como la devuelve el análisis, en el mismo orden.
  - Cada grupo muestra un solo `ColumnMappingPanel`, con la lista de los archivos que abarca.
  - Si un archivo tiene encabezados distintos, forma su propio grupo y su propio mapeo.
  - Se descartaron revisar cada archivo por separado (18 revisiones para Amazon) y rechazar el grupo completo cuando no coinciden.
- **Seguir con el resto:** si un archivo falla, la carga continúa con el siguiente.
  - Se considera fallo un análisis con error, un 409, un 400, un 413 o un 500.
  - Se descartó detener el grupo, porque un duplicado obligaría a sacarlo y empezar de nuevo.
- **Orden de carga:** por nombre de archivo, en orden natural (`localeCompare` con `numeric: true`). Con nombres como `amazon_2018-S1.csv` o `iowa_2633_2012.csv`, ese orden es el cronológico. La tabla de archivos muestra ese mismo orden antes de cargar.
- **Uno a la vez:** los análisis y las cargas se hacen en serie, no en paralelo, para no cargar el servidor ni competir por la transacción de inserción.
- **Un solo archivo:** con un archivo, la página se ve y se comporta como hoy. El panel de mapeo, el botón "Cargar ventas" y `UploadSummary` no cambian. Los tests actuales de `UploadPage.test.tsx` deben pasar sin cambios.
- **Máximo de 50 archivos por selección.** Si se eligen más, no se carga ninguno y la página muestra "Puedes cargar hasta 50 archivos a la vez."

## Comportamiento

### Selección

- `UploadDropzone` recibe todos los archivos:
  - del evento `drop`, con `event.dataTransfer.files`;
  - del `input`, que pasa a tener `multiple`.
- Cada archivo pasa por `validateSalesFile` (`frontend/src/lib/fileValidation.ts`).
  - Los inválidos (formato o tamaño) quedan en la tabla con su motivo, y no se analizan ni se cargan.
  - Los válidos siguen.
- Elegir archivos nuevos reemplaza la selección anterior. Si una respuesta llega tarde para una selección vieja, se ignora, como hoy con `currentFile`.

### Análisis y grupos

1. Se analizan los archivos válidos uno a uno. La tabla muestra "Analizando 3 de 9".
2. Los archivos con la misma lista de `columnas` forman un grupo. El mapeo del grupo sale de `mappingFromAnalysis` del primer archivo, en orden de nombre.
3. Cada grupo muestra su `ColumnMappingPanel` con un título del tipo "9 archivos: online_retail_ii_2009.csv … online_retail_ii_2011Q4.csv".
4. Si el análisis de un archivo falla, queda marcado "Error al analizar", con el mensaje de `getApiErrorMessage`, y no entra en ningún grupo.

### Carga

- **"Cargar ventas"** se habilita cuando:
  - el análisis terminó;
  - hay al menos un archivo analizado sin error;
  - ningún grupo tiene `mappingProblem`.
- **Al cargar:** se sube cada archivo con el `mapeo` de su grupo, en orden de nombre. La página muestra "Cargando 3 de 9" y el dropzone queda deshabilitado.
- **Estado de cada archivo en la tabla:**

  | Estado | Cuándo |
  |---|---|
  | Cargado | La carga respondió 200 |
  | Ya cargado | La carga respondió 409 |
  | Error | Cualquier otra respuesta de error |
  | No válido | Lo rechazó `validateSalesFile` |
  | Error al analizar | Falló el análisis de columnas |

  Para los cargados se muestran las filas leídas, cargadas y rechazadas. Para los demás, el mensaje.
- **Al terminar:**
  - una fila de totales suma las filas leídas, cargadas y rechazadas de los archivos cargados;
  - al hacer clic en un archivo cargado se ve su `UploadSummary`, con los errores por fila;
  - `refreshSalesData(queryClient)` se llama una sola vez;
  - la selección queda visible hasta elegir otros archivos.

## Alcance

- `frontend/src/components/etl/UploadDropzone.tsx`:
  - pasa de `onFileSelected(file)` a `onFilesSelected(files: File[])`;
  - agrega `multiple` al `input`;
  - valida el máximo de 50 archivos.
- `frontend/src/lib/uploadBatch.ts` (nuevo): funciones puras, sin React.
  - `sortFiles(files)`: orden natural por nombre.
  - `groupByHeaders(analyses)`: agrupa por la lista de `columnas`.
  - `batchTotals(results)`: suma las filas de los archivos cargados.
  - `fileStatus(error)`: traduce un error de Axios a "Ya cargado" (409) o "Error".
- `frontend/src/components/etl/UploadBatchTable.tsx` (nuevo): la tabla de archivos con su estado, conteos, totales y el detalle de cada uno.
- `frontend/src/components/etl/index.ts`: exporta el componente nuevo.
- `frontend/src/pages/UploadPage.tsx`:
  - reemplaza el estado de un archivo por una lista de archivos con su análisis, grupo, mapeo y resultado;
  - corre el análisis y la carga en serie;
  - conserva la vista actual cuando hay un solo archivo.
- Tests:
  - `frontend/src/lib/uploadBatch.test.ts` (nuevo);
  - `frontend/src/components/etl/etl.test.tsx`: dropzone con varios archivos y la tabla;
  - `frontend/src/pages/UploadPage.test.tsx`: flujo de varios archivos. Los tests actuales no cambian.
- `CLAUDE.md`: una frase en la sección de frontend sobre la carga de varios archivos.
- `docs/planning/plans/036-datasets-reales.md`: el hallazgo del dropzone apunta a esta tarea.

No se toca el backend.

## Pasos

1. Crear `uploadBatch.ts`.
   - **Verificar:** `cd frontend; npx vitest run src/lib/uploadBatch.test.ts`. Debe cubrir:
     - `sortFiles` ordena `x_2010Q10`, `x_2010Q2` y `x_2009` como `x_2009`, `x_2010Q2`, `x_2010Q10`.
     - `groupByHeaders` junta dos archivos con las mismas columnas y separa uno con una columna más o en otro orden.
     - `batchTotals` suma solo los archivos cargados.
     - `fileStatus` da "Ya cargado" para un 409 y "Error" para un 400, un 500 y un error de red.
2. Cambiar `UploadDropzone` a varios archivos.
   - **Verificar:** `cd frontend; npx vitest run src/components/etl/etl.test.tsx`. Debe cubrir:
     - soltar tres archivos llama a `onFilesSelected` con los tres;
     - el `input` tiene `multiple`;
     - con 51 archivos no se llama a `onFilesSelected` y aparece el mensaje del límite;
     - un archivo `.txt` llega marcado como no válido, junto a los válidos.
3. Crear `UploadBatchTable`.
   - **Verificar:** RTL en `etl.test.tsx`:
     - una fila por archivo con su estado;
     - los conteos de un archivo cargado;
     - el mensaje de un archivo con error;
     - la fila de totales;
     - el `UploadSummary` al elegir un archivo.
4. Rehacer el flujo de `UploadPage`.
   - **Verificar:** `cd frontend; npx vitest run src/pages/UploadPage.test.tsx`. Los tests actuales pasan sin cambios. Tests nuevos:
     - Con tres archivos de mismos encabezados:
       - se llama a `analyzeColumns` tres veces, en orden de nombre;
       - aparece un solo panel de mapeo;
       - `uploadSales` se llama tres veces en ese orden con el mismo `mapeo`.
     - Con un archivo de encabezados distintos aparecen dos paneles, y cada archivo se sube con el `mapeo` de su grupo.
     - Si el segundo archivo responde 409:
       - el tercero se sube igual;
       - la tabla dice "Ya cargado";
       - `refreshSalesData` se llama una vez.
     - "Cargar ventas" queda deshabilitado si un grupo tiene un `mappingProblem`.
     - Elegir otra selección mientras se analiza ignora las respuestas de la anterior.
5. Actualizar `CLAUDE.md` y el hallazgo de la 036.
   - **Verificar:** la verificación global de `docs/planning/TASKS.md` termina con código 0. Desde `frontend/`:
     - `npm run lint`
     - `npm run typecheck`
     - `npm test -- --run`
     - `npm run build`

## Criterios de terminado

- Prueba en la app real, que también completa el paso 036.5 (decisión del usuario del 2026-11-10):
  - Soltar de una vez los 5 archivos de Iowa (tienda 2633) y los 18 de Amazon, cada dataset en su cuenta vacía, los carga a todos en una sola acción y con un solo mapeo revisado por dataset.
  - Las filas leídas de la tabla suman las de los archivos preparados: 95,133 en Iowa y 1,850,717 en Amazon.
  - Las cifras se registran en `docs/pruebas/036-datos-reales.md`.
- Volver a soltar los 5 archivos de Iowa marca los 5 como "Ya cargado" sin cambiar el historial.
- Un solo archivo se carga igual que antes y los tests anteriores de la página pasan sin cambios.
- Ningún archivo soltado se descarta sin aparecer en la tabla.

## Fuera de alcance

- Un endpoint de carga por lotes en el backend.
- Cargar archivos en paralelo.
- Reanudar una carga interrumpida (por ejemplo, al cerrar la pestaña). Los archivos ya cargados quedan; para el resto se vuelve a soltar la selección, y los cargados responden "Ya cargado".
- Cancelar una carga en curso.
- Unir varios archivos en uno antes de subirlo.
- La descarga del XLSX estandarizado (tarea 037).

## STOP

- Detenerse si un test actual de `UploadPage.test.tsx` o `etl.test.tsx` necesita cambiarse para que la carga de un archivo siga funcionando. Solo se aceptan tests nuevos.
- Detenerse si hace falta cambiar el backend o el contrato de `uploadSales` o `analyzeColumns`.

## Mantenimiento

- Las reglas del lote (orden, grupos, totales y estado de un error) viven solo en `frontend/src/lib/uploadBatch.ts`.
- `UploadPage` no agrupa ni ordena por su cuenta.
- Si cambia el límite de archivos por selección, se cambia en `UploadDropzone` y en su test.

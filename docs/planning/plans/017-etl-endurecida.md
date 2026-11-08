# Plan 017: Endurecer la ETL

## Estado

- **Estado:** HECHO
- **Prioridad:** P1
- **Esfuerzo:** L
- **Riesgo:** MED
- **Depende de:** `docs/planning/plans/016-alinear-migraciones.md`
- **Categoría:** backend / datos
- **Origen:** `docs/feedback/feedback-01.md` F-01, F-02, F-03, F-11, F-12, F-13 y pedido 1 del usuario
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Evitar que una carga bloquee el servidor, agote la memoria, falle por una sola
fila o duplique datos. Interpretar los montos según la nueva convención numérica.

## Decisiones tomadas

- **Montos:** solo se aceptan montos mayores que cero. No hay devoluciones.
- **Duplicados:** un archivo idéntico se rechaza con HTTP 409.
- **Coma en montos:** se aplica la regla por dígitos.

| Entrada | Resultado | Motivo |
|---|---|---|
| `1234.56` | 1234.56 | punto decimal |
| `1,234` | 1234 | coma seguida de 3 dígitos: miles |
| `1,234,567.89` | 1234567.89 | miles y decimales |
| `45,95` | 45.95 | coma seguida de 1 o 2 dígitos: decimal heredado |
| `1.234,56` | error de fila | formato europeo no admitido |
| `1234,567` | error de fila | grupo de miles inválido |

Las celdas numéricas de XLSX no pasan por esta regla: ya son números.

## Alcance

- `backend/app/api/etl_routes.py`
- `backend/app/models/models.py`
- `backend/alembic/versions/0004_*.py`
- `backend/tests/test_etl.py`

## Pasos

1. Declarar `upload_ventas` como `def` y leer con `file.file`, para que corra
   en el threadpool.
   - **Verificar:** `/health` responde mientras se procesa una carga.
2. Leer en bloques y abortar con 413 al superar `MAX_UPLOAD_BYTES`. Agregar un
   `MAX_ROWS` configurable, con valor por defecto de 200,000 filas.
   - **Verificar:** tests de archivo sobredimensionado y de exceso de filas.
     `ventas_tienda_2_anios.xlsx` (28,667 filas) se sigue cargando.
3. En XLSX, sumar el tamaño descomprimido declarado en el ZIP antes de abrirlo
   con pandas.
   - **Verificar:** un XLSX con tamaño declarado excesivo se rechaza con 413.
4. Implementar la tabla de decisiones en `_parse_amount` y usarla también al
   leer `cantidad`.
   - **Verificar:** test parametrizado con cada fila de la tabla.
5. Validar `0 < monto ≤ 99,999,999.99` y el rango de `cantidad`, y reportar la
   fila en `errores`.
   - **Verificar:** con monto negativo, cero y `1e9`, el resto del archivo se
     carga y la respuesta indica la fila.
6. Crear `RowValidationError` con mensajes controlados en español. Quitar
   `{exc}` y `str(exc)` de las respuestas y numerar las filas según el formato.
   - **Verificar:** ningún texto de pandas u `OSError` llega a la respuesta.
7. Reescribir el parser SQL: respetar comillas, mapear por nombre de columna,
   leer `cantidad` y rechazar filas sin fecha.
   - **Verificar:** `'Galletas, surtidas'` entra completo y no se usa la fecha
     de hoy.
8. Crear la tabla de cargas con `id_usuario` y `sha256`, con restricción única
   por usuario, mediante la migración `0004`.
   - **Verificar:** `alembic upgrade head`, `alembic check` y `downgrade -1`.
9. Rechazar con 409 un archivo ya cargado por ese usuario. Registrar el hash
   solo si la transacción insertó filas.
   - **Verificar:** el segundo intento devuelve 409, y otro usuario sí puede
     subir el mismo archivo.
10. Borrar los hashes del usuario en la purga del historial.
    - **Verificar:** tras purgar, el mismo archivo se puede cargar de nuevo.

## Criterios de terminado

- Una fila inválida nunca produce un 500 ni tumba el archivo.
- La inserción sigue siendo transaccional.
- La suite ETL pasa.

## STOP

- Detenerse si existen cargas previas con montos negativos o en cero en una
  base real. Esas filas no se borran sin autorización.
- No ejecutar SQL del archivo cargado.

## Limitaciones

- El hash detecta archivos idénticos. No detecta un archivo con datos repetidos
  y contenido distinto.
- Un `1,234` de un archivo antiguo que significaba 1.234 se lee como 1234.
  Esto sigue la convención pedida y debe documentarse en la pantalla de carga.

## Mantenimiento

Cualquier formato nuevo de número se agrega primero a la tabla de decisiones y
a su test parametrizado.

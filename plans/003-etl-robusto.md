# Plan 003: Hacer ETL robusto y transparente

## Estado

- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** MED
- **Depende de:** `plans/001-baseline-pruebas.md`
- **Categoría:** bug
- **Planificado en:** commit `adcb0a4`, 2026-10-17

## Objetivo

Evitar corrupción silenciosa al cargar archivos usados por PyMEs. Rechazar filas inválidas y reportar el motivo. Mantener parser `.sql` educativo sin ejecutar SQL.

## Estado actual

- `backend/app/api/etl_routes.py:26-39` convierte monto inválido a `0.0` y fecha inválida a hoy.
- `backend/app/api/etl_routes.py:90` exige UTF-8 y usa delimitador coma fijo.
- `backend/app/api/etl_routes.py:95-106` interpreta SQL con regex; no ejecuta sentencias.
- La subida limita extensión y tamaño a 25 MB.

## Alcance

- `backend/app/api/etl_routes.py`
- `backend/tests/test_etl.py`
- `backend/scripts/generate_dataset.py` solo si se necesita adaptar fixtures.

No agregar ejecución de SQL ni almacenamiento permanente de archivos.

## Pasos

1. Separar parsing de validación. Detectar delimitador común (``,``, `;`, tab) y aceptar UTF-8; usar fallback controlado para CSV latino.
   - **Verificar:** tests con CSV UTF-8 y CSV separado por `;` producen las mismas columnas.
2. Validar columnas requeridas, monto finito y fecha válida antes de crear `Venta`.
   - **Verificar:** fila inválida no se inserta y no se transforma en monto 0 o fecha actual.
3. Diseñar respuesta con total leído, total insertado y total rechazado, más errores acotados por fila.
   - **Verificar:** respuesta contiene conteos correctos y no incluye datos sensibles.
4. Mantener parser `.sql` como parser limitado de `INSERT ... VALUES`; documentar que no acepta SQL arbitrario ni valores complejos.
   - **Verificar:** fixture SQL simple pasa; no se llama a `execute` con contenido subido.
5. Hacer commit transaccional: insertar filas válidas y revertir si falla la transacción completa.
   - **Verificar:** error de DB deja cero inserciones parciales.

## Criterios de terminado

- CSV español exportado desde Excel no produce filas basura.
- Monto o fecha inválidos aparecen como rechazados.
- Parser `.sql` nunca ejecuta texto recibido.
- `pytest tests/test_etl.py -q` pasa.

## STOP

- Detenerse si el formato real no contiene columnas identificables sin decisión de producto.
- Detenerse si se requiere cambiar contrato de respuesta sin actualizar documentación API.

## Mantenimiento

Agregar un fixture por cada dialecto soportado. Toda nueva fuente de datos debe pasar por la misma validación.

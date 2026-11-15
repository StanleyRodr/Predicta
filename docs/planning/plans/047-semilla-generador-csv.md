# Plan 047: Semilla y fecha fija en el generador CSV

## Estado

- **Estado:** TODO
- **Prioridad:** P2
- **Esfuerzo:** S
- **Depende de:** —
- **Origen:** REQ-10/11; tarea C5 de `docs/reportes/verificacion_2026-11-14.md`
- **Planificado en:** commit `5dbd03d`, 2026-11-14

## Objetivo

`backend/scripts/generate_dataset.py` usa `random` sin semilla y empieza en `datetime.now()`, así que cada ejecución produce un dataset distinto. La tesis necesita una generación reproducible.

## Alcance

- `backend/scripts/generate_dataset.py`:
  - un generador `random.Random(seed)`, con semilla 2026 por defecto;
  - una fecha de inicio fija por defecto;
  - las dos configurables por argumentos.
- Un docstring que nombre a `DatosDePrueba/ventas_fabricadas/generar_ventas.py` como el generador autoritativo del dataset de la tesis.
- `backend/tests/test_generate_dataset.py` (nuevo).

## Pasos

1. Fijar la semilla y la fecha.
   - **Verificar:** una prueba genera el dataset dos veces con la misma semilla y obtiene `DataFrame` iguales; con otra semilla, obtiene uno distinto.
2. Actualizar la fila REQ-10/11 de la §10.

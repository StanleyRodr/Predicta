# Plan 052: Medición de concurrencia

## Estado

- **Estado:** HECHO el 2026-11-14.
- **Prioridad:** P1
- **Esfuerzo:** M
- **Depende de:** —
- **Origen:** decisión del autor del 2026-11-14 (pendiente #13, REQ-02 y REQ-42); tarea C6 de `docs/reportes/verificacion_2026-11-14.md`
- **Planificado en:** commit `5dbd03d`, 2026-11-14

## Objetivo

La tesis dirá que una operación larga no bloquea al resto de usuarios, porque FastAPI ejecuta el ETL y el modelo en hilos de trabajo. Esta tarea lo mide en lugar de solo afirmarlo.

## Decisiones

- **Entorno:** `uvicorn` real y una base PostgreSQL local desechable, `predicta_bench`. Se recrea en cada corrida y nunca toca la base de desarrollo (decisión del autor).
- **Medición:** p50 y p95 de `GET /analytics/stats` de un segundo usuario, primero en reposo y después durante la carga del XLSX completo hecha por un primer usuario.

## Alcance

- `backend/scripts/measure_concurrency.py` (nuevo):
  1. crea `predicta_bench` a partir de `DATABASE_URL` y aplica las migraciones;
  2. levanta `uvicorn` en un puerto libre y crea dos usuarios verificados;
  3. mide y escribe `docs/evaluacion/concurrencia.md`;
  4. al terminar, detiene el servidor y elimina la base.
- `docs/evaluacion/concurrencia.md` (nuevo): el resultado, con fecha y entorno.

## Pasos

1. Escribir y ejecutar el script.
   - **Verificar:** termina con código 0, la base `predicta_bench` ya no existe y `concurrencia.md` tiene las dos tablas.
2. Actualizar la fila REQ-42 de la §10 con el resultado.

# Plan 054: Comparación de costos frente al BI privativo

## Estado

- **Estado:** HECHO el 2026-11-14.
- **Prioridad:** P1
- **Esfuerzo:** S-M
- **Depende de:** —
- **Origen:** decisión del autor del 2026-11-14 (P-07, PE3); tarea D1 de `docs/reportes/verificacion_2026-11-14.md`
- **Planificado en:** commit `5dbd03d`, 2026-11-14

## Objetivo

La PE3 pregunta si el código abierto reduce las barreras económicas frente al BI privativo. La tesis necesita una tabla de costos con fuentes.

## Decisiones (del autor)

- **Escenarios:** 1, 5 y 10 usuarios. Con 5: 1 que diseña y 4 que consultan.
- **Hosting de Predicta:** los planes actuales de `docs/despliegue.md`, con una nota sobre Vercel Hobby, que es solo para uso no comercial.
- **Moneda:** USD de las fuentes oficiales y MXN, con el tipo de cambio y su fecha.

## Alcance

- `docs/costos/comparacion.md` (nuevo):
  - precios de Power BI y Tableau por usuario al mes;
  - costo mensual y anual de cada escenario;
  - costo de Predicta;
  - nota sobre Vercel y las alternativas;
  - fuentes con URL y fecha de consulta.

## Pasos

1. Buscar los precios oficiales y el tipo de cambio.
   - **Verificar:** cada precio tiene URL y fecha.
2. Escribir la tabla.
   - **Verificar:** los totales de cada escenario se recalculan a mano sin diferencias.
3. Cerrar la fila PE3 de la §10.

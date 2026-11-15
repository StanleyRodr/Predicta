# Plan 049: Prueba de serialización DataFrame → JSON

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** S
- **Depende de:** 048
- **Origen:** REQ-60 (escenario «Comunicación de datos» del capítulo 3); tarea C3 de `docs/reportes/verificacion_2026-11-14.md`
- **Planificado en:** commit `5dbd03d`, 2026-11-14

## Objetivo

El capítulo 3 define el escenario «DataFrame → JSON sin pérdida ni errores», pero ninguna prueba lo verifica valor por valor.

## Alcance

- `backend/tests/test_serializacion_json.py` (nuevo), con la prueba `test_serializacion_json`:
  - arma un `DataFrame` mensual conocido;
  - lo pasa por `monthly_forecast_series` y `forecast_payload`, y valida el resultado con `MonthlyForecastResponse`;
  - lo serializa a texto JSON y lo vuelve a leer;
  - compara cada periodo (ISO `YYYY-MM`), monto y cantidad con el `DataFrame` original, sin filas perdidas ni añadidas.
- Un segundo caso a través de la API (`GET /analytics/forecast`) con ventas cargadas.

## Pasos

1. Escribir las pruebas.
   - **Verificar:** `pytest tests/test_serializacion_json.py` pasa; si se altera el redondeo o se pierde una fila, falla.
2. Cerrar REQ-60 en el reporte.

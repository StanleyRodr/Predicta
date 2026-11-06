# Plan 023: Contrato de predicción y esquemas de respuesta

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** L
- **Riesgo:** MED
- **Depende de:** `docs/planning/plans/016-alinear-migraciones.md`, `docs/planning/plans/022-evaluacion-baselines.md`
- **Categoría:** backend / API
- **Origen:** `docs/feedback/feedback-01.md` F-08, F-10, F-25
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Separar consultar de guardar. Mover una proyección en la interfaz no debe
escribir en la base, y guardarla debe ser una acción explícita y consultable.

## Decisiones tomadas

Se guarda solo a pedido. Esto reemplaza la propuesta de F-08 de pasar `/predict`
a POST: si consultar ya no escribe, GET es el verbo correcto.

## Contrato

- `GET /analytics/predict`: proyección del día siguiente, sin escribir.
- `GET /analytics/forecast?categoria=`: serie mensual con historial, proyección,
  intervalos y métricas, sin escribir. También devuelve `modelo`,
  `horizonte_aplicado`, `advertencia` y `extrapolacion` por punto. El horizonte
  lo decide el backend según el plan 021.
- `POST /analytics/predicciones`: recibe `categoria`, recalcula en el servidor y
  guarda. No confía en valores enviados por el cliente.
- `GET /analytics/predicciones`: historial paginado del usuario.
- Menos de 6 meses en la proyección mensual, o menos de 2 días en `/predict`:
  HTTP 422 con `detail` en español.

## Alcance

- `backend/app/api/analytics_routes.py`, `backend/app/schemas/`
- `backend/app/models/models.py`, `backend/alembic/versions/0005_*.py`
- `frontend/src/types/forecast.ts`, `frontend/src/api/forecast.ts`

## Pasos

1. Quitar la escritura de `/predict` y devolver 422 con datos insuficientes.
   - **Verificar:** test que confirma que dos llamadas no crean filas.
2. Ajustar el frontend a ese 422 y eliminar `ForecastUnavailable`.
   - **Verificar:** RTL muestra el mensaje del `detail`.
3. Crear la migración `0005`: agregar `categoria` (nulo significa general),
   `limite_inferior`, `limite_superior` y un identificador de lote, y renombrar
   `precision_estimada` a `r2_holdout`.
   - **Verificar:** `alembic upgrade head`, `alembic check` y `downgrade -1`.
4. Comprobar que `r2_holdout` admite valores negativos grandes.
   - **Verificar:** test con un R² muy negativo, sin error de rango.
5. Crear `GET /analytics/forecast` con `categoria` normalizada mediante
   `normalize_category`.
   - **Verificar:** tests de general, categoría, categoría inexistente, 422 con
     5 meses, y advertencia con 12 meses.
6. Crear `POST` y `GET /analytics/predicciones`, con una fila por mes proyectado
   y un lote por guardado.
   - **Verificar:** tests de guardado, paginación y aislamiento entre usuarios.
7. Declarar modelos Pydantic y `response_model` en las rutas de analytics y ETL.
   - **Verificar:** `/docs` documenta cada respuesta y los tests pasan.
8. Actualizar `docs/ml-models.md`.
   - **Verificar:** el documento refleja el contrato.

## Criterios de terminado

- Ningún GET escribe en la base.
- Toda consulta de `Prediccion` filtra por `id_usuario`.
- Los tipos de `frontend/src/types/*` coinciden con OpenAPI.

## STOP

- Detenerse si existen filas en `predicciones` que la migración no pueda
  conservar. No borrar historial sin autorización.
- No usar `str(exc)` en respuestas.

## Mantenimiento

Toda ruta nueva declara `response_model`.

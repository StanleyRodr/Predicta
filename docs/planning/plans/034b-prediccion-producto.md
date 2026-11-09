# Plan 034b: Predicción e historial por producto

## Estado

- **Estado:** HECHO
- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** MEDIUM (migración que reescribe datos)
- **Depende de:** `docs/planning/plans/033-panel-info-flotante.md`
- **Categoría:** backend / frontend
- **Origen:** pedido del usuario y entrevista de diseño del 2026-11-09
- **Planificado en:** commit `a734296`, 2026-11-09

## Objetivo

Proyectar monto y cantidad de un producto, igual que hoy se proyecta una
categoría. En `/predictions` y en el historial de ventas, al elegir una
categoría aparece un segundo selector con sus productos. Por ejemplo,
"Bebidas" muestra "Coca Cola".

## Decisiones

- **Alcance:** solo predicciones e historial. El dashboard, los reportes PDF/Excel y la predicción de "Mañana" no cambian.
- **Normalización del producto:** se unifican los espacios y cada palabra empieza con mayúscula (`string.capwords`). Los acentos se mantienen: "Café" y "Cafe" son dos productos. Ejemplos: `coca  cola` pasa a `Coca Cola`, y `7up` y `Hershey's` no cambian. Se descartó `str.title()` porque convierte `Hershey's` en `Hershey'S`.
- **Datos ya cargados:** la migración `0006` reescribe `ventas.producto` con la misma regla. El downgrade no recupera la escritura original.
- **Guardado:** se agrega la columna `predicciones.producto`, que acepta nulos. `categoria` sigue guardando la categoría y `producto_referencia` guarda el producto cuando lo hay.
- **Filtro dependiente:** si `producto` llega sin `categoria`, la API responde 422. El filtro usa la pareja (categoría, producto).
- **Lista de productos:** `GET /analytics/productos?categoria=` tiene la categoría obligatoria. Devuelve los nombres ordenados y solo del usuario.
- **Historia corta:** se listan todos los productos. Uno con menos de 6 meses completos responde 422 con el mensaje en español de siempre.
- **Aviso de modelos distintos:** la proyección de un producto se compara con la de su categoría.
- **Proyecciones guardadas:** el título del lote muestra "Bebidas · Coca Cola".
- **Historial:** el producto se habilita solo con una categoría elegida. Cambiar un filtro vuelve a la página 1. No se agregan filtros de fecha.

## Alcance

- `backend/app/services/category_service.py`: agregar `normalize_product`.
- `backend/app/services/etl_service.py`: normalizar el producto al cargar.
- `backend/alembic/versions/0006_producto_normalizado.py`
- `backend/app/models/models.py`: agregar `Prediccion.producto`.
- `backend/app/services/analytics_service.py`, `prediction_service.py`, `backend/app/api/analytics_routes.py`, `backend/app/schemas/schemas.py`
- `backend/tests/`: los tests nuevos y `test_isolation.py::PRIVATE_CASES`.
- `frontend/src/api/`, `frontend/src/types/`
- `frontend/src/pages/PredictionsPage.tsx`, `frontend/src/pages/UploadPage.tsx`, `frontend/src/components/forecast/SavedPredictions.tsx`
- `docs/ml-models.md` y `CLAUDE.md`, si describen el alcance de la proyección.

## Pasos

1. Normalizar el producto en la carga y en los datos ya cargados.
   - **Verificar:** test de `normalize_product` y test ETL de que `coca  cola` se guarda como `Coca Cola`. `alembic upgrade head`, `alembic check` y `alembic downgrade -1` pasan.
2. Crear `GET /analytics/productos?categoria=`.
   - **Verificar:** tests de orden, de variantes de la categoría, de 422 sin categoría y de aislamiento.
3. Agregar `producto` a `/forecast`, `POST /predicciones` y `/ventas`.
   - **Verificar:** tests de proyección por producto, de 422 sin categoría, de 422 por historia corta, del guardado con `producto` y de la paginación filtrada.
4. Agregar el selector dependiente en predicciones, con el aviso contra la categoría y el título del lote.
   - **Verificar:** RTL de selector deshabilitado sin categoría, de la petición con ambos parámetros solo tras el clic, del aviso y de "Bebidas · Coca Cola".
5. Agregar los dos selectores al historial de ventas.
   - **Verificar:** RTL de que el cambio de filtro vuelve a la página 1 y envía `categoria` y `producto`.

## Criterios de terminado

- Elegir "Bebidas" y luego "Coca Cola" proyecta monto y cantidad solo de ese producto.
- El historial muestra solo las ventas de la pareja elegida.
- Ningún usuario ve los productos de otro.
- La verificación global de `docs/planning/TASKS.md` termina con código 0.

## STOP

- Detenerse si la migración no puede revertir la columna o si `alembic check` muestra diferencias.
- Detenerse si la normalización junta dos productos que el usuario considera distintos en el dataset de prueba.

## Mantenimiento

`normalize_product` es el único punto que canoniza nombres de producto, igual
que `normalize_category` para las categorías.

# Plan 006: Preparar schema para monto, cantidad y predicciones

## Estado

- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** HIGH
- **Depende de:** `plans/003-etl-robusto.md`, `plans/005-extraer-ml.md`
- **Categoría:** migración
- **Planificado en:** commit `adcb0a4`, 2026-10-17

## Objetivo

Permitir predicción de ingresos y unidades vendidas. Eliminar tabla `archivos`, que no usa la app, y persistir resultados de predicción.

## Estado actual

- `backend/app/models/models.py:93-104` tiene `Venta` sin cantidad.
- `backend/app/models/models.py:117-132` tiene `Prediccion.cantidad_proyectada`, pero no monto proyectado.
- `Archivo` existe en modelo y migration, pero ETL no lo escribe.
- `backend/alembic/versions/0001_initial.py` es migration actual.

## Alcance

- Nueva migration `backend/alembic/versions/0002_*.py`
- `backend/app/models/models.py`
- `backend/app/api/etl_routes.py`
- `backend/app/ml_models/` y rutas consumidoras
- `backend/scripts/generate_dataset.py`
- Tests afectados

No borrar ventas existentes ni usar `Base.metadata.create_all()` en runtime.

## Decisiones de schema

- Agregar `ventas.cantidad` como número no negativo. Definir valor para archivos antiguos, preferentemente `1` durante migración y carga omitida.
- Agregar `predicciones.monto_proyectado`.
- Mantener `cantidad_proyectada` para unidades.
- Eliminar `archivos` mediante Alembic porque no existe flujo de metadata implementado.

## Pasos

1. Actualizar modelos y generar migration autogenerada; revisar manualmente operaciones y valores existentes.
   - **Verificar:** `alembic upgrade head` termina sin error en una base de prueba.
2. Hacer `cantidad` opcional en entrada ETL con valor explícito `1` cuando fuente no la incluya; validar cantidad no negativa.
   - **Verificar:** CSV antiguo y CSV con cantidad crean ventas correctas.
3. Actualizar dataset sintético para incluir cantidad.
   - **Verificar:** `python scripts/generate_dataset.py` produce columna `cantidad`.
4. Persistir monto y cantidad proyectados en `predicciones`, sin duplicar filas dentro de una misma operación de predicción.
   - **Verificar:** test consulta predicciones y encuentra ambos valores.
5. Confirmar downgrade de migration en una base descartable.
   - **Verificar:** `alembic downgrade -1` termina sin error.

## Criterios de terminado

- Migration revisada, upgrade y downgrade verificados.
- ETL antiguo sigue funcionando con cantidad por defecto.
- Modelo puede guardar monto y unidades proyectadas.
- `archivos` deja de existir en schema y código runtime.

## STOP

- Detenerse si datos reales contienen cantidades no numéricas o negativas sin regla de negocio aprobada.
- Detenerse si downgrade destruye datos sin confirmación explícita.

## Mantenimiento

Toda modificación de modelos requiere nueva migration. No editar migrations ya aplicadas.

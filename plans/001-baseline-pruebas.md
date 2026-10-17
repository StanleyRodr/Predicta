# Plan 001: Crear baseline real de pruebas

## Estado

- **Prioridad:** P1
- **Esfuerzo:** S-M
- **Riesgo:** MED
- **Depende de:** ninguna
- **Categoría:** pruebas
- **Planificado en:** commit `adcb0a4`, 2026-10-17

## Objetivo

Los archivos `backend/tests/test_*.py` solo contienen comentarios. `pytest` no valida comportamiento y falla por ausencia de tests. Crear pruebas reales para auth, ETL y analytics antes de refactorizar.

## Estado actual

- `backend/tests/conftest.py` crea SQLite en memoria y sobrescribe `get_db`.
- `TestClient` ejecuta el lifespan de la app; el lifespan intenta conectar al PostgreSQL configurado.
- `backend/tests/test_auth.py`, `test_etl.py`, `test_analytics.py` y `test_ml.py` no tienen funciones `test_*`.
- Convención: respuestas API tienen mensajes en español.

## Alcance

Modificar únicamente:

- `backend/tests/conftest.py`, si hace falta aislar el lifespan sin perder cobertura.
- `backend/tests/test_auth.py`
- `backend/tests/test_etl.py`
- `backend/tests/test_analytics.py`
- `backend/tests/test_ml.py`

No cambiar lógica de producción en este plan.

## Pasos

1. Preparar `backend/.env` con `DATABASE_URL` y `SECRET_KEY`; confirmar PostgreSQL accesible.
   - **Verificar:** `cd backend; pytest --collect-only` debe recolectar tests sin error de importación.
2. Añadir pruebas de registro, duplicados, contraseña débil, login válido/inválido, `/users/me` autenticado/no autenticado y actualización de perfil.
   - **Verificar:** `pytest tests/test_auth.py -q` debe ejecutar y pasar todos los casos.
3. Añadir pruebas de CSV válido, formato rechazado, usuario no autenticado, historial vacío y aislamiento entre usuarios.
   - **Verificar:** `pytest tests/test_etl.py -q` debe pasar.
4. Añadir pruebas de estadísticas, categorías, evolución temporal, predicción insuficiente, predicción válida y respuestas de exportación.
   - **Verificar:** `pytest tests/test_analytics.py -q` debe pasar.
5. Añadir pruebas unitarias para features estacionales y predictor básico.
   - **Verificar:** `pytest tests/test_ml.py -q` debe pasar.

## Criterios de terminado

- `pytest --cov=app --cov-report=term-missing` termina con código 0.
- Los cuatro archivos contienen tests ejecutables, no solo comentarios.
- Existen casos positivos, negativos y de aislamiento por usuario.
- `git status` muestra solo archivos dentro del alcance.

## STOP

- Detenerse si no existe PostgreSQL accesible y no se puede aislar el lifespan sin tocar producción.
- Detenerse si los modelos o rutas no coinciden con el estado descrito.

## Mantenimiento

Cada cambio de contrato de API debe actualizar sus tests. Mantener fixtures pequeñas y reutilizables.

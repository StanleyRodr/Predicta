# Plan 009: Migrar JWT de `python-jose` a `PyJWT`

## Estado

- **Prioridad:** P2
- **Esfuerzo:** S-M
- **Riesgo:** MED
- **Depende de:** `plans/001-baseline-pruebas.md`, `plans/002-errores-seguros.md`
- **Categoría:** seguridad / dependencias
- **Planificado en:** commit `adcb0a4`, 2026-10-17

## Objetivo

Reemplazar `python-jose` por `PyJWT`, manteniendo tokens Bearer, algoritmo HS256, expiración y respuestas HTTP. JWT continúa siendo la estrategia; solo cambia la librería Python.

## Estado actual

- `backend/app/core/security.py` importa `jwt` y `JWTError` desde `jose`.
- `backend/app/api/deps.py` decodifica tokens y captura `JWTError`.
- `backend/requirements.txt` declara `python-jose[cryptography]`.
- `backend/tests/test_auth.py` cubre login y acceso autenticado.

## Alcance

- `backend/requirements.txt`
- `backend/app/core/security.py`
- `backend/app/api/deps.py`
- `backend/tests/test_auth.py` y tests JWT adicionales
- Documentación de seguridad o API afectada

No cambiar formato público de `access_token`, `token_type`, claims `sub`/`exp`, algoritmo HS256 ni duración configurada.

## Pasos

1. Revisar todos los usos actuales de `python-jose` y registrar claims usados.
   - **Verificar:** búsqueda en `backend/app/` identifica imports y usos antes de editar.
2. Sustituir dependencia por una versión estable de `PyJWT` compatible con Python soportado.
   - **Verificar:** `cd backend; pip install -r requirements.txt -r requirements-dev.txt; pip check` termina sin errores.
3. Adaptar generación, decodificación y excepciones JWT.
   - **Verificar:** login válido genera token; token malformado, sin `sub` o expirado devuelve HTTP 401.
4. Ejecutar regresiones de autenticación.
   - **Verificar:** `cd backend; pytest tests/test_auth.py -q` pasa.
5. Eliminar dependencia e imports de `python-jose`.
   - **Verificar:** búsqueda en `backend/app/` y `backend/requirements*.txt` no encuentra `jose`.
6. Actualizar documentación y ejecutar suite completa.
   - **Verificar:** `cd backend; pytest --cov=app --cov-report=term-missing` pasa.

## Criterios de terminado

- `PyJWT` es la única librería usada para firmar y validar JWT.
- Login, `/users/me`, expiración y rechazo de tokens inválidos conservan comportamiento.
- No existe importación runtime de `jose`.
- `pip check`, tests de auth y suite completa pasan.

## STOP

- Detenerse si cambia el formato de token de clientes existentes.
- Detenerse si se requiere invalidar tokens activos sin estrategia aprobada.
- Detenerse si no existe combinación compatible con Python soportado.

## Mantenimiento

Mantener algoritmo explícito en generación y validación. Nunca aceptar algoritmos provenientes del token. Revisar expiración y rotación de `SECRET_KEY` antes de producción.

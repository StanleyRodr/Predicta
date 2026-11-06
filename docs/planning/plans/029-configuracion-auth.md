# Plan 029: Configuración y autenticación

## Estado

- **Estado:** TODO
- **Prioridad:** P2
- **Esfuerzo:** M
- **Riesgo:** HIGH
- **Depende de:** `docs/planning/plans/015-ci-calidad.md`
- **Categoría:** backend / seguridad
- **Origen:** `docs/feedback/feedback-01.md` F-15, F-16
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Centralizar la configuración, cerrar CORS y reemplazar dependencias de
autenticación sin mantenimiento, sin dejar a ningún usuario fuera del sistema.

## Alcance

- `backend/app/core/config.py` (nuevo), `backend/app/core/database.py`, `backend/app/core/security.py`
- `backend/app/main.py`, `backend/app/services/user_service.py`
- `backend/app/schemas/`, `backend/requirements.txt`
- `backend/.env.example`

## Pasos

1. Crear `app/core/config.py` con `pydantic-settings` y migrar los `os.getenv`.
   - **Verificar:** una búsqueda de `os.getenv` y `load_dotenv` solo encuentra
     `config.py`. Los tests siguen arrancando con SQLite.
2. Usar por defecto el origen de Vite y rechazar `*` fuera de desarrollo.
   - **Verificar:** test de arranque con `*` en producción.
3. Reemplazar `passlib` por `bcrypt` directo o `pwdlib`.
   - **Verificar:** un hash creado con la versión anterior sigue validando.
4. Limitar la contraseña a 72 bytes.
   - **Verificar:** test con texto acentuado: se cuentan bytes, no caracteres.
5. Buscar el rol por nombre en lugar de `DEFAULT_USER_ROLE_ID = 2`.
   - **Verificar:** test con otro orden de inserción de roles.
6. Capturar `IntegrityError` en registro y perfil, y devolver 400.
   - **Verificar:** test que simula la colisión.
7. Usar `filename*=UTF-8''...` en `Content-Disposition`.
   - **Verificar:** test con un nombre de usuario acentuado.
8. Actualizar `.env.example`.
   - **Verificar:** solo tiene valores de ejemplo.

## Criterios de terminado

- Las cuentas existentes inician sesión sin cambiar la contraseña.
- CORS no admite `*` con credenciales fuera de desarrollo.

## STOP

- Detenerse si los hashes actuales no validan con la nueva librería.
- No registrar contraseñas ni tokens en logs.

## Mantenimiento

Toda variable de entorno nueva se declara en `config.py` y en `.env.example`.

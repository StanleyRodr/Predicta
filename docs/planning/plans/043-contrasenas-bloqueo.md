# Plan 043: Contraseñas, bloqueo de cuenta y revocación de sesiones

## Estado

- **Estado:** HECHO el 2026-11-14.
- **Prioridad:** P1
- **Esfuerzo:** L
- **Riesgo:** HIGH (cambia el login y la validación de cada token)
- **Depende de:** `docs/planning/plans/042-verificacion-correo.md` (servicio de correo, `token_service`, `tokens_usuario`)
- **Categoría:** backend + frontend
- **Origen:** pedido del usuario y entrevista de diseño del 2026-11-11
- **Planificado en:** commit `faa97af`, 2026-11-11

## Objetivo

Hoy no existe forma de cambiar ni de recuperar una contraseña. Un token
robado sirve hasta que vence, porque no hay manera de invalidarlo. Además,
el límite de 5 intentos por minuto es por IP: con varias IP, un atacante
puede probar contraseñas contra una sola cuenta sin freno.

Esta tarea agrega cuatro piezas:

- cambio de contraseña desde el perfil;
- restablecimiento por correo;
- bloqueo temporal de la cuenta tras intentos fallidos;
- revocación de todas las sesiones al cambiar o restablecer la contraseña.

## Decisiones

Tomadas por el usuario el 2026-11-11.

- **Cambio de contraseña:** exige la contraseña actual. La nueva cumple las reglas de la 040 y no puede ser igual a la actual. Responde con un token nuevo, así la sesión en curso sigue abierta. Las demás sesiones se cierran. Se envía un aviso al correo.
- **Restablecimiento:** enlace por correo, de un solo uso, válido 30 minutos.
  - Pedirlo siempre responde 200 con el mismo mensaje, exista o no la cuenta.
  - Usarlo cambia la contraseña, cierra todas las sesiones, quita el bloqueo y marca el correo como verificado (abrir el enlace prueba que el correo es del usuario).
  - El enlace usa el fragmento: `{FRONTEND_URL}/restablecer-contrasena#token=...`. La página envía el token por `POST`.
- **Bloqueo:** 10 contraseñas incorrectas seguidas bloquean la cuenta 15 minutos.
  - Mientras dura, el login responde 423 "Cuenta bloqueada temporalmente. Intenta en unos minutos o restablece tu contraseña.", aunque la contraseña sea correcta. Así el ataque no puede seguir probando.
  - Al bloquearse se envía un correo de aviso con un enlace de restablecimiento.
  - Un login correcto pone el contador en cero. Restablecer la contraseña quita el bloqueo.
  - Riesgo aceptado: alguien que conoce un correo puede bloquear esa cuenta 15 minutos. El dueño la desbloquea restableciendo la contraseña.
- **Revocación:** columna `version_token` en el usuario, que viaja en el JWT como claim `ver`. `get_current_user` rechaza con 401 un token cuya `ver` no coincide. Cambiar o restablecer la contraseña incrementa la versión.
  - Los tokens emitidos antes de esta tarea no tienen `ver` y se rechazan. No hay impacto: la 042 borró todos los usuarios.
- **Sesión en el frontend:** el JWT sigue en `localStorage` (decisión del usuario), mitigado con la CSP de la 045.

## API

| Ruta | Cuerpo | Respuesta | Límite |
|---|---|---|---|
| `PUT /users/me/password` | `{password_actual, password_nueva}` | 200 `{access_token, token_type}`; 400 si la actual no coincide o la nueva es igual | 5/minuto |
| `POST /users/contrasena/olvido` | `{correo_electronico}` | Siempre 200 con el mismo mensaje | 3/minuto |
| `POST /users/contrasena/restablecer` | `{token, password_nueva}` | 200; 400 genérico si el token no sirve | 10/minuto |
| `POST /users/login` | sin cambio | 423 si la cuenta está bloqueada | 5/minuto |

Orden de comprobación en el login:

1. Usuario inexistente: 401.
2. Cuenta bloqueada: 423.
3. Contraseña incorrecta: suma un fallo y responde 401. En el décimo fallo, bloquea, envía el aviso y responde 423.
4. Correo sin verificar: 403 (042).
5. Éxito: contador en cero y token con `ver`.

Para que el tiempo del 401 no revele si el correo existe, el login con un usuario inexistente también ejecuta un `bcrypt.checkpw` contra un hash fijo.

## Esquema (migración `0008`)

- `usuarios.version_token`: `Integer`, no nulo, por defecto `0`.
- `usuarios.intentos_fallidos`: `Integer`, no nulo, por defecto `0`.
- `usuarios.bloqueado_hasta`: `DateTime(timezone=True)`, nulo.
- `tokens_usuario.tipo` ya admite `restablecer` (042).

## Alcance

- `backend/app/models/models.py` y `backend/alembic/versions/0008_contrasenas_bloqueo.py` (nuevo).
- `backend/app/core/security.py`: `create_access_token` incluye `ver`; constantes `MAX_FAILED_LOGINS = 10`, `LOCKOUT_MINUTES = 15`, `RESET_TOKEN_MINUTES = 30`; hash fijo para el login de usuario inexistente.
- `backend/app/api/deps.py`: compara `ver` con `version_token`.
- `backend/app/services/user_service.py`: login con contador y bloqueo, cambio y restablecimiento.
- `backend/app/api/user_routes.py`: rutas de la tabla.
- `backend/app/services/email_service.py`: plantillas de restablecimiento, aviso de cambio y aviso de bloqueo.
- `backend/tests/test_passwords.py` y `backend/tests/test_lockout.py` (nuevos). `tests/test_isolation.py` agrega `PUT /users/me/password` a `PRIVATE_CASES`.
- Frontend:
  - `frontend/src/api/auth.ts` y tipos.
  - `frontend/src/pages/ForgotPasswordPage.tsx` (`/olvide-contrasena`) y `frontend/src/pages/ResetPasswordPage.tsx` (`/restablecer-contrasena`), públicas. La de restablecer borra el fragmento de la URL como `VerifyEmailPage`.
  - `frontend/src/pages/LoginPage.tsx`: enlace "¿Olvidaste tu contraseña?" y mensaje del 423.
  - `frontend/src/pages/ProfilePage.tsx`: sección "Cambiar contraseña"; guarda el token nuevo en `authStore`.
  - `frontend/src/lib/authSchemas.ts`: schemas con las reglas de la 040 y confirmación de la contraseña nueva.
  - Tests RTL junto a cada página.
- `CLAUDE.md` y `AGENTS.md`: claim `ver`, bloqueo y rutas nuevas.

## Pasos

1. Migración `0008`.
   - **Verificar:** `alembic upgrade head`, `alembic check`, `alembic downgrade -1` y `alembic upgrade head` pasan en PostgreSQL.
2. Revocación por `ver`.
   - **Verificar:** un token con `ver` vieja o sin `ver` responde 401 en `/users/me`; uno con la `ver` actual responde 200.
3. Cambio de contraseña.
   - **Verificar:** `cd backend; pytest tests/test_passwords.py -q`: actual incorrecta da 400; nueva igual a la actual da 400; éxito devuelve un token que funciona, el token anterior da 401 y queda un aviso en `outbox`.
4. Restablecimiento.
   - **Verificar:** el olvido responde igual con y sin cuenta y solo envía en el primer caso; el token vence a los 30 minutos (reloj simulado); sirve una sola vez; quita el bloqueo, marca el correo verificado e invalida los tokens anteriores.
5. Bloqueo.
   - **Verificar:** `cd backend; pytest tests/test_lockout.py -q`: 9 fallos y un éxito ponen el contador en cero; 10 fallos dan 423 y un correo; la contraseña correcta durante el bloqueo da 423; a los 15 minutos (reloj simulado) vuelve a entrar.
6. Frontend.
   - **Verificar:** RTL de olvido (mismo mensaje siempre), restablecer (éxito, 400, confirmación distinta), login 423 y cambio en el perfil (el token nuevo queda en `authStore`).
7. Verificación global de `docs/planning/TASKS.md`.
   - **Verificar:** todos los comandos terminan con código 0.

## Criterios de terminado

- Cambiar o restablecer la contraseña cierra toda sesión anterior.
- Ninguna respuesta de olvido revela si una cuenta existe.
- Una cuenta no acepta más de 10 contraseñas incorrectas seguidas sin bloquearse.
- Prueba real con Brevo: pedir el restablecimiento, recibir el correo, cambiar la contraseña y entrar.

## Cambios respecto del plan al ejecutarlo

- **Un solo reloj:** `security.utcnow()`. Lo usan el bloqueo, los enlaces (`token_service`) y la expiración del JWT. Los tests lo reemplazan con el fixture `clock` (`tests/conftest.py`), que arranca en la hora real porque PyJWT valida `exp` contra el reloj del sistema. No hizo falta cambiar firmas, así que la condición STOP no aplicó.
- **El aviso de bloqueo se devuelve, no se lanza:** en el intento que bloquea, el login responde con un `JSONResponse(423)`, porque FastAPI descarta los `BackgroundTasks` cuando la ruta lanza una excepción. Los intentos siguientes durante el bloqueo sí lanzan el 423 y no envían correo ni alargan el bloqueo.
- **El contador vuelve a cero al bloquear:** pasados los 15 minutos, la cuenta tiene otra vez 10 intentos.
- **`ver` estricto:** un `ver` ausente, de texto, nulo o booleano da 401. El booleano se rechaza aparte, porque en Python `True == 1`.
- **`DUMMY_HASH`** se calcula al importar `security` con una contraseña aleatoria, en vez de guardar un hash fijo en el código.
- **Login con `response_model=TokenResponse`**, y `PUT /users/me/password` responde igual.
- **Migración en la base local:** la `0008` solo agrega columnas, así que se aplicó sin STOP. Antes se probó en una base temporal `predicta_mig043` (`upgrade`, `check`, `downgrade -1` y `upgrade`); una fila existente quedó en `(0, 0, NULL)`. Las sesiones abiertas antes de la migración piden entrar de nuevo, porque su JWT no trae `ver`.
- **Frontend:** `lib/linkToken.ts` (`useLinkToken` y `MISSING_TOKEN`) es el lector del fragmento que comparten `VerifyEmailPage` y `ResetPasswordPage`. El cambio de contraseña vive en `components/auth/PasswordChangeCard.tsx`, montado en el perfil. El formulario de datos del perfil se llama "Datos de la cuenta" para distinguir sus campos en los tests. En el test de olvido con un correo inválido, el `type="email"` de jsdom frena el envío antes que Zod; se comprueba que no se llama a la API.
- **Prueba real con Brevo (2026-11-14):** el usuario, en local, pidió el restablecimiento, recibió el correo, eligió una contraseña nueva y entró; el enlace no sirvió una segunda vez. También cambió la contraseña desde el perfil y recibió el aviso, y probó el bloqueo tras 10 fallos con su correo de aviso. Todo salió bien.
- **Límites:** `PASSWORD_CHANGE_LIMIT` (5/min), `FORGOT_PASSWORD_LIMIT` (3/min) y `RESET_PASSWORD_LIMIT` (10/min), con sus tests en `tests/test_rate_limit.py`.

## Fuera de alcance

- Refresh tokens o cookies `httpOnly` (el usuario eligió `localStorage` + CSP).
- Autenticación en dos pasos.
- Historial de contraseñas anteriores.
- Lista de sesiones activas.

## STOP

- La comparación de `ver` exige consultar algo más que el usuario que `get_current_user` ya carga.
- El reloj simulado no se puede inyectar en `user_service` sin cambiar muchas firmas.

## Mantenimiento

- Toda operación que deba cerrar sesiones incrementa `version_token`. No hay otra vía de revocación.
- Los tiempos de bloqueo y de los enlaces viven como constantes en `app/core/security.py`.

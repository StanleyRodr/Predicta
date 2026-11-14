# Plan 042: Verificación de correo

## Estado

- **Estado:** HECHO el 2026-11-14.
- **Prioridad:** P1
- **Esfuerzo:** L
- **Riesgo:** HIGH (la migración borra todos los usuarios y sus datos; el login cambia para todos)
- **Depende de:** `docs/planning/plans/040-validacion-campos.md` (reglas de correo) y `docs/planning/plans/041-endurecer-api.md` (límites y configuración)
- **Categoría:** backend + frontend
- **Origen:** pedido del usuario y entrevista de diseño del 2026-11-11
- **Planificado en:** commit `faa97af`, 2026-11-11

## Objetivo

Hoy cualquiera puede registrarse con un correo ajeno o inventado. El sistema
nunca comprueba que el correo exista ni que sea de quien se registra. Sin un
correo confirmado tampoco se puede restablecer una contraseña (tarea 043).

Esta tarea agrega:

- el envío de correos por SMTP;
- la verificación obligatoria del correo al registrarse;
- el cambio de correo con confirmación.

También borra las cuentas actuales, que son de prueba.

## Decisiones

Tomadas por el usuario el 2026-11-11.

- **Verificación obligatoria.** Al registrarse llega un correo con un enlace de un solo uso, válido 24 horas. Sin verificar, el login con la contraseña correcta responde 403 "Verifica tu correo antes de iniciar sesión." y la UI ofrece reenviar el enlace.
- **Proveedor:** Brevo por SMTP, configurado solo con variables de entorno. El código usa SMTP genérico (`smtplib` con STARTTLS), así que cambiar de proveedor no toca código.
  - Variables nuevas: `EMAIL_BACKEND` (`smtp` o `console`), `SMTP_HOST`, `SMTP_PORT` (por defecto 587), `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`, `FRONTEND_URL`.
  - `console` escribe el correo en el log sin enviarlo. Es el valor de desarrollo y de tests.
  - En producción se exige `EMAIL_BACKEND=smtp` con todas sus variables. Si falta una, el arranque falla.
  - La cuenta de Brevo la crea el usuario al desplegar (paso en la guía de la 045).
- **Enlaces:** apuntan a páginas del frontend con el token en el fragmento: `{FRONTEND_URL}/verificar-correo#token=...`. El fragmento no viaja al servidor ni en la cabecera `Referer`. La página envía el token por `POST`. Ningún `GET` cambia estado.
- **Tokens:** 32 bytes aleatorios (`secrets.token_urlsafe`). Se guarda solo su SHA-256. Pedir un token nuevo invalida los anteriores del mismo tipo y usuario. Un token usado o vencido responde 400 "El enlace no es válido o ya venció.", sin distinguir la causa.
- **Cambio de correo:** `PUT /users/me` exige `password_actual` cuando cambia el correo.
  - El correo nuevo queda en `correo_pendiente`. El correo actual sigue sirviendo para entrar hasta confirmar el nuevo. Así un error de tipeo no deja a nadie fuera.
  - Se envía el enlace al correo nuevo y un aviso al anterior.
  - El correo nuevo no puede estar en uso por otra cuenta, ni como correo ni como pendiente.
- **Usuarios existentes:** la migración `0007` borra todos los usuarios. Por `ON DELETE CASCADE` se borran también sus ventas, cargas y predicciones. Los roles se conservan. Es irreversible: el `downgrade` quita las columnas, pero no devuelve los datos. Las cuentas de la tarea 036 se recrean y se recargan después si hacen falta.
- **Envío en segundo plano:** los correos salen con `BackgroundTasks`. La respuesta no espera al SMTP; así su tiempo no revela si una cuenta existe y un fallo del proveedor no da 500. Un fallo de envío queda en el log.
- **Correo duplicado en el registro:** el 400 "El correo electrónico ya se encuentra registrado." se mantiene. Revela que el correo tiene cuenta. Para una demo pública es un riesgo aceptado y queda en el informe de la 039 como informativo.

## API

| Ruta | Cuerpo | Respuesta | Límite |
|---|---|---|---|
| `POST /users/register` | sin cambio | 201; envía el enlace | 3/minuto (041) |
| `POST /users/login` | sin cambio | 403 si la contraseña es correcta y el correo no está verificado | 5/minuto |
| `POST /users/verificacion/reenviar` | `{correo_electronico}` | Siempre 200 con el mismo mensaje, exista o no la cuenta y esté o no verificada | 3/minuto |
| `POST /users/verificacion/confirmar` | `{token}` | 200 y marca el correo verificado (o aplica `correo_pendiente`); 400 genérico si el token no sirve | 10/minuto |
| `PUT /users/me` | `nombre_usuario?`, `correo_electronico?`, `password_actual?` | 200; `password_actual` obligatoria e igual a la actual si cambia el correo, si no 400 | global |

`UserResponse` agrega `correo_verificado` y `correo_pendiente`.

## Esquema (migración `0007`)

- `usuarios.correo_verificado`: `Boolean`, no nulo, por defecto `false`.
- `usuarios.correo_pendiente`: `String(100)`, nulo, único.
- Tabla nueva `tokens_usuario`:
  - `id_token` PK;
  - `id_usuario` FK a `usuarios` con `ON DELETE CASCADE`, con índice;
  - `tipo`: `String(20)`, valores `verificacion` o `restablecer` (este último lo usa la 043);
  - `token_hash`: `String(64)`, único;
  - `expira_en`: `DateTime(timezone=True)`;
  - `usado_en`: `DateTime(timezone=True)`, nulo;
  - `creado_en`: `DateTime(timezone=True)`, `server_default=now()`.
- `DELETE FROM usuarios` en el `upgrade`, antes de agregar las columnas.

## Alcance

- `backend/app/core/config.py` y `backend/.env.example`: variables de correo y validación en producción.
- `backend/app/models/models.py`: columnas nuevas y modelo `TokenUsuario`.
- `backend/alembic/versions/0007_verificacion_correo.py` (nuevo).
- `backend/app/services/email_service.py` (nuevo): `send_email(to, subject, text)` con backend `smtp` o `console`; plantillas de texto plano en español.
- `backend/app/services/token_service.py` (nuevo): crear, invalidar y consumir tokens. La 043 lo reutiliza.
- `backend/app/services/user_service.py` y `backend/app/api/user_routes.py`: rutas y reglas de la tabla.
- `backend/app/schemas/schemas.py`: schemas nuevos con las reglas de la 040.
- `backend/tests/conftest.py`: fixture `outbox` que captura los correos; `auth_headers` y `second_user` crean usuarios ya verificados.
- `backend/tests/test_email_verification.py` (nuevo).
- `backend/tests/test_isolation.py`: no cambia (las rutas nuevas son públicas), salvo que la 039 indique otra cosa.
- Frontend:
  - `frontend/src/api/auth.ts` y `frontend/src/types/`: funciones y tipos nuevos.
  - `frontend/src/pages/VerifyEmailPage.tsx` (nuevo), ruta pública `/verificar-correo`: lee `#token`, borra el fragmento de la URL con `history.replaceState`, hace el `POST` y muestra éxito o error con un enlace al login.
  - `frontend/src/pages/RegisterPage.tsx`: tras el 201 muestra "Te enviamos un enlace a tu correo" en vez de entrar.
  - `frontend/src/pages/LoginPage.tsx`: con 403 muestra el mensaje y un botón "Reenviar enlace".
  - `frontend/src/pages/ProfilePage.tsx`: campo de contraseña actual al cambiar el correo y aviso de correo pendiente.
  - Tests RTL junto a cada página.
- `CLAUDE.md` y `AGENTS.md`: verificación de correo, variables nuevas y fixture `outbox`.

## Pasos

1. Configuración y servicio de correo.
   - **Verificar:** tests de `email_service` con backend `console` y con un `smtplib.SMTP` simulado (STARTTLS, login, envío). En producción sin `SMTP_HOST`, el arranque falla.
2. Modelo, migración y borrado.
   - **STOP antes de ejecutar** `alembic upgrade head` sobre la base local: confirmar con el usuario y sugerir un respaldo con `pg_dump`.
   - **Verificar:** `alembic upgrade head`, `alembic check`, `alembic downgrade -1` y `alembic upgrade head` pasan en PostgreSQL; tras el `upgrade`, `usuarios` está vacía y `roles` no.
3. Tokens.
   - **Verificar:** `token_service` guarda solo el hash; un token vencido, usado o de otro tipo no se consume; uno nuevo invalida el anterior.
4. Registro, login y reenvío.
   - **Verificar:** `cd backend; pytest tests/test_email_verification.py -q`:
     - el registro deja un correo en `outbox` con un enlace `#token=`;
     - el login sin verificar responde 403 y con contraseña incorrecta sigue en 401;
     - el reenvío responde lo mismo para una cuenta verificada, una sin verificar y un correo sin cuenta, y solo envía en el segundo caso;
     - la confirmación verifica y permite el login; repetirla responde 400.
5. Cambio de correo.
   - **Verificar:** sin `password_actual` o con una incorrecta responde 400; con la correcta deja el correo en `correo_pendiente`, envía dos correos y el login con el correo anterior sigue funcionando; al confirmar, el correo cambia y `correo_pendiente` queda nulo.
6. Frontend.
   - **Verificar:** RTL de `VerifyEmailPage` (éxito, 400, sin token, el fragmento se borra), registro con mensaje, login 403 con reenvío y perfil con contraseña actual.
7. Verificación global de `docs/planning/TASKS.md`.
   - **Verificar:** todos los comandos terminan con código 0.

## Criterios de terminado

- Nadie inicia sesión sin haber abierto un enlace enviado a su correo.
- Ningún token se guarda en claro ni sirve dos veces.
- Ninguna respuesta del reenvío revela si una cuenta existe.
- Prueba real: con una cuenta de Brevo en local, registrarse con un correo propio, recibir el enlace y entrar.

## Cambios respecto del plan al ejecutarlo

- **Migración en la base local:** el STOP se resolvió con el usuario el 2026-11-14. Se respaldó `predicta_db` con `pg_dump -Fc` (74 MB, fuera del repo, en el scratchpad de la sesión) y se aplicó la `0007`: borró 7 usuarios, 2.457.393 ventas, 33 cargas y 16 predicciones, y conservó los 2 roles. Antes se probó en una base temporal `predicta_mig042`: con un usuario y una venta sembrados en la `0006`, el `upgrade` dejó `usuarios` y `ventas` vacías y `roles` con 2; `check`, `downgrade -1` y `upgrade` pasaron. La base temporal se borró.
- **Prueba real con Brevo (2026-11-14):** el usuario creó la cuenta, verificó el remitente y configuró `smtp-relay.brevo.com:587` en su `backend/.env` local. Se registró con un correo propio, recibió el enlace, lo abrió y entró. También cambió el correo de la cuenta con éxito (enlace al nuevo y aviso al anterior), y el remitente se ve bien. Brevo no exigió dominio propio, así que el STOP no aplicó. En los tests el SMTP se prueba con un `smtplib.SMTP` simulado.
- **`uvicorn --reload` no relee el `.env`:** solo reinicia al cambiar un `.py`. En la prueba, el primer registro salió por `console` porque el `.env` cambió con el servidor ya levantado. Tras reiniciarlo, "Reenviar enlace" lo envió por Brevo.
- **`FRONTEND_URL` con `https://` en producción:** se agregó a la validación de arranque, porque un enlace a `http://localhost` en un correo real no sirve.
- **El backend `console` registra el texto decodificado** (destinatario, asunto y cuerpo), no el MIME. En quoted-printable los saltos suaves cortaban el enlace y no se podía copiar.
- **Fixture `outbox` con `autouse`:** captura los correos de todos los tests, así ninguno llama al backend real. Los helpers `last_token`, `confirm_email` y `register_verified` de `conftest.py` abren el enlace como lo haría el dueño. Los tests que registraban y entraban en el mismo paso ahora confirman el correo antes.
- **Confirmar un correo pendiente que otra cuenta tomó mientras tanto** responde 400 "El nuevo correo electronico ya esta en uso.", gasta el token y borra `correo_pendiente`. El registro no mira los correos pendientes de otras cuentas; el choque se resuelve al confirmar.
- **Mismo correo con otras mayúsculas** en `PUT /users/me` no cuenta como cambio: no pide contraseña ni envía correos.
- **`test_profile_collision_answers_400`** ahora provoca el choque con el nombre de usuario, porque cambiar el correo ya no escribe `correo_electronico`.
- **Límites:** `RESEND_VERIFICATION_LIMIT` (3/min) y `CONFIRM_LINK_LIMIT` (10/min) en `app/core/rate_limit.py`, con sus tests en `tests/test_rate_limit.py`.
- **Frontend:** `src/test/apiError.ts` arma el error de Axios en los tests de páginas. No había tests de login, registro ni perfil; se crearon.

## Fuera de alcance

- Restablecer y cambiar la contraseña, y el bloqueo (043).
- Correos en HTML. Se usa texto plano.
- Cola de reintentos de envío.
- Ocultar el correo duplicado en el registro (riesgo aceptado).

## STOP

- Antes de aplicar la migración `0007` en cualquier base con datos.
- Brevo exige un dominio propio para enviar a destinatarios externos.
- `BackgroundTasks` no permite capturar los correos en tests sin cambiar la arquitectura.

## Mantenimiento

- Todo correo sale por `email_service.send_email`. Ninguna ruta abre SMTP por su cuenta.
- Todo token de un solo uso pasa por `token_service`.

# Despliegue de Predicta

Guía para publicar Predicta por primera vez: frontend en Vercel, backend en
Railway, base de datos en Neon y correos con Brevo. Cada paso dice qué hacer y
cómo comprobar que salió bien. No hace falta leer el código.

Ningún secreto (claves, contraseñas, cadenas de conexión) se escribe en el
repositorio ni se comparte en chats. Solo se cargan en los paneles de Railway y
Vercel.

## 1. Cómo se conectan las piezas

```
 Navegador ──HTTPS──▶ Vercel (frontend React, archivos estáticos)
     │
     └──HTTPS (fetch con Bearer)──▶ Railway (API FastAPI) ──SSL──▶ Neon (PostgreSQL)
                                          │
                                          └──HTTPS (API)──▶ Brevo (correos)
```

- El navegador descarga la app desde Vercel y habla directo con la API de Railway.
- La API guarda los datos en Neon y envía los correos de verificación y de contraseña por la API HTTPS de Brevo. Railway Hobby bloquea el SMTP saliente (el puerto 587 da `TimeoutError`, comprobado el 2026-11-14), así que en Railway se usa `EMAIL_BACKEND=brevo_api`. En local sirve `smtp`.
- Railway pone un proxy delante de la API. La API lee la IP real del cliente en `X-Forwarded-For` (variable `TRUSTED_PROXIES`).

## 2. Costos y por qué esta combinación

| Servicio | Plan | Costo | Por qué |
|---|---|---|---|
| Vercel | Hobby | Gratis | Uso no comercial; una tesis entra. |
| Railway | Hobby | ~US$5/mes con US$5 de consumo incluidos | Cobra por RAM y CPU usadas; no se duerme. El backend usa ~273 MB al arrancar y ~300 MB con trabajo liviano. |
| Neon | Free | Gratis | 1 GB, sin caducidad. Se suspende tras 5 min sin uso y despierta en menos de un segundo. |
| Brevo | Free | Gratis | 300 correos por día. |

Se descartaron Render gratis (se duerme, 512 MB y su base caduca) y Render
Starter (~US$7, 512 MB). Los precios cambian; revisa las páginas oficiales:
[Railway](https://railway.com/pricing), [Neon](https://neon.com/pricing),
[Vercel](https://vercel.com/pricing) y [Brevo](https://www.brevo.com/pricing/).

## 3. Cuentas

Necesitas cuentas en GitHub (con el repositorio), Vercel y Railway (las dos con
tu cuenta de GitHub), Neon y Brevo. Railway pide una tarjeta para el plan Hobby.

Iniciar sesión con GitHub no basta para desplegar: Railway y Vercel necesitan
su **app de GitHub instalada** con acceso al repositorio. Si Railway muestra
"Could not load branches", instálala desde **New Project → Deploy from GitHub
repo → Configure GitHub App** y da acceso a `Predicta`. En GitHub aparece en
**Settings → Applications → Installed GitHub Apps**.

## 4. Brevo

La cuenta, el remitente y la clave SMTP ya existen (los creaste para la prueba
de la tarea 042). Si empiezas de cero:

1. En **Senders, Domains & Dedicated IPs → Senders**, agrega y verifica el correo remitente.
2. En **SMTP & API → SMTP**, anota el servidor (`smtp-relay.brevo.com`, puerto `587`) y el **Login** (`...@smtp-brevo.com`).
3. Pulsa **Generate a new SMTP key** y guarda la clave en un lugar seguro. Es `SMTP_PASSWORD`, para usar SMTP en local; no es la contraseña de tu cuenta.
4. Para Railway: en **SMTP & API → API Keys**, pulsa **Generate a new API key**, ponle un nombre (por ejemplo, `predicta-railway`) y guárdala. Es `BREVO_API_KEY`. Es distinta de la clave SMTP y empieza con `xkeysib-`.

**Comprobar:** en **Transactional → Logs** verás cada correo enviado.

En local, `uvicorn --reload` no relee `backend/.env`: si cambias el `.env`, reinicia el servidor.

## 5. Neon

1. Crea un proyecto llamado `predicta`, con PostgreSQL 17 y la región **AWS US East (N. Virginia)**.
2. En el panel del proyecto pulsa **Connect**. Elige la base `neondb` (o crea `predicta`) y **desactiva Connection pooling**: la API usa la conexión directa.
3. Copia la cadena. Tiene esta forma:

   ```
   postgresql://usuario:clave@ep-xxxx.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
   ```

4. Cambia el comienzo `postgresql://` por `postgresql+psycopg2://`. Ese es el valor de `DATABASE_URL`.

**Comprobar:** la cadena termina con `sslmode=require`. Sin eso, la API no arranca en producción.

## 6. Railway (backend)

1. **New Project → Deploy from GitHub repo** y elige el repositorio.
2. En el servicio, **Settings**:
   - **Source → Root Directory:** `/backend`.
2. **Config-as-code → Railway Config File:** pulsa **Add File Path** y escribe `/backend/railway.json`. Esta ruta no sigue al Root Directory: siempre se cuenta desde la raíz del repo. Ese archivo fija el arranque, la migración previa, el chequeo de salud y el reinicio. Si Railway no lo toma (en el primer despliegue del 2026-11-14 los campos de Deploy quedaron vacíos y Railpack falló con "No start command detected"), carga a mano en **Settings → Deploy** los mismos valores: Start Command `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --no-proxy-headers`, Pre-deploy Command `alembic upgrade head` y Healthcheck Path `/health/db`.
   - **Deploy → Region:** US East (Virginia), la misma zona que Neon.
   - **Branch:** la que vas a publicar (`main` después de unir la rama de seguridad).
3. **Variables** (pestaña Variables → **Raw Editor**). Una por línea:

   | Variable | Valor en producción |
   |---|---|
   | `ENVIRONMENT` | `production` |
   | `SECRET_KEY` | Nueva, de 64 caracteres: `python -c "import secrets; print(secrets.token_hex(32))"`. No reutilices la local. |
   | `DATABASE_URL` | La de Neon con `postgresql+psycopg2://` (paso 5). |
   | `CORS_ORIGINS` | `https://<tu-app>.vercel.app` (paso 8; por ahora pon el que esperas). |
   | `FRONTEND_URL` | El mismo dominio de Vercel, con `https://`. |
   | `TRUSTED_PROXIES` | `*` (ver la comprobación del paso 9). |
   | `EMAIL_BACKEND` | `brevo_api` (Railway Hobby bloquea SMTP). |
   | `BREVO_API_KEY` | La API key de Brevo (`xkeysib-...`, paso 4). |
   | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | No hacen falta con `brevo_api`; puedes borrarlas de Railway. Solo sirven con `EMAIL_BACKEND=smtp` (en local o en un plan que permita SMTP). |
   | `EMAIL_FROM` | `Predicta <tu-remitente-verificado@...>` |
   | `LOG_LEVEL` | `INFO` |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` (opcional; es el valor por defecto). |
   | `MAX_UPLOAD_ROWS` | `200000` (opcional; es el valor por defecto). |

   La API se niega a arrancar si `SECRET_KEY` tiene menos de 32 caracteres, si `DATABASE_URL` no trae `sslmode`, si falta una variable del backend de correo elegido o si `FRONTEND_URL` no empieza con `https://`. El log de Railway dice cuál falta.

4. **Settings → Networking → Generate Domain.** Edita el subdominio a `predicta-api` si está libre: `https://predicta-api.up.railway.app`. Si eliges otro, cambia ese origen en el `connect-src` de `frontend/vercel.json` y sube el cambio (si no, el build de Vercel falla a propósito).
5. **Límite de gasto:** en la configuración del workspace, **Usage → Usage Limits**, fija un límite duro (por ejemplo, US$10). Railway apaga los servicios al llegar a él en vez de cobrar más.
6. Despliega. Railway instala `requirements.txt` con Python 3.14 (`backend/.python-version`), corre `alembic upgrade head` y arranca uvicorn con un solo worker: el limitador de peticiones vive en memoria y con varios procesos cada uno contaría aparte.

**Comprobar:**

```bash
curl https://predicta-api.up.railway.app/health/db
# {"status":"ok","database":"reachable"}
```

Si la migración falla, Railway no publica la versión nueva y lo muestra en el log del pre-despliegue.

## 7. Vercel (frontend)

1. **Add New → Project** e importa el repositorio.
2. **Root Directory:** `frontend`. Vercel detecta Vite; `frontend/vercel.json` fija el comando (`npm run build`) y la salida (`dist`).
3. **Environment Variables:** `VITE_API_URL` = `https://predicta-api.up.railway.app` (el dominio del paso 6, sin barra final), en Production.
4. **Deploy.** Anota el dominio que te da (`https://<tu-app>.vercel.app`).

El build inserta la CSP en `index.html` con el origen de `VITE_API_URL`. En Vercel también compara ese origen con el de `vercel.json`: si no coinciden, el build falla y dice qué cambiar.

**Comprobar:** abre el dominio de Vercel; se ve la página de inicio. Abrir directo `https://<tu-app>.vercel.app/login` también funciona (la reescritura de `vercel.json` sirve la app en cualquier ruta).

## 8. Cerrar el círculo

1. En Railway, pon el dominio real de Vercel en `CORS_ORIGINS` y `FRONTEND_URL`.
2. Railway vuelve a desplegar solo al cambiar variables. Espera a que termine.

Las previews de Vercel (otros dominios por cada rama) no están en `CORS_ORIGINS`: muestran la interfaz, pero no pueden iniciar sesión. Es intencional.

## 9. Checklist antes de publicar

Usa `API=https://predicta-api.up.railway.app` y `WEB=https://<tu-app>.vercel.app`.

1. **Swagger oculto:** `curl -o /dev/null -w "%{http_code}\n" $API/docs` da `404`.
2. **Cabeceras de la API:** `curl -sI $API/health` muestra `strict-transport-security`, `x-content-type-options: nosniff`, `x-frame-options: DENY` y `content-security-policy`.
3. **Cabeceras del frontend:** `curl -sI $WEB` muestra `content-security-policy` (con `frame-ancestors 'none'`), `strict-transport-security`, `x-content-type-options`, `referrer-policy` y `permissions-policy`.
4. **Registro y verificación:** regístrate en `$WEB/register` con un correo tuyo. Llega el correo, el enlace abre `$WEB/verificar-correo` y confirma la cuenta.
5. **Login sin verificar:** con otra cuenta sin confirmar, el login muestra "Verifica tu correo antes de iniciar sesión." (403).
6. **Límite de login:** el sexto intento fallido en un minuto da 429:

   ```bash
   for i in 1 2 3 4 5 6; do curl -s -o /dev/null -w "%{http_code} " -X POST \
     -d "username=nadie@example.com&password=Mala12345" $API/users/login; done
   # 401 401 401 401 401 429
   ```

7. **IP real en el log:** en el log de Railway (pestaña **Deployments → View logs**), las líneas de esas peticiones muestran tu IP pública, no una IP interna de Railway.
8. **IP falsificada:** espera un minuto y repite con una IP inventada distinta en cada intento:

   ```bash
   for i in 1 2 3 4 5 6; do curl -s -o /dev/null -w "%{http_code} " -X POST \
     -H "X-Forwarded-For: 203.0.113.$i" \
     -d "username=nadie@example.com&password=Mala12345" $API/users/login; done
   ```

   Debe terminar en `429` y el log debe seguir mostrando tu IP real. Si las seis dan `401` o el log muestra `203.0.113.x`, Railway agrega la IP real al final de `X-Forwarded-For` en vez de reemplazar la cabecera, y con `TRUSTED_PROXIES=*` la API toma la de la izquierda: cualquiera podría saltarse el límite. **Detente** y cambia `TRUSTED_PROXIES` por la red del proxy de Railway antes de publicar.
9. **CSP en el navegador:** con DevTools abierto (F12 → Console), recorre login, dashboard, carga, predicciones, reportes y perfil. No debe aparecer ningún mensaje `Refused to ...`.

## 10. Si algo falla

- **Logs:** Railway, en el servicio → **Deployments → View logs** (incluye el pre-despliegue). Vercel, en el proyecto → **Deployments → (el despliegue) → Build Logs** y **Logs**.
- **Error de CORS en el navegador** (`blocked by CORS policy`): `CORS_ORIGINS` no tiene exactamente el dominio de Vercel, con `https://` y sin barra final.
- **La app no llega a la API y la consola dice `Refused to connect`:** el `connect-src` de la CSP no tiene el dominio de Railway. Revisa `VITE_API_URL` en Vercel y el `connect-src` de `frontend/vercel.json`, y vuelve a desplegar.
- **Error de SSL con la base:** `DATABASE_URL` debe tener `sslmode=require` y la conexión directa (sin `-pooler` en el host).
- **La migración falla en el pre-despliegue:** el log muestra el error de Alembic. La versión anterior sigue publicada. Corrige y vuelve a desplegar; no edites tablas a mano.
- **La API no arranca:** el log muestra un error de configuración en español (secreto corto, falta `sslmode`, falta una variable SMTP o `FRONTEND_URL` sin `https://`).
- **No llegan los correos:** revisa spam, **Transactional → Logs** en Brevo y el log de Railway (`No se pudo enviar el correo ...`). Un `TimeoutError` significa que el host bloquea SMTP: usa `EMAIL_BACKEND=brevo_api`. `Brevo respondió 401` es una API key mal copiada o borrada.
- **Memoria agotada o reinicios:** en Railway, **Metrics** muestra la RAM. Una carga de 200,000 filas puede pasar de 400 MB; es normal que suba un momento. Si el servicio se reinicia en cada carga grande, baja `MAX_UPLOAD_ROWS`.

## 11. Operación

- **Consumo:** en Railway, **Usage** muestra el gasto del mes. Si en la primera semana sin uso real pasa de US$5, revisa la memoria antes de seguir.
- **Respaldo manual** (antes de la defensa): con la cadena de Neon en su forma `postgresql://`,

  ```bash
  pg_dump "postgresql://usuario:clave@ep-xxxx.us-east-1.aws.neon.tech/neondb?sslmode=require" -Fc -f predicta.dump
  ```

  Guarda el archivo fuera del repositorio. Para restaurarlo: `pg_restore --clean -d "<cadena>" predicta.dump`.
- **Rotar `SECRET_KEY`:** genera una nueva y cámbiala en Railway. Todas las sesiones se cierran y cada usuario vuelve a entrar.
- **Rotar la clave de Brevo:** genera otra API key (o clave SMTP), cámbiala en Railway y borra la anterior en Brevo.
- **Pausar después de la tesis:** en Railway, quita el despliegue activo del servicio (menú del despliegue → **Remove**) o borra el proyecto; así deja de consumir. Neon y Vercel gratis pueden quedar como están.

## Mantenimiento de esta guía

- Una variable nueva en `backend/.env.example` se agrega a la tabla del paso 6.
- Un origen externo nuevo para el frontend (fuente, CDN, analítica) se agrega a `frontend/csp.ts` y a `frontend/vercel.json`; `src/test/csp.test.ts` exige que coincidan.
- Si cambia el dominio del frontend, actualiza `CORS_ORIGINS` y `FRONTEND_URL` en Railway. Si cambia el de la API, actualiza `VITE_API_URL` en Vercel y el `connect-src` de `frontend/vercel.json`.

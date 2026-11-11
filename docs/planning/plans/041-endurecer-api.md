# Plan 041: Rate limit, proxy, cabeceras y configuración de producción

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** MEDIUM (un límite mal puesto o una IP mal leída bloquea a usuarios legítimos)
- **Depende de:** `docs/planning/plans/039-auditoria-seguridad.md` (S-01, S-02, S-10, S-11, S-12, S-13, S-20, S-21)
- **Categoría:** backend
- **Origen:** pedido del usuario y entrevista de diseño del 2026-11-11
- **Planificado en:** commit `faa97af`, 2026-11-11

## Objetivo

Hoy solo `POST /users/login` tiene límite de peticiones (5/min, `app/api/user_routes.py:47`).
El registro, la carga de archivos y los cálculos de proyección y reportes no
tienen límite. Un script puede crear miles de cuentas o saturar la CPU con
`statsmodels` y `matplotlib`.

Además, el limitador usa `get_remote_address` (`app/core/rate_limit.py`). En un
PaaS, la app está detrás del proxy del proveedor y esa función devuelve la IP
del proxy. Un solo usuario agotaría el límite de todos.

Esta tarea también prepara la configuración para producción: cabeceras de
seguridad, Swagger oculto, `SECRET_KEY` fuerte y PostgreSQL con SSL.

## Decisiones

Tomadas por el usuario el 2026-11-11.

- **Host:** frontend en Vercel, backend en Railway (plan Hobby) y PostgreSQL en Neon (decisión del 2026-11-11). Todo se configura con variables de entorno. Los archivos del proveedor son la 045.
- **Límites por IP:**

  | Ruta | Límite |
  |---|---|
  | `POST /users/login` | 5/minuto (sin cambio) |
  | `POST /users/register` | 3/minuto |
  | `POST /etl/upload-ventas`, `POST /etl/analizar-columnas` | 10/minuto |
  | `GET /analytics/forecast`, `GET /analytics/predict`, `POST /analytics/predicciones`, `/analytics/export/*`, `/analytics/reporte-*`, `/analytics/prediccion-categorias/*` | 20/minuto |
  | Cualquier otra ruta | 120/minuto (límite global) |

  Las rutas nuevas de 042 y 043 declaran su límite en su propia tarea.
- **IP real:** `ProxyHeadersMiddleware` de uvicorn lee `X-Forwarded-For` solo si la conexión viene de un proxy confiable. Variable nueva `TRUSTED_PROXIES` (por comas; por defecto `127.0.0.1`).
  - En Railway la app solo recibe tráfico a través del proxy de Railway, que agrega `X-Forwarded-For`. Por eso allí `TRUSTED_PROXIES=*` es seguro y es el valor de producción. Antes de fijarlo, la 045 comprueba en el despliegue que la IP registrada es la del cliente.
  - Sin proxy confiable, `X-Forwarded-For` se ignora. Así nadie falsifica su IP para saltarse el límite.
- **429:** cuerpo JSON en español: `{"detail": "Demasiadas solicitudes. Intenta de nuevo en un momento."}` con cabecera `Retry-After`.
- **Almacenamiento del limitador:** en memoria, como hoy. Vale para un solo proceso; con varios workers, cada uno cuenta aparte. En Railway se despliega una réplica con un worker (045). Redis queda fuera de alcance.
- **Swagger:** `/docs`, `/redoc` y `/openapi.json` responden 404 con `ENVIRONMENT=production`. Siguen visibles en `development` y `test`.
- **Cabeceras de seguridad** en toda respuesta de la API:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: no-referrer`
  - `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'` (la API solo sirve JSON y archivos)
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`, solo en producción
  - `Cache-Control: no-store` en respuestas de rutas privadas
  - En desarrollo, `/docs` necesita scripts de CDN; la CSP estricta no se aplica a `/docs` y `/redoc` fuera de producción.
- **Tamaño del cuerpo (S-20, agregado el 2026-11-11 tras la auditoría 039):** un middleware rechaza con 413 y un mensaje en español las peticiones a `/etl/*` de más de 26 MB, y de más de 1 MB en el resto de la API. Mira `Content-Length` y, si no viene, cuenta los bytes recibidos y corta al pasar el límite. El rechazo ocurre antes de que Starlette escriba el archivo en disco. `read_limited` conserva su límite de 25 MB como segunda defensa.
- **Raíz de la API (S-21):** `GET /` deja de llamar a `url_for("swagger_ui")`, que no existe y responde 500. Devuelve el nombre y la versión, y la URL de `/docs` solo fuera de producción.
- **`SECRET_KEY` en producción:** mínimo 32 caracteres y distinta de `CHANGE_ME_GENERATE_WITH_OPENSSL`. Si no cumple, el arranque falla con un mensaje claro.
- **PostgreSQL con SSL en producción:** `DATABASE_URL` debe incluir `sslmode=require`, `verify-ca` o `verify-full`. Si no, el arranque falla. Neon entrega su cadena con `sslmode=require` y a veces `channel_binding=require`; ambos parámetros se aceptan.

## Alcance

- `backend/app/core/config.py`: `trusted_proxies` y validaciones de producción para `secret_key` y `database_url`.
- `backend/.env.example`: `TRUSTED_PROXIES` y notas de producción.
- `backend/app/core/rate_limit.py`: constantes de límites, `default_limits=["120/minute"]`, handler 429 en español.
- `backend/app/main.py`: `SlowAPIMiddleware`, `ProxyHeadersMiddleware`, middleware de cabeceras, `docs_url`/`redoc_url`/`openapi_url` según el entorno.
- `backend/app/api/user_routes.py`, `etl_routes.py`, `analytics_routes.py`: decoradores `@limiter.limit` (cada ruta con límite necesita el parámetro `request: Request`).
- Tests:
  - `backend/tests/test_rate_limit.py` (nuevo): activa el limitador solo en sus tests. Comprueba el límite de cada grupo, el 429 en español, `Retry-After`, y que dos IP distintas vía proxy confiable no comparten contador. Con un proxy no confiable, `X-Forwarded-For` se ignora.
  - `backend/tests/test_security_headers.py` (nuevo): cabeceras en rutas públicas, privadas y de error; HSTS solo en producción; Swagger 404 en producción.
  - `backend/tests/test_config.py` o el actual: `SECRET_KEY` corta o de ejemplo y `DATABASE_URL` sin SSL fallan en producción y pasan en desarrollo.
- `CLAUDE.md` y `AGENTS.md`: variable `TRUSTED_PROXIES`, reglas de producción y límites.

## Pasos

1. Validaciones de configuración.
   - **Verificar:** `cd backend; pytest tests/test_config.py -q` cubre los cuatro casos de producción y desarrollo.
2. IP real tras proxy.
   - **Verificar:** test con `X-Forwarded-For` desde `127.0.0.1` (confiable) y desde otra IP (no confiable).
3. Límites por ruta y global.
   - **Verificar:** `cd backend; pytest tests/test_rate_limit.py -q`. La petición número 4 a `/users/register` en un minuto responde 429.
4. Cabeceras, Swagger y raíz.
   - **Verificar:** `cd backend; pytest tests/test_security_headers.py -q`. `GET /` responde 200 en producción y en desarrollo.
5. Límite de tamaño del cuerpo.
   - **Verificar:** `backend/tests/test_body_limit.py` (nuevo):
     - `Content-Length` de 27 MB a `/etl/upload-ventas` da 413 sin llamar a `read_limited`;
     - un cuerpo `chunked` sin `Content-Length` que pasa los 26 MB da 413;
     - 2 MB a `/users/register` da 413;
     - un CSV de 1 MB se sigue cargando.
6. Suite completa con el limitador desactivado como hoy.
   - **Verificar:** la verificación global de `docs/planning/TASKS.md` termina con código 0. CI sigue usando `ENVIRONMENT=test`, sin SSL exigido.

## Criterios de terminado

- Toda ruta tiene un límite: el suyo o el global.
- La IP del límite es la del cliente cuando viene de un proxy confiable, y la de la conexión en otro caso.
- Con `ENVIRONMENT=production`, la app no arranca con secreto débil ni sin SSL, y no expone Swagger.

## Fuera de alcance

- Redis u otro almacenamiento compartido para el limitador.
- WAF o protección DDoS del proveedor.
- Límites por usuario autenticado (solo por IP).

## STOP

- `ProxyHeadersMiddleware` no está en la versión de uvicorn de `requirements.txt` o cambia su API.
- `psycopg2-binary` no acepta `channel_binding=require` en la cadena de Neon.
- Activar `SlowAPIMiddleware` rompe tests actuales de forma que no se arregla con `limiter.enabled = False`.

## Mantenimiento

- Los límites viven como constantes en `app/core/rate_limit.py`. Una ruta nueva costosa declara uno de ellos.
- Cambiar `TRUSTED_PROXIES` a `*` solo es seguro si la app no acepta conexiones directas de internet.

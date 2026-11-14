# Plan 045: CSP del frontend y despliegue en Vercel, Railway y Neon

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** MEDIUM (una CSP mal escrita deja la app en blanco o sin conexión al API; un despliegue mal configurado expone la API sin las defensas de 041-043)
- **Depende de:** `docs/planning/plans/041-endurecer-api.md`, `042-verificacion-correo.md` y `043-contrasenas-bloqueo.md` (variables de entorno finales)
- **Categoría:** frontend + despliegue + documentación
- **Origen:** pedido del usuario y entrevistas de diseño del 2026-11-11
- **Planificado en:** commit `faa97af`, 2026-11-11; host elegido el mismo día

## Objetivo

El usuario publicará Predicta por primera vez. Eligió esta combinación:

- **Vercel** para el frontend estático;
- **Railway** (plan Hobby) para el backend FastAPI;
- **Neon** para PostgreSQL;
- **Brevo** para los correos (042).

El JWT vive en `localStorage`. La defensa principal contra un XSS que lo robe
es una Content Security Policy estricta.

Esta tarea deja:

- la CSP;
- los archivos de configuración de Vercel y Railway;
- una guía paso a paso para el primer despliegue;
- el despliegue real comprobado.

## Decisiones

Tomadas por el usuario el 2026-11-11.

### Por qué esta combinación

- **Railway Hobby (~US$5/mes, con US$5 de consumo incluidos).** Railway cobra por la RAM y la CPU usadas. El backend ocupa unos 273 MB al arrancar y unos 300 MB con trabajo liviano (medido el 2026-11-11). Una carga de 200,000 filas puede pasar de 400 MB. En Railway eso no mata el proceso, como sí pasaría en un plan de 512 MB fijos. Además, el servicio no se duerme: el jurado no espera 30–60 s al abrir la app.
- **Neon gratis.** 1 GB por proyecto, sin cargos por excedente y sin caducidad. Un PostgreSQL en Railway consumiría del mismo crédito de US$5 y pasaría el presupuesto.
- **Vercel Hobby gratis.** Es para uso no comercial; una tesis entra.
- Descartadas:
  - Render gratis: se duerme, tiene 512 MB y su PostgreSQL gratis caduca.
  - Render Starter: ~US$7 y 512 MB.
- Los precios cambian; la guía remite a las páginas oficiales.

### Frontend (Vercel)

- **CSP en `<meta>` dentro de `frontend/index.html`**, para que también funcione con `npm run preview`:

  ```
  default-src 'self';
  script-src 'self';
  style-src 'self';
  img-src 'self' data: blob:;
  font-src 'self';
  connect-src 'self' <origen de VITE_API_URL>;
  object-src 'none';
  base-uri 'self';
  form-action 'self'
  ```

  - `connect-src` se completa en el build con el origen de `VITE_API_URL`, mediante un plugin pequeño en `vite.config.ts`.
  - Si Chart.js o Tailwind necesitan estilos en línea, se permite `style-src 'self' 'unsafe-inline'` y se documenta el motivo. `script-src` nunca lleva `'unsafe-inline'` ni `'unsafe-eval'`.
- **`frontend/vercel.json`:**
  - las cabeceras que no funcionan en `<meta>`: `Content-Security-Policy` con `frame-ancestors 'none'`, `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` y `Permissions-Policy`;
  - una reescritura de toda ruta a `/index.html`, para que `/verificar-correo` y `/restablecer-contrasena` abran bien desde el correo.
  - La CSP de la cabecera es igual a la del `<meta>` más `frame-ancestors`. Un test compara ambas.
- **Proyecto de Vercel:** raíz `frontend/`, comando `npm run build`, salida `dist/`, variable `VITE_API_URL` con la URL pública de Railway.
- **Previews de Vercel:** no se agregan a `CORS_ORIGINS`. Solo el dominio de producción habla con la API. Las previews muestran la interfaz, pero no inician sesión.

### Backend (Railway)

- **`backend/railway.json`** (config as code):
  - raíz del servicio `backend/`;
  - comando de inicio `uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-proxy-headers`, con una réplica y un worker, por el limitador en memoria de la 041. La app ya lee `X-Forwarded-For` con su propio `ProxyHeadersMiddleware` según `TRUSTED_PROXIES` (041), así que el de uvicorn se apaga para que ese sea el único lugar (cambio del 2026-11-14);
  - comando de pre-despliegue `alembic upgrade head`: si la migración falla, Railway no publica la versión nueva;
  - `healthcheckPath` en `/health/db`, para que una versión sin base no reciba tráfico;
  - reinicio ante fallos.
- **Versión de Python:** `backend/.python-version` con `3.14` (la de CI). Si el builder de Railway no ofrece 3.14, se usa 3.13, porque el código pide 3.12+. Debe ser la misma versión que corre los tests.
- **Variables en Railway:**
  - `ENVIRONMENT=production`;
  - `SECRET_KEY` nueva, generada con `python -c "import secrets; print(secrets.token_hex(32))"`;
  - `DATABASE_URL`, la de Neon, con el prefijo `postgresql+psycopg2://` y `sslmode=require`;
  - `CORS_ORIGINS` con el dominio de Vercel;
  - `TRUSTED_PROXIES=*`;
  - `FRONTEND_URL` con el dominio de Vercel;
  - `EMAIL_BACKEND=smtp`, `SMTP_HOST=smtp-relay.brevo.com`, `SMTP_PORT=587`, `SMTP_USER`, `SMTP_PASSWORD` (la clave SMTP de Brevo, no la contraseña de la cuenta) y `EMAIL_FROM`;
  - `LOG_LEVEL=INFO`.
- **Límite de gasto:** la guía indica configurar en Railway un límite de uso mensual, para que la factura no pase el monto que el usuario decida.
- **Región:** Railway y Neon en la misma región (por ejemplo, US East), para que cada consulta no cruce continentes.

### Base de datos (Neon)

- Un proyecto con una base `predicta`. La guía explica cómo copiar la cadena de conexión directa (sin pooler) y cambiar `postgresql://` por `postgresql+psycopg2://`.
- Neon se suspende tras 5 minutos sin uso y despierta en menos de un segundo. No hace falta cambiar nada.
- Los respaldos son los que da el plan gratis de Neon (historial de restauración corto). La guía explica cómo hacer un `pg_dump` manual antes de la defensa.

## Contenido de la guía (`docs/despliegue.md`)

Escrita para quien despliega por primera vez. Cada paso dice qué hacer, dónde hacer clic y cómo comprobar que salió bien.

1. Cómo se conectan las piezas: navegador → Vercel (frontend) → Railway (API) → Neon (PostgreSQL), y Railway → Brevo (correo). Incluye un diagrama simple.
2. Costos y por qué se eligió esta combinación, con enlaces a las páginas oficiales de precios.
3. Cuentas: GitHub, Vercel, Railway (con tarjeta), Neon y Brevo.
4. Brevo: crear la cuenta, verificar la dirección remitente y generar la clave SMTP.
5. Neon: crear el proyecto en la región elegida y copiar `DATABASE_URL`.
6. Railway:
   - crear el servicio desde el repositorio con raíz `backend/`;
   - cargar las variables;
   - fijar el límite de gasto;
   - generar el dominio público.
7. Vercel: importar el repositorio con raíz `frontend/`, cargar `VITE_API_URL` y desplegar.
8. Cerrar el círculo: poner el dominio de Vercel en `CORS_ORIGINS` y `FRONTEND_URL` de Railway y volver a desplegar.
9. Checklist previa a publicar, cada punto con su comando o acción:
   - `/docs` responde 404;
   - `curl -I` muestra las cabeceras en la API y en el frontend;
   - el registro envía el correo y el enlace verifica la cuenta;
   - el login sin verificar da 403;
   - el sexto login fallido en un minuto da 429;
   - el log de Railway muestra la IP del cliente, no la del proxy;
   - una petición con `X-Forwarded-For: 203.0.113.7` falsificada no cambia la IP registrada. Con `TRUSTED_PROXIES=*`, `ProxyHeadersMiddleware` toma la dirección de más a la izquierda; si Railway agrega la IP real al final en vez de reemplazar la cabecera, `*` dejaría elegir la IP y saltar el límite. En ese caso se usa la red del proxy de Railway en `TRUSTED_PROXIES` en lugar de `*` (hallado en la 041);
   - la consola del navegador no muestra violaciones de CSP.
10. Qué hacer si algo falla:
    - dónde ver los logs de Railway y Vercel;
    - error de CORS;
    - error de SSL;
    - la migración falla en el pre-despliegue;
    - se agota la memoria.
11. Operación:
    - cómo ver el consumo en Railway;
    - `pg_dump` manual;
    - rotar `SECRET_KEY` (cierra todas las sesiones) y la clave SMTP;
    - cómo pausar el servicio después de la tesis para no seguir pagando.

## Alcance

- `frontend/index.html`: `<meta http-equiv="Content-Security-Policy">`.
- `frontend/vite.config.ts`: inserta el origen de `VITE_API_URL` en `connect-src` durante el build.
- `frontend/vercel.json` (nuevo): cabeceras y reescritura.
- `frontend/src/test/` o un test de build:
  - la CSP de `dist/index.html` contiene el origen del API y no contiene `'unsafe-eval'`;
  - la CSP de `vercel.json` es igual a la del `<meta>` más `frame-ancestors`.
- `backend/railway.json` y `backend/.python-version` (nuevos).
- `docs/despliegue.md` (nuevo).
- `docs/security.md`: resumen de las defensas finales, con enlaces a la 039 y a la guía.
- `CLAUDE.md` y `AGENTS.md`: CSP, archivos de Vercel y Railway, y guía.

## Pasos

1. CSP en `index.html` con el plugin de Vite.
   - **Verificar:** `cd frontend; npm run build` genera `dist/index.html` con `connect-src 'self' https://api.ejemplo.com` cuando `VITE_API_URL=https://api.ejemplo.com`.
2. La app funciona con la CSP en local.
   - **Verificar:** con `npm run preview` y el backend local, recorrer login, dashboard, carga, predicciones y reportes en el navegador. La consola no muestra violaciones de CSP.
3. `vercel.json`.
   - **Verificar:** el test de CSP pasa y la reescritura cubre `/verificar-correo` y `/restablecer-contrasena`.
4. `railway.json` y `.python-version`.
   - **Verificar:** el JSON es válido contra el esquema de Railway (`https://railway.com/railway.schema.json`) y los comandos son iguales a los de la guía.
5. Guía de despliegue.
   - **Verificar:** cada variable de `backend/.env.example` aparece en la guía con su valor de producción. Cada punto de la checklist tiene su comando o acción.
6. Despliegue real, hecho por el usuario con la guía y con apoyo.
   - Las cuentas, la tarjeta y los secretos los maneja el usuario. Ningún secreto se escribe en el repositorio ni en el chat.
   - **Verificar:** todos los puntos de la checklist de la guía se cumplen sobre los dominios reales.
7. ZAP baseline contra los dominios reales.
   - **Verificar:** las alertas de cabeceras de la 039 desaparecen. El informe nuevo queda en `docs/seguridad/`.
8. Verificación global de `docs/planning/TASKS.md`.
   - **Verificar:** todos los comandos terminan con código 0.

## Criterios de terminado

- Predicta responde en un dominio de Vercel y otro de Railway, con HTTPS, sin suspensión y con datos en Neon.
- La build del frontend sale con CSP sin `'unsafe-eval'` ni scripts en línea.
- La guía permite repetir el despliegue desde cero sin leer el código.
- ZAP ya no reporta las cabeceras faltantes de la 039.

## Fuera de alcance

- Dominio propio y DNS. Se usan los subdominios de Vercel y Railway.
- Backups automáticos más allá de los que da Neon.
- Monitoreo y alertas, salvo los logs y gráficos de consumo que ya traen Railway y Vercel.
- Varias réplicas del backend y Redis para el limitador.
- Despliegues de preview conectados a la API.

## STOP

- Chart.js, react-chartjs-2 u otra dependencia exige `'unsafe-eval'`.
- El builder de Railway no ofrece Python 3.12 o superior.
- El consumo medido en Railway en la primera semana pasa de US$5 sin carga real: revisar la memoria antes de seguir.
- La IP registrada en Railway con `TRUSTED_PROXIES=*` no es la del cliente.
- Neon o Railway cambian sus planes de forma que la combinación ya no cabe en ~US$5/mes.

## Mantenimiento

- Una variable de entorno nueva se agrega a `.env.example`, a la guía y a Railway.
- Un origen externo nuevo (fuente, CDN, analítica) se agrega a la CSP de `index.html` y de `vercel.json`. El test exige que coincidan.
- Cambiar el dominio del frontend exige actualizar `CORS_ORIGINS` y `FRONTEND_URL` en Railway.

# Plan 045: CSP del frontend y guía de despliegue

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** MEDIUM (una CSP mal escrita deja la app en blanco o sin conexión al API)
- **Depende de:** `docs/planning/plans/041-endurecer-api.md`, `042-verificacion-correo.md` y `043-contrasenas-bloqueo.md` (variables de entorno finales)
- **Categoría:** frontend + documentación
- **Origen:** pedido del usuario y entrevista de diseño del 2026-11-11
- **Planificado en:** commit `faa97af`, 2026-11-11

## Objetivo

El usuario publicará Predicta por primera vez y aún no eligió proveedor.
El JWT vive en `localStorage`, así que la defensa principal contra un XSS que
lo robe es una Content Security Policy estricta en el frontend.

Esta tarea deja:

- una CSP que funciona en cualquier host;
- plantillas de cabeceras para los proveedores candidatos;
- una guía paso a paso para el primer despliegue.

## Decisiones

Tomadas por el usuario el 2026-11-11.

- **Host:** PaaS, por decidir. La guía cubre las combinaciones explicadas en la entrevista:
  - Vercel (frontend) + Render (backend) + Neon (PostgreSQL), la recomendada;
  - todo en Render;
  - Railway (backend y PostgreSQL) + Vercel.
- **CSP en `<meta>` dentro de `frontend/index.html`.** Funciona en cualquier host estático:

  ```
  default-src 'self';
  script-src 'self';
  style-src 'self';
  img-src 'self' data: blob:;
  font-src 'self';
  connect-src 'self' <VITE_API_URL>;
  object-src 'none';
  base-uri 'self';
  form-action 'self'
  ```

  - `connect-src` se completa en el build con el origen de `VITE_API_URL`, mediante un plugin pequeño en `vite.config.ts`.
  - `frame-ancestors` y HSTS no funcionan en `<meta>`. Van en las plantillas de cabeceras del host.
  - Si Chart.js o Tailwind necesitan estilos en línea, se permite `style-src 'self' 'unsafe-inline'` y se documenta el motivo. `script-src` nunca lleva `'unsafe-inline'` ni `'unsafe-eval'`.
- **Plantillas de cabeceras** (CSP completa con `frame-ancestors 'none'`, HSTS, `nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy`), una por proveedor:
  - `frontend/vercel.json`;
  - `frontend/public/_headers` (Netlify, Cloudflare Pages y Render static sites leen este formato o uno equivalente; la guía indica cuál);
  - reescritura de rutas a `index.html` para que `/verificar-correo` y `/restablecer-contrasena` funcionen al abrirlas desde el correo.
- **Backend en el PaaS:**
  - un solo worker: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers`, por el limitador en memoria (041);
  - `alembic upgrade head` como comando de pre-despliegue;
  - `TRUSTED_PROXIES` según el proveedor.
- **Sin archivos de infraestructura de un proveedor** para el backend (`render.yaml`, `railway.json`). Se agregan cuando el usuario elija host.

## Contenido de la guía (`docs/despliegue.md`)

1. Qué es cada pieza (frontend estático, API, PostgreSQL, SMTP) y cómo se conectan.
2. Comparación breve de las tres combinaciones, con el aviso de que precios y planes gratuitos cambian.
3. Cuentas necesarias: GitHub, proveedor elegido, Neon si aplica, Brevo.
4. Brevo: crear la cuenta, verificar el remitente, obtener las credenciales SMTP.
5. PostgreSQL: crear la base y copiar `DATABASE_URL` con `sslmode=require`.
6. Backend: variables de entorno, una por una, con su valor de producción:
   - `ENVIRONMENT=production`;
   - `SECRET_KEY` generada con `python -c "import secrets; print(secrets.token_hex(32))"`;
   - `DATABASE_URL`, `CORS_ORIGINS`, `TRUSTED_PROXIES`, `FRONTEND_URL`;
   - las variables `SMTP_*` y `EMAIL_*`.
   - Además: comando de inicio y comando de pre-despliegue.
7. Frontend: `VITE_API_URL`, comando de build, carpeta `dist` y la plantilla de cabeceras.
8. Checklist previa a publicar:
   - Swagger responde 404;
   - las cabeceras aparecen en `curl -I`;
   - el registro envía el correo;
   - el login sin verificar da 403;
   - el sexto login fallido en un minuto da 429;
   - la CSP no muestra errores en la consola del navegador.
9. Qué hacer si algo falla: logs del proveedor, error de CORS, error de SSL y la app que "se duerme" en planes gratuitos.
10. Rotar `SECRET_KEY` (cierra todas las sesiones) y la contraseña SMTP.

## Alcance

- `frontend/index.html`: `<meta http-equiv="Content-Security-Policy">`.
- `frontend/vite.config.ts`: inserta el origen de `VITE_API_URL` en `connect-src` durante el build.
- `frontend/vercel.json` y `frontend/public/_headers` (nuevos).
- `frontend/src/test/` o un test de build: la CSP del `dist/index.html` contiene el origen del API y no contiene `'unsafe-eval'`.
- `docs/despliegue.md` (nuevo).
- `docs/security.md`: resumen de las defensas finales, con enlaces a la 039 y a la guía.
- `CLAUDE.md` y `AGENTS.md`: CSP, plantillas y guía.

## Pasos

1. CSP en `index.html` con el plugin de Vite.
   - **Verificar:** `cd frontend; npm run build` genera `dist/index.html` con `connect-src 'self' https://api.ejemplo.com` cuando `VITE_API_URL=https://api.ejemplo.com`.
2. La app funciona con la CSP.
   - **Verificar:** con `npm run preview` y el backend local, recorrer login, dashboard, carga, predicciones y reportes en el navegador. La consola no muestra violaciones de CSP.
3. Plantillas de cabeceras y reescritura.
   - **Verificar:** `vercel.json` y `_headers` son JSON y texto válidos y declaran las mismas cabeceras. Un test compara la lista de cabeceras de ambas.
4. Guía de despliegue.
   - **Verificar:** cada variable de `backend/.env.example` aparece en la guía con su valor de producción. Cada punto de la checklist tiene el comando o la acción para comprobarlo.
5. ZAP baseline de nuevo contra la build con CSP y el backend en `production`.
   - **Verificar:** las alertas de cabeceras de la 039 desaparecen. El informe nuevo queda en `docs/seguridad/`.
6. Verificación global de `docs/planning/TASKS.md`.
   - **Verificar:** todos los comandos terminan con código 0.

## Criterios de terminado

- La build del frontend sale con CSP sin `'unsafe-eval'` ni scripts en línea.
- La guía permite desplegar en cualquiera de las tres combinaciones sin leer el código.
- ZAP ya no reporta las cabeceras faltantes de la 039.

## Fuera de alcance

- Elegir el proveedor y hacer el despliegue real. Lo hace el usuario con la guía.
- Dominio propio y DNS.
- Backups automáticos más allá de los que da el proveedor de PostgreSQL.
- Monitoreo y alertas.

## STOP

- Chart.js, react-chartjs-2 o una dependencia exige `'unsafe-eval'`.
- La CSP en `<meta>` bloquea algo que solo se arregla con cabeceras del host.

## Mantenimiento

- Una variable de entorno nueva se agrega también a la guía.
- Un origen externo nuevo (fuente, CDN, analítica) se agrega a la CSP de `index.html` y a las dos plantillas.

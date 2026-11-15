# Seguridad JWT

Predicta usa `PyJWT` para firmar y validar tokens Bearer con algoritmo HS256.
La migracion reemplaza `python-jose` sin cambiar el contrato publico.

- Claim de identidad: `sub`, como identificador de usuario en texto.
- Claim de versión: `ver`, comparado con `usuarios.version_token` (tarea 043).
- Claim de expiracion: `exp`, configurado por `ACCESS_TOKEN_EXPIRE_MINUTES`.
- Algoritmo: `HS256`, declarado explicitamente al crear y validar.
- Error de token invalido, expirado, sin `sub` o con `ver` vieja: HTTP 401 generico.

Desde la tarea 043, cada token lleva también `ver`, la `version_token` del
usuario. Un token sin `ver` o con una versión vieja da 401. Cambiar o
restablecer la contraseña sube la versión y cierra todas las sesiones
anteriores. Rotar `SECRET_KEY` invalida todos los tokens a la vez
(`docs/despliegue.md`, sección Operación).

## Auditorías

- `docs/seguridad/auditoria-039.md`: auditoría del 2026-11-11 (tarea 039), con hallazgos, severidad y tarea que corrige cada uno.

- `docs/seguridad/zap-baseline-039.md`: ZAP baseline en local, antes de las correcciones.
- `docs/seguridad/zap-baseline-045.md`: ZAP baseline contra los dominios reales, después de las correcciones.

## Defensas en producción (tareas 039 a 045)

| Riesgo | Defensa | Dónde |
|---|---|---|
| Fuerza bruta y abuso | Límites por IP: login 5/min, registro 3/min, carga 10/min, cómputo 20/min, resto 120/min; 429 con `Retry-After` | `backend/app/core/rate_limit.py` |
| IP falsificada | `X-Forwarded-For` solo desde `TRUSTED_PROXIES` | `backend/app/main.py`, `docs/despliegue.md` paso 9 |
| Fuerza bruta distribuida contra una cuenta | 10 fallos seguidos bloquean 15 min (423) y envían un enlace de restablecimiento | `backend/app/services/user_service.py` |
| Enumeración de cuentas | Mismo mensaje en reenvío y olvido; bcrypt contra un hash fijo si el correo no existe | `backend/app/api/user_routes.py`, `app/core/security.py` |
| Correos ajenos o inventados | Verificación obligatoria por enlace de 24 h | tarea 042 |
| Sesión robada | Revocación por `ver`; expiración de 30 min | tarea 043 |
| Tokens de enlace filtrados | Solo se guarda su SHA-256; un uso; viajan en el fragmento (`#token=`), que no llega al servidor ni al `Referer` | `backend/app/services/token_service.py` |
| XSS que robe el JWT de `localStorage` | CSP sin `unsafe-inline` ni `unsafe-eval` en scripts; `connect-src` solo al API | `frontend/csp.ts`, `frontend/vercel.json` |
| Clickjacking y rastreo | `frame-ancestors 'none'`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` | `frontend/vercel.json`, `backend/app/core/middleware.py` |
| Cuerpos enormes | 413 antes de leer: 26 MB en `/etl`, 1 MB en el resto | `backend/app/core/middleware.py` |
| Fórmulas en Excel | Apóstrofo ante `=`, `+`, `-`, `@`, tabulador y retorno | `report_service.neutralize_formula` |
| Eco de datos en errores | 422 solo con `loc`, `msg` y `type`; 500 genérico | `backend/app/main.py` |
| Configuración débil | En producción: `SECRET_KEY` de 32+, `sslmode` en la base, SMTP completo, `FRONTEND_URL` con `https://`, Swagger oculto, HSTS | `backend/app/core/config.py` |
| Dependencias y secretos | `pip-audit`, `npm audit` y gitleaks en cada push | `.github/workflows/ci.yml` |

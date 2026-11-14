# Auditoría de seguridad 039

- **Fecha:** 2026-11-11
- **Commit auditado:** `424cda1` (branch `feat/039-seguridad`)
- **Plan:** `docs/planning/plans/039-auditoria-seguridad.md`
- **Alcance:** backend (`backend/app/`), frontend (`frontend/src/`), dependencias, historial de git y la app en ejecución en local.

## Resumen

No hay hallazgos de severidad alta explotables por un usuario anónimo para leer
datos de otro usuario o ejecutar código:

- todas las consultas filtran por `id_usuario`;
- el parser SQL no ejecuta SQL;
- React escapa todo el texto que muestra.

Los riesgos principales para publicar la app son estos:

- **abuso sin freno:** rate limit solo en el login, IP del proxy compartida y subida sin límite previo;
- **cuentas:** correo sin verificar, sin recuperación de contraseña y sin bloqueo;
- **configuración de producción:** sin cabeceras de seguridad, Swagger público, sin exigir un secreto fuerte ni SSL;
- **dependencias** con avisos de seguridad.

| Severidad | Cantidad |
|---|---|
| Alta | 3 |
| Media | 12 |
| Baja | 6 |
| Informativa | 4 |

Todos los hallazgos altos y medios tienen tarea asignada. S-18, S-19 y S-20
aparecieron en esta auditoría. Pasaron por el STOP de hallazgo imprevisto y el
usuario aprobó su subtarea el 2026-11-11.

## Metodología

1. Revisión manual con la checklist del plan (9 áreas).
2. Reglas `S` de ruff (flake8-bandit) sobre `app/`, `tests/` y `scripts/`.
3. `pip-audit -r requirements.txt` (pip-audit 2.x).
4. `npm audit` y `npm audit --omit=dev` (npm de Node 24).
5. `gitleaks git` 8.30.1 sobre el historial completo.
6. OWASP ZAP 2.17.0 (paquete multiplataforma, Java 26), solo con escaneo pasivo:
   - plan de automatización con importación de `/openapi.json`, spider y espera del escaneo pasivo;
   - backend con `ENVIRONMENT=production` sobre una base PostgreSQL temporal (`predicta_zap`, borrada al terminar);
   - frontend con `npm run build` y `vite preview`.

   El informe completo está en `docs/seguridad/zap-baseline-039.md`.

## Severidad

| Severidad | Criterio |
|---|---|
| Alta | Un atacante anónimo obtiene datos de otro usuario, ejecuta código o deja la API fuera de servicio con poco esfuerzo |
| Media | Requiere una cuenta, interacción de la víctima o condiciones específicas; o debilita una defensa clave |
| Baja | Exposición de información menor o defensa en profundidad faltante |
| Informativa | Buena práctica o riesgo aceptado con mitigación |

## Hallazgos

| ID | Hallazgo | Severidad | Evidencia | Tarea | Estado |
|---|---|---|---|---|---|
| S-01 | Rate limit solo en `POST /users/login`; registro, carga y cómputo sin límite | Alta | `app/api/user_routes.py:47` es el único `@limiter.limit` | 041 | Corregido en la 041 (2026-11-14) |
| S-02 | `get_remote_address` detrás de un proxy usa la IP del proxy: un usuario agota el límite de todos | Alta | `app/core/rate_limit.py:18` | 041 | Corregido en la 041 (2026-11-14) |
| S-20 | La subida no se limita antes de recibirla: Starlette guarda todo el multipart en disco temporal y `read_limited` corta a 25 MB recién después | Alta | `app/api/etl_routes.py:68-104`, `app/services/etl_service.py:324` | 041 (041.6) | Corregido en la 041 (2026-11-14) |
| S-03 | Sin verificación de correo: cualquiera registra correos ajenos o inventados | Media | `app/api/user_routes.py:23-43` | 042 | Corregido en la 042 (2026-11-14) |
| S-04 | Sin cambio ni restablecimiento de contraseña; un token robado vale hasta que vence | Media | No existen rutas; `app/core/security.py:27` solo emite `sub` y `exp` | 043 | Corregido en la 043 (2026-11-14) |
| S-05 | Sin bloqueo por cuenta: con varias IP se prueban contraseñas contra una cuenta sin freno | Media | `app/services/user_service.py:78-90` | 043 | Corregido en la 043 (2026-11-14) |
| S-06 | Inyección de fórmulas en Excel: un producto `=HYPERLINK(...)` se exporta tal cual | Media | `app/services/report_service.py:201` (`df.to_excel` sin neutralizar) | 040 | Corregido en la 040 (2026-11-11) |
| S-07 | El correo distingue mayúsculas: `Ana@x.com` y `ana@x.com` son dos cuentas | Media | `app/services/user_service.py:29` compara por igualdad exacta | 040 | Corregido en la 040 (2026-11-11) |
| S-10 | Sin cabeceras de seguridad en API ni frontend (CSP, HSTS, `nosniff`, anti-clickjacking) | Media | ZAP 10038, 10020 y 10021 en `localhost:4173`; 10021 en la API. `curl` a `/users/me` sin esas cabeceras | 041, 045 | API corregida en la 041 (2026-11-14); frontend pendiente en la 045 |
| S-12 | `SECRET_KEY` acepta cualquier longitud desde 1 carácter, también en producción | Media | `app/core/config.py:28` (`min_length=1`) | 041 | Corregido en la 041 (2026-11-14) |
| S-13 | `DATABASE_URL` sin SSL exigido en producción | Media | `app/core/config.py:27` | 041 | Corregido en la 041 (2026-11-14) |
| S-16 | Sin escaneo de dependencias ni de secretos en CI | Media | `.github/workflows/ci.yml` no ejecuta `pip-audit`, `npm audit` ni `gitleaks` | 044 | Corregido en la 044 (2026-11-11) |
| S-18 | `PyJWT==2.10.1` con 22 avisos. Aplican a Predicta CVE-2026-32597 (`crit` ignorado) y GHSA-hxm8-2xgr-2p9m (firma con caracteres extra aceptada); el resto afecta a JWK, `PyJWKClient` y algoritmos asimétricos, que no se usan. Ninguno permite falsificar un token sin la `SECRET_KEY`. CVE-2025-45768 no tiene corrección y está disputada; la mitiga la `SECRET_KEY` mínima de S-12 | Media | `pip-audit`; `requirements.txt:16`. Versión corregida: 2.15.1 | 044 (044.0) | Corregido en la 044 (2026-11-11) |
| S-19 | `follow-redirects` 1.16.1 (alta según npm, GHSA-mrwp-f3q8-3g9p), vía `axios@1.20.0`. Solo actúa con axios en Node; en el navegador axios usa XHR, así que el impacto real es bajo. Bloquea `npm audit --omit=dev` en CI | Media | `npm audit --omit=dev`; `npm ls follow-redirects` | 044 (044.0) | Corregido en la 044 (2026-11-11) |
| S-08 | Límites distintos entre Zod y Pydantic: nombre máx. 50 y contraseña máx. 72 bytes solo en el backend | Baja | `frontend/src/lib/authSchemas.ts:3-24` vs `app/schemas/schemas.py:25-40` | 040 | Corregido en la 040 (2026-11-11) |
| S-09 | Query params `categoria` y `producto` sin `max_length` (la base acepta 100 y 150) | Baja | `app/api/analytics_routes.py:28-33` | 040 | Corregido en la 040 (2026-11-11) |
| S-11 | `/docs`, `/redoc` y `/openapi.json` públicos en producción | Baja | Con `ENVIRONMENT=production`, `GET /docs` y `GET /openapi.json` responden 200; `app/main.py:62` | 041 | Corregido en la 041 (2026-11-14) |
| S-14 | Las respuestas 422 repiten el valor recibido, incluida la contraseña del registro | Baja | `POST /users/register` con contraseña débil devuelve `"input":"secretoDebil"` | 040 | Corregido en la 040 (2026-11-11) |
| S-21 | `GET /` responde 500 siempre: `url_for("swagger_ui")` no existe. La respuesta es genérica (ZAP 90022) y no filtra datos | Baja | `app/main.py:142`; `NoMatchFound: No route exists for name "swagger_ui"` en el log | 041 (041.4) | Corregido en la 041 (2026-11-14) |
| S-22 | Diferencia de tiempo en el login: con un correo inexistente no se ejecuta bcrypt, lo que permite adivinar qué correos tienen cuenta | Baja | `app/services/user_service.py:84-86` | 043 (hash fijo ya planificado) | Corregido en la 043 (2026-11-14) |
| S-23 | Una build sin `VITE_API_URL` apunta a `http://localhost:8000`; en producción falla en silencio (contenido mixto) | Baja | `frontend/src/lib/apiUrl.ts:1-5` | — | Riesgo aceptado: la guía de la 045 exige la variable |
| S-15 | JWT en `localStorage`: un XSS podría robarlo | Informativa | `frontend/src/stores/authStore.ts:23` | 045 (CSP) | Riesgo aceptado por el usuario |
| S-17 | El 403 de `require_role` incluye el nombre del rol requerido | Informativa | `app/api/deps.py:60` | — | Riesgo aceptado: ninguna ruta usa `require_role` hoy |
| S-24 | CORS con `allow_credentials=True`, aunque la API usa Bearer y no cookies | Informativa | `app/main.py:90` | — | Sin impacto con orígenes explícitos; revisar si se agregan cookies |
| S-25 | El registro responde "El correo electrónico ya se encuentra registrado." y revela si un correo tiene cuenta | Informativa | `app/api/user_routes.py:30-34` | — | Riesgo aceptado por el usuario para la demo (plan 042) |

Las severidades de S-01, S-02 y S-20 son altas porque, en un host público,
bastan una cuenta gratuita o ninguna para dejar la API sin servicio.

## Resultado por área de la checklist

1. **Autenticación.**
   - El JWT usa HS256 fijo en creación y validación (`app/core/security.py:18`, `app/api/deps.py:31`), con `exp`.
   - Un `sub` ausente o no numérico da 401 (`deps.py:31-37`); un usuario borrado con token vigente también (`deps.py:40-41`).
   - Hallazgos: S-04, S-05, S-12, S-18, S-22.
2. **Autorización y multi-tenencia.** Sin hallazgos.
   - Toda consulta a `Venta`, `Prediccion` y `CargaArchivo` filtra por `id_usuario`: `analytics_service.py:62` y `:337`, `prediction_service.py:161`, `etl_service.py:421-479`.
   - Las rutas de analytics pasan siempre `current_user.id_usuario`.
   - `tests/test_isolation.py::PRIVATE_CASES` cubre las rutas privadas.
3. **Entrada.**
   - Los schemas validan tipos y longitudes del usuario; la paginación está acotada (`analytics_routes.py:188-189`, `:271-272`).
   - El nombre de usuario no restringe caracteres y no se rechazan caracteres de control (los cubre la 040).
   - Hallazgos: S-07, S-08, S-09.
4. **ETL.**
   - Límites de 25 MB (`etl_service.py:30`), 200,000 filas y 200 MB descomprimidos en XLSX (`:31`).
   - El parser SQL solo lee `INSERT ... VALUES`, sin ejecutar nada.
   - Producto y categoría con longitud máxima (`:286-292`).
   - Los errores de lectura van al log y la respuesta es genérica (`:352-354`).
   - Hallazgo: S-20.
5. **Salida.**
   - Los 500 son genéricos (`main.py:70-82`).
   - `Content-Disposition` es seguro con `filename*` (`analytics_routes.py:60-68`).
   - El PDF no ejecuta fórmulas.
   - Hallazgos: S-06, S-14, S-21, S-25.
6. **Configuración.**
   - CORS con orígenes explícitos; `*` solo en desarrollo (`config.py:45-53`).
   - Hallazgos: S-10, S-11, S-12, S-13, S-24.
7. **Frontend.**
   - No hay `dangerouslySetInnerHTML`, `innerHTML`, `eval`, `new Function`, `window.open` ni `href` armados con datos del usuario en `src/` (búsqueda sin resultados).
   - El 401 limpia la sesión y redirige (`src/api/http.ts:25-27`).
   - Hallazgos: S-15, S-23.
8. **Dependencias.**
   - Hallazgos: S-18, S-19.
   - Además, `npm audit` (con desarrollo) reporta 7 avisos moderados en dependencias de desarrollo (por ejemplo `minimatch`), que no llegan al build. Quedan para la actualización general pospuesta.
9. **Repositorio.**
   - gitleaks: 107 commits, ~3.57 MB, **sin secretos**.
   - `.env`, `.env.*` (salvo `.env.example`), `backend/temp_data/` y `backend/ventas_*.csv` están en `.gitignore`.
   - Los únicos CSV versionados son los resultados agregados de `docs/evaluacion/`, sin datos personales.

## Reglas `S` de ruff (bandit)

Se activaron en `backend/pyproject.toml` (`extend-select = ["S"]`). `ruff check app/` pasa.

| Regla | Dónde | Decisión |
|---|---|---|
| S105 | `app/schemas/schemas.py:15` y `:18` (`PASSWORD_HINT`, `PASSWORD_TOO_LONG`) | Falso positivo: son mensajes. `# noqa: S105` con motivo |
| S101, S105, S106, S107 | `tests/**` | Ignoradas en `per-file-ignores`: los tests usan `assert` y credenciales desechables |
| S310, S311 | `scripts/**` | Ignoradas en `per-file-ignores`: `random` genera datos sintéticos y `urlopen` usa URL fijas de datasets |

## ZAP baseline

Escaneo pasivo, sin ataques activos. 0 alertas altas, 2 medias, 2 bajas y 3 informativas.

| Alerta ZAP | Riesgo | Sitio | Hallazgo |
|---|---|---|---|
| CSP Header Not Set (10038) | Medio | frontend | S-10 |
| Missing Anti-clickjacking Header (10020) | Medio | frontend | S-10 |
| X-Content-Type-Options Header Missing (10021) | Bajo | frontend y API | S-10 |
| Application Error Disclosure (90022) | Bajo | API, `GET /` | S-21 |
| Information Disclosure - Suspicious Comments (10027) | Informativo | bundle JS | Comentarios de librerías en el bundle; sin impacto |
| Modern Web Application (10109) | Informativo | frontend | Sin impacto |
| Authentication Request Identified (10111) | Informativo | `/users/login` | Sin impacto |

La 045 repite ZAP contra los dominios reales. Las alertas 10038, 10020 y 10021 deben desaparecer.

## Riesgos aceptados

- S-15: JWT en `localStorage`, mitigado con CSP (decisión del usuario del 2026-11-11).
- S-25: el registro revela si un correo tiene cuenta (decisión del usuario del 2026-11-11).
- El bloqueo por cuenta de la 043 permite bloquear a otro usuario durante 15 minutos. Se desbloquea restableciendo la contraseña.
- El limitador guarda sus contadores en memoria y exige un solo worker (041 y 045).
- S-17, S-23 y S-24, por los motivos de la tabla.

## Fuera de alcance

- Pruebas de penetración con explotación activa (ZAP solo pasivo).
- Endurecimiento de servidor propio: el host es Vercel + Railway + Neon (plan 045).

# Plan 039: Auditoría de seguridad

## Estado

- **Estado:** HECHO el 2026-11-11. Informe en `docs/seguridad/auditoria-039.md`.
- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** LOW (solo lee código y escribe un informe; no cambia el comportamiento)
- **Depende de:** ninguna
- **Categoría:** seguridad
- **Origen:** pedido del usuario y entrevista de diseño del 2026-11-11
- **Planificado en:** commit `faa97af`, 2026-11-11

## Objetivo

Antes de publicar Predicta en un host, hay que saber qué huecos tiene.
Esta tarea revisa el código a mano y con herramientas. Produce un informe
de hallazgos con severidad en `docs/seguridad/auditoria-039.md`.

Las tareas 040 a 045 corrigen los hallazgos conocidos. Esta tarea confirma
esos hallazgos con evidencia y busca otros nuevos.

## Decisiones

Tomadas por el usuario el 2026-11-11.

- **Alcance:** auditoría y corrección. Se corrigen los hallazgos de severidad alta y media. Los bajos e informativos quedan en el informe.
- **Uso esperado:** demo pública de tesis. Cualquiera puede registrarse.
- **Herramientas:** revisión manual, `bandit` (vía reglas `S` de ruff), `gitleaks`, `pip-audit`, `npm audit` y OWASP ZAP baseline.
  - ZAP corre una sola vez contra la app en local. Usa la versión de Java (hay Java 26 en el equipo; Docker no está instalado). Su informe queda en `docs/seguridad/`. No entra en CI.
  - La integración en CI de las otras herramientas es la tarea 044. Aquí solo se ejecutan a mano.
- **Hallazgo imprevisto:** si aparece un hallazgo alto o medio que ninguna tarea 040-045 cubre, STOP. Se reporta al usuario con severidad y propuesta. Con su aprobación, se agrega como subtarea de la tarea que corresponda.

## Hallazgos conocidos al planificar

Vistos en la lectura previa del 2026-11-11. La auditoría los confirma con archivo y línea.

| ID | Hallazgo | Severidad estimada | Tarea |
|---|---|---|---|
| S-01 | Rate limit solo en `POST /users/login`; registro, carga y cómputo sin límite | Alta | 041 |
| S-02 | `get_remote_address` detrás de un proxy ve la IP del proxy: un usuario bloquea a todos | Alta | 041 |
| S-03 | Sin verificación de correo: cualquiera registra correos ajenos | Media | 042 |
| S-04 | Sin cambio ni restablecimiento de contraseña; sin revocación de tokens | Media | 043 |
| S-05 | Sin bloqueo por intentos fallidos por cuenta | Media | 043 |
| S-06 | Inyección de fórmulas en Excel: un producto `=HYPERLINK(...)` se exporta tal cual | Media | 040 |
| S-07 | El correo no se normaliza a minúsculas: `Ana@x.com` y `ana@x.com` son dos cuentas | Media | 040 |
| S-08 | Límites de campos distintos entre Zod y Pydantic (nombre máx. 50 y contraseña máx. 72 bytes solo en backend) | Baja | 040 |
| S-09 | Query params `categoria` y `producto` sin `max_length` | Baja | 040 |
| S-10 | Sin cabeceras de seguridad en API ni frontend (CSP, HSTS, nosniff, frame) | Media | 041, 045 |
| S-11 | `/docs`, `/redoc` y `/openapi.json` públicos en producción | Baja | 041 |
| S-12 | `SECRET_KEY` acepta cualquier longitud desde 1 carácter | Media | 041 |
| S-13 | `DATABASE_URL` sin SSL exigido en producción | Media | 041 |
| S-14 | Respuestas 422 de Pydantic reflejan el valor recibido (`input`) | Baja | 040 |
| S-15 | JWT en `localStorage`: un XSS lo roba. Se mantiene, mitigado con CSP | Informativa | 045 |
| S-16 | Sin escaneo de dependencias ni secretos en CI | Media | 044 |
| S-17 | `require_role` incluye el nombre del rol en el mensaje 403 | Informativa | — |

## Checklist de revisión manual

Cada punto queda en el informe como "sin hallazgo" o con un ID `S-NN`.

1. **Autenticación:** creación y validación del JWT (`app/core/security.py`, `app/api/deps.py`), algoritmo fijo, `exp`, `sub` no numérico, usuario borrado con token vigente.
2. **Autorización y multi-tenencia:** cada consulta de `Venta`, `Prediccion` y `CargaArchivo` filtra por `id_usuario`. Comparar las rutas con `tests/test_isolation.py::PRIVATE_CASES`.
3. **Entrada:** cada schema Pydantic y cada `Query`/`Form`/`File` de las rutas: tipos, longitudes, rangos, caracteres de control.
4. **ETL:** límites de bytes, filas y descompresión de XLSX; parser SQL; codificaciones; nombres de archivo en logs.
5. **Salida:** errores 500 y 422, `Content-Disposition`, exportaciones Excel y PDF, mensajes que revelan si un correo existe.
6. **Configuración:** `app/core/config.py`, CORS, `.env.example`, valores por defecto en producción.
7. **Frontend:** uso de `dangerouslySetInnerHTML`, `href` construidos con datos, almacenamiento del token, manejo del 401, `VITE_API_URL`.
8. **Dependencias:** versiones fijadas en `requirements.txt` y `package-lock.json`.
9. **Repositorio:** secretos en el historial, `.gitignore` de `.env`, `temp_data/` y CSV generados.

## Severidad

| Severidad | Criterio |
|---|---|
| Alta | Un atacante anónimo obtiene datos de otro usuario, ejecuta código o deja la API fuera de servicio con poco esfuerzo |
| Media | Requiere una cuenta, interacción de la víctima o condiciones específicas; o debilita una defensa clave |
| Baja | Exposición de información menor o defensa en profundidad faltante |
| Informativa | Buena práctica o riesgo aceptado con mitigación |

## Alcance

- `docs/seguridad/auditoria-039.md` (nuevo): resumen, metodología, tabla de hallazgos (ID, título, severidad, archivo:línea, evidencia, tarea que lo corrige, estado), riesgos aceptados.
- `docs/seguridad/zap-baseline-039.html` o `.md` (nuevo): informe de ZAP.
- `docs/security.md`: enlace al informe nuevo.
- `backend/pyproject.toml`: activar las reglas `S` de ruff (bandit). Cada excepción lleva `# noqa: S...` con motivo, o va en `per-file-ignores` para `tests/`.

No se corrige código de la aplicación en esta tarea, salvo lo que exija activar las reglas `S`.

## Pasos

1. Revisión manual con la checklist.
   - **Verificar:** cada punto de la checklist tiene un resultado en el informe, con archivo y línea.
2. Activar las reglas `S` de ruff.
   - **Verificar:** `cd backend; ruff check app/` termina con código 0. Cada `noqa: S` tiene un motivo escrito.
3. Ejecutar `pip-audit` y `npm audit`.
   - **Verificar:** `cd backend; pip-audit -r requirements.txt` y `cd frontend; npm audit --omit=dev` quedan registrados en el informe, con las CVE encontradas y su severidad.
4. Ejecutar `gitleaks` sobre el historial completo.
   - **Verificar:** `gitleaks detect --source . --redact` queda registrado. Cada coincidencia se clasifica como falso positivo o secreto real.
   - Si hay un secreto real, STOP: el usuario debe rotarlo antes de seguir.
5. Ejecutar ZAP baseline contra la app en local.
   - Backend con `ENVIRONMENT=production` y una base PostgreSQL local; frontend con `npm run build` y `npm run preview`.
   - **Verificar:** el informe de ZAP queda en `docs/seguridad/` y cada alerta está en la tabla de hallazgos.
6. Escribir el informe y asignar tareas.
   - **Verificar:** todo hallazgo alto o medio tiene tarea asignada (040-045) o pasó por el STOP de hallazgo imprevisto.

## Criterios de terminado

- `docs/seguridad/auditoria-039.md` lista S-01 a S-17 confirmados o descartados, más los nuevos.
- Ningún hallazgo alto o medio queda sin tarea.
- `ruff check app/` pasa con las reglas `S` activas.

## Fuera de alcance

- Corregir los hallazgos (tareas 040-045).
- Pruebas de penetración manuales con explotación activa.
- Endurecimiento de un servidor propio (VPS): el host será Vercel + Railway + Neon (ver la 045).

## Cambios respecto del plan al ejecutarlo

- ruff no tenía `select` propio; se agregó `[tool.ruff.lint] extend-select = ["S"]` en `backend/pyproject.toml`. También se agregaron `per-file-ignores` para `tests/` y `scripts/`.
- gitleaks se instaló con winget. ZAP no se pudo instalar con winget: su instalador y el de su JRE piden permisos de administrador. Se usó el zip multiplataforma oficial (SHA-256 verificado contra el release) con Java 26, en una carpeta temporal fuera del repositorio.
- ZAP corrió solo en modo pasivo: importación de `/openapi.json`, spider y escaneo pasivo. La API se escaneó en `127.0.0.1:8000`, porque `localhost` resolvía a IPv6, donde uvicorn no escuchaba.
- Hubo tres STOP por hallazgos imprevistos (S-18, S-19 y S-20). El usuario aprobó el 2026-11-11:
  - la subtarea 044.0 (dependencias), adelantando la 044 para que se ejecute justo después de la 039;
  - la subtarea 041.6 (límite del cuerpo).
- S-21 (500 en `GET /`) es baja y se corrige dentro de la 041, que ya cambia esa ruta.

## STOP

- Un secreto real en el historial de git.
- Un hallazgo alto o medio sin tarea que lo cubra.
- Una CVE crítica en una dependencia sin versión corregida.

## Mantenimiento

- El informe registra el commit auditado. Una auditoría nueva crea otro archivo, no sobrescribe este.

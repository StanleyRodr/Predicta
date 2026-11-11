# Plan 040: Validación de campos y exportación segura

## Estado

- **Estado:** HECHO el 2026-11-11.
- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** MEDIUM (endurece validaciones que hoy aceptan datos; los tests actuales pueden depender de lo laxo)
- **Depende de:** `docs/planning/plans/039-auditoria-seguridad.md` (S-06, S-07, S-08, S-09, S-14)
- **Categoría:** backend + frontend
- **Origen:** pedido del usuario y entrevista de diseño del 2026-11-11
- **Planificado en:** commit `faa97af`, 2026-11-11

## Objetivo

Frontend (Zod) y backend (Pydantic) validan los mismos campos con reglas
distintas. Por ejemplo, `nombre_usuario` tiene máximo 50 solo en el backend,
y el límite de 72 bytes de la contraseña tampoco existe en el frontend. El
correo distingue mayúsculas, así que `Ana@x.com` y `ana@x.com` son dos
cuentas. Los reportes Excel copian textos del usuario sin neutralizar
fórmulas.

Esta tarea deja una sola regla por campo, igual en ambos lados, y vuelve
seguros los textos exportados.

## Decisiones

Tomadas por el usuario el 2026-11-11.

- **Reglas estrictas compartidas** (tabla abajo). El backend es la autoridad; el frontend repite las reglas para dar el error antes del envío.
- **Fuente de los límites en el frontend:** `frontend/src/lib/fieldLimits.ts` con constantes. Un test del backend lee ese archivo y lo compara con las constantes de `app/schemas/schemas.py`. Si alguien cambia un lado sin el otro, el test falla.
- **Excel:** un texto que empieza con `=`, `+`, `-`, `@`, tabulador (`\t`) o retorno (`\r`) se exporta con un apóstrofo delante. Los datos guardados no cambian. Los números no se tocan. El PDF no ejecuta fórmulas y no cambia.
- **422 sin eco:** las respuestas 422 conservan `loc`, `msg` y `type` de cada error, pero quitan `input`, `ctx` y `url`.

## Reglas de campos

| Campo | Regla | Dónde |
|---|---|---|
| `correo_electronico` | Recortar espacios, pasar a minúsculas, `EmailStr`, máx. 100 (columna `String(100)`) | registro, login, perfil, olvido de contraseña |
| `nombre_usuario` | Recortar espacios, 3-50, solo letras (con tilde), dígitos, espacio, punto, guion y guion bajo | registro, perfil |
| `password` | 8-72 bytes UTF-8, una minúscula, una mayúscula, un dígito | registro, cambio y restablecimiento (043) |
| Contraseña en login | 1-72 bytes, sin reglas de fuerza | login |
| `categoria` (query y path) | máx. 100 | `/analytics/*`, incluido `/analytics/prediccion-categorias/{categoria}` |
| `producto` (query) | máx. 150 | `/analytics/*` |
| Todo texto de la API | Sin caracteres de control (`\x00`-`\x1f`, `\x7f`) | schemas y query params de texto |
| `producto` y `categoria` en la ETL | Una fila con caracteres de control se rechaza con mensaje por fila | `etl_service.build_venta` |

Expresión del nombre:

- Python: `^[\w .\-]+$` (en Python 3 `\w` incluye letras Unicode, dígitos y `_`).
- Zod: `/^[\p{L}\p{N} ._-]+$/u`.

El login busca el correo en minúsculas. Así sigue funcionando para quien escribe `Ana@x.com`.

No hace falta migración de datos: la tarea 042 borra todos los usuarios actuales. Hasta entonces, un correo guardado con mayúsculas se encuentra igual porque la búsqueda compara con `func.lower`.

## Alcance

- `backend/app/schemas/schemas.py`: constantes de límites, validadores de correo, nombre y caracteres de control; `max_length` en los textos.
- `backend/app/api/analytics_routes.py`: `max_length` en `CATEGORY` y `PRODUCT`; validación de caracteres de control.
- `backend/app/api/user_routes.py` y `backend/app/services/user_service.py`: buscar y guardar el correo en minúsculas.
- `backend/app/services/etl_service.py`: rechazar filas con caracteres de control en `producto` o `categoria`.
- `backend/app/services/report_service.py`: función `neutralize_formula(value)` aplicada a cada columna de texto antes de `to_excel`.
- `backend/app/main.py`: handler de `RequestValidationError` que quita `input`, `ctx` y `url`.
- `frontend/src/lib/fieldLimits.ts` (nuevo) y `frontend/src/lib/authSchemas.ts`: mismas reglas, incluido el máximo de 72 bytes con `TextEncoder`.
- `frontend/src/pages/*`: `maxLength` en los `input` según `fieldLimits.ts`.
- Tests:
  - `backend/tests/test_field_validation.py` (nuevo): tabla de casos válidos e inválidos por campo; correo con mayúsculas en registro y login; 422 sin `input`.
  - `backend/tests/test_field_limits_contract.py` (nuevo): compara `fieldLimits.ts` con `schemas.py`.
  - `backend/tests/test_reports.py` o el archivo de reportes actual: Excel con `=1+1`, `+5`, `-x`, `@a` y un monto negativo numérico.
  - `frontend/src/lib/authSchemas.test.ts`: casos de cada regla, incluido 72 bytes con tildes.

## Pasos

1. Constantes y reglas del backend.
   - **Verificar:** `cd backend; pytest tests/test_field_validation.py -q`. Cubre cada fila de la tabla de reglas, con un caso válido y uno inválido.
2. Correo en minúsculas.
   - **Verificar:** registrar `Ana@X.com` guarda `ana@x.com`; registrar `ana@x.com` después responde 400; login con `ANA@x.com` funciona.
3. Query params acotados.
   - **Verificar:** `categoria` de 101 caracteres responde 422 en `/analytics/forecast`; `producto` de 151 responde 422.
4. ETL rechaza caracteres de control.
   - **Verificar:** un CSV con una fila `"Pan\x00"` rechaza esa fila con mensaje y carga el resto.
5. Excel seguro.
   - **Verificar:** el Excel exportado tiene `'=1+1` como texto y el monto `-5.0` sigue siendo número.
6. 422 sin eco.
   - **Verificar:** un registro con `password` inválida responde 422 y el cuerpo no contiene la contraseña enviada.
7. Frontend con las mismas reglas.
   - **Verificar:** `cd frontend; npx vitest run src/lib/authSchemas.test.ts` y `cd backend; pytest tests/test_field_limits_contract.py -q`.
8. Verificación global de `docs/planning/TASKS.md`.
   - **Verificar:** todos los comandos terminan con código 0.

## Criterios de terminado

- Cada campo de la tabla tiene la misma regla en Zod y Pydantic, con tests en ambos lados.
- Ninguna respuesta 422 contiene el valor enviado.
- Ningún texto exportado a Excel empieza con un carácter de fórmula sin apóstrofo.

## Cambios respecto del plan al ejecutarlo

- `UserResponse` ya no hereda de `UserBase`. Declara `nombre_usuario` y `correo_electronico` como texto simple, así una cuenta guardada antes de estas reglas (con mayúsculas o caracteres que hoy se rechazan) se sigue pudiendo leer.
- `PRODUCT` ya tenía `max_length=150`; se le agregó la regla de caracteres de control. También se acotaron `GET /analytics/productos?categoria=`, el path `/analytics/prediccion-categorias/{categoria}` (100) y `/analytics/reporte-mensual/{mes}` (20).
- La contraseña también rechaza caracteres de control (`validate_new_password`, reutilizable por la 043).
- La ETL no acepta montos negativos (F-03), así que el caso "monto `-5.0` sigue siendo número" se prueba con `neutralize_formula(-5.0)`. En el Excel se comprueba que los montos `10` y `1234.5` siguen numéricos.
- La ETL comprueba los caracteres de control después de normalizar. `normalize_product` y `normalize_category` ya convierten tabulador, salto de línea y los separadores `\x1c`-`\x1f` en espacios. Lo que queda, por ejemplo `\x00`, rechaza la fila.
- Las pruebas del frontend se agregaron a `authSchemas.test.ts`, sin cambiar los casos existentes.
- `pytest --cov` muestra más `ResourceWarning` de conexiones SQLite (184). Ya pasaba antes: el commit `cbbf520` daba 110 con cobertura. Sin cobertura la suite tiene 1 warning, como antes.

## Fuera de alcance

- Cambiar los datos ya guardados.
- Sanitizar HTML: React ya escapa el texto y no hay `dangerouslySetInnerHTML` (confirmado en 039).
- Los campos nuevos de contraseña (043) usan estas reglas, pero se crean en esa tarea.

## STOP

- Un test actual falla porque dependía de una entrada ahora inválida, y el cambio afecta un caso de uso real (por ejemplo, nombres de producto con caracteres permitidos hoy en datasets reales de la 036).
- El handler de 422 rompe el formato que lee `frontend/src/lib/apiErrors.ts`.

## Mantenimiento

- Un límite nuevo se declara en `schemas.py` y en `fieldLimits.ts`; el test de contrato lo exige.
- `neutralize_formula` es el único punto de neutralización de fórmulas. Toda exportación nueva a Excel o CSV la usa.

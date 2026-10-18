# Tareas del Proyecto

Plan de trabajo backend para Predicta. Ejecutar en orden salvo tareas sin dependencia.

**Base del plan:** commit `adcb0a4`  
**Estado:** `TODO`, `EN PROGRESO`, `HECHO`, `BLOQUEADO`

## Orden de ejecución

| ID | Tarea | Plan | Prioridad | Esfuerzo | Depende de | Estado |
|---|---|---|---|---|---|---|
| 001 | Crear baseline real de pruebas | `plans/001-baseline-pruebas.md` | P1 | S-M | — | HECHO |
| 002 | Ocultar detalles internos en errores | `plans/002-errores-seguros.md` | P2 | S | 001 | HECHO |
| 003 | Hacer ETL robusto | `plans/003-etl-robusto.md` | P1 | M | 001 | HECHO |
| 004 | Normalizar categorías | `plans/004-categorias-canonicas.md` | P2 | S | 003 | HECHO |
| 005 | Extraer lógica ML | `plans/005-extraer-ml.md` | P2 | M | 001 | HECHO |
| 006 | Actualizar schema para monto y cantidad | `plans/006-schema-predicciones.md` | P1 | M | 003, 005 | HECHO |
| 007 | Formalizar RLM y métricas | `plans/007-rlm-metricas.md` | P1 | M | 005, 006 | EN PROGRESO |
| 008 | Agregar filtros de fecha | `plans/008-filtros-fecha.md` | P2 | S | 001 | TODO |
| 009 | Migrar JWT de `python-jose` a `PyJWT` | `plans/009-migrar-pyjwt.md` | P2 | S-M | 001, 002 | TODO |

## Reglas de ejecución

- Leer el plan completo antes de modificar código.
- Ejecutar cada verificación indicada antes de avanzar.
- Si aparece una condición STOP, detenerse y reportar; no improvisar.
- Actualizar estado de tarea en esta tabla al iniciar, terminar o bloquearse.
- No modificar `README.md` raíz como parte de estas tareas.
- No crear un índice dentro de `plans/`; esa función pertenece a este archivo.

## Subtareas detalladas

### Tarea 001 — Crear baseline real de pruebas

Plan: `plans/001-baseline-pruebas.md` | Depende de: ninguna | Esfuerzo: S-M

- [x] 001.1 Configurar entorno de pruebas aislado en SQLite, con `DATABASE_URL` y `SECRET_KEY` definidos antes de importar la app. Verificar: `cd backend; pytest --collect-only` recolecta 26 tests sin error.
- [x] 001.2 Crear pruebas de registro, duplicados, contraseña débil, login, `/users/me` y actualización de perfil. Verificar: `cd backend; pytest tests/test_auth.py -q` pasa.
- [x] 001.3 Crear pruebas ETL para CSV válido, XLSX, formato rechazado, usuario no autenticado, historial vacío y aislamiento por usuario. Verificar: `cd backend; pytest tests/test_etl.py -q` pasa.
- [x] 001.4 Crear pruebas de estadísticas, categorías, evolución temporal, predicción insuficiente, predicción válida y exportaciones. Verificar: `cd backend; pytest tests/test_analytics.py -q` pasa.
- [x] 001.5 Crear pruebas unitarias para features estacionales y agregación mensual. Verificar: `cd backend; pytest tests/test_ml.py -q` pasa.
- [x] 001.6 Confirmar baseline completo. Verificar: `cd backend; pytest --cov=app --cov-report=term-missing` termina con código 0: 26 passed, 67% coverage.

### Tarea 002 — Ocultar detalles internos en errores

Plan: `plans/002-errores-seguros.md` | Depende de: 001 | Esfuerzo: S

- [x] 002.1 Registrar la excepción completa de `clear_history` en logs del servidor. Verificar: el error queda en log sin exponerlo en la respuesta.
- [x] 002.2 Reemplazar `str(exc)` por mensaje genérico en la respuesta 500. Verificar: el test no encuentra SQL, credenciales, host ni stack trace en el body.
- [x] 002.3 Ocultar `str(exc)` en `/health/db` y conservar HTTP 503. Verificar: el test devuelve estado público genérico cuando DB no está disponible.
- [x] 002.4 Ejecutar regresiones de auth y ETL. Verificar: `cd backend; pytest tests/test_auth.py tests/test_etl.py -q` pasa: 14 passed.
- [x] 002.5 Ejecutar lint de los archivos modificados. Verificar: no hay errores nuevos; `B008` preexistente de FastAPI permanece pendiente de configuración Ruff.

### Tarea 003 — Hacer ETL robusto y transparente

Plan: `plans/003-etl-robusto.md` | Depende de: 001 | Esfuerzo: M

- [x] 003.1 Separar parsing de validación; detectar coma, punto y coma o tabulador; aceptar UTF-8 y fallback latino controlado. Verificar: fixtures con UTF-8, `;` y `cp1252` pasan.
- [x] 003.2 Validar columnas requeridas, monto finito y fecha válida antes de crear `Venta`. Verificar: fila inválida no se convierte en monto `0.0` ni fecha actual.
- [x] 003.3 Devolver total leído, insertado y rechazado, con errores acotados por fila. Verificar: respuesta contiene conteos correctos sin datos sensibles.
- [x] 003.4 Mantener parser `.sql` limitado a `INSERT ... VALUES`, sin ejecutar SQL, y documentar el límite. Verificar: parser permanece separado de la ejecución SQL.
- [x] 003.5 Hacer inserción transaccional para evitar registros parciales cuando falla la operación. Verificar: `commit` ejecuta rollback y devuelve error genérico si falla.
- [x] 003.6 Ejecutar pruebas ETL completas. Verificar: `cd backend; pytest tests/test_etl.py -q` pasa: 9 passed.

### Tarea 004 — Normalizar categorías con catálogo canónico

Plan: `plans/004-categorias-canonicas.md` | Depende de: 003 | Esfuerzo: S

- [x] 004.1 Crear una función única que normalice espacios, mayúsculas y acentos sin perder información. Verificar: entradas equivalentes devuelven el mismo valor canónico.
- [x] 004.2 Aplicar la normalización al cargar ventas y resolver parámetros de reportes. Verificar: `cuidado personal`, `CUIDADO PERSONAL` y `Cuidado Personal` usan el mismo filtro.
- [x] 004.3 Conservar categorías desconocidas sin convertirlas en `General`. Verificar: una categoría nueva no se pierde durante la carga.
- [x] 004.4 Devolver error solo cuando no existen registros para la categoría solicitada. Verificar: el filtro usa la categoría normalizada y conserva el código documentado para ausencia de registros.
- [x] 004.5 Probar mayúsculas, espacios, acentos y categorías desconocidas. Verificar: `cd backend; pytest tests/test_categories.py tests/test_etl.py tests/test_analytics.py -q` pasa: 21 passed.

### Tarea 005 — Extraer el procesamiento ML

Plan: `plans/005-extraer-ml.md` | Depende de: 001 | Esfuerzo: M

- [x] 005.1 Crear módulo tipado en `backend/app/ml_models/forecast.py` para features, agregación y predicción. Verificar: tests unitarios ejecutan sin `TestClient` ni PDF.
- [x] 005.2 Mover la lógica diaria y mensual desde `analytics_routes.py` a `ml_models/`. Verificar: las rutas llaman al módulo y no entrenan modelos duplicados.
- [x] 005.3 Tratar meses sin observaciones como ausentes, no como ingresos cero fabricados. Verificar: test con enero y marzo no crea febrero artificial.
- [x] 005.4 Mantener respuestas HTTP y archivos PDF compatibles. Verificar: `cd backend; pytest tests/test_ml.py tests/test_analytics.py -q` pasa.
- [x] 005.5 Confirmar lint del módulo nuevo. Verificar: `ruff check app/ml_models/forecast.py tests/test_ml.py` termina sin errores; tipos externos de pandas/sklearn quedan pendientes de stubs.

### Tarea 006 — Preparar schema para monto, cantidad y predicciones

Plan: `plans/006-schema-predicciones.md` | Depende de: 003 y 005 | Esfuerzo: M

- [x] 006.1 Actualizar modelos y crear migration para `ventas.cantidad`, `predicciones.monto_proyectado` y eliminación de `archivos`. Verificar: migration revisada manualmente.
- [x] 006.2 Aplicar migration en una base temporal. Verificar: `alembic upgrade head` termina sin error.
- [x] 006.3 Verificar reversión en la misma base temporal. Verificar: `alembic downgrade -1` termina sin error.
- [x] 006.4 Hacer que ETL lea `cantidad`, use `1` cuando la fuente antigua no la incluya y rechace cantidades negativas. Verificar: tests ETL pasan.
- [x] 006.5 Actualizar dataset sintético para generar columna `cantidad`. Verificar: CSV generado contiene `cantidad`.
- [x] 006.6 Persistir monto y cantidad proyectados en `predicciones`. Verificar: test consulta ambos valores.
- [x] 006.7 Confirmar ausencia de uso runtime de `Archivo`. Verificar: modelo, exportaciones y `alembic/env.py` ya no registran `Archivo`.

### Tarea 007 — Formalizar RLM para monto y cantidad

Plan: `plans/007-rlm-metricas.md` | Depende de: 005 y 006 | Esfuerzo: M

- [x] 007.1 Definir y documentar matriz de features con orden estable. Verificar: tests comprueban número y valores de predictores.
- [x] 007.2 Entrenar targets separados para monto y cantidad con los mismos predictores. Verificar: API devuelve campos separados para ambos valores.
- [x] 007.3 Agregar tendencia y dummies mensuales al modelo mensual. Verificar: test confirma features estacionales.
- [x] 007.4 Agregar tendencia y 7 dummies de día de semana al modelo diario. Verificar: test confirma los 7 días y predicción diaria válida.
- [x] 007.5 Calcular R², MAPE y RMSE con validación temporal. Verificar: métricas no usan observaciones futuras ni datos de validación durante entrenamiento.
- [x] 007.6 Calcular límites inferior y superior del intervalo de predicción. Verificar: límite inferior no supera al superior y ningún valor final es negativo.
- [x] 007.7 Persistir predicción, monto, cantidad, fecha y métrica asociada. Verificar: una petición crea el registro esperado en `predicciones`.
- [x] 007.8 Documentar features, métricas, datos mínimos y limitaciones de la RLM. Verificar: `docs/ml-models.md` refleja el comportamiento real.
- [ ] 007.9 Ejecutar suite ML y analytics. Verificar: `cd backend; pytest tests/test_ml.py tests/test_analytics.py -q` pasa.

### Tarea 008 — Agregar filtros de fecha a analytics

Plan: `plans/008-filtros-fecha.md` | Depende de: 001 | Esfuerzo: S

- [ ] 008.1 Crear helper para validar y aplicar `fecha_desde` y `fecha_hasta` junto con el filtro de usuario. Verificar: consulta filtra en PostgreSQL antes de agregar.
- [ ] 008.2 Aplicar el helper a `/analytics/stats`, `/analytics/stats/categories` y `/analytics/stats/temporal`. Verificar: cada endpoint devuelve solo registros del rango.
- [ ] 008.3 Validar rango invertido y conservar comportamiento sin fechas. Verificar: rango inválido devuelve HTTP 422; sin parámetros no cambia respuesta.
- [ ] 008.4 Crear tests para rango válido, un solo día, rango vacío y rango invertido. Verificar: `cd backend; pytest tests/test_analytics.py -q` pasa.
- [ ] 008.5 Documentar parámetros en OpenAPI. Verificar: `/docs` muestra nombres, formato y límites.

### Tarea 009 — Migrar JWT de `python-jose` a `PyJWT`

Plan: `plans/009-migrar-pyjwt.md` | Depende de: 001 y 002 | Esfuerzo: S-M

- [ ] 009.1 Revisar uso actual de `python-jose` en generación y validación de tokens. Verificar: búsqueda identifica `security.py` y `deps.py` como únicos puntos runtime.
- [ ] 009.2 Sustituir dependencia por `PyJWT` con soporte criptográfico compatible. Verificar: `pip check` no reporta dependencias rotas.
- [ ] 009.3 Adaptar creación, decodificación, expiración y manejo de errores JWT. Verificar: tokens válidos se aceptan y tokens inválidos o expirados se rechazan con HTTP 401.
- [ ] 009.4 Actualizar tests de login, `/users/me` y credenciales inválidas. Verificar: `cd backend; pytest tests/test_auth.py -q` pasa.
- [ ] 009.5 Confirmar que no queda importación runtime de `jose`. Verificar: búsqueda en `backend/app/` no encuentra `from jose` ni `import jose`.
- [ ] 009.6 Documentar migración y ejecutar suite completa. Verificar: `cd backend; pytest --cov=app --cov-report=term-missing` pasa.

## Verificación global

Desde la raíz, cuando el entorno esté preparado:

```bash
make lint
make typecheck
make test
```

En Windows sin GNU Make, ejecutar los comandos equivalentes desde `backend/`:

```powershell
ruff check app/
mypy app/
pytest --cov=app --cov-report=term-missing
```

Antes de ejecutar pruebas se requiere `backend/.env`, `DATABASE_URL` configurado y PostgreSQL accesible.

## Fase posterior: frontend

Después del plan 008, construir frontend con React, Tailwind CSS y Chart.js:

1. Autenticación y cliente HTTP con JWT.
2. Carga de CSV/XLSX.
3. Dashboard con evolución temporal y categorías.
4. Predicciones de monto y cantidad con intervalo de confianza.
5. Descarga de reportes.

## Hallazgos pospuestos

No forman parte de esta tanda: migración `python-jose` a `PyJWT` (plan 009), actualización adicional de dependencias, CI, CORS estricto, contrato uniforme de errores en `/predict` y anotaciones de fecha. Revisarlos después de completar 001-008.

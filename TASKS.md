# Tareas del Proyecto

Plan de trabajo backend para Predicta. Ejecutar en orden salvo tareas sin dependencia.

**Base del plan:** commit `adcb0a4`  
**Estado:** `TODO`, `EN PROGRESO`, `HECHO`, `BLOQUEADO`

## Orden de ejecución

| ID | Tarea | Plan | Prioridad | Esfuerzo | Depende de | Estado |
|---|---|---|---|---|---|---|
| 001 | Crear baseline real de pruebas | `plans/001-baseline-pruebas.md` | P1 | S-M | — | HECHO |
| 002 | Ocultar detalles internos en errores | `plans/002-errores-seguros.md` | P2 | S | 001 | HECHO |
| 003 | Hacer ETL robusto | `plans/003-etl-robusto.md` | P1 | M | 001 | TODO |
| 004 | Normalizar categorías | `plans/004-categorias-canonicas.md` | P2 | S | 003 | TODO |
| 005 | Extraer lógica ML | `plans/005-extraer-ml.md` | P2 | M | 001 | TODO |
| 006 | Actualizar schema para monto y cantidad | `plans/006-schema-predicciones.md` | P1 | M | 003, 005 | TODO |
| 007 | Formalizar RLM y métricas | `plans/007-rlm-metricas.md` | P1 | M | 005, 006 | TODO |
| 008 | Agregar filtros de fecha | `plans/008-filtros-fecha.md` | P2 | S | 001 | TODO |

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

- [ ] 003.1 Separar parsing de validación; detectar coma, punto y coma o tabulador; aceptar UTF-8 y fallback latino controlado. Verificar: fixtures con UTF-8 y `;` generan las mismas columnas.
- [ ] 003.2 Validar columnas requeridas, monto finito y fecha válida antes de crear `Venta`. Verificar: fila inválida no se convierte en monto `0.0` ni fecha actual.
- [ ] 003.3 Devolver total leído, insertado y rechazado, con errores acotados por fila. Verificar: respuesta contiene conteos correctos sin datos sensibles.
- [ ] 003.4 Mantener parser `.sql` limitado a `INSERT ... VALUES`, sin ejecutar SQL, y documentar el límite. Verificar: fixture SQL simple pasa y no se llama `execute` con contenido subido.
- [ ] 003.5 Hacer inserción transaccional para evitar registros parciales cuando falla la operación. Verificar: error de DB deja cero inserciones parciales.
- [ ] 003.6 Ejecutar pruebas ETL completas. Verificar: `cd backend; pytest tests/test_etl.py -q` pasa.

### Tarea 004 — Normalizar categorías con catálogo canónico

Plan: `plans/004-categorias-canonicas.md` | Depende de: 003 | Esfuerzo: S

- [ ] 004.1 Crear una función única que normalice espacios, mayúsculas y acentos sin perder información. Verificar: entradas equivalentes devuelven el mismo valor canónico.
- [ ] 004.2 Aplicar la normalización al cargar ventas y resolver parámetros de reportes. Verificar: `cuidado personal`, `CUIDADO PERSONAL` y `Cuidado Personal` usan el mismo filtro.
- [ ] 004.3 Conservar categorías desconocidas sin convertirlas en `General`. Verificar: una categoría nueva no se pierde durante la carga.
- [ ] 004.4 Devolver error solo cuando no existen registros para la categoría solicitada. Verificar: reporte de categoría existente funciona y categoría sin registros devuelve el código documentado.
- [ ] 004.5 Probar mayúsculas, espacios, acentos y categorías desconocidas. Verificar: `cd backend; pytest tests/test_etl.py tests/test_analytics.py -q` pasa.

### Tarea 005 — Extraer el procesamiento ML

Plan: `plans/005-extraer-ml.md` | Depende de: 001 | Esfuerzo: M

- [ ] 005.1 Crear módulo o clase tipada en `backend/app/ml_models/forecast.py` para features, agregación y predicción. Verificar: tests unitarios ejecutan sin `TestClient` ni PDF.
- [ ] 005.2 Mover la lógica diaria y mensual desde `analytics_routes.py` a `ml_models/`. Verificar: las rutas llaman al módulo y no entrenan modelos duplicados.
- [ ] 005.3 Tratar meses sin observaciones como ausentes, no como ingresos cero fabricados. Verificar: fixture con meses separados no crea ceros intermedios de entrenamiento.
- [ ] 005.4 Mantener respuestas HTTP y archivos PDF compatibles. Verificar: `cd backend; pytest tests/test_ml.py tests/test_analytics.py -q` pasa.
- [ ] 005.5 Confirmar lint y tipos del módulo nuevo. Verificar: `cd backend; ruff check app/; mypy app/` termina sin errores.

### Tarea 006 — Preparar schema para monto, cantidad y predicciones

Plan: `plans/006-schema-predicciones.md` | Depende de: 003 y 005 | Esfuerzo: M

- [ ] 006.1 Actualizar modelos y generar migration para `ventas.cantidad`, `predicciones.monto_proyectado` y eliminación de `archivos`. Verificar: revisar manualmente la migration antes de aplicarla.
- [ ] 006.2 Aplicar migration en una base de prueba. Verificar: desde `backend`, `alembic upgrade head` termina sin error.
- [ ] 006.3 Hacer que ETL lea `cantidad`, use `1` cuando la fuente antigua no la incluya y rechace cantidades negativas. Verificar: CSV antiguo y CSV con cantidad crean ventas correctas.
- [ ] 006.4 Actualizar dataset sintético para generar columna `cantidad`. Verificar: desde `backend`, `python scripts/generate_dataset.py` crea CSV con la columna.
- [ ] 006.5 Persistir monto y cantidad proyectados sin duplicar filas en una misma operación. Verificar: test consulta `predicciones` y encuentra ambos valores.
- [ ] 006.6 Verificar reversión en una base descartable. Verificar: desde `backend`, `alembic downgrade -1` termina sin error.
- [ ] 006.7 Confirmar ausencia de uso runtime de `Archivo`. Verificar: búsqueda en `backend/app/` no encuentra escrituras de metadata de archivos.

### Tarea 007 — Formalizar RLM para monto y cantidad

Plan: `plans/007-rlm-metricas.md` | Depende de: 005 y 006 | Esfuerzo: M

- [ ] 007.1 Definir y documentar matriz de features con orden estable. Verificar: tests comprueban número y valores de predictores.
- [ ] 007.2 Entrenar targets separados para monto y cantidad con los mismos predictores. Verificar: API devuelve campos separados para ambos valores.
- [ ] 007.3 Agregar tendencia y dummies mensuales al modelo mensual. Verificar: test confirma features estacionales.
- [ ] 007.4 Agregar tendencia y 7 dummies de día de semana al modelo diario. Verificar: test confirma los 7 días y predicción diaria válida.
- [ ] 007.5 Calcular R², MAPE y RMSE con validación temporal. Verificar: métricas no usan observaciones futuras ni datos de validación durante entrenamiento.
- [ ] 007.6 Calcular límites inferior y superior del intervalo de predicción. Verificar: límite inferior no supera al superior y ningún valor final es negativo.
- [ ] 007.7 Persistir predicción, monto, cantidad, fecha y métrica asociada. Verificar: una petición crea el registro esperado en `predicciones`.
- [ ] 007.8 Documentar features, métricas, datos mínimos y limitaciones de la RLM. Verificar: `docs/ml-models.md` refleja el comportamiento real.
- [ ] 007.9 Ejecutar suite ML y analytics. Verificar: `cd backend; pytest tests/test_ml.py tests/test_analytics.py -q` pasa.

### Tarea 008 — Agregar filtros de fecha a analytics

Plan: `plans/008-filtros-fecha.md` | Depende de: 001 | Esfuerzo: S

- [ ] 008.1 Crear helper para validar y aplicar `fecha_desde` y `fecha_hasta` junto con el filtro de usuario. Verificar: consulta filtra en PostgreSQL antes de agregar.
- [ ] 008.2 Aplicar el helper a `/analytics/stats`, `/analytics/stats/categories` y `/analytics/stats/temporal`. Verificar: cada endpoint devuelve solo registros del rango.
- [ ] 008.3 Validar rango invertido y conservar comportamiento sin fechas. Verificar: rango inválido devuelve HTTP 422; sin parámetros no cambia respuesta.
- [ ] 008.4 Crear tests para rango válido, un solo día, rango vacío y rango invertido. Verificar: `cd backend; pytest tests/test_analytics.py -q` pasa.
- [ ] 008.5 Documentar parámetros en OpenAPI y `docs/api.md`. Verificar: `/docs` muestra nombres, formato y límites.

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

No forman parte de esta tanda: actualización de dependencias, CI, CORS estricto, contrato uniforme de errores en `/predict` y anotaciones de fecha. Revisarlos después de completar 001-008.

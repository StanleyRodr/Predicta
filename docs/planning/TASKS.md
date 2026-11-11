# Tareas del Proyecto

Plan de trabajo backend para Predicta. Ejecutar en orden salvo tareas sin dependencia.

**Base del plan:** commit `adcb0a4`  
**Estado:** `TODO`, `EN PROGRESO`, `HECHO`, `BLOQUEADO`

## Orden de ejecución

| ID | Tarea | Plan | Prioridad | Esfuerzo | Depende de | Estado |
|---|---|---|---|---|---|---|
| 001 | Crear baseline real de pruebas | `docs/planning/plans/001-baseline-pruebas.md` | P1 | S-M | — | HECHO |
| 002 | Ocultar detalles internos en errores | `docs/planning/plans/002-errores-seguros.md` | P2 | S | 001 | HECHO |
| 003 | Hacer ETL robusto | `docs/planning/plans/003-etl-robusto.md` | P1 | M | 001 | HECHO |
| 004 | Normalizar categorías | `docs/planning/plans/004-categorias-canonicas.md` | P2 | S | 003 | HECHO |
| 005 | Extraer lógica ML | `docs/planning/plans/005-extraer-ml.md` | P2 | M | 001 | HECHO |
| 006 | Actualizar schema para monto y cantidad | `docs/planning/plans/006-schema-predicciones.md` | P1 | M | 003, 005 | HECHO |
| 007 | Formalizar RLM y métricas | `docs/planning/plans/007-rlm-metricas.md` | P1 | M | 005, 006 | HECHO |
| 008 | Agregar filtros de fecha | `docs/planning/plans/008-filtros-fecha.md` | P2 | S | 001 | HECHO |
| 009 | Migrar JWT de `python-jose` a `PyJWT` | `docs/planning/plans/009-migrar-pyjwt.md` | P2 | S-M | 001, 002 | HECHO |
| 010 | Crear fundacion frontend | `docs/planning/plans/010-frontend-fundacion.md` | P1 | M | 001-009 | HECHO |
| 011 | Implementar auth y layout frontend | `docs/planning/plans/011-frontend-auth-layout.md` | P1 | M | 010 | HECHO |
| 012 | Implementar carga ETL e historial | `docs/planning/plans/012-frontend-carga-historial.md` | P1 | M | 011 | HECHO |
| 013 | Implementar dashboard y analytics | `docs/planning/plans/013-frontend-dashboard.md` | P1 | M | 011, 012 | HECHO |
| 014 | Implementar predicciones y reportes | `docs/planning/plans/014-frontend-predicciones-reportes.md` | P1 | M | 013 | HECHO |
| 015 | CI y calidad automática | `docs/planning/plans/015-ci-calidad.md` | P1 | M | — | HECHO |
| 016 | Alinear modelos y migraciones | `docs/planning/plans/016-alinear-migraciones.md` | P1 | M | 015 | HECHO |
| 017 | Endurecer la ETL | `docs/planning/plans/017-etl-endurecida.md` | P1 | L | 016 | HECHO |
| 018 | Convención numérica 0,000.00 | `docs/planning/plans/018-convencion-numerica.md` | P1 | S-M | — | HECHO |
| 019 | Sesión, errores y descargas en frontend | `docs/planning/plans/019-frontend-sesion-descargas.md` | P1 | M | — | HECHO |
| 020 | Reportes seguros y capa de servicios | `docs/planning/plans/020-reportes-servicios.md` | P1 | L | 017, 018 | HECHO |
| 021 | Corregir modelo y proyectar 12 meses | `docs/planning/plans/021-modelo-horizonte.md` | P1 | L | 020 | HECHO |
| 022 | Evaluación y modelos de referencia | `docs/planning/plans/022-evaluacion-baselines.md` | P1 | L | 021 | HECHO |
| 023 | Contrato de predicción y esquemas | `docs/planning/plans/023-contrato-prediccion.md` | P1 | L | 016, 022 | HECHO |
| 024 | Series de analítica por dimensión | `docs/planning/plans/024-analitica-dimensiones.md` | P1 | M | 020 | HECHO |
| 025 | Dashboard general, categoría y mes | `docs/planning/plans/025-dashboard-explorador.md` | P1 | L | 018, 019, 024 | HECHO |
| 026 | Proyecciones en gráficos | `docs/planning/plans/026-proyecciones-graficas.md` | P1 | L | 018, 019, 023 | HECHO |
| 027 | Métricas comprensibles | `docs/planning/plans/027-metricas-comprensibles.md` | P1 | S-M | 026 | HECHO |
| 028 | Accesibilidad | `docs/planning/plans/028-accesibilidad.md` | P2 | M | 025, 026 | HECHO |
| 029 | Configuración y autenticación | `docs/planning/plans/029-configuracion-auth.md` | P2 | M | 015 | HECHO |
| 030 | Cerrar huecos de pruebas | `docs/planning/plans/030-cobertura-tests.md` | P2 | M | 017, 023, 024 | HECHO |
| 031 | Limpieza y documentación | `docs/planning/plans/031-limpieza-documentacion.md` | P3 | S-M | 015-030 | HECHO |
| 032 | Explicaciones claras en predicciones | `docs/planning/plans/032-explicaciones-predicciones.md` | P1 | M | 027, 028 | HECHO |
| 033 | Panel del "i" sin barras de desplazamiento | `docs/planning/plans/033-panel-info-flotante.md` | P2 | S | 032 | HECHO |
| 034 | Métrica MAE | `docs/planning/plans/034-metrica-mae.md` | P1 | S-M | 022, 032 | HECHO |
| 034b | Predicción e historial por producto | `docs/planning/plans/034b-prediccion-producto.md` | P1 | M | 033 | HECHO |
| 035 | Mapeo de columnas en la carga de ventas | `docs/planning/plans/035-mapeo-columnas.md` | P1 | M | 034b | HECHO |
| 036 | Pruebas con datasets reales de e-commerce | `docs/planning/plans/036-datasets-reales.md` | P1 | M | 035 | HECHO |
| 038 | Carga de varios archivos a la vez | `docs/planning/plans/038-carga-varios-archivos.md` | P1 | M | 035 | HECHO |
| 039 | Auditoría de seguridad | `docs/planning/plans/039-auditoria-seguridad.md` | P1 | M | — | HECHO |
| 040 | Validación de campos y exportación segura | `docs/planning/plans/040-validacion-campos.md` | P1 | M | 039 | TODO |
| 041 | Rate limit, proxy, cabeceras y configuración de producción | `docs/planning/plans/041-endurecer-api.md` | P1 | M | 039 | TODO |
| 042 | Verificación de correo | `docs/planning/plans/042-verificacion-correo.md` | P1 | L | 040, 041 | TODO |
| 043 | Contraseñas, bloqueo y revocación de sesiones | `docs/planning/plans/043-contrasenas-bloqueo.md` | P1 | L | 042 | TODO |
| 044 | Escáneres de seguridad en CI | `docs/planning/plans/044-escaneres-ci.md` | P1 | S | 039 | TODO |
| 045 | CSP y despliegue en Vercel, Railway y Neon | `docs/planning/plans/045-guia-despliegue.md` | P1 | M | 041, 042, 043 | TODO |

## Reglas de ejecución

- Leer el plan completo antes de modificar código.
- Ejecutar cada verificación indicada antes de avanzar.
- Si aparece una condición STOP, detenerse y reportar; no improvisar.
- Actualizar estado de tarea en esta tabla al iniciar, terminar o bloquearse.
- No modificar `README.md` raíz como parte de estas tareas. Única excepción autorizada: tarea 031.
- No crear un índice dentro de `docs/planning/plans/`; esa función pertenece a este archivo.

## Subtareas detalladas

### Tarea 001 — Crear baseline real de pruebas

Plan: `docs/planning/plans/001-baseline-pruebas.md` | Depende de: ninguna | Esfuerzo: S-M

- [x] 001.1 Configurar entorno de pruebas aislado en SQLite, con `DATABASE_URL` y `SECRET_KEY` definidos antes de importar la app. Verificar: `cd backend; pytest --collect-only` recolecta 26 tests sin error.
- [x] 001.2 Crear pruebas de registro, duplicados, contraseña débil, login, `/users/me` y actualización de perfil. Verificar: `cd backend; pytest tests/test_auth.py -q` pasa.
- [x] 001.3 Crear pruebas ETL para CSV válido, XLSX, formato rechazado, usuario no autenticado, historial vacío y aislamiento por usuario. Verificar: `cd backend; pytest tests/test_etl.py -q` pasa.
- [x] 001.4 Crear pruebas de estadísticas, categorías, evolución temporal, predicción insuficiente, predicción válida y exportaciones. Verificar: `cd backend; pytest tests/test_analytics.py -q` pasa.
- [x] 001.5 Crear pruebas unitarias para features estacionales y agregación mensual. Verificar: `cd backend; pytest tests/test_ml.py -q` pasa.
- [x] 001.6 Confirmar baseline completo. Verificar: `cd backend; pytest --cov=app --cov-report=term-missing` termina con código 0: 26 passed, 67% coverage.

### Tarea 002 — Ocultar detalles internos en errores

Plan: `docs/planning/plans/002-errores-seguros.md` | Depende de: 001 | Esfuerzo: S

- [x] 002.1 Registrar la excepción completa de `clear_history` en logs del servidor. Verificar: el error queda en log sin exponerlo en la respuesta.
- [x] 002.2 Reemplazar `str(exc)` por mensaje genérico en la respuesta 500. Verificar: el test no encuentra SQL, credenciales, host ni stack trace en el body.
- [x] 002.3 Ocultar `str(exc)` en `/health/db` y conservar HTTP 503. Verificar: el test devuelve estado público genérico cuando DB no está disponible.
- [x] 002.4 Ejecutar regresiones de auth y ETL. Verificar: `cd backend; pytest tests/test_auth.py tests/test_etl.py -q` pasa: 14 passed.
- [x] 002.5 Ejecutar lint de los archivos modificados. Verificar: no hay errores nuevos; `B008` preexistente de FastAPI permanece pendiente de configuración Ruff.

### Tarea 003 — Hacer ETL robusto y transparente

Plan: `docs/planning/plans/003-etl-robusto.md` | Depende de: 001 | Esfuerzo: M

- [x] 003.1 Separar parsing de validación; detectar coma, punto y coma o tabulador; aceptar UTF-8 y fallback latino controlado. Verificar: fixtures con UTF-8, `;` y `cp1252` pasan.
- [x] 003.2 Validar columnas requeridas, monto finito y fecha válida antes de crear `Venta`. Verificar: fila inválida no se convierte en monto `0.0` ni fecha actual.
- [x] 003.3 Devolver total leído, insertado y rechazado, con errores acotados por fila. Verificar: respuesta contiene conteos correctos sin datos sensibles.
- [x] 003.4 Mantener parser `.sql` limitado a `INSERT ... VALUES`, sin ejecutar SQL, y documentar el límite. Verificar: parser permanece separado de la ejecución SQL.
- [x] 003.5 Hacer inserción transaccional para evitar registros parciales cuando falla la operación. Verificar: `commit` ejecuta rollback y devuelve error genérico si falla.
- [x] 003.6 Ejecutar pruebas ETL completas. Verificar: `cd backend; pytest tests/test_etl.py -q` pasa: 9 passed.

### Tarea 004 — Normalizar categorías con catálogo canónico

Plan: `docs/planning/plans/004-categorias-canonicas.md` | Depende de: 003 | Esfuerzo: S

- [x] 004.1 Crear una función única que normalice espacios, mayúsculas y acentos sin perder información. Verificar: entradas equivalentes devuelven el mismo valor canónico.
- [x] 004.2 Aplicar la normalización al cargar ventas y resolver parámetros de reportes. Verificar: `cuidado personal`, `CUIDADO PERSONAL` y `Cuidado Personal` usan el mismo filtro.
- [x] 004.3 Conservar categorías desconocidas sin convertirlas en `General`. Verificar: una categoría nueva no se pierde durante la carga.
- [x] 004.4 Devolver error solo cuando no existen registros para la categoría solicitada. Verificar: el filtro usa la categoría normalizada y conserva el código documentado para ausencia de registros.
- [x] 004.5 Probar mayúsculas, espacios, acentos y categorías desconocidas. Verificar: `cd backend; pytest tests/test_categories.py tests/test_etl.py tests/test_analytics.py -q` pasa: 21 passed.

### Tarea 005 — Extraer el procesamiento ML

Plan: `docs/planning/plans/005-extraer-ml.md` | Depende de: 001 | Esfuerzo: M

- [x] 005.1 Crear módulo tipado en `backend/app/ml_models/forecast.py` para features, agregación y predicción. Verificar: tests unitarios ejecutan sin `TestClient` ni PDF.
- [x] 005.2 Mover la lógica diaria y mensual desde `analytics_routes.py` a `ml_models/`. Verificar: las rutas llaman al módulo y no entrenan modelos duplicados.
- [x] 005.3 Tratar meses sin observaciones como ausentes, no como ingresos cero fabricados. Verificar: test con enero y marzo no crea febrero artificial.
- [x] 005.4 Mantener respuestas HTTP y archivos PDF compatibles. Verificar: `cd backend; pytest tests/test_ml.py tests/test_analytics.py -q` pasa.
- [x] 005.5 Confirmar lint del módulo nuevo. Verificar: `ruff check app/ml_models/forecast.py tests/test_ml.py` termina sin errores; tipos externos de pandas/sklearn quedan pendientes de stubs.

### Tarea 006 — Preparar schema para monto, cantidad y predicciones

Plan: `docs/planning/plans/006-schema-predicciones.md` | Depende de: 003 y 005 | Esfuerzo: M

- [x] 006.1 Actualizar modelos y crear migration para `ventas.cantidad`, `predicciones.monto_proyectado` y eliminación de `archivos`. Verificar: migration revisada manualmente.
- [x] 006.2 Aplicar migration en una base temporal. Verificar: `alembic upgrade head` termina sin error.
- [x] 006.3 Verificar reversión en la misma base temporal. Verificar: `alembic downgrade -1` termina sin error.
- [x] 006.4 Hacer que ETL lea `cantidad`, use `1` cuando la fuente antigua no la incluya y rechace cantidades negativas. Verificar: tests ETL pasan.
- [x] 006.5 Actualizar dataset sintético para generar columna `cantidad`. Verificar: CSV generado contiene `cantidad`.
- [x] 006.6 Persistir monto y cantidad proyectados en `predicciones`. Verificar: test consulta ambos valores.
- [x] 006.7 Confirmar ausencia de uso runtime de `Archivo`. Verificar: modelo, exportaciones y `alembic/env.py` ya no registran `Archivo`.

### Tarea 007 — Formalizar RLM para monto y cantidad

Plan: `docs/planning/plans/007-rlm-metricas.md` | Depende de: 005 y 006 | Esfuerzo: M

- [x] 007.1 Definir y documentar matriz de features con orden estable. Verificar: tests comprueban número y valores de predictores.
- [x] 007.2 Entrenar targets separados para monto y cantidad con los mismos predictores. Verificar: API devuelve campos separados para ambos valores.
- [x] 007.3 Agregar tendencia y dummies mensuales al modelo mensual. Verificar: test confirma features estacionales.
- [x] 007.4 Agregar tendencia y 7 dummies de día de semana al modelo diario. Verificar: test confirma los 7 días y predicción diaria válida.
- [x] 007.5 Calcular R², MAPE y RMSE con validación temporal. Verificar: métricas no usan observaciones futuras ni datos de validación durante entrenamiento.
- [x] 007.6 Calcular límites inferior y superior del intervalo de predicción. Verificar: límite inferior no supera al superior y ningún valor final es negativo.
- [x] 007.7 Persistir predicción, monto, cantidad, fecha y métrica asociada. Verificar: una petición crea el registro esperado en `predicciones`.
- [x] 007.8 Documentar features, métricas, datos mínimos y limitaciones de la RLM. Verificar: `docs/ml-models.md` refleja el comportamiento real.
- [x] 007.9 Ejecutar suite ML y analytics. Verificar: `cd backend; pytest tests/test_ml.py tests/test_analytics.py -q` pasa: 20 passed.

### Tarea 008 — Agregar filtros de fecha a analytics

Plan: `docs/planning/plans/008-filtros-fecha.md` | Depende de: 001 | Esfuerzo: S

- [x] 008.1 Crear helper para validar y aplicar `fecha_desde` y `fecha_hasta` junto con el filtro de usuario. Verificar: consulta filtra en PostgreSQL antes de agregar.
- [x] 008.2 Aplicar el helper a `/analytics/stats`, `/analytics/stats/categories` y `/analytics/stats/temporal`. Verificar: cada endpoint devuelve solo registros del rango.
- [x] 008.3 Validar rango invertido y conservar comportamiento sin fechas. Verificar: rango inválido devuelve HTTP 422; sin parámetros no cambia respuesta.
- [x] 008.4 Crear tests para rango válido, un solo día, rango vacío y rango invertido. Verificar: `cd backend; pytest tests/test_analytics.py -q` pasa.
- [x] 008.5 Documentar parámetros en OpenAPI. Verificar: `/docs` muestra nombres, formato y límites.

### Tarea 009 — Migrar JWT de `python-jose` a `PyJWT`

Plan: `docs/planning/plans/009-migrar-pyjwt.md` | Depende de: 001 y 002 | Esfuerzo: S-M

- [x] 009.1 Revisar uso actual de `python-jose` en generación y validación de tokens. Verificar: búsqueda identifica `security.py` y `deps.py` como únicos puntos runtime.
- [x] 009.2 Sustituir dependencia por `PyJWT` con soporte criptográfico compatible. Verificar: `pip check` no reporta dependencias rotas.
- [x] 009.3 Adaptar creación, decodificación, expiración y manejo de errores JWT. Verificar: tokens válidos se aceptan y tokens inválidos o expirados se rechazan con HTTP 401.
- [x] 009.4 Actualizar tests de login, `/users/me` y credenciales inválidas. Verificar: `cd backend; pytest tests/test_auth.py -q` pasa.
- [x] 009.5 Confirmar que no queda importación runtime de `jose`. Verificar: búsqueda en `backend/app/` no encuentra `from jose` ni `import jose`.
- [x] 009.6 Documentar migración y ejecutar suite completa. Verificar: `cd backend; pytest --cov=app --cov-report=term-missing` pasa.

### Tarea 010 — Crear fundacion frontend

Plan: `docs/planning/plans/010-frontend-fundacion.md` | Depende de: backend 001-009 | Esfuerzo: M

- [x] 010.1 Crear React 19 + TypeScript + Vite y scripts npm. Verificar: `npm install` y `npm run build` pasan desde `frontend/`.
- [x] 010.2 Configurar Tailwind CSS v4 con tokens oscuros y componentes base manuales. Verificar: smoke test confirma estilos y foco visible.
- [x] 010.3 Configurar Axios, TanStack Query, React Router y Zustand. Verificar: `npx tsc --noEmit` pasa.
- [x] 010.4 Configurar Vitest + React Testing Library. Verificar: `npm test -- --run` pasa.

### Tarea 011 — Implementar auth y layout frontend

Plan: `docs/planning/plans/011-frontend-auth-layout.md` | Depende de: 010 | Esfuerzo: M

- [x] 011.1 Implementar registro y login con Zod y React Hook Form. Verificar: tests cubren exito y errores 400/401/422.
- [x] 011.2 Implementar store JWT en localStorage e interceptor Axios 401. Verificar: tests confirman Bearer, logout y redireccion sin loop.
- [x] 011.3 Implementar perfil y `ProtectedRoute`. Verificar: anonimo va a `/login`; autenticado accede al shell.
- [x] 011.4 Implementar layout responsive y navegacion en español. Verificar: RTL confirma rutas privadas y mobile basico.

### Tarea 012 — Implementar carga ETL e historial

Plan: `docs/planning/plans/012-frontend-carga-historial.md` | Depende de: 011 | Esfuerzo: M

- [x] 012.1 Implementar dropzone para CSV/XLSX/SQL con limite 25 MB. Verificar: tests rechazan archivo vacio, extension invalida y archivo grande.
- [x] 012.2 Mostrar resumen de carga y errores acotados por fila. Verificar: conteos y errores backend aparecen sin datos inventados.
- [x] 012.3 Implementar historial paginado. Verificar: `skip`/`limit` cambian pagina y estado vacio funciona.
- [x] 012.4 Implementar purga con confirmacion. Verificar: cancelar no llama API; confirmar invalida cache.

### Tarea 013 — Implementar dashboard y analytics

Plan: `docs/planning/plans/013-frontend-dashboard.md` | Depende de: 011 y 012 | Esfuerzo: M

- [x] 013.1 Implementar filtros inclusivos `fecha_desde`/`fecha_hasta`. Verificar: sin rango, un dia, rango vacio e invertido.
- [x] 013.2 Mostrar KPIs globales. Verificar: loading, cero, datos y error tienen tests.
- [x] 013.3 Crear grafico Chart.js de categorias. Verificar: labels y dataset coinciden con API.
- [x] 013.4 Crear grafico Chart.js temporal. Verificar: fechas, datos vacios y accesibilidad funcionan.
- [x] 013.5 Integrar dashboard responsive y cache por rango. Verificar: tres endpoints reciben mismos limites.

### Tarea 014 — Implementar predicciones y reportes

Plan: `docs/planning/plans/014-frontend-predicciones-reportes.md` | Depende de: 013 | Esfuerzo: M

- [x] 014.1 Mostrar monto, cantidad, fecha e intervalos separados. Verificar: valores normales, cero, null y error.
- [x] 014.2 Mostrar R², MAPE y RMSE sin convertir null en cero. Verificar: test cubre dataset insuficiente.
- [x] 014.3 Evitar prediccion automatica y refetch al enfocar ventana. Verificar: request ocurre solo tras click.
- [x] 014.4 Implementar descargas Excel/PDF/anual/mensual/categoria como blob. Verificar: nombre, extension y object URL funcionan.
- [x] 014.5 Integrar paginas protegidas de predicciones y reportes. Verificar: build y suite frontend pasan.

## Fase 2: feedback 01 y pedidos del usuario

**Base:** commit `16cb972`. **Origen:** `docs/feedback/feedback-01.md` (F-01 a F-34, todos autorizados el 2026-11-05) y cinco pedidos del usuario.

| Pedido | Tareas |
|---|---|
| 1. Números con formato `0,000.00` | 017, 018 |
| 2. Gráficos general, por categoría y por mes | 024, 025 |
| 3. Proyecciones graficadas por general, categoría y mes | 021, 023, 026 |
| 4. Gráfica inicial legible por año | 024, 025 |
| 5. Métricas comprensibles para usuarios comunes | 027 |

**Decisiones tomadas:**

- Moneda: `$` sin código de país, con 2 decimales.
- Coma en cargas: seguida de 3 dígitos es miles; seguida de 1 o 2 dígitos es decimal.
- Por mes: totales mensuales, con detalle diario al elegir un mes.
- Proyección: hasta 12 meses, general o por categoría. "Por mes" es una selección dentro de la curva.
- Modelo escalonado: con menos de 6 meses no hay proyección mensual; de 6 a 23, solo tendencia; con 24 o más, tendencia y estacionalidad.
- Horizonte: la mitad de los meses observados, con máximo de 12.
- Meses 7 a 12: se muestran marcados como extrapolación sin validar.
- Gráfica inicial: años superpuestos, con selector para aislar un año.
- Medida: selector Monto / Cantidad en dashboard y proyecciones, con Monto por defecto.
- PDF: fuera de las vistas nuevas; solo cambian el formato numérico y el top 20 de ventas.
- Excel: guarda `#,##0.00`; se acepta que se muestre según la configuración regional del equipo.
- `MAX_ROWS`: 200,000 filas por archivo.
- `Prediccion`: consultar no escribe; se guarda solo a pedido y el historial es consultable.
- F-03: no se aceptan montos negativos ni en cero.
- F-13: un archivo idéntico se rechaza con HTTP 409.
- F-27: se agrega `statsmodels`.

**Orden de ejecución acordado:** 015, 018, 019, 016, 017, 020, 024, 025, 021, 022, 023, 026, 027, 028, 029, 030, 031.

### Tarea 015 — CI y calidad automática

Plan: `docs/planning/plans/015-ci-calidad.md` | Depende de: ninguna | Esfuerzo: M

- [x] 015.1 Configurar ruff y mypy en `backend/pyproject.toml`. Verificar: `ruff check app/` y `mypy app/` sin errores nuevos.
- [x] 015.2 Configurar ESLint y el script `lint`. Verificar: `npm run lint` termina con código 0.
- [x] 015.3 Crear `.pre-commit-config.yaml`. Verificar: `pre-commit run --all-files` termina con código 0.
- [x] 015.4 Crear workflow con jobs de backend y frontend. Verificar: ambos pasan en una rama de prueba.

### Tarea 016 — Alinear modelos y migraciones

Plan: `docs/planning/plans/016-alinear-migraciones.md` | Depende de: 015 | Esfuerzo: M

- [x] 016.1 Registrar las diferencias con `alembic check`. Verificar: coinciden con F-06 o se documenta lo adicional.
- [x] 016.2 Corregir tipos `Mapped[date]` e índices redundantes. Verificar: `mypy app/` y `pytest` pasan.
- [x] 016.3 Crear la migración `0003`. Verificar: `upgrade`, `check` y `downgrade -1` pasan en PostgreSQL.
- [x] 016.4 Activar `alembic check` en CI. Verificar: el job pasa.

### Tarea 017 — Endurecer la ETL

Plan: `docs/planning/plans/017-etl-endurecida.md` | Depende de: 016 | Esfuerzo: L

- [x] 017.1 Mover la carga al threadpool. Verificar: `/health` responde durante una carga.
- [x] 017.2 Limitar bytes, filas y tamaño descomprimido de XLSX. Verificar: tests de 413 y carga de las 28,667 filas de prueba.
- [x] 017.3 Aplicar la regla de coma por dígitos. Verificar: test parametrizado con la tabla del plan.
- [x] 017.4 Validar rangos por fila. Verificar: una fila inválida no impide cargar el resto.
- [x] 017.5 Usar mensajes controlados y numeración correcta. Verificar: ningún texto de excepción llega a la respuesta.
- [x] 017.6 Reescribir el parser SQL. Verificar: respeta comillas y rechaza filas sin fecha.
- [x] 017.7 Rechazar duplicados por SHA-256 y usuario. Verificar: 409 en el segundo intento y carga posible tras purgar.

### Tarea 018 — Convención numérica 0,000.00

Plan: `docs/planning/plans/018-convencion-numerica.md` | Depende de: ninguna | Esfuerzo: S-M

- [x] 018.1 Centralizar formatos en `formatters.ts`. Verificar: `1234.5` se muestra como `$1,234.50`.
- [x] 018.2 Reemplazar formatos directos en componentes. Verificar: `toLocaleString` y `toFixed` solo aparecen en `formatters.ts`.
- [x] 018.3 Aplicar formatos a ejes y tooltips. Verificar: tests de callbacks.
- [x] 018.4 Aplicar la convención a PDF y Excel. Verificar: tests de `format_money` y `number_format`.

### Tarea 019 — Sesión, errores y descargas en frontend

Plan: `docs/planning/plans/019-frontend-sesion-descargas.md` | Depende de: ninguna | Esfuerzo: M

- [x] 019.1 Vaciar la caché al cerrar sesión y ante 401. Verificar: test RTL entre usuarios A y B.
- [x] 019.2 Incluir `userId` en todas las claves privadas. Verificar: búsqueda de `queryKey`.
- [x] 019.3 Leer errores desde Blob. Verificar: se muestra el mensaje del backend.
- [x] 019.4 Corregir revocación de URL y timeouts. Verificar: tests de ambos.
- [x] 019.5 Invalidar consultas tras carga o purga. Verificar: test de invalidación.

### Tarea 020 — Reportes seguros y capa de servicios

Plan: `docs/planning/plans/020-reportes-servicios.md` | Depende de: 017, 018 | Esfuerzo: L

- [x] 020.1 Agregar tests de caracterización. Verificar: pasan sobre el código actual.
- [x] 020.2 Eliminar `plt.` y temporales. Verificar: búsquedas vacías y dos reportes concurrentes sin error.
- [x] 020.3 Extraer `report_service`, `analytics_service` y `etl_service`. Verificar: los tests pasan sin cambios.
- [x] 020.4 Agregar en SQL y acotar el PDF a resúmenes y top 20. Verificar: valores iguales y páginas acotadas.
- [x] 020.5 Mostrar el año real en el reporte mensual. Verificar: test de etiquetas.

### Tarea 021 — Corregir modelo y proyectar 12 meses

Plan: `docs/planning/plans/021-modelo-horizonte.md` | Depende de: 020 | Esfuerzo: L

- [x] 021.1 Corregir tendencia y dummies. Verificar: tests de distancia entre meses y de columnas.
- [x] 021.2 Excluir el último mes incompleto y aplicar el modelo escalonado. Verificar: tests con mes cortado y con 5, 6, 23 y 24 meses.
- [x] 021.3 Calcular intervalos con `statsmodels`. Verificar: `inferior ≤ prediccion ≤ superior`, sin negativos.
- [x] 021.4 Crear `monthly_forecast_series` y migrar reportes. Verificar: puntos según el horizonte aplicado y tests de exportación.
- [x] 021.5 Proyectar por categoría. Verificar: las categorías suman el general en el caso del plan.
- [x] 021.6 Actualizar `docs/ml-models.md` y `CLAUDE.md`. Verificar: describen el modelo real.

### Tarea 022 — Evaluación y modelos de referencia

Plan: `docs/planning/plans/022-evaluacion-baselines.md` | Depende de: 021 | Esfuerzo: L

- [x] 022.1 Implementar backtesting con origen móvil. Verificar: ningún origen ve datos futuros.
- [x] 022.2 Implementar modelos de referencia, WAPE y MASE. Verificar: tests con valores calculados a mano.
- [x] 022.3 Medir la cobertura del intervalo y diagnosticar residuos. Verificar: el reporte incluye ambos.
- [x] 022.4 Comparar contra SARIMA o ETS en un script reproducible. Verificar: dos ejecuciones dan lo mismo.
- [x] 022.5 Evaluar los niveles del modelo recortando a 6, 12 y 18 meses. Verificar: la tabla muestra el error de cada nivel.
- [x] 022.6 Documentar los resultados y sus límites. Verificar: incluye los casos donde la regresión pierde.

### Tarea 023 — Contrato de predicción y esquemas

Plan: `docs/planning/plans/023-contrato-prediccion.md` | Depende de: 016, 022 | Esfuerzo: L

- [x] 023.1 Quitar la escritura de `/predict` y devolver 422. Verificar: dos llamadas no crean filas.
- [x] 023.2 Crear la migración `0005`. Verificar: `upgrade`, `check` y `downgrade -1` pasan.
- [x] 023.3 Crear `GET /analytics/forecast` con modelo, horizonte, advertencia y extrapolación. Verificar: tests de general, categoría, 422 con 5 meses y advertencia con 12.
- [x] 023.4 Crear `POST` y `GET /analytics/predicciones`. Verificar: guardado, paginación y aislamiento.
- [x] 023.5 Declarar `response_model` en analytics y ETL. Verificar: `/docs` documenta cada respuesta.

### Tarea 024 — Series de analítica por dimensión

Plan: `docs/planning/plans/024-analitica-dimensiones.md` | Depende de: 020 | Esfuerzo: M

- [x] 024.1 Crear `/analytics/stats/series` por mes y día. Verificar: pasa en SQLite y PostgreSQL.
- [x] 024.2 Agregar filtro de categoría y validación. Verificar: tests de categoría y de 422.
- [x] 024.3 Omitir periodos sin ventas. Verificar: febrero no aparece entre enero y marzo.
- [x] 024.4 Agregar filtros a `/ventas`. Verificar: test de paginación con filtro.
- [x] 024.5 Probar el aislamiento. Verificar: un usuario no recibe datos de otro.

### Tarea 025 — Dashboard general, categoría y mes

Plan: `docs/planning/plans/025-dashboard-explorador.md` | Depende de: 018, 019, 024 | Esfuerzo: L

- [x] 025.1 Crear cliente, tipos y selector de vistas y medida. Verificar: tests de cliente y RTL de Monto / Cantidad.
- [x] 025.2 Crear la gráfica de años superpuestos. Verificar: meses faltantes en `null`, nunca en cero.
- [x] 025.3 Crear vistas por categoría y por mes. Verificar: parámetros correctos por vista.
- [x] 025.4 Conservar el historial completo mensual. Verificar: RTL de la vista secundaria.
- [x] 025.5 Integrar filtros, caché y móvil. Verificar: claves completas y sin desbordamiento a 375 px.

### Tarea 026 — Proyecciones en gráficos

Plan: `docs/planning/plans/026-proyecciones-graficas.md` | Depende de: 018, 019, 023 | Esfuerzo: L

- [x] 026.1 Crear cliente, tipos y selector. Verificar: no hay petición antes del clic.
- [x] 026.2 Crear gráfico con historial, proyección y banda. Verificar: sin puntos inventados.
- [x] 026.3 Marcar la extrapolación y mostrar las advertencias del backend. Verificar: RTL de nota, estilo, horizonte menor a 12 y aviso de categoría.
- [x] 026.4 Crear la tabla mensual, la selección de mes y el selector Monto / Cantidad. Verificar: RTL con valores, cero y `null`.
- [x] 026.5 Agregar guardado y lista de proyecciones. Verificar: RTL de guardado, error y lista vacía.

### Tarea 027 — Métricas comprensibles

Plan: `docs/planning/plans/027-metricas-comprensibles.md` | Depende de: 026 | Esfuerzo: S-M

- [x] 027.1 Centralizar textos en `metricExplanations.ts`. Verificar: tests con valores normales, cero, negativos y `null`.
- [x] 027.2 Crear `InfoHint` accesible. Verificar: funciona con teclado.
- [x] 027.3 Reescribir `ForecastQuality` con títulos, unidades y etiqueta. Verificar: RTL de unidades y rangos.
- [x] 027.4 Explicar la banda y plegar el detalle técnico. Verificar: RTL de texto y plegado.

### Tarea 028 — Accesibilidad

Plan: `docs/planning/plans/028-accesibilidad.md` | Depende de: 025, 026 | Esfuerzo: M

- [x] 028.1 Corregir foco, Escape e ids de `Modal`. Verificar: RTL de cada comportamiento.
- [x] 028.2 Dar equivalente en texto a todos los gráficos. Verificar: RTL encuentra la tabla.
- [x] 028.3 Corregir el menú móvil. Verificar: botón con nombre accesible.

### Tarea 029 — Configuración y autenticación

Plan: `docs/planning/plans/029-configuracion-auth.md` | Depende de: 015 | Esfuerzo: M

- [x] 029.1 Centralizar configuración y cerrar CORS. Verificar: `os.getenv` solo en `config.py` y `*` rechazado en producción.
- [x] 029.2 Reemplazar `passlib`. Verificar: los hashes existentes siguen validando.
- [x] 029.3 Limitar contraseña a 72 bytes y buscar el rol por nombre. Verificar: tests de ambos.
- [x] 029.4 Capturar `IntegrityError` y corregir `Content-Disposition`. Verificar: tests de ambos.

### Tarea 030 — Cerrar huecos de pruebas

Plan: `docs/planning/plans/030-cobertura-tests.md` | Depende de: 017, 023, 024 | Esfuerzo: M

- [x] 030.1 Crear `second_user` y corregir el test de purga. Verificar: falla si se quita el filtro.
- [x] 030.2 Crear tests de aislamiento por endpoint. Verificar: la lista cubre todas las rutas privadas.
- [x] 030.3 Completar rutas sin prueba. Verificar: informe de cobertura.
- [x] 030.4 Correr la suite en PostgreSQL y quitar el parche de fechas. Verificar: ambos motores pasan.

### Tarea 031 — Limpieza y documentación

Plan: `docs/planning/plans/031-limpieza-documentacion.md` | Depende de: 015-030 | Esfuerzo: S-M

- [x] 031.1 Eliminar código muerto. Verificar: búsquedas vacías y suites en verde.
- [x] 031.2 Corregir `VITE_API_URL` y el select de categoría. Verificar: tests de ambos.
- [x] 031.3 Actualizar `AGENTS.md`, `README.md`, `Makefile` y `CHANGELOG.md`. Verificar: coinciden con el sistema final.
- [x] 031.4 Ejecutar la verificación global. Verificar: todos los comandos terminan con código 0.

## Fase 3: revisión del usuario

**Base:** commit `39d3d7a` (merge del PR #2). **Origen:** revisión de `/predictions` por el usuario y entrevista de diseño del 2026-11-08.

**Decisiones tomadas:**

- Un botón "i" en cada aparición de intervalo del 95 %, extrapolación y el aviso de cautela; también en mes en curso, tipo de modelo, rango del día siguiente y proyecciones guardadas.
- Etiqueta por métrica: MAPE y RMSE relativo al mes promedio con los rangos del MAPE; R² con 0.6 / 0.3 / 0; mejora con 20 % / 5 % / −5 %. Sin valor: "Sin dato".
- La etiqueta general es el promedio de las etiquetas disponibles, redondeado hacia abajo.
- El aviso se llama "Toma esta proyección con cautela" y lista los motivos que el backend envía en `advertencias`.

### Tarea 032 — Explicaciones claras en predicciones

Plan: `docs/planning/plans/032-explicaciones-predicciones.md` | Depende de: 027, 028 | Esfuerzo: M

- [x] 032.1 Agregar `advertencias` al pronóstico mensual sin cambiar `advertencia`. Verificar: tests con y sin motivos.
- [x] 032.2 Centralizar los textos de los conceptos. Verificar: cada concepto tiene título y explicación.
- [x] 032.3 Calcular la etiqueta de cada métrica y la general. Verificar: tests de rangos, límites, `null` y promedio.
- [x] 032.4 Mostrar los badges, la etiqueta general y el resumen. Verificar: RTL de cada badge y de "Sin dato".
- [x] 032.5 Agregar el "i" en cada concepto y la lista de motivos del aviso. Verificar: RTL con clic, Enter y Escape.

### Tarea 033 — Panel del "i" sin barras de desplazamiento

Plan: `docs/planning/plans/033-panel-info-flotante.md` | Depende de: 032 | Esfuerzo: S

- [x] 033.1 Calcular la posición del panel en `placeHint`. Verificar: tests de abajo, arriba y bordes.
- [x] 033.2 Dibujar el panel en un portal que siga al botón. Verificar: RTL de portal, clic fuera y Escape.
- [x] 033.3 Explicar una vez el rango y la extrapolación en las proyecciones guardadas. Verificar: RTL sin "i" en las tablas de lotes.

### Tarea 034 — Métrica MAE

Plan: `docs/planning/plans/034-metrica-mae.md` | Depende de: 022, 032 | Esfuerzo: S-M

- [x] 034.1 Calcular MAE y RMSE con `sklearn.metrics`. Verificar: test con la fórmula de la tesis y RMSE sin cambios.
- [x] 034.2 Exponer `mae` en las métricas mensuales y diarias. Verificar: tests de la API con valor y con `null`.
- [x] 034.3 Mostrar el MAE en "Detalle técnico". Verificar: RTL de unidad y "No disponible".
- [x] 034.4 Agregar el MAE a la evaluación y regenerarla. Verificar: columna MAE del modelo y de las referencias.
- [x] 034.5 Actualizar la documentación y resolver REQ-37. Verificar: `docs/ml-models.md` y `CLAUDE.md` listan el MAE.

## Fase 4: predicción por producto

**Base:** commit `a734296` (merge del PR #3). **Origen:** pedido del usuario y entrevista de diseño del 2026-11-09.

**Decisiones tomadas:**

- Solo predicciones e historial. El dashboard, los reportes y "Mañana" no cambian.
- El producto se normaliza con espacios unificados y mayúscula inicial en cada palabra; los acentos se mantienen. La migración `0006` normaliza los datos ya cargados.
- El producto depende de la categoría: sin `categoria`, la API responde 422.
- La proyección de un producto se compara con la de su categoría.
- `predicciones.producto` es una columna nueva que acepta nulos.

### Tarea 034b — Predicción e historial por producto

Plan: `docs/planning/plans/034b-prediccion-producto.md` | Depende de: 033 | Esfuerzo: M

- [x] 034b.1 Normalizar el producto al cargar y en la migración `0006`. Verificar: tests de normalización; `upgrade`, `check` y `downgrade -1` pasan.
- [x] 034b.2 Crear `GET /analytics/productos?categoria=`. Verificar: tests de orden, 422 y aislamiento.
- [x] 034b.3 Agregar `producto` a `/forecast`, `POST /predicciones` y `/ventas`. Verificar: tests de proyección, guardado, 422 y paginación.
- [x] 034b.4 Agregar el selector dependiente en predicciones. Verificar: RTL de selector, petición tras el clic, aviso y título del lote.
- [x] 034b.5 Agregar los selectores al historial de ventas. Verificar: RTL de página 1 y parámetros.

## Fase 5: mapeo de columnas

**Base:** commit `3e92380`. **Origen:** pedido del usuario, entrevista de diseño y revisión Goldfish del 2026-11-09 (`docs/planning/plans/035.5-correciones.md`).

**Decisiones tomadas:**

- Sin LLM y sin coincidencia aproximada: solo nombres exactos y un diccionario de sinónimos. No se agrega asistente de dudas.
- La UI muestra la propuesta y el usuario la confirma antes de cargar. El servidor no guarda el archivo entre pasos.
- Sin `mapeo`, la carga exige los nombres exactos en CSV y XLSX, igual que hoy. Hay tres excepciones intencionales: se rechazan las fechas numéricas, una categoría `NaN` pasa a "General" y un XLSX sin filas responde 200.
- Sin columna de monto, `build_venta` calcula `monto = round(precio_unitario * cantidad, 2)`.
- La descarga del XLSX estandarizado pasa a la tarea 037.

### Tarea 035 — Mapeo de columnas en la carga de ventas

Plan: `docs/planning/plans/035-mapeo-columnas.md` | Depende de: 034b | Esfuerzo: M

- [x] 035.1 Crear `column_mapping.py`. Verificar: `pytest tests/test_column_mapping.py` con sinónimos, empates, orden de roles, validación y dataset generado.
- [x] 035.2 Agregar `read_table`, la regla SQL, `mapeo` en `load_sales`, el monto derivado y las tres excepciones. Verificar: los tests ETL actuales pasan sin cambios y los nuevos pasan.
- [x] 035.3 Crear `POST /etl/analizar-columnas` y `mapeo` en la carga. Verificar: tests CSV/XLSX/SQL, sin escrituras, 400, 409 y 401, y `test_isolation.py`.
- [x] 035.4 Agregar `ColumnMappingPanel` en la carga. Verificar: RTL de propuesta, badges, habilitación, `mapeo` enviado, error del análisis y cambio de archivo.
- [x] 035.5 Actualizar `CLAUDE.md`. Verificar: la verificación global termina con código 0.

## Fase 6: datos reales

**Base:** commit `bf0c7c7`. **Origen:** pedido del usuario del 2026-11-10.

**Decisiones tomadas:**

- Ningún dataset se descarga sin la aprobación del usuario. Solo se aceptan datasets con 12 meses o más de ventas con fecha, y se prefieren los que traen varios archivos de la misma empresa.
- Los datos reales quedan en `backend/temp_data/`, fuera de git. `backend/scripts/prepare_real_dataset.py` los prepara sin borrar filas inválidas.
- La 036 agrega a `SYNONYMS` los encabezados en inglés que falten para los datasets aprobados.
- Cada empresa se carga en su propia cuenta de prueba. Los resultados van en `docs/pruebas/036-datos-reales.md`.

### Tarea 036 — Pruebas con datasets reales de e-commerce

Plan: `docs/planning/plans/036-datasets-reales.md` | Depende de: 035 | Esfuerzo: M

- [x] 036.1 Obtener la aprobación de cada dataset y confirmar su ficha. Verificar: la tabla del plan marca cada dataset como aprobado o rechazado.
- [x] 036.2 Descargar los datasets aprobados en `backend/temp_data/`. Verificar: `git status` no muestra datos.
- [x] 036.3 Crear `prepare_real_dataset.py`. Verificar: límites de filas y bytes, rangos sin solapar y suma de filas igual al origen.
- [x] 036.4 Agregar los sinónimos que falten. Verificar: un test de encabezados por dataset, sin empates, y los tests actuales sin cambios.
- [x] 036.5 Cargar los archivos de cada empresa en orden. Verificar: totales, serie mensual sin huecos, `meses_observados` de todos los archivos y 409 al repetir.
- [x] 036.6 Documentar los resultados y cerrar. Verificar: la verificación global termina con código 0.

## Fase 7: carga de varios archivos

**Base:** commit `bf0c7c7`. **Origen:** hallazgo de la tarea 036 y pedido del usuario del 2026-11-10.

**Decisiones tomadas:**

- El 037 sigue reservado para la descarga del XLSX estandarizado; la carga de varios archivos es la 038.
- Solo frontend: la página llama a `analizar-columnas` y `upload-ventas` una vez por archivo, en serie y en orden natural de nombre. La API no cambia.
- Los archivos con los mismos encabezados comparten un solo mapeo; uno con encabezados distintos muestra el suyo.
- Si un archivo falla (409, 400, 413 o 500), la carga sigue con el resto y una tabla muestra el estado de cada uno.
- Un solo archivo se carga igual que hoy. Máximo de 50 archivos por selección.

### Tarea 038 — Carga de varios archivos a la vez

Plan: `docs/planning/plans/038-carga-varios-archivos.md` | Depende de: 035 | Esfuerzo: M

- [x] 038.1 Crear `uploadBatch.ts` con orden, grupos, totales y estado de error. Verificar: `npx vitest run src/lib/uploadBatch.test.ts`.
- [x] 038.2 Aceptar varios archivos en `UploadDropzone`. Verificar: RTL de `drop` con tres archivos, `multiple`, límite de 50 y archivo no válido.
- [x] 038.3 Crear `UploadBatchTable`. Verificar: RTL de estados, conteos, totales y detalle.
- [x] 038.4 Rehacer el flujo de `UploadPage`. Verificar: tests actuales sin cambios; RTL de un grupo, dos grupos, 409 en medio y selección reemplazada.
- [x] 038.5 Actualizar `CLAUDE.md` y el hallazgo de la 036. Verificar: la verificación global termina con código 0.

## Fase 8: seguridad y despliegue

**Base:** commit `faa97af`. **Origen:** pedido del usuario y entrevista de diseño del 2026-11-11.

**Decisiones tomadas:**

- Auditoría y corrección: se corrigen los hallazgos altos y medios; los bajos e informativos quedan en el informe. Un hallazgo alto o medio sin tarea es STOP y, con aprobación, se agrega como subtarea.
- Uso esperado: demo pública de tesis, con registro abierto.
- Host: frontend en Vercel (Hobby, gratis), backend en Railway (Hobby, ~US$5/mes, sin suspensión y memoria según uso) y PostgreSQL en Neon (gratis, sin caducidad). Se descartaron Render gratis (se suspende, 512 MB y base que caduca) y Render Starter (512 MB). Todo se configura con variables de entorno; la 045 agrega `vercel.json`, `railway.json` y la guía.
- Herramientas: revisión manual, reglas `S` de ruff (bandit), `pip-audit`, `npm audit`, `gitleaks` y OWASP ZAP baseline (a mano, con Java).
- Sesión: el JWT sigue en `localStorage`, mitigado con CSP estricta.
- Rate limit por IP real tras proxy confiable (`TRUSTED_PROXIES`): login 5/min, registro 3/min, carga 10/min, cómputo 20/min y global 120/min.
- En producción: Swagger oculto, `SECRET_KEY` de 32 caracteres o más, PostgreSQL con `sslmode=require` y cabeceras de seguridad.
- Campos: reglas estrictas iguales en Zod y Pydantic; correo en minúsculas; 422 sin eco del valor; Excel con apóstrofo ante fórmulas.
- Correo: verificación obligatoria por enlace de 24 h, enviado por Brevo vía SMTP genérico. Los enlaces van al frontend con el token en el fragmento y se confirman por `POST`.
- La migración `0007` borra todos los usuarios actuales y sus datos (son de prueba).
- Contraseñas: cambio con la actual, restablecimiento por enlace de 30 min, bloqueo de 15 min tras 10 fallos con aviso por correo, revocación de sesiones por `version_token`.
- Cambio de correo: exige la contraseña actual y confirmar el correo nuevo antes de aplicarlo.
- Una sola branch `feat/039-seguridad`, con un commit por tarea y sin coautoría.

**Orden de ejecución acordado:** 039, 044, 040, 041, 042, 043, 045. La 044 se adelantó el 2026-11-11, tras la auditoría, para que el CI vigile el resto.

### Tarea 039 — Auditoría de seguridad

Plan: `docs/planning/plans/039-auditoria-seguridad.md` | Depende de: ninguna | Esfuerzo: M

- [x] 039.1 Revisar el código con la checklist manual. Verificar: cada punto tiene resultado con archivo y línea en el informe.
- [x] 039.2 Activar las reglas `S` de ruff. Verificar: `ruff check app/` termina con código 0 y cada `noqa: S` tiene motivo.
- [x] 039.3 Ejecutar `pip-audit` y `npm audit`. Verificar: resultados registrados en el informe.
- [x] 039.4 Ejecutar `gitleaks` sobre el historial. Verificar: cada coincidencia clasificada; un secreto real es STOP.
- [x] 039.5 Ejecutar ZAP baseline en local. Verificar: informe en `docs/seguridad/` y cada alerta en la tabla.
- [x] 039.6 Escribir `docs/seguridad/auditoria-039.md`. Verificar: todo hallazgo alto o medio tiene tarea o pasó por el STOP.

### Tarea 040 — Validación de campos y exportación segura

Plan: `docs/planning/plans/040-validacion-campos.md` | Depende de: 039 | Esfuerzo: M

- [ ] 040.1 Aplicar las reglas de campos en Pydantic. Verificar: `pytest tests/test_field_validation.py` con un caso válido y uno inválido por regla.
- [ ] 040.2 Guardar y buscar el correo en minúsculas. Verificar: registro con mayúsculas, duplicado y login.
- [ ] 040.3 Acotar `categoria` y `producto` y rechazar caracteres de control en la API y la ETL. Verificar: tests de 422 y de fila rechazada.
- [ ] 040.4 Neutralizar fórmulas en el Excel. Verificar: `'=1+1` como texto y montos numéricos sin cambio.
- [ ] 040.5 Quitar el eco del valor en los 422. Verificar: el cuerpo no contiene la contraseña enviada.
- [ ] 040.6 Repetir las reglas en Zod con `fieldLimits.ts`. Verificar: tests de `authSchemas` y `test_field_limits_contract.py`.

### Tarea 041 — Rate limit, proxy, cabeceras y configuración de producción

Plan: `docs/planning/plans/041-endurecer-api.md` | Depende de: 039 | Esfuerzo: M

- [ ] 041.1 Validar `SECRET_KEY` y SSL en producción. Verificar: tests de configuración en producción y desarrollo.
- [ ] 041.2 Leer la IP real tras un proxy confiable. Verificar: test con proxy confiable y no confiable.
- [ ] 041.3 Aplicar límites por ruta y global con 429 en español. Verificar: `pytest tests/test_rate_limit.py`.
- [ ] 041.4 Agregar cabeceras y ocultar Swagger en producción. Verificar: `pytest tests/test_security_headers.py`.
- [ ] 041.5 Documentar `TRUSTED_PROXIES` y los límites. Verificar: la verificación global termina con código 0.
- [ ] 041.6 Limitar el tamaño del cuerpo antes de leerlo (S-20) y corregir el 500 de `GET /` (S-21). Verificar: `pytest tests/test_body_limit.py` y `GET /` responde 200.

### Tarea 042 — Verificación de correo

Plan: `docs/planning/plans/042-verificacion-correo.md` | Depende de: 040, 041 | Esfuerzo: L

- [ ] 042.1 Crear `email_service` y sus variables. Verificar: tests con `console` y SMTP simulado; producción sin SMTP no arranca.
- [ ] 042.2 Crear la migración `0007` que borra los usuarios. Verificar: STOP y confirmación antes de aplicarla; `upgrade`, `check` y `downgrade -1` pasan.
- [ ] 042.3 Crear `token_service`. Verificar: solo se guarda el hash y un token sirve una vez.
- [ ] 042.4 Exigir la verificación en el login y agregar reenvío y confirmación. Verificar: `pytest tests/test_email_verification.py`.
- [ ] 042.5 Cambiar el correo con contraseña y confirmación. Verificar: tests de `correo_pendiente`.
- [ ] 042.6 Agregar `VerifyEmailPage` y los cambios en registro, login y perfil. Verificar: RTL de cada página.

### Tarea 043 — Contraseñas, bloqueo y revocación de sesiones

Plan: `docs/planning/plans/043-contrasenas-bloqueo.md` | Depende de: 042 | Esfuerzo: L

- [ ] 043.1 Crear la migración `0008`. Verificar: `upgrade`, `check` y `downgrade -1` pasan.
- [ ] 043.2 Revocar sesiones con el claim `ver`. Verificar: token con `ver` vieja o sin `ver` da 401.
- [ ] 043.3 Agregar el cambio de contraseña. Verificar: `pytest tests/test_passwords.py`.
- [ ] 043.4 Agregar olvido y restablecimiento por correo. Verificar: mismo mensaje con y sin cuenta, 30 min y un solo uso.
- [ ] 043.5 Bloquear tras 10 fallos durante 15 min. Verificar: `pytest tests/test_lockout.py`.
- [ ] 043.6 Agregar las páginas de olvido y restablecimiento y el cambio en el perfil. Verificar: RTL de cada página.

### Tarea 044 — Escáneres de seguridad en CI

Plan: `docs/planning/plans/044-escaneres-ci.md` | Depende de: 039 | Esfuerzo: S

- [ ] 044.0 Subir `PyJWT` a 2.15.1 y aplicar `npm audit fix` (S-18, S-19). Verificar: suites de auth y frontend pasan; `pip-audit` y `npm audit --omit=dev --audit-level=high` terminan con código 0.
- [ ] 044.1 Agregar `pip-audit` al job `backend`. Verificar: termina con código 0 en local.
- [ ] 044.2 Agregar `npm audit` al job `frontend`. Verificar: termina con código 0 en local.
- [ ] 044.3 Agregar el job `secrets` y el hook de `gitleaks`. Verificar: `pre-commit run gitleaks --all-files` pasa y falla con un secreto falso.
- [ ] 044.4 Comprobar CI en la branch. Verificar: los tres jobs pasan en GitHub Actions.

### Tarea 045 — CSP y despliegue en Vercel, Railway y Neon

Plan: `docs/planning/plans/045-guia-despliegue.md` | Depende de: 041, 042, 043 | Esfuerzo: M

- [ ] 045.1 Agregar la CSP en `index.html` con el origen del API. Verificar: `dist/index.html` contiene el `connect-src` esperado.
- [ ] 045.2 Recorrer la app con la CSP en local. Verificar: la consola no muestra violaciones.
- [ ] 045.3 Crear `frontend/vercel.json` con cabeceras y reescritura. Verificar: test que compara su CSP con la del `<meta>`.
- [ ] 045.4 Crear `backend/railway.json` y `backend/.python-version`. Verificar: JSON válido contra el esquema de Railway.
- [ ] 045.5 Escribir `docs/despliegue.md`. Verificar: cada variable de `.env.example` y cada punto de la checklist aparecen.
- [ ] 045.6 Desplegar con la guía. Verificar: la checklist se cumple sobre los dominios reales.
- [ ] 045.7 Repetir ZAP baseline contra los dominios reales. Verificar: las alertas de cabeceras de la 039 desaparecen.
- [ ] 045.8 Verificación global. Verificar: todos los comandos terminan con código 0.

## Verificación global

Desde `backend/`, con el entorno virtual activo:

```bash
ruff check app/
mypy app/
pytest --cov=app --cov-report=term-missing
```

Desde `frontend/`:

```bash
npm run lint
npm run typecheck
npm test -- --run
npm run build
```

Las pruebas del backend no necesitan PostgreSQL: usan SQLite en memoria. Con `TEST_DATABASE_URL` apuntando a una base desechable, la misma suite corre sobre PostgreSQL.

## Fase posterior: frontend

Después del plan 008, construir frontend con React, Tailwind CSS y Chart.js:

1. Autenticación y cliente HTTP con JWT.
2. Carga de CSV/XLSX.
3. Dashboard con evolución temporal y categorías.
4. Predicciones de monto y cantidad con intervalo de confianza.
5. Descarga de reportes.

## Hallazgos pospuestos

No forman parte de esta tanda: actualización adicional de dependencias, CI, CORS estricto, contrato uniforme de errores en `/predict` y anotaciones de fecha. Revisarlos después de completar 001-009.

Actualización 2026-11-05: CI pasa a la tarea 015, las anotaciones de fecha a la 016, el contrato de `/predict` a la 023 y CORS a la 029. La actualización general de dependencias sigue pospuesta.

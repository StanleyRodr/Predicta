# Tareas del Proyecto

Plan de trabajo backend para Predicta. Ejecutar en orden salvo tareas sin dependencia.

**Base del plan:** commit `adcb0a4`  
**Estado:** `TODO`, `EN PROGRESO`, `HECHO`, `BLOQUEADO`

## Orden de ejecución

| ID | Tarea | Plan | Prioridad | Esfuerzo | Depende de | Estado |
|---|---|---|---|---|---|---|
| 001 | Crear baseline real de pruebas | `plans/001-baseline-pruebas.md` | P1 | S-M | — | TODO |
| 002 | Ocultar detalles internos en errores | `plans/002-errores-seguros.md` | P2 | S | 001 | TODO |
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

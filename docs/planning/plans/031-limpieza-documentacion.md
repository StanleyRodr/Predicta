# Plan 031: Limpieza y documentación

## Estado

- **Estado:** TODO
- **Prioridad:** P3
- **Esfuerzo:** S-M
- **Riesgo:** LOW
- **Depende de:** 015-030
- **Categoría:** limpieza / documentación
- **Origen:** `docs/feedback/feedback-01.md` F-28, F-30, F-31, F-34
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Eliminar código muerto y dejar la documentación igual al sistema final.

## Excepción autorizada

Esta tarea sí puede modificar el `README.md` raíz. El usuario autorizó F-34 como
excepción a la regla de `docs/planning/TASKS.md`. La excepción aplica solo aquí.

## Alcance

- `backend/app/ml_models/forecast.py`, `backend/app/utils/`
- `frontend/src/pages/SectionPlaceholder.tsx`, `frontend/src/pages/ReportsPage.tsx`
- `frontend/src/lib/apiErrors.ts`
- `AGENTS.md`, `README.md`, `Makefile`, `CHANGELOG.md`

## Pasos

1. Eliminar `predict_next_day`, `daily_aggregates`, `app/utils/` y
   `SectionPlaceholder.tsx`, tras confirmar que nada los usa.
   - **Verificar:** búsquedas sin resultados, y lint, tipos y tests pasan.
2. Usar `VITE_API_URL` en el mensaje de error de conexión.
   - **Verificar:** test con otra URL.
3. Cambiar la categoría de reportes a un select alimentado por
   `/analytics/stats/categories`.
   - **Verificar:** RTL con la lista y con lista vacía.
4. Corregir `AGENTS.md`: el frontend existe y los tests no necesitan PostgreSQL.
   - **Verificar:** el texto coincide con `CLAUDE.md`.
5. Actualizar `README.md`: estado de los sprints y versión de Python.
   - **Verificar:** los comandos del README funcionan.
6. Quitar del `Makefile` los targets de Docker sin docker-compose.
   - **Verificar:** los targets restantes apuntan a comandos existentes.
7. Completar `CHANGELOG.md` con las tareas 001 a 031.
   - **Verificar:** cada grupo de tareas tiene su entrada.
8. Ejecutar la verificación global de backend y frontend.
   - **Verificar:** todos los comandos terminan con código 0.

## Criterios de terminado

- No queda código muerto de la lista.
- La documentación describe el sistema final.

## STOP

- Detenerse si un elemento de la lista todavía tiene usos.

## Mantenimiento

Cada tarea futura actualiza su documentación en el mismo cambio.

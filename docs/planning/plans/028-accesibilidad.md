# Plan 028: Accesibilidad

## Estado

- **Estado:** TODO
- **Prioridad:** P2
- **Esfuerzo:** M
- **Riesgo:** LOW
- **Depende de:** `docs/planning/plans/025-dashboard-explorador.md`, `docs/planning/plans/026-proyecciones-graficas.md`
- **Categoría:** frontend
- **Origen:** `docs/feedback/feedback-01.md` F-19
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Hacer usables modales, gráficos y navegación con teclado y lector de pantalla.
Va después de los gráficos nuevos para cubrirlos también.

## Alcance

- `frontend/src/components/ui/Modal.tsx`
- `frontend/src/components/layout/AppShell.tsx`
- Gráficos de `frontend/src/components/analytics/` y `frontend/src/components/forecast/`

## Pasos

1. Cerrar `Modal` con Escape, mantener el foco dentro y restaurarlo al cerrar.
   - **Verificar:** RTL de los tres comportamientos.
2. Reemplazar `id="modal-title"` por `useId()`.
   - **Verificar:** dos modales no comparten id.
3. Crear un contenedor de gráfico con `role="img"`, descripción y una tabla
   alternativa para lectores de pantalla.
   - **Verificar:** RTL encuentra la tabla con los valores del gráfico.
4. Aplicar el contenedor a todos los gráficos.
   - **Verificar:** ningún gráfico queda con `aria-label` en un `div` sin rol.
5. Dar etiquetas accesibles al menú móvil en lugar de "MENU" y "X".
   - **Verificar:** RTL busca el botón por su nombre accesible.
6. Comprobar que las series no se distinguen solo por color.
   - **Verificar:** líneas de proyección punteadas y leyendas con texto.

## Criterios de terminado

- Todas las pantallas se recorren con teclado.
- Cada gráfico tiene su equivalente en texto.

## STOP

- Detenerse si una mejora exige cambiar el diseño de una pantalla completa.

## Mantenimiento

Todo gráfico nuevo usa el contenedor accesible.

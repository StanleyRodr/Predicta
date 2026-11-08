# Plan 033: Panel del "i" sin barras de desplazamiento

## Estado

- **Estado:** HECHO
- **Prioridad:** P2
- **Esfuerzo:** S
- **Riesgo:** LOW
- **Depende de:** `docs/planning/plans/032-explicaciones-predicciones.md`
- **Categoría:** frontend / UX
- **Origen:** revisión del usuario de las tablas de `/predictions`, 2026-11-08
- **Planificado en:** commit `e88d811`, 2026-11-08

## Objetivo

Que abrir un "i" nunca agregue barras de desplazamiento. Hoy, dentro de
"Detalle mensual" y de "Proyecciones guardadas", el panel agranda la tabla. En
las guardadas aparecen las dos barras, la vertical y la horizontal.

## Diseño

- **Causa:** el panel de `InfoHint` es `position: absolute` y queda dentro del `overflow-x-auto` de `ForecastTable`. En CSS, un eje con `overflow` distinto de `visible` hace que el otro eje también recorte.
- **Corrección:** el panel se dibuja en `document.body` con `createPortal` y `position: fixed`, junto a su botón. El botón no se mueve y la corrección vale para todos los "i" de la app.
- **Posición:**
  - Abre hacia abajo con 8 px de separación y, si no cabe, hacia arriba.
  - Se ajusta horizontalmente con 16 px de margen, para que nunca salga de la pantalla.
  - Su ancho es como máximo `min(16rem, 100vw - 32px)`.
- **Al desplazar o cambiar el tamaño de la ventana:** el panel sigue al botón. El evento `scroll` se escucha en fase de captura, para incluir el desplazamiento de la tabla.
- **Sin dependencias nuevas:** el cálculo se escribe a mano con `getBoundingClientRect`.
- **Proyecciones guardadas:** las tablas de cada lote ya no llevan "i". Una línea arriba de la lista explica el rango del 95 % y la extrapolación.

## Alcance

- `frontend/src/components/ui/InfoHint.tsx`
- `frontend/src/components/forecast/ForecastTable.tsx`
- `frontend/src/components/forecast/SavedPredictions.tsx`

## Pasos

1. Separar el cálculo de la posición en una función pura, `placeHint`.
   - **Verificar:** tests de abrir abajo, voltear arriba y ajustarse a los dos bordes.
2. Dibujar el panel en un portal que siga al botón.
   - **Verificar:** RTL de que el panel queda fuera del contenedor con `overflow`, el clic dentro no lo cierra, y el clic fuera y Escape sí.
3. Quitar los "i" de las tablas de lotes y explicarlos una vez arriba de la lista.
   - **Verificar:** RTL de que las tablas de lotes no tienen "i" y "Detalle mensual" sí.

## Criterios de terminado

- Ningún "i" agrega barras de desplazamiento.
- El panel no sale de la pantalla a 375 px de ancho.
- Teclado y lector de pantalla funcionan igual que antes.

## STOP

- Detenerse si el portal rompe el foco o el cierre con Escape.

## Mantenimiento

Todo "i" nuevo usa `InfoHint`; nunca un panel con posición absoluta propia.

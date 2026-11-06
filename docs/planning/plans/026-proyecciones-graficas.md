# Plan 026: Proyecciones en gráficos

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** L
- **Riesgo:** MED
- **Depende de:** `docs/planning/plans/018-convencion-numerica.md`, `docs/planning/plans/019-frontend-sesion-descargas.md`, `docs/planning/plans/023-contrato-prediccion.md`
- **Categoría:** frontend / ML
- **Origen:** pedido 3 del usuario
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Mostrar la proyección como un gráfico de historial y próximos meses, general o
por categoría, además de los valores numéricos.

## Decisiones tomadas

- Horizonte: hasta 12 meses, con detalle mensual. Lo decide el backend según el
  historial (plan 021).
- "Por mes" es una selección dentro de la curva: eliges un mes futuro y se
  resalta su detalle, también dentro de una categoría.
- Los meses 7 a 12 se muestran con un estilo distinto y una nota.
- Selector Monto / Cantidad, con Monto por defecto.
- La proyección sigue calculándose solo por acción explícita del usuario.
- Guardar es una acción aparte, con el botón "Guardar proyección".

## Alcance

- `frontend/src/pages/PredictionsPage.tsx`
- `frontend/src/components/forecast/`
- `frontend/src/api/forecast.ts`, `frontend/src/types/forecast.ts`

## Pasos

1. Crear el cliente y los tipos de `/analytics/forecast` y `/analytics/predicciones`.
   - **Verificar:** `npm run typecheck` y tests del cliente.
2. Crear el selector General / Categoría. Cambiarlo no dispara el cálculo hasta
   pulsar "Calcular proyección".
   - **Verificar:** test: no hay petición antes del clic.
3. Crear `ForecastChart`: línea sólida para el historial, línea punteada para la
   proyección y banda de incertidumbre entre `inferior` y `superior`.
   - **Verificar:** test de `forecastChartData`, sin puntos inventados.
4. Diferenciar visualmente los puntos con `extrapolacion` verdadero, sin
   calcular la regla en el navegador.
   - **Verificar:** RTL de la nota y del estilo.
5. Crear la tabla mensual con mes, monto, cantidad y rango.
   - **Verificar:** RTL con valores normales, cero y `null`.
6. Agregar la selección de un mes del gráfico para resaltar su detalle.
   - **Verificar:** RTL del mes seleccionado.
7. Conservar las tarjetas del día siguiente como dato complementario.
   - **Verificar:** los tests de `ForecastMetricCard` pasan.
8. Agregar "Guardar proyección" y la lista de proyecciones guardadas.
   - **Verificar:** RTL de guardado, error y lista vacía.
9. Mostrar el `detail` del 422 cuando falten datos, general o por categoría.
   - **Verificar:** RTL con el mensaje del backend.
10. Mostrar la `advertencia` del backend junto al gráfico, por ejemplo
    "Confiabilidad limitada: aún no hay dos años para detectar temporadas".
    - **Verificar:** RTL con y sin advertencia, y con un horizonte menor a 12.
11. Agregar el selector Monto / Cantidad.
    - **Verificar:** RTL del cambio de serie, ejes y tabla, sin nueva petición.
12. Avisar cuando una categoría use otro modelo que el total, porque sus
    proyecciones no suman exacto.
    - **Verificar:** RTL del aviso.

## Criterios de terminado

- General y categoría se proyectan en un gráfico con incertidumbre visible.
- Ningún cambio de filtro escribe en la base.
- La interfaz no llama "garantía" a una proyección.
- `npm run typecheck`, `npm test -- --run` y `npm run build` pasan.

## STOP

- Detenerse si la banda es tan amplia que el gráfico pierde lectura. Reportarlo
  antes de cambiar el método (plan 021).
- No calcular fechas futuras en el navegador: vienen del backend.

## Mantenimiento

Si se agrega un horizonte configurable, extender primero tipos y tests.

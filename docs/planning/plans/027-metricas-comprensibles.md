# Plan 027: Métricas comprensibles

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** S-M
- **Riesgo:** LOW
- **Depende de:** `docs/planning/plans/026-proyecciones-graficas.md`
- **Categoría:** frontend / UX
- **Origen:** pedido adicional del usuario
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Que un dueño de tienda sin formación estadística entienda en `/predictions` qué
tan confiable es una proyección. Hoy ve R², MAPE y RMSE sin unidades ni
explicación.

## Diseño

Cada métrica muestra un título sencillo, una frase con el valor real y un botón
de información. La sigla técnica queda como dato secundario.

| Métrica | Título | Frase de ejemplo | Explicación |
|---|---|---|---|
| MAPE | Error promedio | "Se desvía cerca de 12.50% del valor real." | Cuánto se equivoca en promedio, en porcentaje. Menos es mejor. |
| RMSE | Margen típico | "Suele fallar por unos $1,250.00." | El tamaño habitual del error, en dinero o unidades. Penaliza más los errores grandes. |
| R² | Patrón explicado | "Explica cerca del 80% de los cambios en las ventas." | Cuánto de la variación captura el modelo. Si es negativo, rinde peor que usar el promedio. |
| Mejora | Frente a un cálculo simple | "Acierta 18% mejor que repetir el mismo mes del año anterior." | Compara el modelo con el mejor modelo de referencia del plan 022. |

Una etiqueta resume el error promedio, con estos rangos orientativos:

| MAPE | Etiqueta |
|---|---|
| Menor que 10% | Muy buena |
| 10% a 20% | Buena |
| 20% a 50% | Aceptable |
| Mayor que 50% | Baja |

La interfaz aclara que los rangos son orientativos.

## Alcance

- `frontend/src/components/forecast/ForecastQuality.tsx`
- `frontend/src/components/ui/InfoHint.tsx` (nuevo)
- `frontend/src/lib/metricExplanations.ts` (nuevo)

## Pasos

1. Centralizar títulos, frases y explicaciones en `metricExplanations.ts`.
   - **Verificar:** tests con valores normales, cero, negativos y `null`.
2. Crear `InfoHint`, que funciona con clic, teclado y lector de pantalla, no solo
   con el puntero.
   - **Verificar:** RTL abre con Enter y cierra con Escape.
3. Reescribir `ForecastQuality` con los títulos sencillos y las unidades
   correctas: `%` en MAPE, `$` en RMSE de monto y unidades en RMSE de cantidad.
   - **Verificar:** RTL de cada unidad.
4. Mostrar la etiqueta de calidad y el resumen en una frase.
   - **Verificar:** test de cada rango y sus límites.
5. Explicar la banda de incertidumbre junto al gráfico: "El valor real
   probablemente caerá dentro de esta zona".
   - **Verificar:** RTL del texto.
6. Mantener R², MAPE, RMSE, WAPE y MASE en un bloque "Detalle técnico" plegado.
   - **Verificar:** RTL de abrir y cerrar.
7. Conservar "No disponible" y explicar por qué falta el dato.
   - **Verificar:** `null` nunca se muestra como cero.

## Criterios de terminado

- La página se entiende sin conocer las siglas.
- Cada valor tiene su unidad.
- Los textos son correctos en español, con acentos.

## STOP

- Detenerse si una frase promete más de lo que mide la métrica.
- No usar la palabra "precisión" para el R².

## Mantenimiento

Cada métrica nueva se agrega a `metricExplanations.ts` con título, frase y
explicación.

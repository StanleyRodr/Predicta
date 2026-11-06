# Plan 020: Reportes seguros y capa de servicios

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** L
- **Riesgo:** MED
- **Depende de:** `docs/planning/plans/017-etl-endurecida.md`, `docs/planning/plans/018-convencion-numerica.md`
- **Categoría:** backend
- **Origen:** `docs/feedback/feedback-01.md` F-04, F-09, F-14, F-32
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Generar reportes sin estado global compartido entre hilos, con memoria acotada,
y dejar las rutas como una capa HTTP delgada.

## Fuera de alcance

Las vistas nuevas por categoría y año son solo para la web. Los PDF no las
incorporan en esta fase.

## Alcance

- `backend/app/api/analytics_routes.py`, `backend/app/api/etl_routes.py`
- `backend/app/services/report_service.py` (nuevo)
- `backend/app/services/analytics_service.py` (nuevo)
- `backend/app/services/etl_service.py` (nuevo)

## Pasos

1. Antes de mover código, agregar tests de caracterización de las exportaciones
   y de `/reporte-mensual`.
   - **Verificar:** los tests pasan sobre el código actual.
2. Reemplazar `plt.subplots`, `plt.xticks` y `plt.tight_layout` por
   `matplotlib.figure.Figure` y métodos de `ax` y `fig`.
   - **Verificar:** una búsqueda de `plt.` en reportes no encuentra resultados.
3. Generar las imágenes en `BytesIO` y eliminar los PNG temporales.
   - **Verificar:** una búsqueda de `tempfile` no encuentra resultados y dos
     reportes concurrentes terminan sin error.
4. Mover PDF, Excel y gráficos a `report_service.py`.
   - **Verificar:** los tests del paso 1 pasan sin cambios.
5. Mover las agregaciones a `analytics_service.py` y resolverlas con `GROUP BY`.
   - **Verificar:** los valores coinciden con los de antes del cambio.
6. Mover el parseo y la validación a `etl_service.py`.
   - **Verificar:** la suite ETL pasa sin cambios.
7. Limitar el PDF a resúmenes y al top 20 de ventas, sin detalle completo.
   - **Verificar:** con 28,667 filas, el PDF queda en un número acotado de
     páginas.
8. Mostrar el año real en las barras del reporte mensual (F-32).
   - **Verificar:** test de las etiquetas.

## Criterios de terminado

- Cada ruta valida, llama a un servicio y responde.
- Todo filtro por `id_usuario` se conserva. Los servicios lo reciben de forma
  explícita.
- Las respuestas HTTP no cambian, salvo el contenido acotado del PDF.

## STOP

- Detenerse si un test de caracterización falla tras mover código: es un cambio
  de comportamiento y no se corrige ajustando el test.
- No agregar lógica nueva durante los pasos 4 a 6.

## Mantenimiento

Las rutas no contienen lógica de negocio. Lo nuevo se agrega en los servicios.

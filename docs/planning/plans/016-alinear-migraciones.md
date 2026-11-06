# Plan 016: Alinear modelos y migraciones

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** MED
- **Depende de:** `docs/planning/plans/015-ci-calidad.md`
- **Categoría:** datos
- **Origen:** `docs/feedback/feedback-01.md` F-06, F-29
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Lograr que `alembic check` no detecte diferencias entre los modelos y la base,
antes de que las tareas 017 y 023 agreguen migraciones nuevas.

## Estado actual

- El modelo usa `idx_ventas_usuario_fecha` e `idx_ventas_categoria`; la
  migración `0001` crea `ix_ventas_usuario_fecha` e `ix_ventas_categoria`.
- `predicciones.id_usuario` es `NOT NULL` en el modelo y `nullable=True` en la
  migración. No tiene índice.
- `index=True` en `ventas.id_usuario` y `ventas.fecha_venta` duplica parte del
  índice compuesto.
- `fecha_venta` y `fecha_proyeccion` son `Date`, pero están tipadas como
  `Mapped[datetime]`.
- La nota de F-06 sobre cambios sin commitear ya no aplica: entraron en el
  commit `18e36df`.

## Alcance

- `backend/app/models/models.py`
- `backend/alembic/versions/0003_*.py`
- `.github/workflows/ci.yml`

## Pasos

1. Ejecutar `alembic check` en una base temporal y guardar las diferencias.
   - **Verificar:** la lista coincide con F-06 o se documenta lo adicional.
2. Cambiar las columnas `Date` a `Mapped[date]`.
   - **Verificar:** `mypy app/` y `pytest` pasan.
3. Decidir qué índices quedan y quitar los redundantes del modelo. Conservar
   el índice compuesto `(id_usuario, fecha_venta)`.
   - **Verificar:** ninguna consulta por usuario pierde cobertura de índice.
4. Crear la migración `0003`: renombrar índices, agregar el índice de
   `predicciones.id_usuario` y aplicar `NOT NULL`.
   - **Verificar:** revisión manual de `upgrade` y `downgrade`.
5. Antes de aplicar `NOT NULL`, contar las filas con `id_usuario` nulo.
   - **Verificar:** la migración falla con un mensaje claro si existen, sin
     borrar datos en silencio.
6. Activar `alembic check` en CI.
   - **Verificar:** `alembic upgrade head`, `alembic check` sin diferencias y
     `alembic downgrade -1` pasan en PostgreSQL.

## Criterios de terminado

- `alembic check` está en verde en CI.
- La migración baja y sube sin error.

## STOP

- Detenerse si hay filas de `predicciones` con `id_usuario` nulo. Borrarlas es
  una decisión del usuario.
- No usar `create_all()` en runtime.

## Mantenimiento

Toda migración nueva debe pasar `alembic check` y una prueba de `downgrade`.

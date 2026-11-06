# Plan 030: Cerrar huecos de pruebas

## Estado

- **Estado:** TODO
- **Prioridad:** P2
- **Esfuerzo:** M
- **Riesgo:** LOW
- **Depende de:** `docs/planning/plans/017-etl-endurecida.md`, `docs/planning/plans/023-contrato-prediccion.md`, `docs/planning/plans/024-analitica-dimensiones.md`
- **Categoría:** pruebas
- **Origen:** `docs/feedback/feedback-01.md` F-17
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Probar de verdad el aislamiento entre usuarios y correr la suite sobre el mismo
motor que producción.

## Alcance

- `backend/tests/`
- `.github/workflows/ci.yml`
- `backend/app/api/analytics_routes.py` (parche `isinstance(r.fecha, str)`)

## Pasos

1. Crear el fixture `second_user`.
   - **Verificar:** el fixture entrega encabezados de un usuario distinto.
2. Corregir `test_clear_history_deletes_only_current_user_sales`, que hoy no crea
   un segundo usuario.
   - **Verificar:** el test falla si se quita el filtro por usuario.
3. Crear tests de aislamiento parametrizados por endpoint, incluidas las
   exportaciones y las rutas nuevas.
   - **Verificar:** cada endpoint con datos privados aparece en la lista.
4. Agregar tests de `/reporte-mensual`, `/prediccion-categorias` y la paginación
   de `/ventas`, si aún faltan.
   - **Verificar:** el informe de cobertura muestra esas líneas.
5. Ejecutar la suite en CI también sobre PostgreSQL.
   - **Verificar:** el job pasa con ambos motores.
6. Quitar el parche `isinstance(r.fecha, str)`, si PostgreSQL y SQLite quedan
   cubiertos con una conversión común.
   - **Verificar:** ambos motores pasan.

## Criterios de terminado

- Ningún test promete en su nombre algo que no comprueba.
- Quitar un filtro `id_usuario` hace fallar al menos un test.

## STOP

- Detenerse y reportar si aparece una fuga real entre usuarios. Es prioridad
  sobre el resto de la tarea.

## Mantenimiento

Todo endpoint nuevo con datos privados entra en la lista de aislamiento.

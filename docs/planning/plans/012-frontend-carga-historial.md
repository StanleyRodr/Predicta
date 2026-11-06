# Plan 012: Carga ETL e historial

## Estado

- **Estado:** HECHO
- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** MED
- **Depende de:** `docs/planning/plans/011-frontend-auth-layout.md`
- **Categoria:** frontend / ETL
- **Planificado en:** commit `96e38cc`, 2026-10-18

## Objetivo

Permitir cargar CSV, XLSX o SQL y revisar resultado, errores por fila e
historial del usuario sin exponer datos de otros usuarios.

## Contrato backend

- `POST /etl/upload-ventas`: multipart field `file`.
- Extensiones: `.csv`, `.xlsx`, `.sql`.
- Limite: 25 MB.
- Respuesta: `registros_leidos`, `registros_cargados`, `filas_rechazadas`,
  `errores` y `message`.
- `DELETE /etl/clear-history`: elimina historial del usuario autenticado.
- `GET /analytics/ventas`: `skip`, `limit`; responde registros paginados.

## Pasos

1. Crear tipos `UploadResult`, `UploadRowError`, `SalesHistoryResponse` y
   `SaleRecord` desde respuestas reales de FastAPI.
   - **Verificar:** `npx tsc --noEmit` pasa.
2. Crear schema de archivo: obligatorio, extension permitida y maximo 25 MB.
   - **Verificar:** tests rechazan archivo vacio, tipo no permitido y archivo grande.
3. Crear `UploadDropzone` con selector de archivo y soporte drag-and-drop.
   - **Verificar:** RTL confirma teclado, seleccion, cancelacion y estado loading.
4. Crear mutation TanStack Query para `/etl/upload-ventas` usando
   `multipart/form-data`; no establecer boundary manualmente.
   - **Verificar:** mock confirma FormData con campo `file` y refresh del historial.
5. Mostrar resumen de carga: leidos, cargados, rechazados y tasa visual simple.
   - **Verificar:** test renderiza conteos y cero errores correctamente.
6. Mostrar tabla de errores limitada a los errores recibidos por API, con fila y
   mensaje. No inventar errores del servidor.
   - **Verificar:** test muestra fila concreta y estado sin errores.
7. Crear historial paginado con `/analytics/ventas`, `skip` y `limit`, newest first.
   - **Verificar:** test cambia pagina, conserva usuario y muestra estado vacio.
8. Crear modal de confirmacion para `DELETE /etl/clear-history`.
   - **Verificar:** cancelar no llama API; confirmar invalida cache y vacia tabla.

## Criterios de terminado

- Carga valida CSV/XLSX/SQL desde navegador.
- Errores HTTP 400, 413, 401 y 500 tienen mensajes en español.
- Historial respeta paginacion backend.
- Ningun archivo se carga automaticamente sin accion explicita.

## STOP

- Detenerse si el backend cambia el nombre multipart `file`.
- No parsear archivos completos en frontend; backend es fuente de validacion.
- No mostrar contenido SQL cargado como HTML.

## Mantenimiento

Si backend agrega una extension, actualizar schema, texto permitido y tests en
la misma entrega.

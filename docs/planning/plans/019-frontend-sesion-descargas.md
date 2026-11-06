# Plan 019: Sesión, errores y descargas en el frontend

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** MED
- **Depende de:** ninguna
- **Categoría:** frontend / seguridad
- **Origen:** `docs/feedback/feedback-01.md` F-07, F-18
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Impedir que un usuario vea datos de otro en el mismo navegador, y corregir los
errores y las descargas antes de agregar más consultas por filtro.

## Alcance

- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/App.tsx`, `frontend/src/api/http.ts`, `frontend/src/api/reports.ts`
- `frontend/src/pages/PredictionsPage.tsx`, `frontend/src/pages/UploadPage.tsx`

## Pasos

1. Llamar a `queryClient.clear()` en el logout manual y en el evento
   `predicta:unauthorized`.
   - **Verificar:** test RTL con login A, predicción, logout, login B: no
     aparece ningún dato de A.
2. Incluir `userId` en todas las claves de consulta, incluidas `["forecast"]`
   y `["sales-history", page]`.
   - **Verificar:** una búsqueda de `queryKey` no encuentra claves de datos
     privados sin `userId`.
3. Leer el Blob de error con `await data.text()` y `JSON.parse`, y reutilizar
   `getApiErrorMessage`.
   - **Verificar:** test que muestra "Muestreo insuficiente" desde un Blob.
4. Revocar la URL de descarga con `setTimeout`.
   - **Verificar:** test con temporizadores falsos.
5. Definir timeouts por petición: 120 s para cargas y reportes, y 15 s para el
   resto.
   - **Verificar:** test de la configuración de cada cliente.
6. Invalidar `analytics` y `forecast` después de una carga o una purga.
   - **Verificar:** test que confirma la invalidación.

## Criterios de terminado

- Ningún dato de un usuario queda en caché tras cerrar sesión.
- Los errores de descarga muestran el mensaje público del backend.
- `npm run typecheck`, `npm test -- --run` y `npm run build` pasan.

## STOP

- Detenerse si limpiar la caché provoca un bucle de redirección en el 401.

## Mantenimiento

Toda consulta nueva de datos privados incluye `userId` en su clave.

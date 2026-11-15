# Plan 053: Pruebas E2E con Playwright

## Estado

- **Estado:** HECHO el 2026-11-14. Job `e2e` en verde en la ejecución `43678072381` de GitHub Actions.
- **Prioridad:** P1
- **Esfuerzo:** L
- **Depende de:** 050
- **Origen:** REQ-50, REQ-51, REQ-53, REQ-54 y REQ-62; tarea C4 de `docs/reportes/verificacion_2026-11-14.md`
- **Planificado en:** commit `5dbd03d`, 2026-11-14

## Objetivo

Las gráficas, el diseño responsive y la actualización sin recarga solo tienen pruebas unitarias en jsdom. La tesis necesita evidencia en un navegador real con datos de la API.

## Decisiones

- **Backend real:** `uvicorn` con PostgreSQL. En local, la base desechable `predicta_e2e`; en CI, un job `e2e` con PostgreSQL 17 (decisión del autor).
- **Datos:** el XLSX de la tesis, cargado a través de la API con el mapeo propuesto. El usuario se confirma directamente en la base de prueba.

## Alcance

- `frontend/package.json`: `@playwright/test` como devDependency y el script `e2e`.
- `frontend/playwright.config.ts` y `frontend/e2e/*.spec.ts` (nuevos). `webServer` levanta `uvicorn` y `vite preview`.
- `frontend/e2e/global-setup.ts`: recrea y migra la base, crea el usuario y carga las ventas.
- Escenarios:
  - **REQ-50:** la gráfica de líneas de la proyección se dibuja con datos de `/analytics/forecast`.
  - **REQ-51:** la gráfica de barras de ingresos por categoría muestra las 5 categorías.
  - **REQ-53:** a 375 px y a 1440 px no hay *scroll* horizontal (`scrollWidth ≤ clientWidth`). Las capturas se guardan en `docs/evaluacion/capturas/`.
  - **REQ-54:** cambiar un filtro no dispara un `load` nuevo.
  - **REQ-62:** ningún escenario deja errores en la consola.
- `.github/workflows/ci.yml`: job `e2e`.
- `CLAUDE.md` y `AGENTS.md`: el comando nuevo.

## Pasos

1. Configurar Playwright y la base E2E.
   - **Verificar:** `npm run e2e` levanta los servidores y una prueba mínima pasa.
2. Escribir los escenarios.
   - **Verificar:** `npm run e2e` pasa en local, y `npm run lint` y `typecheck` pasan.
3. Agregar el job de CI.
   - **Verificar:** el job `e2e` pasa en GitHub Actions.
4. Cerrar las filas REQ-50..52 y REQ-53, REQ-62 de la §10.

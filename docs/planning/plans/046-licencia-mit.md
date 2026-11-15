# Plan 046: Licencia MIT

## Estado

- **Estado:** HECHO el 2026-11-14.
- **Prioridad:** P1
- **Esfuerzo:** S
- **Depende de:** —
- **Origen:** decisión del autor del 2026-11-14 (pendiente #15, REQ-09); tarea C7 de `docs/reportes/verificacion_2026-11-14.md`
- **Planificado en:** commit `5dbd03d`, 2026-11-14

## Objetivo

El repositorio no tiene licencia, así que el código queda con «todos los derechos reservados» y la tesis no puede presentarlo como código abierto (PE3).

## Alcance

- `LICENSE` (MIT, 2026, autor del proyecto) en la raíz.
- `frontend/package.json`: `"license": "MIT"`.
- `frontend/package-lock.json`: el campo `license` del paquete raíz, si npm lo refleja.

## Pasos

1. Agregar `LICENSE` y el campo `license`.
   - **Verificar:** `npx license-checker --production --excludePrivatePackages --summary` da `MIT: 46`; `npm run build` pasa.
   - **Nota:** sin `--excludePrivatePackages`, `license-checker` marca como `UNLICENSED` a todo paquete con `"private": true`, sin leer su campo `license` (`lib/index.js`). `private` se conserva para evitar una publicación accidental en npm.
2. Cerrar las filas REQ-09 de la §10 de `docs/checking/VERIFICACION_TESIS.md`.

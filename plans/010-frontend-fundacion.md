# Plan 010: Fundacion frontend

## Estado

- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** MED
- **Depende de:** tareas backend 001-009
- **Categoria:** frontend / arquitectura
- **Planificado en:** commit `96e38cc`, 2026-10-18

## Objetivo

Crear la base ejecutable de `frontend/` con React 19, TypeScript, Vite,
Tailwind CSS v4 y Chart.js. Vite es herramienta de build y servidor de
desarrollo; no es un framework alternativo a React.

## Stack obligatorio

- React 19 + TypeScript
- Vite
- Tailwind CSS v4 con tokens CSS en `@theme`
- Chart.js + `react-chartjs-2`
- Axios
- TanStack Query
- Zustand
- React Router
- React Hook Form + Zod
- Vitest + React Testing Library

## Pasos

1. Crear `package.json`, scripts npm y configuración Vite dentro de `frontend/`.
   - **Verificar:** `npm install` y `npm run build` terminan con código 0.
2. Crear `src/app`, `src/api`, `src/components`, `src/hooks`, `src/lib`,
   `src/pages`, `src/stores` y `src/types` con imports TypeScript estrictos.
   - **Verificar:** `npx tsc --noEmit` termina con código 0.
3. Crear cliente Axios con `VITE_API_URL`, timeout y serialización JSON.
   - **Verificar:** test confirma que URL base proviene de variable de entorno.
4. Crear `QueryClientProvider`, `BrowserRouter` y store Zustand vacío pero
   tipado para sesión.
   - **Verificar:** la aplicación carga en `npm run dev` sin errores de consola.
5. Crear tokens Tailwind v4 para tema oscuro tipo terminal: fondo grafito,
   superficie, borde, texto, ámbar, positivo y error.
   - **Verificar:** smoke test renderiza fondo, texto y foco visible.
6. Crear componentes base manuales: `Button`, `Input`, `Card`, `Badge`,
   `Alert`, `Spinner`, `EmptyState` y `Modal`.
   - **Verificar:** tests cubren variantes, disabled, keyboard focus y estados vacíos.
7. Configurar Vitest, jsdom, RTL y setup de matchers.
   - **Verificar:** `npm test -- --run` pasa con al menos un test de smoke.

## Contrato de entorno

- `VITE_API_URL=http://localhost:8000`
- No incluir secretos en variables `VITE_*`.
- Backend ya permite `http://localhost:5173` mediante `CORS_ORIGINS`.

## Criterios de terminado

- Frontend compila con TypeScript estricto.
- Tailwind v4 funciona sin `tailwind.config.js` innecesario.
- Cliente HTTP, router, Query y store tienen una única instancia.
- Test y build ejecutan desde `frontend/`.

## STOP

- Detenerse si Node.js soportado por el entorno no puede instalar React 19.
- Detenerse si el backend no responde en `/health` durante la prueba manual.
- No instalar una libreria UI adicional sin actualizar este plan.

## Mantenimiento

Toda nueva pagina debe reutilizar tokens y componentes base. No colocar URLs
del backend directamente en componentes de pagina.

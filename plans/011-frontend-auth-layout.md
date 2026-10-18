# Plan 011: Autenticacion y layout frontend

## Estado

- **Prioridad:** P1
- **Esfuerzo:** M
- **Riesgo:** MED
- **Depende de:** `plans/010-frontend-fundacion.md`
- **Categoria:** frontend / auth
- **Planificado en:** commit `96e38cc`, 2026-10-18

## Objetivo

Implementar registro, login, perfil, persistencia de sesion y navegacion
protegida contra el backend JWT existente.

## Contrato backend

- `POST /users/register`: JSON con `nombre_usuario`, `correo_electronico`,
  `password`; responde 201.
- `POST /users/login`: `application/x-www-form-urlencoded` con `username` y
  `password`; responde `access_token` y `token_type`.
- `GET /users/me`: devuelve perfil autenticado.
- `PUT /users/me`: actualiza nombre o correo.
- Token usa Bearer, claim `sub`, expiracion y algoritmo HS256 en backend.

## Pasos

1. Crear tipos `UserResponse`, `LoginResponse`, `RegisterPayload` y
   `UserUpdatePayload`.
   - **Verificar:** `npx tsc --noEmit` pasa sin `any` en auth.
2. Crear schemas Zod para registro, login y perfil. Replicar la regla backend:
   minimo 8 caracteres, mayuscula, minuscula y digito.
   - **Verificar:** tests cubren password valido, debil, correo invalido y campos vacios.
3. Crear funciones Axios para registro, login, perfil y actualizacion.
   - **Verificar:** MSW o mocks de Axios confirman metodo, ruta, body y content type.
4. Crear `authStore` Zustand con token, usuario, `isAuthenticated`,
   `setSession`, `clearSession` e hidratacion desde `localStorage`.
   - **Verificar:** test confirma persistencia, restauracion y logout sin datos residuales.
5. Agregar interceptor Axios para adjuntar `Authorization: Bearer <token>`.
   En respuesta 401, limpiar store y navegar a `/login`.
   - **Verificar:** test confirma header en peticiones autenticadas y limpieza ante 401.
6. Crear `LoginPage`, `RegisterPage` y `ProfilePage` con React Hook Form.
   - **Verificar:** RTL cubre submit exitoso, errores 400/401/422 y estados loading.
7. Crear `AppShell`, sidebar responsive, navegación y `ProtectedRoute`.
   Rutas: `/login`, `/register`, `/dashboard`, `/upload`, `/predictions`,
   `/reports`, `/profile`.
   - **Verificar:** usuario anónimo va a `/login`; usuario autenticado accede al shell.
8. Mostrar expiracion de sesion como mensaje accionable; no intentar renovar
   token porque backend no expone refresh token.
   - **Verificar:** 401 redirige sin loop infinito.

## Diseño

UI en español. Numeros monetarios usan `IBM Plex Mono` y `tabular-nums`.
Estados de error explican accion concreta. Foco visible por teclado. Respeta
`prefers-reduced-motion`.

## Criterios de terminado

- Login, registro, perfil y logout funcionan contra API real.
- Token nunca aparece en URL ni logs de interfaz.
- Rutas privadas no muestran contenido antes de resolver hidratacion.
- Mobile: sidebar colapsa y formularios conservan accesibilidad.

## STOP

- Detenerse si backend cambia formato de login o respuesta JWT.
- No implementar cookies httpOnly: requiere cambio backend fuera de alcance.
- No crear refresh token en frontend.

## Mantenimiento

Todo endpoint protegido debe usar cliente Axios compartido. No leer
`localStorage` directamente dentro de paginas.

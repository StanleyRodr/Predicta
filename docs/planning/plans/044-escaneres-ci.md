# Plan 044: Escáneres de seguridad en CI

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** S
- **Riesgo:** LOW (solo agrega jobs y hooks; puede bloquear merges si una dependencia tiene una CVE nueva)
- **Depende de:** `docs/planning/plans/039-auditoria-seguridad.md` (S-16; las herramientas ya se ejecutaron a mano)
- **Categoría:** CI
- **Origen:** pedido del usuario y entrevista de diseño del 2026-11-11
- **Planificado en:** commit `faa97af`, 2026-11-11

## Objetivo

La tarea 039 ejecuta los escáneres una sola vez, a mano. Sin CI, una
dependencia con una vulnerabilidad nueva o un secreto en un commit pasan sin
aviso. Esta tarea los ejecuta en cada push.

## Decisiones

Tomadas por el usuario el 2026-11-11.

- **Herramientas en CI:**
  - reglas `S` de ruff (bandit), activadas en la 039: ya corren con `ruff check app/` en el job `backend`;
  - `pip-audit` en el job `backend`;
  - `npm audit` en el job `frontend`;
  - `gitleaks` en un job nuevo `secrets`, sobre todo el historial.
- **Umbral:** el job falla con una vulnerabilidad de severidad alta o crítica.
  - `npm audit --omit=dev --audit-level=high`: solo dependencias de producción, porque las de desarrollo no llegan al build.
  - `pip-audit -r requirements.txt`: no filtra por severidad. Una excepción se declara con `--ignore-vuln <ID>` y un comentario con el motivo y la fecha de revisión.
- **ZAP** no entra en CI: se ejecuta a mano antes de cada despliegue importante, como en la 039.
- **`gitleaks` también en pre-commit**, para frenar el secreto antes del commit.

## Alcance

- `.github/workflows/ci.yml`:
  - `backend`: paso `pip install pip-audit` y `pip-audit -r requirements.txt`;
  - `frontend`: paso `npm audit --omit=dev --audit-level=high`;
  - job nuevo `secrets` con `actions/checkout` (`fetch-depth: 0`) y `gitleaks/gitleaks-action` con versión fijada.
- `.gitleaks.toml` (nuevo, solo si la 039 encontró falsos positivos): reglas `allowlist` con el motivo de cada una.
- `.pre-commit-config.yaml`: hook de `gitleaks` con versión fijada.
- `backend/requirements-dev.txt`: `pip-audit` con versión fijada.
- `CLAUDE.md` y `AGENTS.md`: los escáneres en "Before submitting" y en la descripción de CI.

## Pasos

1. `pip-audit` en el job `backend`.
   - **Verificar:** `cd backend; pip-audit -r requirements.txt` termina con código 0 en local.
2. `npm audit` en el job `frontend`.
   - **Verificar:** `cd frontend; npm audit --omit=dev --audit-level=high` termina con código 0 en local.
3. Job `secrets` y hook de pre-commit.
   - **Verificar:** `pre-commit run gitleaks --all-files` termina con código 0. Un archivo de prueba con un secreto falso, sin commitear, hace fallar el hook; luego se borra.
4. CI en la branch.
   - **Verificar:** los jobs `backend`, `frontend` y `secrets` pasan en GitHub Actions al hacer push de `feat/039-seguridad`.

## Criterios de terminado

- Cada push ejecuta ruff `S`, `pip-audit`, `npm audit` y `gitleaks`.
- Toda excepción a un escáner tiene un motivo escrito en el archivo donde se declara.

## Fuera de alcance

- Dependabot o Renovate para actualizar dependencias solas.
- ZAP en CI.
- La actualización general de dependencias (sigue pospuesta en `docs/planning/TASKS.md`).

## STOP

- Una vulnerabilidad alta o crítica sin versión corregida: reportarla al usuario antes de ignorarla.
- `gitleaks-action` exige una licencia para el repositorio. En ese caso, usar el binario de `gitleaks` directamente en el job.

## Mantenimiento

- Las excepciones (`--ignore-vuln`, `allowlist`) se revisan en cada auditoría nueva.

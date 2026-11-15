# Concurrencia: una carga larga frente a otras solicitudes

Generado por `backend/scripts/measure_concurrency.py` el 2026-11-15 04:32 UTC.

**Entorno:** `uvicorn` con 1 worker (como en producción), PostgreSQL local en la base
desechable `predicta_bench`, cliente y servidor en la misma máquina (sin latencia de red).

**Prueba:** el usuario A sube el XLSX de la tesis (28,667 filas) mientras el usuario B
consulta `GET /analytics/stats` cada 0.4 s. Se compara con B consultando en reposo.

La carga de A tardó **12.5 s** (estado 200,
28,667 filas cargadas).

| Momento | n | p50 (ms) | p95 (ms) | Máximo (ms) | Respuestas distintas de 200 |
|---|---|---|---|---|---|
| En reposo | 30 | 6.2 | 9.1 | 9.5 | 0 |
| Durante la carga de A | 17 | 365.8 | 517.0 | 536.5 | 0 |

Durante la carga, la mediana de B fue 59.3 veces la de reposo. Ninguna solicitud de B esperó a que terminara la carga (la más lenta tardó 0.54 s de 12.5 s): el servidor siguió atendiendo a B mientras procesaba el archivo de A en un hilo de trabajo. La latencia sí sube, porque B comparte la CPU (y el GIL de Python) con el ETL.

`SIN UMBRAL`: la tesis no fija una latencia máxima; los valores se reportan sin aprobar
ni reprobar. Una ejecución en otra máquina dará otros números.

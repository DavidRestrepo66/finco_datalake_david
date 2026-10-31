# Plan de pruebas (T-06)

Las pruebas se ejecutan en local antes de cada PR con `python verificar.py` (ruff, pytest y `dbt build`); no hay integración continua (R-01).

## Casos de prueba

| ID | Caso | HU | Tipo | Cómo se ejecuta | Estado (30 oct) |
|---|---|---|---|---|---|
| CP-ING-01 | El extractor TRM recorre todas las páginas de Socrata | HU-03 | Unitaria | `pytest ingesta` | Automatizada |
| CP-ING-02 | El extractor reintenta 3 veces y falla con código distinto de 0 | HU-06 | Unitaria | `pytest ingesta` | Automatizada |
| CP-ING-03 | Cada registro bronze tiene metadatos de origen y carga | HU-03, 04, 05 | Integración | `pytest ingesta` (requiere PostgreSQL) | Automatizada |
| CP-SIL-01 | TRM en silver única por fecha | HU-07 | Calidad dbt | `dbt build` (test `unique`) | Automatizada |
| CP-SIL-02 | Vigencias de tasa sin solapamiento | HU-08 | Calidad dbt | `dbt build` (unit tests y `unique` en `silver_tasa_intervencion`) | Automatizada |
| CP-GLD-01 | Integridad referencial hechos → dim_fecha | HU-10 | Calidad dbt | `dbt build` (test `relationships`) | Automatizada |
| CP-GLD-02 | Mart mensual con una fila por mes desde 2020 | HU-09 | Calidad dbt | `dbt build` (`unique` y `not_null` sobre `anio_mes`) | Automatizada, incluido `dbt/tests/mart_mensual_empieza_en_2020_01.sql` |
| CP-E2E-01 | Pipeline completo termina con código 0 | HU-12 | Integración | `docker compose run --rm pipeline` | Ejecutada en Docker: código 0, `PASS=42 ERROR=0`, 12.0 s |
| CP-DASH-01 | Tablero muestra 3 visualizaciones con datos | HU-13 | Aceptación | Manual en Metabase | Verificada por API: 3 tarjetas, 81 filas cada una, filtro `Fechas` |
| CP-INST-01 | Instalación en máquina limpia siguiendo el README | HU-02 | Instalación | Manual | Ejecutada el 30 oct en clon limpio: pasa (`docs/evidencia/ejecucion-2026-10-30-instalacion-limpia.md`) |
| CP-APP-01 | La app descarga el CSV filtrado y avisa si no hay datos | HU-14 | Unitaria | `pytest app` | Automatizada; la interfaz responde en `:8501` |

CP-APP-01 es un caso agregado en este plan; no estaba en el README.

## Criterios de aceptación de la entrega

- `python verificar.py` termina con "Todo en orden".
- Todos los casos CP-* pasan o quedan registrados con su evidencia en T-07.

## Evidencia (T-07)

Cada ejecución pega en el PR la salida de `verificar.py`. Los casos manuales guardan captura o registro en `docs/evidencia/`.

Corridas registradas:

- `docs/evidencia/ejecucion-2026-10-29.md` — por rama, antes del merge.
- `docs/evidencia/ejecucion-2026-10-30-instalacion-limpia.md` — instalación en clon limpio (HU-02).
- `docs/evidencia/ejecucion-2026-10-30.md` — sobre `main`: pipeline en Docker, datos cargados, tablero por API y app.

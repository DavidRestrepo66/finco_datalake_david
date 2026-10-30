# Matriz de trazabilidad v2 (T-05, T-09)

Estado al 30 oct 2026, sobre `main` (commit `3b31b45`). "Hecho" significa implementado,
mergeado y verificado en `main`; "Pendiente" es lo que falta para la entrega final.
La evidencia de las corridas está en `docs/evidencia/ejecucion-2026-10-30.md`.

| Requisito | HU | Casos de uso | Caso de prueba | Implementación | Estado |
|---|---|---|---|---|---|
| RF-01 | HU-03, 04, 05, 06 | CU-03 | CP-ING-01, 02 | `ingesta/`, `data/fuentes/` | Hecho (PR #3, #8, #10) |
| RF-01b | HU-08, 09 | CU-04 | CP-SIL-02, CP-GLD-02 | `dbt/models/silver/`, `dbt/models/gold/` | Hecho (PR #14, #22) |
| RF-02 | HU-03, 04, 05 | CU-03 | CP-ING-03 | `ingesta/carga_bronze.py`, `data/bronze/` | Hecho |
| RF-03 | HU-07, 08 | CU-04 | CP-SIL-01 | `dbt/models/silver/` | Hecho (PR #7, #14) |
| RF-04 | HU-09 | CU-04 | CP-GLD-02 | `dbt/models/gold/` | Hecho (PR #9, #22) |
| RF-05 | HU-07, 08, 10 | CU-04 | CP-SIL-01, CP-GLD-01 | tests en `*.yml` de dbt | Hecho |
| RF-06 | HU-11 | CU-07 | Aceptación de HU-11 | `dbt docs` | Hecho (PR #17) |
| RF-07 | HU-13 | CU-05 | CP-DASH-01 | Metabase | Hecho y verificado por API (PR #16, #18) |
| RF-08 | HU-12, 02 | CU-02, CU-08 | CP-E2E-01 | `pipeline.py`, `verificar.py` | HU-12 hecho y verificado; HU-02 pendiente |
| RF-09 | HU-14 | CU-06 | CP-APP-01 | `app/` | Hecho (PR #13, #19) |
| RNF-01 | HU-01, 02 | CU-01, CU-08 | CP-INST-01 | `docker-compose.yml`, `Dockerfile` | HU-01 hecho; HU-02 pendiente |
| RNF-02 | HU-12 | CU-02 | CP-E2E-01 | `pipeline.py` | Medido: 12.0 s (umbral < 5 min) |
| RNF-03 | Todas | — | `verificar.py` | ruff | Hecho |
| RNF-04 | Todas | — | Historial de Git | PRs enlazados a HU | Hecho |
| RNF-05 | HU-11 | CU-07 | Aceptación de HU-11 | `dbt docs` | Hecho (PR #17) |

## Lo que falta

- **HU-02 / CP-INST-01:** instalar y ejecutar en una máquina limpia siguiendo solo el README.
  Los pasos de instalación están ahora en la sección «Inicio rápido» del `README.md`.
- **T-09:** actas de sprint y retrospectiva (no se redactan con datos inventados).
- **CP-GLD-02:** falta un test que fije la fecha mínima `2020-01` del mart.

Todas las HU restantes (HU-01 y HU-03 a HU-14) están en `main`.

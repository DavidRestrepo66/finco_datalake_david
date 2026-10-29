# Matriz de trazabilidad v1 (T-05)

Estado al 29 oct 2026. "Hecho" significa implementado y verificado en su rama; "En PR" significa que aún no está en `main`.

| Requisito | HU | Casos de uso | Caso de prueba | Implementación | Estado |
|---|---|---|---|---|---|
| RF-01 | HU-03, 04, 05, 06 | CU-03 | CP-ING-01, 02 | `ingesta/`, `data/fuentes/` | HU-03 hecho; HU-04/05 en PR #10; HU-06 en PR #8 |
| RF-01b | HU-08, 09 | CU-04 | CP-SIL-02, CP-GLD-02 | `dbt/models/silver/`, `dbt/models/gold/` | En rama `feature/HU-09b-mart-mensual`, sin PR |
| RF-02 | HU-03, 04, 05 | CU-03 | CP-ING-03 | `ingesta/carga_bronze.py`, `data/bronze/` | Hecho |
| RF-03 | HU-07, 08 | CU-04 | CP-SIL-01 | `dbt/models/silver/` | HU-07 en PR #7; HU-08 en rama sin PR |
| RF-04 | HU-09 | CU-04 | CP-GLD-02 | `dbt/models/gold/` | HU-09a en PR #9; hecho mensual y mart en rama sin PR |
| RF-05 | HU-07, 08, 10 | CU-04 | CP-SIL-01, CP-GLD-01 | tests en `*.yml` de dbt | En PR o rama |
| RF-06 | HU-11 | CU-07 | Aceptación de HU-11 | `dbt docs` | Pendiente |
| RF-07 | HU-13 | CU-05 | CP-DASH-01 | Metabase | Pendiente |
| RF-08 | HU-12, 02 | CU-02, CU-08 | CP-E2E-01 | `pipeline.py`, `verificar.py` | HU-12 en PR #12; HU-02 pendiente |
| RF-09 | HU-14 | CU-06 | CP-APP-01 | `app/` | En PR #13 |
| RNF-01 | HU-01, 02 | CU-01, CU-08 | CP-INST-01 | `docker-compose.yml`, `Dockerfile` | HU-01 hecho; HU-02 pendiente |
| RNF-02 | HU-12 | CU-02 | CP-E2E-01 | `pipeline.py` | Sin medir |
| RNF-03 | Todas | — | `verificar.py` | ruff | Hecho |
| RNF-04 | Todas | — | Historial de Git | PRs enlazados a HU | Hecho |
| RNF-05 | HU-11 | CU-07 | Aceptación de HU-11 | `dbt docs` | Pendiente |

Los números de PR son los de GitHub al 29 oct (#7, #8, #9, #10, #12 y #13). La rama del mart aún no tiene PR.

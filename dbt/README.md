# dbt: capas silver y gold

Lee `bronze.*` de PostgreSQL y construye `silver` (y luego `gold`). Las credenciales vienen del
entorno (`.env`), no de `profiles.yml`.

```bash
python -m venv .venv && .venv/bin/pip install -r dbt/requirements.txt
set -a; . ./.env; set +a
cd dbt && ../.venv/bin/dbt build --profiles-dir .
```

`dbt build` corre los modelos, las pruebas `unique`/`not_null` y las pruebas unitarias.

| Modelo | Tabla | Regla |
|---|---|---|
| `silver_trm` | `silver.trm` | Una fila por día calendario. Cada vigencia de bronze se expande a sus días; si un día está en dos lotes gana el más reciente (HU-07). |
| `silver_ipc` | `silver.ipc` | IPC mensual limpio y tipado desde el CSV del Banco de la República (HU-08). |
| `silver_tasa_intervencion` | `silver.tasa_intervencion` | Tasa de política por vigencia, sin solapamientos (HU-08). |
| `silver_usura` | `silver.usura` | Tasa de usura de consumo (Superfinanciera vía Socrata), por vigencia (HU-15). |
| `silver_cdt` | `silver.cdt` | Captaciones de CDT a 90 días (Superfinanciera vía Socrata), con tasa y monto (HU-16). |
| `silver_brent` | `silver.brent` | Precio diario del Brent (FRED) limpio y tipado (HU-15). |
| `silver_fed` | `silver.fed` | Tasa efectiva de la Fed (FRED) limpia y tipada (HU-15). |
| `dim_fecha` | `gold.dim_fecha` | Un día calendario por fila, desde `fecha_inicio_dim` (2019-01-01) hasta el último día con TRM (HU-09). |
| `fact_trm_diaria` | `gold.fact_trm_diaria` | Hecho diario de la TRM. `relationships` contra `dim_fecha`: falla e identifica fechas huérfanas (HU-10). |
| `fact_indicadores_mensual` | `gold.fact_indicadores_mensual` | Hecho mensual: IPC, inflación anual, tasa vigente, usura, Brent promedio, Fed funds y CDT a 90 días ponderado por monto. |
| `mart_mensual` | `gold.mart_mensual` | Una fila por mes: TRM promedio + todos los indicadores de `fact_indicadores_mensual`. |

## Linaje de datos (HU-11)

```sh
cd dbt
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .      # http://localhost:8080
```

Abre el modelo `mart_mensual`: el grafo muestra el camino `bronze.*_raw` → silver → hechos de gold → mart,
y cada columna indica en su descripción de qué modelo y campo sale.

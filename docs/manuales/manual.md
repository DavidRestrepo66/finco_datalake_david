# Manual técnico y de usuario (T-08)

## Manual de usuario

### Requisitos
Solo Docker con Compose.

### Instalación y ejecución
```sh
cp .env.example .env
docker compose up -d                      # PostgreSQL (esquemas bronze, silver, gold) y Metabase
docker compose run --rm pipeline          # ingesta de TRM, IPC y tasa + dbt build + tablero
docker compose --profile app up app       # app web: http://localhost:8501
```

La TRM se carga de forma incremental: cada corrida pide a datos.gov.co solo desde la última vigencia ya cargada
(menos 7 días de margen para recoger correcciones). La primera corrida trae todo desde 2020. Para forzar la
carga completa: `python -m ingesta.carga_bronze trm --completo`.

### Qué se obtiene
- **Tablero (Metabase):** http://localhost:3000, tablero «Tablero macroeconómico» con filtro de fechas.
  Se crea automáticamente al final del pipeline (`metabase/tablero.py`, con `METABASE_ADMIN_EMAIL` y
  `METABASE_ADMIN_PASSWORD` de `.env`); si ya existe, no lo duplica.
- **App web (Streamlit):** http://localhost:8501 (`docker compose --profile app up -d app`). La barra lateral tiene la
  navegación numerada, el periodo global (atajos Último año / Desde 2020 / 2023 y Desde/Hasta por mes) y el
  selector de tema Claro/Oscuro. Cuatro páginas:
  - *01 Inicio:* presentación, datos de contexto (periodo cubierto y último dato salen de la base), indicadores del
    periodo y el flujo de los datos.
  - *02 Análisis:* KPI con variación frente al periodo anterior de igual longitud (la tasa real es la diferencia
    simple tasa − inflación), gráfico de la TRM (eje izquierdo) frente a inflación y tasa (eje derecho) con bandas de
    ciclos de subidas/recortes de la tasa, activables por serie, gráfico de tasa real y «Lectura del periodo» generada
    desde los datos.
  - *03 Datos:* elegir conjunto (mart mensual o TRM diaria), columnas visibles, vista previa de 12 filas y botón
    «Descargar CSV» con exactamente las columnas visibles y las filas del periodo.
  - *04 Calidad y linaje:* resultado de las pruebas dbt (filtrable por capa silver/gold), linaje de `mart_mensual`
    y enlace a Metabase (`METABASE_URL`, por defecto http://localhost:3000). Lee `run_results.json` y `manifest.json`
    de la carpeta `DBT_TARGET_DIR` (en Docker: `/app/dbt_target`, volumen `./dbt/target` de solo lectura en el servicio
    `app`; el servicio `pipeline` monta `./dbt/target` para dejar ahí los artefactos de dbt). Si faltan, la página
    explica cómo montarlos.
- **Linaje:** `cd dbt && dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .`

### Solución de problemas
- **La app no abre (`localhost:8501` no responde) y `docker compose logs app` muestra `File does not exist: app/ui.py`.**
  La imagen de Docker quedó desactualizada respecto al código (se construyó antes de que el entrypoint se
  renombrara a `ui.py`). Reconstruirla y volver a levantar la app:
  ```sh
  docker compose --profile app build app
  docker compose --profile app up -d app
  ```
  Conviene hacerlo después de cada `git pull` que cambie código en `app/`.

## Manual técnico

### Arquitectura
Ver `docs/diseno/arquitectura.md` (lakehouse híbrido: bronze en Parquet y PostgreSQL; silver y gold con dbt) y `docs/diseno/modelo-datos.md`.

### Estructura
| Ruta | Contenido |
|---|---|
| `ingesta/` | Extractor TRM y cargador de CSV a bronze |
| `data/fuentes/` | CSV de IPC y tasa del Banco de la República |
| `dbt/` | Modelos silver y gold, pruebas y linaje |
| `metabase/` | Script que crea el tablero por la API |
| `app/` | Aplicación Streamlit |
| `pipeline.py`, `verificar.py` | Pipeline de un comando y verificación local |

### Verificación local
`python verificar.py` corre ruff, pytest y `dbt build` (requiere `.env` exportado y PostgreSQL arriba).

### Limitaciones conocidas
- El tablero no tiene respaldo fuera de la base interna de Metabase: si se borra el volumen `pgdata`, hay que volver a correr el pipeline para recrearlo.
- Las instrucciones no se han probado en una máquina limpia (HU-02).

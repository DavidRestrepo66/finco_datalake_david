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
- **App web (Streamlit):** el rango de fechas se elige arriba y aplica a dos pestañas.
  - *Consulta y descarga:* elegir conjunto (TRM diaria o mart mensual), ver la vista previa y descargar el CSV.
    Si el rango no tiene datos, muestra un mensaje y no genera archivo.
  - *Análisis:* sobre el mart mensual del rango, muestra variación de la TRM, inflación promedio, tasa vigente y
    tasa real (tasa − inflación), gráficos de la TRM y de inflación frente a tasa, y una lectura en texto
    generada desde los datos (máximo/mínimo de la TRM, correlación TRM–inflación). La correlación no implica causalidad.
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

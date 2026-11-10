# App de consulta (HU-14)

`python -m streamlit run app/ui.py` (o `docker compose --profile app up app`).

El `python -m` es necesario: Streamlit agrega la carpeta del script al frente de `sys.path`, y sin la
raíz del proyecto en el path el paquete `app` no se resuelve.

Páginas (menú lateral, despachadas desde `app/paginas.py`):

- **01 Inicio** (`paginas.inicio`): presentación, periodo cubierto y último dato desde la base, indicadores del
  periodo y el flujo de los datos.
- **02 Análisis** (`app/analisis.py`): KPI con variación frente al periodo anterior, TRM frente a inflación y tasa
  con bandas de ciclos, tasa real (tasa − inflación), «Lectura del periodo», y las fuentes nuevas: TRM frente al
  Brent y tasa de intervención frente a usura de consumo y CDT a 90 días.
- **03 Datos** (`app/consulta.py`): elegir conjunto, columnas visibles, vista previa y descarga del CSV con
  exactamente las columnas visibles y las filas del periodo. Si el rango no tiene datos se muestra un mensaje y no
  se genera archivo.
- **04 Calidad y linaje** (`app/calidad.py`): resultado de las pruebas dbt (filtrable por capa), linaje de
  `mart_mensual` y enlace a Metabase. Lee `run_results.json` y `manifest.json` de `DBT_TARGET_DIR`.

Conjuntos disponibles en la página de datos:

- **TRM diaria** (`gold.fact_trm_diaria`), filtrada por `fecha`.
- **Mart mensual** (`gold.mart_mensual`: `anio_mes`, `trm_promedio`, `ipc`, `inflacion_anual`, `tasa_vigente`,
  `tasa_usura_consumo`, `brent_promedio`, `fed_funds`, `tasa_cdt_90`), filtrado por `anio_mes` (primer día de cada
  mes; un mes entra si su fecha está dentro de Desde–Hasta).

Módulos de apoyo: `graficos.py` (figuras Plotly), `estilos.py` (paleta institucional y componentes HTML),
`ui.py` (arranque, conexión y barra lateral).

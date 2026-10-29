# App de consulta (HU-14)

`streamlit run app/app.py` (o `docker compose up app`).

Conjuntos disponibles:

- **TRM diaria** (`gold.fact_trm_diaria`), filtrada por `fecha`.
- **Mart mensual** (`gold.mart_mensual`: `anio_mes`, `trm_promedio`, `ipc`, `inflacion_anual`, `tasa_vigente`),
  filtrado por `anio_mes` (primer día de cada mes; un mes entra si su fecha está dentro de Desde–Hasta).

Elige el conjunto y el rango de fechas, revisa la vista previa y descarga el CSV con exactamente esas filas.
Si el rango no tiene datos se muestra un mensaje y no se genera archivo.

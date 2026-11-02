"""App web Streamlit (HU-14): ver datos de gold, filtrarlos por fechas y descargarlos en CSV.

Conjuntos: TRM diaria (gold.fact_trm_diaria) y mart mensual (gold.mart_mensual: anio_mes, trm_promedio,
ipc, inflacion_anual, tasa_vigente). En el mart mensual el rango filtra por `anio_mes` (primer día de cada mes).
Un rango sin datos muestra un mensaje y no ofrece descarga.

Uso: python -m streamlit run app/ui.py   (o `docker compose --profile app up app`)

El archivo no se llama `app.py` a propósito: Streamlit pone la carpeta del script al
frente de `sys.path`, y un `app.py` dentro del paquete `app` haría que `from app import
consulta` resuelva al propio script en vez de al paquete.
"""

import datetime as dt
import os

import pandas
import psycopg
import streamlit as st

from app import analisis, consulta

ETIQUETAS = {"trm_diaria": "TRM diaria", "mart_mensual": "Mart mensual (TRM, IPC, inflación, tasa)"}


def conectar():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )


st.title("Finco · Datos y análisis")
desde = st.date_input("Desde", dt.date(2023, 1, 1))
hasta = st.date_input("Hasta", dt.date(2023, 12, 31))
tab_datos, tab_analisis = st.tabs(["Consulta y descarga", "Análisis"])

with tab_datos:
    conjunto = st.selectbox("Conjunto de datos", list(consulta.CONJUNTOS), format_func=ETIQUETAS.get)

    try:
        with conectar() as con:
            columnas, filas = consulta.consultar(con, conjunto, desde, hasta)
    except ValueError as error:
        st.error(str(error))
    else:
        contenido = consulta.a_csv(columnas, filas)
        if contenido is None:
            st.info("No hay datos en el rango elegido.")
        else:
            st.caption(f"Vista previa: {len(filas)} filas")
            st.dataframe([dict(zip(columnas, fila)) for fila in filas])
            st.download_button("Descargar CSV", contenido, file_name=f"{conjunto}_{desde}_{hasta}.csv", mime="text/csv")


def mostrar_analisis():
    try:
        with conectar() as con:
            columnas, filas = consulta.consultar(con, "mart_mensual", desde, hasta)
    except ValueError as error:
        st.error(str(error))
        return
    ind = analisis.indicadores([dict(zip(columnas, f)) for f in filas])
    if ind is None:
        st.info("No hay datos completos en el rango elegido.")
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Variación de la TRM", f"{ind['variacion_trm_pct']:+.1f} %")
    c2.metric("Inflación promedio", f"{ind['inflacion_promedio']:.1f} %")
    c3.metric("Tasa vigente", f"{ind['tasa_ultima']:.1f} %")
    c4.metric("Tasa real", f"{ind['tasa_real_ultima']:+.1f} pts")
    datos = pandas.DataFrame([dict(zip(columnas, f)) for f in filas]).set_index("anio_mes").astype(float)
    st.subheader("TRM promedio mensual")
    st.line_chart(datos["trm_promedio"])
    st.subheader("Inflación anual y tasa de intervención (%)")
    st.line_chart(datos[["inflacion_anual", "tasa_vigente"]])
    st.subheader("Lectura del periodo")
    for texto in analisis.conclusiones(ind):
        st.markdown(f"- {texto}")


with tab_analisis:
    mostrar_analisis()

"""App web Streamlit (HU-14): ver datos de gold, filtrarlos por fechas y descargarlos en CSV.

Uso: streamlit run app/app.py   (o `docker compose up app`)
"""

import datetime as dt
import os

import psycopg
import streamlit as st

from app import consulta

ETIQUETAS = {"trm_diaria": "TRM diaria"}


def conectar():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )


st.title("Finco · Consulta de datos")
conjunto = st.selectbox("Conjunto de datos", list(consulta.CONJUNTOS), format_func=ETIQUETAS.get)
desde = st.date_input("Desde", dt.date(2023, 1, 1))
hasta = st.date_input("Hasta", dt.date(2023, 12, 31))

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
        st.dataframe([dict(zip(columnas, fila)) for fila in filas])
        st.download_button("Descargar CSV", contenido, file_name=f"{conjunto}_{desde}_{hasta}.csv", mime="text/csv")

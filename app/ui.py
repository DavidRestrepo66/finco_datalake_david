"""App web Streamlit de Finco: inicio, análisis, datos y calidad/linaje sobre la capa gold.

Este archivo solo arma la barra lateral (marca, navegación, periodo global y tema), guarda el estado en
`st.session_state` y despacha a `app/paginas.py`. Conjuntos: TRM diaria (gold.fact_trm_diaria) y mart mensual
(gold.mart_mensual); la lógica vive en `app/consulta.py`, `app/analisis.py`, `app/graficos.py` y `app/calidad.py`.

Uso: python -m streamlit run app/ui.py   (o `docker compose --profile app up app`)
Variables: POSTGRES_*, METABASE_URL (default http://localhost:3000), DBT_TARGET_DIR (default dbt/target).

El archivo no se llama `app.py` a propósito: Streamlit pone la carpeta del script al
frente de `sys.path`, y un `app.py` dentro del paquete `app` haría que `from app import
consulta` resuelva al propio script en vez de al paquete.
"""

import datetime as dt
import os

import psycopg
import streamlit as st

from app import analisis, consulta, estilos, paginas

TEMAS_UI = ["Claro", "Oscuro"]
CACHE_SEGUNDOS = 300


def conectar():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )


@st.cache_data(ttl=CACHE_SEGUNDOS, show_spinner=False)
def cargar_conjunto(conjunto, desde, hasta):
    with conectar() as con:
        return consulta.consultar(con, conjunto, desde, hasta)


@st.cache_data(ttl=CACHE_SEGUNDOS, show_spinner=False)
def cargar_mart():
    columnas, filas = cargar_conjunto("mart_mensual", dt.date(1900, 1, 1), dt.date(2100, 12, 31))
    return [dict(zip(columnas, f)) for f in filas]


@st.cache_data(ttl=CACHE_SEGUNDOS, show_spinner=False)
def cargar_ultimo_dato():
    with conectar() as con:
        return con.execute("select max(fecha) from gold.fact_trm_diaria").fetchone()[0]


def _ajustar_desde():
    st.session_state["hasta"] = max(st.session_state["hasta"], st.session_state["desde"])


def _ajustar_hasta():
    st.session_state["desde"] = min(st.session_state["desde"], st.session_state["hasta"])


def _aplicar_atajo(rango):
    st.session_state["desde"], st.session_state["hasta"] = rango


def barra_lateral(meses):
    """Marca, navegación, periodo global y tema. Devuelve (página, desde, hasta, tema)."""
    atajos = analisis.atajos(meses)
    estado = st.session_state
    if estado.get("desde") not in meses or estado.get("hasta") not in meses:
        estado["desde"], estado["hasta"] = atajos["Último año"]
    nombres = list(paginas.PAGINAS)
    with st.sidebar:
        st.markdown('<div class="marca"><div class="marca-cuadro"></div><div class="marca-nombre">Finco</div></div>', unsafe_allow_html=True)
        pagina = st.radio(
            "Navegación", nombres, key="pagina", label_visibility="collapsed",
            format_func=lambda n: f"{nombres.index(n) + 1:02d}  {n}",
        )
        st.markdown('<div class="etiqueta-lateral acento">Periodo · todas las páginas</div>', unsafe_allow_html=True)
        columnas = st.columns(len(atajos))
        for col, (etiqueta, rango) in zip(columnas, atajos.items()):
            activo = (estado["desde"], estado["hasta"]) == rango
            col.button(etiqueta, key=f"atajo_{etiqueta}", on_click=_aplicar_atajo, args=(rango,), type="primary" if activo else "secondary", use_container_width=True)
        c1, c2 = st.columns(2)
        c1.selectbox("Desde", meses, key="desde", format_func=analisis.etiqueta_mes, on_change=_ajustar_desde)
        c2.selectbox("Hasta", meses, key="hasta", format_func=analisis.etiqueta_mes, on_change=_ajustar_hasta)
        n = sum(1 for m in meses if estado["desde"] <= m <= estado["hasta"])
        st.markdown(f'<div class="nota-lateral">{n} de {len(meses)} meses · datos de {estilos.e(analisis.etiqueta_mes(meses[0]))} a {estilos.e(analisis.etiqueta_mes(meses[-1]))}</div>', unsafe_allow_html=True)
        st.markdown('<div class="etiqueta-lateral">Tema</div>', unsafe_allow_html=True)
        tema = st.radio("Tema", TEMAS_UI, key="tema", horizontal=True, label_visibility="collapsed")
    return pagina, estado["desde"], estado["hasta"], tema.lower()


st.set_page_config(page_title="Finco", layout="wide")
try:
    mart = cargar_mart()
    ultimo_dato = cargar_ultimo_dato()
except psycopg.Error as error:
    st.error(f"No se pudo consultar la base de datos: {error}")
    st.stop()
if not mart:
    st.warning("gold.mart_mensual no tiene filas. Ejecuta el pipeline: docker compose run --rm pipeline")
    st.stop()

pagina, desde, hasta, tema = barra_lateral(sorted(f["anio_mes"] for f in mart))
st.markdown(estilos.css(tema), unsafe_allow_html=True)
contexto = paginas.Contexto(
    mart=mart,
    desde=desde,
    hasta=hasta,
    ultimo_dato=ultimo_dato,
    tema=tema,
    consultar=cargar_conjunto,
    metabase_url=os.getenv("METABASE_URL", "http://localhost:3000"),
    carpeta_dbt=os.getenv("DBT_TARGET_DIR", "dbt/target"),
)
paginas.PAGINAS[pagina](contexto)

"""Páginas de la app Streamlit: una función por página, todas reciben un `Contexto`.

El contexto reúne lo que decide la barra lateral (periodo y tema) y los datos ya cargados (con caché) en
`app/ui.py`. Todo texto que viene de la base, de los CSV o de las variables de entorno pasa por
`estilos` (html.escape) antes de llegar a `st.markdown(..., unsafe_allow_html=True)`.
"""

import calendar
import datetime as dt
import decimal
from collections.abc import Callable
from dataclasses import dataclass

import streamlit as st

from app import analisis, calidad, consulta, estilos, graficos

SERIES_UI = [
    ("trm", "TRM promedio", "eje izq."),
    ("inflacion", "Inflación anual", "eje der."),
    ("tasa", "Tasa de intervención", "eje der."),
]
CONJUNTOS_UI = {"mart_mensual": "Mart mensual", "trm_diaria": "TRM diaria"}
CAPAS = {"todas": "Todas", "silver": "Silver", "gold": "Gold"}
FLUJO = [
    ("01", "Fuentes", "TRM diaria de datos.gov.co (API Socrata); IPC y tasa de intervención en CSV del Banco de la República.", "bronze/"),
    ("02", "Pipeline", "Limpieza y deduplicación en silver; modelo estrella y mart_mensual en gold. dbt ejecuta las pruebas de calidad.", "docker compose run --rm pipeline"),
    ("03", "Tablero", "Metabase publica el Tablero macroeconómico sobre la capa gold.", None),
    ("04", "App", "Esta app: análisis interactivo, consulta y descarga, calidad y linaje.", "localhost:8501"),
]


@dataclass
class Contexto:
    mart: list  # todas las filas de gold.mart_mensual (dicts)
    desde: dt.date  # primer día del mes inicial
    hasta: dt.date  # primer día del mes final
    ultimo_dato: dt.date | None  # max(fecha) de gold.fact_trm_diaria
    tema: str  # «claro» u «oscuro»
    consultar: Callable  # (conjunto, desde, hasta) -> (columnas, filas), con caché
    metabase_url: str
    carpeta_dbt: str


def fin_de_mes(fecha):
    return fecha.replace(day=calendar.monthrange(fecha.year, fecha.month)[1])


def filas_del_periodo(ctx):
    return sorted((f for f in ctx.mart if ctx.desde <= f["anio_mes"] <= ctx.hasta), key=lambda f: f["anio_mes"])


def etiqueta_periodo(ctx):
    n = len(filas_del_periodo(ctx))
    return f"{analisis.etiqueta_mes(ctx.desde)} – {analisis.etiqueta_mes(ctx.hasta)} · {n} {'mes' if n == 1 else 'meses'}"


def _html(contenido):
    st.markdown(contenido, unsafe_allow_html=True)


def _formatear(valor):
    if isinstance(valor, (decimal.Decimal, float)):
        return analisis.numero(float(valor), 2)
    return str(valor)


def _resumen_calidad(ctx):
    """(resultados, manifest, filas, resumen) de los artefactos de dbt, o None si faltan o no se pueden leer."""
    cargado = calidad.cargar(ctx.carpeta_dbt)
    if cargado is None:
        return None
    resultados, manifest = cargado
    try:
        filas = calidad.pruebas(resultados, manifest)
    except (KeyError, TypeError, AttributeError):
        return None
    return resultados, manifest, filas, calidad.resumen(filas)


def inicio(ctx):
    _html(
        estilos.encabezado(
            "Lakehouse analítico · datos financieros públicos de Colombia",
            "TRM, inflación y tasa de intervención en un solo modelo",
            grande=True,
            intro=(
                "Finco descarga datos públicos de datos.gov.co y del Banco de la República, los limpia en capas "
                "bronze, silver y gold con dbt y los publica en un mart mensual listo para consultar, comparar "
                "y descargar."
            ),
        )
    )
    meses = sorted(f["anio_mes"] for f in ctx.mart)
    if meses:
        cubierto = (f"{meses[0].year} – {meses[-1].year}", f"mart_mensual: {analisis.etiqueta_mes(meses[0])} a {analisis.etiqueta_mes(meses[-1])}, {len(meses)} filas")
    else:
        cubierto = ("Sin datos", "mart_mensual está vacío")
    if ctx.ultimo_dato:
        ultimo = (
            f"{ctx.ultimo_dato.day} {analisis.MESES[ctx.ultimo_dato.month - 1]} {ctx.ultimo_dato.year}",
            "TRM diaria" + (f"; mensual hasta {analisis.etiqueta_mes(meses[-1])}" if meses else ""),
        )
    else:
        ultimo = ("Sin datos", "fact_trm_diaria está vacía")
    leido = _resumen_calidad(ctx)
    if leido:
        r = leido[3]
        pruebas = (
            f"{r['pass']} / {r['total']}",
            "Todas en PASS en la última ejecución" if r["fallidas"] == 0 else f"{r['fallidas']} fallidas o con aviso",
        )
    else:
        pruebas = ("Sin leer", "Falta montar dbt/target")
    _html(estilos.hechos([("Fuentes públicas", "3", "TRM · IPC e inflación · tasa de intervención"), ("Periodo cubierto", *cubierto), ("Último dato", *ultimo), ("Pruebas dbt", *pruebas)]))

    _html(estilos.titulo2("Indicadores principales", etiqueta_periodo(ctx)))
    items = analisis.kpis(ctx.mart, ctx.desde, ctx.hasta)
    if items is None:
        st.info("No hay meses completos en el periodo elegido.")
    else:
        _html(estilos.rejilla_kpi(items, con_delta=False))

    _html(estilos.titulo2("Cómo fluyen los datos"))
    sin_esquema = ctx.metabase_url.split("://", 1)[-1]
    _html(estilos.pasos([(n, t, c, cmd or sin_esquema) for n, t, c, cmd in FLUJO]))


def analisis_pagina(ctx):
    filas = filas_del_periodo(ctx)
    anterior = analisis.periodo_anterior(ctx.mart, ctx.desde, ctx.hasta)
    comparado = (
        f"Comparado con {analisis.etiqueta_mes(anterior[0])} – {analisis.etiqueta_mes(anterior[1])}"
        if anterior
        else "Sin periodo anterior completo para comparar"
    )
    _html(estilos.encabezado("02 · Análisis", "TRM frente a inflación y tasa", f"{etiqueta_periodo(ctx)} · {comparado}"))
    items = analisis.kpis(ctx.mart, ctx.desde, ctx.hasta)
    if items is None:
        st.info("No hay meses completos en el periodo elegido.")
        return
    _html(estilos.rejilla_kpi(items))

    columnas = st.columns(len(SERIES_UI) + 1)
    visibles = []
    for col, (clave, nombre, eje) in zip(columnas, SERIES_UI):
        if col.checkbox(f"{nombre} ({eje})", value=True, key=f"serie_{clave}"):
            visibles.append(clave)
    bandas_on = columnas[-1].checkbox("Marcar cambios de tasa", value=True, key="ver_bandas")
    bandas = analisis.bandas_de_tasa(ctx.mart)
    if visibles:
        fig = graficos.figura_principal(filas, bandas, tuple(visibles), bandas_on, ctx.tema)
        st.plotly_chart(fig, use_container_width=True, config=graficos.CONFIG, theme=None)
        _html(estilos.leyenda_bandas())
    else:
        st.info("Activa al menos una serie para ver el gráfico.")

    izq, der = st.columns(2, gap="large")
    with izq:
        _html(estilos.titulo2("Tasa real"))
        _html('<div class="subtitulo">Tasa de intervención descontada la inflación anual (diferencia simple)</div>')
        st.plotly_chart(graficos.figura_tasa_real(filas, bandas, bandas_on, ctx.tema), use_container_width=True, config=graficos.CONFIG, theme=None)
    with der:
        _html(estilos.titulo2("Lectura del periodo"))
        _html('<div class="subtitulo">Generada a partir de los datos filtrados</div>')
        _html(estilos.lectura(analisis.lectura(filas)))


def selector_columnas(columnas, clave):
    """Buscador de columnas: elegir una la agrega como etiqueta con ✕ debajo. Siempre queda al menos una."""
    if clave not in st.session_state:
        st.session_state[clave] = list(columnas)
    activas = [c for c in st.session_state[clave] if c in columnas]

    def agregar():
        elegida = st.session_state[clave + "_buscar"]
        if elegida and elegida not in st.session_state[clave]:
            st.session_state[clave] = st.session_state[clave] + [elegida]
        st.session_state[clave + "_buscar"] = None

    pendientes = [c for c in columnas if c not in activas]
    st.selectbox(
        "Columnas visibles",
        pendientes,
        index=None,
        placeholder="Buscar una columna para agregar…",
        key=clave + "_buscar",
        on_change=agregar,
        disabled=not pendientes,
    )
    with st.container(horizontal=True, gap="xxsmall"):
        for nombre in activas:
            if st.button(f"{nombre} ✕", key=f"{clave}_x_{nombre}", help=f"Quitar {nombre}", disabled=len(activas) == 1, width="content"):
                st.session_state[clave] = [c for c in activas if c != nombre]
                st.rerun()
    return activas


def datos(ctx):
    _html(estilos.encabezado("03 · Datos", "Consulta y descarga", etiqueta_periodo(ctx)))
    izq, der = st.columns(2, gap="large")
    conjunto = izq.radio("Conjunto", list(CONJUNTOS_UI), format_func=CONJUNTOS_UI.get, horizontal=True, key="conjunto")
    try:
        columnas, filas = ctx.consultar(conjunto, ctx.desde, fin_de_mes(ctx.hasta))
    except ValueError as error:
        st.error(str(error))
        return
    with der:
        visibles = selector_columnas(columnas, f"vis_{conjunto}")
    indices = [columnas.index(c) for c in visibles]
    filas_vis = [tuple(f[i] for i in indices) for f in filas]
    contenido = consulta.a_csv(visibles, filas_vis)
    if contenido is None:
        st.info("No hay datos en el periodo elegido.")
        return
    nombre = f"finco_{conjunto}_{ctx.desde:%Y-%m}_{ctx.hasta:%Y-%m}.csv"
    n = len(filas_vis)
    c1, c2 = st.columns([3, 1])
    with c1:
        _html(
            estilos.resumen(
                f"{analisis.numero(n, 0)} filas · {len(visibles)} {'columna' if len(visibles) == 1 else 'columnas'}",
                f"Vista previa de las primeras {min(12, n)} filas. El CSV incluye exactamente estas columnas y todas las filas del periodo.",
            )
        )
    with c2:
        st.write("")
        st.download_button("Descargar CSV", contenido, file_name=nombre, mime="text/csv", key="descarga")
    _html(estilos.tabla(visibles, [[_formatear(v) for v in fila] for fila in filas_vis[:12]]))
    _html(f'<div class="archivo">Archivo: {estilos.e(nombre)}</div>')


def _vacio_calidad():
    return (
        '<div class="vacio">'
        '<div class="h2">No se encontraron los artefactos de dbt</div>'
        "<p>La app busca <strong>run_results.json</strong> (resultado de las pruebas) y <strong>manifest.json</strong> "
        "(linaje por columna) en la carpeta indicada por DBT_TARGET_DIR. Monta la carpeta target del proyecto dbt "
        "como volumen de solo lectura en el servicio de la app:</p>"
        '<pre class="codigo">services:\n  app:\n    environment:\n      DBT_TARGET_DIR: /app/dbt_target\n'
        "    volumes:\n      - ./dbt/target:/app/dbt_target:ro</pre>"
        '<p class="pagina-detalle">Después: docker compose run --rm pipeline y docker compose up -d app. '
        "Esta página no muestra resultados de pruebas sin esos archivos.</p></div>"
    )


def calidad_pagina(ctx):
    leido = _resumen_calidad(ctx)
    if leido:
        generado = (leido[0].get("metadata") or {}).get("generated_at", "")
        detalle = f"Leído de {ctx.carpeta_dbt}/run_results.json y manifest.json" + (f" · ejecución del {generado[:16].replace('T', ' ')} UTC" if generado else "")
    else:
        detalle = "Artefactos de dbt no disponibles"
    _html(estilos.encabezado("04 · Calidad y linaje", "Pruebas dbt y origen de cada columna", detalle))

    if leido is None:
        _html(_vacio_calidad())
    else:
        _, manifest, filas, r = leido
        _html(
            estilos.rejilla_kpi(
                [
                    {"clave": "x", "etiqueta": "Pruebas ejecutadas", "valor_texto": str(r["total"])},
                    {"clave": "x", "etiqueta": "En PASS", "valor_texto": str(r["pass"])},
                    {"clave": "x", "etiqueta": "Fallidas o con aviso", "valor_texto": str(r["fallidas"])},
                    {"clave": "x", "etiqueta": "Modelos cubiertos", "valor_texto": str(r["modelos"])},
                ],
                con_delta=False,
            )
        )
        a, b = st.columns([1, 1])
        with a:
            _html(estilos.titulo2("Pruebas"))
        capa = b.radio("Capa", list(CAPAS), format_func=CAPAS.get, horizontal=True, key="capa", label_visibility="collapsed")
        mostradas = [f for f in filas if capa == "todas" or f["capa"] == capa]
        _html(estilos.tabla(["Modelo", "Capa", "Columna", "Prueba", "Estado"], [[f["modelo"], f["capa"], f["columna"], f["prueba"], f["estado"]] for f in mostradas], etiquetas={"Estado"}, alta=True))
        _html(estilos.titulo2("Linaje de mart_mensual"))
        try:
            _html(estilos.linaje(calidad.linaje(manifest, "mart_mensual")))
        except (KeyError, TypeError, AttributeError):
            st.info("El manifest de dbt no incluye el modelo mart_mensual.")

    c1, c2 = st.columns([3, 1])
    with c1:
        _html(estilos.resumen("Tablero macroeconómico en Metabase", f"{ctx.metabase_url} · configurable con la variable de entorno METABASE_URL").replace('class="resumen"', 'class="resumen metabase"'))
    with c2:
        st.write("")
        if ctx.metabase_url.startswith(("http://", "https://")):
            st.link_button("Abrir Metabase", ctx.metabase_url)


PAGINAS = {"Inicio": inicio, "Análisis": analisis_pagina, "Datos": datos, "Calidad y linaje": calidad_pagina}

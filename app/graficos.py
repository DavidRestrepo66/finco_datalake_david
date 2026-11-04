"""Figuras Plotly de la página Análisis (sin Streamlit).

Funciones puras: reciben filas del mart mensual (anio_mes, trm_promedio, inflacion_anual, tasa_vigente) y las
bandas de `analisis.bandas_de_tasa`, y devuelven un `go.Figure`. Los colores son hex fijos tomados del sistema
de diseño «Modernist» (Plotly no resuelve `var(--...)`), en variante clara y oscura. Esquinas rectas, fuente
Archivo, tooltip unificado y separadores es-CO (punto de miles, coma decimal).
"""

import datetime as dt

import plotly.graph_objects as go

FUENTE = "Archivo, system-ui, sans-serif"
CONFIG = {"displayModeBar": False, "displaylogo": False}

PALETAS = {
    "claro": {
        "fondo": "#f3f2f2",
        "texto": "#201e1d",
        "acento": "#ec3013",
        "divisor": "#9f9d9d",
        "neutro500": "#9b9797",
        "neutro700": "#605d5d",
        "banda_subida": "#fff2ef",
        "banda_recorte": "#eae7e7",
    },
    "oscuro": {
        "fondo": "#161514",
        "texto": "#eceaea",
        "acento": "#ff563c",
        "divisor": "#5b5958",
        "neutro500": "#8f8a8a",
        "neutro700": "#bab6b6",
        "banda_subida": "#3b1a13",
        "banda_recorte": "#2f2c2b",
    },
}

# Una entrada por serie: sumar otra serie es sumar una fila. `color` es la clave de la paleta.
SERIES = [
    {"clave": "trm", "columna": "trm_promedio", "nombre": "TRM promedio", "eje": "y", "color": "acento",
     "dash": "solid", "escalon": False, "ancho": 2.5, "plantilla": "$ %{y:,.2f}"},
    {"clave": "inflacion", "columna": "inflacion_anual", "nombre": "Inflación anual", "eje": "y2",
     "color": "texto", "dash": "solid", "escalon": False, "ancho": 2, "plantilla": "%{y:,.2f} %"},
    {"clave": "tasa", "columna": "tasa_vigente", "nombre": "Tasa de intervención", "eje": "y2",
     "color": "neutro500", "dash": "dash", "escalon": True, "ancho": 2, "plantilla": "%{y:,.2f} %"},
]
MEDIO_MES = dt.timedelta(days=15)


def _paleta(tema):
    if tema not in PALETAS:
        raise ValueError(f"tema desconocido: {tema}")
    return PALETAS[tema]


def _num(valor):
    return None if valor is None else float(valor)


def _ordenar(filas):
    return sorted(filas, key=lambda f: f["anio_mes"])


def _eje_x(p, fechas):
    largo = len(fechas) > 30
    eje = {
        "type": "date",
        "showgrid": False,
        "showline": True,
        "linecolor": p["texto"],
        "linewidth": 2,
        "ticks": "outside",
        "tickcolor": p["texto"],
        "tickfont": {"color": p["neutro700"], "size": 11},
        "tickformat": "%Y" if largo else "%m/%Y",
        "dtick": "M12" if largo else "M3",
        "hoverformat": "%m/%Y",
    }
    if fechas:
        eje["range"] = [fechas[0].isoformat(), fechas[-1].isoformat()]
    return eje


def _eje_y(p, titulo, rejilla):
    return {
        "title": {"text": titulo, "font": {"color": p["neutro700"], "size": 11}},
        "showgrid": rejilla,
        "gridcolor": p["divisor"],
        "gridwidth": 1,
        "zeroline": False,
        "showline": False,
        "tickfont": {"color": p["neutro700"], "size": 11},
        "tickformat": ",.0f",
    }


def _layout(p, altura):
    return {
        "height": altura,
        "margin": {"l": 72, "r": 64, "t": 16, "b": 40},
        "paper_bgcolor": p["fondo"],
        "plot_bgcolor": p["fondo"],
        "font": {"family": FUENTE, "color": p["texto"], "size": 12},
        "showlegend": False,
        "hovermode": "x unified",
        "hoverlabel": {
            "bgcolor": p["fondo"],
            "bordercolor": p["texto"],
            "font": {"family": FUENTE, "color": p["texto"], "size": 12},
        },
        "separators": ",.",
    }


def _bandas(fig, p, bandas, fechas):
    """Una banda por ciclo de la tasa (add_vrect), recortada al rango graficado."""
    if not fechas:
        return
    for b in bandas:
        x0 = max(b["desde"] - MEDIO_MES, fechas[0])
        x1 = min(b["hasta"] + MEDIO_MES, fechas[-1])
        if x1 <= x0:
            continue
        subida = b["direccion"] == "subida"
        etiquetar = len(fechas) <= 36 or (x1 - x0).days >= 90
        opciones = {}
        if etiquetar:
            opciones = {
                "annotation_text": "SUBIDAS" if subida else "RECORTES",
                "annotation_position": "top left",
                "annotation_font": {"size": 10, "color": p["neutro700"], "family": FUENTE},
            }
        fig.add_vrect(
            x0=x0.isoformat(), x1=x1.isoformat(), fillcolor=p["banda_subida" if subida else "banda_recorte"],
            opacity=1, layer="below", line_width=0, **opciones,
        )


def figura_principal(filas, bandas, series=("trm", "inflacion", "tasa"), mostrar_bandas=True, tema="claro"):
    """TRM (eje izquierdo, COP) frente a inflación y tasa (eje derecho, %), con bandas de ciclo de tasa."""
    p = _paleta(tema)
    filas = _ordenar(filas)
    fechas = [f["anio_mes"] for f in filas]
    fig = go.Figure(layout=_layout(p, 400))
    activas = [s for s in SERIES if s["clave"] in series]
    for s in activas:
        fig.add_trace(
            go.Scatter(
                x=fechas,
                y=[_num(f[s["columna"]]) for f in filas],
                name=s["nombre"],
                yaxis=s["eje"],
                mode="lines",
                line={
                    "color": p[s["color"]],
                    "width": s["ancho"],
                    "dash": s["dash"],
                    "shape": "hv" if s["escalon"] else "linear",
                },
                hovertemplate=s["plantilla"] + "<extra></extra>",
            )
        )
    hay_izq = any(s["eje"] == "y" for s in activas)
    hay_der = any(s["eje"] == "y2" for s in activas)
    fig.update_layout(
        xaxis=_eje_x(p, fechas),
        yaxis={**_eje_y(p, "COP", rejilla=hay_izq), "visible": hay_izq},
        yaxis2={
            **_eje_y(p, "%", rejilla=hay_der and not hay_izq),
            "overlaying": "y",
            "side": "right",
            "visible": hay_der,
            "rangemode": "tozero",
            "tickformat": ",.0f",
        },
    )
    if mostrar_bandas:
        _bandas(fig, p, bandas, fechas)
    return fig


def figura_tasa_real(filas, bandas, mostrar_bandas=True, tema="claro"):
    """Tasa real (tasa vigente menos inflación anual, puntos porcentuales) con las mismas bandas."""
    p = _paleta(tema)
    filas = _ordenar(filas)
    fechas = [f["anio_mes"] for f in filas]
    reales = [
        None if f["tasa_vigente"] is None or f["inflacion_anual"] is None
        else float(f["tasa_vigente"]) - float(f["inflacion_anual"])
        for f in filas
    ]
    fig = go.Figure(layout=_layout(p, 260))
    fig.add_trace(
        go.Scatter(
            x=fechas, y=reales, name="Tasa real", mode="lines",
            line={"color": p["texto"], "width": 2},
            hovertemplate="%{y:,.2f} %<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis=_eje_x(p, fechas),
        yaxis={
            **_eje_y(p, "%", rejilla=True), "zeroline": True, "zerolinecolor": p["texto"], "zerolinewidth": 1,
            "tickformat": ",.0f",
        },
    )
    if mostrar_bandas:
        _bandas(fig, p, bandas, fechas)
    return fig

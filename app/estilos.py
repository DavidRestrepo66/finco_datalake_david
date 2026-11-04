"""Estilos y bloques HTML de la app (sin Streamlit): sistema de diseño «Modernist».

`css(tema)` devuelve el `<style>` con los tokens del diseño claro u oscuro (radio 0, reglas de 2px, Archivo,
acento #ec3013). Los constructores de HTML (`encabezado`, `rejilla_kpi`, `tabla`, ...) escapan con
`html.escape` todo texto interpolado: el contenido de la base y de los CSV no es confiable.
"""

from html import escape

TEMAS = {
    "claro": {
        "bg": "#f3f2f2", "surface": "#eae9e9", "text": "#201e1d", "accent": "#ec3013",
        "accent_text": "#ae1800", "accent_100": "#fff2ef", "divider": "#9f9d9d",
        "n200": "#eae7e7", "n500": "#9b9797", "n700": "#605d5d", "n800": "#444141", "hover": "#dfdddd",
    },
    "oscuro": {
        "bg": "#161514", "surface": "#211f1e", "text": "#eceaea", "accent": "#ff563c",
        "accent_text": "#ff9a88", "accent_100": "#3b1a13", "divider": "#5b5958",
        "n200": "#2f2c2b", "n500": "#8f8a8a", "n700": "#bab6b6", "n800": "#d7d3d3", "hover": "#2a2827",
    },
}

PLANTILLA = """<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800&display=swap');
:root {
  --bg: %(bg)s; --surface: %(surface)s; --text: %(text)s; --accent: %(accent)s;
  --accent-text: %(accent_text)s; --accent-100: %(accent_100)s; --divider: %(divider)s;
  --n200: %(n200)s; --n500: %(n500)s; --n700: %(n700)s; --n800: %(n800)s; --hover: %(hover)s;
  --font: "Archivo", system-ui, sans-serif;
}
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"] {
  background: var(--bg) !important; color: var(--text) !important; font-family: var(--font) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
.stApp p, .stApp label, .stApp li, .stApp span, .stApp div, .stApp button, .stApp input, .stApp table {
  font-family: var(--font);
}
.stApp, .stApp p, .stApp label, .stApp li { color: var(--text); }
*, *::before, *::after { border-radius: 0 !important; }
.block-container { max-width: 1240px; padding: 32px clamp(16px, 4vw, 56px) 64px; }
a { color: var(--accent-text); text-underline-offset: 3px; }
a:hover { color: var(--accent); }
:focus-visible { outline: 2px solid var(--accent) !important; outline-offset: 2px; }
::selection { background: color-mix(in srgb, var(--accent) 30%%, transparent); }

/* barra lateral */
[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 2px solid var(--divider); }
[data-testid="stSidebar"] > div:first-child { padding-top: 8px; }
.marca { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
.marca-cuadro { width: 14px; height: 14px; background: var(--accent); }
.marca-nombre { font-weight: 800; font-size: 22px; letter-spacing: -0.01em; }
.etiqueta-lateral {
  font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; font-weight: 600;
  color: var(--n700); margin: 16px 0 4px; text-align: left;
}
.etiqueta-lateral.acento { color: var(--accent-text); }
.nota-lateral { font-size: 12px; color: var(--n700); }
[data-testid="stSidebar"] [role="radiogroup"] { gap: 0; border-top: 2px solid var(--divider); }
[data-testid="stSidebar"] [role="radiogroup"] label {
  width: 100%%; padding: 10px 8px; margin: 0; border-bottom: 1px solid var(--divider); font-weight: 600;
  cursor: pointer; display: flex; align-items: baseline;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: var(--hover); }
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: var(--text); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * { color: var(--bg) !important; }
[data-testid="stSidebar"] [role="radiogroup"][aria-label="Tema"] { border-top: 0; }
.stApp [role="radiogroup"][aria-label="Tema"] label { border: 1px solid var(--divider); }

/* controles */
.stButton > button, .stDownloadButton > button, .stLinkButton > a {
  border: 1px solid var(--divider); background: transparent; color: var(--text); font-weight: 600;
  justify-content: flex-start; text-align: left;
}
.stButton > button:hover, .stLinkButton > a:hover { background: var(--hover); color: var(--text); border-color: var(--divider); }
.stButton > button[kind="primary"], .stDownloadButton > button {
  background: var(--accent); color: var(--bg); border-color: var(--accent);
}
.stButton > button[kind="primary"] p, .stDownloadButton > button p { color: var(--bg) !important; }
.stDownloadButton > button:hover, .stButton > button[kind="primary"]:hover { background: var(--accent-text); border-color: var(--accent-text); }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="tag"] {
  background: var(--surface) !important; border-color: var(--divider) !important; color: var(--text) !important;
}
[data-baseweb="select"] *, [data-baseweb="tag"] * { color: var(--text) !important; }
[data-baseweb="tag"] { background: var(--text) !important; }
[data-baseweb="tag"] * { color: var(--bg) !important; }
[data-baseweb="popover"] *, [data-baseweb="menu"] { background: var(--bg) !important; color: var(--text) !important; }
[data-testid="stCheckbox"] label span { color: var(--text) !important; }
[data-testid="stAlert"] { background: var(--surface); border: 1px solid var(--divider); color: var(--text); }
[data-testid="stPlotlyChart"] { border-top: 2px solid var(--text); padding-top: 8px; }

/* contenido */
.pagina-cab {
  display: flex; flex-direction: column; gap: 8px; padding-bottom: 16px;
  border-bottom: 2px solid var(--divider); margin-bottom: 24px;
}
.kicker { font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent-text); font-weight: 600; }
.pagina-h1 {
  margin: 0; font-weight: 800; font-size: 36px; line-height: 1.05; letter-spacing: -0.015em; color: var(--text);
}
.pagina-h1.grande { font-size: clamp(34px, 4.6vw, 56px); line-height: 1.02; max-width: 16ch; }
.pagina-detalle { font-size: 14px; color: var(--n700); }
.pagina-intro { margin: 0; max-width: 62ch; font-size: 17px; color: var(--n800); }
.h2 { margin: 24px 0 8px; font-weight: 800; font-size: 22px; color: var(--text); }
.h2 small { font-size: 13px; font-weight: 400; color: var(--n700); margin-left: 12px; }
.subtitulo { font-size: 13px; color: var(--n700); margin-bottom: 8px; }

.hechos { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); border-top: 2px solid var(--text); border-bottom: 2px solid var(--divider); margin-bottom: 8px; }
.hecho { padding: 16px 16px 16px 0; margin-right: 16px; border-right: 1px solid var(--divider); display: flex; flex-direction: column; gap: 4px; }
.hecho-etiqueta, .hecho-nota { font-size: 12px; color: var(--n700); }
.hecho-valor { font-weight: 800; font-size: 26px; line-height: 1.1; }

.kpi-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%%, 220px), 1fr));
  border-top: 2px solid var(--text); border-left: 1px solid var(--divider); margin-bottom: 8px;
}
.kpi { padding: 16px; display: flex; flex-direction: column; gap: 6px; border-right: 1px solid var(--divider); border-bottom: 2px solid var(--divider); }
.kpi-label { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--n800); }
.kpi-swatch { width: 12px; height: 3px; background: var(--n800); display: inline-block; }
.kpi-swatch.sw-trm { background: var(--accent); }
.kpi-swatch.sw-inflacion { background: var(--text); }
.kpi-swatch.sw-tasa { background: var(--n500); }
.kpi-value { font-weight: 800; font-size: 32px; line-height: 1; font-variant-numeric: tabular-nums; }
.kpi-nota { font-size: 12px; color: var(--n700); }
.kpi-delta { font-size: 13px; font-weight: 600; font-variant-numeric: tabular-nums; color: var(--n800); }
.kpi-delta.sube { color: var(--accent-text); }
.kpi-delta.sin { color: var(--n700); font-weight: 400; }

.flujo { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); border-top: 2px solid var(--text); }
.paso { padding: 16px 16px 16px 0; border-bottom: 1px solid var(--divider); display: flex; flex-direction: column; gap: 6px; }
.paso-num { font-size: 12px; font-weight: 600; color: var(--accent-text); }
.paso-titulo { font-weight: 700; font-size: 17px; }
.paso-texto { font-size: 13px; color: var(--n800); }
code, .codigo { font-size: 12px; background: var(--surface); padding: 4px 6px; align-self: flex-start; color: var(--text); }
pre.codigo { padding: 16px; border: 1px solid var(--divider); line-height: 1.6; overflow-x: auto; font-size: 13px; }

.leyenda { display: flex; gap: 16px; flex-wrap: wrap; font-size: 12px; color: var(--n700); margin-top: 8px; }
.leyenda-item { display: flex; align-items: center; gap: 6px; }
.muestra { width: 14px; height: 10px; border: 1px solid var(--divider); display: inline-block; }
.muestra.subida { background: var(--accent-100); }
.muestra.recorte { background: var(--n200); }
.lectura { border-top: 2px solid var(--text); padding-top: 12px; display: flex; flex-direction: column; gap: 12px; }
.lectura p { margin: 0; font-size: 16px; line-height: 1.55; max-width: 60ch; }

.resumen { border-top: 2px solid var(--text); padding-top: 12px; margin: 16px 0; }
.resumen-titulo { font-weight: 700; font-size: 17px; }
.resumen-nota { font-size: 13px; color: var(--n700); }
.archivo { font-size: 12px; color: var(--n700); margin-top: 8px; }

.tabla-caja { overflow-x: auto; border-top: 2px solid var(--text); }
.tabla-caja.alta { max-height: 440px; overflow-y: auto; }
.tabla { width: 100%%; border-collapse: collapse; font-size: 14px; font-variant-numeric: tabular-nums; }
.tabla th {
  text-align: left; font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--n700);
  padding: 8px; border-bottom: 2px solid var(--divider); position: sticky; top: 0; background: var(--bg);
}
.tabla td { padding: 8px; border-bottom: 1px solid var(--divider); text-align: left; }
.tabla tbody tr:hover { background: var(--hover); }
.tag { display: inline-block; font-size: 11px; font-weight: 700; letter-spacing: 0.02em; padding: 3px 10px; background: var(--n200); color: var(--text); }
.tag.malo { background: var(--accent); color: var(--bg); }

.linaje-fila { display: grid; grid-template-columns: minmax(150px, 200px) minmax(0, 1fr); gap: 16px; padding: 12px 0; border-bottom: 1px solid var(--divider); }
.linaje-col { font-weight: 700; }
.cadena { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; font-size: 13px; }
.nodo { padding: 3px 8px; background: var(--surface); border: 1px solid var(--divider); }
.flecha { color: var(--accent-text); font-weight: 700; }
.vacio { border-top: 2px solid var(--accent); padding-top: 16px; max-width: 760px; display: flex; flex-direction: column; gap: 12px; }
.vacio p { margin: 0; }
.vacio .h2 { margin: 0; }
.metabase { border-top: 2px solid var(--text); padding-top: 16px; margin-top: 32px; }
</style>"""


def css(tema="claro"):
    """El <style> completo de la app para el tema «claro» u «oscuro»."""
    if tema not in TEMAS:
        raise ValueError(f"tema desconocido: {tema}")
    return PLANTILLA % TEMAS[tema]


def e(texto):
    """Texto escapado para interpolar en HTML (también comillas)."""
    return escape(str(texto), quote=True)


def encabezado(kicker, titulo, detalle=None, grande=False, intro=None):
    clase = "pagina-h1 grande" if grande else "pagina-h1"
    partes = [f'<div class="kicker">{e(kicker)}</div>', f'<h1 class="{clase}">{e(titulo)}</h1>']
    if intro:
        partes.append(f'<p class="pagina-intro">{e(intro)}</p>')
    if detalle:
        partes.append(f'<div class="pagina-detalle">{e(detalle)}</div>')
    return f'<header class="pagina-cab">{"".join(partes)}</header>'


def titulo2(texto, nota=None):
    extra = f"<small>{e(nota)}</small>" if nota else ""
    return f'<div class="h2">{e(texto)}{extra}</div>'


def hechos(items):
    """Rejilla de datos de contexto: [(etiqueta, valor, nota)]."""
    celdas = "".join(
        f'<div class="hecho"><div class="hecho-etiqueta">{e(et)}</div>'
        f'<div class="hecho-valor">{e(v)}</div><div class="hecho-nota">{e(n)}</div></div>'
        for et, v, n in items
    )
    return f'<div class="hechos">{celdas}</div>'


def rejilla_kpi(items, con_delta=True):
    """Rejilla de KPI con bordes. Cada item: clave, etiqueta, valor_texto, nota y (opcional) delta y delta_texto."""
    celdas = []
    for k in items:
        clave = "".join(c for c in str(k.get("clave", "")) if c.isalnum())
        delta = ""
        if con_delta and "delta_texto" in k:
            d = k.get("delta")
            clase = "kpi-delta sin" if d is None else "kpi-delta sube" if d > 0 else "kpi-delta"
            delta = f'<div class="{clase}">{e(k["delta_texto"])}</div>'
        nota = f'<div class="kpi-nota">{e(k["nota"])}</div>' if k.get("nota") and not delta else ""
        celdas.append(
            f'<div class="kpi"><div class="kpi-label"><span class="kpi-swatch sw-{clave}"></span>{e(k["etiqueta"])}</div>'
            f'<div class="kpi-value">{e(k["valor_texto"])}</div>{nota}{delta}</div>'
        )
    return f'<div class="kpi-grid">{"".join(celdas)}</div>'


def pasos(items):
    """Pasos del flujo de datos: [(numero, titulo, cuerpo, comando)]."""
    celdas = "".join(
        f'<div class="paso"><div class="paso-num">{e(n)} →</div><div class="paso-titulo">{e(t)}</div>'
        f'<div class="paso-texto">{e(c)}</div><code>{e(cmd)}</code></div>'
        for n, t, c, cmd in items
    )
    return f'<div class="flujo">{celdas}</div>'


def tabla(columnas, filas, etiquetas=(), alta=False):
    """Tabla HTML; las columnas en `etiquetas` se muestran como etiqueta (p. ej. el estado de una prueba)."""
    cab = "".join(f"<th>{e(c)}</th>" for c in columnas)
    cuerpo = []
    for fila in filas:
        celdas = []
        for c, valor in zip(columnas, fila):
            if c in etiquetas:
                malo = " malo" if str(valor) != "PASS" else ""
                celdas.append(f'<td><span class="tag{malo}">{e(valor)}</span></td>')
            else:
                celdas.append(f"<td>{e(valor)}</td>")
        cuerpo.append(f'<tr>{"".join(celdas)}</tr>')
    caja = "tabla-caja alta" if alta else "tabla-caja"
    return f'<div class="{caja}"><table class="tabla"><thead><tr>{cab}</tr></thead><tbody>{"".join(cuerpo)}</tbody></table></div>'


def lectura(parrafos):
    return '<div class="lectura">' + "".join(f"<p>{e(p)}</p>" for p in parrafos) + "</div>"


def leyenda_bandas():
    return (
        '<div class="leyenda"><span class="leyenda-item"><span class="muestra subida"></span>Ciclo de subidas</span>'
        '<span class="leyenda-item"><span class="muestra recorte"></span>Ciclo de recortes</span>'
        "<span>Eje izquierdo: COP por dólar · eje derecho: porcentaje</span></div>"
    )


def resumen(titulo, nota):
    return f'<div class="resumen"><div class="resumen-titulo">{e(titulo)}</div><div class="resumen-nota">{e(nota)}</div></div>'


def linaje(filas):
    """Linaje por columna: [(columna, [nodos])]; cada cadena va de la columna a su fuente."""
    out = []
    for columna, cadena in filas:
        nodos = []
        for i, n in enumerate(cadena):
            flecha = '<span class="flecha">←</span>' if i < len(cadena) - 1 else ""
            nodos.append(f'<span class="nodo">{e(n)}</span>{flecha}')
        out.append(f'<div class="linaje-fila"><div class="linaje-col">{e(columna)}</div><div class="cadena">{"".join(nodos)}</div></div>')
    return f'<div class="linaje">{"".join(out)}</div>'

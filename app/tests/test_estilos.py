import pytest

from app import estilos


def test_css_claro_tiene_tokens_del_diseno_y_reglas_base():
    css = estilos.css("claro")
    assert css.startswith("<style>") and css.rstrip().endswith("</style>")
    for token in ("#f3f2f2", "#201e1d", "#ec3013", "Archivo", "border-radius: 0", "2px solid"):
        assert token in css
    for clase in (".kpi-grid", ".kicker", ".pagina-h1", ".tabla"):
        assert clase in css


def test_css_oscuro_cambia_los_tokens():
    css = estilos.css("oscuro")
    for token in ("#161514", "#eceaea", "#ff563c"):
        assert token in css
    assert "#f3f2f2" not in css


def test_css_tema_desconocido_es_error():
    with pytest.raises(ValueError):
        estilos.css("sepia")


def test_encabezado_escapa_el_texto():
    html = estilos.encabezado("<b>k</b>", "T & <i>", "detalle <x>")
    assert "<b>" not in html and "&lt;b&gt;" in html and "&amp;" in html and "&lt;x&gt;" in html
    assert 'class="kicker"' in html and "<h1" in html


def test_rejilla_kpi_escapa_y_marca_el_delta():
    items = [
        {
            "clave": "trm",
            "etiqueta": "TRM <script>",
            "valor_texto": "+1,0 %",
            "nota": "n & m",
            "delta": 0.5,
            "delta_texto": "▲ +0,50 pp",
        }
    ]
    html = estilos.rejilla_kpi(items)
    assert 'class="kpi-grid"' in html
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "kpi-delta" in html
    solo_nota = estilos.rejilla_kpi(items, con_delta=False)
    assert "n &amp; m" in solo_nota and "kpi-delta" not in solo_nota


def test_tabla_escapa_celdas_y_encabezados():
    html = estilos.tabla(["a<b"], [['<img src=x onerror=alert(1)>']])
    assert "<img" not in html and "&lt;img" in html and "a&lt;b" in html
    assert 'class="tabla"' in html


def test_tabla_permite_estado_como_etiqueta_pero_siempre_escapada():
    html = estilos.tabla(["Estado"], [["PASS"]], etiquetas={"Estado"})
    assert 'class="tag' in html and ">PASS<" in html

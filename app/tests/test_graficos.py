import datetime as dt

import pytest

pytest.importorskip("plotly")

from app import analisis, graficos


def filas(n=24):
    out = []
    for i in range(n):
        out.append(
            {
                "anio_mes": dt.date(2023 + i // 12, i % 12 + 1, 1),
                "trm_promedio": 4000.0 + 10 * i,
                "ipc": 100.0 + i,
                "inflacion_anual": 8.0 - 0.1 * i,
                "tasa_vigente": 10.0 if i < 6 else 11.0 if i < 12 else 10.5,
            }
        )
    return out


BANDAS = analisis.bandas_de_tasa(filas())


def test_principal_tiene_una_traza_por_serie_en_el_eje_correcto():
    fig = graficos.figura_principal(filas(), BANDAS)
    trazas = {t.name: t for t in fig.data}
    assert list(trazas) == ["TRM promedio", "Inflación anual", "Tasa de intervención"]
    assert trazas["TRM promedio"].yaxis == "y"
    assert trazas["Inflación anual"].yaxis == "y2"
    assert trazas["Tasa de intervención"].yaxis == "y2"
    assert fig.layout.yaxis2.overlaying == "y" and fig.layout.yaxis2.side == "right"
    assert fig.layout.yaxis.title.text == "COP" and fig.layout.yaxis2.title.text == "%"


def test_la_tasa_es_un_escalon_con_linea_discontinua():
    fig = graficos.figura_principal(filas(), BANDAS)
    tasa = fig.data[2]
    assert tasa.line.shape == "hv"
    assert tasa.line.dash == "dash"
    assert fig.data[0].line.shape == "linear" or fig.data[0].line.shape is None


def test_colores_fijos_por_serie_y_variante_clara_u_oscura():
    claro = graficos.figura_principal(filas(), BANDAS, tema="claro")
    oscuro = graficos.figura_principal(filas(), BANDAS, tema="oscuro")
    assert claro.data[0].line.color == "#007b99"
    assert oscuro.data[0].line.color == "#2bb5d6"
    assert claro.data[1].line.color == "#f39200" and oscuro.data[1].line.color == "#f39200"
    assert claro.layout.paper_bgcolor == "#ffffff" and oscuro.layout.paper_bgcolor == "#0f1a1d"
    for fig in (claro, oscuro):
        for t in fig.data:
            assert t.line.color.startswith("#")  # hex, nunca var(--...)
        assert "var(" not in fig.to_json()


def test_tooltip_unificado_fuente_archivo_y_separadores_es_co():
    fig = graficos.figura_principal(filas(), BANDAS)
    assert fig.layout.hovermode == "x unified"
    assert "Archivo" in fig.layout.font.family
    assert fig.layout.separators == ",."
    assert all(t.hovertemplate for t in fig.data)


def test_bandas_se_dibujan_con_vrect_y_etiqueta():
    fig = graficos.figura_principal(filas(), BANDAS)
    assert len(fig.layout.shapes) == len(BANDAS) > 0
    assert all(s.type == "rect" and s.xref == "x" and s.yref == "y domain" for s in fig.layout.shapes)
    assert all(s.layer == "below" for s in fig.layout.shapes)
    textos = {a.text for a in fig.layout.annotations}
    assert "SUBIDAS" in textos


def test_bandas_se_pueden_ocultar():
    fig = graficos.figura_principal(filas(), BANDAS, mostrar_bandas=False)
    assert len(fig.layout.shapes) == 0
    assert len(fig.layout.annotations) == 0


def test_bandas_fuera_del_rango_graficado_se_descartan_y_las_parciales_se_recortan():
    rango = filas()[12:]  # 2024-01 .. 2024-12
    fig = graficos.figura_principal(rango, BANDAS)
    inicio = dt.datetime(2023, 12, 17)
    for s in fig.layout.shapes:
        assert dt.datetime.fromisoformat(str(s.x0)) >= inicio


def test_series_ocultas_no_generan_trazas():
    fig = graficos.figura_principal(filas(), BANDAS, series=("trm",))
    assert [t.name for t in fig.data] == ["TRM promedio"]
    fig = graficos.figura_principal(filas(), BANDAS, series=("inflacion", "tasa"))
    assert fig.layout.yaxis.visible is False


def test_esquinas_rectas_sin_barra_de_herramientas():
    fig = graficos.figura_principal(filas(), BANDAS)
    assert graficos.CONFIG["displayModeBar"] is False
    assert fig.layout.hoverlabel.bordercolor == "#1d2a2e"


def test_tasa_real_es_tasa_menos_inflacion_con_bandas():
    fig = graficos.figura_tasa_real(filas(), BANDAS)
    assert len(fig.data) == 1 and fig.data[0].name == "Tasa real"
    esperado = [f["tasa_vigente"] - f["inflacion_anual"] for f in filas()]
    assert list(fig.data[0].y) == pytest.approx(esperado)
    assert len(fig.layout.shapes) == len(BANDAS)


def test_sin_filas_devuelve_figura_vacia_sin_fallar():
    assert len(graficos.figura_principal([], []).data) in (0, 3)
    assert len(graficos.figura_tasa_real([], []).layout.shapes) == 0


def test_tema_desconocido_es_error():
    with pytest.raises(ValueError):
        graficos.figura_principal(filas(), BANDAS, tema="sepia")


def filas_ext(n=24):
    out = filas(n)
    for i, f in enumerate(out):
        f.update({"brent_promedio": 60.0 + i, "tasa_usura_consumo": 28.0 - 0.1 * i, "tasa_cdt_90": 7.0 + 0.05 * i})
    return out


def test_trm_brent_tiene_trm_a_la_izquierda_y_brent_a_la_derecha():
    fig = graficos.figura_trm_brent(filas_ext())
    assert [t.name for t in fig.data] == ["TRM promedio", "Brent promedio"]
    assert fig.data[0].yaxis == "y" and fig.data[1].yaxis == "y2"
    assert fig.layout.yaxis2.title.text == "USD/barril"


def test_credito_compara_intervencion_usura_y_cdt_en_un_solo_eje():
    fig = graficos.figura_credito(filas_ext())
    assert [t.name for t in fig.data] == ["Tasa de intervención", "Tasa de usura (consumo)", "CDT a 90 días"]
    assert fig.data[0].line.shape == "hv"
    for t in fig.data:
        assert t.line.color.startswith("#")


def test_nuevas_figuras_aceptan_tema_oscuro_y_rechazan_desconocido():
    assert graficos.figura_credito(filas_ext(), tema="oscuro").layout.paper_bgcolor == "#0f1a1d"
    with pytest.raises(ValueError):
        graficos.figura_trm_brent(filas_ext(), tema="sepia")

import datetime as dt

import pytest

from app import analisis


def mes(m, trm, infl, tasa, anio=2024):
    return {"anio_mes": dt.date(anio, m, 1), "trm_promedio": trm, "inflacion_anual": infl, "tasa_vigente": tasa}


FILAS = [mes(1, 4000.0, 8.0, 13.0), mes(2, 4400.0, 7.0, 12.0), mes(3, 4200.0, 6.0, 11.0)]


def test_sin_filas_no_hay_indicadores():
    assert analisis.indicadores([]) is None


def test_variacion_de_la_trm_entre_el_primer_y_el_ultimo_mes():
    assert analisis.indicadores(FILAS)["variacion_trm_pct"] == pytest.approx(5.0)


def test_maximo_y_minimo_de_la_trm_con_su_mes():
    ind = analisis.indicadores(FILAS)
    assert ind["trm_max"] == (dt.date(2024, 2, 1), 4400.0)
    assert ind["trm_min"] == (dt.date(2024, 1, 1), 4000.0)


def test_inflacion_promedio_y_ultima_tasa():
    ind = analisis.indicadores(FILAS)
    assert ind["inflacion_promedio"] == pytest.approx(7.0)
    assert ind["tasa_ultima"] == 11.0
    assert ind["tasa_real_ultima"] == pytest.approx(5.0)  # 11 - 6


def test_correlacion_trm_inflacion_pearson():
    filas = [mes(1, 1.0, 1.0, 1.0), mes(2, 2.0, 2.0, 1.0), mes(3, 3.0, 3.0, 1.0)]
    assert analisis.indicadores(filas)["correlacion_trm_inflacion"] == pytest.approx(1.0)


def test_correlacion_no_definida_con_menos_de_tres_meses_o_sin_variacion():
    assert analisis.indicadores(FILAS[:2])["correlacion_trm_inflacion"] is None
    constantes = [mes(m, 4000.0, 5.0, 10.0) for m in (1, 2, 3)]
    assert analisis.indicadores(constantes)["correlacion_trm_inflacion"] is None


def test_ignora_meses_con_valores_nulos():
    filas = FILAS + [mes(4, None, None, None)]
    ind = analisis.indicadores(filas)
    assert ind["meses"] == 3
    assert ind["variacion_trm_pct"] == pytest.approx(5.0)


def test_conclusiones_describen_los_indicadores():
    textos = " ".join(analisis.conclusiones(analisis.indicadores(FILAS)))
    assert "subió" in textos and "5,0 %" in textos
    assert "tasa real" in textos


def test_conclusiones_dicen_que_bajo_cuando_la_trm_cae():
    filas = [mes(1, 4000.0, 5.0, 10.0), mes(2, 3800.0, 5.0, 10.0)]
    assert "bajó" in " ".join(analisis.conclusiones(analisis.indicadores(filas)))

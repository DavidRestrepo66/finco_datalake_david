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


# --- rediseño: KPI con delta, lectura, bandas de tasa y atajos de periodo ---


def serie(n=12, inicio=(2023, 7), trm=None, infl=None, tasa=None):
    """n meses consecutivos desde `inicio`; cada columna es una función del índice del mes."""
    trm = trm or (lambda i: 4000.0 + 100 * i)
    infl = infl or (lambda i: 10.0 - 0.5 * i)
    tasa = tasa or (lambda i: 12.0)
    anio, m = inicio
    filas = []
    for i in range(n):
        filas.append(mes(m, trm(i), infl(i), tasa(i), anio=anio))
        m += 1
        if m == 13:
            anio, m = anio + 1, 1
    return filas


def por_clave(items):
    return {k["clave"]: k for k in items}


def test_kpis_calcula_valores_del_periodo_y_delta_contra_el_anterior_de_igual_longitud():
    filas = serie(12, tasa=lambda i: 12.0 if i < 8 else 11.0)  # 2023-07 .. 2024-06
    k = por_clave(analisis.kpis(filas, dt.date(2024, 1, 1), dt.date(2024, 6, 1)))
    # periodo: i=6..11 (trm 4600..5100); anterior: i=0..5 (trm 4000..4500)
    assert k["trm"]["valor"] == pytest.approx((5100 / 4600 - 1) * 100)
    assert k["trm"]["delta"] == pytest.approx((5100 / 4600 - 1) * 100 - (4500 / 4000 - 1) * 100)
    assert k["inflacion"]["valor"] == pytest.approx(sum(10 - 0.5 * i for i in range(6, 12)) / 6)
    assert k["inflacion"]["delta"] == pytest.approx(-3.0)
    assert k["tasa"]["valor"] == 11.0
    assert k["tasa"]["delta"] == pytest.approx(-1.0)  # cierre anterior (i=5): 12
    assert k["tasa_real"]["valor"] == pytest.approx(11.0 - 4.5)  # diferencia simple, no Fisher
    assert k["tasa_real"]["delta"] == pytest.approx((11.0 - 4.5) - (12.0 - 7.5))


def test_kpis_delta_es_none_si_no_hay_periodo_anterior_completo():
    filas = serie(12)
    items = analisis.kpis(filas, dt.date(2023, 7, 1), dt.date(2023, 12, 1))
    assert [k["delta"] for k in items] == [None, None, None, None]
    assert all(k["delta_texto"] == "Sin periodo anterior comparable" for k in items)
    # periodo anterior incompleto (solo 3 meses disponibles antes)
    assert analisis.periodo_anterior(filas, dt.date(2023, 10, 1), dt.date(2024, 3, 1)) is None


def test_kpis_variacion_con_un_solo_mes_no_tiene_delta():
    filas = serie(12)
    k = por_clave(analisis.kpis(filas, dt.date(2024, 3, 1), dt.date(2024, 3, 1)))
    assert k["trm"]["valor"] == 0.0
    assert k["trm"]["delta"] is None
    assert k["tasa"]["delta"] == pytest.approx(0.0)


def test_kpis_sin_meses_en_el_rango_devuelve_none():
    assert analisis.kpis(serie(12), dt.date(2030, 1, 1), dt.date(2030, 6, 1)) is None


def test_kpis_incluyen_textos_en_espanol():
    filas = serie(12, tasa=lambda i: 12.0 if i < 8 else 11.0)
    k = por_clave(analisis.kpis(filas, dt.date(2024, 1, 1), dt.date(2024, 6, 1)))
    assert k["trm"]["valor_texto"] == "+10,9 %"
    assert k["tasa"]["valor_texto"] == "11,00 %"
    assert k["tasa"]["delta_texto"] == "▼ −1,00 pp vs. periodo anterior"
    assert k["tasa_real"]["nota"] == "Tasa vigente menos la inflación anual"


def test_periodo_anterior_devuelve_el_rango_de_igual_longitud():
    filas = serie(12)
    assert analisis.periodo_anterior(filas, dt.date(2024, 1, 1), dt.date(2024, 6, 1)) == (
        dt.date(2023, 7, 1),
        dt.date(2023, 12, 1),
    )


def tasa_con_cambios(cambios):
    """Tasa que parte de 10 y cambia en los índices dados al valor dado."""
    def f(i):
        v = 10.0
        for idx, nuevo in sorted(cambios.items()):
            if i >= idx:
                v = nuevo
        return v

    return f


def test_cambios_de_tasa_lista_mes_y_diferencia():
    filas = serie(8, tasa=tasa_con_cambios({2: 10.5, 5: 10.25}))
    cambios = analisis.cambios_de_tasa(filas)
    assert [(c["anio_mes"], c["delta"]) for c in cambios] == [(dt.date(2023, 9, 1), 0.5), (dt.date(2023, 12, 1), -0.25)]


def test_bandas_agrupan_cambios_del_mismo_sentido_con_hasta_tres_meses_de_separacion():
    # subidas en i=2,4,6 (separación 2) -> 1 banda; recorte en i=7 -> otra; subida en i=12 (separación 5) -> otra
    filas = serie(14, tasa=tasa_con_cambios({2: 11, 4: 12, 6: 13, 7: 12.5, 12: 13}))
    bandas = analisis.bandas_de_tasa(filas)
    assert [(b["direccion"], b["desde"], b["hasta"], b["cambios"]) for b in bandas] == [
        ("subida", dt.date(2023, 9, 1), dt.date(2024, 1, 1), 3),
        ("recorte", dt.date(2024, 2, 1), dt.date(2024, 2, 1), 1),
        ("subida", dt.date(2024, 7, 1), dt.date(2024, 7, 1), 1),
    ]


def test_bandas_separan_cambios_del_mismo_sentido_a_mas_de_tres_meses():
    filas = serie(10, tasa=tasa_con_cambios({1: 11, 5: 12}))
    assert [b["cambios"] for b in analisis.bandas_de_tasa(filas)] == [1, 1]


def test_bandas_sin_cambios_de_tasa():
    assert analisis.bandas_de_tasa(serie(6)) == []
    assert analisis.bandas_de_tasa([]) == []


def test_lectura_son_tres_parrafos_con_conteo_de_subidas_y_recortes():
    filas = serie(8, tasa=tasa_con_cambios({1: 10.5, 2: 11, 5: 10.5}))
    parrafos = analisis.lectura(filas)
    assert len(parrafos) == 3
    assert "jul 2023" in parrafos[0] and "feb 2024" in parrafos[0]
    assert "3 veces (2 subidas, 1 recorte)" in parrafos[2]
    assert "por debajo del inicio del periodo" in parrafos[1]


def test_lectura_sin_cambios_de_tasa_dice_que_se_mantuvo():
    parrafos = analisis.lectura(serie(6))
    assert "se mantuvo en 12,00 %" in parrafos[2]


def test_lectura_concuerda_en_singular():
    filas = serie(6, tasa=tasa_con_cambios({2: 11}))
    assert "1 vez (1 subida, 0 recortes)" in analisis.lectura(filas)[2]


def test_lectura_sin_filas_completas_devuelve_lista_vacia():
    assert analisis.lectura([]) == []


def test_atajos_de_periodo_se_calculan_con_los_meses_disponibles():
    meses = [dt.date(2020 + i // 12, i % 12 + 1, 1) for i in range(81)]
    a = analisis.atajos(meses)
    assert list(a) == ["Último año", "Desde 2020", "2023"]
    assert a["Último año"] == (meses[-12], meses[-1])
    assert a["Desde 2020"] == (meses[0], meses[-1])
    assert a["2023"] == (dt.date(2023, 1, 1), dt.date(2023, 12, 1))


def test_atajo_de_anio_se_recorta_a_los_meses_disponibles_y_se_omite_si_no_hay():
    meses = [dt.date(2023, m, 1) for m in range(1, 7)]
    assert analisis.atajos(meses)["2023"] == (dt.date(2023, 1, 1), dt.date(2023, 6, 1))
    assert "2023" not in analisis.atajos([dt.date(2024, 1, 1), dt.date(2024, 2, 1)])

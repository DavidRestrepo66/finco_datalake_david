"""Análisis breve del mart mensual para la app web: indicadores y conclusiones en texto.

Lógica sin Streamlit. Recibe filas como diccionarios con anio_mes, trm_promedio, inflacion_anual
y tasa_vigente; los meses con algún valor nulo se ignoran.
"""

from statistics import StatisticsError, correlation, mean


def indicadores(filas):
    """Indicadores del rango, o None si no hay meses completos."""
    meses = [f for f in filas if None not in (f["trm_promedio"], f["inflacion_anual"], f["tasa_vigente"])]
    if not meses:
        return None
    meses = sorted(meses, key=lambda f: f["anio_mes"])
    trm = [float(f["trm_promedio"]) for f in meses]
    inflacion = [float(f["inflacion_anual"]) for f in meses]
    ultimo = meses[-1]
    mayor = max(meses, key=lambda f: f["trm_promedio"])
    menor = min(meses, key=lambda f: f["trm_promedio"])
    return {
        "meses": len(meses),
        "desde": meses[0]["anio_mes"],
        "hasta": ultimo["anio_mes"],
        "variacion_trm_pct": (trm[-1] / trm[0] - 1) * 100,
        "trm_max": (mayor["anio_mes"], float(mayor["trm_promedio"])),
        "trm_min": (menor["anio_mes"], float(menor["trm_promedio"])),
        "inflacion_promedio": mean(inflacion),
        "tasa_ultima": float(ultimo["tasa_vigente"]),
        "tasa_real_ultima": float(ultimo["tasa_vigente"]) - float(ultimo["inflacion_anual"]),
        "correlacion_trm_inflacion": _correlacion(trm, inflacion),
    }


def _correlacion(x, y):
    if len(x) < 3:
        return None
    try:
        return correlation(x, y)
    except StatisticsError:
        return None


def _num(valor, decimales=1):
    return f"{valor:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _mes(fecha):
    return fecha.strftime("%m/%Y")


def conclusiones(ind):
    """Frases que resumen los indicadores."""
    sube = ind["variacion_trm_pct"] >= 0
    textos = [
        (
            f"Entre {_mes(ind['desde'])} y {_mes(ind['hasta'])} la TRM promedio "
            f"{'subió' if sube else 'bajó'} {_num(abs(ind['variacion_trm_pct']))} %."
        ),
        (
            f"El máximo fue {_num(ind['trm_max'][1], 2)} COP en {_mes(ind['trm_max'][0])} y el mínimo "
            f"{_num(ind['trm_min'][1], 2)} COP en {_mes(ind['trm_min'][0])}."
        ),
        f"La inflación anual promedio del rango fue {_num(ind['inflacion_promedio'])} %.",
    ]
    real = ind["tasa_real_ultima"]
    textos.append(
        f"La tasa de intervención vigente es {_num(ind['tasa_ultima'])} %; frente a la inflación del último mes, "
        f"la tasa real es {_num(real)} puntos ({'positiva' if real >= 0 else 'negativa'})."
    )
    r = ind["correlacion_trm_inflacion"]
    if r is None:
        textos.append("No hay meses suficientes (o variación) para medir la relación entre TRM e inflación.")
    else:
        fuerza = "fuerte" if abs(r) >= 0.7 else "moderada" if abs(r) >= 0.4 else "débil"
        sentido = "positiva" if r >= 0 else "negativa"
        textos.append(
            f"La correlación entre TRM e inflación es {fuerza} y {sentido} (r = {_num(r, 2)}); "
            "correlación no implica causalidad."
        )
    return textos

"""Análisis breve del mart mensual para la app web: indicadores y conclusiones en texto.

Lógica sin Streamlit. Recibe filas como diccionarios con anio_mes, trm_promedio, inflacion_anual
y tasa_vigente; los meses con algún valor nulo se ignoran.

Tasa real: es la diferencia simple `tasa_vigente - inflacion_anual` (puntos porcentuales), la misma que usa
`indicadores()`. La maqueta de diseño usaba la fórmula de Fisher ((1+t)/(1+p)-1); se eligió la diferencia
simple para que la página Análisis, los KPI y las conclusiones en texto den el mismo número.
"""

import datetime as dt
from itertools import pairwise
from statistics import StatisticsError, correlation, mean

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
SEPARACION_MAXIMA_BANDA = 3  # meses entre cambios del mismo sentido para agruparlos en un ciclo
SIN_ANTERIOR = "Sin periodo anterior comparable"


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


# --- Rediseño de la app: KPI con delta, lectura del periodo, bandas de tasa y atajos de periodo ---


def numero(valor, decimales=1):
    """Número con separadores es-CO (punto de miles, coma decimal)."""
    return _num(valor, decimales)


def porcentaje(valor, decimales=2):
    return f"{_num(valor, decimales)} %"


def con_signo(valor, decimales, unidad):
    """«+1,2 %», «−0,5 pp» o «±0,0 %» si el valor redondeado es cero."""
    redondeado = round(valor, decimales)
    signo = "+" if redondeado > 0 else "−" if redondeado < 0 else "±"
    return f"{signo}{_num(abs(valor), decimales)}{unidad}"


def etiqueta_mes(fecha):
    """«ene 2020»."""
    return f"{MESES[fecha.month - 1]} {fecha.year}"


def _completos(filas):
    meses = [f for f in filas if None not in (f["trm_promedio"], f["inflacion_anual"], f["tasa_vigente"])]
    return sorted(meses, key=lambda f: f["anio_mes"])


def _ventana(filas, desde, hasta):
    """(meses completos ordenados, índice inicial y final+1 del rango dado)."""
    meses = _completos(filas)
    idx = [i for i, f in enumerate(meses) if desde <= f["anio_mes"] <= hasta]
    if not idx:
        return meses, None, None
    return meses, idx[0], idx[-1] + 1


def periodo_anterior(filas, desde, hasta):
    """(desde, hasta) del periodo inmediatamente anterior de igual longitud, o None si no está completo."""
    meses, a, b = _ventana(filas, desde, hasta)
    if a is None or a - (b - a) < 0:
        return None
    inicio = a - (b - a)
    return meses[inicio]["anio_mes"], meses[a - 1]["anio_mes"]


def _variacion_trm(meses):
    return (float(meses[-1]["trm_promedio"]) / float(meses[0]["trm_promedio"]) - 1) * 100


def _inflacion_promedio(meses):
    return mean(float(f["inflacion_anual"]) for f in meses)


def _tasa_real(fila):
    return float(fila["tasa_vigente"]) - float(fila["inflacion_anual"])


def kpis(filas, desde, hasta):
    """Cuatro KPI del rango [desde, hasta] con su delta frente al periodo anterior de igual longitud.

    Cada elemento: clave, etiqueta, valor, valor_texto, nota, delta y delta_texto. El delta es None si no
    hay un periodo anterior completo (o, en la variación de la TRM, si el rango es de un solo mes).
    Devuelve None si el rango no tiene meses completos.
    """
    meses, a, b = _ventana(filas, desde, hasta)
    if a is None:
        return None
    actual = meses[a:b]
    previo = meses[a - (b - a) : a] if a - (b - a) >= 0 else None
    ultimo = actual[-1]
    cierre_previo = previo[-1] if previo else None

    var = _variacion_trm(actual)
    inf = _inflacion_promedio(actual)
    tasa = float(ultimo["tasa_vigente"])
    real = _tasa_real(ultimo)
    items = [
        (
            "trm", "Variación de la TRM", var, con_signo(var, 1, " %"),
            f"$ {_num(float(actual[0]['trm_promedio']), 0)} → $ {_num(float(ultimo['trm_promedio']), 0)}",
            var - _variacion_trm(previo) if previo and len(actual) > 1 else None,
        ),
        (
            "inflacion", "Inflación promedio", inf, porcentaje(inf),
            f"Cierre del periodo: {porcentaje(float(ultimo['inflacion_anual']))}",
            inf - _inflacion_promedio(previo) if previo else None,
        ),
        (
            "tasa", "Tasa vigente", tasa, porcentaje(tasa),
            f"Vigente a {etiqueta_mes(ultimo['anio_mes'])}",
            tasa - float(cierre_previo["tasa_vigente"]) if previo else None,
        ),
        (
            "tasa_real", "Tasa real", real, porcentaje(real),
            "Tasa vigente menos la inflación anual",
            real - _tasa_real(cierre_previo) if previo else None,
        ),
    ]
    resultado = []
    for clave, etiqueta, valor, valor_texto, nota, delta in items:
        if delta is None:
            delta_texto = SIN_ANTERIOR
        else:
            flecha = "▲ " if round(delta, 2) > 0 else "▼ " if round(delta, 2) < 0 else ""
            delta_texto = f"{flecha}{con_signo(delta, 2, ' pp')} vs. periodo anterior"
        resultado.append(
            {
                "clave": clave, "etiqueta": etiqueta, "valor": valor, "valor_texto": valor_texto,
                "nota": nota, "delta": delta, "delta_texto": delta_texto,
            }
        )
    return resultado


def cambios_de_tasa(filas):
    """Meses en que la tasa vigente cambió frente al mes anterior: [{anio_mes, delta}] (delta en pp)."""
    con_tasa = sorted((f for f in filas if f["tasa_vigente"] is not None), key=lambda f: f["anio_mes"])
    cambios = []
    for anterior, actual in pairwise(con_tasa):
        delta = float(actual["tasa_vigente"]) - float(anterior["tasa_vigente"])
        if delta != 0:
            cambios.append({"anio_mes": actual["anio_mes"], "delta": delta})
    return cambios


def bandas_de_tasa(filas):
    """Ciclos de la tasa: cambios del mismo sentido separados por 3 meses o menos forman una banda.

    Cada banda: desde y hasta (mes del primer y del último cambio), direccion («subida» o «recorte») y cambios.
    """
    con_tasa = sorted((f for f in filas if f["tasa_vigente"] is not None), key=lambda f: f["anio_mes"])
    posicion = {f["anio_mes"]: i for i, f in enumerate(con_tasa)}
    bandas = []
    for c in cambios_de_tasa(con_tasa):
        direccion = "subida" if c["delta"] > 0 else "recorte"
        i = posicion[c["anio_mes"]]
        ultima = bandas[-1] if bandas else None
        if (
            ultima
            and ultima["direccion"] == direccion
            and i - posicion[ultima["hasta"]] <= SEPARACION_MAXIMA_BANDA
        ):
            ultima["hasta"] = c["anio_mes"]
            ultima["cambios"] += 1
        else:
            bandas.append({"desde": c["anio_mes"], "hasta": c["anio_mes"], "direccion": direccion, "cambios": 1})
    return bandas


def _plural(n, singular, plural):
    return f"{n} {singular if n == 1 else plural}"


def lectura(filas):
    """Tres párrafos que resumen el periodo (TRM, inflación y decisiones de tasa); [] si no hay meses completos."""
    meses = _completos(filas)
    if not meses:
        return []
    primero, ultimo = meses[0], meses[-1]
    var = _variacion_trm(meses)
    inicio_inf, cierre_inf = float(primero["inflacion_anual"]), float(ultimo["inflacion_anual"])
    tasa = float(ultimo["tasa_vigente"])
    real = _tasa_real(ultimo)
    cambios = cambios_de_tasa(meses)
    subidas = sum(1 for c in cambios if c["delta"] > 0)
    recortes = len(cambios) - subidas
    parrafos = [
        (
            f"Entre {etiqueta_mes(primero['anio_mes'])} y {etiqueta_mes(ultimo['anio_mes'])} la TRM promedio pasó de "
            f"$ {_num(float(primero['trm_promedio']), 0)} a $ {_num(float(ultimo['trm_promedio']), 0)}, "
            f"una variación de {con_signo(var, 1, ' %')}."
        ),
        (
            f"La inflación anual promedió {porcentaje(_inflacion_promedio(meses))} y cerró en "
            f"{porcentaje(cierre_inf)}, "
            f"{'por debajo' if cierre_inf < inicio_inf else 'por encima'} del inicio del periodo."
        ),
    ]
    if cambios:
        parrafos.append(
            f"El Banco de la República cambió la tasa {_plural(len(cambios), 'vez', 'veces')} "
            f"({_plural(subidas, 'subida', 'subidas')}, {_plural(recortes, 'recorte', 'recortes')}) "
            f"y la dejó en {porcentaje(tasa)}, con una tasa real de {porcentaje(real)}."
        )
    else:
        parrafos.append(
            f"La tasa de intervención se mantuvo en {porcentaje(tasa)} durante todo el periodo, "
            f"con una tasa real de cierre de {porcentaje(real)}."
        )
    return parrafos


def atajos(meses):
    """Atajos de periodo {etiqueta: (desde, hasta)} a partir de los meses disponibles (primer día de cada mes)."""
    meses = sorted(meses)
    if not meses:
        return {}
    resultado = {"Último año": (meses[-12:][0], meses[-1])}
    desde_2020 = [m for m in meses if m >= dt.date(2020, 1, 1)]
    if desde_2020:
        resultado["Desde 2020"] = (desde_2020[0], meses[-1])
    de_2023 = [m for m in meses if m.year == 2023]
    if de_2023:
        resultado["2023"] = (de_2023[0], de_2023[-1])
    return resultado


# --- Nuevas fuentes: Brent, usura y CDT (columnas opcionales del mart) ---

COLUMNAS_FACTORES = ("brent_promedio", "tasa_usura_consumo")


def factores(filas):
    """Relaciones con las fuentes nuevas, o None si el mart no las trae o no hay datos.

    correlacion_trm_brent: Pearson entre la TRM y el Brent de los meses que tienen ambos (None con menos de 3).
    usura_ultima y spread_usura_tasa (usura menos tasa de intervención, en pp): último mes con ambas tasas.
    """
    if not filas or not all(c in filas[0] for c in COLUMNAS_FACTORES):
        return None
    con_brent = [f for f in sorted(filas, key=lambda f: f["anio_mes"]) if None not in (f["trm_promedio"], f["brent_promedio"])]
    con_usura = [f for f in sorted(filas, key=lambda f: f["anio_mes"]) if None not in (f["tasa_usura_consumo"], f["tasa_vigente"])]
    if not con_brent and not con_usura:
        return None
    ultima = con_usura[-1] if con_usura else None
    return {
        "correlacion_trm_brent": _correlacion(
            [float(f["trm_promedio"]) for f in con_brent], [float(f["brent_promedio"]) for f in con_brent]
        ),
        "usura_ultima": float(ultima["tasa_usura_consumo"]) if ultima else None,
        "spread_usura_tasa": float(ultima["tasa_usura_consumo"]) - float(ultima["tasa_vigente"]) if ultima else None,
    }


def lectura_factores(filas):
    """Frases sobre la TRM frente al Brent y la usura frente a la tasa de intervención; [] si no hay datos."""
    f = factores(filas)
    if f is None:
        return []
    textos = []
    r = f["correlacion_trm_brent"]
    if r is None:
        textos.append("No hay meses suficientes (o variación) para medir la relación entre la TRM y el Brent.")
    else:
        fuerza = "fuerte" if abs(r) >= 0.7 else "moderada" if abs(r) >= 0.4 else "débil"
        textos.append(
            f"La correlación entre la TRM y el Brent es {fuerza} y {'positiva' if r >= 0 else 'negativa'} "
            f"(r = {_num(r, 2)}); correlación no implica causalidad."
        )
    if f["usura_ultima"] is not None:
        textos.append(
            f"La tasa de usura de consumo y ordinario es {porcentaje(f['usura_ultima'])}, "
            f"{_num(f['spread_usura_tasa'])} puntos por encima de la tasa de intervención."
        )
    return textos

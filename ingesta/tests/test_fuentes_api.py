
from ingesta.extractores.fred import extraer_fred
from ingesta.extractores.trm_socrata import extraer_socrata


class Resp:
    def __init__(self, data=None, text=""):
        self._d, self.text = data, text

    def raise_for_status(self):
        pass

    def json(self):
        return self._d


class Sesion:
    def __init__(self, filas=None, texto=""):
        self.filas, self.texto, self.llamadas = filas or [], texto, []

    def get(self, url, params=None, timeout=None):
        self.llamadas.append((url, params))
        if not self.filas and self.texto:
            return Resp(text=self.texto)
        o, n = int(params["$offset"]), int(params["$limit"])
        return Resp(self.filas[o : o + n])


def test_socrata_generico_pagina_y_usa_url_filtro_y_orden():
    filas = [{"a": i} for i in range(25)]
    s = Sesion(filas)
    r = extraer_socrata("http://x/y.json", "f >= '2020'", "f, g", sesion=s, tam_pagina=10)
    assert r == filas
    assert {u for u, _ in s.llamadas} == {"http://x/y.json"}
    assert s.llamadas[0][1]["$where"] == "f >= '2020'" and s.llamadas[0][1]["$order"] == "f, g"


def test_fred_devuelve_filas_crudas_como_texto():
    s = Sesion(texto="observation_date,FEDFUNDS\n2020-01-01,1.55\n2020-02-01,1.58\n")
    r = extraer_fred("FEDFUNDS", "2020-01-01", sesion=s)
    assert r == [
        {"observation_date": "2020-01-01", "FEDFUNDS": "1.55"},
        {"observation_date": "2020-02-01", "FEDFUNDS": "1.58"},
    ]
    url, params = s.llamadas[0]
    assert url == "https://fred.stlouisfed.org/graph/fredgraph.csv"
    assert params == {"id": "FEDFUNDS", "cosd": "2020-01-01"}


def test_fred_conserva_los_valores_vacios_de_dias_sin_dato():
    s = Sesion(texto="observation_date,DCOILBRENTEU\n2020-01-01,\n")
    assert extraer_fred("DCOILBRENTEU", "2020-01-01", sesion=s)[0]["DCOILBRENTEU"] == ""

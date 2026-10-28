
from ingesta.extractores.trm_socrata import FECHA_INICIO, extraer_trm


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


class FakeSession:
    """Simula la API Socrata sin red: devuelve `filas` paginadas por $limit/$offset."""

    def __init__(self, filas):
        self.filas = filas
        self.llamadas = []

    def get(self, url, params=None, timeout=None):
        self.llamadas.append(params)
        offset, limit = int(params["$offset"]), int(params["$limit"])
        return FakeResponse(self.filas[offset : offset + limit])


def _filas(n):
    return [
        {"valor": str(3000 + i), "vigenciadesde": f"d{i}", "vigenciahasta": f"h{i}"}
        for i in range(n)
    ]


def test_recorre_todas_las_paginas():  # CP-ING-01
    sesion = FakeSession(_filas(25))
    resultado = extraer_trm(sesion, tam_pagina=10)
    assert resultado == _filas(25)
    assert [p["$offset"] for p in sesion.llamadas] == [0, 10, 20]


def test_filtra_desde_2020_y_ordena():
    sesion = FakeSession(_filas(3))
    extraer_trm(sesion, tam_pagina=10)
    assert FECHA_INICIO == "2020-01-01"
    assert "2020-01-01" in sesion.llamadas[0]["$where"]
    assert sesion.llamadas[0]["$order"] == "vigenciadesde"


def test_conserva_el_valor_original_sin_transformar():
    filas = [{"valor": "3158.43", "vigenciadesde": "x", "vigenciahasta": "y"}]
    assert extraer_trm(FakeSession(filas))[0]["valor"] == "3158.43"

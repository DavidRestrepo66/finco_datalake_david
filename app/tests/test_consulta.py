import datetime as dt

import pytest

from app import consulta


class ConexionFalsa:
    """Imita la parte de psycopg que usa consulta: execute(sql, params) -> cursor."""

    def __init__(self, columnas, filas):
        self.columnas, self.filas, self.llamadas = columnas, filas, []

    def execute(self, sentencia, params):
        self.llamadas.append((sentencia.as_string(), params))
        outer = self

        class Cursor:
            def __init__(self):
                self.description = [(c,) for c in outer.columnas]

            def fetchall(self):
                return outer.filas

        return Cursor()


def test_conjuntos_ofrece_la_trm_diaria():
    assert "trm_diaria" in consulta.CONJUNTOS


def test_consultar_filtra_por_rango_inclusivo_y_devuelve_columnas_y_filas():
    filas = [(dt.date(2023, 1, 2), 4600.5)]
    con = ConexionFalsa(["fecha", "valor"], filas)
    columnas, resultado = consulta.consultar(con, "trm_diaria", dt.date(2023, 1, 1), dt.date(2023, 12, 31))
    assert columnas == ["fecha", "valor"]
    assert resultado == filas
    sentencia, params = con.llamadas[0]
    assert "gold" in sentencia and "fact_trm_diaria" in sentencia
    assert params == (dt.date(2023, 1, 1), dt.date(2023, 12, 31))


def test_consultar_rechaza_un_conjunto_desconocido():
    with pytest.raises(ValueError, match="conjunto"):
        consulta.consultar(ConexionFalsa([], []), "otro", dt.date(2023, 1, 1), dt.date(2023, 1, 2))


def test_consultar_rechaza_rango_invertido():
    with pytest.raises(ValueError, match="rango"):
        consulta.consultar(ConexionFalsa([], []), "trm_diaria", dt.date(2023, 2, 1), dt.date(2023, 1, 1))


def test_a_csv_tiene_encabezado_y_exactamente_las_filas():
    texto = consulta.a_csv(["fecha", "valor"], [(dt.date(2023, 1, 2), 4600.5), (dt.date(2023, 1, 3), 4590)])
    assert texto.splitlines() == ["fecha,valor", "2023-01-02,4600.5", "2023-01-03,4590"]


def test_a_csv_sin_filas_no_genera_archivo():
    assert consulta.a_csv(["fecha", "valor"], []) is None

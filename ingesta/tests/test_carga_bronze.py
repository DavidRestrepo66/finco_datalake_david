import pytest

psycopg = pytest.importorskip("psycopg")

from ingesta.carga_bronze import cargar_trm, conectar, crear_tablas

FILAS = [
    {"valor": "3158.43", "vigenciadesde": "2026-10-24T00:00:00.000", "vigenciahasta": "2026-10-26T00:00:00.000"},
    {"valor": "3185.01", "vigenciadesde": "2026-10-23T00:00:00.000", "vigenciahasta": "2026-10-23T00:00:00.000"},
]


@pytest.fixture
def conn():
    try:
        c = conectar()
    except psycopg.OperationalError:
        pytest.skip("PostgreSQL no disponible (docker compose up -d)")
    crear_tablas(c)
    yield c
    c.rollback()  # nada de la prueba queda en la base
    c.close()


def test_cada_registro_tiene_fuente_fecha_de_carga_y_lote(conn):  # CP-ING-03
    lote = cargar_trm(conn, FILAS)
    filas = conn.execute(
        "select fuente, cargado_en, lote_id, valor from bronze.trm_raw where lote_id = %s order by valor",
        (lote,),
    ).fetchall()
    assert len(filas) == 2
    for fuente, cargado_en, lote_id, _ in filas:
        assert fuente == "datos.gov.co/ceyp-9c7c"
        assert cargado_en is not None
        assert lote_id == lote
    assert [f[3] for f in filas] == ["3158.43", "3185.01"]  # valor original, como texto


def test_nueva_ejecucion_crea_lote_nuevo_sin_tocar_el_anterior(conn):
    lote1 = cargar_trm(conn, FILAS)
    antes = conn.execute("select * from bronze.trm_raw where lote_id = %s order by id", (lote1,)).fetchall()
    lote2 = cargar_trm(conn, FILAS)
    assert lote2 != lote1
    despues = conn.execute("select * from bronze.trm_raw where lote_id = %s order by id", (lote1,)).fetchall()
    assert antes == despues

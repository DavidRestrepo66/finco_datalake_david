"""Prueba de humo de la app web (HU-14): el script de Streamlit se ejecuta sin excepciones.

Regresión: el entrypoint se llamaba `app/app.py`, igual que el paquete. Streamlit pone la carpeta
del script al frente de `sys.path`, así que `from app import consulta` resolvía al propio script y
la app fallaba con `partially initialized module 'app'`.
"""

import os
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")
pytest.importorskip("streamlit")

from streamlit.testing.v1 import AppTest

RUTA = Path(__file__).resolve().parents[1] / "ui.py"


@pytest.fixture(autouse=True)
def requiere_postgres():
    try:
        conexion = psycopg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            dbname=os.environ["POSTGRES_DB"],
        )
    except KeyError:
        pytest.skip("faltan las variables POSTGRES_*")
    except psycopg.OperationalError:
        pytest.skip("PostgreSQL no disponible (docker compose up -d)")
    conexion.close()


def test_el_paquete_app_apunta_al_paquete_y_no_al_script():
    import app

    assert Path(app.__file__).name == "__init__.py"


PAGINAS = ["Inicio", "Análisis", "Datos", "Calidad y linaje"]


def ejecutar(pagina=None):
    at = AppTest.from_file(str(RUTA), default_timeout=60)
    if pagina:
        at.session_state["pagina"] = pagina
    at.run()
    return at


def test_el_script_se_ejecuta_sin_excepciones():
    at = ejecutar()

    assert not at.exception, [str(e.value) for e in at.exception]


def test_la_barra_lateral_ofrece_las_cuatro_paginas_el_periodo_y_el_tema():
    at = ejecutar()

    navegacion = at.sidebar.radio(key="pagina")
    assert list(navegacion.options) == [f"{i:02d}  {n}" for i, n in enumerate(PAGINAS, 1)]
    assert [s.label for s in at.sidebar.selectbox] == ["Desde", "Hasta"]
    assert list(at.sidebar.radio(key="tema").options) == ["Claro", "Oscuro"]
    assert [b.label for b in at.sidebar.button] == ["Último año", "Desde 2020", "2023"]


@pytest.mark.parametrize("pagina", PAGINAS)
def test_cada_pagina_se_renderiza_sin_excepciones(pagina):
    at = ejecutar(pagina)

    assert not at.exception, [str(e.value) for e in at.exception]
    assert at.sidebar.radio(key="pagina").value == pagina


def test_cambiar_de_pagina_con_el_widget_de_navegacion():
    at = ejecutar()
    at.sidebar.radio(key="pagina").set_value("Datos").run()

    assert not at.exception, [str(e.value) for e in at.exception]
    assert any("Consulta y descarga" in m.value for m in at.markdown)


def test_el_tema_oscuro_se_renderiza_sin_excepciones():
    at = ejecutar("Análisis")
    at.sidebar.radio(key="tema").set_value("Oscuro").run()

    assert not at.exception, [str(e.value) for e in at.exception]
    assert any("#0f1a1d" in m.value for m in at.markdown)


def test_el_atajo_2023_fija_el_periodo_global():
    at = ejecutar("Datos")
    at.sidebar.button(key="atajo_2023").click().run()

    assert not at.exception, [str(e.value) for e in at.exception]
    assert at.session_state["desde"].isoformat() == "2023-01-01"
    assert at.session_state["hasta"].isoformat() == "2023-12-01"


def test_datos_ofrece_el_boton_de_descarga():
    at = ejecutar("Datos")

    assert not at.exception, [str(e.value) for e in at.exception]
    assert len(at.get("download_button")) == 1
    assert at.get("download_button")[0].proto.label == "Descargar CSV"


def test_calidad_sin_artefactos_explica_como_montarlos(monkeypatch, tmp_path):
    monkeypatch.setenv("DBT_TARGET_DIR", str(tmp_path))
    at = ejecutar("Calidad y linaje")

    assert not at.exception, [str(e.value) for e in at.exception]
    assert any("No se encontraron los artefactos de dbt" in m.value for m in at.markdown)


def test_datos_columnas_se_quitan_con_x_y_se_agregan_con_el_buscador():
    at = ejecutar("Datos")
    clave = "vis_mart_mensual"
    todas = list(at.session_state[clave])
    assert len(todas) == 5

    quitar = next(b for b in at.button if b.label == "trm_promedio ✕")
    quitar.click().run()
    assert not at.exception, [str(e.value) for e in at.exception]
    assert "trm_promedio" not in at.session_state[clave]

    buscador = next(s for s in at.selectbox if s.label == "Columnas visibles")
    buscador.select("trm_promedio").run()
    assert not at.exception, [str(e.value) for e in at.exception]
    assert "trm_promedio" in at.session_state[clave]


def test_datos_no_permite_quitar_la_ultima_columna():
    at = ejecutar("Datos")
    for nombre in ["trm_promedio", "ipc", "inflacion_anual", "tasa_vigente"]:
        next(b for b in at.button if b.label == f"{nombre} ✕").click().run()
    assert at.session_state["vis_mart_mensual"] == ["anio_mes"]
    assert next(b for b in at.button if b.label == "anio_mes ✕").disabled

import json

import pytest

from app import calidad

MANIFEST = {
    "nodes": {
        "model.finco.silver_ipc": {
            "name": "silver_ipc",
            "schema": "silver",
            "resource_type": "model",
            "columns": {},
        },
        "model.finco.fact_ind": {
            "name": "fact_ind",
            "schema": "gold",
            "resource_type": "model",
            "columns": {"inflacion": {"description": "Inflación (de silver.ipc.inflacion)."}},
        },
        "model.finco.mart_mensual": {
            "name": "mart_mensual",
            "schema": "gold",
            "resource_type": "model",
            "columns": {
                "anio_mes": {"description": "Primer día del mes."},
                "inflacion": {"description": "Inflación (de gold.fact_ind.inflacion)."},
            },
        },
        "test.finco.not_null_mart_anio_mes.abc": {
            "name": "not_null_mart_anio_mes",
            "attached_node": "model.finco.mart_mensual",
            "column_name": "anio_mes",
            "test_metadata": {"name": "not_null"},
        },
        "test.finco.sin_traslapes": {
            "name": "sin_traslapes",
            "attached_node": "model.finco.silver_ipc",
            "column_name": None,
            "test_metadata": None,
        },
    },
    "unit_tests": {
        "unit_test.finco.silver_ipc.gana_lote": {"name": "gana_lote", "model": "silver_ipc"}
    },
    "parent_map": {
        "model.finco.mart_mensual": ["model.finco.fact_ind"],
        "model.finco.fact_ind": ["model.finco.silver_ipc"],
        "model.finco.silver_ipc": ["source.finco.bronze.ipc_raw"],
    },
}
RESULTADOS = {
    "metadata": {"generated_at": "2026-10-31T03:41:13.027161Z"},
    "results": [
        {"unique_id": "model.finco.mart_mensual", "status": "success"},
        {"unique_id": "test.finco.not_null_mart_anio_mes.abc", "status": "pass"},
        {"unique_id": "test.finco.sin_traslapes", "status": "fail"},
        {"unique_id": "unit_test.finco.silver_ipc.gana_lote", "status": "pass"},
    ],
}


def test_pruebas_ignora_modelos_y_describe_cada_prueba():
    pruebas = calidad.pruebas(RESULTADOS, MANIFEST)
    assert [p["modelo"] for p in pruebas] == ["mart_mensual", "silver_ipc", "silver_ipc"]
    primera = pruebas[0]
    assert (primera["capa"], primera["columna"], primera["prueba"], primera["estado"]) == (
        "gold",
        "anio_mes",
        "not_null",
        "PASS",
    )


def test_prueba_singular_y_unitaria_usan_su_nombre():
    pruebas = calidad.pruebas(RESULTADOS, MANIFEST)
    assert (pruebas[1]["prueba"], pruebas[1]["columna"], pruebas[1]["estado"]) == (
        "sin_traslapes",
        "(tabla)",
        "FAIL",
    )
    assert (pruebas[2]["prueba"], pruebas[2]["estado"]) == ("gana_lote (unitaria)", "PASS")


def test_resumen_cuenta_pasadas_y_no_pasadas():
    resumen = calidad.resumen(calidad.pruebas(RESULTADOS, MANIFEST))
    assert resumen == {"total": 3, "pass": 2, "fallidas": 1, "modelos": 2}


def test_linaje_sigue_la_descripcion_hasta_la_fuente():
    linaje = dict(calidad.linaje(MANIFEST, "mart_mensual"))
    assert linaje["inflacion"] == [
        "mart_mensual.inflacion",
        "fact_ind.inflacion",
        "silver_ipc.inflacion",
        "bronze.ipc_raw",
    ]
    assert linaje["anio_mes"] == ["mart_mensual.anio_mes"]


def test_cargar_devuelve_none_si_faltan_los_archivos(tmp_path):
    assert calidad.cargar(tmp_path) is None


def test_cargar_lee_ambos_archivos(tmp_path):
    (tmp_path / "run_results.json").write_text(json.dumps(RESULTADOS))
    (tmp_path / "manifest.json").write_text(json.dumps(MANIFEST))
    resultados, manifest = calidad.cargar(tmp_path)
    assert resultados["metadata"]["generated_at"].startswith("2026-10-31")
    assert "nodes" in manifest


def test_cargar_rechaza_json_invalido(tmp_path):
    (tmp_path / "run_results.json").write_text("{no es json")
    (tmp_path / "manifest.json").write_text("{}")
    assert calidad.cargar(tmp_path) is None


@pytest.mark.parametrize("ruta", [None, ""])
def test_cargar_sin_carpeta_configurada(ruta):
    assert calidad.cargar(ruta) is None

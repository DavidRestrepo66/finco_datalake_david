"""Calidad y linaje a partir de los artefactos de dbt (run_results.json y manifest.json).

Lógica sin Streamlit. Si los archivos no están (o no se pueden leer) `cargar` devuelve None y la
página lo explica en vez de inventar resultados.
"""

import json
import re
from pathlib import Path

ESTADOS = {"pass": "PASS", "fail": "FAIL", "error": "ERROR", "warn": "WARN", "skipped": "SKIP"}
ORIGEN = re.compile(r"\bde (\w+)\.(\w+)\.(\w+)")
MODELO = re.compile(r"\b(silver|gold)\.(\w+)")


def cargar(carpeta):
    """(run_results, manifest) de la carpeta, o None si faltan o no son JSON válido."""
    if not carpeta:
        return None
    base = Path(carpeta)
    try:
        resultados = json.loads((base / "run_results.json").read_text(encoding="utf-8"))
        manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return resultados, manifest


def _modelo(manifest, unique_id):
    return manifest["nodes"].get(unique_id)


def pruebas(resultados, manifest):
    """Una fila por prueba (de datos o unitaria): modelo, capa, columna, prueba y estado."""
    filas = []
    for r in resultados["results"]:
        uid, estado = r["unique_id"], ESTADOS.get(r["status"], r["status"].upper())
        if uid.startswith("test."):
            nodo = manifest["nodes"].get(uid, {})
            modelo = _modelo(manifest, nodo.get("attached_node", "")) or {}
            meta = nodo.get("test_metadata") or {}
            filas.append(
                {
                    "modelo": modelo.get("name", "?"),
                    "capa": modelo.get("schema", "?"),
                    "columna": nodo.get("column_name") or "(tabla)",
                    "prueba": meta.get("name") or nodo.get("name", uid),
                    "estado": estado,
                }
            )
        elif uid.startswith("unit_test."):
            nodo = manifest.get("unit_tests", {}).get(uid, {})
            nombre = nodo.get("model", "?")
            modelo = next(
                (n for n in manifest["nodes"].values() if n.get("name") == nombre), {}
            )
            filas.append(
                {
                    "modelo": nombre,
                    "capa": modelo.get("schema", "?"),
                    "columna": "(tabla)",
                    "prueba": f"{nodo.get('name', uid)} (unitaria)",
                    "estado": estado,
                }
            )
    return filas


def resumen(filas):
    pasadas = sum(1 for f in filas if f["estado"] == "PASS")
    return {
        "total": len(filas),
        "pass": pasadas,
        "fallidas": len(filas) - pasadas,
        "modelos": len({f["modelo"] for f in filas}),
    }


def _buscar(manifest, esquema, nombre):
    for candidato in (nombre, f"{esquema}_{nombre}"):
        for uid, nodo in manifest["nodes"].items():
            if nodo.get("resource_type") == "model" and nodo["name"] == candidato:
                return uid, nodo
    return None, None


def _fuentes(manifest, uid, vistos=None):
    vistos = vistos if vistos is not None else set()
    fuentes = []
    for padre in manifest["parent_map"].get(uid, []):
        if padre in vistos:
            continue
        vistos.add(padre)
        if padre.startswith("source."):
            _, _, esquema, tabla = padre.split(".", 3)
            fuentes.append(f"{esquema}.{tabla}")
        else:
            fuentes.extend(_fuentes(manifest, padre, vistos))
    return fuentes


def linaje(manifest, modelo):
    """[(columna, [nodos desde la columna hasta la fuente])] siguiendo «de esquema.modelo.columna»."""
    uid, nodo = _buscar(manifest, "", modelo)
    resultado = []
    for columna, info in nodo["columns"].items():
        cadena, actual_uid, descripcion = [f"{modelo}.{columna}"], uid, info.get("description", "")
        for _ in range(10):
            hallado = ORIGEN.search(descripcion)
            if not hallado:
                break
            esquema, nombre, col = hallado.groups()
            sig_uid, sig = _buscar(manifest, esquema, nombre)
            if not sig:
                break
            actual_uid = sig_uid
            cadena.append(f"{sig['name']}.{col}")
            descripcion = sig["columns"].get(col, {}).get("description", "")
        # Sin «de esquema.modelo.columna»: usa el modelo que la descripción nombra («con silver.ipc»).
        nombrado = MODELO.search(descripcion)
        sig_uid, sig = _buscar(manifest, *nombrado.groups()) if nombrado else (None, None)
        if sig and sig_uid != actual_uid:
            actual_uid = sig_uid
            cadena.append(sig["name"])
        if len(cadena) > 1:
            cadena.extend(dict.fromkeys(_fuentes(manifest, actual_uid)))
        resultado.append((columna, cadena))
    return resultado

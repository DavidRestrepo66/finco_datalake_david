"""Extractor de series de FRED (Federal Reserve Bank of St. Louis) como CSV público, sin API key."""

import csv
import io
import time

import requests

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
TIMEOUT_SEGUNDOS = 30
REINTENTOS = 3
ESPERA_INICIAL_SEGUNDOS = 1


class ExtraccionError(Exception):
    """FRED siguió fallando después de todos los reintentos."""


def extraer_fred(serie, desde, sesion=None, espera=time.sleep):
    """Filas de la serie `serie` desde `desde` (ISO), tal como las entrega FRED: todo como texto."""
    sesion = sesion or requests.Session()
    intentos = REINTENTOS + 1
    for intento in range(1, intentos + 1):
        try:
            r = sesion.get(URL, params={"id": serie, "cosd": desde}, timeout=TIMEOUT_SEGUNDOS)
            r.raise_for_status()
            return list(csv.DictReader(io.StringIO(r.text)))
        except requests.RequestException as e:
            if intento == intentos:
                raise ExtraccionError(f"no se pudo extraer {serie} de FRED tras {intentos} intentos: {e}") from e
            espera(ESPERA_INICIAL_SEGUNDOS * 2 ** (intento - 1))

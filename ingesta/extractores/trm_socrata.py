"""Extractor de la TRM desde la API Socrata de datos.gov.co (dataset ceyp-9c7c)."""

import requests

URL = "https://www.datos.gov.co/resource/ceyp-9c7c.json"
FECHA_INICIO = "2020-01-01"
TAM_PAGINA = 1000
TIMEOUT_SEGUNDOS = 30


def extraer_trm(sesion=None, tam_pagina=TAM_PAGINA):
    """Devuelve todas las filas de la TRM desde FECHA_INICIO, tal como las entrega la fuente."""
    sesion = sesion or requests.Session()
    filas = []
    offset = 0
    while True:
        params = {
            "$where": f"vigenciadesde >= '{FECHA_INICIO}T00:00:00'",
            "$order": "vigenciadesde",
            "$limit": tam_pagina,
            "$offset": offset,
        }
        respuesta = sesion.get(URL, params=params, timeout=TIMEOUT_SEGUNDOS)
        respuesta.raise_for_status()
        pagina = respuesta.json()
        filas.extend(pagina)
        if len(pagina) < tam_pagina:
            return filas
        offset += tam_pagina

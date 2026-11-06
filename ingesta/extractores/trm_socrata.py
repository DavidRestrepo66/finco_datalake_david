"""Extractor de la TRM desde la API Socrata de datos.gov.co (dataset ceyp-9c7c)."""

import logging
import time

import requests

URL = "https://www.datos.gov.co/resource/ceyp-9c7c.json"
FECHA_INICIO = "2020-01-01"
TAM_PAGINA = 1000
TIMEOUT_SEGUNDOS = 30
REINTENTOS = 3  # además del primer intento
ESPERA_INICIAL_SEGUNDOS = 1  # se duplica en cada reintento: 1, 2, 4

log = logging.getLogger("ingesta.trm")


class ExtraccionError(Exception):
    """La fuente siguió fallando después de todos los reintentos."""


def _pedir_pagina(sesion, params, espera, url=URL):
    """Pide una página; ante fallas de red o HTTP reintenta con espera creciente."""
    intentos = REINTENTOS + 1
    for intento in range(1, intentos + 1):
        try:
            respuesta = sesion.get(url, params=params, timeout=TIMEOUT_SEGUNDOS)
            respuesta.raise_for_status()
            return respuesta.json()
        except requests.RequestException as e:
            if intento == intentos:
                log.error("TRM: falló el intento %d de %d, sin más reintentos: %s", intento, intentos, e)
                raise ExtraccionError(f"no se pudo extraer la TRM tras {intentos} intentos: {e}") from e
            pausa = ESPERA_INICIAL_SEGUNDOS * 2 ** (intento - 1)
            log.warning("TRM: falló el intento %d de %d (%s); reintento en %ss", intento, intentos, e, pausa)
            espera(pausa)


def extraer_socrata(url, where, order, sesion=None, tam_pagina=TAM_PAGINA, espera=time.sleep):
    """Todas las filas de un dataset Socrata que cumplen `where`, paginadas y ordenadas por `order`."""
    sesion = sesion or requests.Session()
    filas = []
    offset = 0
    while True:
        params = {"$where": where, "$order": order, "$limit": tam_pagina, "$offset": offset}
        pagina = _pedir_pagina(sesion, params, espera, url)
        filas.extend(pagina)
        if len(pagina) < tam_pagina:
            return filas
        offset += tam_pagina


def extraer_trm(sesion=None, tam_pagina=TAM_PAGINA, espera=time.sleep, desde=FECHA_INICIO):
    """Devuelve las filas de la TRM con vigenciadesde >= `desde` (por defecto FECHA_INICIO), tal como las entrega la fuente."""
    return extraer_socrata(
        URL, f"vigenciadesde >= '{desde}T00:00:00'", "vigenciadesde", sesion, tam_pagina, espera
    )

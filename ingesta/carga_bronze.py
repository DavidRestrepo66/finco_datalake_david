"""Carga de las fuentes a la capa bronze (lakehouse híbrido).

Bronze guarda el dato original (como texto, sin transformar) más tres metadatos:
fuente, fecha-hora de carga e identificador de lote. Cada ejecución crea un lote nuevo
y nunca modifica los lotes anteriores.

El lote se escribe primero como archivo Parquet (el lake, fuente de verdad inmutable)
y se replica en PostgreSQL (`bronze.*`) para que dbt construya silver y gold.

El IPC y la tasa de intervención llegan como CSV descargados a mano (D-10). Su lote
guarda además el nombre del archivo y su hash SHA-256; en PostgreSQL cada fila del CSV
se guarda completa como `jsonb` (texto original), porque el formato del Banco puede
cambiar de columnas sin que bronze tenga que cambiar.
"""

import datetime as dt
import logging
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import psycopg
import pyarrow as pa
import pyarrow.parquet as pq
from psycopg import sql
from psycopg.types.json import Jsonb

FUENTE_TRM = "datos.gov.co/ceyp-9c7c"
FUENTE_IPC = "banrep.gov.co/ipc (CSV)"
FUENTE_TASA = "banrep.gov.co/tasa-intervencion (CSV)"
RAIZ_LAKE = Path(os.getenv("LAKE_DIR", "data/bronze"))
RAIZ_FUENTES = Path("data/fuentes")

# conjunto -> (fuente, ruta por defecto del CSV versionado)
CONJUNTOS_CSV = {
    "ipc": (FUENTE_IPC, RAIZ_FUENTES / "ipc.csv"),
    "tasa_intervencion": (FUENTE_TASA, RAIZ_FUENTES / "tasa_intervencion.csv"),
}
USO = "uso: python -m ingesta.carga_bronze trm [--completo] | ipc [ruta.csv] | tasa [ruta.csv] | usura | brent | fed | cdt"


# La TRM se pide desde (última vigencia cargada − margen): el solape recoge correcciones recientes de la
# fuente y es inocuo porque silver deja, por día, el lote más reciente.
MARGEN_DIAS = 7


def _extraer_usura(conn):
    from ingesta.extractores.trm_socrata import FECHA_INICIO, extraer_socrata

    return extraer_socrata(
        "https://www.datos.gov.co/resource/pare-7x5i.json",
        f"vigencia_hasta >= '{FECHA_INICIO}T00:00:00'",
        "vigencia_desde, modalidad",
    )


def ultima_fecha_cdt(conn):
    """Mayor `fechacorte` ya cargada en bronze.cdt_raw, o None si está vacía."""
    fila = conn.execute("select max((fila->>'fechacorte')::timestamp)::date from bronze.cdt_raw").fetchone()
    return fila[0]


def _extraer_cdt(conn):
    """Tasa de captación de CDT a 90 días (Superfinanciera), solo desde la última fecha cargada menos el margen."""
    from ingesta.extractores.trm_socrata import extraer_socrata

    desde = desde_incremental(ultima_fecha_cdt(conn))
    return extraer_socrata(
        "https://www.datos.gov.co/resource/axk9-g2nh.json",
        f"descripcion = 'A 90 DIAS' AND fechacorte >= '{desde}T00:00:00'",
        "fechacorte, codigoentidad, tipoentidad, subcuenta",
        tam_pagina=10000,
    )


def _extraer_fred(serie):
    def extraer(conn):
        from ingesta.extractores.fred import extraer_fred
        from ingesta.extractores.trm_socrata import FECHA_INICIO

        return extraer_fred(serie, FECHA_INICIO)

    return extraer


# nombre -> (fuente, extractor(conn) -> filas crudas). Cada uno se carga como lote nuevo en bronze.<nombre>_raw.
FUENTES_API = {
    "usura": ("datos.gov.co/pare-7x5i", _extraer_usura),
    "brent": ("fred.stlouisfed.org/DCOILBRENTEU", _extraer_fred("DCOILBRENTEU")),
    "fed": ("fred.stlouisfed.org/FEDFUNDS", _extraer_fred("FEDFUNDS")),
    "cdt": ("datos.gov.co/axk9-g2nh (CDT a 90 días)", _extraer_cdt),
}


def conectar():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "finco"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        dbname=os.getenv("POSTGRES_DB", "finco"),
        connect_timeout=5,
    )


def crear_tablas(conn):
    conn.execute(
        """
        create table if not exists bronze.trm_raw (
            id bigserial primary key,
            lote_id uuid not null,
            fuente text not null,
            cargado_en timestamptz not null default now(),
            valor text,
            vigenciadesde text,
            vigenciahasta text
        )
        """
    )
    for nombre in FUENTES_API:
        crear_tabla_api(conn, nombre)
    for conjunto in CONJUNTOS_CSV:
        conn.execute(
            sql.SQL(
                """
                create table if not exists bronze.{} (
                    id bigserial primary key,
                    lote_id uuid not null,
                    fuente text not null,
                    cargado_en timestamptz not null default now(),
                    archivo text not null,
                    hash_archivo text not null,
                    numero_fila integer not null,
                    fila jsonb not null
                )
                """
            ).format(sql.Identifier(f"{conjunto}_raw"))
        )


def crear_tabla_api(conn, nombre):
    conn.execute(
        sql.SQL(
            """
            create table if not exists bronze.{} (
                id bigserial primary key,
                lote_id uuid not null,
                fuente text not null,
                cargado_en timestamptz not null default now(),
                fila jsonb not null
            )
            """
        ).format(sql.Identifier(f"{nombre}_raw"))
    )


def escribir_parquet(nombre, filas, lote_id, fuente, cargado_en, raiz=RAIZ_LAKE, meta=None):
    """Escribe el lote como Parquet en <raiz>/<nombre>/lote_id=<lote>/datos.parquet.

    `meta` agrega metadatos constantes del lote (por ejemplo archivo y hash del CSV).
    """
    raiz = Path(raiz)
    columnas = sorted({k for f in filas for k in f})
    datos = {c: [f.get(c) for f in filas] for c in columnas}
    datos["lote_id"] = [str(lote_id)] * len(filas)
    datos["fuente"] = [fuente] * len(filas)
    datos["cargado_en"] = [cargado_en] * len(filas)
    for clave, valor in (meta or {}).items():
        datos[clave] = [valor] * len(filas)
    ruta = raiz / nombre / f"lote_id={lote_id}" / "datos.parquet"
    ruta.parent.mkdir(parents=True, exist_ok=False)  # un lote nunca se sobrescribe
    pq.write_table(pa.table(datos), ruta)
    return ruta


def cargar_trm(conn, filas, lote_id=None, cargado_en=None):
    """Inserta las filas en un lote nuevo y devuelve su identificador."""
    lote_id = lote_id or uuid.uuid4()
    cargado_en = cargado_en or datetime.now(UTC)
    with conn.cursor() as cur:
        cur.executemany(
            "insert into bronze.trm_raw (lote_id, fuente, cargado_en, valor, vigenciadesde, vigenciahasta)"
            " values (%s, %s, %s, %s, %s, %s)",
            [
                (lote_id, FUENTE_TRM, cargado_en, f.get("valor"), f.get("vigenciadesde"), f.get("vigenciahasta"))
                for f in filas
            ],
        )
    return lote_id


def cargar_csv(conn, conjunto, filas, meta, lote_id=None, cargado_en=None):
    """Inserta las filas de un CSV en bronze.<conjunto>_raw como lote nuevo y devuelve su id."""
    fuente, _ = CONJUNTOS_CSV[conjunto]
    lote_id = lote_id or uuid.uuid4()
    cargado_en = cargado_en or datetime.now(UTC)
    with conn.cursor() as cur:
        cur.executemany(
            sql.SQL(
                "insert into bronze.{} (lote_id, fuente, cargado_en, archivo, hash_archivo, numero_fila, fila)"
                " values (%s, %s, %s, %s, %s, %s, %s)"
            ).format(sql.Identifier(f"{conjunto}_raw")),
            [
                (lote_id, fuente, cargado_en, meta["archivo"], meta["hash_archivo"], n, Jsonb(f))
                for n, f in enumerate(filas, start=1)
            ],
        )
    return lote_id


def ultima_vigencia(conn):
    """Mayor `vigenciadesde` ya cargada en bronze.trm_raw, o None si está vacía."""
    fila = conn.execute("select max(vigenciadesde::timestamp)::date from bronze.trm_raw").fetchone()
    return fila[0]


def desde_incremental(ultima):
    """Fecha (ISO) desde la que pedir la TRM: todo si no hay carga previa; si no, la última menos el margen."""
    from ingesta.extractores.trm_socrata import FECHA_INICIO

    if ultima is None:
        return FECHA_INICIO
    return max(ultima - dt.timedelta(days=MARGEN_DIAS), dt.date.fromisoformat(FECHA_INICIO)).isoformat()


def desde_trm(completo):
    """Desde qué fecha pedir la TRM: todo con `completo`, o solo lo nuevo según lo ya cargado."""
    from ingesta.extractores.trm_socrata import FECHA_INICIO

    if completo:
        return FECHA_INICIO
    with conectar() as conn:
        crear_tablas(conn)
        return desde_incremental(ultima_vigencia(conn))


def cargar_api(conn, nombre, filas, fuente, lote_id=None, cargado_en=None):
    """Inserta las filas crudas (jsonb, texto) en bronze.<nombre>_raw como lote nuevo y devuelve su id."""
    lote_id = lote_id or uuid.uuid4()
    cargado_en = cargado_en or datetime.now(UTC)
    with conn.cursor() as cur:
        cur.executemany(
            sql.SQL("insert into bronze.{} (lote_id, fuente, cargado_en, fila) values (%s, %s, %s, %s)").format(
                sql.Identifier(f"{nombre}_raw")
            ),
            [(lote_id, fuente, cargado_en, Jsonb(f)) for f in filas],
        )
    return lote_id


def main_api(nombre):
    from ingesta.extractores.fred import ExtraccionError as ErrorFred
    from ingesta.extractores.trm_socrata import ExtraccionError as ErrorSocrata

    fuente, extraer = FUENTES_API[nombre]
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    with conectar() as conn:
        crear_tablas(conn)
        try:
            filas = extraer(conn)
        except (ErrorSocrata, ErrorFred) as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        lote = uuid.uuid4()
        ahora = datetime.now(UTC)
        ruta = escribir_parquet(nombre, filas, lote, fuente, ahora)
        cargar_api(conn, nombre, filas, fuente, lote, ahora)
    print(f"{nombre}: {len(filas)} registros en {ruta} y en bronze.{nombre}_raw, lote {lote}")
    return 0


def main_csv(conjunto, ruta):
    from ingesta.extractores.banrep import leer_csv

    fuente, ruta_defecto = CONJUNTOS_CSV[conjunto]
    ruta = Path(ruta or ruta_defecto)
    if not ruta.is_file():
        print(f"error: no existe el archivo {ruta}", file=sys.stderr)
        return 1
    try:
        filas, meta = leer_csv(ruta)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    lote = uuid.uuid4()
    ahora = datetime.now(UTC)
    ruta_lote = escribir_parquet(conjunto, filas, lote, fuente, ahora, RAIZ_LAKE, meta)
    with conectar() as conn:
        crear_tablas(conn)
        cargar_csv(conn, conjunto, filas, meta, lote, ahora)
    print(f"{conjunto}: {len(filas)} registros de {meta['archivo']} en {ruta_lote} y en bronze.{conjunto}_raw, lote {lote}")
    return 0


def main(argv):
    from ingesta.extractores.trm_socrata import ExtraccionError, extraer_trm

    if len(argv) in (1, 2) and argv[0] in ("ipc", "tasa"):
        conjunto = "ipc" if argv[0] == "ipc" else "tasa_intervencion"
        return main_csv(conjunto, argv[1] if len(argv) == 2 else None)
    if len(argv) == 1 and argv[0] in FUENTES_API:
        return main_api(argv[0])
    if argv not in (["trm"], ["trm", "--completo"]):
        print(USO, file=sys.stderr)
        return 2
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        desde = desde_trm(completo=argv == ["trm", "--completo"])
        filas = extraer_trm(desde=desde)
    except ExtraccionError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    lote = uuid.uuid4()
    ahora = datetime.now(UTC)
    ruta = escribir_parquet("trm", filas, lote, FUENTE_TRM, ahora)
    with conectar() as conn:
        crear_tablas(conn)
        cargar_trm(conn, filas, lote, ahora)
    print(f"TRM desde {desde}: {len(filas)} registros en {ruta} y en bronze.trm_raw, lote {lote}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

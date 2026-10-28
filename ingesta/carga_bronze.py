"""Carga de las fuentes a la capa bronze (lakehouse híbrido).

Bronze guarda el dato original (como texto, sin transformar) más tres metadatos:
fuente, fecha-hora de carga e identificador de lote. Cada ejecución crea un lote nuevo
y nunca modifica los lotes anteriores.

El lote se escribe primero como archivo Parquet (el lake, fuente de verdad inmutable)
y se replica en PostgreSQL (`bronze.*`) para que dbt construya silver y gold.
"""

import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import psycopg
import pyarrow as pa
import pyarrow.parquet as pq

FUENTE_TRM = "datos.gov.co/ceyp-9c7c"
RAIZ_LAKE = Path(os.getenv("LAKE_DIR", "data/bronze"))


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


def escribir_parquet(nombre, filas, lote_id, fuente, cargado_en, raiz=RAIZ_LAKE):
    """Escribe el lote como Parquet en <raiz>/<nombre>/lote_id=<lote>/datos.parquet."""
    raiz = Path(raiz)
    columnas = sorted({k for f in filas for k in f})
    datos = {c: [f.get(c) for f in filas] for c in columnas}
    datos["lote_id"] = [str(lote_id)] * len(filas)
    datos["fuente"] = [fuente] * len(filas)
    datos["cargado_en"] = [cargado_en] * len(filas)
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


def main(argv):
    from ingesta.extractores.trm_socrata import extraer_trm

    if argv != ["trm"]:
        print("uso: python -m ingesta.carga_bronze trm", file=sys.stderr)
        return 2
    filas = extraer_trm()
    lote = uuid.uuid4()
    ahora = datetime.now(UTC)
    ruta = escribir_parquet("trm", filas, lote, FUENTE_TRM, ahora)
    with conectar() as conn:
        crear_tablas(conn)
        cargar_trm(conn, filas, lote, ahora)
    print(f"TRM: {len(filas)} registros en {ruta} y en bronze.trm_raw, lote {lote}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

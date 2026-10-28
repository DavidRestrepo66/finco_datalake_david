"""Carga de las fuentes a la capa bronze de PostgreSQL.

Bronze guarda el dato original (como texto, sin transformar) más tres metadatos:
fuente, fecha-hora de carga e identificador de lote. Cada ejecución crea un lote nuevo
y nunca modifica los lotes anteriores.
"""

import os
import sys
import uuid

import psycopg

FUENTE_TRM = "datos.gov.co/ceyp-9c7c"


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


def cargar_trm(conn, filas):
    """Inserta las filas en un lote nuevo y devuelve su identificador."""
    lote_id = uuid.uuid4()
    with conn.cursor() as cur:
        cur.executemany(
            "insert into bronze.trm_raw (lote_id, fuente, valor, vigenciadesde, vigenciahasta)"
            " values (%s, %s, %s, %s, %s)",
            [
                (lote_id, FUENTE_TRM, f.get("valor"), f.get("vigenciadesde"), f.get("vigenciahasta"))
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
    with conectar() as conn:
        crear_tablas(conn)
        lote = cargar_trm(conn, filas)
    print(f"TRM: {len(filas)} registros cargados en bronze.trm_raw, lote {lote}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

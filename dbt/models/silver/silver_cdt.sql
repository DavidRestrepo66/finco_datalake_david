{{ config(alias='cdt') }}

-- Tasa de captación de CDT a 90 días por entidad y fecha de corte.
-- Bronze trae filas crudas (jsonb, texto); aquí se tipan. Si una entidad aparece dos veces
-- el mismo día en lotes distintos (por el margen de la carga incremental), gana el lote más reciente.
with tipada as (
    select
        id,
        lote_id,
        cargado_en,
        fila->>'tipoentidad' as tipo_entidad,
        fila->>'codigoentidad' as codigo_entidad,
        fila->>'nombreentidad' as entidad,
        fila->>'subcuenta' as subcuenta,
        (fila->>'fechacorte')::timestamp::date as fecha,
        (fila->>'tasa')::numeric as tasa,
        (fila->>'monto')::numeric as monto
    from {{ source('bronze', 'cdt_raw') }}
),

ordenada as (
    select
        *,
        row_number() over (
            partition by tipo_entidad, codigo_entidad, subcuenta, fecha
            order by cargado_en desc, id desc
        ) as posicion
    from tipada
)

select fecha, tipo_entidad, codigo_entidad, entidad, subcuenta, tasa, monto, lote_id, cargado_en
from ordenada
where posicion = 1

{{ config(alias='usura') }}

-- Tasa de usura por modalidad y periodo de vigencia (todas las modalidades).
-- Bronze guarda la fila como jsonb (texto); aquí se tipa y la tasa pierde el '%'.
-- Si una vigencia de una modalidad aparece en dos lotes, gana el lote más reciente.
with tipada as (
    select
        id,
        lote_id,
        cargado_en,
        trim(fila->>'modalidad') as modalidad,
        (fila->>'vigencia_desde')::timestamp::date as vigencia_desde,
        (fila->>'vigencia_hasta')::timestamp::date as vigencia_hasta,
        trim_scale(replace(trim(fila->>'interes_bancario_corriente'), '%', '')::numeric) as tasa_usura
    from {{ source('bronze', 'usura_raw') }}
),

ordenada as (
    select
        *,
        row_number() over (
            partition by modalidad, vigencia_desde
            order by cargado_en desc, id desc
        ) as posicion
    from tipada
)

select modalidad, vigencia_desde, vigencia_hasta, tasa_usura, lote_id, cargado_en
from ordenada
where posicion = 1

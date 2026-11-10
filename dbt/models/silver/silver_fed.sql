{{ config(alias='fed') }}

-- Tasa de fondos federales mensual (FRED, FEDFUNDS), en porcentaje.
-- Si un mes aparece en dos lotes, gana el lote más reciente.
with tipada as (
    select
        id,
        lote_id,
        cargado_en,
        date_trunc('month', (fila->>'observation_date')::date)::date as mes,
        nullif(trim(fila->>'FEDFUNDS'), '')::numeric as fed_funds
    from {{ source('bronze', 'fed_raw') }}
),

ordenada as (
    select
        *,
        row_number() over (partition by mes order by cargado_en desc, id desc) as posicion
    from tipada
)

select mes, fed_funds, lote_id, cargado_en
from ordenada
where posicion = 1 and fed_funds is not null

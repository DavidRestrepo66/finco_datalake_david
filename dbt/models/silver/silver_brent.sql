{{ config(alias='brent') }}

-- Brent diario en dólares por barril (FRED, DCOILBRENTEU).
-- Los días sin dato llegan como cadena vacía y se excluyen.
-- Si un día aparece en dos lotes, gana el lote más reciente.
with tipada as (
    select
        id,
        lote_id,
        cargado_en,
        (fila->>'observation_date')::date as fecha,
        nullif(trim(fila->>'DCOILBRENTEU'), '')::numeric as brent
    from {{ source('bronze', 'brent_raw') }}
),

ordenada as (
    select
        *,
        row_number() over (partition by fecha order by cargado_en desc, id desc) as posicion
    from tipada
)

select fecha, brent, lote_id, cargado_en
from ordenada
where posicion = 1 and brent is not null

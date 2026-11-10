-- Hecho mensual de indicadores: una fila por mes desde enero de 2020.
-- IPC (índice), inflación anual, tasa de intervención y tasa de usura de consumo y ordinario
-- vigentes el último día del mes, Brent promedio del mes y tasa de la Fed del mes.
-- El IPC de 2019 solo se usa para calcular la inflación anual de 2020.
-- CDT a 90 días: promedio mensual de la tasa ponderado por monto.
-- Usura, Brent, Fed y CDT quedan nulos en los meses sin dato.
with ipc as (
    select
        mes as anio_mes,
        indice as ipc,
        round((indice / lag(indice, 12) over (order by mes) - 1) * 100, 2) as inflacion_anual
    from {{ ref('silver_ipc') }}
),

brent_mensual as (
    select
        date_trunc('month', fecha)::date as anio_mes,
        round(avg(brent), 2) as brent_promedio
    from {{ ref('silver_brent') }}
    group by 1
),

cdt_mensual as (
    select
        date_trunc('month', fecha)::date as anio_mes,
        round(sum(tasa * monto) / nullif(sum(monto), 0), 2) as tasa_cdt_90
    from {{ ref('silver_cdt') }}
    group by 1
)

select
    ipc.anio_mes,
    ipc.ipc,
    ipc.inflacion_anual,
    tasa.tasa as tasa_vigente,
    usura.tasa_usura as tasa_usura_consumo,
    brent_mensual.brent_promedio,
    fed.fed_funds,
    cdt_mensual.tasa_cdt_90
from ipc
left join {{ ref('silver_tasa_intervencion') }} as tasa
    on (ipc.anio_mes + interval '1 month' - interval '1 day')::date
       between tasa.fecha_inicio and tasa.fecha_fin
left join {{ ref('silver_usura') }} as usura
    on usura.modalidad = 'CONSUMO Y ORDINARIO'
   and (ipc.anio_mes + interval '1 month' - interval '1 day')::date
       between usura.vigencia_desde and usura.vigencia_hasta
left join brent_mensual
    on brent_mensual.anio_mes = ipc.anio_mes
left join {{ ref('silver_fed') }} as fed
    on fed.mes = ipc.anio_mes
left join cdt_mensual
    on cdt_mensual.anio_mes = ipc.anio_mes
where ipc.anio_mes >= date '2020-01-01'

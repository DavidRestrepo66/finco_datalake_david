-- S3: las vigencias de usura de una misma modalidad no se solapan. Devuelve filas (y falla) si hay solape.
select a.modalidad, a.vigencia_desde, a.vigencia_hasta, b.vigencia_desde as otra_desde, b.vigencia_hasta as otra_hasta
from {{ ref('silver_usura') }} as a
join {{ ref('silver_usura') }} as b
    on a.modalidad = b.modalidad
   and a.vigencia_desde < b.vigencia_desde
   and b.vigencia_desde <= a.vigencia_hasta

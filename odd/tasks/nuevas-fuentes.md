# Nuevas fuentes: usura, Brent, Fed y CDT 90 días
Rama feat/nuevas-fuentes (sobre #27 y #28). Hasta el mart y la app; un commit por fuente.

## Specs
- S1: «quiero agregar mas fuentes» — elegidas: tasa de usura (HU-15), Brent y tasa de la Fed (HU-16), tasas de captación/CDT.
- S2: «Hasta el mart y la app (completo)»: bronze, silver, gold (columnas en mart_mensual) y gráfico/correlación en Análisis.
- S3: cada mes desde 2020-01 tiene tasa de usura de «CONSUMO Y ORDINARIO», brent_promedio y fed_funds; vigencias de usura sin solape por modalidad.
- S4: Análisis muestra la correlación entre la TRM y el Brent y compara la usura con la tasa de intervención.
- S5: CDT: filtrar por plazo («A 90 DIAS») y fecha al extraer (2,1 M de filas).

## Tasks
- T1 (S1,S5) infraestructura de ingesta de fuentes API + pipeline: pendiente
- T2 (S3) usura: hecho (dbt; sin commit)
- T3 (S3) Brent y Fed: hecho (dbt; sin commit)
- T4 (S5) CDT 90: pendiente
- T5 (S4) app/Análisis: pendiente
- T6 docs, manual, trazabilidad: pendiente

## Log
L1: "buano ahora quiero agregar mas fuentes"
L2: fuentes elegidas: usura, Brent+Fed, captación/CDT; alcance completo hasta mart y app; rama apilada sobre #27 + #28, un commit por fuente.

# Plan completo finco: del MVP al cierre (HU-06 a HU-14, HU-02 y documentos)
Continúa `mvp-datawarehouse.md` (HU-01, 03, 04, 05 y HU-07 ya entregadas). Fuente: `06-product-backlog.md`.
Cadena de PR apilados a main; cada PR ≤ 400 líneas; el PO mergea en orden.

## Specs
- S1: HU-06 "Reintentos y registro de errores en la TRM" (`06-product-backlog.md`, escenarios de la HU-06).
- S2: HU-08 "Dado que bronze contiene los cambios de tasa con su fecha de decisión Cuando ejecuto "dbt build" sobre silver Entonces cada registro tiene fecha_inicio y fecha_fin de vigencia Y los periodos de vigencia no se solapan". IPC por mes.
- S3: HU-09 "Entonces existe una dimensión de fecha, un hecho diario de TRM y un hecho mensual de indicadores Y el mart mensual tiene una fila por mes con TRM promedio, IPC y tasa vigente".
- S4: HU-10 "Entonces el test relationships entre cada hecho y la dimensión de fecha pasa" y "Entonces el test relationships falla e identifica el registro huérfano".
- S5: HU-11 "Entonces el grafo de linaje muestra el camino desde las tablas bronze hasta el mart Y cada columna del mart tiene una descripción que indica su origen".
- S6: HU-12 "Cuando ejecuto "docker compose run --rm pipeline" Entonces se ejecutan en orden la ingesta de las 2 fuentes y "dbt build" Y el script informa la duración total y termina con código 0 si todo fue exitoso" y "Entonces el pipeline no ejecuta "dbt build" Y termina con código distinto de 0 indicando qué etapa falló".
- S7: HU-13 "Entonces veo al menos 3 visualizaciones: evolución de la TRM, inflación anual y tasa de intervención frente a inflación Y puedo filtrar por rango de fechas Y el tablero fue creado automáticamente por un script contra la API de Metabase, sin pasos manuales".
- S8: HU-14 "Entonces veo una vista previa con solo los meses de 2023 Y al pedir la descarga obtengo un archivo CSV con exactamente esas filas" y "Entonces la aplicación muestra un mensaje indicando que no hay datos Y no genera un archivo vacío". Tecnología: Streamlit (decisión del usuario).
- S9: HU-02 "Instalar y ejecutar siguiendo solo el README (solo Docker)". Documentos T-02 a T-09 del backlog (casos de uso, arquitectura, ER y ADR, trazabilidad, plan de pruebas, evidencia, manuales, retrospectiva).

## Tasks
- T1 (S1) HU-06 reintentos y errores del extractor TRM. [x] rama feature/HU-06-reintentos-trm
- T2 (S3, S4) Gold con la TRM: dim_fecha, hecho diario de TRM, pruebas relationships (HU-09 parte A, HU-10). [ ] sobre HU-07
- T3 (S6) Pipeline de un comando en Docker: `pipeline.py`, `verificar.py`, servicio `pipeline` (HU-12). [ ]
- T4 (S2) IPC y tasa en silver (HU-08). [ ] BLOQUEADA: faltan los CSV reales que descarga el usuario en `data/fuentes/`
- T5 (S3, S4) Hecho mensual y mart mensual (HU-09 parte B, HU-10). [ ] depende de T4
- T6 (S8) App web Streamlit de consulta y descarga (HU-14). [ ] depende de T2; mart mensual cuando exista T5
- T7 (S7) Tablero Metabase creado por script contra su API (HU-13). [ ] depende de T5
- T8 (S5) Linaje: descripciones de columnas y dbt docs (HU-11). [ ] depende de T5
- T9 (S9) Documentos T-02 a T-08, trazabilidad y README para HU-02. [ ] al final de cada HU lo que le toque

## Log
- L1: "sigue con todo el proceso y tareas para llevar a cabo el proyecto"
- L2: CSV del Banco: "Los descargo yo y los dejo en data/fuentes/ (Recomendada)". HU-14: "Streamlit (Recomendada)". PR: "Apilados; activo borrar rama al mergear (Recomendada)".

# MVP data warehouse finco (HU-01, 03, 04, 05)
Orden fijado por el PO: Docker, luego ingesta. Fuente: `06-product-backlog.md`.

## Specs
- S1: HU-01 "Cuando ejecuto `docker compose up -d` Entonces PostgreSQL acepta conexiones con los esquemas bronze, silver y gold creados Y Metabase responde en el puerto configurado".
- S2: Se copia `.env.example` a `.env`; sin secretos reales en el repositorio.
- S3: HU-03 TRM desde 2020-01-01 en bronze, con fuente, fecha-hora de carga e identificador de lote (API ceyp-9c7c).
- S4: HU-04/05 IPC (desde 2019-01) y tasa de intervención desde CSV versionado en el repositorio, con metadatos de lote (nombre de archivo y hash).

## Tasks
- T1 (S1, S2) Docker Compose: PostgreSQL con esquemas + Metabase. [x]
- T2 (S3) Extractor TRM y carga a bronze. [ ]
- T3 (S4) Cargador CSV de IPC y tasa. [ ]

## Log
- L1: "no, quiero que lo hagamos en orden" -> orden del plan de sprints, MVP primero.

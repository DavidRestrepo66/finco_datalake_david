# Plan restante hasta la entrega final (20 nov)
Fuentes: `02-planeacion-cronograma.md` (Gantt) y `06-product-backlog.md` (criterios). Complementa `mvp-datawarehouse.md`.
Estado al 2026-10-29: hechas HU-01, 03, 07, 10, 12, 14; HU-04/05 sin CSV reales; HU-09 solo parte diaria.

## Specs
- S1: HU-04/05 "el CSV de IPC exportado del Banco de la República (desde enero de 2019) está versionado en el repositorio" y "el CSV de tasa de intervención exportado del Banco de la República está versionado en el repositorio".
- S2: HU-08 "cada registro tiene fecha_inicio y fecha_fin de vigencia Y los periodos de vigencia no se solapan".
- S3: HU-09 "existe una dimensión de fecha, un hecho diario de TRM y un hecho mensual de indicadores Y el mart mensual tiene una fila por mes con TRM promedio, IPC y tasa vigente".
- S4: HU-12 "se ejecutan en orden la ingesta de las 2 fuentes y "dbt build"" (hoy solo cubre TRM).
- S5: HU-06 "reintenta al menos 3 veces con espera creciente Y si todos los intentos fallan, registra el error en el log y termina con código distinto de 0".
- S6: HU-11 "el grafo de linaje muestra el camino desde las tablas bronze hasta el mart Y cada columna del mart tiene una descripción que indica su origen".
- S7: HU-13 "al menos 3 visualizaciones: evolución de la TRM, inflación anual y tasa de intervención frente a inflación Y puedo filtrar por rango de fechas Y el tablero fue creado automáticamente por un script contra la API de Metabase, sin pasos manuales".
- S8: HU-02 "Dado una máquina con solo Docker instalado y sin datos previos del proyecto Cuando sigo los pasos del README en orden Entonces el pipeline termina sin errores Y puedo abrir el tablero con datos cargados y usar la aplicación web".
- S9: Tareas de documentación T-02 a T-09 (backlog, Épica 7). `docs/*.md` están hoy vacíos.

## Tasks (ID, specs, responsable, fecha Gantt)
### Sprint 2 (hasta 1 nov)
- T1 (S1) Versionar CSV reales de IPC y tasa en `data/fuentes/` y cargarlos. David, 30 oct–1 nov. [x] cargados en bronze el 29 oct (867 y 10485 filas); falta commit de los CSV.
- T2 (S9) T-02 Casos de uso y flujos (`docs/casos-uso.md`). David, hasta 8 nov. [x] commit docs: casos de uso y flujos.
- T3 (S9) T-03 Diagrama de arquitectura. Andrey, 29 oct–1 nov. [x] docs/arquitectura.md
- T4 (S9) T-04 ER de 3 capas y ADR Opción B. Juan, 26 oct–1 nov. [x] docs/modelo-datos.md
### Sprint 3 (2–8 nov)
- T5 (S2) HU-08 Silver de IPC y tasa por vigencia. Juan, 3–6 nov. [ ] depende T1
- T6 (S3) HU-09 Completar: hecho mensual y mart mensual. Juan, 4–8 nov. [ ] depende T5
- T7 (S4) HU-12 Pipeline con IPC y tasa. Andrey, 4–8 nov. [ ] depende T5
- T8 (S5) HU-06 Reintentos y log de errores en TRM. David, 2–4 nov. [ ]
- T9 (S9) T-06 Plan de pruebas y casos. Juan, 2–6 nov. [ ]
- T10 (S9) T-05 Matriz de trazabilidad v1 (`docs/trazabilidad.md`). Andrey, 5–8 nov. [ ]
### Sprint 4 (9–15 nov)
- T11 (S7) HU-13 Tablero Metabase por script. Andrey, 9–13 nov. [ ] depende T6
- T12 (S6) HU-11 Linaje con dbt docs. Juan, 9–11 nov. [ ] depende T6
- T13 (S9) T-07 Ejecución de pruebas y evidencia. Juan, 10–15 nov. [ ]
- T14 (S9) T-08 Manual técnico y de usuario. Andrey, 11–15 nov. [ ]
- T15 HU-14 Actualizar la app para leer el mart mensual cuando exista. David. [ ] depende T6
### Cierre (16–20 nov)
- T16 (S8) HU-02 Instalación en máquina limpia con solo el README. Andrey, 16–18 nov. [ ]
- T17 (S9) T-09 Trazabilidad final, actas, retrospectiva. Andrey/todos, 16–19 nov. [ ]
- T18 Ensayo de demo. Todos, 18–19 nov. [ ]

## Log
- L1: "no hay un plan definido para cumplir con las histirias de usuarios y las tareas ?"
- L2: "si" (crear el documento con HU y T-xx pendientes, fecha del Gantt y criterio del backlog).

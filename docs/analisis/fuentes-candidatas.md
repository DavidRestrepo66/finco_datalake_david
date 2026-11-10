# Fuentes de datos candidatas

**Estado:** propuesta, fuera del alcance de la entrega final (20 de noviembre de 2026). Implementadas en la rama `feat/nuevas-fuentes`: tasa de usura (1), CDT a 90 días (2), Brent y tasa de la Fed (4). Pendientes: 3 y 5.
**Fecha de verificación:** 2 de noviembre de 2026. Cada fuente se consultó directamente por su API pública.
**Objetivo:** ampliar las fuentes del lakehouse para que un analista obtenga más contexto sobre la TRM, la
inflación y las tasas de interés en Colombia.

Fuentes actuales, como referencia: TRM (Socrata, datos.gov.co), IPC y tasa de intervención (CSV del Banco de la República).

## 1. Candidatas recomendadas

Ordenadas por valor analítico y esfuerzo. Las fuentes 1 a 3 reutilizan el extractor Socrata de la TRM
(`ingesta/extractores/trm_socrata.py`).

| # | Fuente | Qué aporta | Acceso | Verificado el 2 nov 2026 |
|---|---|---|---|---|
| 1 | **Tasa de interés bancario corriente y usura (TIBC)**, Superintendencia Financiera. datos.gov.co `pare-7x5i` | Costo del crédito para personas y empresas, comparable con la tasa de intervención y la inflación | Socrata | Actualizado el 1 nov 2026. Son 396 filas con vigencia (`vigencia_desde`, `vigencia_hasta`) por `modalidad`. *Consumo y ordinario* arranca en 2007, *Microcrédito* llega hasta 2023-01, y las modalidades productivas existen desde 2023-04 |
| 2 | **Tasas de captación y operaciones del mercado monetario**, Superfinanciera. `axk9-g2nh` (y `inq8-ndez`, diarias) | Tasa de los CDT por entidad y plazo (por ejemplo, a 90 días). Permite calcular una DTF propia y comparar el ahorro con la inflación | Socrata | Actualizado el 30 oct 2026. Tiene unas 2,1 millones de filas, así que hay que filtrar por `descripcion` (plazo) y fecha al extraer |
| 3 | **Tasas de interés activas por tipo de crédito – Histórico**, Superfinanciera. `w9zh-vetq` (y `qzsc-9esp`, últimos dos meses) | Tasa efectiva promedio por entidad, tipo de crédito, producto, plazo y garantía | Socrata | Actualizado el 30 oct 2026. Es un volumen alto, así que se agrega a nivel mensual en silver |
| 4 | **FRED** (Federal Reserve Bank of St. Louis): petróleo Brent `DCOILBRENTEU` (diario) y tasa de la Fed `FEDFUNDS` (mensual) | Motores externos de la TRM. Habilitan el análisis de la relación entre el precio del petróleo y la TRM | CSV sin API key: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<serie>&cosd=<desde>` | Responde, con datos hasta octubre de 2026 |
| 5 | **Banco Mundial – API de indicadores**: crecimiento del PIB `NY.GDP.MKTP.KD.ZG`, desempleo y cuenta corriente | Contexto macro anual de Colombia | JSON sin key: `https://api.worldbank.org/v2/country/COL/indicator/<id>?format=json` | Responde. El último dato es de 2025 (actualizado el 8 oct 2026) |

## 2. Descartadas por ahora

| Fuente | Motivo |
|---|---|
| IBR y DTF del Banco de la República en datos.gov.co (`ev8i-uzwt`, `gtwv-4pxq`) | Son recursos de tipo enlace (`href`), no tablas, así que la API no las consulta. La DTF se puede calcular a partir de la candidata 2 |
| SUAMECA (Banco de la República) | No respondió desde el entorno de prueba. Se mantiene la exportación manual a CSV, como con el IPC |
| DANE: desempleo y PIB trimestral | Publica en Excel o como microdatos, sin una API estable. El extractor sería frágil |
| IMF DataMapper | La API responde, pero el filtro por país no devolvió Colombia en la prueba. Hace falta investigarla más |
| ANH: producción fiscalizada de crudo (`fdvb-hsrf`) | Es relevante para la TRM, pero se actualiza con poca frecuencia (la última vez en junio de 2026) |

## 3. Cómo encajan en la arquitectura

- **Bronze:** cada fuente se guarda en crudo con su lote, igual que las fuentes actuales.
- **Silver:**
  - La candidata 1 se modela por vigencia (fecha de inicio y de fin), con el mismo patrón que `silver_tasa_intervencion`.
  - Las candidatas 2 y 3 se agregan a promedio mensual por plazo o tipo de crédito.
  - La candidata 4 se normaliza por día (Brent) y por mes (Fed).
- **Gold:** las candidatas 1 a 4 suman columnas al `mart_mensual`, por ejemplo `tasa_usura_consumo`, `tasa_cdt_90`, `brent_promedio` y `fed_funds`. La candidata 5 es anual y va en un hecho anual aparte, sin mezclarse con el mart mensual.
- **App y tablero:** la pestaña *Análisis* puede sumar la correlación entre la TRM y el Brent, y comparar la usura con la tasa de intervención.

## 4. Historias de usuario propuestas

Son candidatas: no forman parte del backlog del Entregable 1 (`entregables/entregable-1/06-product-backlog.md`).
Si el equipo las acepta, se agregan al backlog y a la matriz de trazabilidad.

**HU-15 — Cargar la tasa de usura (candidata 1).**
Como analista, quiero consultar la tasa de usura por modalidad junto con la tasa de intervención, para comparar el costo del crédito con la política monetaria.

```gherkin
Dado que el pipeline se ejecutó
Cuando consulto el mart mensual
Entonces cada mes tiene la tasa de usura vigente de la modalidad «CONSUMO Y ORDINARIO»
Y los periodos de vigencia en silver no se solapan dentro de una misma modalidad
```

**HU-16 — Cargar factores externos de la TRM (candidata 4).**
Como analista, quiero ver el precio promedio del Brent y la tasa de la Fed por mes, para analizar qué factores externos acompañan los movimientos de la TRM.

```gherkin
Dado que el pipeline se ejecutó
Cuando consulto el mart mensual
Entonces cada mes desde 2020-01 tiene brent_promedio y fed_funds
Y la pestaña Análisis muestra la correlación entre la TRM y el Brent
```

## 5. Próximo paso sugerido

Implementar primero HU-15 y HU-16, con un PR por fuente. Las dos son baratas, encajan en el modelo actual y
no requieren credenciales. Las candidatas 2, 3 y 5 quedan para una segunda iteración.

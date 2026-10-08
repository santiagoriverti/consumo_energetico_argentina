# CONTEXTO — fuentes, decisiones y trampas

## 1. Fuentes

| Fuente | Qué trae | Desde | Dónde |
|---|---|---|---|
| CAMMESA, Base del Informe Mensual (BDI) | demanda eléctrica mensual por agente, provincia, tarifa (MWh) | 2012-01 | `microfe.cammesa.com/.../Sintesis%20Mensual/BASE_INFORME_MENSUAL_AAAA-MM.zip` |
| ENARGAS GED | gas entregado (miles de m³ de 9.300 kcal) y usuarios por provincia, distribuidora y tipo de usuario | 1993-01 | `enargas.gob.ar/secciones/transporte-y-distribucion/datos-estadisticos/GED/GED.xlsx` |
| ENARGAS GEGU | gas a grandes usuarios industriales por provincia y rama | 1994-11 | `.../GEGU/GEGU.xlsx` |
| ENARGAS GETD | gas entregado total del sistema por tipo de usuario y origen (Dis / Tra = by-pass / Off = boca de pozo) | 1993-01 | `.../GETD/GETD.xlsx` |
| SSPM (datos.gob.ar) | totales nacionales de CAMMESA (dataset 367) y ENARGAS (364), para validar | 1996/2001 | API de series, IDs en `fuentes.SERIES` |
| INDEC IPI manufacturero | nivel general original y desestacionalizado (2016 = 100) | 2016-01 | `453.1_SERIE_ORIGNAL_0_0_14_46`, `453.1_SERIE_DESEADA_0_0_24_58` |
| IGN | límites provinciales (WFS `ign:provincia`) | — | `scripts/preparar_mapa.py` → `data/reference/provincias.geojson` |

### CAMMESA: qué base cubre qué
- `2015-12` → detalle 2012-01 a 2014-12 (y 2015, pisado por la siguiente) · un solo xlsx, hoja `DEMANDA`.
- `2018-12` → 2015-01 a 2018-12 · un solo xlsx, hoja `DEMANDA`.
- `2022-12` → 2019-01 a 2022-12 · zip con `Bases_Demanda_INFORME_MENSUAL/Demanda Mensual.xlsx`.
- vigente (hoy `2026-08`) → 2023-01 al último mes · mismo formato que 2022-12 + columna `TIPO DEMANDA`.
- No existen bases anteriores a 2015-12 (404). En los meses repetidos gana la base más nueva.
- La hoja tiene arriba un resumen y abajo el detalle; el encabezado del detalle es la fila con `MES` en la
  columna B. El orden de columnas cambia entre bases (TARIFA / CATEGORIA TARIFA): leer por nombre.
- **No usar** el CSV "Demanda histórica" de datos.energia.gob.ar: corta en feb-2020 y en 2013-2017 duplica
  líneas (la tarifa de 10-300 kW y el alumbrado público aparecen en dos categorías: suma 148,7 TWh en 2013
  contra 125,2 reales).

## 2. Definiciones y decisiones

- **Sector eléctrico por tarifa** (`procesar.sector_tarifa`):
  - industria: todo agente del MEM que no es distribuidor (GU, AG autogeneradores, AR) + tarifas de
    distribuidoras ≥ 300 kW (`GRANDES USUARIOS C DEM MAYOR O IGUAL 300KW` hasta ene-2016,
    `TARIFA USUARIO NO RESIDENCIAL >=300KWH` feb-2016 a ene-2026, `GRANDES USUARIOS GUDI` desde feb-2026),
    `GUMES/GUPAS` y `MERCADO TERMINO DISTRIB`.
  - comercio: no residencial < 300 kW, alumbrado público, clubes.
  - hogares: tarifas residenciales, sociales, electrodependientes.
  - Por qué no la "CATEGORIA TARIFA" de CAMMESA: hasta 2014 la tarifa de 10-300 kW ("SANCIONADO") estaba en
    Industrial/Comercial Grande y el alumbrado público en Residencial.
  - Resultado: total y residencial = SSPM con error < 0,21% en 2012-2025 (máximo: residencial 2018, 0,201%).
- **Gas**: INDUSTRIALES → industria; DOMICILIARIOS → hogares; COMERCIALES + ENTES OFICIALES → comercio.
  Fuera: GNC (transporte), centrales eléctricas (generación), SDB (subdistribuidores; ~0,7 mil millones de
  m³/año, mayormente residencial en pueblos chicos).
- **By-pass industrial** (GETD, tipo Industria, origen ≠ Dis): ~15-18% del gas industrial (1,8 mil millones de
  m³ en 2025). GETD lo informa por área de licencia, no por provincia: se reparte entre las provincias del
  área con la estructura del consumo industrial de distribución del mismo mes. Áreas con by-pass grande:
  Pampeana (Bahía Blanca, desde 2023) y Sur (Patagonia). Industria (GED + by-pass) = serie "Industria" de la
  SSPM con error < 0,12%.
- **RTP** (Refinería/planta Cerri, ~1,5 mil millones de m³) y exportaciones: fuera (no son consumo final).
- **Energía**: TJ de energía final. 1 MWh = 0,0036 TJ; 1.000 m³ × 9.300 kcal × 4,1868 kJ/kcal = 0,038937 TJ.
- **Base 2016 = 100**: la misma del IPI manufacturero (comparación directa). A confirmar con el usuario.
- **Desestacionalización**: STL robusto sobre log (período 12, seasonal 13). Es ruidosa porque el gas
  industrial tiene cortes de invierno de magnitud variable; la tendencia-ciclo es la lectura principal.
- **Provincias**: sumas móviles de 12 meses. Buenos Aires incluye CABA (CAMMESA no las separa).
- **Ramas (GEGU)**: solo grandes usuarios de distribuidoras (sin by-pass). Se agrupan
  Metalúrgica / Ferrosa / No Ferrosa y Química / Petroquímica porque ENARGAS reclasificó en 2025.
- **Costa Atlántica** (`procesar.AGENTES_COSTA`, `indices.costa`): demanda eléctrica total (todos los
  sectores) de dos cooperativas que son agentes distribuidores del MEM: Villa Gesell (`CEVIGE3W`) y San
  Bernardo, Partido de La Costa (`CSBERN3W`, CESOP). **Pinamar y General Madariaga no son agentes del MEM**:
  su demanda está dentro de la de una distribuidora regional y CAMMESA no la informa por separado (verificado
  buscando PINAMAR, MADARIAGA, CARILO, OSTENDE, VALERIA en las descripciones de agentes). ENARGAS tampoco
  publica gas por partido (solo provincia y subzona de cada distribuidora).
  - Verano = promedio mensual de enero y febrero; invierno = promedio mensual de junio a agosto (población
    permanente); "enero / promedio" = enero sobre el promedio mensual de su año, promediado 2012-2025.
  - Referencia: el total del país (toda la demanda de CAMMESA) con las mismas definiciones (`Total país`).
  - Se compara contra 2016 (año base del índice) y contra el año anterior.
- **Certificados**: `fuentes._get` reintenta con `verify=False` solo si la verificación SSL falla (CAMMESA y
  ENARGAS no envían la cadena completa). Son datos públicos y la integridad se controla contra las series de
  la SSPM. Alternativa más estricta (la que usa infraestuctura_argentina con ENACOM): armar un bundle de
  certifi con el certificado intermedio.

## 3. Trampas y anomalías conocidas

- **oct-2019 a mar-2020**: un único gran usuario "Otras industrias" de Camuzzi Gas Pampeana (provincia de
  Buenos Aires) pasa de ~10 a ~280 millones de m³ por mes (abr-nov 2020: 80-120) y explica el pico del
  índice industrial (desest. 124 en feb-2020). Por volumen no parece manufactura (¿planta de GNL de Bahía
  Blanca, una central?). **Pendiente decidir** si se corrige (ver ESTADO §5).
- **Destilería** (Pampeana, BA): de ~50 a ~6 millones de m³/mes desde may-2025. Un solo usuario; explica buena
  parte de la caída del gas industrial de Buenos Aires en 2025-26 junto con cementeras.
- **Carnaval** cae en febrero o marzo según el año: mueve ±6% la demanda de grandes usuarios del mes. Para
  medir saltos de nomenclatura se comparan bimestres (`control_calidad.py` §3).
- **Reforma 2026**: desde feb-2026 los usuarios ≥ 300 kW de distribuidoras pasan a `GRANDES USUARIOS GUDI` y
  parte pasa a `MERCADO TERMINO DISTRIB` (de ~3 a ~200 GWh/mes); las residenciales pasan a "con / sin
  subsidio" y las no residenciales < 300 kW a `NO RESIDENCIAL GRAL`. Enero 2026 mezcla tarifas viejas y nuevas.
- **Patagonia**: el gas industrial de Neuquén, Río Negro, Chubut y Santa Cruz salta entre distribución y
  by-pass (pocos usuarios). Sus variaciones provinciales de gas no son confiables; la electricidad sí.
- Tierra del Fuego no está en el SADI (no hay electricidad en CAMMESA). Misiones y Formosa: sin gas por redes.
- Los textos de los xlsx de ENARGAS son UTF-8 correctos (los "�" que aparecen en la consola de Windows son
  de la consola).
- La API de datos.gob.ar acepta pocas series por pedido: `fuentes.series_nacionales` pide de a 10.
- **Villa Gesell (CEVIGE)**: julio de 2019 vale 8,1 GWh contra 11,5 a 15 en los demás julios (el invierno
  2019 del gráfico 11 cae a 83). Además, entre 2017 y 2019 la demanda comercial baja de 58,0 a 43,4 GWh/año
  y la residencial sube de 72,4 a 80,8 (2018) y 79,3 (2019): parece una reclasificación de tarifas. Para la
  costa usar la demanda total, no la apertura por sector.
- La demanda de verano de la costa depende mucho de la temperatura (aire acondicionado) y la de invierno de
  la calefacción eléctrica: las variaciones de la costa son descriptivas hasta corregir por clima.

## 4. Ideas para seguir (no implementadas)

- Clasificar los ~600 grandes usuarios eléctricos del MEM por rama (tabla `grandes_usuarios_electricidad.csv.gz`
  con agente, descripción y provincia) → índice eléctrico por rama comparable al de gas.
- Corrección de temperatura para hogares (la SSPM publica la temperatura media de CAMMESA:
  `temperatura_media` en `series_nacionales.csv`; para provincias, SMN).
- Ponderación alternativa por costo (la electricidad vale más por TJ que el gas) como sensibilidad.
- Población por provincia (Censo 2022) para consumo per cápita de hogares.
- Combustibles líquidos para industria (Secretaría de Energía, ventas por canal) y GLP.
- **Foco Pinamar / General Madariaga** (propuesta de la sección LaTeX, 5 pasos): (1) energía facturada y
  usuarios por mes y categoría por partido, pedidos a la distribuidora regional y al OCEBA (Organismo de
  Control de Energía Eléctrica de la Provincia de Buenos Aires), con Villa Gesell, La Costa y Mar Chiquita como
  comparación; (2) gas por localidad a Camuzzi Gas Pampeana; (3) por usuario, por habitante (Censo 2022) y
  corregido por temperatura (estaciones del SMN de la zona); (4) luces nocturnas satelitales (VIIRS) por
  partido mientras llegan los datos; (5) índice mensual de la Costa Atlántica con componentes temporada y
  población permanente para el boletín mensual de la UADE.

## 5. Reproducibilidad

- `construir.py` produce los mismos bytes en `data/processed/` y `output/graficos/` si los datos no cambian
  (los `.csv.gz` se escriben con `mtime=0`). El Excel de `output/` cambia siempre (guarda la fecha).
- Entorno probado: Python 3.14.5, pandas 2.3.3, numpy 2.4.6, matplotlib 3.10.9, openpyxl 3.1.5,
  statsmodels 0.14.6, requests 2.34.2 (PC del usuario) y el entorno por defecto de Colab.
- Los notebooks leen `data/processed/` del repo: en Colab no se baja nada salvo con `ACTUALIZAR = True`.

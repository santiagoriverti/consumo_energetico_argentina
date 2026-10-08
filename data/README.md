# data/

| Carpeta | Versionada | Quién la escribe |
|---|---|---|
| `processed/` | sí | `scripts/construir.py` (`pipeline.preparar`). Los notebooks leen de acá: funcionan sin bajar nada |
| `reference/` | sí | a mano (`provincias.csv`) y `scripts/preparar_mapa.py` (`provincias.geojson`) |
| `cache/` | **no** (`.gitignore`) | `src/fuentes.py`: descargas originales. Se regenera con `construir.py` |

## processed/ — tablas base

Fechas: primer día del mes (`AAAA-MM-01`). Provincias: las 23 jurisdicciones de
`reference/provincias.csv` (Buenos Aires y CABA juntas como `Buenos Aires y CABA`; `Sin provincia` si la
fuente no la informa). Filas a octubre de 2026.

| Archivo | Filas | Columnas | Contenido |
|---|---|---|---|
| `electricidad_provincia_sector.csv` | 11.616 | `fecha, provincia, sector, mwh` | Demanda eléctrica CAMMESA por sector (`industria`, `hogares`, `comercio`; asignado por tarifa). 2012-01 → 2026-08. Sin Tierra del Fuego (no está en el sistema interconectado) |
| `gas_provincia_sector.csv` | 23.099 | `fecha, provincia, sector, miles_m3, usuarios` | Gas entregado ENARGAS (miles de m³ de 9.300 kcal) y usuarios facturables. Industria incluye el by-pass repartido por área de licencia (con `usuarios` = 0). Excluye GNC, centrales eléctricas y subdistribuidores. 1993-01 → 2026-07. Sin Misiones ni Formosa (no tienen red de gas) |
| `gas_industria_ramas.csv` | 47.140 | `fecha, provincia, rama, miles_m3` | Gas a grandes usuarios industriales de las distribuidoras por rama (sin by-pass), con las ramas agrupadas de `procesar.RAMAS_AGRUPADAS`. 1994-11 → 2026-07 |
| `series_nacionales.csv` | 368 | `indice_tiempo` + 15 series de `fuentes.SERIES` | Totales nacionales de datos.gob.ar: `elec_*` (GWh, CAMMESA vía SSPM), `temperatura_media` (°C), `gas_*` (millones de m³, ENARGAS vía SSPM), `ipi_original` / `ipi_desest` (INDEC, 2016 = 100). Se usan para validar y para comparar con el IPI |
| `tarifas_cammesa.csv` | 79 | `tipo_agente, tarifa, categoria_tarifa, desde, hasta, gwh, sector` | Cada tarifa de CAMMESA con la categoría original, el período en que aparece y el sector asignado. Documenta la clasificación |
| `grandes_usuarios_electricidad.csv.gz` | 74.556 | `fecha, agente, provincia, agente_desc, tipo_agente, mwh` | Demanda mensual de cada agente industrial del MEM (GU, AG, AR). Insumo para clasificar por rama (pendiente). gzip con `mtime=0` (mismos datos → mismos bytes) |
| `electricidad_costa_atlantica.csv` | 979 | `fecha, localidad, sector, mwh` | Demanda de las cooperativas de Villa Gesell (`CEVIGE3W`) y San Bernardo, Partido de La Costa (`CSBERN3W`) — `procesar.AGENTES_COSTA`. 2012-01 → 2026-08 |

Unidades para pasar a energía: 1 MWh = 0,0036 TJ; 1.000 m³ de 9.300 kcal = 0,038937 TJ
(`procesar.TJ_POR_MWH`, `procesar.TJ_POR_MIL_M3`).

## reference/

- `provincias.csv`: `provincia` (nombre usado en todo el proyecto), `region` (Pampeana, NOA, NEA, Cuyo,
  Patagonia), `codigos_indec` (`02|06` para Buenos Aires y CABA), `cammesa` y `enargas` (cómo las nombra
  cada fuente; `|` separa varios alias). Si una fuente trae un nombre nuevo, agregarlo acá.
- `provincias.geojson`: límites provinciales del IGN simplificados (69 KB). Propiedades `codigo_indec`,
  `nombre`. Sin Antártida ni islas del Atlántico Sur al este de Malvinas.

## cache/ (no versionada, ~100 MB sin el IGN)

| Archivo | Origen |
|---|---|
| `BASE_INFORME_MENSUAL_{2015-12,2018-12,2022-12,AAAA-MM}.zip` | CAMMESA (~93 MB; la última es la vigente) |
| `cammesa_demanda_<base>.csv.gz` | detalle de demanda ya leído de cada base (leer el Excel tarda ~1 minuto) |
| `enargas_{GED,GEGU,GETD}.xlsx` | ENARGAS (~7 MB) |
| `series_datos_gob.csv` | API de series de datos.gob.ar |
| `ign_provincias.json` | IGN (~110 MB; solo lo usa `preparar_mapa.py`) |

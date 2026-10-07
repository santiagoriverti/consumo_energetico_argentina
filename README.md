# Índice de consumo energético de Argentina (ICE)

Cuánta energía consumen la **industria** y los **hogares** de Argentina, mes a mes y por provincia,
sumando electricidad y gas natural en una misma unidad física (terajoules, TJ). Datos abiertos de
CAMMESA y ENARGAS, 2012 → hoy (gas desde 1993).

| Notebook | Qué hace | Colab |
|---|---|---|
| `01_evolucion_nacional` | Índice industrial y de hogares, aporte de electricidad y gas, comparación con el IPI manufacturero del INDEC, ramas industriales | [![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santiagoriverti/consumo_energetico_argentina/blob/main/notebooks/01_evolucion_nacional.ipynb) |
| `02_provincias` | Ranking, mapa y trayectoria por provincia y región | [![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santiagoriverti/consumo_energetico_argentina/blob/main/notebooks/02_provincias.ipynb) |

Cada notebook termina descargando un ZIP con el Excel, los gráficos en PNG y las tablas en CSV.

## Primeros resultados (12 meses a julio 2026)

- **Industria: −8,1%** de energía frente a los 12 meses anteriores y −10,3% frente a 2023. Las fuentes van
  en direcciones opuestas: la **electricidad industrial sube 4,0%** y el **gas industrial cae 11,8%**.
- La caída del gas se concentra en pocos usuarios muy grandes: destilería (−62%), cementeras (−13%),
  siderurgia (−4%) y "otras industrias" (−18%), sobre todo en el área de Camuzzi Gas Pampeana (Buenos Aires).
- El índice desestacionalizado está en **93,9** (2016 = 100); el IPI manufacturero del INDEC, en ~90.
- **Hogares: +2,4%** (electricidad +2,2%, gas +2,5%). Desde 2016 el consumo eléctrico residencial creció
  17% y el de gas cayó 5,5%.
- Buenos Aires (con CABA) concentra el 48% de la energía industrial; Santa Fe 13%, Chubut 10% (aluminio),
  Córdoba 7% y Mendoza 5%.

Cifras de `python scripts/construir.py` (ver `ESTADO.md`).

## Método

1. **Electricidad** (CAMMESA, Base del Informe Mensual: demanda por agente, provincia y tarifa, 2012 →).
   Industria = grandes usuarios del mercado mayorista (GUMA, GUME, GUPA, autogeneradores) + usuarios de las
   distribuidoras con demanda ≥ 300 kW (GUDI). El sector se asigna **por tarifa**, porque la categoría de
   CAMMESA cambió de criterio en 2016 y en 2026. Incluye grandes comercios (no se pueden separar).
2. **Gas** (ENARGAS, datos operativos: gas entregado y usuarios por provincia y tipo de usuario, 1993 →).
   Industria = usuarios industriales de las distribuidoras + *by-pass* (industrias conectadas directo a
   los gasoductos), repartido entre las provincias de cada área de licencia.
3. **Agregación**: suma física de energía final en TJ (1 MWh = 0,0036 TJ; 1.000 m³ de 9.300 kcal =
   0,03894 TJ). Sin ponderadores arbitrarios: cada fuente pesa lo que pesa en energía (en la industria, el
   gas es ~3/4).
4. **Índice**: base 2016 = 100 (la del IPI manufacturero). Desestacionalización STL robusta; variaciones
   interanuales sobre la serie original; provincias en sumas de 12 meses.
5. **Validación** (`scripts/control_calidad.py`): la demanda eléctrica total y residencial coincide con la
   serie nacional de CAMMESA publicada por la SSPM (error < 0,2% en todos los años) y el gas por sector
   con la de ENARGAS (< 0,2%; comercio < 1,5%).

Detalle de fuentes, decisiones y trampas en [`CONTEXTO.md`](CONTEXTO.md).

## Limitaciones

- La electricidad "industrial" incluye grandes comercios y servicios (≥ 300 kW).
- El gas industrial de unas pocas provincias depende de muy pocos usuarios y del reparto del *by-pass*
  (Patagonia en particular). Entre oct-2019 y mar-2020 un solo usuario "Otras industrias" de Buenos Aires
  explica el pico del índice (ver `CONTEXTO.md`).
- No incluye combustibles líquidos, GLP ni autogeneración con combustibles propios.
- Tierra del Fuego no está en el sistema eléctrico interconectado (solo gas); Misiones y Formosa no tienen
  gas natural por redes. Buenos Aires incluye CABA.

## Uso local

```bash
pip install -r requirements.txt
python scripts/construir.py            # baja las fuentes (~100 MB, quedan en data/cache/) y arma todo
python scripts/control_calidad.py      # controles (esperable: 0 ALERTAS)
python -m pytest tests -q
python scripts/gen_notebooks.py        # regenera los notebooks
```

## Estructura

```
src/fuentes.py      descargas y lectura (CAMMESA, ENARGAS, datos.gob.ar)
src/procesar.py     sectores, provincias, by-pass, conversión a TJ
src/indices.py      índices, desestacionalización, cortes provinciales y por rama
src/graficos.py     gráficos;  src/exportar.py  Excel + ZIP;  src/pipeline.py  orquestación
scripts/            construir, control_calidad, gen_notebooks, preparar_mapa
data/processed/     tablas base (versionadas);  data/reference/  provincias y mapa (IGN)
output/             Excel y gráficos de la última corrida
```

Fuentes: CAMMESA, ENARGAS, Secretaría de Política Económica (series de tiempo de datos.gob.ar), INDEC e
IGN (límites provinciales).

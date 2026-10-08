# Índice de consumo energético de Argentina (ICE)

Cuánta energía consumen la **industria** y los **hogares** de Argentina, mes a mes y por provincia,
sumando electricidad y gas natural en una misma unidad física (terajoules, TJ). Datos abiertos de
CAMMESA y ENARGAS, 2012 → hoy (gas desde 1993). Incluye un primer análisis local de la Costa Atlántica
como base de una propuesta para Pinamar y General Madariaga.

| Notebook | Qué hace | Colab |
|---|---|---|
| `01_evolucion_nacional` | Índice industrial y de hogares, aporte de electricidad y gas, comparación con el IPI manufacturero del INDEC, ramas industriales | [![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santiagoriverti/consumo_energetico_argentina/blob/main/notebooks/01_evolucion_nacional.ipynb) |
| `02_provincias` | Ranking, mapa y trayectoria por provincia y región; hogares por provincia; Costa Atlántica (Villa Gesell y San Bernardo) | [![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santiagoriverti/consumo_energetico_argentina/blob/main/notebooks/02_provincias.ipynb) |

Cada notebook termina descargando un ZIP con el Excel, los gráficos en PNG y las tablas en CSV. Por
defecto usan las tablas ya procesadas del repo (`ACTUALIZAR = False`); con `True` bajan todo de nuevo.

## Primeros resultados (12 meses a julio 2026)

- **Industria: −8,1%** de energía frente a los 12 meses anteriores y −10,3% frente a 2023. Las fuentes van
  en direcciones opuestas: la **electricidad industrial sube 4,0%** y el **gas industrial cae 11,8%**.
- La caída del gas se concentra en pocos usuarios muy grandes: destilería (−62%), cementeras (−13%),
  siderurgia (−4%) y "otras industrias" (−18%), sobre todo en el área de Camuzzi Gas Pampeana (Buenos Aires).
- Índice industrial desestacionalizado: **93,9** en julio 2026 (2016 = 100); tendencia-ciclo 93,4, la más
  baja desde 2012. El IPI manufacturero desestacionalizado del INDEC: 87,0.
- **Hogares: +2,4%** (electricidad +2,2%, gas +2,5%). Desde 2016 el consumo eléctrico residencial creció
  17% y el de gas cayó 5,5%.
- Buenos Aires (con CABA) concentra el 48% de la energía industrial; Santa Fe 13%, Chubut 10% (aluminio),
  Córdoba 7% y Mendoza 5%.
- **Costa Atlántica**: desde 2016 la demanda eléctrica de invierno (población permanente) creció 18% en
  Villa Gesell y 24% en San Bernardo, contra 10% en el país; la de temporada (enero-febrero) cayó 2% y 32%
  (país +3,5%). La costa se volvió mucho menos estacional.

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
   serie nacional de CAMMESA publicada por la SSPM (error < 0,21% en todos los años) y el gas por sector
   con la de ENARGAS (hogares e industria < 0,2%; comercio < 1,5%).
6. **Costa Atlántica**: Pinamar y General Madariaga no son agentes del mercado eléctrico mayorista (CAMMESA
   no los informa por separado); sí lo son las cooperativas de Villa Gesell y de San Bernardo (Partido de La
   Costa). Se compara la demanda de temporada (enero-febrero) con la de invierno (junio-agosto).

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
python scripts/probar_latex.py         # compila la sección del informe INECO (requiere pdflatex)
```

En Windows, con `PYTHONUTF8=1`. Detalle de cada script en [`scripts/README.md`](scripts/README.md).

## Estructura

```
src/fuentes.py      descargas y lectura (CAMMESA, ENARGAS, datos.gob.ar)
src/procesar.py     sectores, provincias, by-pass, conversión a TJ, agentes de la Costa Atlántica
src/indices.py      índices, desestacionalización, cortes provinciales, por rama y de la costa
src/graficos.py     gráficos;  src/exportar.py  Excel + ZIP;  src/pipeline.py  orquestación
scripts/            construir, control_calidad, gen_notebooks, probar_latex, preparar_mapa (ver scripts/README.md)
notebooks/          01_evolucion_nacional, 02_provincias (generados por gen_notebooks.py)
data/processed/     tablas base (versionadas);  data/reference/  provincias y mapa (ver data/README.md)
output/             Excel y gráficos de la última corrida de construir.py
docs/informe_indicadores/  sección LaTeX del informe INECO "Propuesta de Indicadores Económicos"
tests/              tests de las piezas que no dependen de descargas
```

Documentos para retomar el trabajo: [`ESTADO.md`](ESTADO.md) (estado y próximos pasos),
[`CONTEXTO.md`](CONTEXTO.md) (fuentes y decisiones), [`CLAUDE.md`](CLAUDE.md) (reglas para sesiones de
Claude).

Fuentes: CAMMESA, ENARGAS, Secretaría de Política Económica (series de tiempo de datos.gob.ar), INDEC e
IGN (límites provinciales).

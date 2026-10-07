"""Genera los notebooks de notebooks/ (no editarlos a mano: editar este script y regenerar).

Uso:  python scripts/gen_notebooks.py
"""
from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
COLAB = 'https://colab.research.google.com/assets/colab-badge.svg'
GH = 'https://colab.research.google.com/github/santiagoriverti/consumo_energetico_argentina/blob/main/notebooks'

SETUP = r'''# Configuracion: en Colab clona (o actualiza) el repo; en local usa la carpeta del repo
import os, sys, subprocess, importlib
REPO = 'https://github.com/santiagoriverti/consumo_energetico_argentina.git'
if 'google.colab' in sys.modules:
    RAIZ = '/content/consumo_energetico_argentina'
    if os.path.exists(RAIZ):
        # Trae la ultima version de GitHub y descarta cambios locales (la copia de Colab es descartable)
        subprocess.run(['git', '-C', RAIZ, 'fetch', '-q', '--depth', '1', 'origin', 'main'], check=True)
        subprocess.run(['git', '-C', RAIZ, 'reset', '-q', '--hard', 'FETCH_HEAD'], check=True)
    else:
        subprocess.run(['git', 'clone', '-q', '--depth', '1', REPO, RAIZ], check=True)
else:  # subir desde la carpeta actual hasta encontrar el repo
    RAIZ = os.getcwd()
    while not os.path.exists(os.path.join(RAIZ, 'src', 'pipeline.py')) and os.path.dirname(RAIZ) != RAIZ:
        RAIZ = os.path.dirname(RAIZ)
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
# Si el notebook ya se corrio en esta sesion, olvidar los modulos de src cargados (pueden ser viejos)
for m in [m for m in sys.modules if m == 'src' or m.startswith('src.')]:
    del sys.modules[m]
importlib.invalidate_caches()
v = subprocess.run(['git', '-C', RAIZ, 'log', '-1', '--format=%h (%ad) %s', '--date=short'],
                   capture_output=True, text=True).stdout.strip()
print('Version del repo:', v or 'sin git')

import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, Markdown
from src import pipeline, graficos, indices
pd.set_option('display.float_format', lambda x: f'{x:,.1f}')
pd.set_option('display.max_columns', 30)'''

CARGA = r'''# ACTUALIZAR = True vuelve a bajar CAMMESA y ENARGAS (~100 MB, unos minutos). Con False usa las tablas
# del repo (data/processed/), que se actualizan con scripts/construir.py.
ACTUALIZAR = False
R = pipeline.calcular(actualizar=ACTUALIZAR)
print(R['meta'])'''


def md(texto: str) -> dict:
    return {'cell_type': 'markdown', 'metadata': {}, 'source': texto.strip('\n').splitlines(keepends=True)}


def code(texto: str) -> dict:
    return {'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [],
            'source': texto.strip('\n').splitlines(keepends=True)}


def descarga(nombre: str) -> list[dict]:
    """Celdas finales comunes: exportan todo y, en Colab, descargan el ZIP."""
    return [
        md(r'''
## Descargar todos los resultados

ZIP con el Excel (una hoja por tabla), los gráficos en PNG (`graficos/`) y las tablas en CSV
(`datos/`). En Colab se descarga solo; en la PC queda en la carpeta `_descargas/` del repo.
'''),
        code(f'''from src.exportar import zip_resultados
zip_path = zip_resultados(R, '{nombre}')
print('ZIP:', zip_path)
if 'google.colab' in sys.modules:
    from google.colab import files
    files.download(zip_path)'''),
    ]


def guardar(nombre: str, celdas: list[dict]) -> None:
    nb = {'cells': celdas, 'metadata': {
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python'}, 'colab': {'provenance': []}},
        'nbformat': 4, 'nbformat_minor': 5}
    ruta = RAIZ / 'notebooks' / nombre
    ruta.parent.mkdir(exist_ok=True)
    ruta.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('escrito', ruta.relative_to(RAIZ))


# ------------------------------------------------------------------------------------------------
NB01 = [
    md(rf'''
# 01 · Índice de consumo energético: evolución nacional

[![Abrir en Colab]({COLAB})]({GH}/01_evolucion_nacional.ipynb)

Mide cuánta energía consume la **industria** (y los **hogares**) de Argentina mes a mes, sumando
electricidad y gas natural en una misma unidad física (terajoules, TJ).

- **Electricidad**: CAMMESA, demanda por agente y tarifa (2012 →). Industria = grandes usuarios del mercado
  mayorista (GUMA, GUME, GUPA, autogeneradores) + usuarios de las distribuidoras con demanda ≥ 300 kW.
- **Gas**: ENARGAS, gas entregado por tipo de usuario (1993 →). Industria = usuarios industriales de las
  distribuidoras + *by-pass* (industrias que toman el gas directo de los gasoductos).
- Índice base **2016 = 100** (la misma base que el IPI manufacturero del INDEC). Desestacionalización STL.

Detalle de fuentes, decisiones y limitaciones: `README.md` y `CONTEXTO.md` del repo.
'''),
    code(SETUP),
    code(CARGA),
    md(r'''
## El índice industrial

La serie original tiene mucha estacionalidad: en invierno el gas para la industria cae porque las
distribuidoras priorizan a los hogares (contratos interrumpibles). La tendencia-ciclo resume la dirección.
'''),
    code(r'''fig = graficos.g01_indice_industrial(R); plt.show()'''),
    code(r'''i, v = R['indices'], R['variaciones']
cols = ['industria', 'industria_desest', 'industria_tendencia', 'industria_electricidad', 'industria_gas']
t = i[cols].join(v[['industria', 'industria_contrib_electricidad', 'industria_contrib_gas']], rsuffix='_var_ia_%')
display(t.dropna(subset=['industria']).tail(13))'''),
    md(r'''
**Ojo con oct-2019 a mar-2020.** Un único gran usuario clasificado como "Otras industrias" en el área de
Camuzzi Gas Pampeana (provincia de Buenos Aires) multiplica por 20 su consumo de gas (hasta ~280 millones de
m³ por mes) y explica casi todo el pico del índice antes de la pandemia. No parece consumo manufacturero:
está documentado como anomalía a resolver en `CONTEXTO.md`.
'''),
    md(r'''
## Electricidad y gas

En energía, el gas es ~3/4 del consumo industrial. Las dos fuentes no se mueven igual: la electricidad
sigue de cerca la actividad; el gas además refleja cortes de invierno, cambios de combustible y unos pocos
usuarios muy grandes (refinerías, siderurgia, petroquímica).
'''),
    code(r'''fig = graficos.g02_componentes_industria(R); plt.show()'''),
    code(r'''fig = graficos.g05_contribuciones(R); plt.show()'''),
    code(r'''a = R['anual']
display((a[['industria_electricidad', 'industria_gas', 'industria_total', 'industria_part_elec_%']]
         .dropna().assign(var_total_pct=lambda x: 100 * x['industria_total'].pct_change())))'''),
    md(r'''
## Energía vs producción industrial

Mismo año base que el IPI manufacturero del INDEC: si la energía cae más que la producción, la industria se
vuelve menos intensiva en energía (o cambió la composición hacia ramas menos intensivas).
'''),
    code(r'''fig = graficos.g03_industria_vs_ipi(R); plt.show()'''),
    code(r'''x = i[['industria_desest', 'ipi_manufacturero_desest', 'intensidad_industria']].dropna()
display(x.groupby(x.index.year).mean())'''),
    md(r'''
## Ramas industriales (gas de grandes usuarios)

ENARGAS informa el gas de los grandes usuarios industriales de las distribuidoras por rama de actividad (no
incluye el *by-pass*). Es el único corte por rama disponible con datos abiertos mensuales.
'''),
    code(r'''fig = graficos.g09_ramas(R); plt.show()'''),
    code(r'''display(R['ramas']['resumen'])'''),
    md(r'''
## Hogares

Consumo residencial de electricidad y gas. Depende sobre todo del clima (calefacción y aire acondicionado) y
de las tarifas; el gas por usuario descuenta el crecimiento de la cantidad de usuarios conectados.
'''),
    code(r'''fig = graficos.g04_hogares(R); plt.show()'''),
    code(r'''fig = graficos.g10_gas_por_usuario(R); plt.show()'''),
    code(r'''display(R['anual'][['hogares_electricidad', 'hogares_gas', 'hogares_total', 'hogares_part_elec_%']].dropna())'''),
    *descarga('ICE_01_evolucion_nacional'),
]

# ------------------------------------------------------------------------------------------------
NB02 = [
    md(rf'''
# 02 · Índice de consumo energético: provincias

[![Abrir en Colab]({COLAB})]({GH}/02_provincias.ipynb)

Distribución geográfica del consumo energético industrial (electricidad + gas, en TJ) y su evolución.
Para evitar la estacionalidad, todo se compara en **sumas de 12 meses**.

- Buenos Aires incluye CABA (CAMMESA no las separa).
- Tierra del Fuego no está conectada al sistema eléctrico nacional (solo gas); Misiones y Formosa no tienen
  red de gas natural (solo electricidad).
- El *by-pass* industrial de gas (industrias conectadas directo a los gasoductos) se reparte entre las
  provincias de cada área de licencia según el consumo industrial de distribución del mes. En la Patagonia
  (área de Camuzzi Gas del Sur) ese reparto pesa mucho: tomar con cuidado las variaciones de Neuquén, Río
  Negro, Chubut y Santa Cruz.
'''),
    code(SETUP),
    code(CARGA),
    md(r'''
## Dónde se consume la energía industrial
'''),
    code(r'''fig = graficos.g07_ranking_provincias(R); plt.show()'''),
    code(r'''t = R['provincias_industria']
display(t[['region', 'tj_12m', 'participacion_%', 'part_electricidad_%', 'var_12m_vs_anterior_%',
           'var_12m_vs_anterior_electricidad_%', 'var_12m_vs_anterior_gas_%', 'var_12m_vs_2023_%',
           f'var_12m_vs_{indices.BASE}_%']])'''),
    md(r'''
## Cómo cambió desde 2023

Las provincias chicas pueden mostrar variaciones grandes por un solo usuario: leer el mapa junto con la
participación de cada provincia en el total (tabla de arriba).
'''),
    code(r'''fig = graficos.g06_mapa_industria(R, 'var_12m_vs_2023_%'); plt.show()'''),
    code(r'''fig = graficos.g06_mapa_industria(R, 'var_12m_vs_anterior_%'); plt.show()'''),
    md(r'''
## Trayectoria por provincia

Suma de 12 meses a diciembre de cada año (y al último mes) con 2016 = 100.
'''),
    code(r'''fig = graficos.g08_heatmap_provincias(R); plt.show()'''),
    md(r'''
## Por región
'''),
    code(r'''from src import procesar
p = R['panel']
p = p[(p['sector'] == 'industria') & (p['fecha'] <= pd.Timestamp(R['meta']['ultimo_mes_indice']))]
reg = p.merge(procesar.provincias()[['provincia', 'region']], on='provincia')
anual = reg.groupby([reg['fecha'].dt.year, 'region'])['tj'].sum().unstack()
anual = anual[reg.groupby(reg['fecha'].dt.year)['fecha'].nunique() == 12]
display((100 * anual / anual.loc[indices.BASE]).round(1))'''),
    md(r'''
## Hogares por provincia
'''),
    code(r'''display(R['provincias_hogares'][['region', 'tj_12m', 'participacion_%', 'part_electricidad_%',
                                   'var_12m_vs_anterior_%', 'var_12m_vs_2023_%']])'''),
    md(r'''
Gas por usuario residencial (m³ por mes, promedio de 12 meses): el clima de cada provincia pesa más que
cualquier otra cosa.
'''),
    code(r'''g = R['gas_por_usuario'].rolling(12).mean()
t = g.iloc[[-37, -13, -1]].T
t.columns = [d.strftime('12m a %m/%Y') for d in t.columns]
display(t.sort_values(t.columns[-1], ascending=False))'''),
    *descarga('ICE_02_provincias'),
]


if __name__ == '__main__':
    guardar('01_evolucion_nacional.ipynb', NB01)
    guardar('02_provincias.ipynb', NB02)

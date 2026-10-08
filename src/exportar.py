"""Exportacion de resultados: Excel, graficos PNG y CSV.

- `exportar(R, dir_salida)`: escribe indice_consumo_energetico.xlsx, graficos/ y datos/ (CSV de los
  resultados). scripts/construir.py lo usa con output/ (versionado).
- `zip_resultados(R, nombre)`: lo que llaman los notebooks al final. Exporta todo a
  _descargas/<nombre>/ (ignorado por git, no toca output/) y lo comprime en _descargas/<nombre>.zip.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from . import fuentes, graficos, indices

DESCARGAS = fuentes.RAIZ / '_descargas'
EXCEL = 'indice_consumo_energetico.xlsx'


def version_repo() -> str:
    """Commit del repo con que se genero la salida (para saber si un ZIP es de una version vieja)."""
    try:
        r = subprocess.run(['git', '-C', str(fuentes.RAIZ), 'log', '-1', '--format=%h (%ad)', '--date=short'],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or 'desconocida'
    except (OSError, subprocess.SubprocessError):
        return 'desconocida'


def notas(R: dict) -> list[str]:
    m = R['meta']
    return [
        'Indice de consumo energetico (ICE) de la industria y los hogares de Argentina, por provincia.',
        f'Version del codigo (commit): {version_repo()}',
        f"Ultimo mes: electricidad {m['ultimo_mes_electricidad']} | gas {m['ultimo_mes_gas']} | "
        f"indice (ambas fuentes) {m['ultimo_mes_indice']}",
        f'Indices base {indices.BASE} = 100. Energia en TJ (terajoules): 1 MWh = 0,0036 TJ; 1.000 m3 de gas de '
        '9.300 kcal = 0,03894 TJ. Variaciones en %.',
        'Industria: electricidad de grandes usuarios (MEM y >= 300 kW de distribuidoras) + gas a usuarios '
        'industriales (distribucion + by-pass). Hogares: tarifas residenciales y usuarios domiciliarios.',
        'Buenos Aires incluye CABA. Metodologia: README y CONTEXTO.md del repo '
        'github.com/santiagoriverti/consumo_energetico_argentina.',
    ]


def _fecha_texto(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if isinstance(df.index, pd.DatetimeIndex):
        df.index = df.index.strftime('%Y-%m')
    return df


def hojas(R: dict) -> dict[str, pd.DataFrame]:
    return {
        'Indices_nacionales': R['indices'],
        'Var_interanual_%': R['variaciones'],
        'TJ_mensual': R['nacional_tj'].loc['2012-01-01':],
        'TJ_anual': R['anual'],
        'Prov_industria': R['provincias_industria'],
        'Prov_hogares': R['provincias_hogares'],
        'Prov_indice_industria_12m': R['provincias_indice_industria'],
        'Prov_indice_hogares_12m': R['provincias_indice_hogares'],
        'Ramas_gas_resumen': R['ramas']['resumen'],
        'Ramas_gas_TJ_anual': R['ramas']['anual'],
        'Ramas_gas_indice_12m': R['ramas']['indice_12m'],
        'Gas_m3_por_usuario': R['gas_por_usuario'].loc['2012-01-01':],
        'Costa_resumen': R['costa']['resumen'],
        'Costa_GWh_mensual': R['costa']['mensual_gwh'],
        'Costa_temporadas_indice': R['costa']['temporadas_indice'],
        'Tarifas_CAMMESA': R['tablas']['tarifas'],
    }


def exportar(R: dict, dir_salida: Path, con_csv: bool = True) -> None:
    dir_salida = Path(dir_salida)
    (dir_salida / 'graficos').mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(dir_salida / EXCEL, engine='openpyxl') as xw:
        pd.DataFrame({'nota': notas(R)}).to_excel(xw, sheet_name='Notas', index=False)
        for nombre, df in hojas(R).items():
            _fecha_texto(df).to_excel(xw, sheet_name=nombre[:31])
    if con_csv:
        (dir_salida / 'datos').mkdir(exist_ok=True)
        for nombre, df in hojas(R).items():
            _fecha_texto(df).to_csv(dir_salida / 'datos' / f'{nombre.lower()}.csv', float_format='%.4f',
                                    lineterminator='\n')
    for nombre, f in graficos.GRAFICOS.items():
        fig = f(R)
        fig.savefig(dir_salida / 'graficos' / f'{nombre}.png')
        plt.close(fig)


def zip_resultados(R: dict, nombre: str) -> str:
    """Exporta Excel, graficos y CSV a _descargas/<nombre>/ y devuelve la ruta del ZIP."""
    carpeta = DESCARGAS / nombre
    if carpeta.exists():
        shutil.rmtree(carpeta)
    exportar(R, carpeta)
    (carpeta / 'LEEME.txt').write_text(
        '\n'.join(notas(R) + ['', 'Contenido:', f'  {EXCEL}  todas las tablas (una hoja por tabla)',
                              '  graficos/   graficos en PNG', '  datos/      las mismas tablas en CSV']) + '\n',
        encoding='utf-8')
    return shutil.make_archive(str(carpeta), 'zip', carpeta)

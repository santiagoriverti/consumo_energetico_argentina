"""Orquestacion.

- `preparar(refrescar)`: fuentes -> tablas base en data/processed/ (versionadas). Lo corre
  scripts/construir.py; baja ~100 MB la primera vez (queda en data/cache/).
- `calcular(actualizar)`: tablas base -> diccionario R con indices, cortes y metadatos. Es lo que usan
  los notebooks: por defecto lee las tablas versionadas del repo (rapido); con actualizar=True baja
  todo de nuevo antes.
"""
from __future__ import annotations

import pandas as pd

from . import fuentes, indices, procesar

P = fuentes.PROCESADOS
ARCHIVOS = {
    'electricidad': 'electricidad_provincia_sector.csv',
    'gas': 'gas_provincia_sector.csv',
    'ramas_gas': 'gas_industria_ramas.csv',
    'series': 'series_nacionales.csv',
    'tarifas': 'tarifas_cammesa.csv',
    'grandes_usuarios': 'grandes_usuarios_electricidad.csv.gz',
    'costa': 'electricidad_costa_atlantica.csv',
}


def preparar(refrescar: bool = False) -> dict[str, pd.DataFrame]:
    dem = fuentes.demanda_cammesa(refrescar)
    ged = fuentes.gas_distribucion(refrescar)
    getd = fuentes.gas_total_sistema(refrescar)
    gegu = fuentes.gas_grandes_usuarios(refrescar)
    T = {
        'electricidad': procesar.electricidad(dem),
        'gas': procesar.gas(ged, getd),
        'ramas_gas': procesar.ramas_gas(gegu),
        'series': fuentes.series_nacionales(refrescar),
        'tarifas': procesar.tabla_tarifas(dem),
        'grandes_usuarios': procesar.grandes_usuarios_electricos(dem),
        'costa': procesar.electricidad_agentes(dem, procesar.AGENTES_COSTA),
    }
    P.mkdir(parents=True, exist_ok=True)
    for k, df in T.items():
        df.to_csv(P / ARCHIVOS[k], index=(k == 'series'), float_format='%.4f', lineterminator='\n')
    return T


def leer() -> dict[str, pd.DataFrame]:
    T = {}
    for k, a in ARCHIVOS.items():
        if k == 'series':
            T[k] = pd.read_csv(P / a, parse_dates=['indice_tiempo'], index_col='indice_tiempo')
        elif k == 'tarifas':
            T[k] = pd.read_csv(P / a, parse_dates=['desde', 'hasta'])
        else:
            T[k] = pd.read_csv(P / a, parse_dates=['fecha'])
    return T


def calcular(actualizar: bool = False) -> dict:
    T = preparar(refrescar=True) if actualizar else leer()
    panel = procesar.panel(T['electricidad'], T['gas'])
    R = indices.construir(panel, T['gas'], T['ramas_gas'], T['series'], procesar.provincias())
    R['costa'] = indices.costa(T['costa'], T['electricidad'])
    R['tablas'] = T
    return R

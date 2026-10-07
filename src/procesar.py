"""De los datos crudos a un panel mensual homogeneo: fecha x provincia x sector x fuente, en TJ.

Decisiones (detalle en CONTEXTO.md):
- Electricidad: la categoria se asigna por TARIFA y no por la columna "CATEGORIA TARIFA" de CAMMESA, que
  cambio de criterio (hasta ene-2016 los usuarios de 10 a 300 kW y el alumbrado publico estaban en
  "Industrial/Comercial Grande" o "Residencial"). Industria = grandes usuarios del MEM (GUMA, GUME, GUPA,
  autogeneradores) + usuarios de las distribuidoras con demanda >= 300 kW (GUDI). Incluye grandes
  comercios (shoppings, supermercados, hospitales): no hay forma de separarlos con estos datos.
- Gas: tipo de usuario de ENARGAS (distribuidoras). Industria = INDUSTRIALES + el by-pass industrial
  (gas que la industria toma directo de los gasoductos de transporte), repartido entre las provincias de
  cada area de licencia segun el consumo industrial de distribucion de ese mes.
- Sectores: industria, hogares (residencial), comercio (comercial + entes oficiales + alumbrado publico).
  Quedan afuera: GNC (transporte), centrales electricas y subdistribuidores (SDB) del gas.
- Buenos Aires incluye CABA (CAMMESA no las separa). Tierra del Fuego no esta en el sistema electrico
  interconectado (solo gas); Misiones y Formosa no tienen red de gas natural (solo electricidad).
"""
from __future__ import annotations

import re
import unicodedata

import pandas as pd

from . import fuentes

TJ_POR_MWH = 0.0036                       # 1 MWh = 3,6 GJ
TJ_POR_MIL_M3 = 9300 * 4.1868 * 1e-6      # 1.000 m3 de 9.300 kcal = 38,94 GJ = 0,03894 TJ

SECTORES = ['industria', 'hogares', 'comercio']
GAS_SECTOR = {'INDUSTRIALES': 'industria', 'DOMICILIARIOS': 'hogares', 'COMERCIALES': 'comercio',
              'ENTES OFICIALES': 'comercio'}
SIN_PROVINCIA = 'Sin provincia'


def _norm(s: str) -> str:
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^A-Z0-9]+', ' ', s.upper()).strip()


def provincias() -> pd.DataFrame:
    return pd.read_csv(fuentes.REFERENCIA / 'provincias.csv', dtype=str, keep_default_na=False)


def _mapa_alias(columna: str) -> dict[str, str]:
    m = {}
    for _, r in provincias().iterrows():
        for alias in filter(None, r[columna].split('|')):
            m[_norm(alias)] = r['provincia']
    return m


# ------------------------------------------------------------------------------------------------
# Electricidad
# ------------------------------------------------------------------------------------------------
_RE_INDUSTRIA = re.compile(r'>= ?300|MAYOR O IGUAL 300|GUMA|GUME|GUPA|GUDI|GRANDES USUARIOS|MERCADO TERMINO')
_RE_COMERCIO = re.compile(r'NO RES|ALUMBRADO|SANCIONADO|CLUBES|MENOR 10KW')
_RE_HOGARES = re.compile(r'RES|SOCIAL|ELECTROD')
_CATEGORIA_CAMMESA = {'RESIDENCIAL': 'hogares', 'COMERCIAL': 'comercio', 'INDUSTRIAL COMERCIAL GRANDE': 'industria',
                      'MERCADO A TERMINO': 'industria'}


def sector_tarifa(tarifa: str, tipo_agente: str = 'DI', categoria_tarifa: str = '') -> str:
    """Sector de una linea de demanda de CAMMESA (ver docstring del modulo)."""
    if tipo_agente not in ('DI', 'DM'):  # GU, AG (autogeneradores), AR: agentes del MEM
        return 'industria'
    t = _norm(tarifa).replace(' ', '')
    t_esp = _norm(tarifa)
    if _RE_INDUSTRIA.search(tarifa.upper()) or _RE_INDUSTRIA.search(t_esp):
        return 'industria'
    if _RE_COMERCIO.search(t_esp) or 'NORES' in t:
        return 'comercio'
    if _RE_HOGARES.search(t_esp):
        return 'hogares'
    return _CATEGORIA_CAMMESA.get(_norm(categoria_tarifa), 'sin_clasificar')


def tabla_tarifas(dem: pd.DataFrame) -> pd.DataFrame:
    """Cada tarifa con su sector asignado, la categoria original de CAMMESA y el periodo en que aparece."""
    t = (dem.groupby(['tipo_agente', 'tarifa', 'categoria_tarifa'])
         .agg(desde=('fecha', 'min'), hasta=('fecha', 'max'), gwh=('mwh', lambda x: x.sum() / 1e3))
         .reset_index())
    t['sector'] = [sector_tarifa(a, b, c) for a, b, c in zip(t['tarifa'], t['tipo_agente'], t['categoria_tarifa'])]
    return t.sort_values(['sector', 'gwh'], ascending=[True, False]).reset_index(drop=True)


def electricidad(dem: pd.DataFrame) -> pd.DataFrame:
    """fecha, provincia, sector, mwh (CAMMESA, todas las bases unidas)."""
    alias = _mapa_alias('cammesa')
    claves = dem[['tarifa', 'tipo_agente', 'categoria_tarifa']].drop_duplicates()
    claves['sector'] = [sector_tarifa(a, b, c) for a, b, c in
                        zip(claves['tarifa'], claves['tipo_agente'], claves['categoria_tarifa'])]
    d = dem.merge(claves, on=['tarifa', 'tipo_agente', 'categoria_tarifa'], how='left')
    d['provincia'] = d['provincia_cammesa'].map(lambda p: alias.get(_norm(p), SIN_PROVINCIA))
    return d.groupby(['fecha', 'provincia', 'sector'], as_index=False)['mwh'].sum()


def grandes_usuarios_electricos(dem: pd.DataFrame) -> pd.DataFrame:
    """Demanda mensual de cada agente industrial del MEM (para analisis por empresa / rama)."""
    alias = _mapa_alias('cammesa')
    d = dem[~dem['tipo_agente'].isin(['DI', 'DM'])].copy()
    d['provincia'] = d['provincia_cammesa'].map(lambda p: alias.get(_norm(p), SIN_PROVINCIA))
    return (d.groupby(['fecha', 'agente', 'provincia'], as_index=False)
            .agg(agente_desc=('agente_desc', 'last'), tipo_agente=('tipo_agente', 'last'), mwh=('mwh', 'sum')))


# ------------------------------------------------------------------------------------------------
# Gas
# ------------------------------------------------------------------------------------------------
def gas(ged: pd.DataFrame, getd: pd.DataFrame | None = None) -> pd.DataFrame:
    """fecha, provincia, sector, miles_m3, usuarios (distribucion + by-pass industrial repartido)."""
    alias = _mapa_alias('enargas')
    g = ged[ged['tipo'].isin(list(GAS_SECTOR))].copy()
    g['provincia'] = g['provincia_enargas'].map(lambda p: alias.get(_norm(p), SIN_PROVINCIA))
    g['sector'] = g['tipo'].map(GAS_SECTOR)
    out = g.groupby(['fecha', 'provincia', 'sector'], as_index=False)[['miles_m3', 'usuarios']].sum()
    if getd is not None:
        bp = bypass_industrial(ged, getd)
        bp = bp.groupby(['fecha', 'provincia'], as_index=False)['miles_m3'].sum().assign(sector='industria')
        out = (pd.concat([out, bp.assign(usuarios=0.0)])
               .groupby(['fecha', 'provincia', 'sector'], as_index=False)[['miles_m3', 'usuarios']].sum())
    return out


def bypass_industrial(ged: pd.DataFrame, getd: pd.DataFrame) -> pd.DataFrame:
    """By-pass industrial (GETD origen != Dis) repartido entre las provincias de su area de licencia con la
    estructura del consumo industrial de distribucion del mismo mes (fecha, area, provincia, miles_m3)."""
    alias = _mapa_alias('enargas')
    bp = getd[(getd['tipo'] == 'Industria') & (getd['origen'] != 'Dis')]
    bp = bp.groupby(['fecha', 'area_licencia'], as_index=False)['miles_m3'].sum()
    ind = ged[ged['tipo'] == 'INDUSTRIALES'].copy()
    ind['provincia'] = ind['provincia_enargas'].map(lambda p: alias.get(_norm(p), SIN_PROVINCIA))
    ind['area_licencia'] = ind['distribuidora']
    pesos = ind.groupby(['fecha', 'area_licencia', 'provincia'], as_index=False)['miles_m3'].sum()
    pesos['peso'] = pesos['miles_m3'] / pesos.groupby(['fecha', 'area_licencia'])['miles_m3'].transform('sum')
    r = bp.merge(pesos[['fecha', 'area_licencia', 'provincia', 'peso']], on=['fecha', 'area_licencia'], how='left')
    sin_peso = r['peso'].isna()
    r.loc[sin_peso, 'provincia'] = SIN_PROVINCIA
    r.loc[sin_peso, 'peso'] = 1.0
    r['miles_m3'] = r['miles_m3'] * r['peso']
    return r[['fecha', 'area_licencia', 'provincia', 'miles_m3']]


# ENARGAS reclasifico ramas: 'Metalurgica Ferrosa' pasa a 'Metalurgica' en 2025 y parte de 'Petroquimica'
# pasa a 'Quimica' en 2025. Se agrupan para que las series sean comparables en el tiempo.
RAMAS_AGRUPADAS = {'METALURGICA': 'Metalúrgica', 'METALURGICA FERROSA': 'Metalúrgica',
                   'METALURGICA NO FERROSA': 'Metalúrgica', 'SIDERURGIA': 'Siderurgia',
                   'QUIMICA': 'Química y petroquímica', 'PETROQUIMICA': 'Química y petroquímica'}


def ramas_gas(gegu: pd.DataFrame) -> pd.DataFrame:
    """Grandes usuarios industriales de gas por provincia y rama (con las ramas de RAMAS_AGRUPADAS)."""
    alias = _mapa_alias('enargas')
    g = gegu.copy()
    g['provincia'] = g['provincia_enargas'].map(lambda p: alias.get(_norm(p), SIN_PROVINCIA))
    g['rama'] = g['rama'].map(lambda r: RAMAS_AGRUPADAS.get(_norm(r), r))
    return g.groupby(['fecha', 'provincia', 'rama'], as_index=False)['miles_m3'].sum()


# ------------------------------------------------------------------------------------------------
# Panel
# ------------------------------------------------------------------------------------------------
def panel(elec: pd.DataFrame, gas_: pd.DataFrame) -> pd.DataFrame:
    """fecha, provincia, sector, fuente (electricidad / gas), tj. Solo los sectores de SECTORES."""
    e = elec[elec['sector'].isin(SECTORES)].assign(fuente='electricidad', tj=lambda x: x['mwh'] * TJ_POR_MWH)
    g = gas_[gas_['sector'].isin(SECTORES)].assign(fuente='gas', tj=lambda x: x['miles_m3'] * TJ_POR_MIL_M3)
    cols = ['fecha', 'provincia', 'sector', 'fuente', 'tj']
    return pd.concat([e[cols], g[cols]], ignore_index=True).sort_values(cols[:4]).reset_index(drop=True)

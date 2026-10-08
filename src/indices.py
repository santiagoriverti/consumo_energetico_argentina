"""Indices de consumo energetico (ICE) a partir del panel en TJ.

- Agregacion: suma fisica de energia final (TJ) de electricidad y gas. Cada fuente pesa lo que pesa en
  energia; no hay ponderadores arbitrarios. Las contribuciones de cada fuente a la variacion interanual
  suman exactamente la variacion del total.
- Base: promedio BASE = 100 (la misma base que el IPI manufacturero del INDEC, para compararlos directo).
- Desestacionalizacion: STL robusto sobre el logaritmo (periodo 12). Las variaciones interanuales se
  calculan sobre la serie original.
- Provincias: suma movil de 12 meses (sin estacionalidad) contra el total del anio base.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL

from .procesar import SECTORES, SIN_PROVINCIA, TJ_POR_MIL_M3

BASE = 2016
FUENTES = ['electricidad', 'gas']


def a_base(s: pd.Series | pd.DataFrame, base: int = BASE):
    return 100 * s / s[s.index.year == base].mean()


def desestacionalizar(s: pd.Series) -> pd.DataFrame:
    """original, desestacionalizada y tendencia-ciclo (STL robusto en logaritmos)."""
    x = s.dropna()
    res = STL(np.log(x), period=12, seasonal=13, robust=True).fit()
    return pd.DataFrame({'original': x, 'desest': np.exp(res.observed - res.seasonal),
                         'tendencia': np.exp(res.trend)}).reindex(s.index)


def var_ia(df):
    return 100 * (df / df.shift(12) - 1)


def nacional_tj(panel: pd.DataFrame) -> pd.DataFrame:
    """TJ mensuales del pais: columnas <sector>_<fuente> y <sector>_total (NaN si falta una fuente)."""
    w = panel.pivot_table(index='fecha', columns=['sector', 'fuente'], values='tj', aggfunc='sum')
    w = w.reindex(columns=pd.MultiIndex.from_product([SECTORES, FUENTES]))
    # un mes sin datos de una fuente (p. ej. gas del ultimo mes) queda NaN, no 0
    hay = panel.groupby(['fecha', 'fuente']).size().unstack().reindex(columns=FUENTES).notna()
    for (sec, fu) in w.columns:
        w.loc[~hay[fu].reindex(w.index, fill_value=False), (sec, fu)] = np.nan
    out = pd.DataFrame(index=w.index)
    for sec in SECTORES:
        for fu in FUENTES:
            out[f'{sec}_{fu}'] = w[(sec, fu)]
        out[f'{sec}_total'] = w[sec].sum(axis=1, min_count=2)
    out.index.name = 'fecha'
    return out


def indices_nacionales(tj: pd.DataFrame, series: pd.DataFrame) -> pd.DataFrame:
    """Indices base BASE = 100 (original, desestacionalizado y tendencia) y el IPI manufacturero."""
    tj = tj.loc['2012-01-01':]
    out = pd.DataFrame(index=tj.index)
    for sec in SECTORES:
        for fu in FUENTES:
            out[f'{sec}_{fu}'] = a_base(tj[f'{sec}_{fu}'])
        d = desestacionalizar(a_base(tj[f'{sec}_total']))
        out[sec] = d['original']
        out[f'{sec}_desest'] = d['desest']
        out[f'{sec}_tendencia'] = d['tendencia']
    ipi = series[['ipi_original', 'ipi_desest']].reindex(out.index)
    out['ipi_manufacturero'] = a_base(ipi['ipi_original'])
    out['ipi_manufacturero_desest'] = a_base(ipi['ipi_desest'])
    # intensidad energetica de la industria: energia por unidad de produccion (ambos desestacionalizados)
    out['intensidad_industria'] = 100 * out['industria_desest'] / out['ipi_manufacturero_desest']
    return out


def variaciones(tj: pd.DataFrame) -> pd.DataFrame:
    """Variacion interanual (%) de cada sector y contribucion de cada fuente (p.p.), sobre la serie original."""
    tj = tj.loc['2012-01-01':]
    out = pd.DataFrame(index=tj.index)
    for sec in SECTORES:
        out[f'{sec}'] = var_ia(tj[f'{sec}_total'])
        for fu in FUENTES:
            out[f'{sec}_{fu}'] = var_ia(tj[f'{sec}_{fu}'])
            out[f'{sec}_contrib_{fu}'] = 100 * (tj[f'{sec}_{fu}'] - tj[f'{sec}_{fu}'].shift(12)) / tj[f'{sec}_total'].shift(12)
    return out


def anual(tj: pd.DataFrame) -> pd.DataFrame:
    """TJ por anio (solo anios completos para cada columna) y participacion de la electricidad."""
    a = tj.groupby(tj.index.year).sum(min_count=12)
    meses = tj.notna().groupby(tj.index.year).sum()
    a = a.where(meses == 12)
    for sec in SECTORES:
        a[f'{sec}_part_elec_%'] = 100 * a[f'{sec}_electricidad'] / a[f'{sec}_total']
    a.index.name = 'anio'
    return a


# ------------------------------------------------------------------------------------------------
# Provincias
# ------------------------------------------------------------------------------------------------
def provincial_12m(panel: pd.DataFrame, sector: str) -> pd.DataFrame:
    """Suma movil de 12 meses de TJ por provincia (meses donde estan las dos fuentes)."""
    p = panel[(panel['sector'] == sector) & (panel['provincia'] != SIN_PROVINCIA)]
    ult = panel.groupby('fuente')['fecha'].max().min()
    p = p[(p['fecha'] >= '2012-01-01') & (p['fecha'] <= ult)]
    w = p.pivot_table(index='fecha', columns='provincia', values='tj', aggfunc='sum').fillna(0.0)
    return w.rolling(12).sum().dropna(how='all')


def indice_provincial(panel: pd.DataFrame, sector: str) -> pd.DataFrame:
    """Suma de 12 meses / total del anio base x 100 (el valor de diciembre de BASE es 100)."""
    r = provincial_12m(panel, sector)
    return 100 * r / r.loc[f'{BASE}-12-01']


def resumen_provincial(panel: pd.DataFrame, sector: str, provincias: pd.DataFrame) -> pd.DataFrame:
    """Ultimos 12 meses por provincia: TJ, participacion, % electrico y variaciones."""
    p = panel[(panel['sector'] == sector) & (panel['provincia'] != SIN_PROVINCIA)]
    ult = panel.groupby('fuente')['fecha'].max().min()
    p = p[p['fecha'] <= ult]
    w = p.pivot_table(index='fecha', columns=['provincia', 'fuente'], values='tj', aggfunc='sum').fillna(0.0)
    r12 = w.rolling(12).sum()
    ahora, antes = r12.loc[ult], r12.loc[ult - pd.DateOffset(years=1)]
    base = r12.loc[pd.Timestamp(f'{BASE}-12-01')]
    por_fuente = ahora.unstack('fuente').reindex(columns=FUENTES).fillna(0.0)
    t = pd.DataFrame({
        'tj_12m': ahora.groupby(level='provincia').sum(),
        'tj_12m_electricidad': por_fuente['electricidad'],
        'tj_12m_anterior': antes.groupby(level='provincia').sum(),
        f'tj_{BASE}': base.groupby(level='provincia').sum(),
        'tj_2023': r12.loc[pd.Timestamp('2023-12-01')].groupby(level='provincia').sum(),
    })
    t['participacion_%'] = 100 * t['tj_12m'] / t['tj_12m'].sum()
    t['part_electricidad_%'] = 100 * t['tj_12m_electricidad'] / t['tj_12m']
    t['var_12m_vs_anterior_%'] = 100 * (t['tj_12m'] / t['tj_12m_anterior'] - 1)
    antes_fuente = antes.unstack('fuente').reindex(columns=FUENTES)
    for fu in FUENTES:  # por fuente: la electricidad es la senal mas estable (ver CONTEXTO.md)
        t[f'var_12m_vs_anterior_{fu}_%'] = 100 * (por_fuente[fu] / antes_fuente[fu] - 1)
    t['var_12m_vs_2023_%'] = 100 * (t['tj_12m'] / t['tj_2023'] - 1)
    t[f'var_12m_vs_{BASE}_%'] = 100 * (t['tj_12m'] / t[f'tj_{BASE}'] - 1)
    t = t.join(provincias.set_index('provincia')[['region']])
    t.index.name = 'provincia'
    return t.sort_values('tj_12m', ascending=False)


# ------------------------------------------------------------------------------------------------
# Otros cortes
# ------------------------------------------------------------------------------------------------
def ramas(ramas_gas: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Gas de grandes usuarios industriales por rama: TJ anuales y suma de 12 meses (indice base BASE)."""
    r = ramas_gas.assign(tj=ramas_gas['miles_m3'] * TJ_POR_MIL_M3)
    w = r.pivot_table(index='fecha', columns='rama', values='tj', aggfunc='sum').fillna(0.0).sort_index()
    meses = w.groupby(w.index.year).size()
    an = w.groupby(w.index.year).sum()
    an = an[meses.reindex(an.index) == 12]
    an.index.name = 'anio'
    r12 = w.rolling(12).sum().dropna(how='all')
    ult = w.index.max()
    ref = pd.Timestamp(f'{BASE}-12-01')
    t = pd.DataFrame({'tj_12m': r12.loc[ult], 'tj_12m_anterior': r12.loc[ult - pd.DateOffset(years=1)],
                      f'tj_{BASE}': r12.loc[ref], 'tj_2023': r12.loc[pd.Timestamp('2023-12-01')]})
    t['participacion_%'] = 100 * t['tj_12m'] / t['tj_12m'].sum()
    t['var_12m_vs_anterior_%'] = 100 * (t['tj_12m'] / t['tj_12m_anterior'] - 1)
    t['var_12m_vs_2023_%'] = 100 * (t['tj_12m'] / t['tj_2023'] - 1)
    t[f'var_12m_vs_{BASE}_%'] = 100 * (t['tj_12m'] / t[f'tj_{BASE}'] - 1)
    t = t.replace([np.inf, -np.inf], np.nan)
    t.index.name = 'rama'
    return {'anual': an, 'resumen': t.sort_values('tj_12m', ascending=False),
            'indice_12m': 100 * r12.loc['2012-01-01':] / r12.loc[ref]}


def gas_por_usuario(gas: pd.DataFrame) -> pd.DataFrame:
    """Consumo residencial de gas por usuario (m3 por mes): pais y provincias."""
    h = gas[(gas['sector'] == 'hogares') & (gas['provincia'] != SIN_PROVINCIA)]
    w = h.pivot_table(index='fecha', columns='provincia', values=['miles_m3', 'usuarios'], aggfunc='sum')
    out = 1000 * w['miles_m3'] / w['usuarios']
    out.insert(0, 'Total pais', 1000 * w['miles_m3'].sum(axis=1) / w['usuarios'].sum(axis=1))
    return out


def costa(costa_elec: pd.DataFrame, elec_pais: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    """Electricidad de las cooperativas de la Costa Atlantica (procesar.AGENTES_COSTA): temporada de verano
    (promedio mensual ene-feb) vs invierno (promedio mensual jun-ago, poblacion permanente). Con elec_pais
    (tabla electricidad del pipeline) agrega la demanda total del pais como referencia."""
    if elec_pais is not None:
        pais = elec_pais.groupby(['fecha', 'sector'], as_index=False)['mwh'].sum().assign(localidad='Total país')
        costa_elec = pd.concat([costa_elec, pais], ignore_index=True)
    w = costa_elec.pivot_table(index='fecha', columns='localidad', values='mwh', aggfunc='sum') / 1e3  # GWh
    hog = costa_elec[costa_elec['sector'] == 'hogares'].pivot_table(index='fecha', columns='localidad',
                                                                     values='mwh', aggfunc='sum') / 1e3

    def temporada(meses):
        x = w[w.index.month.isin(meses)]
        n = x.groupby(x.index.year).size()
        return x.groupby(x.index.year).mean()[n == len(meses)]

    ver, inv = temporada([1, 2]), temporada([6, 7, 8])
    meses = w.groupby(w.index.year).size()
    completos = meses[meses == 12].index
    anual = w.groupby(w.index.year).sum().loc[completos]
    perfil = w[w.index.year.isin(completos)]
    perfil = perfil / perfil.groupby(perfil.index.year).transform('mean')
    perfil = perfil.groupby(perfil.index.month).mean()     # mes / promedio mensual de su anio
    ua, uv, ui = completos.max(), ver.index.max(), inv.index.max()
    hog_anual = hog.groupby(hog.index.year).sum().loc[completos]
    t = pd.DataFrame({
        f'gwh_{ua}': anual.loc[ua],
        f'part_hogares_{ua}_%': 100 * hog_anual.loc[ua] / anual.loc[ua],
        'enero_vs_promedio': perfil.loc[1],
        f'verano_{uv}_vs_{uv - 1}_%': 100 * (ver.loc[uv] / ver.loc[uv - 1] - 1),
        f'verano_{uv}_vs_{BASE}_%': 100 * (ver.loc[uv] / ver.loc[BASE] - 1),
        f'invierno_{ui}_vs_{ui - 1}_%': 100 * (inv.loc[ui] / inv.loc[ui - 1] - 1),
        f'invierno_{ui}_vs_{BASE}_%': 100 * (inv.loc[ui] / inv.loc[BASE] - 1),
        f'verano_sobre_invierno_{BASE}': ver.loc[BASE] / inv.loc[BASE],
        f'verano_sobre_invierno_{ui}': ver.loc[ui] / inv.loc[ui],
    })
    t.index.name = 'localidad'
    temporadas = pd.concat({'verano': 100 * ver / ver.loc[BASE], 'invierno': 100 * inv / inv.loc[BASE]}, axis=1)
    return {'mensual_gwh': w, 'anual_gwh': anual, 'perfil_mensual': perfil, 'temporadas_indice': temporadas,
            'resumen': t}


def construir(panel: pd.DataFrame, gas: pd.DataFrame, ramas_gas: pd.DataFrame, series: pd.DataFrame,
              provincias: pd.DataFrame) -> dict:
    tj = nacional_tj(panel)
    R = {
        'panel': panel,
        'nacional_tj': tj,
        'indices': indices_nacionales(tj, series),
        'variaciones': variaciones(tj),
        'anual': anual(tj.loc['2012-01-01':]),
        'provincias_indice_industria': indice_provincial(panel, 'industria'),
        'provincias_indice_hogares': indice_provincial(panel, 'hogares'),
        'provincias_industria': resumen_provincial(panel, 'industria', provincias),
        'provincias_hogares': resumen_provincial(panel, 'hogares', provincias),
        'gas_por_usuario': gas_por_usuario(gas),
        'series': series,
    }
    R['ramas'] = ramas(ramas_gas)
    ult =panel.groupby('fuente')['fecha'].max()
    R['meta'] = {'base': BASE, 'ultimo_mes_electricidad': ult['electricidad'].strftime('%Y-%m'),
                 'ultimo_mes_gas': ult['gas'].strftime('%Y-%m'),
                 'ultimo_mes_indice': ult.min().strftime('%Y-%m')}
    return R

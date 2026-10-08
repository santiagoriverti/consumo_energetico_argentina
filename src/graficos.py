"""Graficos (matplotlib). Cada funcion recibe R (pipeline.calcular) y devuelve la figura.

Colores por entidad, fijos en todos los graficos: electricidad azul, gas naranja; industria / hogares /
comercio con los tres primeros colores de la paleta categorica validada; totales en tinta oscura.
Variaciones: divergente rojo-gris-azul centrada en 0 (o en 100 para indices). Regiones: convencion de
los proyectos del usuario (Pampeana seagreen, Patagonia darkorange, NOA mediumpurple, Cuyo crimson,
NEA saddlebrown).
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PatchCollection
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Polygon

from . import fuentes, indices, procesar

AZUL, NARANJA, AQUA, VIOLETA = '#2a78d6', '#eb6834', '#1baf7a', '#4a3aa7'
TINTA, TINTA_2, GRIS = '#0b0b0b', '#52514e', '#b8b7b2'
FUENTE_COLOR = {'electricidad': AZUL, 'gas': NARANJA}
SECTOR_COLOR = {'industria': AZUL, 'hogares': NARANJA, 'comercio': AQUA}
REGION_COLOR = {'Pampeana': 'seagreen', 'Patagonia': 'darkorange', 'NOA': 'mediumpurple', 'Cuyo': 'crimson',
                'NEA': 'saddlebrown'}
DIVERGENTE = LinearSegmentedColormap.from_list('div', ['#c0302f', '#e34948', '#f1f0ec', AZUL, '#1d5aa6'])

plt.rcParams.update({
    'figure.figsize': (11, 5.2), 'figure.dpi': 100, 'savefig.dpi': 150, 'savefig.bbox': 'tight',
    'font.size': 10, 'axes.titlesize': 12, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left',
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': GRIS,
    'axes.grid': True, 'grid.color': '#e6e5e1', 'grid.linewidth': 0.8, 'axes.axisbelow': True,
    'axes.labelcolor': TINTA_2, 'xtick.color': TINTA_2, 'ytick.color': TINTA_2,
    'legend.frameon': False, 'lines.linewidth': 2,
})


def _fuente(fig, texto: str = 'Fuente: CAMMESA (demanda por agente) y ENARGAS (gas entregado). '
                              'Elaboración propia.') -> None:
    fig.text(0.01, -0.02, texto, fontsize=8, color=TINTA_2, ha='left', va='top')


def _ultimo(R) -> str:
    return pd.Timestamp(R['meta']['ultimo_mes_indice']).strftime('%m/%Y')


def g01_indice_industrial(R):
    i = R['indices']
    fig, ax = plt.subplots()
    ax.plot(i.index, i['industria'], color=GRIS, lw=1, label='Serie original')
    ax.plot(i.index, i['industria_desest'], color=TINTA_2, lw=1, label='Desestacionalizada')
    ax.plot(i.index, i['industria_tendencia'], color=TINTA, lw=2.2, label='Tendencia-ciclo')
    ax.axhline(100, color=TINTA_2, lw=0.8, ls='--')
    ult = i['industria_tendencia'].dropna()
    ax.annotate(f"{ult.iloc[-1]:.1f}", (ult.index[-1], ult.iloc[-1]), xytext=(6, 0),
                textcoords='offset points', va='center', fontsize=9, color=TINTA)
    ax.set_title(f'Índice de consumo energético industrial (electricidad + gas, {indices.BASE} = 100)')
    ax.set_ylabel(f'{indices.BASE} = 100')
    ax.legend(loc='lower left')
    _fuente(fig)
    return fig


def g02_componentes_industria(R):
    i = R['indices']
    fig, ax = plt.subplots()
    for fu in indices.FUENTES:
        s = i[f'industria_{fu}'].rolling(12).mean()
        ax.plot(s.index, s, color=FUENTE_COLOR[fu], label=fu.capitalize())
        ax.annotate(f'{s.dropna().iloc[-1]:.1f}', (s.dropna().index[-1], s.dropna().iloc[-1]), xytext=(6, 0),
                    textcoords='offset points', va='center', fontsize=9, color=TINTA)
    s = i['industria'].rolling(12).mean()
    ax.plot(s.index, s, color=TINTA, lw=1.2, ls='--', label='Total (energía)')
    ax.axhline(100, color=TINTA_2, lw=0.8, ls=':')
    ax.set_title(f'Industria: consumo por fuente (promedio móvil 12 meses, {indices.BASE} = 100)')
    ax.set_ylabel(f'{indices.BASE} = 100')
    ax.legend(loc='lower left')
    _fuente(fig)
    return fig


def g03_industria_vs_ipi(R):
    i = R['indices'].loc[f'{indices.BASE}-01-01':]
    fig, ax = plt.subplots()
    ax.plot(i.index, i['industria_desest'], color=TINTA, label='Consumo energético industrial (desest.)')
    ax.plot(i.index, i['ipi_manufacturero_desest'], color=VIOLETA, label='IPI manufacturero INDEC (desest.)')
    ax.axhline(100, color=TINTA_2, lw=0.8, ls='--')
    ax.set_title(f'Energía consumida por la industria vs producción industrial ({indices.BASE} = 100)')
    ax.set_ylabel(f'{indices.BASE} = 100')
    ax.legend(loc='lower left')
    _fuente(fig, 'Fuente: CAMMESA, ENARGAS e INDEC (IPI manufacturero). Elaboración propia.')
    return fig


def g04_hogares(R):
    i = R['indices']
    fig, ax = plt.subplots()
    for fu in indices.FUENTES:
        s = i[f'hogares_{fu}'].rolling(12).mean()
        ax.plot(s.index, s, color=FUENTE_COLOR[fu], label=fu.capitalize())
    s = i['hogares'].rolling(12).mean()
    ax.plot(s.index, s, color=TINTA, lw=1.2, ls='--', label='Total (energía)')
    ax.axhline(100, color=TINTA_2, lw=0.8, ls=':')
    ax.set_title(f'Hogares: consumo residencial por fuente (promedio móvil 12 meses, {indices.BASE} = 100)')
    ax.set_ylabel(f'{indices.BASE} = 100')
    ax.legend(loc='upper left')
    _fuente(fig)
    return fig


def g05_contribuciones(R, meses: int = 36):
    v = R['variaciones'][['industria', 'industria_contrib_electricidad', 'industria_contrib_gas']].dropna()
    v = v.iloc[-meses:]
    fig, ax = plt.subplots()
    x = np.arange(len(v))
    pos, neg = np.zeros(len(v)), np.zeros(len(v))
    for fu in indices.FUENTES:
        c = v[f'industria_contrib_{fu}'].to_numpy()
        base = np.where(c >= 0, pos, neg)
        ax.bar(x, c, bottom=base, width=0.8, color=FUENTE_COLOR[fu], label=f'Aporte {fu}',
               edgecolor='white', linewidth=1)
        pos, neg = pos + np.clip(c, 0, None), neg + np.clip(c, None, 0)
    ax.plot(x, v['industria'], color=TINTA, marker='o', ms=3, lw=1.5, label='Variación total')
    ax.axhline(0, color=TINTA_2, lw=0.8)
    ax.set_xticks(x[::3])
    ax.set_xticklabels(v.index[::3].strftime('%m/%y'), rotation=0)
    ax.set_ylabel('%  /  p.p.')
    ax.set_title('Industria: variación interanual del consumo de energía y aporte de cada fuente')
    ax.legend(loc='lower left', ncols=3)
    _fuente(fig)
    return fig


# ------------------------------------------------------------------------------------------------
# Mapas y provincias
# ------------------------------------------------------------------------------------------------
def _geometrias() -> list[tuple[str, list]]:
    d = json.loads((fuentes.REFERENCIA / 'provincias.geojson').read_text(encoding='utf-8'))
    cod = {}
    for _, r in procesar.provincias().iterrows():
        for c in r['codigos_indec'].split('|'):
            cod[c] = r['provincia']
    return [(cod[f['properties']['codigo_indec']], f['geometry']['coordinates']) for f in d['features']]


def mapa(valores: pd.Series, ax, cmap=DIVERGENTE, norm=None, sin_dato: str = '#ffffff'):
    """Coroplético de provincias (valores indexados por la columna 'provincia' de provincias.csv)."""
    parches, colores = [], []
    norm = norm or TwoSlopeNorm(vcenter=0, vmin=min(-1, valores.min()), vmax=max(1, valores.max()))
    for prov, multipoli in _geometrias():
        v = valores.get(prov, np.nan)
        for poli in multipoli:
            parches.append(Polygon(np.asarray(poli[0]), closed=True))
            colores.append(sin_dato if pd.isna(v) else cmap(norm(v)))
    ax.add_collection(PatchCollection(parches, facecolor=colores, edgecolor='white', linewidth=0.5))
    ax.set_xlim(-74.5, -52.5)
    ax.set_ylim(-55.5, -21.5)
    ax.set_aspect(1 / np.cos(np.deg2rad(38)))
    ax.axis('off')
    return plt.cm.ScalarMappable(norm=norm, cmap=cmap)


def g06_mapa_industria(R, columna: str = 'var_12m_vs_2023_%'):
    t = R['provincias_industria']
    fig, ax = plt.subplots(figsize=(6.2, 8.5))
    lim = float(np.ceil(t[columna].abs().clip(upper=40).max() / 5) * 5)
    sm = mapa(t[columna].clip(-lim, lim), ax, norm=TwoSlopeNorm(vcenter=0, vmin=-lim, vmax=lim))
    cb = fig.colorbar(sm, ax=ax, shrink=0.5, pad=0.02)
    cb.set_label('%')
    cb.outline.set_visible(False)
    texto = {'var_12m_vs_2023_%': 'vs 2023', f'var_12m_vs_{indices.BASE}_%': f'vs {indices.BASE}',
             'var_12m_vs_anterior_%': 'vs 12 meses anteriores'}[columna]
    ax.set_title(f'Consumo energético industrial:\núltimos 12 meses a {_ultimo(R)} {texto}', fontsize=11)
    _fuente(fig, 'Fuente: CAMMESA y ENARGAS. Buenos Aires incluye CABA.\nVariaciones mayores a ±40% se '
                 'muestran en el extremo de la escala.')
    return fig


def g07_ranking_provincias(R):
    t = R['provincias_industria'].sort_values('tj_12m')
    fig, ax = plt.subplots(figsize=(10, 7.5))
    y = np.arange(len(t))
    pj = 1e3  # TJ -> PJ
    elec = t['tj_12m_electricidad'] / pj
    gas = (t['tj_12m'] - t['tj_12m_electricidad']) / pj
    ax.barh(y, elec, color=AZUL, height=0.75, label='Electricidad', edgecolor='white', linewidth=1)
    ax.barh(y, gas, left=elec, color=NARANJA, height=0.75, label='Gas', edgecolor='white', linewidth=1)
    for k, (prov, r) in enumerate(t.iterrows()):
        ax.text(r['tj_12m'] / pj, k, f"  {r['participacion_%']:.1f}%", va='center', fontsize=8, color=TINTA_2)
    ax.set_yticks(y)
    ax.set_yticklabels(t.index, fontsize=9)
    for lab in ax.get_yticklabels():
        lab.set_color(REGION_COLOR.get(t.loc[lab.get_text(), 'region'], TINTA))
    ax.grid(axis='y', visible=False)
    ax.set_xlabel('PJ (petajoules) en los últimos 12 meses')
    ax.set_title(f'Consumo energético industrial por provincia (12 meses a {_ultimo(R)}; % del país)')
    ax.legend(loc='lower right')
    _fuente(fig, 'Fuente: CAMMESA y ENARGAS. Nombre de la provincia coloreado por región. '
                 'Buenos Aires incluye CABA.')
    return fig


def g08_heatmap_provincias(R):
    ip = R['provincias_indice_industria']
    dic = ip[ip.index.month == 12]
    tabla = pd.concat([dic, ip.iloc[[-1]]]) if ip.index[-1].month != 12 else dic
    tabla.index = [str(d.year) if d.month == 12 else d.strftime('%m/%Y') for d in tabla.index]
    orden = R['provincias_industria'].index
    tabla = tabla.T.reindex(orden)
    fig, ax = plt.subplots(figsize=(12, 8))
    norm = TwoSlopeNorm(vcenter=100, vmin=50, vmax=150)
    ax.imshow(tabla.clip(50, 150).to_numpy(), cmap=DIVERGENTE, norm=norm, aspect='auto')
    for (k, j), v in np.ndenumerate(tabla.to_numpy()):
        if not np.isnan(v):
            ax.text(j, k, f'{v:.0f}', ha='center', va='center', fontsize=7,
                    color='white' if abs(v - 100) > 35 else TINTA)
    ax.set_xticks(range(tabla.shape[1]))
    ax.set_xticklabels(tabla.columns, fontsize=8)
    ax.set_yticks(range(tabla.shape[0]))
    ax.set_yticklabels(tabla.index, fontsize=8)
    ax.grid(False)
    ax.set_title(f'Consumo energético industrial por provincia: suma de 12 meses ({indices.BASE} = 100)')
    _fuente(fig, 'Fuente: CAMMESA y ENARGAS. Provincias ordenadas por consumo. Columnas: 12 meses a '
                 'diciembre de cada año y al último mes.')
    return fig


def g09_ramas(R):
    t = R['ramas']['resumen'].dropna(subset=['var_12m_vs_2023_%']).sort_values('var_12m_vs_2023_%')
    fig, ax = plt.subplots(figsize=(10, 6.5))
    col = [AZUL if v >= 0 else '#e34948' for v in t['var_12m_vs_2023_%']]
    ax.barh(t.index, t['var_12m_vs_2023_%'], color=col, height=0.7)
    for k, (rama, r) in enumerate(t.iterrows()):
        v = r['var_12m_vs_2023_%']
        ax.text(v, k, f" {v:+.1f}% ({r['participacion_%']:.0f}% del total) ", va='center', fontsize=8,
                color=TINTA_2, ha='left' if v >= 0 else 'right')
    ax.axvline(0, color=TINTA_2, lw=0.8)
    vmin, vmax = min(t['var_12m_vs_2023_%'].min(), 0), max(t['var_12m_vs_2023_%'].max(), 0)
    ax.set_xlim(vmin - 0.45 * (vmax - vmin) * (vmin < 0), vmax + 0.35 * (vmax - vmin))  # lugar para las etiquetas
    ax.grid(axis='y', visible=False)
    ax.set_xlabel('%')
    ult = pd.Timestamp(R['ramas']['indice_12m'].index[-1]).strftime('%m/%Y')
    ax.set_title(f'Gas de grandes usuarios industriales por rama: 12 meses a {ult} vs 2023')
    _fuente(fig, 'Fuente: ENARGAS (gas entregado a grandes usuarios industriales de las distribuidoras; '
                 'no incluye by-pass).')
    return fig


def g10_gas_por_usuario(R):
    g = R['gas_por_usuario']['Total pais']
    fig, ax = plt.subplots()
    ax.plot(g.index, g, color=GRIS, lw=1, label='Mensual')
    m = g.rolling(12).mean()
    ax.plot(m.index, m, color=NARANJA, label='Promedio móvil 12 meses')
    ax.set_ylabel('m³ por usuario por mes')
    ax.set_title('Hogares: consumo de gas natural por usuario residencial')
    ax.legend(loc='upper left')
    _fuente(fig, 'Fuente: ENARGAS (usuarios residenciales en condiciones de ser facturados).')
    return fig


def g11_costa_atlantica(R):
    t = R['costa']['temporadas_indice']
    locs = [c for c in t['verano'].columns if c != 'Total país']
    fig, axs = plt.subplots(1, len(locs), figsize=(11, 4.6), sharey=True)
    for ax, loc in zip(np.atleast_1d(axs), locs):
        for temp, col, etiqueta in [('verano', NARANJA, 'Verano (ene-feb)'), ('invierno', AZUL, 'Invierno (jun-ago)')]:
            s = t[temp][loc].dropna()
            ax.plot(s.index, s, color=col, marker='o', ms=4, label=etiqueta)
            ax.annotate(f'{s.iloc[-1]:.0f}', (s.index[-1], s.iloc[-1]), xytext=(6, 0), textcoords='offset points',
                        va='center', fontsize=9, color=TINTA)
        ax.axhline(100, color=TINTA_2, lw=0.8, ls='--')
        ax.set_title(loc, fontsize=11)
    np.atleast_1d(axs)[0].set_ylabel(f'demanda mensual promedio ({indices.BASE} = 100)')
    np.atleast_1d(axs)[0].legend(loc='lower left')
    fig.suptitle('Costa Atlántica: demanda eléctrica de temporada y de invierno', x=0.01, ha='left',
                 fontweight='bold', fontsize=12)
    _fuente(fig, 'Fuente: CAMMESA (demanda de las cooperativas eléctricas de Villa Gesell y San Bernardo). '
                 'Elaboración propia.')
    return fig


GRAFICOS = {
    '01_indice_industrial': g01_indice_industrial,
    '02_industria_por_fuente': g02_componentes_industria,
    '03_industria_vs_ipi': g03_industria_vs_ipi,
    '04_hogares_por_fuente': g04_hogares,
    '05_industria_contribuciones': g05_contribuciones,
    '06_mapa_industria': g06_mapa_industria,
    '07_ranking_provincias': g07_ranking_provincias,
    '08_heatmap_provincias': g08_heatmap_provincias,
    '09_ramas_gas': g09_ramas,
    '10_gas_por_usuario': g10_gas_por_usuario,
    '11_costa_atlantica': g11_costa_atlantica,
}

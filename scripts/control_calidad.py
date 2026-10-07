"""Controles de calidad de los datos y del indice. Correr antes de commitear resultados nuevos.

Uso:  python scripts/control_calidad.py     (imprime los controles y la cantidad de ALERTAS)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import fuentes, pipeline, procesar  # noqa: E402

ALERTAS: list[str] = []
pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 20)


def chequear(ok: bool, mensaje: str) -> None:
    print(('  ok      ' if ok else '  ALERTA  ') + mensaje)
    if not ok:
        ALERTAS.append(mensaje)


def anual_completo(s: pd.Series) -> pd.Series:
    n = s.groupby(s.index.year).count()
    return s.groupby(s.index.year).sum()[n == 12]


def main() -> int:
    T = pipeline.leer()
    e, g, s = T['electricidad'], T['gas'], T['series']

    print('\n1. Electricidad (CAMMESA por agente) vs totales nacionales de CAMMESA publicados por la SSPM')
    ea = e.pivot_table(index='fecha', columns='sector', values='mwh', aggfunc='sum') / 1e3
    tot = anual_completo(ea.sum(axis=1))
    res = anual_completo(ea['hogares'])
    ref_tot, ref_res = anual_completo(s['elec_total'].dropna()), anual_completo(s['elec_residencial'].dropna())
    d_tot = (100 * (tot / ref_tot - 1)).dropna()
    d_res = (100 * (res / ref_res - 1)).dropna()
    print(pd.DataFrame({'dif_total_%': d_tot, 'dif_residencial_%': d_res}).round(3).T.to_string())
    chequear(d_tot.abs().max() < 0.5, f'demanda total: diferencia maxima {d_tot.abs().max():.3f}% (tolerancia 0,5%)')
    chequear(d_res.abs().max() < 0.5, f'demanda residencial: diferencia maxima {d_res.abs().max():.3f}% (tolerancia 0,5%)')

    print('\n2. Tarifas sin clasificar y demanda sin provincia')
    t = T['tarifas']
    chequear((t['sector'] == 'sin_clasificar').sum() == 0,
             f"tarifas sin clasificar: {list(t.loc[t['sector'] == 'sin_clasificar', 'tarifa'])}")
    sp = e.loc[e['provincia'] == procesar.SIN_PROVINCIA, 'mwh'].sum() / e['mwh'].sum()
    chequear(sp < 0.001, f'electricidad sin provincia: {100 * sp:.3f}% del total')
    sg = g.loc[g['provincia'] == procesar.SIN_PROVINCIA, 'miles_m3'].sum() / g['miles_m3'].sum()
    chequear(sg < 0.005, f'gas sin provincia: {100 * sg:.3f}% del total')

    print('\n3. Saltos en la electricidad industrial cuando cambia la nomenclatura de tarifas o de base')
    print('   (var. i.a. del bimestre que empieza en el cambio vs la del bimestre anterior: los bimestres')
    print('   neutralizan feriados moviles como Carnaval, que en 2026 cayo en febrero y en 2025 en marzo)')
    ind = ea['industria']
    bim = ind.rolling(2).sum()
    via = 100 * (bim / bim.shift(12) - 1)  # via.loc[m] = bimestre (m-1, m)
    for mes in ['2015-01-01', '2016-02-01', '2019-01-01', '2023-02-01', '2026-02-01']:
        m = pd.Timestamp(mes)
        despues, antes = via.loc[m + pd.DateOffset(months=1)], via.loc[m - pd.DateOffset(months=1)]
        salto = despues - antes
        chequear(abs(salto) < 4, f'{mes[:7]}: bimestre anterior {antes:+.1f}% i.a., bimestre desde el cambio '
                                 f'{despues:+.1f}% i.a. (salto {salto:+.1f} p.p., tolerancia 4)')

    print('\n4. Bases de CAMMESA: meses que aparecen en dos bases (2015 en las bases 2015-12 y 2018-12)')
    try:
        b15 = fuentes.leer_base_cammesa('2015-12')
        b18 = fuentes.leer_base_cammesa('2018-12')
        comp = {}
        for nom, b in [('base 2015-12', b15), ('base 2018-12', b18)]:
            b = b[b['fecha'].dt.year == 2015]
            comp[nom] = procesar.electricidad(b).groupby('sector')['mwh'].sum() / 1e6
        c = pd.DataFrame(comp)
        c['dif_%'] = 100 * (c.iloc[:, 0] / c.iloc[:, 1] - 1)
        print(c.round(3).to_string())
        chequear(c['dif_%'].abs().max() < 1, f'2015 por sector entre bases: diferencia maxima {c["dif_%"].abs().max():.2f}%')
    except FileNotFoundError as ex:
        print('  (sin cache de CAMMESA: correr scripts/construir.py)', ex)

    print('\n5. Gas (ENARGAS distribucion + by-pass industrial) vs totales de ENARGAS publicados por la SSPM')
    ga = g.pivot_table(index='fecha', columns='sector', values='miles_m3', aggfunc='sum') / 1e3
    pares = {'hogares': s['gas_residencial'], 'industria': s['gas_industria'],
             'comercio': s['gas_comercial'] + s['gas_entes_oficiales']}
    filas = {}
    for sec, ref in pares.items():
        a, b = anual_completo(ga[sec].loc['1996-01-01':]), anual_completo(ref.dropna())
        filas[sec] = (100 * (a / b - 1)).dropna()
    d = pd.DataFrame(filas)
    print(d.loc[2010:].round(2).T.to_string())
    for sec in pares:
        x = d[sec].loc[2012:]
        chequear(x.abs().max() < 3, f'gas {sec} 2012+: diferencia maxima {x.abs().max():.2f}% (tolerancia 3%)')

    print('\n6. Cobertura')
    ult = {'electricidad': e['fecha'].max(), 'gas': g['fecha'].max()}
    print(f"  ultimo mes: electricidad {ult['electricidad']:%Y-%m}, gas {ult['gas']:%Y-%m}")
    for nom, df in [('electricidad', e), ('gas', g)]:
        meses = pd.date_range(df['fecha'].min(), df['fecha'].max(), freq='MS')
        faltan = meses.difference(pd.DatetimeIndex(df['fecha'].unique()))
        chequear(len(faltan) == 0, f'{nom}: meses faltantes {list(faltan.strftime("%Y-%m"))}')
    atraso = (pd.Timestamp.today().to_period('M') - ult['gas'].to_period('M')).n
    chequear(atraso <= 4, f'atraso del gas: {atraso} meses')

    print(f'\n{len(ALERTAS)} ALERTAS')
    for a in ALERTAS:
        print('  -', a)
    return 0 if not ALERTAS else 1


if __name__ == '__main__':
    sys.exit(main())

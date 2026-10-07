"""Construye todo: baja las fuentes, arma las tablas base (data/processed/), calcula los indices y
escribe output/ (Excel + graficos). Imprime las cifras principales.

Uso:  python scripts/construir.py              (usa lo que ya esta en data/cache/)
      python scripts/construir.py --refrescar  (vuelve a bajar todo: nuevo mes de CAMMESA / ENARGAS)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import exportar, fuentes, indices, pipeline  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--refrescar', action='store_true', help='volver a bajar las fuentes')
    args = ap.parse_args()

    pipeline.preparar(refrescar=args.refrescar)
    R = pipeline.calcular()
    exportar.exportar(R, fuentes.RAIZ / 'output', con_csv=False)

    m, i, v = R['meta'], R['indices'], R['variaciones']
    ult = i['industria'].last_valid_index()
    print(f"\nUltimo mes: electricidad {m['ultimo_mes_electricidad']}, gas {m['ultimo_mes_gas']}")
    print(f"ICE industria {ult:%m/%Y}: {i.loc[ult, 'industria']:.1f} (desest. {i.loc[ult, 'industria_desest']:.1f}), "
          f"var. i.a. {v.loc[ult, 'industria']:+.1f}% (electricidad {v.loc[ult, 'industria_contrib_electricidad']:+.1f} p.p., "
          f"gas {v.loc[ult, 'industria_contrib_gas']:+.1f} p.p.)")
    print(f"ICE hogares {ult:%m/%Y}: {i.loc[ult, 'hogares']:.1f} (desest. {i.loc[ult, 'hogares_desest']:.1f}), "
          f"var. i.a. {v.loc[ult, 'hogares']:+.1f}%")
    a = R['anual']
    print('\nTJ anuales (miles) y % electrico:')
    print((a[['industria_total', 'hogares_total', 'comercio_total']] / 1e3).round(0).join(
        a[['industria_part_elec_%', 'hogares_part_elec_%']].round(1)).dropna().to_string())
    t = R['provincias_industria']
    print(f'\nIndustria por provincia (12 meses a {m["ultimo_mes_indice"]}):')
    print(t[['participacion_%', 'part_electricidad_%', 'var_12m_vs_anterior_%', 'var_12m_vs_2023_%',
             f'var_12m_vs_{indices.BASE}_%']].round(1).to_string())
    print('\nescrito output/', exportar.EXCEL, '+ output/graficos/')


if __name__ == '__main__':
    main()

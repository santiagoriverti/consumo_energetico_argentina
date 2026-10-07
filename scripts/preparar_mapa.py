"""Genera data/reference/provincias.geojson (limites provinciales simplificados) desde el WFS del IGN.

Se corre una sola vez (el resultado se versiona). El original pesa ~110 MB; simplificado (Douglas-Peucker,
tolerancia 0,02 grados) queda en unos cientos de KB, suficiente para mapas a escala pais. Se descartan la
Antartida y las islas del Atlantico Sur al este de las Malvinas (no hay datos de energia y deforman el mapa).

Uso:  python scripts/preparar_mapa.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import fuentes  # noqa: E402

URL = ('https://wms.ign.gob.ar/geoserver/ign/ows?service=WFS&version=1.0.0&request=GetFeature'
       '&typeName=ign:provincia&outputFormat=application/json')
TOLERANCIA = 0.02          # grados
LAT_MIN, LON_MAX = -56.0, -55.0


def rdp(p: np.ndarray, eps: float) -> np.ndarray:
    """Douglas-Peucker iterativo."""
    n = len(p)
    if n < 4:
        return p
    keep = np.zeros(n, dtype=bool)
    keep[0] = keep[-1] = True
    pila = [(0, n - 1)]
    while pila:
        i, j = pila.pop()
        if j <= i + 1:
            continue
        a, b = p[i], p[j]
        seg = p[i + 1:j]
        ab = b - a
        largo = np.hypot(*ab)
        if largo == 0:
            d = np.hypot(*(seg - a).T)
        else:
            d = np.abs(ab[0] * (seg[:, 1] - a[1]) - ab[1] * (seg[:, 0] - a[0])) / largo
        k = int(np.argmax(d))
        if d[k] > eps:
            m = i + 1 + k
            keep[m] = True
            pila += [(i, m), (m, j)]
    return p[keep]


def simplificar_anillo(anillo: list) -> list | None:
    p = np.asarray(anillo, dtype=float)[:, :2]
    if p[:, 1].max() < LAT_MIN or p[:, 0].min() > LON_MAX:
        return None
    # cortar el anillo cerrado en dos mitades para que Douglas-Peucker no colapse
    mitad = len(p) // 2
    q = np.vstack([rdp(p[:mitad + 1], TOLERANCIA)[:-1], rdp(p[mitad:], TOLERANCIA)])
    if len(q) < 4:
        return None
    return np.round(q, 3).tolist()


def main() -> None:
    crudo = fuentes.bajar(URL, fuentes.CACHE / 'ign_provincias.json')
    d = json.loads(crudo.read_text(encoding='utf-8'))
    salida = []
    for f in d['features']:
        polis = []
        for poli in f['geometry']['coordinates']:
            anillos = [simplificar_anillo(a) for a in poli]
            if anillos and anillos[0] is not None:
                polis.append([a for a in anillos if a is not None])
        salida.append({'type': 'Feature',
                       'properties': {'codigo_indec': f['properties']['in1'], 'nombre': f['properties']['nam']},
                       'geometry': {'type': 'MultiPolygon', 'coordinates': polis}})
    destino = fuentes.REFERENCIA / 'provincias.geojson'
    destino.write_text(json.dumps({'type': 'FeatureCollection', 'features': salida}, ensure_ascii=False,
                                  separators=(',', ':')), encoding='utf-8')
    print('escrito', destino.relative_to(fuentes.RAIZ), f'{destino.stat().st_size / 1e3:.0f} KB',
          sum(len(a) for f in salida for p in f['geometry']['coordinates'] for a in p), 'vertices')


if __name__ == '__main__':
    main()

"""Compila la seccion del informe INECO con el preambulo del documento completo, para verificar que no
tenga errores antes de pasarla al Overleaf.

Copia docs/informe_indicadores/seccion_energia.tex, bibitems_energia.tex y las figuras que cita (desde
output/graficos/) a _local_run/latex/ (ignorado por git) y corre pdflatex dos veces. Falla si falta una
figura o una referencia, si pdflatex da error o si hay cajas desbordadas (overfull).

Requiere pdflatex (MiKTeX o TeX Live). Uso:  python scripts/probar_latex.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / 'docs' / 'informe_indicadores'
DESTINO = RAIZ / '_local_run' / 'latex'

# Mismo preambulo que el documento "Propuesta de Indicadores Economicos" (Overleaf del usuario)
PREAMBULO = r'''\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish]{babel}
\usepackage{lmodern}
\usepackage[margin=2.5cm]{geometry}
\usepackage{amsmath}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{xcolor}
\usepackage{titlesec}
\usepackage[hidelinks]{hyperref}
\definecolor{titulos}{RGB}{20,60,20}
\titleformat{\section}{\Large\bfseries\color{titulos}}{\thesection.}{0.6em}{}
\titleformat{\subsection}{\large\bfseries\color{titulos}}{\thesubsection.}{0.6em}{}
'''

MAIN = PREAMBULO + r'''\begin{document}
\input{seccion_energia}
\clearpage
\begin{thebibliography}{99}
\input{bibitems_energia}
\end{thebibliography}
\end{document}
'''


def main() -> int:
    pdflatex = shutil.which('pdflatex')
    if not pdflatex:
        print('No se encontro pdflatex (instalar MiKTeX o TeX Live).')
        return 1
    seccion = (DOCS / 'seccion_energia.tex').read_text(encoding='utf-8')
    bib = (DOCS / 'bibitems_energia.tex').read_text(encoding='utf-8')
    problemas = []

    figuras = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{figuras/([^}]+)\}', seccion)
    citas = {c.strip() for grupo in re.findall(r'\\cite\{([^}]+)\}', seccion) for c in grupo.split(',')}
    claves = set(re.findall(r'\\bibitem\{([^}]+)\}', bib))
    problemas += [f'falta el bibitem {c}' for c in sorted(citas - claves)]

    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    (DESTINO / 'figuras').mkdir(parents=True)
    for f in figuras:
        origen = RAIZ / 'output' / 'graficos' / f
        if origen.exists():
            shutil.copy(origen, DESTINO / 'figuras' / f)
        else:
            problemas.append(f'falta la figura output/graficos/{f}')
    shutil.copy(DOCS / 'seccion_energia.tex', DESTINO)
    shutil.copy(DOCS / 'bibitems_energia.tex', DESTINO)
    (DESTINO / 'main.tex').write_text(MAIN, encoding='utf-8')

    if not problemas:
        for _ in range(2):  # dos pasadas para las referencias cruzadas
            subprocess.run([pdflatex, '-interaction=nonstopmode', '-halt-on-error', 'main.tex'], cwd=DESTINO,
                           capture_output=True)
        log = (DESTINO / 'main.log').read_text(encoding='latin-1')
        problemas += [l for l in log.splitlines() if l.startswith('!')]
        problemas += [l for l in log.splitlines() if 'Overfull' in l or re.search(r'(Citation|Reference).*undefined', l)]
        paginas = re.search(r'Output written on main\.pdf \((\d+) page', log)
        print(f'Figuras: {len(figuras)} · citas: {len(citas)} · paginas: {paginas.group(1) if paginas else "?"}')
        print(f'PDF: {DESTINO / "main.pdf"}')

    for p in problemas:
        print('  PROBLEMA ', p)
    print('OK: compila sin errores ni advertencias' if not problemas else f'{len(problemas)} problemas')
    return 0 if not problemas else 1


if __name__ == '__main__':
    sys.exit(main())

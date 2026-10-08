# Sección del informe INECO "Propuesta de Indicadores Económicos"

El documento completo (siete secciones, una por indicador) está en el **Overleaf del usuario**. Este repo
guarda solo la sección del índice de consumo energético.

| Archivo | Qué es |
|---|---|
| `seccion_energia.tex` | `\section{Consumo de Energía en Argentina y en Pinamar}`: metodología, resultados nacionales y provinciales, foco local (Costa Atlántica) y propuesta para Pinamar y General Madariaga. Se pega en el Overleaf reemplazando la sección |
| `bibitems_energia.tex` | Las 6 referencias nuevas (`cammesa`, `enargas`, `indec_ipi`, `sspm`, `stl`, `indec_censo`). Se pegan dentro de `thebibliography` del documento |

## Figuras

La sección usa 4 gráficos de `output/graficos/`, que en el Overleaf van en la carpeta `figuras/` con el
mismo nombre: `01_indice_industrial.png`, `03_industria_vs_ipi.png`, `07_ranking_provincias.png` y
`11_costa_atlantica.png`. Los nombres no chocan con los de las otras secciones del documento (verificado en
oct-2026 contra las secciones del Overleaf y las de los repos IPC_jubilados, indice_inmobiliario_argentina e
infraestuctura_argentina).

## Cuando cambian los datos

1. `python scripts/construir.py --refrescar` y `python scripts/control_calidad.py` (0 ALERTAS).
2. Actualizar en `seccion_energia.tex` las cifras que cambien (la lista está en `ESTADO.md` §2 y §3). Las
   cifras salen de lo que imprime `construir.py` y de `R['costa']['resumen']` (notebook 02).
3. `python scripts/probar_latex.py` → "OK: compila sin errores ni advertencias".
4. Volver a subir al Overleaf la sección y las 4 figuras.

## Convenciones del documento (para mantener el estilo de las otras secciones)

- Estructura: párrafo introductorio, `\subsection{Metodología}`, `\subsection{Resultados}` (acá además
  `\subsection{Foco local: ...}`).
- Decimales con coma (`8,1\%`), miles con punto (`141.251`); negativos en tablas como `$-2{,}5$`.
- Cuadros con `booktabs`, `\small`, `\caption` arriba y nota al pie en `\parbox` con `\footnotesize`
  ("Fuente: INECO--UADE en base a ...").
- Figuras `[!htb]`, centradas, con `\caption` descriptivo y `\label{fig:ice_...}`; cuadros `\label{tab:ice_...}`.
- Pendiente del documento completo (no de esta sección): la introducción habla de "seis indicadores" y
  del orden del boletín; con esta sección son siete.

# scripts/

Todos se corren desde la raíz del repo, con `PYTHONUTF8=1` en Windows.

| Script | Qué hace | Cuándo |
|---|---|---|
| `construir.py [--refrescar]` | Fuentes → `data/processed/` → índices → `output/` (Excel + 11 gráficos). Imprime las cifras principales. Sin `--refrescar` usa `data/cache/`; si falta algo, lo baja | Cada vez que cambia el código o los datos. `--refrescar` una vez por mes (nuevo dato de CAMMESA / ENARGAS) |
| `control_calidad.py` | 6 bloques de controles (validación contra la SSPM, tarifas sin clasificar, saltos de nomenclatura, bases de CAMMESA superpuestas, gas contra la SSPM, cobertura). Termina con `N ALERTAS` y sale con código 1 si hay alertas | Antes de cada commit con datos nuevos. Esperable: **0 ALERTAS** |
| `gen_notebooks.py` | Escribe `notebooks/01_evolucion_nacional.ipynb` y `02_provincias.ipynb` (sin outputs) | Cada vez que cambia el contenido de un notebook: **los .ipynb no se editan a mano** |
| `probar_latex.py` | Compila `docs/informe_indicadores/seccion_energia.tex` con el preámbulo del informe INECO en `_local_run/latex/`; falla si falta una figura o un bibitem, si hay errores o cajas desbordadas | Cada vez que cambia la sección o sus cifras. Requiere pdflatex (MiKTeX en la PC del usuario) |
| `preparar_mapa.py` | Baja los límites provinciales del IGN (~110 MB) y escribe `data/reference/provincias.geojson` simplificado | Solo si hay que regenerar el mapa (está versionado) |

## Duración aproximada (PC del usuario)

- `construir.py` con el cache completo: menos de un minuto. En una PC nueva: unos minutos (baja ~100 MB
  y lee los Excel de CAMMESA, ~1 minuto cada uno).
- `control_calidad.py`: ~30 segundos (lee las bases 2015-12 y 2018-12 del cache; si no están, las baja).
- `pytest`: segundos.

## Probar los notebooks sin ensuciar los del repo

```bash
python scripts/gen_notebooks.py
mkdir -p _local_run && cp notebooks/*.ipynb _local_run/
cd _local_run
python -m jupyter nbconvert --to notebook --execute --inplace 01_evolucion_nacional.ipynb
python -m jupyter nbconvert --to notebook --execute --inplace 02_provincias.ipynb
```

`_local_run/` y `_descargas/` (donde los notebooks dejan el ZIP) están en `.gitignore`.

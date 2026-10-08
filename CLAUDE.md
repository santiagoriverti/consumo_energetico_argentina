# CLAUDE.md — instrucciones para sesiones de Claude en este repo

## Al empezar

1. `git pull` antes de cualquier cambio (el usuario trabaja desde más de una PC).
2. Leer **`ESTADO.md`** (estado, cifras vigentes, dónde se citan, próximos pasos, rutina, PC nueva).
3. Si hay que tocar cálculos: leer **`CONTEXTO.md`** (fuentes, decisiones, trampas).
4. Según la tarea: `data/README.md` (tablas y columnas), `scripts/README.md` (qué hace cada script),
   `docs/informe_indicadores/README.md` (sección LaTeX del informe INECO).
5. Historial de sesiones: `.claude/memory/project.md`.
6. Si `data/cache/` está vacía (PC nueva o clon nuevo), `python scripts/construir.py` la llena (~100 MB).

## Reglas del usuario

- **Commits solo con el usuario (Santiago Riverti). NUNCA agregar `Co-Authored-By: Claude`** ni
  ninguna atribución a Claude en commits o PRs. Commit/push solo cuando el usuario lo pide.
- Idioma: español (rioplatense) en respuestas, commits y documentación.
- El usuario corre los notebooks en **Google Colab** (cada notebook clona el repo desde GitHub: un
  cambio no llega a Colab hasta que se pushea). La primera celda imprime "Version del repo": pedirle que
  la chequee cuando pasa resultados.
- **Cada notebook termina descargando un ZIP con todo** (Excel, gráficos PNG, CSV y LEEME.txt), vía
  `src.exportar.zip_resultados`. Escribe en `_descargas/` (ignorado); no toca `data/processed` ni
  `output/`, que solo actualiza `scripts/construir.py`.
- La sección LaTeX (`docs/informe_indicadores/seccion_energia.tex`) es para el documento "Propuesta de
  Indicadores Económicos" del INECO-UADE, que vive en el Overleaf del usuario: se le pasa el código para
  copiar y pegar y las figuras de `output/graficos/`.
- Repo **público**.

## Reglas técnicas que muerden

- Windows: correr Python con `PYTHONUTF8=1`.
- **Los `.ipynb` se generan con `python scripts/gen_notebooks.py`**: no editarlos a mano ni con
  NotebookEdit. Se versionan sin outputs.
- **No escribir scripts ni ediciones con heredocs de bash** (rompen `\\` y `\n`). Usar las
  herramientas de archivos o un `.py` aparte.
- Probar notebooks sin ensuciar los del repo: copiarlos a `_local_run/` (ignorado) y ejecutar con
  `python -m jupyter nbconvert --to notebook --execute --inplace` (ver `scripts/README.md`).
- **El sector eléctrico se asigna por TARIFA** (`procesar.sector_tarifa`), nunca por la columna
  "CATEGORIA TARIFA" de CAMMESA (cambió de criterio en feb-2016 y en 2026). Si aparece una tarifa nueva,
  `control_calidad.py` la marca como "sin clasificar": agregarla a las reglas y a `tests/`.
- CAMMESA: el certificado de `microfe.cammesa.com` y el de `enargas.gob.ar` no validan en Python
  (`fuentes._get` reintenta con `verify=False` solo ante un SSLError; la integridad se controla contra la
  SSPM). La BDI vigente cambia de nombre cada mes (`BASE_INFORME_MENSUAL_AAAA-MM.zip`;
  `periodo_cammesa_vigente` busca hasta 7 meses atrás); las históricas (2015-12, 2018-12, 2022-12) son fijas.
- ENARGAS: los datos completos están en el **pivot cache** de cada planilla (`fuentes.leer_pivot_caches`);
  las hojas visibles son tablas dinámicas filtradas. Los caches se identifican por sus campos.
- Costa Atlántica: solo hay datos de los agentes de `procesar.AGENTES_COSTA` (Villa Gesell `CEVIGE3W`, San
  Bernardo `CSBERN3W`). Pinamar y General Madariaga **no** son agentes del MEM: no inventar cifras locales.
- **Cifras citadas** (README, ESTADO §2, `seccion_energia.tex`) = las que imprimen `construir.py` /
  `control_calidad.py` / `R['costa']['resumen']`. Si cambian, actualizar todos los documentos de la tabla
  de `ESTADO.md` §3 y correr `python scripts/probar_latex.py`.
- Antes de commitear resultados nuevos: `python scripts/control_calidad.py` (0 ALERTAS) y
  `python -m pytest tests -q`.
- `data/cache/` guarda las descargas (ignorado). `--refrescar` en construir.py baja todo de nuevo.
- `construir.py` es reproducible byte a byte (los `.csv.gz` se escriben con `mtime=0`) **salvo**
  `output/indice_consumo_energetico.xlsx`, que guarda la fecha de escritura: si los datos no cambiaron,
  descartarlo con `git checkout -- output/indice_consumo_energetico.xlsx` antes de commitear.

## Cierre de sesión

Actualizar `ESTADO.md` (fecha, cobertura, cifras, verificación, próximos pasos, commits) y
`.claude/memory/project.md`. Commit + push si el usuario lo pide (si el push pide credenciales, lo
hace el usuario: Claude no ingresa tokens).

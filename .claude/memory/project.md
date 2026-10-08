# Memoria del proyecto — consumo_energetico_argentina

Estado vigente: `ESTADO.md`. Este archivo es el historial de sesiones.

## Sesión 1 [2026-10-07 / 2026-10-08] — arranque, Costa Atlántica y sección LaTeX

Pedido inicial: "crear un índice de consumo energético en Argentina tomando a las industrias y ver cómo
evoluciona en el tiempo y geográficamente (también se podrían tomar hogares)". Repo nuevo (solo README).

### 2026-10-07 — v0 (commit 0b9f55a)
- Relevamiento de fuentes: CAMMESA BDI (4 bases cubren 2012-2026 por agente/provincia/tarifa), ENARGAS
  GED/GEGU/GETD (pivot caches con datos completos 1993-2026), SSPM 364/367 para validar, IPI INDEC, IGN.
- Descartado el CSV de datos.energia.gob.ar (corta en 2020 y duplica 2013-2017).
- Clasificación eléctrica por tarifa (la categoría de CAMMESA cambió en 2016 y 2026). Valida contra SSPM
  < 0,21%. Gas = GED + by-pass de GETD repartido por área de licencia; valida contra SSPM (industria y
  hogares < 0,2%, comercio < 1,5%).
- Pipeline `src/` + `scripts/` + 2 notebooks Colab con ZIP. Hallazgos: industria 12m a jul-2026 −8,1%
  (electricidad +4,0%, gas −11,8%); anomalía de un usuario "Otras industrias" en Pampeana oct-2019/mar-2020;
  Carnaval mueve feb/mar ±6% en grandes usuarios (el control de saltos usa bimestres).

### 2026-10-08 — Colab, Costa Atlántica y sección LaTeX (commit 90462d1)
- El usuario corrió los 2 notebooks en Colab con 0b9f55a: tablas idénticas a las locales.
- Pidió la sección "Consumo de energía en Pinamar" para el documento "Propuesta de Indicadores
  Económicos" (Overleaf; las otras secciones: Termómetro, Fortaleza Macro, IIJP, Infraestructura,
  Inmobiliario, Supermercados), con foco en Pinamar, Madariaga, etc.
- Pinamar y Madariaga no son agentes del MEM → se usaron las cooperativas vecinas que sí lo son (Villa
  Gesell CEVIGE3W, San Bernardo CSBERN3W): verano (ene-feb) vs invierno (jun-ago) vs total país. Desde 2016
  invierno +18% / +24% (país +10%), verano −2% / −32% (país +3,5%): la costa se desestacionaliza.
- `docs/informe_indicadores/seccion_energia.tex` (compilada con MiKTeX y el preámbulo del documento) +
  propuesta de 5 pasos para el índice local. Título: "Consumo de Energía en Argentina y en Pinamar".

### 2026-10-08 — cierre de sesión (commit siguiente a 90462d1)
- Documentación completa para retomar desde otra PC: `ESTADO.md` (PC nueva, rutina, commits),
  `CONTEXTO.md` (Costa Atlántica, certificados, reproducibilidad), `data/README.md`, `scripts/README.md`,
  `docs/informe_indicadores/README.md`, `CLAUDE.md`.
- `scripts/probar_latex.py` (compila la sección), `bibitems_energia.tex`, `.csv.gz` con `mtime=0`
  (construir.py reproducible salvo el Excel), test de `indices.costa` (28 tests).
- Pendiente: ver ESTADO §5 (decisiones metodológicas, anomalía 2019-20, datos por partido para Pinamar y
  Madariaga, ramas eléctricas, intro del Overleaf "seis → siete indicadores", re-correr NB02 en Colab).

# Memoria del proyecto — consumo_energetico_argentina

## Sesión 1 [2026-10-07] — arranque

Pedido: "crear un índice de consumo energético en Argentina tomando a las industrias y ver cómo evoluciona
en el tiempo y geográficamente (también se podrían tomar hogares)". Repo nuevo (solo README inicial).

Hecho:
- Relevamiento de fuentes: CAMMESA BDI (4 bases cubren 2012-2026 por agente/provincia/tarifa), ENARGAS
  GED/GEGU/GETD (pivot caches con datos completos 1993-2026), SSPM 364/367 para validar, IPI INDEC, IGN.
- Descartado el CSV de datos.energia.gob.ar (corta en 2020 y duplica 2013-2017).
- Clasificación eléctrica por tarifa (la categoría de CAMMESA cambió en 2016 y 2026). Valida contra SSPM
  < 0,2%. Gas = GED + by-pass de GETD repartido por área de licencia; valida contra SSPM < 0,12%.
- Pipeline: `src/` (fuentes, procesar, indices, graficos, exportar, pipeline), `scripts/` (construir,
  control_calidad, gen_notebooks, preparar_mapa), 2 notebooks Colab con ZIP, 27 tests, 0 alertas.
- Hallazgos: industria 12m a jul-2026 −8,1% (electricidad +4,0%, gas −11,8%); anomalía de un usuario
  "Otras industrias" en Pampeana oct-2019/mar-2020; Carnaval mueve feb/mar ±6% en grandes usuarios.

Pendiente: ver ESTADO §5 (decisiones metodológicas, anomalía 2019-20, ramas eléctricas, Colab).

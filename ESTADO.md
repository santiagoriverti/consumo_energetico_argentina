# ESTADO — consumo_energetico_argentina (ICE)

**Última actualización:** 2026-10-07 (sesión 1: arranque del proyecto). Punto de entrada para retomar:
este archivo → `CLAUDE.md` (reglas) → `CONTEXTO.md` (fuentes, decisiones, trampas) →
`.claude/memory/project.md` (historial).

## 0. Estado en una línea

Versión 0 funcionando y verificada en local: pipeline completo (CAMMESA + ENARGAS → panel en TJ → índices
nacionales, provinciales y por rama), 2 notebooks para Colab, 0 alertas de calidad, 27 tests. Falta correrlo
en Colab y que el usuario confirme las decisiones metodológicas de §5.

## 1. Cobertura de datos

| Fuente | Último dato | Cómo se actualiza |
|---|---|---|
| CAMMESA BDI (electricidad) | ago-2026 (base `2026-08`) | `construir.py --refrescar` busca la base más nueva |
| ENARGAS GED / GEGU / GETD (gas) | jul-2026 | `--refrescar` (los xlsx se reemplazan en el mismo URL) |
| SSPM series (validación) e IPI INDEC | ago-2026 / jul-2026 | `--refrescar` |
| Índice (ambas fuentes) | **jul-2026** | — |

## 2. Cifras vigentes (`python scripts/construir.py`)

- **ICE industria jul-2026**: 92,3 (desest. 93,9; tendencia 93,4; 2016 = 100); var. i.a. +0,7%
  (electricidad +0,8 p.p., gas −0,1 p.p.).
- **12 meses a jul-2026 vs 12 anteriores**: industria −8,1% (electricidad +4,0%, gas −11,8%); vs 2023 −10,3%;
  vs 2016 −6,7%. Hogares +2,4% (electricidad +2,2%, gas +2,5%).
- Energía industrial 12 meses: 515 PJ (electricidad 136, gas 379; el gas es 74%). Hogares: 639 PJ.
- Intensidad energética industrial (ICE desest. / IPI desest., 2016 = 100): 2019 117; 2021 100; 2024 114;
  2025 105.
- Provincias (industria, 12 meses): Buenos Aires y CABA 48,4% (−14,2% i.a.), Santa Fe 13,0%, Chubut 10,2%,
  Córdoba 6,6%, Mendoza 5,0%.
- Ramas (gas de grandes usuarios, 12 meses vs anteriores): destilería −62%, cementeras −13%, otras
  industrias −18%, aceiteras +7%, alimenticia +6%.

## 3. Dónde se citan las cifras

| Documento | Qué cifras |
|---|---|
| `README.md` | "Primeros resultados" (12 meses, PJ por provincia, ramas, índice desest.) |
| `ESTADO.md` §2 | todas |
| Markdown de `scripts/gen_notebooks.py` | solo lecturas cualitativas (gas ~3/4, anomalía 2019-20) |

## 4. Verificación

- `python scripts/control_calidad.py` → **0 ALERTAS** (electricidad total/residencial vs SSPM < 0,21%; gas
  por sector vs SSPM < 1,5%; sin tarifas sin clasificar; saltos de nomenclatura < 1,3 p.p.; 2015 entre
  bases < 0,2%; sin meses faltantes).
- `python -m pytest tests -q` → 27 passed.
- Notebooks 01 y 02 ejecutados en local con `nbconvert` (sin errores). **Colab: pendiente.**

## 5. Próximos pasos / decisiones a confirmar con el usuario

1. **Decisiones metodológicas**: base 2016 = 100 (= IPI manufacturero); agregación física en TJ (el gas
   pesa 3/4 en industria); incluir grandes comercios ≥ 300 kW en "industria" eléctrica.
2. **Anomalía oct-2019 a mar-2020** (un usuario "Otras industrias" de Pampeana): ¿dejarla, marcarla o
   corregirla (p. ej. topear ese usuario a su nivel 2017-2019)?
3. Clasificar los grandes usuarios eléctricos del MEM por rama (CONTEXTO §4).
4. Hogares: corrección por temperatura y consumo per cápita (población por provincia).
5. Correr los notebooks en Colab y comparar el ZIP con `output/`.

## 6. Rutina mensual

```bash
git pull
python scripts/construir.py --refrescar
python scripts/control_calidad.py      # 0 ALERTAS; si hay tarifas nuevas, clasificarlas
python -m pytest tests -q
# actualizar cifras de README y ESTADO §2; commit + push
```

## 7. PC nueva

`pip install -r requirements.txt` y `python scripts/construir.py` (baja ~100 MB a `data/cache/`). El mapa
(`data/reference/provincias.geojson`) está versionado; `scripts/preparar_mapa.py` solo hace falta para
regenerarlo (baja ~110 MB del IGN).

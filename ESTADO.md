# ESTADO — consumo_energetico_argentina (ICE)

**Última actualización:** 2026-10-08 (cierre de la sesión 1). Punto de entrada para retomar: este archivo →
`CLAUDE.md` (reglas) → `CONTEXTO.md` (fuentes, decisiones, trampas) → `.claude/memory/project.md`
(historial). Detalle de tablas en `data/README.md`, de scripts en `scripts/README.md` y de la sección LaTeX
en `docs/informe_indicadores/README.md`.

## 0. Estado en una línea

Versión 0 funcionando y verificada (local y Colab): pipeline completo (CAMMESA + ENARGAS → panel en TJ →
índices nacionales, provinciales, por rama y Costa Atlántica), 2 notebooks, 0 alertas, 28 tests, sección
LaTeX lista para el Overleaf. **No hay trabajo a medias**: lo pendiente son decisiones del usuario (§5) y
que vuelva a correr el notebook 02 en Colab con la sección Costa Atlántica.

## 1. Cobertura de datos

| Fuente | Último dato | Cómo se actualiza |
|---|---|---|
| CAMMESA BDI (electricidad) | ago-2026 (base `2026-08`) | `construir.py --refrescar` busca la base más nueva |
| ENARGAS GED / GEGU / GETD (gas) | jul-2026 | `--refrescar` (los xlsx se reemplazan en el mismo URL) |
| SSPM series (validación) e IPI INDEC | ago-2026 / jul-2026 | `--refrescar` |
| Índice (ambas fuentes) | **jul-2026** | — |
| Costa Atlántica (cooperativas en CAMMESA) | ago-2026 | igual que CAMMESA |

## 2. Cifras vigentes (`python scripts/construir.py`)

- **ICE industria jul-2026**: 92,3 (desest. 93,9; tendencia-ciclo 93,4, mínimo desde 2012; máximo ago-2023
  104,0; 2016 = 100); var. i.a. +0,7% (electricidad +0,8 p.p., gas −0,1 p.p.). IPI manufacturero desest.
  jul-2026: 87,0 (promedio 2026: 90,5).
- **12 meses a jul-2026 vs 12 anteriores**: industria −8,1% (electricidad +4,0%, gas −11,8%); vs 2023 −10,3%;
  vs 2016 −6,7%. Hogares +2,4% (electricidad +2,2%, gas +2,5%); vs 2016: electricidad +16,9%, gas −5,5%.
- Energía industrial 12 meses: 515 PJ (electricidad 136, gas 379; el gas es 74%). Hogares: 639 PJ.
  Electricidad en la energía de los hogares: 30,6% (2012) → 37,9% (2025).
- Intensidad energética industrial (ICE desest. / IPI desest., 2016 = 100): 2019 117; 2021 100; 2024 114;
  2025 105.
- Provincias (industria, 12 meses): Buenos Aires y CABA 48,4% (−14,2% i.a.: gas −18,5%, electricidad +0,8%),
  Santa Fe 13,0%, Chubut 10,2%, Córdoba 6,6% (electricidad +10,1%), Mendoza 5,0%; las cinco suman 83%.
- Ramas (gas de grandes usuarios, 12 meses vs anteriores): destilería −62%, cementeras −13%, otras
  industrias −18%, siderurgia −4%, aceiteras +7%, alimenticia +6%.
- **Costa Atlántica** (cooperativas de Villa Gesell y San Bernardo; total país entre paréntesis): demanda
  2025 150,6 y 47,9 GWh (141.251); enero / promedio mensual 1,43 y 2,07 (1,11); verano 2026 vs 2025 −2,5% y
  −2,1% (−6,0%); verano 2026 vs 2016 −2,2% y −31,9% (+3,5%); invierno 2026 vs 2016 +18,0% y +24,3% (+10,2%);
  verano / invierno 2016 → 2026: 1,34 → 1,11 y 3,08 → 1,69 (1,04 → 0,98).

## 3. Dónde se citan las cifras (actualizar todo junto si cambian)

| Documento | Qué cifras |
|---|---|
| `README.md` | "Primeros resultados": 12 meses, índice desest., tendencia, IPI, hogares, provincias, Costa Atlántica |
| `ESTADO.md` §2 | todas |
| `docs/informe_indicadores/seccion_energia.tex` | sección del informe INECO: 12 meses, PJ, tendencia, ramas, intensidad, provincias, hogares, Cuadro 2 de la Costa Atlántica y su párrafo. Validación (< 0,21%, < 1,5%), by-pass 15-18% |
| `README.md` y `CONTEXTO.md` | validación (< 0,21%; gas < 0,2% / comercio < 1,5%) |
| Markdown de `scripts/gen_notebooks.py` | solo lecturas cualitativas (gas ~3/4, anomalía 2019-20, ~280 millones de m³) |

## 4. Verificación (2026-10-08)

- `python scripts/control_calidad.py` → **0 ALERTAS** (electricidad total/residencial vs SSPM < 0,21%; gas
  por sector vs SSPM < 1,5%; sin tarifas sin clasificar; saltos de nomenclatura de hasta 1,31 p.p.
  (tolerancia 4); 2015 entre bases < 0,2%; sin meses faltantes; atraso del gas 3 meses).
- `python -m pytest tests -q` → 28 passed.
- `python scripts/probar_latex.py` → compila sin errores ni advertencias (4 figuras, 6 citas).
- `construir.py` corrido dos veces: `data/processed/` y `output/graficos/` idénticos byte a byte.
- Notebooks 01 y 02 ejecutados en local con `nbconvert` (sin errores).
- **Colab**: el usuario corrió los dos notebooks con el commit `0b9f55a` y las tablas coinciden con las
  locales. La sección Costa Atlántica del NB02 (commit `90462d1` en adelante) todavía no se corrió en Colab.

## 5. Próximos pasos / decisiones a confirmar con el usuario

1. **Decisiones metodológicas**: base 2016 = 100 (= IPI manufacturero); agregación física en TJ (el gas
   pesa 3/4 en industria); incluir grandes comercios ≥ 300 kW en "industria" eléctrica.
2. **Anomalía oct-2019 a mar-2020** (un usuario "Otras industrias" de Camuzzi Pampeana): ¿dejarla, marcarla o
   corregirla (p. ej. topear ese usuario a su nivel 2017-2019)? Si se corrige, cambian cifras históricas y
   el texto de la sección LaTeX ("el caso está en revisión").
3. **Foco Pinamar / General Madariaga** (5 pasos en `CONTEXTO.md` §4 y en la sección LaTeX): pedir datos por
   partido (distribuidora regional, OCEBA, Camuzzi Gas Pampeana), temperatura del SMN, luces nocturnas VIIRS.
4. Clasificar los grandes usuarios eléctricos del MEM por rama (`grandes_usuarios_electricidad.csv.gz`).
5. Hogares: corrección por temperatura y consumo per cápita (población por provincia).
6. Documento completo del Overleaf (no es de este repo): la introducción dice "seis indicadores"; con esta
   sección son siete. El usuario puede pedir que se redacte ese párrafo. Título usado:
   "Consumo de Energía en Argentina y en Pinamar" (el usuario lo había llamado "Consumo de energia en Pinamar").

## 6. Rutina mensual

```bash
git pull
python scripts/construir.py --refrescar
python scripts/control_calidad.py      # 0 ALERTAS; si hay tarifas nuevas, clasificarlas (CLAUDE.md)
python -m pytest tests -q
```

Después: actualizar las cifras de la tabla de §3 (README, ESTADO §2, `seccion_energia.tex`), correr
`python scripts/probar_latex.py`, `python scripts/gen_notebooks.py` si cambió algún texto de los notebooks,
y commit + push (sin `output/indice_consumo_energetico.xlsx` si los datos no cambiaron: ver `CLAUDE.md`).

## 7. PC nueva

1. `git clone https://github.com/santiagoriverti/consumo_energetico_argentina.git` en
   `C:\Users\<usuario>\Desktop\INECO\Repositorios\` y `git config user.name "Santiago Riverti"` /
   `user.email` si la PC no los tiene.
2. Python 3.10 o más nuevo (probado con 3.14) y `pip install -r requirements.txt`.
3. Activar UTF-8 en Python: `$env:PYTHONUTF8=1` (PowerShell) o `export PYTHONUTF8=1` (Git Bash).
4. `python scripts/construir.py`: baja ~100 MB a `data/cache/` (CAMMESA ~93 MB, ENARGAS ~7 MB) y arma todo;
   tiene que dar las cifras de §2 si las fuentes no publicaron un mes nuevo.
5. `python scripts/control_calidad.py` (0 ALERTAS) y `python -m pytest tests -q` (28 passed).
6. Opcional: MiKTeX o TeX Live para `probar_latex.py`. El mapa (`data/reference/provincias.geojson`) está
   versionado; `preparar_mapa.py` solo hace falta para regenerarlo (baja ~110 MB del IGN).

Colab no necesita nada: los notebooks clonan el repo y leen `data/processed/`.

## 8. Commits

| Commit | Qué |
|---|---|
| `f7926c2` | Initial commit (README de GitHub) |
| `0b9f55a` | ICE v0: pipeline, índices, 2 notebooks, documentación (verificado en Colab) |
| `90462d1` | Costa Atlántica (Villa Gesell, San Bernardo) y sección LaTeX del informe INECO |
| siguiente | Cierre de sesión 1: documentación completa (`data/`, `scripts/`, `docs/` README), `probar_latex.py`, bibitems, `.csv.gz` reproducible, test de la costa |

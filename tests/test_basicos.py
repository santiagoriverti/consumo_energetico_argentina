"""Tests de las piezas que no dependen de descargas."""
import io
import zipfile

import numpy as np
import pandas as pd
import pytest

from src import fuentes, indices, procesar


@pytest.mark.parametrize('tarifa, tipo, esperado', [
    ('GUMAS/AUTOGENERADORES', 'GU', 'industria'),
    ('GUMAS/AUTOGENERADORES', 'AG', 'industria'),
    ('GUMES/GUPAS', 'DI', 'industria'),
    ('GRANDES USUARIOS C DEM MAYOR O IGUAL 300KW', 'DI', 'industria'),
    ('TARIFA USUARIO NO RESIDENCIAL >=300KWH', 'DI', 'industria'),
    ('TARIFA USUARIO NO RESIDENCIAL >=300KWH S Y E', 'DI', 'industria'),
    ('GRANDES USUARIOS GUDI', 'DI', 'industria'),
    ('MERCADO TERMINO DISTRIB', 'DI', 'industria'),
    ('TARIFA USUARIO NO RESIDENCIAL <300KWH', 'DI', 'comercio'),
    ('SANCIONADO DEM.MAYOR O IGUAL 10 Y MENOR300 KW', 'DI', 'comercio'),
    ('TARIFA USUARIO NO RES.>10 KW Y < DE 300 KW', 'DI', 'comercio'),
    ('MENOR 10KW NO RES. MENOR 4000 KWH BIM', 'DI', 'comercio'),
    ('NO RESIDENCIAL GRAL', 'DI', 'comercio'),
    ('Alumbrado Publico', 'DI', 'comercio'),
    ('CLUBES DE BARRIO Y ENTIDADES DE BIEN PUBLICO', 'DI', 'comercio'),
    ('RES. MENOR O IGUAL 1000 KWH BIM', 'DI', 'hogares'),
    ('RESIDENCIAL NIVEL 2 BASE', 'DI', 'hogares'),
    ('RESIDENCIAL PLAN ESTIMULO AHORRO >=10 Y <=20%', 'DI', 'hogares'),
    ('TARIFA SOCIAL CONSUMO BASE', 'DI', 'hogares'),
    ('TARIFA BASE ELECTRODEPENDIENTES', 'DI', 'hogares'),
    ('RESIDENCIAL GENERAL DEM.SIN SUBSIDIO', 'DM', 'hogares'),
])
def test_sector_tarifa(tarifa, tipo, esperado):
    assert procesar.sector_tarifa(tarifa, tipo) == esperado


def test_conversiones():
    assert procesar.TJ_POR_MWH == pytest.approx(0.0036)
    assert procesar.TJ_POR_MIL_M3 == pytest.approx(0.038937, rel=1e-4)  # 9.300 kcal x 4,1868 kJ/kcal


def test_provincias_alias():
    p = procesar.provincias()
    assert len(p) == 23 and p['provincia'].is_unique
    alias = procesar._mapa_alias('enargas')
    assert alias[procesar._norm('Capital Federal')] == 'Buenos Aires y CABA'
    assert procesar._mapa_alias('cammesa')[procesar._norm('SGO.DEL ESTERO')] == 'Santiago del Estero'


def test_a_base_y_desestacionalizar():
    idx = pd.date_range('2012-01-01', '2020-12-01', freq='MS')
    est = 1 + 0.2 * np.sin(2 * np.pi * idx.month / 12)
    s = pd.Series(50 * est * np.linspace(1, 1.2, len(idx)), index=idx)
    b = indices.a_base(s, 2016)
    assert b[b.index.year == 2016].mean() == pytest.approx(100)
    d = indices.desestacionalizar(b)
    # la desestacionalizada no tiene el ciclo de +-20%
    assert d['desest'].pct_change().abs().max() < 0.05


def test_bypass_reparte_por_area():
    f = pd.Timestamp('2024-01-01')
    ged = pd.DataFrame({'fecha': [f, f], 'provincia_enargas': ['Chubut', 'Neuquen'], 'distribuidora': ['Sur', 'Sur'],
                        'tipo': ['INDUSTRIALES'] * 2, 'miles_m3': [300.0, 100.0], 'usuarios': [1.0, 1.0]})
    getd = pd.DataFrame({'fecha': [f], 'origen': ['Tra'], 'area_licencia': ['Sur'], 'tipo': ['Industria'],
                         'miles_m3': [40.0]})
    r = procesar.bypass_industrial(ged, getd).set_index('provincia')['miles_m3']
    assert r['Chubut'] == pytest.approx(30) and r['Neuquén'] == pytest.approx(10)


def test_leer_pivot_cache(tmp_path):
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    definicion = (f'<pivotCacheDefinition xmlns="{ns}"><cacheFields count="3">'
                  '<cacheField name="Periodo"><sharedItems><d v="2024-01-01T00:00:00"/></sharedItems></cacheField>'
                  '<cacheField name="Tipo"><sharedItems><s v="A"/><s v="B"/></sharedItems></cacheField>'
                  '<cacheField name="Volumen"><sharedItems/></cacheField>'
                  '<cacheField name="Calc" formula="Volumen*2" databaseField="0"/>'
                  '</cacheFields></pivotCacheDefinition>')
    registros = (f'<pivotCacheRecords xmlns="{ns}"><r><x v="0"/><x v="1"/><n v="5"/></r>'
                 '<r><x v="0"/><x v="0"/><n v="7"/></r></pivotCacheRecords>')
    p = tmp_path / 'x.xlsx'
    with zipfile.ZipFile(p, 'w') as z:
        z.writestr('xl/pivotCache/pivotCacheDefinition1.xml', definicion)
        z.writestr('xl/pivotCache/pivotCacheRecords1.xml', registros)
    df = fuentes.leer_pivot_caches(p)[0]
    assert list(df.columns) == ['Periodo', 'Tipo', 'Volumen']
    assert df['Tipo'].tolist() == ['B', 'A'] and df['Volumen'].tolist() == [5.0, 7.0]


def test_detalle_bdi():
    filas = [['DEMANDA TOTAL', None, None, None], [None, None, None, None],
             ['AÑO', 'MES', 'AGENTE NEMO', 'TARIFA', 'TIPO AGENTE', 'PROVINCIA', 'CATEGORIA TARIFA', 'DEMANDA [MWh]'],
             [2024, pd.Timestamp('2024-01-01'), 'X1', 'RESIDENCIAL', 'DI', 'CHACO', 'Residencial', 10.5]]
    buf = io.BytesIO()
    pd.DataFrame(filas).to_excel(buf, sheet_name='DEMANDA', header=False, index=False)
    df = fuentes._leer_detalle_bdi(buf.getvalue())
    assert df.loc[0, 'mwh'] == 10.5 and df.loc[0, 'agente'] == 'X1' and df.loc[0, 'tipo_demanda'] == ''

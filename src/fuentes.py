"""Descarga y lectura de las fuentes (todo queda guardado en data/cache/, ignorado por git).

- CAMMESA, Base del Informe Mensual (BDI): demanda de energia electrica por agente, provincia y tarifa,
  mensual. Cuatro bases cubren 2012 -> hoy: 2015-12 (detalle 2012-2015), 2018-12 (2015-2018), 2022-12
  (2019-2022) y la vigente (2023 -> ultimo mes publicado). En los meses repetidos gana la base mas nueva.
- ENARGAS, datos operativos de distribucion: los datos completos estan en el *pivot cache* de cada
  planilla (las hojas visibles son tablas dinamicas filtradas).
    GED  gas entregado y numero de usuarios por provincia, distribuidora y tipo de usuario (1993 ->)
    GEGU gas entregado a grandes usuarios industriales por provincia y rama de actividad (1994 ->)
    GETD gas entregado total del sistema por tipo de usuario y origen (incluye by-pass) (1993 ->)
- datos.gob.ar (API de series de tiempo): totales nacionales de CAMMESA y ENARGAS publicados por la
  Secretaria de Politica Economica (para validar), temperatura media e IPI manufacturero del INDEC.
"""
from __future__ import annotations

import datetime as dt
import io
import re
import warnings
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pandas as pd
import requests
import urllib3

RAIZ = Path(__file__).resolve().parents[1]
CACHE = RAIZ / 'data' / 'cache'
REFERENCIA = RAIZ / 'data' / 'reference'
PROCESADOS = RAIZ / 'data' / 'processed'
UA = {'User-Agent': 'Mozilla/5.0 (consumo_energetico_argentina)'}

CAMMESA_URL = ('https://microfe.cammesa.com/static-content/CammesaWeb/download-manager-files/'
               'Sintesis%20Mensual/BASE_INFORME_MENSUAL_{periodo}.zip')
CAMMESA_HISTORICAS = ['2015-12', '2018-12', '2022-12']

ENARGAS_URL = 'https://www.enargas.gob.ar/secciones/transporte-y-distribucion/datos-estadisticos/{c}/{c}.xlsx'

SERIES_URL = 'https://apis.datos.gob.ar/series/api/series/?ids={ids}&format=csv&limit=5000'
SERIES = {
    # CAMMESA via SSPM (dataset 367), GWh
    'elec_residencial': '367.3_DEMANDA_REIAL__19',
    'elec_comercio_industria': '367.3_COMERCIO_ERIA__20',
    'elec_grandes_usuarios': '367.3_GRANDES_USIOS__16',
    'elec_total': '367.3_DEMANDA_TOTAL__13',
    'temperatura_media': '367.3_TEMPERATURDIO__20',
    # ENARGAS via SSPM (dataset 364), millones de m3
    'gas_residencial': '364.3_RESIDENCIAIAL__11',
    'gas_comercial': '364.3_COMERCIALIAL__9',
    'gas_entes_oficiales': '364.3_ENTES_OFICLES__15',
    'gas_industria': '364.3_INDUSTRIARIA__9',
    'gas_centrales': '364.3_CENTRALES_CAS__20',
    'gas_gnc': '364.3_GNCGNC__3',
    'gas_sdb': '364.3_SDBSDB__3',
    'gas_total': '364.3_TOTALTAL__5',
    # INDEC, IPI manufacturero (2016 = 100)
    'ipi_original': '453.1_SERIE_ORIGNAL_0_0_14_46',
    'ipi_desest': '453.1_SERIE_DESEADA_0_0_24_58',
}


# ------------------------------------------------------------------------------------------------
# Descargas
# ------------------------------------------------------------------------------------------------
def _get(url: str, **kw) -> requests.Response:
    """GET con reintento sin verificar el certificado (microfe.cammesa.com y enargas.gob.ar no envian la
    cadena completa y Python no los valida; son sitios oficiales y solo se bajan datos publicos)."""
    try:
        return requests.get(url, headers=UA, timeout=600, **kw)
    except requests.exceptions.SSLError:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return requests.get(url, headers=UA, timeout=600, verify=False, **kw)


def bajar(url: str, destino: Path, refrescar: bool = False) -> Path:
    destino = Path(destino)
    if destino.exists() and not refrescar:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    r = _get(url, stream=True)
    r.raise_for_status()
    tmp = destino.with_name(destino.name + '.part')
    with open(tmp, 'wb') as f:
        for bloque in r.iter_content(1 << 20):
            f.write(bloque)
    tmp.replace(destino)
    return destino


def _existe(url: str) -> bool:
    try:
        r = _get(url, stream=True)
        r.close()
        return r.status_code == 200
    except requests.RequestException:
        return False


# ------------------------------------------------------------------------------------------------
# CAMMESA
# ------------------------------------------------------------------------------------------------
def periodo_cammesa_vigente(refrescar: bool = False, hoy: dt.date | None = None) -> str:
    """Ultima Base del Informe Mensual publicada (AAAA-MM). Sin refrescar, usa la mas nueva del cache."""
    if not refrescar:
        en_cache = sorted(CACHE.glob('BASE_INFORME_MENSUAL_*.zip'))
        vigentes = [p.stem[-7:] for p in en_cache if p.stem[-7:] not in CAMMESA_HISTORICAS]
        if vigentes:
            return vigentes[-1]
    hoy = hoy or dt.date.today()
    mes = pd.Period(hoy, freq='M')
    for k in range(1, 8):
        periodo = str(mes - k)
        if _existe(CAMMESA_URL.format(periodo=periodo)):
            return periodo
    raise RuntimeError('No se encontro una Base del Informe Mensual de CAMMESA en los ultimos 7 meses')


_COLUMNAS_BDI = {
    'MES': 'fecha', 'AGENTE NEMO': 'agente', 'AGENTE DESCRIPCION': 'agente_desc', 'TIPO AGENTE': 'tipo_agente',
    'REGION': 'region', 'PROVINCIA': 'provincia_cammesa', 'CATEGORIA AREA': 'categoria_area',
    'CATEGORIA DEMANDA': 'categoria_demanda', 'TARIFA': 'tarifa', 'CATEGORIA TARIFA': 'categoria_tarifa',
    'TIPO DEMANDA': 'tipo_demanda', 'DEMANDA [MWH]': 'mwh',
}


def _leer_detalle_bdi(contenido: bytes) -> pd.DataFrame:
    """Hoja DEMANDA de la BDI: arriba un resumen; el detalle por agente empieza en la fila con 'MES'."""
    raw = pd.read_excel(io.BytesIO(contenido), sheet_name='DEMANDA', header=None, engine='openpyxl')
    filas = raw.index[raw[1].astype(str).str.strip().str.upper().eq('MES')]
    if len(filas) == 0:
        raise ValueError('No se encontro el encabezado del detalle de demanda')
    f = filas[0]
    nombres = [str(c).strip().upper() for c in raw.iloc[f]]
    df = raw.iloc[f + 1:].copy()
    df.columns = nombres
    df = df[[c for c in nombres if c in _COLUMNAS_BDI]].rename(columns=_COLUMNAS_BDI)
    df = df[df['agente'].notna() & df['fecha'].notna()]
    df['fecha'] = pd.to_datetime(df['fecha']).dt.to_period('M').dt.to_timestamp()
    df['mwh'] = pd.to_numeric(df['mwh'], errors='coerce').fillna(0.0)
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype(str).str.strip()
    if 'tipo_demanda' not in df:
        df['tipo_demanda'] = ''
    return df.reset_index(drop=True)


def leer_base_cammesa(periodo: str, refrescar: bool = False) -> pd.DataFrame:
    """Detalle de demanda de una BDI (con cache en CSV: leer el Excel tarda ~1 minuto)."""
    csv = CACHE / f'cammesa_demanda_{periodo}.csv.gz'
    if csv.exists() and not refrescar:
        return pd.read_csv(csv, parse_dates=['fecha'], keep_default_na=False,
                           dtype={'agente': str, 'tarifa': str, 'tipo_demanda': str})
    zpath = bajar(CAMMESA_URL.format(periodo=periodo), CACHE / f'BASE_INFORME_MENSUAL_{periodo}.zip', refrescar)
    with zipfile.ZipFile(zpath) as z:
        nombres = [n for n in z.namelist() if n.lower().endswith('.xlsx')]
        demanda = [n for n in nombres if re.search(r'demanda mensual\.xlsx$', n, re.I)]
        miembro = demanda[0] if demanda else nombres[0]
        df = _leer_detalle_bdi(z.read(miembro))
    df['base'] = periodo
    df.to_csv(csv, index=False)
    return df


def demanda_cammesa(refrescar: bool = False) -> pd.DataFrame:
    """Detalle de demanda 2012 -> hoy uniendo las bases; en los meses repetidos gana la base mas nueva."""
    vigente = periodo_cammesa_vigente(refrescar)
    partes, cubiertos = [], set()
    for periodo in sorted(set(CAMMESA_HISTORICAS + [vigente]), reverse=True):
        df = leer_base_cammesa(periodo, refrescar=refrescar and periodo == vigente)
        df = df[~df['fecha'].isin(list(cubiertos))]
        cubiertos |= set(df['fecha'].unique())
        partes.append(df)
    return pd.concat(partes, ignore_index=True).sort_values(['fecha', 'agente', 'tarifa']).reset_index(drop=True)


# ------------------------------------------------------------------------------------------------
# ENARGAS
# ------------------------------------------------------------------------------------------------
_NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'


def _valor_xml(el):
    tag = el.tag.replace(_NS, '')
    if tag == 'n':
        return float(el.get('v'))
    if tag == 'm':
        return None
    return el.get('v')


def leer_pivot_caches(path: Path) -> list[pd.DataFrame]:
    """Todos los pivot caches de un .xlsx como DataFrames (una fila por registro de la fuente)."""
    salida = []
    with zipfile.ZipFile(path) as z:
        defs = sorted(n for n in z.namelist() if re.match(r'xl/pivotCache/pivotCacheDefinition\d+\.xml$', n))
        for d in defs:
            k = re.search(r'(\d+)\.xml$', d).group(1)
            raiz = ET.fromstring(z.read(d))
            campos, compartidos = [], []
            for cf in raiz.iter(_NS + 'cacheField'):
                if cf.get('databaseField') == '0' or cf.get('formula'):
                    continue  # campos calculados: no tienen valores en los registros
                campos.append(cf.get('name'))
                si = cf.find(_NS + 'sharedItems')
                compartidos.append([_valor_xml(x) for x in si] if si is not None else [])
            filas = []
            for r in ET.fromstring(z.read(f'xl/pivotCache/pivotCacheRecords{k}.xml')).iter(_NS + 'r'):
                filas.append([compartidos[i][int(el.get('v'))] if el.tag == _NS + 'x' else _valor_xml(el)
                              for i, el in enumerate(r)])
            salida.append(pd.DataFrame(filas, columns=campos))
    return salida


def _cache_enargas(codigo: str, campos: set[str], refrescar: bool) -> pd.DataFrame:
    path = bajar(ENARGAS_URL.format(c=codigo), CACHE / f'enargas_{codigo}.xlsx', refrescar)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for df in leer_pivot_caches(path):
            if set(df.columns) == campos:
                df['Periodo'] = pd.to_datetime(df['Periodo']).dt.to_period('M').dt.to_timestamp()
                return df
    raise ValueError(f'ENARGAS {codigo}: no hay un pivot cache con los campos {sorted(campos)}')


def gas_distribucion(refrescar: bool = False) -> pd.DataFrame:
    """GED: fecha, provincia_enargas, distribuidora, tipo (DOMICILIARIOS, INDUSTRIALES, ...),
    miles_m3 (de 9300 kcal) y usuarios."""
    df = _cache_enargas('GED', {'Periodo', 'Provincia', 'Distribuidor', 'TipoDeCliente', 'Variable', 'Cantidad'},
                        refrescar)
    df = df.pivot_table(index=['Periodo', 'Provincia', 'Distribuidor', 'TipoDeCliente'], columns='Variable',
                        values='Cantidad', aggfunc='sum').reset_index()
    df = df.rename(columns={'Periodo': 'fecha', 'Provincia': 'provincia_enargas', 'Distribuidor': 'distribuidora',
                            'TipoDeCliente': 'tipo', 'Volumen': 'miles_m3', 'NroClientes': 'usuarios'})
    df.columns.name = None
    return df[['fecha', 'provincia_enargas', 'distribuidora', 'tipo', 'miles_m3', 'usuarios']]


def gas_grandes_usuarios(refrescar: bool = False) -> pd.DataFrame:
    """GEGU: grandes usuarios industriales por provincia y rama (miles de m3 de 9300 kcal)."""
    df = _cache_enargas('GEGU', {'Periodo', 'Distribuidor', 'Provincia', 'ciiu_clasif', 'Volumen'}, refrescar)
    return df.rename(columns={'Periodo': 'fecha', 'Provincia': 'provincia_enargas', 'Distribuidor': 'distribuidora',
                              'ciiu_clasif': 'rama', 'Volumen': 'miles_m3'})


def gas_total_sistema(refrescar: bool = False) -> pd.DataFrame:
    """GETD: gas entregado total del sistema por tipo de usuario y origen (Dis = distribuidoras,
    Tra = by-pass desde los gasoductos de transporte, Off = boca de pozo) y area de licencia."""
    df = _cache_enargas('GETD', {'Periodo', 'Fuente', 'Distribuidor', 'TipoDeCliente', 'Volumen'}, refrescar)
    return df.rename(columns={'Periodo': 'fecha', 'Fuente': 'origen', 'Distribuidor': 'area_licencia',
                              'TipoDeCliente': 'tipo', 'Volumen': 'miles_m3'})


# ------------------------------------------------------------------------------------------------
# datos.gob.ar
# ------------------------------------------------------------------------------------------------
def series_nacionales(refrescar: bool = False) -> pd.DataFrame:
    """Series mensuales de SERIES (columnas con los nombres cortos), indice = primer dia del mes."""
    destino = CACHE / 'series_datos_gob.csv'
    if not destino.exists() or refrescar:
        partes = []
        nombres, ids = list(SERIES), list(SERIES.values())
        for i in range(0, len(ids), 10):  # la API acepta pocas series por pedido
            r = _get(SERIES_URL.format(ids=','.join(ids[i:i + 10])))
            r.raise_for_status()
            p = pd.read_csv(io.StringIO(r.text), parse_dates=['indice_tiempo'], index_col='indice_tiempo')
            p.columns = nombres[i:i + 10]  # la API devuelve las columnas en el orden pedido
            partes.append(p)
        df = pd.concat(partes, axis=1)
        destino.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(destino)
    return pd.read_csv(destino, parse_dates=['indice_tiempo'], index_col='indice_tiempo')

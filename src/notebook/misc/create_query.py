"""
The `create_query` module includes query generators and indicator genarator for QualiCharge indicators.

Each 'query_xx' function is defined with:

Parameters
----------
param: tuple of two or three str 
    Indicator parameters (see indicator codification)
simple: boolean (default False)
    If False, additional columns are added in the result Table
gen: boolean (default False)
    If True, the query is generic (with variables) else the query is specific (with values)

Returns
-------
String
    SQL query to apply
"""

import pandas as pd
import sys
from sqlalchemy import types, dialects

create_query = sys.modules[__name__]

P_TAB = """puissance(p_range, p_cat) AS (
        VALUES 
            (numrange(0, 15.0), 1), 
            (numrange(15.0, 26.0), 2), 
            (numrange(26, 65.0), 3),
            (numrange(65, 175.0), 4),
            (numrange(175, 360.0), 5),
            (numrange(360, NULL), 6)
    )"""
JOIN_P = "LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range "
PDC_ALL = f"""pointdecharge 
    LEFT JOIN station ON station.id = station_id 
    LEFT JOIN localisation ON localisation_id = localisation.id"""
COG_ALL = f"""LEFT JOIN city on city.code = code_insee_commune
    LEFT JOIN epci on city.epci_id = epci.id
    LEFT JOIN department on city.department_id = department.id
    LEFT JOIN region on department.region_id = region.id"""
STAT_ALL = f"""station 
    LEFT JOIN localisation ON localisation_id = localisation.id"""
TABLE = {'00': 'national', '01': 'region', '02': 'department', '03': 'epci', '04': 'city'}
G_OVERHEAD = f"""QUERY,
    VAL,
    PERIM,
    LEVEL"""
STAT_NB_PDC = f"""stat_nb_pdc AS (
    SELECT
      count(station_id) AS nb_pdc,
      localisation_id
    FROM
      pointdecharge
      LEFT JOIN station ON station.id = station_id
    GROUP BY
      station_id,
      localisation_id
)
"""
# URL_POP = 'https://unpkg.com/@etalab/decoupage-administratif@4.0.0/data/communes.json'
# POP = None 

def to_indicator(engine, indicator, simple=True, histo=False, format='pandas', histo_timest=None, json_orient='split',
                 table_name=None, table_option="replace", table_dtype=None, query_gen=False, test=None):
    """create data for an indicator
    
    Parameters
    ----------
    engine: sqlalchemy object
        Connector to postgreSQL database
    indicator: str 
        Indicator name (see indicator codification)
    simple: boolean, default False
        If False, additional columns are added
    histo: boolean, default False
        If True, timestamp additional column is added (with others additional columns)
    format: enum ('pandas', 'query', 'histo', 'json', 'table'), default 'pandas'
        Define the return format:
        - 'pandas'-> query result Dataframe
        - 'query'-> postgreSQL query String
        - 'json'-> json query result string
        - 'table' -> Dataframe (table creation confirmation with the number of lines created)
    json_orient: string, default 'split'
        Json structure (see 'orient' option for 'DataFrame.to_json').
    histo_timest: string (used if histo=True), default None
        Value of timestamp. If None the timestamp is the execution query timestamp.
    table_name: string (used if format='table'), default None
        Name of the table to create (format='table'). If None the name is the indicator name.
    table_option: string (used if format='table'), default 'replace'
        Option if table exists ('replace' or 'append')
    query_gen: boolean (default False)
        If True, the query is generic (with variables) else the query is specific (with values)
    test: string, default None
        choice of historization solution
    Returns
    -------
    String or Dataframe
        see 'format' parameter
    """
    indic = indicator + '-00'
    simple = False if histo else simple
    query = getattr(create_query, 'query_' + indic.split('-')[0])(*indic.split('-')[1:], simple=simple, gen=query_gen)
    table_dtype = table_dtype if table_dtype else {'value': types.FLOAT, 'category': types.TEXT, 'code_z': types.TEXT, 'query': types.TEXT, 'perimeter': types.TEXT, 'code_p': types.TEXT, 'zoning': types.TEXT, 
        'timestamp': types.TIMESTAMP, 'add_value': dialects.postgresql.JSONB}
    if histo:
        query = create_query.query_histo(query, timestamp=histo_timest)
    if format == 'query':
        return query
    with engine.connect() as conn:
        data_pd = pd.read_sql_query(query, conn)
    if format == 'pandas':
        return data_pd
    if format == 'json':
        return '{"' + indicator + '": ' + data_pd.to_json(index=False, orient=json_orient) + "}"
    if format == 'table':
        return indic_to_table(data_pd, table_name, engine, table_option=table_option, table_dtype=table_dtype, histo=histo, test=test)

def indic_to_table(pd_df, table_name, engine, table_option="replace", table_dtype=None, histo=None, test=None):
    """ Load a DataFrame in a Table
    
    Parameters
    ----------
    engine: sqlalchemy object
        Connector to postgreSQL database
    pd_df: DataFrame 
        Data to load
    table_name: string
        Name of the table to create.
    table_option: string (used if format='table'), default 'replace'
        Option if table exists 'replace' or 'append'

    Returns
    -------
    Dataframe
        Table creation confirmation with the number of lines created.
    """
    from datetime import datetime
    if histo:
        if 'code' not in pd_df.columns:
            pd_df.insert(len(pd_df.columns)-5, 'code', [""]*len(pd_df))
        if len(pd_df.columns) == 7:
            pd_df.insert(1, 'category', [""]*len(pd_df))
        pd_df.insert(0, 'quantity', [1]*len(pd_df))
        pd_df.insert(2, 'last', pd_df[pd_df.columns[1]])
        cols = pd_df.columns
        pd_df.rename(columns={cols[1]: 'value', cols[3]: 'category'}, inplace = True)
        pd_df = pd_df.astype({'quantity': 'int', 'last': 'float', 'value': 'float', 
                              'query': 'string', 'perim': 'string', 'val': 'string', 'level': 'string'})
        pd_df.rename(columns={'code': 'target', 'query': 'code'}, inplace = True)
        if not test:
            pd_df['add_value'] = pd.Series([{'quantity': quantity, 'last': last} 
                                        for quantity, last in zip(pd_df['quantity'], pd_df['last'])])
            del pd_df['last']
            del pd_df['quantity']
        elif test == '1bis':
            pd_df['all_value'] = pd.Series([{'quantity': quantity, 'value': value, 'last': last} 
                                        for quantity, value, last in zip(pd_df['quantity'], pd_df['value'], pd_df['last'])])
            del pd_df['last']
            del pd_df['quantity']
            del pd_df['value']
    if table_name:
        dtype = table_dtype if table_dtype else {}
        pd_df.to_sql(table_name, engine, if_exists=table_option, index=False, dtype=dtype)
        return pd.read_sql_query('SELECT COUNT(*) AS count FROM "' + table_name + '"', engine)
    return pd_df

def query_histo(query, timestamp=None):

    if timestamp:
        datation = "datation(timest) AS (VALUES ('" + timestamp + "'::timestamp)) "
    else:
        datation = "datation(timest) AS (VALUES (CURRENT_TIMESTAMP)) "
    return " WITH query AS (" + query + "), " + datation + " SELECT * FROM query, datation "

def init_param_ixx(simple, gen, indic,  *param):
    '''parameters initialization for 'query_ixx' and 'query_txx' functions  '''
    
    perim, val, level = (param + ('00', '00', '00'))[:3]
    perim = perim.rjust(2, '0')
    val = val.rjust(2, '0')
    level = level.rjust(2, '0')

    g_overhead = "" if simple else f"{G_OVERHEAD},"
    s_overhead = "" if simple else f"""'{indic}' AS QUERY,
    '{perim}' AS PERIM,
    '{val}' AS VAL,
    '{level}' AS LEVEL"""
    where_isin_perim = "" if perim == '00' else f"""WHERE
    {TABLE[perim]}.code = '{val}'"""
    from_perim = """FROM
        region""" if perim == '00' else f"""FROM
        {TABLE[perim]}"""
    table_level = "" if level == '00' else f"{TABLE[level]}"
    table_level_code = "" if level == '00' else f"{TABLE[level]}.code"
    table_level_pop = "" if level == '00' else f"{TABLE[level]}.population * 100000"
    table_level_area = "" if level == '00' else f"{TABLE[level]}.area::float * 100000000"
    coma = "" if f"{s_overhead}" == "" else ","

    if gen:
        s_overhead = "" if simple else f"""'{{indic}}' AS QUERY,
    '{{perim}}' AS PERIM,
    '{{val}}' AS VAL,
    '{{level}}' AS LEVEL"""
        where_isin_perim = "" if perim == '00' else f"""WHERE
    {{TABLE[perim]}}.code = '{{val}}'"""
        from_perim = """FROM
        region""" if perim == '00' else f"""FROM
        {TABLE[perim]}"""
        table_level = "" if level == '00' else f"{{TABLE[level]}}"
        table_level_code = "" if level == '00' else f"{{TABLE[level]}}.code"
        table_level_pop = "" if level == '00' else f"{{TABLE[level]}}.population * 100000"
        table_level_area = "" if level == '00' else f"{{TABLE[level]}}.area::float * 100000000"

    coma1 = "" if f"{table_level_code}{s_overhead}" == "" else ","
    coma2 = "" if f"{table_level_code}" == "" else ","
    coma3 = "" if f"{s_overhead}" == "" or f"{table_level_code}" == "" else ","
    group_by = "" if f"{table_level_code}{g_overhead}" == "" else f"""GROUP BY
    {g_overhead}
    {table_level_code}"""
    code = "" if level == '00' else "code"

    return {'perim': perim, 'level': level, 'coma': coma, 'coma1': coma1, 'coma2': coma2, 'coma3': coma3, 
            'code': code, 'group_by': group_by, 'g_overhead': g_overhead, 's_overhead': s_overhead, 
            'where_isin_perim': where_isin_perim, 'from_perim': from_perim, 
            'table_level': table_level, 'table_level_code': table_level_code,
            'table_level_pop': table_level_pop, 'table_level_area': table_level_area}

def query_t1(*param, simple=True, gen=False):
    '''Create SQL query for 't1' indicators (see parameters in module docstring)'''

    indic = 't1'
    prm = init_param_ixx(simple, gen, indic, *param)

    return f"""
WITH 
    {P_TAB}
SELECT
    count(id_pdc_itinerance) AS nb_pdc,
    p_range{prm['coma1']}
    {prm['table_level_code']}{prm['coma3']}
    {prm['s_overhead']}
FROM
    {PDC_ALL}
    {COG_ALL}
    {JOIN_P}
{prm['where_isin_perim']}
GROUP BY
    {prm['g_overhead']}
    p_range{prm['coma2']}
    {prm['table_level_code']}
ORDER BY
    nb_pdc DESC"""

def query_t2(*param, simple=True, gen=False):
    '''Create SQL query for 't2' indicators (see parameters in module docstring)'''
    
    indic = 't2'
    prm = init_param_ixx(simple, gen, indic, *param)

    return f"""WITH 
    t1 AS (
        {query_t1(*param, simple=True, gen=gen)}
    )
SELECT
    nb_pdc / (
        SELECT 
            sum(nb_pdc) 
        FROM 
            t1
    ) * 100 AS pct_nb_pdc,
    p_range{prm['coma1']}
    {prm['code']}{prm['coma3']}
    {prm['s_overhead']}
FROM 
    t1"""

def query_t3(*param, simple=True, gen=False):
    '''Create SQL query for 't3' indicators (see parameters in module docstring)'''

    indic = 't3'
    prm = init_param_ixx(simple, gen, indic, *param)

    return f"""
WITH 
    {STAT_NB_PDC}
SELECT
    count(nb_pdc) AS nb_stations,
    nb_pdc{prm['coma1']}
    {prm['table_level_code']}{prm['coma3']}
    {prm['s_overhead']}
FROM
    stat_nb_pdc
    LEFT JOIN localisation ON localisation_id = localisation.id
    {COG_ALL}
{prm['where_isin_perim']}
GROUP BY
    {prm['g_overhead']}
    nb_pdc{prm['coma2']}
    {prm['table_level_code']}
ORDER BY
    nb_stations DESC"""

def query_t4(*param, simple=True, gen=False):
    '''Create SQL query for 't4' indicators (see parameters in module docstring)'''
    
    indic = 't4'
    prm = init_param_ixx(simple, gen, indic, *param)

    return f"""WITH 
    t3 AS (
        {query_t3(*param, simple=True, gen=gen)}
    )
SELECT
    nb_stations / (
        SELECT 
            sum(nb_stations) 
        FROM 
            t3
    ) * 100 AS pct_nb_stations,
    nb_pdc{prm['coma1']}
    {prm['code']}{prm['coma3']}
    {prm['s_overhead']}
FROM 
    t3"""

def query_t5(*param, simple=True, gen=False):
    '''Create SQL query for 't5' indicators (see parameters in module docstring)'''
    
    indic = 't5'
    prm = init_param_ixx(simple, gen, indic, *param)

    return f"""
SELECT
    count(id_station_itinerance) AS nb_stations,
    implantation_station{prm['coma1']}
    {prm['table_level_code']}{prm['coma3']}
    {prm['s_overhead']}
FROM
    {STAT_ALL}
    {COG_ALL}
{prm['where_isin_perim']}
GROUP BY
    {prm['g_overhead']}
    implantation_station{prm['coma2']}
    {prm['table_level_code']}
ORDER BY
    nb_stations DESC"""

def query_t6(*param, simple=True, gen=False):
    '''Create SQL query for 't6' indicators (see parameters in module docstring)'''

    indic = 't6'
    prm = init_param_ixx(simple, gen, indic, *param)

    return f"""WITH 
    t5 AS (
        {query_t5(*param, simple=True, gen=gen)}
    )
SELECT
    nb_stations / (
        SELECT 
            sum(nb_stations) 
        FROM 
            t5
    ) * 100 AS pct_nb_stations,
    implantation_station{prm['coma1']}
    {prm['code']}{prm['coma3']}
    {prm['s_overhead']}
FROM 
    t5"""

def query_t8(*param, simple=True, gen=False):
    '''Create SQL query for 't8' indicators (see parameters in module docstring)'''
    
    indic = 't8'
    prm = init_param_ixx(simple, gen, indic, *param)

    return f"""
SELECT
    count(id_station_itinerance) AS nb_stations,
    nom_operateur{prm['coma1']}
    {prm['table_level_code']}{prm['coma3']}
    {prm['s_overhead']}
FROM
    {STAT_ALL}
    {COG_ALL}
    LEFT JOIN operateur ON operateur_id = operateur.id
{prm['where_isin_perim']}
GROUP BY
    {prm['g_overhead']}
    nom_operateur{prm['coma2']}
    {prm['table_level_code']}
ORDER BY
    nb_stations DESC"""

def query_t9(*param, simple=True, gen=False):
    '''Create SQL query for 't9' indicators (see parameters in module docstring)'''

    indic = 't9'
    prm = init_param_ixx(simple, gen, indic, *param)

    return f"""WITH 
    t8 AS (
        {query_t8(*param, simple=True, gen=gen)}
    )
SELECT
    nb_stations / (
        SELECT 
            sum(nb_stations) 
        FROM 
            t8
    ) * 100 AS pct_nb_stations,
    nom_operateur{prm['coma1']}
    {prm['code']}{prm['coma3']}
    {prm['s_overhead']}
FROM 
    t8"""

def query_i1(*param, simple=True, gen=False):
    '''Create SQL query for 'i1' indicators (see parameters in module docstring)'''

    indic = 'i1'
    param = init_param_ixx(simple, gen, indic, *param)

    if param['perim'] == param['level'] == '00':
        return f"""
SELECT
    count(id_pdc_itinerance) AS nb_pdc{param['coma']}
    {param['s_overhead']}
FROM
    pointdecharge"""

    return f"""
SELECT
    count(id_pdc_itinerance) AS nb_pdc{param['coma1']}
    {param['table_level_code']}{param['coma3']}
    {param['s_overhead']}
FROM
    {PDC_ALL}
    {COG_ALL}
{param['where_isin_perim']}
{param['group_by']}
ORDER BY
    nb_pdc DESC"""

def query_i2(*param, simple=True, gen=False):
    '''Create SQL query for 'i2' indicators (see parameters in module docstring)'''

    indic = 'i2'
    prm = init_param_ixx(simple, gen, indic, *param)

    if prm['level'] == '00':
        return f"""
SELECT 
    (
        {query_i1(*param, simple=True, gen=gen)}
    ) / (
        SELECT 
            sum(population) 
        {prm['from_perim']}
        {prm['where_isin_perim']}
    ) * 100000 AS nb_pdc_pop{prm['coma']}
    {prm['s_overhead']}"""    

    return f"""
WITH
    i1 AS (
        {query_i1(*param, simple=True, gen=gen)}
    )
SELECT
    i1.nb_pdc::float / {prm['table_level_pop']} AS nb_pdc_pop,
    {prm['table_level_code']}{prm['coma3']}
    {prm['s_overhead']}
FROM
    i1
    LEFT JOIN {prm['table_level']} on i1.code = {prm['table_level_code']}
ORDER by
    nb_pdc_pop DESC"""

def query_i3(*param, simple=True, gen=False):
    '''Create SQL query for 'i3' indicators (see parameters in module docstring)'''

    indic = 'i3'
    prm = init_param_ixx(simple, gen, indic, *param)

    if prm['level'] == '00':
        return f"""
SELECT 
    (
        {query_i1(*param, simple=True, gen=gen)}
    ) / (
        SELECT 
            sum(area::float) 
        {prm['from_perim']}
        {prm['where_isin_perim']}
    ) * 100000000 AS nb_pdc_area{prm['coma']}
    {prm['s_overhead']}"""

    return f"""
WITH
    i1 AS (
        {query_i1(*param, simple=True, gen=gen)}
    )
SELECT
    i1.nb_pdc::float / {prm['table_level_area']} AS nb_pdc_area,
    {prm['table_level_code']}{prm['coma3']}
    {prm['s_overhead']}
FROM
    i1
    LEFT JOIN {prm['table_level']} on i1.code = {prm['table_level_code']}
ORDER by
    nb_pdc_area DESC"""

def query_i4(*param, simple=True, gen=False):
    '''Create SQL query for 'i4' indicators (see parameters in module docstring)'''

    indic = 'i4'
    param = init_param_ixx(simple, gen, indic, *param)

    if param['perim'] == param['level'] == '00':
        return f"""
SELECT
    count(id_station_itinerance) AS nb_stat{param['coma']}
    {param['s_overhead']}
FROM
    station"""

    return f"""
SELECT
    count(id_station_itinerance) AS nb_stat{param['coma1']}
    {param['table_level_code']}{param['coma3']}
    {param['s_overhead']}
FROM
    {STAT_ALL}
    {COG_ALL}
{param['where_isin_perim']}
{param['group_by']}
ORDER BY
    nb_stat DESC"""

def query_i5(*param, simple=True, gen=False):
    '''Create SQL query for 'i5' indicators (see parameters in module docstring)'''

    indic = 'i5'
    prm = init_param_ixx(simple, gen, indic, *param)

    if prm['level'] == '00':
        return f"""
SELECT 
    (
        {query_i4(*param, simple=True, gen=gen)}
    ) / (
        SELECT 
            sum(population) 
        {prm['from_perim']}
        {prm['where_isin_perim']}
    ) * 100000 AS nb_stat_pop{prm['coma']}
    {prm['s_overhead']}"""    

    return f"""
WITH
    i4 AS (
        {query_i4(*param, simple=True, gen=gen)}
    )
SELECT
    i4.nb_stat::float / {prm['table_level_pop']} AS nb_stat_pop,
    {prm['table_level_code']}{prm['coma3']}
    {prm['s_overhead']}
FROM
    i4
    LEFT JOIN {prm['table_level']} on i4.code = {prm['table_level_code']}
ORDER by
    nb_stat_pop DESC"""

def query_i6(*param, simple=True, gen=False):
    '''Create SQL query for 'i6' indicators (see parameters in module docstring)'''

    indic = 'i6'
    prm = init_param_ixx(simple, gen, indic, *param)

    if prm['level'] == '00':
        return f"""
SELECT 
    (
        {query_i4(*param, simple=True, gen=gen)}
    ) / (
        SELECT 
            sum(area::float) 
        {prm['from_perim']}
        {prm['where_isin_perim']}
    ) * 100000000 AS nb_stat_area{prm['coma']}
    {prm['s_overhead']}"""

    return f"""
WITH
    i4 AS (
        {query_i4(*param, simple=True, gen=gen)}
    )
SELECT
    i4.nb_stat::float / {prm['table_level_area']} AS nb_stat_area,
    {prm['table_level_code']}{prm['coma3']}
    {prm['s_overhead']}
FROM
    i4
    LEFT JOIN {prm['table_level']} on i4.code = {prm['table_level_code']}
ORDER by
    nb_stat_area DESC"""

def query_i7(*param, simple=True, gen=False):
    '''Create SQL query for 'i7' indicators (see parameters in module docstring)'''

    indic = 'i7'
    param = init_param_ixx(simple, gen, indic, *param)

    if param['perim'] == param['level'] == '00':
        return f"""
SELECT
    sum(puissance_nominale) AS p_nom{param['coma']}
    {param['s_overhead']}
FROM
    pointdecharge"""

    return f"""
SELECT
    sum(puissance_nominale) AS p_nom{param['coma1']}
    {param['table_level_code']}{param['coma3']}
    {param['s_overhead']}
FROM
    {PDC_ALL}
    {COG_ALL}
{param['where_isin_perim']}
{param['group_by']}
ORDER BY
    p_nom DESC"""

def query_i8(*param, simple=True, gen=False):
    '''Create SQL query for 'i8' indicators (see parameters in module docstring)'''

    indic = 'i8'
    prm = init_param_ixx(simple, gen, indic, *param)

    if prm['level'] == '00':
        return f"""
SELECT 
    (
        {query_i7(*param, simple=True, gen=gen)}
    ) / (
        SELECT 
            sum(population) 
        {prm['from_perim']}
        {prm['where_isin_perim']}
    ) * 100000 AS p_nom_pop{prm['coma']}
    {prm['s_overhead']}"""    

    return f"""
WITH
    i7 AS (
        {query_i7(*param, simple=True, gen=gen)}
    )
SELECT
    i7.p_nom::float / {prm['table_level_pop']} AS p_nom_pop,
    {prm['table_level_code']}{prm['coma3']}
    {prm['s_overhead']}
FROM
    i7
    LEFT JOIN {prm['table_level']} on i7.code = {prm['table_level_code']}
ORDER by
    p_nom_pop DESC"""

def query_i9(*param, simple=True, gen=False):
    '''Create SQL query for 'i9' indicators (see parameters in module docstring)'''

    indic = 'i9'
    prm = init_param_ixx(simple, gen, indic, *param)

    if prm['level'] == '00':
        return f"""
SELECT 
    (
        {query_i7(*param, simple=True, gen=gen)}
    ) / (
        SELECT 
            sum(area::float) 
        {prm['from_perim']}
        {prm['where_isin_perim']}
    ) * 100000000 AS p_nom_area{prm['coma']}
    {prm['s_overhead']}"""

    return f"""
WITH
    i7 AS (
        {query_i7(*param, simple=True, gen=gen)}
    )
SELECT
    i7.p_nom::float / {prm['table_level_area']} AS p_nom_area,
    {prm['table_level_code']}{prm['coma3']}
    {prm['s_overhead']}
FROM
    i7
    LEFT JOIN {prm['table_level']} on i7.code = {prm['table_level_code']}
ORDER by
    p_nom_area DESC"""

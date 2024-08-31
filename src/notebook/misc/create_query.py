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

create_query = sys.modules[__name__]

NATIONAL = "national(code, name) AS (VALUES ('00', 'national')) "
NATIONAL_S = "national(code) AS (VALUES ('00')) "
NATIONAL_G = "national(code) AS (VALUES ('{perim}')) "
P_TAB = ("puissance(p_range, p_cat) AS ( VALUES " + 
             "(numrange(0, 15.0), 1), (numrange(15.0, 26.0), 2), (numrange(26, 65.0), 3), " + 
             "(numrange(65, 175.0), 4), (numrange(175, 360.0), 5), (numrange(360, NULL), 6)) ")
JOIN_P = "LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range "
PDC_ALL = "pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id "
STAT_ALL = "station LEFT JOIN localisation ON localisation_id = localisation.id "
ISIN_GEOM = 'ST_Within("coordonneesXY", geometry) '

TABLE_DIC = "table_dic(code_d, table_d) AS (VALUES ('00', 'national'), ('01', 'region'), ('02', 'department'), ('03', 'epci'), ('04', 'city'))"
TABLE = {'00': 'national', '01': 'region', '02': 'department', '03': 'epci', '04': 'city'}

def to_indicator(engine, indicator, simple=False, histo=False, format='pandas', histo_timest=None, json_orient='split',
                 table_name=None, table_option="replace", query_gen=False):
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
        If True, timestamp additional column is added (without others additional columns)
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

    Returns
    -------
    String or Dataframe
        see 'format' parameter
    """
    indic = indicator + '-00'
    simple = True if histo else simple
    query = getattr(create_query, 'query_' + indic.split('-')[0])(*indic.split('-')[1:], simple=simple, gen=query_gen)
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
        table_name = table_name if table_name else indicator
        return indic_to_table(data_pd, table_name, engine, table_option=table_option)

def indic_to_table(pd_df, table_name, engine, table_option="replace"):
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
    pd_df.to_sql(table_name, engine, if_exists=table_option, index=False)
    return pd.read_sql_query('SELECT COUNT(*) AS count FROM "' + table_name + '"', engine)

def query_histo(query, timestamp=None):

    if timestamp:
        datation = "datation(timest) AS (VALUES ('" + timestamp + "'::timestamp)) "
    else:
        datation = "datation(timest) AS (VALUES (CURRENT_TIMESTAMP)) "

    return " WITH query AS (" + query + "), " + datation + " SELECT * FROM query, datation "

def init_param_txx(simple, gen, *param):
    '''parameters initialization for 'query_txx' functions
    '''
    perim, zone = (param + ('00', '00'))[:2]
    perim = perim.rjust(2, '0')
    zone = zone.rjust(2, '0')
    
    code_name = "code " if simple else "code, name "
    perimeter = f"perimeter(level) AS (VALUES ('{perim}')) "
    
    national = NATIONAL_S if simple else NATIONAL
    table_perim = f"{TABLE[perim]}"

    if gen:
        national = NATIONAL_G
        perimeter = f"perimeter(level) AS (VALUES ('{{perim}}')) "
        table_perim = f"{{TABLE[perim]}}"
        zone = f"{{zone}}"

    return (perim, zone, code_name, perimeter, national, table_perim)

def query_t1(*param, simple=False, gen=False):
    '''Create SQL query for 't1' indicators (see parameters in module docstring)'''
    
    perim, zone, code_name, perimeter, national, table_perim = init_param_txx(simple, gen, *param)

    if perim == '00':
        return f"""
    WITH {P_TAB}, 
         {national}, {perimeter}
    SELECT count(id_pdc_itinerance) AS nb_pdc, p_cat, p_range, level, {code_name}
    FROM perimeter, pointdecharge {JOIN_P}, {table_perim}
    GROUP BY p_cat, p_range, level, {code_name} ORDER BY nb_pdc DESC"""

    return f"""
    WITH {P_TAB}, 
         {perimeter}
    SELECT count(id_pdc_itinerance) AS nb_pdc, p_cat, p_range, level, {code_name}
    FROM perimeter, {PDC_ALL} {JOIN_P}, {table_perim}
    WHERE code = '{zone}' AND {ISIN_GEOM}
    GROUP BY p_cat, p_range, level, {code_name} ORDER BY nb_pdc DESC"""

def query_t2(*param, simple=False, gen=False):
    '''Create SQL query for 't2' indicators (see parameters in module docstring)'''
    
    code_name = "code " if simple else "code, name "

    return f"""
    WITH t1 AS ({query_t1(*param, simple=simple, gen=gen)})
    SELECT nb_pdc / (SELECT sum(nb_pdc) FROM t1) * 100 AS pct_nb_pdc, p_cat, p_range, level, {code_name}
    FROM t1"""

def query_t3(*param, simple=False, gen=False):
    '''Create SQL query for 't3' indicators (see parameters in module docstring)'''
    
    perim, zone, code_name, perimeter, national, table_perim = init_param_txx(simple, gen, *param)

    if perim == '00':
        return f""" 
    WITH stat AS (SELECT count(station_id) AS nb_pdc
            FROM pointdecharge LEFT JOIN station ON station.id = station_id 
            GROUP BY station_id), {national}, {perimeter}
    SELECT count(nb_pdc) AS nb_stations, nb_pdc, level, {code_name}
    FROM perimeter, stat, {table_perim}
    GROUP BY nb_pdc, level, {code_name} ORDER BY nb_stations DESC"""

    return f"""
    WITH stat AS (SELECT count(station_id) AS nb_pdc, {code_name}
            FROM {PDC_ALL}, {table_perim} 
            WHERE code = '{zone}' AND {ISIN_GEOM} GROUP BY station_id, {code_name}), 
        {perimeter}
    SELECT count(nb_pdc) AS nb_stations, nb_pdc, level, {code_name}
    FROM perimeter, stat
    GROUP BY nb_pdc, level, {code_name} ORDER BY nb_stations DESC"""

def query_t4(*param, simple=False, gen=False):
    '''Create SQL query for 't4' indicators (see parameters in module docstring)'''
    
    code_name = "code " if simple else "code, name " 

    return f"""
    WITH t3 AS ({query_t3(*param, simple=simple, gen=gen)})
    SELECT nb_stations / (SELECT sum(nb_stations) FROM t3) * 100 AS pct_nb_stations, nb_pdc, level, {code_name}
    FROM t3"""

def query_t5(*param, simple=False, gen=False):
    '''Create SQL query for 't5' indicators (see parameters in module docstring)'''
    
    perim, zone, code_name, perimeter, national, table_perim = init_param_txx(simple, gen, *param)
    
    if perim == '00':
        return f"""
    WITH {national}, {perimeter}
    SELECT count(id_station_itinerance) AS nb_stations, implantation_station AS implantation, level, {code_name} 
    FROM perimeter, station, {table_perim}
    GROUP BY implantation, level, {code_name} ORDER BY nb_stations DESC"""
    
    return f"""
    WITH {perimeter}
    SELECT count(id_station_itinerance) AS nb_stations, implantation_station AS implantation, level, {code_name}
    FROM perimeter, {STAT_ALL}, {table_perim}
    WHERE code = '{zone}' AND {ISIN_GEOM}
    GROUP BY implantation, level, {code_name} ORDER BY nb_stations DESC"""

def query_t6(*param, simple=False, gen=False):
    '''Create SQL query for 't6' indicators (see parameters in module docstring)'''
    
    code_name = "code " if simple else "code, name " 

    return f"""
    WITH t5 AS ({query_t5(*param, simple=simple, gen=gen)})
    SELECT nb_stations / (SELECT sum(nb_stations) FROM t5) * 100 AS pct_nb_stations, implantation, level, {code_name}
    FROM t5"""
    """return (" WITH t5 AS (" + query_t5(*param) + ")" +
        " SELECT nb_stations / (SELECT sum(nb_stations) FROM t5) * 100 AS pct_nb_stations, implantation, level" + code_name +
        " FROM t5")"""

def init_param_ixx(simple, gen, *param):
    '''parameters initialization for 'query_ixx' functions  '''
    
    perim, val, zone = (param + ('00', '00', '00'))[:3]
    perim = perim.rjust(2, '0')
    val = val.rjust(2, '0')
    zone = zone.rjust(2, '0')

    code_name = ", code " if simple else ", code, name "
    perimeter = f"perimeter(level) AS (VALUES ('{perim}')) "
    perim_zon = f"perim_zon(level) AS (VALUES ('{zone}')) "
    perim_val = f"perim_zon(code) AS (VALUES ('{val}')) "

    national = NATIONAL_S if simple else NATIONAL
    table_perim = f"{TABLE[perim]}"
    table_zone = f"{TABLE[zone]}"

    if gen:
        national = NATIONAL_G
        perimeter = f"perimeter(level) AS (VALUES ('{{perim}}')) "
        perim_zon = f"perim_zon(level) AS (VALUES ('{{zone}}')) "
        perim_val = f"perim_zon(code) AS (VALUES ('{{val}}')) "
        table_perim = f"{{TABLE[perim]}}"
        table_zone = f"{{TABLE[zone]}}"
    
    return (perim, val, zone, 
            code_name, perimeter, perim_zon, perim_val,
            national, table_perim, table_zone)

def query_i11(*param, simple=False, gen=False):

    perim, val, zone = (param + ('00', '00', '00'))[:3]
    perim = perim.rjust(2, '0')
    val = val.rjust(2, '0')
    zone = zone.rjust(2, '0')

    pdc_cog = f"""
        x_city AS (SELECT geometry, code AS c_code, department_id, epci_id  FROM city),
        x_department AS (SELECT id as d_id, code AS d_code, region_id FROM department),
        x_epci AS (SELECT id as e_id, code AS e_code FROM epci),
        x_region AS (SELECT id as r_id, code AS r_code FROM region),
        city_cog AS (SELECT geometry, c_code, d_code, e_code, r_code from x_city LEFT JOIN x_department ON x_department.d_id = department_id LEFT JOIN x_epci ON x_epci.e_id = epci_id LEFT JOIN x_region ON region_id = x_region.r_id),
        pdc_all AS (SELECT * from pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id),
        pdc_cog AS (SELECT * from pdc_all LEFT JOIN city_cog ON ST_Within("coordonneesXY", geometry))"""

    FIELD = {'00': 'all_data', '01': 'r_code', '02': 'd_code', '03': 'e_code', '04': 'c_code'}
    zone = perim if zone == '00' else zone
    code_val = FIELD[perim]
    code_zone = FIELD[zone]
    
    # perimeter = f"perimeter(level, all_data) AS (VALUES ('{zone}', '00')) "

    return f"""
    WITH {pdc_cog}, 
         perimeter(level, all_data) AS (VALUES ('{zone}', '00'))
    SELECT count(id_pdc_itinerance) AS nb_pdc, level, {code_zone} AS x_code
    FROM perimeter, pdc_cog
    WHERE {code_val} = '{val}'
    GROUP BY level, x_code ORDER BY nb_pdc DESC"""

def query_i1(*param, simple=False, gen=False):
    '''Create SQL query for 'i1' indicators (see parameters in module docstring)'''

    (perim, val, zone, code_name, perimeter, perim_zon, perim_val,
     national, table_perim, table_zone) = init_param_ixx(simple, gen, *param)

    pdc_loc = f"""pdc_loc AS (SELECT id_pdc_itinerance, "coordonneesXY"
                     FROM {TABLE[perim]}, {PDC_ALL}
                     WHERE  code = '{val}' AND {ISIN_GEOM})"""
    if gen:
        pdc_loc = f"""pdc_loc AS (SELECT id_pdc_itinerance, "coordonneesXY"
                         FROM {{TABLE[perim]}}, {PDC_ALL}
                         WHERE  code = '{{val}}' AND {ISIN_GEOM})"""
    
    if perim == zone == '00':
        return f""" 
    WITH  {national}, {perim_zon}
    SELECT count(id_pdc_itinerance) AS nb_pdc, level {code_name} 
    FROM perim_zon, pointdecharge, {table_perim}
    GROUP BY level {code_name} """
    
    if perim == '00':
        return f"""
    WITH {national}, {perim_zon}
    SELECT count(id_pdc_itinerance) AS nb_pdc, level {code_name} 
    FROM perim_zon, {PDC_ALL} LEFT JOIN {table_zone} ON {ISIN_GEOM}
    GROUP BY level {code_name} ORDER BY nb_pdc DESC"""

    if int(zone) <= int(perim):
        return f"""
    WITH {pdc_loc}, {perimeter}, {perim_val}
    SELECT count(id_pdc_itinerance) AS nb_pdc, level, code
    FROM perimeter, perim_zon, pdc_loc
    GROUP BY level, code ORDER BY nb_pdc DESC"""

    return f"""
    WITH {pdc_loc}, {perim_zon}
    SELECT count(id_pdc_itinerance) AS nb_pdc, level {code_name}
    FROM perim_zon, pdc_loc LEFT JOIN {table_zone} ON {ISIN_GEOM}
    GROUP BY level {code_name} ORDER BY nb_pdc DESC"""

def query_i4(*param, simple=False, gen=False):
    '''Create SQL query for 'i4' indicators (see parameters in module docstring)'''
    
    (perim, val, zone, code_name, perimeter, perim_zon, perim_val,
     national, table_perim, table_zone) = init_param_ixx(simple, gen, *param)

    stat_loc = f"""stat_loc AS (SELECT id_station_itinerance, "coordonneesXY"
                     FROM {TABLE[perim]}, {STAT_ALL}
                     WHERE  code = '{val}' AND {ISIN_GEOM})"""
    if gen:
        stat_loc = f"""stat_loc AS (SELECT id_station_itinerance, "coordonneesXY"
                     FROM {{TABLE[perim]}}, {STAT_ALL}
                     WHERE  code = '{{val}}' AND {ISIN_GEOM})"""
        
    if perim == zone == '00':
        return f""" 
    WITH  {national}, {perim_zon}
    SELECT count(id_station_itinerance) AS nb_stat, level {code_name} 
    FROM perim_zon, station, {table_perim}
    GROUP BY level {code_name} """

    if perim == '00':
        return f"""
    WITH {national}, {perim_zon}
    SELECT count(id_station_itinerance) AS nb_stat, level {code_name} 
    FROM perim_zon, {STAT_ALL} LEFT JOIN {table_zone} ON {ISIN_GEOM}
    GROUP BY level {code_name} ORDER BY nb_stat DESC"""

    if int(zone) <= int(perim):
        return f"""
    WITH {stat_loc}, {perimeter}, {perim_val}
    SELECT count(id_station_itinerance) AS nb_stat, level, code
    FROM perimeter, perim_zon, stat_loc
    GROUP BY level, code ORDER BY nb_stat DESC"""

    return f"""
    WITH {stat_loc}, {perim_zon}
    SELECT count(id_station_itinerance) AS nb_stat, level {code_name}
    FROM perim_zon, stat_loc LEFT JOIN {table_zone} ON {ISIN_GEOM}
    GROUP BY level {code_name} ORDER BY nb_stat DESC"""

def query_i7(*param, simple=False, gen=False):
    '''Create SQL query for 'i7' indicators (see parameters in module docstring)'''

    (perim, val, zone, code_name, perimeter, perim_zon, perim_val,
     national, table_perim, table_zone) = init_param_ixx(simple, gen, *param)

    pnom_loc = f"""pnom_loc AS (SELECT puissance_nominale, "coordonneesXY"
                   FROM {TABLE[perim]}, {PDC_ALL}
                   WHERE  code = '{val}' AND {ISIN_GEOM})"""
    if gen:
            pnom_loc = f"""pnom_loc AS (SELECT puissance_nominale, "coordonneesXY"
                   FROM {{TABLE[perim]}}, {PDC_ALL}
                   WHERE  code = '{{val}}' AND {ISIN_GEOM})"""

    if perim == zone == '00':
        return f""" 
    WITH  {national}, {perim_zon}
    SELECT sum(puissance_nominale) AS p_nom, level {code_name} 
    FROM perim_zon, pointdecharge, {table_perim}
    GROUP BY level {code_name} """

    if perim == '00':
        return f"""
    WITH {national}, {perim_zon}
    SELECT sum(puissance_nominale) AS p_nom, level {code_name} 
    FROM perim_zon, {PDC_ALL} LEFT JOIN {table_zone} ON {ISIN_GEOM}
    GROUP BY level {code_name} ORDER BY p_nom DESC"""

    if int(zone) <= int(perim):
        return f"""
    WITH {pnom_loc}, {perimeter}, {perim_val}
    SELECT sum(puissance_nominale) AS p_nom, level, code
    FROM perimeter, perim_zon, pnom_loc
    GROUP BY level, code ORDER BY p_nom DESC"""

    return f"""
    WITH {pnom_loc}, {perim_zon}
    SELECT sum(puissance_nominale) AS p_nom, level {code_name}
    FROM perim_zon, pnom_loc LEFT JOIN {table_zone} ON {ISIN_GEOM}
    GROUP BY level {code_name} ORDER BY p_nom DESC"""

"""
The `create_query` module includes query generators for QualiCharge indicators.

Each 'query_xx' function is defined with:

Parameters
----------
param: tuple of two or three str 
    Indicator parameters (see indicator codification)
simple: boolean (default False)
    If False, additional columns are added in the result Table

Returns
-------
String
    SQL query to apply
"""
NATIONAL = "national(code, name) AS (VALUES ('00', 'national')) "
P_TAB = ("puissance(p_range, p_cat) AS ( VALUES " + 
             "(numrange(0, 15.0), 1), (numrange(15.0, 26.0), 2), (numrange(26, 65.0), 3), " + 
             "(numrange(65, 175.0), 4), (numrange(175, 360.0), 5), (numrange(360, NULL), 6)) ")
P_JOIN = "LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range "
PDC_ALL = "pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id "
STAT_ALL = "station LEFT JOIN localisation ON localisation_id = localisation.id "
ISIN_GEOM = 'ST_Within("coordonneesXY", geometry) '

TABLE = {'00': 'national', '01': 'region', '02': 'department', '03': 'epci', '04': 'city'}

def init_param_txx(simple, *param):
    '''parameters initialization for 'query_txx' functions
    '''
    level, zone = (param + ('00', '00'))[:2]
    level = level.rjust(2, '0')
    zone = zone.rjust(2, '0')
    
    code_name = ", code " if simple else ", code, name "
    perimeter = "perimeter(level) AS (VALUES ('" + level + "')) "
    
    return (level, zone, code_name, perimeter)

def query_t1(*param, simple=False):
    '''Create SQL query for 't1' indicators (see parameters in module docstring)'''
    
    level, zone, code_name, perimeter = init_param_txx(simple, *param)

    if level == '00':
        return (" WITH " + P_TAB + ", " + NATIONAL + ", " + perimeter +
                " SELECT count(id_pdc_itinerance) AS nb_pdc, p_cat, p_range, level" + code_name + 
                " FROM perimeter, pointdecharge " + P_JOIN + ", " + TABLE[level] +
                " GROUP BY p_cat, p_range, level" + code_name + " ORDER BY nb_pdc DESC")

    return (" WITH " + P_TAB + ", " + perimeter +
            " SELECT count(id_pdc_itinerance) AS nb_pdc, p_cat, p_range, level" + code_name +
            " FROM perimeter, " + PDC_ALL + P_JOIN + ", " + TABLE[level] +
            " WHERE code = '" + zone + "' AND " + ISIN_GEOM +
            " GROUP BY p_cat, p_range, level" + code_name + " ORDER BY nb_pdc DESC")

def query_t2(*param, simple=False):
    '''Create SQL query for 't2' indicators (see parameters in module docstring)'''
    
    code_name = ", code " if simple else ", code, name "

    return (" WITH t1 AS (" + query_t1(*param) + ")" +
        " SELECT nb_pdc / (SELECT sum(nb_pdc) FROM t1) * 100 AS pct_nb_pdc, p_cat, p_range, level" + code_name +
        " FROM t1")


def query_t3(*param, simple=False):
    '''Create SQL query for 't3' indicators (see parameters in module docstring)'''
    
    level, zone, code_name, perimeter = init_param_txx(simple, *param)

    if level == '00':
        return (" WITH stat AS (SELECT count(station_id) AS nb_pdc " + 
                    " FROM pointdecharge LEFT JOIN station ON station.id = station_id " + 
                    " GROUP BY station_id), " + NATIONAL + ", " + perimeter +
                " SELECT count(nb_pdc) AS nb_stations, nb_pdc, level" + code_name + 
                " FROM perimeter, stat, " + TABLE[level] +
                " GROUP BY nb_pdc, level" + code_name + " ORDER BY nb_stations DESC")
    
    return (" WITH stat AS (SELECT count(station_id) AS nb_pdc" + code_name + 
                " FROM " + PDC_ALL + ", " + TABLE[level] + 
                " WHERE code = '" + zone + "' AND " + ISIN_GEOM +
                " GROUP BY station_id" + code_name + "), " + perimeter + 
            " SELECT count(nb_pdc) AS nb_stations, nb_pdc, level" + code_name +
            " FROM perimeter, stat " +
            " GROUP BY nb_pdc, level" + code_name + " ORDER BY nb_stations DESC")

def query_t4(*param, simple=False):
    '''Create SQL query for 't4' indicators (see parameters in module docstring)'''
    
    code_name = ", code " if simple else ", code, name " 

    return (" WITH t3 AS (" + query_t3(*param) + ")" +
        " SELECT nb_stations / (SELECT sum(nb_stations) FROM t3) * 100 AS pct_nb_pdc, nb_pdc, level" + code_name +
        " FROM t3")

def query_t5(*param, simple=False):
    '''Create SQL query for 't5' indicators (see parameters in module docstring)'''
    
    level, zone, code_name, perimeter = init_param_txx(simple, *param)
    
    if level == '00':
        return (" WITH " + NATIONAL + ", " + perimeter +
                " SELECT count(id_station_itinerance) AS nb_stations, implantation_station AS implantation, level" + code_name + 
                " FROM perimeter, station, " + TABLE[level] +
                " GROUP BY implantation, level" + code_name + " ORDER BY nb_stations DESC")
    
    return (" WITH " + perimeter +
            " SELECT count(id_station_itinerance) AS nb_stations, implantation_station AS implantation, level" + code_name +
            " FROM perimeter, " + STAT_ALL + ", " + TABLE[level] +
            " WHERE code = '" + zone + "' AND " + ISIN_GEOM +
            " GROUP BY implantation, level" + code_name + " ORDER BY nb_stations DESC")

def query_t6(*param, simple=False):
    '''Create SQL query for 't6' indicators (see parameters in module docstring)'''
    
    code_name = ", code " if simple else ", code, name " 

    return (" WITH t5 AS (" + query_t5(*param) + ")" +
        " SELECT nb_stations / (SELECT sum(nb_stations) FROM t5) * 100 AS pct_nb_stations, implantation, level" + code_name +
        " FROM t5")

def init_param_ixx(simple, *param):
    '''parameters initialization for 'query_ixx' functions  '''
    
    level, val, zone = (param + ('00', '00', '00'))[:3]
    level = level.rjust(2, '0')
    val = val.rjust(2, '0')
    zone = zone.rjust(2, '0')

    code_name = ", code " if simple else ", code, name "
    perimeter = "perimeter(level) AS (VALUES ('" + level + "')) "
    perim_zon = "perim_zon(level) AS (VALUES ('" + zone + "')) "
    perim_val = "perim_zon(code) AS (VALUES ('" + val + "')) "

    return (level, val, zone, code_name, perimeter, perim_zon, perim_val)

def query_i1(*param, simple=False):
    '''Create SQL query for 'i1' indicators (see parameters in module docstring)'''

    level, val, zone, code_name, perimeter, perim_zon, perim_val = init_param_ixx(simple, *param)
    
    pdc_loc = (' pdc_loc AS (SELECT id_pdc_itinerance, "coordonneesXY" ' +
                        " FROM " + PDC_ALL + "," + TABLE[level] +
                        " WHERE  code = '" + val + "' AND " + ISIN_GEOM + ")" )
    
    if level == zone == '00':
        return (" WITH " + NATIONAL + ", " + perimeter +
                " SELECT count(id_pdc_itinerance) AS nb_pdc, level" + code_name + 
                " FROM perimeter, pointdecharge, " + TABLE[level] +
                " GROUP BY level" + code_name)
    
    if level == '00':
        return (" WITH " + NATIONAL + ", " + perim_zon +
                " SELECT count(id_pdc_itinerance) AS nb_pdc, level" + code_name + 
                " FROM perim_zon, " + PDC_ALL + " LEFT JOIN " + TABLE[zone] + " ON " + ISIN_GEOM +
                " GROUP BY level" + code_name + " ORDER BY nb_pdc DESC")
    
    if int(zone) <= int(level):
        return (" WITH " + pdc_loc + ", " + perimeter + ", " + perim_val +
                " SELECT count(id_pdc_itinerance) AS nb_pdc, level, code" +
                " FROM perimeter, perim_zon, pdc_loc" +
                " GROUP BY level, code ORDER BY nb_pdc DESC")

    return (" WITH " + pdc_loc + ", " + perim_zon +
            " SELECT count(id_pdc_itinerance) AS nb_pdc, level" + code_name + 
            " FROM perim_zon, pdc_loc LEFT JOIN " + TABLE[zone] + " ON " + ISIN_GEOM +
            " GROUP BY level" + code_name + " ORDER BY nb_pdc DESC")

def query_i4(*param, simple=False):
    '''Create SQL query for 'i4' indicators (see parameters in module docstring)'''
    
    level, val, zone, code_name, perimeter, perim_zon, perim_val = init_param_ixx(simple, *param)

    stat_loc = (' stat_loc AS (SELECT id_station_itinerance, "coordonneesXY" ' +
                        " FROM " + STAT_ALL + "," + TABLE[level] +
                        " WHERE  code = '" + val + "' AND " + ISIN_GEOM + ")")
    
    if level == zone == '00':
        return (" WITH " + NATIONAL + ", " + perimeter +
                " SELECT count(id_station_itinerance) AS nb_stat, level" + code_name + 
                " FROM perimeter, station, " + TABLE[level] +
                " GROUP BY level" + code_name)

    if level == '00':
        return (" WITH " + NATIONAL + ", " + perim_zon +
                " SELECT count(id_station_itinerance) AS nb_stat, level" + code_name + 
                " FROM perim_zon, " + STAT_ALL + " LEFT JOIN " + TABLE[zone] + " ON " + ISIN_GEOM +
                " GROUP BY level" + code_name + " ORDER BY nb_stat DESC")    

    if int(zone) <= int(level):
        return (" WITH " + stat_loc + ", " + perimeter + ", " + perim_val +
                " SELECT count(id_station_itinerance) AS nb_stat, level, code" +
                " FROM perimeter, perim_zon, stat_loc" +
                " GROUP BY level, code ORDER BY nb_stat DESC")

    return (" WITH " + stat_loc + ", " + perim_zon +
            " SELECT count(id_station_itinerance) AS nb_stat, level" + code_name + 
            " FROM perim_zon, stat_loc LEFT JOIN " + TABLE[zone] + " ON " + ISIN_GEOM +
            " GROUP BY level" + code_name + " ORDER BY nb_stat DESC")

def query_i7(*param, simple=False):
    '''Create SQL query for 'i7' indicators (see parameters in module docstring)'''
    
    level, val, zone, code_name, perimeter, perim_zon, perim_val = init_param_ixx(simple, *param)

    pnom_loc = (' pnom_loc AS (SELECT puissance_nominale, "coordonneesXY" ' +
                        " FROM " + PDC_ALL + "," + TABLE[level] +
                        " WHERE  code = '" + val + "' AND " + ISIN_GEOM + ")")
    
    if level == zone == '00':
        return (" WITH " + NATIONAL + ", " + perimeter +
                " SELECT sum(puissance_nominale) AS p_nom, level" + code_name + 
                " FROM perimeter, pointdecharge, " + TABLE[level] +
                " GROUP BY level" + code_name)
    
    if level == '00':
        return (" WITH " + NATIONAL + ", " + perim_zon +
                " SELECT sum(puissance_nominale) AS p_nom, level" + code_name + 
                " FROM perim_zon, " + PDC_ALL + " LEFT JOIN " + TABLE[zone] + " ON " + ISIN_GEOM +
                " GROUP BY level" + code_name + " ORDER BY p_nom DESC")   

    if int(zone) <= int(level):
        return (" WITH " + pnom_loc + ", " + perimeter + ", " + perim_val +
                " SELECT sum(puissance_nominale) AS p_nom, level, code" +
                " FROM perimeter, perim_zon, pnom_loc" +
                " GROUP BY level, code ORDER BY p_nom DESC")

    return (" WITH " + pnom_loc + ", " + perim_zon +
            " SELECT sum(puissance_nominale) AS p_nom, level" + code_name + 
            " FROM perim_zon, pnom_loc LEFT JOIN " + TABLE[zone] + " ON " + ISIN_GEOM +
            " GROUP BY level" + code_name + " ORDER BY p_nom DESC")
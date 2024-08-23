"""
The `create_query` module includes query generators for QualiCharge indicators.


    Parameters
    ----------
    param : DataFrame
        Data used to calculate the indicator.
    
    Returns
    -------
    DataFrame
        Indicator as tabular data

"""
P_TAB = ("puissance(p_range, p_cat) AS ( VALUES " + 
             "(numrange(0, 15.0), 1), (numrange(15.0, 26.0), 2), (numrange(26, 65.0), 3), " + 
             "(numrange(65, 175.0), 4), (numrange(175, 360.0), 5), (numrange(360, NULL), 6)) ")
P_JOIN = "LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range "
PDC_ALL = "pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id "
STAT_ALL = "station LEFT JOIN localisation ON localisation_id = localisation.id "
ISIN_GEOM = 'ST_Within("coordonneesXY", geometry) '

LEVEL = {'00': 'national', '01': 'region', '02': 'department', '03': 'epci', '04': 'city',
         '0': 'national', '1': 'region', '2': 'department', '3': 'epci', '4': 'city'}

def query_t1(*param):
    
    level, zone = (param + ('00', '00'))[:2]
    
    if int(level) == 0:
        return (" WITH " + P_TAB + 
                " SELECT count(id_pdc_itinerance) AS nb_pdc, p_cat, p_range " +
                " FROM pointdecharge " + P_JOIN +
                " GROUP BY p_cat, p_range ORDER BY nb_pdc DESC")
    
    lvl = LEVEL[level]
    zon = "'" + zone + "'"
    return (" WITH " + P_TAB + 
            " SELECT count(id_pdc_itinerance) AS nb_pdc, p_cat, p_range, code, name " +
            " FROM " + PDC_ALL + P_JOIN + ", " + lvl +
            " WHERE code = " + zon + " AND " + ISIN_GEOM +
            " GROUP BY p_cat, p_range, code, name ORDER BY nb_pdc DESC")

def query_t2(*param):
    
    code_name = ", code, name " if param[0] and int(param[0]) else "" 
    return (" WITH t1 AS (" + query_t1(*param) + ")" +
        " SELECT nb_pdc / (SELECT sum(nb_pdc) FROM t1) * 100 AS pct_nb_pdc, p_cat, p_range" + code_name +
        " FROM t1")


def query_t3(*param):
    
    level, zone = (param + ('00', '00'))[:2]
    
    if int(level) == 0:
        return (" WITH stat AS (SELECT count(station_id) AS nb_pdc " + 
                    " FROM pointdecharge LEFT JOIN station ON station.id = station_id " + 
                    " GROUP BY station_id) " + 
                " SELECT nb_pdc, count(nb_pdc) AS nb_stations FROM stat " +
                " GROUP BY nb_pdc ORDER BY nb_stations DESC")
    
    lvl = LEVEL[level]
    zon = "'" + zone + "'"
    return (" WITH stat AS (SELECT count(station_id) AS nb_pdc, code, name " + 
                " FROM " + PDC_ALL + ", " + lvl + 
                " WHERE code = " + zon + " AND " + ISIN_GEOM +
                " GROUP BY station_id, code, name)" + 
            " SELECT nb_pdc, count(nb_pdc) AS nb_stations, code, name FROM stat " +
            " GROUP BY nb_pdc, code, name ORDER BY nb_stations DESC")

def query_t4(*param):
    
    code_name = ", code, name " if param[0] and int(param[0]) else "" 
    return (" WITH t3 AS (" + query_t3(*param) + ")" +
        " SELECT nb_pdc, nb_stations / (SELECT sum(nb_stations) FROM t3) * 100 AS pct_nb_pdc" + code_name +
        " FROM t3")

def query_t5(*param):
    
    level, zone = (param + ('00', '00'))[:2]
    
    if int(level) == 0:
        return (" SELECT implantation_station AS implantation, count(id_station_itinerance) AS nb_stations " +
                " FROM station " +
                " GROUP BY implantation ORDER BY nb_stations DESC")
    
    lvl = LEVEL[level]
    zon = "'" + zone + "'"
    return (" SELECT implantation_station AS implantation, count(id_station_itinerance) AS nb_stations, code, name " +
            " FROM " + STAT_ALL + ", " + lvl +
            " WHERE code = " + zon + " AND " + ISIN_GEOM +
            " GROUP BY implantation, code, name ORDER BY nb_stations DESC")

def query_t6(*param):
    
    code_name = ", code, name " if param[0] and int(param[0]) else "" 
    return (" WITH t5 AS (" + query_t5(*param) + ")" +
        " SELECT implantation, nb_stations / (SELECT sum(nb_stations) FROM t5) * 100 AS pct_nb_stations" + code_name +
        " FROM t5")

def query_i1(*param):
    
    level, val_level, zone = (param + ('00', '00', '00'))[:3]

    if int(level) == 0 and int(zone) == int(level):
        return " SELECT count(id_pdc_itinerance) AS nb_pdc FROM pointdecharge"
    
    zon = LEVEL[zone]
    if int(level) == 0:
        return (" SELECT count(id_pdc_itinerance) AS nb_pdc, code, name " +
                " FROM " + PDC_ALL + " LEFT JOIN " + zon + " ON " + ISIN_GEOM +
                " GROUP BY code, name ORDER BY nb_pdc DESC")
    
    val_lvl = "'" + val_level + "'"
    lvl = LEVEL[level]
    with_pdc_loc = (' WITH pdc_loc AS (SELECT id_pdc_itinerance, "coordonneesXY" ' +
                        " FROM " + PDC_ALL + "," + lvl +
                        " WHERE  code = " + val_lvl + " AND " + ISIN_GEOM + ")" )
    if int(zone) <= int(level):
        return with_pdc_loc + " SELECT count(id_pdc_itinerance) AS nb_pdc FROM pdc_loc"

    return (with_pdc_loc +
            " SELECT count(id_pdc_itinerance) AS nb_pdc, code, name " +
            " FROM pdc_loc LEFT JOIN " + zon + " ON " + ISIN_GEOM +
            " GROUP BY code, name ORDER BY nb_pdc DESC")

def query_i4(*param):
    
    level, val_level, zone = (param + ('00', '00', '00'))[:3]

    if int(level) == 0 and int(zone) == int(level):
        return " SELECT count(id_station_itinerance) AS nb_stat FROM station"
    
    zon = LEVEL[zone]
    if int(level) == 0:
        return (" SELECT count(id_station_itinerance) AS nb_stat, code, name " +
                " FROM " + STAT_ALL + " LEFT JOIN " + zon + " ON " + ISIN_GEOM +
                " GROUP BY code, name ORDER BY nb_stat DESC")
    
    val_lvl = "'" + val_level + "'"
    lvl = LEVEL[level]
    with_stat_loc = (' WITH stat_loc AS (SELECT id_station_itinerance, "coordonneesXY" ' +
                        " FROM " + STAT_ALL + "," + lvl +
                        " WHERE  code = " + val_lvl + " AND " + ISIN_GEOM + ")")
    if int(zone) <= int(level):
        return with_stat_loc + " SELECT count(id_station_itinerance) AS nb_stat FROM stat_loc"

    return (with_stat_loc +
            " SELECT count(id_station_itinerance) AS nb_stat, code, name " +
            " FROM stat_loc LEFT JOIN " + zon + " ON " + ISIN_GEOM +
            " GROUP BY code, name ORDER BY nb_stat DESC")

def query_i7(*param):
    
    level, val_level, zone = (param + ('00', '00', '00'))[:3]

    if int(level) == 0 and int(zone) == int(level):
        return " SELECT sum(puissance_nominale) AS p_nom FROM pointdecharge"

    zon = LEVEL[zone]
    if int(level) == 0:
        return (" SELECT sum(puissance_nominale) AS p_nom, code, name " +
                " FROM " + PDC_ALL + " LEFT JOIN " + zon + " ON " + ISIN_GEOM +
                " GROUP BY code, name ORDER BY p_nom DESC")
    
    val_lvl = "'" + val_level + "'"
    lvl = LEVEL[level]
    with_pnom_loc = (' WITH pnom_loc AS (SELECT puissance_nominale, "coordonneesXY" ' +
                        " FROM " + PDC_ALL + "," + lvl +
                        " WHERE  code = " + val_lvl + " AND " + ISIN_GEOM + ")")
    if int(zone) <= int(level):
        return with_pnom_loc + " SELECT sum(puissance_nominale) AS p_nom FROM pnom_loc"

    return  (with_pnom_loc +
            " SELECT sum(puissance_nominale) AS p_nom, code, name " +
            " FROM pnom_loc LEFT JOIN " + zon + " ON " + ISIN_GEOM +
            " GROUP BY code, name ORDER BY p_nom DESC")


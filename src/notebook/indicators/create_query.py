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
LEVEL = {'00': 'national', '01': 'region', '02': 'department', '03': 'epci', '04': 'city'}

def query_t1(*param):
    
    level, zone = (param + (None, None))[:2]
    
    if level == '00':
        return (" WITH " + P_TAB + 
                " SELECT count(id_pdc_itinerance) AS nb_pdc, p_cat, p_range " +
                " FROM pointdecharge " + P_JOIN +
                " GROUP BY p_cat, p_range ORDER BY nb_pdc DESC")
    
    lvl = LEVEL[level]
    zon = "'" + zone + "'"
    return (" WITH " + P_TAB + 
            " SELECT count(id_pdc_itinerance) AS nb_pdc, p_cat, p_range, code, name " +
            " FROM " + PDC_ALL + P_JOIN + ", " + lvl +
            " WHERE code = " + zon + ' AND ST_Within("coordonneesXY", geometry) ' +
            " GROUP BY p_cat, p_range, code, name ORDER BY nb_pdc DESC")

def query_t3(*param):
    
    level, zone = (param + (None, None))[:2]
    
    if level == '00':
        return (" WITH stat AS (SELECT count(station_id) AS nb_pdc " + 
                    " FROM pointdecharge LEFT JOIN station ON station.id = station_id " + 
                    " GROUP BY station_id) " + 
                " SELECT nb_pdc, count(nb_pdc) AS nb_stations FROM stat " +
                " GROUP BY nb_pdc ORDER BY nb_stations DESC")
    
    lvl = LEVEL[level]
    zon = "'" + zone + "'"
    return (" WITH stat AS (SELECT count(station_id) AS nb_pdc, code, name " + 
                " FROM " + PDC_ALL + ", " + lvl + 
                " WHERE code = " + zon + ' AND ST_Within("coordonneesXY", geometry) ' +
                " GROUP BY station_id, code, name)" + 
            " SELECT nb_pdc, count(nb_pdc) AS nb_stations, code, name FROM stat " +
            " GROUP BY nb_pdc, code, name ORDER BY nb_stations DESC")

def query_t5(*param):
    
    level, zone = (param + (None, None))[:2]
    
    if level == '00':
        return (" SELECT implantation_station, count(id_station_itinerance) AS nb_stations FROM station " +
                " GROUP BY implantation_station ORDER BY nb_stations DESC")
    
    lvl = LEVEL[level]
    zon = "'" + zone + "'"
    return (" SELECT implantation_station, count(id_station_itinerance) AS nb_stations, code, name " +
            " FROM " + STAT_ALL + ", " + lvl +
            " WHERE code = " + zon + ' AND ST_Within("coordonneesXY", geometry) ' +
            " GROUP BY implantation_station, code, name ORDER BY nb_stations DESC")

def query_i1(*param):
    
    level, val_level, zone = (param + (None, None, None))[:3]
    zon = LEVEL[zone]

    if level == '00':
        return (" SELECT count(id_pdc_itinerance) AS nb_pdc, code, name " +
                " FROM " + PDC_ALL + " LEFT JOIN " + zon + ' on ST_Within("coordonneesXY", geometry)' +
                " GROUP BY code, name ORDER BY nb_pdc DESC")
    
    val_lvl = "'" + val_level + "'"
    lvl = LEVEL[level]
    return (' WITH pdc_loc AS (SELECT id_pdc_itinerance, "coordonneesXY" ' +
                " FROM " + PDC_ALL + "," + lvl +
                " WHERE  code = " + val_lvl + ' AND ST_Within("coordonneesXY", geometry)) ' +
            " SELECT count(id_pdc_itinerance) AS nb_pdc, code, name " +
            " FROM pdc_loc LEFT JOIN " + zon + ' on ST_Within("coordonneesXY", geometry)' +
            " GROUP BY code, name ORDER BY nb_pdc DESC")

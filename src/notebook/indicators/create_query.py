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
LEVEL = {'00': 'national', '01': 'region', '02': 'department', '03': 'epci', '04': 'city'}

def query_t1(*param):
    
    level, zone = (param + (None, None))[:2]
    
    if level == '00':
        return (" WITH " + P_TAB + 
                " SELECT count(id_pdc_itinerance) AS nb_pdc, p_cat, p_range" +
                " FROM pointdecharge " + P_JOIN +
                " GROUP BY p_cat, p_range ORDER BY nb_pdc DESC")
    
    lvl = LEVEL[level]
    zon = "'" + zone + "'"
    return (" WITH " + P_TAB + 
            " SELECT count(id_pdc_itinerance) AS nb_pdc, p_cat, p_range, code, name" +
            " FROM " + PDC_ALL + P_JOIN + ", " + lvl +
            " WHERE code = " + zon + ' AND ST_Within("coordonneesXY", geometry)' +
            " GROUP BY p_cat, p_range, code, name ORDER BY nb_pdc DESC")
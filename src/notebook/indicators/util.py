"""
The `util` module includes functions and classes used for QualiCharge indicators.
"""
import pandas as pd

def init_data_pandas(indic, indic_dict, engine, *param):
    """create DataFrame for an indicator"""
    query = indic_dict[indic]['query']
    with engine.connect() as conn:
        data_pd = pd.read_sql_query(query, conn)
    return data_pd

def indic_to_table(indicator, table_name, engine, option="replace"):
    """ Save the indicator to a table"""
    indicator.to_sql(table_name, engine, if_exists=option, index=False)
    # test (à supprimer)
    query = 'SELECT COUNT(*) AS count FROM ' + table_name
    print(pd.read_sql_query(query, engine))

'''
def init_data_sources(indics, indic_dict, sql_dict, engine):
    """create source DataFrame for a list of indicators"""
    sources_list = set(indic_dict[indic]['source'] for indic in indics)
    with engine.connect() as conn:
        data_dict = {source: pd.read_sql_query(query, conn) for source, query in sql_dict.items() if source in sources_list}
    
    # provisoire
    if 'static' in sql_dict:
        data_dict['static']["departement"] = data_dict['static']["code_insee_commune"].str.slice(stop=2)
    
    return data_dict

def indic_to_table(indicator, table_name, engine, option="replace"):
    """ Save the indicator to a table"""
    indicator.to_sql(table_name, engine, if_exists=option, index=False)
    # test (à supprimer)
    query = 'SELECT COUNT(*) AS count FROM ' + table_name
    print(pd.read_sql_query(query, engine))

"""
The `source` module includes QualiCharge indicator generation functions
"""
import uuid
import pandas as pd

def indic_i1(data):
    """create result DataFrame of 'i1' indicator.
    i1 indicator is the number of pdc for each department.
    
    Parameters
    ----------
    data : DataFrame
        Data used to calculate the indicator.
    
    Returns
    -------
    DataFrame
        Indicator as tabular data
    """
    indicator = pd.pivot_table(data, index=["departement"], values="id_pdc_itinerance", aggfunc="count")
    # another method (à supprimer): 
    # indicator = data.loc[:, ["departement"]].reset_index().groupby("departement").count()

    indicator = indicator.reset_index().rename(columns={"id_pdc_itinerance": "nombre_pdc"})
    indicator["uuid"] = indicator.apply(lambda _: uuid.uuid4(), axis=1)
    
    # test (à supprimer)
    print(indicator)
    return indicator

# autres calculs d'indicateurs à ajouter
'''
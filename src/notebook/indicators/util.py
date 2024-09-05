"""
The `util` module includes functions and classes used for QualiCharge indicators.
"""
import pandas as pd
import create_query

def indic_pandas(engine, indic):
    """create DataFrame for an indicator"""

    query = getattr(create_query, 'query_' + indic.split('-')[0])(*indic.split('-')[1:])
    with engine.connect() as conn:
        data_pd = pd.read_sql_query(query, conn)
    return data_pd

def indic_to_table(indic_pd, table_name, engine, option="replace"):
    """ Save the indicator to a table"""
    indic_pd.to_sql(table_name, engine, if_exists=option, index=False)
    return pd.read_sql_query('SELECT COUNT(*) AS count FROM ' + table_name, engine)

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

'''

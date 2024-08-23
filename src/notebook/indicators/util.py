"""
The `util` module includes functions and classes used for QualiCharge indicators.
"""
import pandas as pd
import create_query

def to_indicator(engine, indicator, simple=False, format='pandas', table_name=None, table_option="replace"):
    """create data for an indicator
    
    Parameters
    ----------
    engine: sqlalchemy object
        Connector to postgreSQL database
    indicator: str 
        Indicator name (see indicator codification)
    simple: boolean, default False
        If False, additional columns are added in the result Table
    format: enum ('pandas', 'json', 'table'), default 'pandas'
        Define the return format:
        - 'pandas'-> Dataframe
        - 'json'-> json string
        - 'table' -> Dataframe (table creation confirmation with the number of lines created)
    table_name: string (used if format='table'), default None
        Name of the table to create (format='table'). If None the name is the indicator name.
    table_option: string (used if format='table'), default 'replace'
        Option if table exists ('replace' or 'append')

    Returns
    -------
    String or Dataframe
        see 'format' parameter
    """
    indic = indicator + '-00'
    query = getattr(create_query, 'query_' + indic.split('-')[0])(*indic.split('-')[1:], simple=simple)
    with engine.connect() as conn:
        data_pd = pd.read_sql_query(query, conn)
    if format == 'pandas':
        return data_pd
    if format == 'json':
        return '{"' + indicator + '": ' + data_pd.to_json(index=False, orient='split') + "}"
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
    return pd.read_sql_query('SELECT COUNT(*) AS count FROM ' + table_name, engine)
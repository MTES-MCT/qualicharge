# -*- coding: utf-8 -*-
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
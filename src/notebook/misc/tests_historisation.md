---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.16.2
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

<!-- #region editable=true slideshow={"slide_type": ""} -->
# Tests historisation

<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
import os
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, types
from create_query import to_indicator

engine = create_engine(os.getenv("DATABASE_URL"))
```

## Tests Solution 1

```python
# fonction qui retourne l'indicateur sous différents formats (par défaut un DataFrame) à partir de la requête définie
to_indicator(engine, 't1-02-75')
```

```python
# ajout d'indicateurs dans la table 'quotidien'
# on simule l'envoi quotidien des indicateurs (en répétant le même indicateur)
to_indicator(engine, 'i1',          histo=True, format='table', table_name='quotidien', table_option='replace')
to_indicator(engine, 'i1-01-93-02', histo=True, format='table', table_name='quotidien', table_option='append')
to_indicator(engine, 't1-02-75',    histo=True, format='table', table_name='quotidien', table_option='append')
to_indicator(engine, 't3-04-13001', histo=True, format='table', table_name='quotidien', table_option='append')
to_indicator(engine, 'i1',          histo=True, format='table', table_name='quotidien', table_option='append')
to_indicator(engine, 't1-02-75',    histo=True, format='table', table_name='quotidien', table_option='append')
to_indicator(engine, 't3-04-13001', histo=True, format='table', table_name='quotidien', table_option='append')
to_indicator(engine, 't1-02-75',    histo=True, format='table', table_name='quotidien', table_option='append')
```

```python
# tous les indicateurs ont le même format
with engine.connect() as conn:
    quotidien = pd.read_sql_table('quotidien', conn)
quotidien
```

```python
# passage de la table 'quotidien' à la table 'mensuel' (chaque mois on retrouve un seul enregistrement de chaque indicateur)
# le traitement pourrait se faire directement en SQL sans passer par un DataFrame
# la requête est la même pour passer de jour à mois que pour passer de mois à année

query = """
SELECT
  SUM(nombre) AS nombre,  SUM(somme) AS somme,  crit_v,  query,  level,  val,  area
FROM
  quotidien
WHERE
  (timest >= CAST(NOW() AS date))   AND   (timest < CAST((NOW() + INTERVAL '1 month') AS date))
GROUP BY
  crit_v,  query,  level,  val,  area
ORDER BY
  query,  level,  val,  area
"""

with engine.connect() as conn:
    mensuel = pd.read_sql_query(query, conn)

mensuel.to_sql('mensuel', engine, if_exists='replace', index=False)

mensuel
```

```python
# indicateur 't1-m-02-75' sur le mois
# la requête est générique (en séparant les cas ou c'est la moyenne de ceux ou c'est la somme)

query = """
SELECT
  somme / nombre AS nb_pdc,  crit_v AS p_range
FROM
  mensuel
WHERE
  query = 't1' AND level = '02' AND val = '75'
"""
with engine.connect() as conn:
    t1_m_02_75 = pd.read_sql_query(query, conn)

# on retrouve l'indicateur du jour
t1_m_02_75
```

## Tests solution 2

```python
import json
```

```python
val_t8_01_93_02 = [
    {
        "department": "01",
        "operators": [
            {
                "name": "Bouygues",
                "sum": 42,
                "delta": 3
            },
            {
                "name": "Electra",
                "sum": 12,
                "delta": -2
            },
            {
                "name": "Engie",
                "sum": 252,
                "delta": 154
            }
        ]
    },
    {
        "department": "02",
        "operators": [
            {
                "name": "Bouygues",
                "sum": 4,
                "delta": 3
            },
            {
                "name": "Electra",
                "sum": 52,
                "delta": 23
            },
            {
                "name": "Engie",
                "sum": 1,
                "delta": 1
            }
        ]
    }
]
```

```python
t8_01_93_02 = pd.DataFrame({'code': ['t8']*3, 'level': [1]*3, 'target': [93]*3, 'sub_level': [2]*3, 
                            'value': [val_t8_01_93_02]*3, 
                            'timestamp': ['2024-09-09T15:05:28+00:00', '2024-09-10T15:05:28+00:00', 
                                          '2024-09-11T15:05:28+00:00']})
t8_01_93_02
```

```python
dtype={'code': types.TEXT, 'level': types.SMALLINT, 'target': types.TEXT, 'sub_level': types.SMALLINT, 
       'value': types.JSON, 'timestamp': types.TIMESTAMP}
t8_01_93_02.to_sql("mensuel_3", engine, if_exists="replace", dtype=dtype)
```

```python
query = """
with dpt_ext as
    (select 
        target, level, code, sub_level, 
        jsonb_path_query(to_jsonb(value), '$.department') as department, 
        jsonb_path_query(to_jsonb(value), ' $.operators') as oper_json, 
        timestamp
    from 
        mensuel_3)
select 
    target, level, code, sub_level, department, 
    jsonb_path_query(to_jsonb(oper_json), ' $.name') as operator, 
    jsonb_path_query(to_jsonb(oper_json), ' $.sum') as sum, 
    jsonb_path_query(to_jsonb(oper_json), ' $.delta') as delta, 
    timestamp
from 
    dpt_ext
"""
with engine.connect() as conn:
    test_json = pd.read_sql_query(query, conn)
test_json
```

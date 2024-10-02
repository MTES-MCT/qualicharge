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
# Tests fonctionnels historisation

<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
import os
from datetime import datetime, timedelta
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, types, dialects
from create_query import to_indicator

engine = create_engine(os.getenv("DATABASE_URL"))
```

```python
dd = timedelta(days=1)
ti = datetime.fromisoformat('2024-01-01')
duree = 5 # 365
test = 't8---01'
#test = 't8---02'
#test = 't8---03'
#test = 't8---04'
```

```python
dtype_0 = {'value': types.FLOAT, 'category': types.TEXT, 'code_z': types.TEXT, 'query': types.TEXT, 'perim': types.TEXT, 'code_p': types.TEXT, 'zoning': types.TEXT, 
        'timestamp': types.TIMESTAMP, 'period': types.TEXT, 'add_value': dialects.postgresql.JSONB}
```

```python
# simulation de l'historisation quotidienne de l'indicateur 'test' sur un an
ti = datetime.fromisoformat('2024-01-01')
period = 'd'
print(to_indicator(engine, test, histo=True, format='table', histo_period=period, histo_timest= ti.isoformat(), table_name='quotidien_0', table_option='replace', table_dtype=dtype_0))
for i in range(duree):
    ti += dd
    to_indicator(engine, test, histo=True, format='table', histo_period=period, histo_timest= ti.isoformat(), table_name='quotidien_0', table_option='append', table_dtype=dtype_0)

```

```python
with engine.connect() as conn:
    quotidien_0 = pd.read_sql_query("SELECT * FROM quotidien_0", conn)
quotidien_0
```

```python
# passage de la table 'quotidien' à la table 'mensuel' (chaque mois on retrouve un seul enregistrement de chaque indicateur)
# le traitement nécessite de reconstruire le JSON pour l'ensemble des lignes d'un même indicateur (à faire sous pandas ?)
# le traitement est le même pour passer de jour à mois que pour passer de mois à année

# requête pour générer un tableau "à plat" :
query = """
SELECT
  *
FROM
  quotidien_0
WHERE
  period ='d' AND
  timestamp >= to_timestamp('2024-01-01', 'YYYY-MM-DD')   AND
  timestamp < to_timestamp('2025-01-01', 'YYYY-MM-DD')
"""

with engine.connect() as conn:
    mensuel = pd.read_sql_query(query, conn)
mensuel
```

```python
df = pd.DataFrame({'a':[1,2,3], 'b':[4,5,6], 'c':[{'d':1, 'e':7}, {'d':2, 'e':8}, {'d':3, 'e':9}]})
mean = (df['a'] * df['b']).sum() / df['b'].sum()
mean
df['c']
```

```python
histo = mensuel.sort_values(by='timestamp', ascending=False).set_index(['code', 'level', 'target', 'category'])
for idx in histo.index.unique()[0:1]:
    print(idx)
    data_n = histo.loc[idx]
    quantity = data_n[
    last = data_n['value'][0]
    value = 
    #print(histo.loc[idx])
    print(data_n['value'][0])
    print(data_n)
```

```python
#%%timeit
with engine.connect() as conn:
    mensuel = pd.read_sql_query(query, conn)
```

```python
mensuel.to_sql('mensuel_0', engine, if_exists='replace', index=False)
```

### Tests perf sol 1

```python
# simulation de l'historisation quotidienne de l'indicateur 'test' sur un an
to_indicator(engine, test, histo=True, format='table', histo_timest= ti.isoformat(), table_name='quotidien_1', table_option='replace', test='1')
for i in range(duree):
    ti += dd
    to_indicator(engine, test, histo=True, format='table', histo_timest= ti.isoformat(), table_name='quotidien_1', table_option='append', test='1')
```

```python
with engine.connect() as conn:
    quotidien_1 = pd.read_sql_query("SELECT * FROM quotidien_1", conn)
quotidien_1
```

```python
# passage de la table 'quotidien' à la table 'mensuel' (chaque mois on retrouve un seul enregistrement de chaque indicateur)
# une requête unique donne à la fois le format d'historisation et le format de l'indicateur
# la requête est la même pour passer de jour à mois que pour passer de mois à année

query = """
SELECT
  SUM(quantity) AS quantity,  SUM(quantity * value)/SUM(quantity) AS value,  last, category,  target, code,  perim,  val,  level
FROM
  quotidien_1
WHERE
  (timest >= to_timestamp('2024-01-01', 'YYYY-MM-DD')   AND   timest < to_timestamp('2025-01-01', 'YYYY-MM-DD'))
GROUP BY
  last, category,  target, code,  perim,  val,  level
ORDER BY
  code,  perim,  val,  level
"""

with engine.connect() as conn:
    mensuel = pd.read_sql_query(query, conn)
mensuel
```

```python
#%%timeit
with engine.connect() as conn:
    mensuel = pd.read_sql_query(query, conn)
```

```python
mensuel.to_sql('mensuel_1', engine, if_exists='replace', index=False)
```

### tests perf sol 1 bis

```python
dtype_1_bis = {'category': types.TEXT, 'target': types.TEXT, 'code': types.TEXT, 'perim': types.TEXT, 'val': types.TEXT, 'level': types.TEXT, 
               'timestamp': types.TIMESTAMP, 'all_value': dialects.postgresql.JSONB}
```

```python
# simulation de l'historisation quotidienne de l'indicateur 'test' sur un an
ti = datetime.fromisoformat('2024-01-01')
to_indicator(engine, test, histo=True, format='table', histo_timest= ti.isoformat(), table_name='quotidien_1_bis', table_option='replace', table_dtype=dtype_1_bis, test='1bis')
for i in range(duree):
    ti += dd
    to_indicator(engine, test, histo=True, format='table', histo_timest= ti.isoformat(), table_name='quotidien_1_bis', table_option='append', table_dtype=dtype_1_bis, test='1bis')
```

```python
with engine.connect() as conn:
    quotidien_1_bis = pd.read_sql_query("SELECT * FROM quotidien_1_bis", conn)
quotidien_1_bis
```

```python
# passage de la table 'quotidien' à la table 'mensuel' (chaque mois on retrouve un seul enregistrement de chaque indicateur)
# le traitement nécessite de reconstruire le JSON pour l'ensemble des lignes d'un même indicateur (à faire sous pandas ?)
# le traitement est le même pour passer de jour à mois que pour passer de mois à année

# requête pour générer un tableau "à plat" :
query = """
SELECT
  SUM((all_value->>'quantity')::float) AS quantity,  
  SUM((all_value->>'quantity')::float * (all_value->>'value')::float) / SUM((all_value->>'quantity')::float) AS value,  
  (all_value->>'last')::float AS last, 
  category, target, code, perim, val, level
FROM
  quotidien_1_bis
WHERE
  (timest >= to_timestamp('2024-01-01', 'YYYY-MM-DD')   AND   timest < to_timestamp('2025-01-01', 'YYYY-MM-DD'))
GROUP BY
  last, category, target, code, perim, val, level
ORDER BY
  value, code, perim, val, level
"""

with engine.connect() as conn:
    mensuel = pd.read_sql_query(query, conn)
mensuel
```

```python
#%%timeit
with engine.connect() as conn:
    mensuel = pd.read_sql_query(query, conn)
```

```python
mensuel.to_sql('mensuel_1_bis', engine, if_exists='replace', index=False)
```

### Tests perf sol 2 

```python
with engine.connect() as conn:
    quotidien_1_bis = pd.read_sql_query("SELECT * FROM quotidien_1_bis", conn)
```

```python
quotidien_2 = quotidien_1_bis[['code', 'perim', 'val', 'level', 'timest']].drop_duplicates().reset_index(drop=True)
quotidien_2['timest'] = quotidien_2['timest'].astype('string')
```

```python
# génération du json
def value_2(row, df):
    param = row.to_dict()
    query = f"code == '{param['code']}' and perim == '{param['perim']}' and val == '{param['val']}' and level == '{param['level']}' and timest == '{param['timest']}'"
    return df.query(query)[['target', 'category', 'all_value']].to_dict(orient='records')    
```

```python
quotidien_1_bis['timest'] = quotidien_1_bis['timest'].astype('string')
quotidien_2['result'] = pd.Series([value_2(row, quotidien_1_bis) for row_idx, row in quotidien_2.iterrows()])
quotidien_2
```

```python
quotidien_2['result'][0][:5]
```

```python
dtype_2 = {'result': dialects.postgresql.JSONB, 'code': types.TEXT, 'perim': types.TEXT, 'val': types.TEXT, 'level': types.TEXT, 'timestamp': types.TIMESTAMP}
quotidien_2.to_sql("quotidien_2", engine, if_exists="replace", dtype=dtype_2)
```

```python
# passage de la table 'quotidien' à la table 'mensuel' (chaque mois on retrouve un seul enregistrement de chaque indicateur)
# le traitement nécessite de reconstruire le JSON pour l'ensemble des lignes d'un même indicateur (à faire sous pandas ?)
# le traitement est le même pour passer de jour à mois que pour passer de mois à année

# requête pour générer un tableau "à plat" :
query = """
WITH quotidien_flat AS
    (SELECT 
        code, perim, val, level, 
        jsonb_path_query(result, '$.target') AS target, 
        jsonb_path_query(result, '$.category') AS category, 
        jsonb_path_query(result, '$.all_value') AS all_value, 
        timest
    FROM 
        quotidien_2)
SELECT
  SUM((all_value->>'quantity')::float) AS quantity,  
  SUM((all_value->>'quantity')::float * (all_value->>'value')::float) / SUM((all_value->>'quantity')::float) AS value,  
  (all_value->>'last')::float AS last, 
  category, target, code, perim, val, level
FROM
  quotidien_flat
WHERE
  (timest::TIMESTAMP >= to_timestamp('2024-01-01', 'YYYY-MM-DD')   AND   timest::TIMESTAMP < to_timestamp('2025-01-01', 'YYYY-MM-DD'))
GROUP BY
  last, category, target, code, perim, val, level
ORDER BY
  value, code, perim, val, level
"""
with engine.connect() as conn:
    mensuel = pd.read_sql_query(query, conn)
mensuel
```

```python
#%%timeit
with engine.connect() as conn:
    mensuel = pd.read_sql_query(query, conn)
```

```python
mensuel.to_sql('mensuel_2', engine, if_exists='replace', index=False)
```

<!-- #region jp-MarkdownHeadingCollapsed=true -->
## Résultats des tests 

Comparaison des temps de réponse d'une query pour les trois solutions avec le scénario suivant :

- requête t8 de calcul des résultats annuels à partir des résultats des requêtes quotidiennes stockées sur un an dans une table.
- avec t8 : nb station par opérateur et par région-01/département-02/EPCI-03/communes-04

| requete | s0 durée | s1 durée | s1bis durée | s0-1 rows | s2 durée | s2 rows |s2/s1bis|
| ------- | -------- | -------- | ----------- | --------- | -------- | ------- | ------ |
| t8---01 | 212      | 161      | 208         | 121146    | 434      | 366     |  1.8   |
| t8---02 | 422      | 187      | 438         | 389058    | 1420     | 366     |  3.2   |
| t8---03 | 676      | 320      | 777         | 822036    | 3180     | 366     |  4.5   |
| t8---04 |          | 861      | 1240        | 1445334   | 5980     | 366     |  4.8   |

NOTA : 

- pour les solutions 1bis et 2 la requête n'est pas suffisante pour générer le format d'historisation
  - pour la solution 1 bis : génération du json des valeurs,
  - pour la solution 2 : regroupement des lignes de chaque indicateur et génération du json complet des résultats)
<!-- #endregion -->

# Annexe : autres tests


## Tests sol 1 autres

```python
# ajout d'indicateurs dans la table 'quotidien'
# on simule l'envoi quotidien des indicateurs (en répétant le même indicateur)
to_indicator(engine, 'i1',          histo=True, format='table', table_name='quotidien_1', table_option='replace', test='1')
to_indicator(engine, 'i1-01-93-02', histo=True, format='table', table_name='quotidien_1', table_option='append', test='1')
to_indicator(engine, 't1-02-75',    histo=True, format='table', table_name='quotidien_1', table_option='append', test='1')
to_indicator(engine, 't3-04-13001', histo=True, format='table', table_name='quotidien_1', table_option='append', test='1')
to_indicator(engine, 'i1',          histo=True, format='table', table_name='quotidien_1', table_option='append', test='1')
to_indicator(engine, 't1-02-75',    histo=True, format='table', table_name='quotidien_1', table_option='append', test='1')
to_indicator(engine, 't3-04-13001', histo=True, format='table', table_name='quotidien_1', table_option='append', test='1')
to_indicator(engine, 't1-02-75',    histo=True, format='table', table_name='quotidien_1', table_option='append', test='1')
```

```python
# tous les indicateurs ont le même format
with engine.connect() as conn:
    quotidien_1 = pd.read_sql_table('quotidien_1', conn)
quotidien_1
```

```python
# passage de la table 'quotidien' à la table 'mensuel' (chaque mois on retrouve un seul enregistrement de chaque indicateur)
# le traitement pourrait se faire directement en SQL sans passer par un DataFrame
# la requête est la même pour passer de jour à mois que pour passer de mois à année

query = """
SELECT
  SUM(quantity) AS quantity,  SUM(quantity * value) / SUM(quantity) AS value, last, category, target, code, perim, val, level
FROM
  quotidien_1
WHERE
  (timest >= CAST(NOW() AS date))   AND   (timest < CAST((NOW() + INTERVAL '1 month') AS date))
GROUP BY
  last, category, target, code, perim, val, level
ORDER BY
  code, perim, val, level
"""

with engine.connect() as conn:
    mensuel = pd.read_sql_query(query, conn)
mensuel
```

```python
mensuel.to_sql('mensuel_1', engine, if_exists='replace', index=False)
```

```python
# indicateur 't1-m-02-75' sur le mois
# la requête est générique (en séparant les cas ou c'est la moyenne de ceux ou c'est la somme)

query = """
SELECT
  value::int AS nb_pdc,  category AS p_range
FROM
  mensuel_1
WHERE
  code = 't1' AND perim = '02' AND val = '75'
"""
with engine.connect() as conn:
    t1_m_02_75 = pd.read_sql_query(query, conn)

# on retrouve l'indicateur du jour
t1_m_02_75
```

```python
to_indicator(engine, 't1-02-75')
```

## Tests solution 2 bis

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
       'value': dialects.postgresql.JSONB, 'timestamp': types.TIMESTAMP}
t8_01_93_02.to_sql("mensuel_3", engine, if_exists="replace", dtype=dtype)
```

```python
query = """
with dpt_ext as
    (select 
        target, level, code, sub_level, 
        jsonb_path_query(value, '$.department') as department, 
        jsonb_path_query(value, '$.operators') as oper_json, 
        timestamp
    from 
        mensuel_3)
select 
    target, level, code, sub_level, department, 
    jsonb_path_query(oper_json, '$.name') as operator, 
    jsonb_path_query(oper_json, '$.sum') as sum, 
    jsonb_path_query(oper_json, '$.delta') as delta, 
    timestamp
from 
    dpt_ext
"""
with engine.connect() as conn:
    test_json = pd.read_sql_query(query, conn)
test_json
```

```python
val_t8_01_93_02 = [
    {   "code": "01",
        "crit_v": "Bouygues",
        "value": {
            'quantite': 5, 
            "moyenne": 10}},
    {   "department": "01",
        "operators": "Electra",
        "value": {
            'quantite': 15, 
            "moyenne": 20}},
    {   "department": "01",
        "operators": "Engie",
        "value": {
            'quantite': 25, 
            "moyenne": 30}},
    
    {   "department": "02",
        "operators": "Bouygues",
        "value": {
            'quantite': 5, 
            "moyenne": 10}},
    {   "department": "02",
        "operators": "Electra",
        "value": {
            'quantite': 15, 
            "moyenne": 20}},
    {   "department": "02",
        "operators": "Engie",
        "value": {
            'quantite': 25, 
            "moyenne": 30}}
]
```

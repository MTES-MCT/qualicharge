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
from datetime import datetime, timedelta
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, types, dialects
from create_query import to_indicator

engine = create_engine(os.getenv("DATABASE_URL"))
```

Plusieurs solutions sont testées (pour chaque niveau d'historisation):

- solution 1 : une table avec les résultats des indicateurs (plusieurs lignes par indicateur)
- solution 1bis : une table avec un champ JSON pour les valeurs (plusieurs lignes par indicateur)
- solution 2 : une table avec une valeur JSON par indicateur (une ligne par indicateur)


## Principes indicateurs

- résultat instantané : valeur unique (ex. puissance, nombre de stations...)
- résultat sur une période : ensemble de valeurs (ex. puissance quotidienne...)

### Historisation : Pour ne pas stocker un ensemble des valeurs on stocke des données agrégées 'scalables'

- quantité de valeurs (nécessaire pour les calculs)
- valeur moyenne
- dernière valeur de la période (optionnel ou obligatoire ?)
- écart-type (optionnel)
- valeur mini (optionnel)
- valeur maxi (optionnel)

ex. 'dernière valeur' utile quand on veut comparer une évolution entre deux dates (ex entre fin 2023 et fin 2024) ou avoir une courbe des valeurs mensuelles

### Types d'indicateur

- valeur unique (tableau avec une colonne et une valeur)
- avec un paramètre -> liste de valeurs (tableau avec deux colonnes et n valeurs)
- avec deux paramètres -> liste de valeurs (tableau avec trois colonnes et n x n valeurs)



## Tests perf Solution 1

```python
dd = timedelta(days=1)
```

```python
# %%timeit
# fonction qui retourne l'indicateur sous différents formats (par défaut un DataFrame) à partir de la requête définie
to_indicator(engine, 't8---02', histo=True, format='table', histo_timest= '2024-01-01')
```

```python
ti = datetime.fromisoformat('2024-01-01')
```

```python
%%timeit
to_indicator(engine, 't8---02', histo=True, format='table', histo_timest= ti.isoformat(), table_name='quotidien_1', table_option='replace')
```

```python
ti = datetime.fromisoformat('2024-01-01')
to_indicator(engine, 't8---02', histo=True, format='table', histo_timest= ti.isoformat(), table_name='quotidien_1', table_option='replace')
for i in range(365):
    ti += dd
    to_indicator(engine, 't8---02', histo=True, format='table', histo_timest= ti.isoformat(), table_name='quotidien_1', table_option='append')
```

```python
%%timeit
# passage de la table 'quotidien' à la table 'mensuel' (chaque mois on retrouve un seul enregistrement de chaque indicateur)
# le traitement pourrait se faire directement en SQL sans passer par un DataFrame
# la requête est la même pour passer de jour à mois que pour passer de mois à année

query = """
SELECT
  SUM(quantity) AS quantity,  SUM(quantity * mean) AS somme,  last, crit_v,  code, query,  level,  val,  area
FROM
  quotidien_1
WHERE
  (timest >= to_timestamp('2024-01-01', 'YYYY-MM-DD')   AND   timest < to_timestamp('2025-01-01', 'YYYY-MM-DD'))
GROUP BY
  last, crit_v,  code, query,  level,  val,  area
ORDER BY
  query,  level,  val,  area
"""

with engine.connect() as conn:
    mensuel = pd.read_sql_query(query, conn)
mensuel
```

## tests perf sol 1 bis

```python
# fonction qui retourne l'indicateur sous différents formats (par défaut un DataFrame) à partir de la requête définie
to_indicator(engine, 't8---02', histo=True, format='table', histo_timest= '2024-01-01', test='1bis')
```

```python
ti = datetime.fromisoformat('2024-01-01')
dtype_1_bis = {'crit_v': types.TEXT, 'code': types.TEXT, 'query': types.TEXT, 'level': types.TEXT, 'val': types.TEXT, 'area': types.TEXT, 
        'timestamp': types.TIMESTAMP, 'value': dialects.postgresql.JSONB}
```

```python
%%timeit
to_indicator(engine, 't8---02', histo=True, format='table', histo_timest= ti.isoformat(), table_name='quotidien_1_bis', table_option='replace', table_dtype=dtype_1_bis, test='1bis')
```

```python
ti = datetime.fromisoformat('2024-01-01')
to_indicator(engine, 't8---02', histo=True, format='table', histo_timest= ti.isoformat(), table_name='quotidien_1_bis', table_option='replace', table_dtype=dtype_1_bis, test='1bis')
for i in range(365):
    ti += dd
    to_indicator(engine, 't8---02', histo=True, format='table', histo_timest= ti.isoformat(), table_name='quotidien_1_bis', table_option='append', table_dtype=dtype_1_bis, test='1bis')
```

```python
%%timeit
# passage de la table 'quotidien' à la table 'mensuel' (chaque mois on retrouve un seul enregistrement de chaque indicateur)
# le traitement pourrait se faire directement en SQL sans passer par un DataFrame
# la requête est la même pour passer de jour à mois que pour passer de mois à année

query = """
SELECT
  SUM((value->>'quantity')::float) AS quantity,  SUM((value->>'quantity')::float * (value->>'mean')::float) AS somme,  (value->>'last')::float AS last, crit_v,  code, query,  level,  val,  area
FROM
  quotidien_1_bis
WHERE
  (timest >= to_timestamp('2024-01-01', 'YYYY-MM-DD')   AND   timest < to_timestamp('2025-01-01', 'YYYY-MM-DD'))
GROUP BY
  last, crit_v,  code, query,  level,  val,  area
ORDER BY
  query,  level,  val,  area
"""

with engine.connect() as conn:
    mensuel = pd.read_sql_query(query, conn)
mensuel
```

## tests perf sol 2 

```python

```

## tests sol 1 autres

```python
# ajout d'indicateurs dans la table 'quotidien'
# on simule l'envoi quotidien des indicateurs (en répétant le même indicateur)
to_indicator(engine, 'i1',          histo=True, format='table', table_name='quotidien_1', table_option='replace')
to_indicator(engine, 'i1-01-93-02', histo=True, format='table', table_name='quotidien_1', table_option='append')
to_indicator(engine, 't1-02-75',    histo=True, format='table', table_name='quotidien_1', table_option='append')
to_indicator(engine, 't3-04-13001', histo=True, format='table', table_name='quotidien_1', table_option='append')
to_indicator(engine, 'i1',          histo=True, format='table', table_name='quotidien_1', table_option='append')
to_indicator(engine, 't1-02-75',    histo=True, format='table', table_name='quotidien_1', table_option='append')
to_indicator(engine, 't3-04-13001', histo=True, format='table', table_name='quotidien_1', table_option='append')
to_indicator(engine, 't1-02-75',    histo=True, format='table', table_name='quotidien_1', table_option='append')
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
  SUM(nombre) AS nombre,  SUM(somme) AS somme,  crit_v,  code, query,  level,  val,  area
FROM
  quotidien_1
WHERE
  (timest >= CAST(NOW() AS date))   AND   (timest < CAST((NOW() + INTERVAL '1 month') AS date))
GROUP BY
  crit_v,  code, query,  level,  val,  area
ORDER BY
  query,  level,  val,  area
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
  (somme / nombre)::int AS nb_pdc,  crit_v AS p_range
FROM
  mensuel_1
WHERE
  query = 't1' AND level = '02' AND val = '75'
"""
with engine.connect() as conn:
    t1_m_02_75 = pd.read_sql_query(query, conn)

# on retrouve l'indicateur du jour
t1_m_02_75
```

## Tests solution 1 bis

```python
val_t8_01_93_02 = [{'quantite': 30, 'moyenne': 50}, {'quantite': 20, 'moyenne': 60}]
                   
quotidien_1_bis = pd.DataFrame({'value': val_t8_01_93_02*3, 'crit_v': ['']*6, 'code': ['01', '02']*3, 'query': ['t8']*6, 'level': [1]*6, 'val': [93]*6, 'area': [2]*6, 
                            'timestamp': ['2024-09-09T15:05:28+00:00', '2024-09-09T15:05:28+00:00', '2024-09-10T15:05:28+00:00', 
                                          '2024-09-10T15:05:28+00:00', '2024-09-11T15:05:28+00:00', '2024-09-11T15:05:28+00:00']})
quotidien_1_bis
```

```python
dtype_1_bis = {'value': dialects.postgresql.JSONB, 'crit_v': types.TEXT, 'code': types.TEXT, 'query': types.TEXT, 'level': types.SMALLINT, 'val': types.TEXT, 'area': types.SMALLINT, 
        'timestamp': types.TIMESTAMP}
quotidien_1_bis.to_sql("quotidien_1_bis", engine, if_exists="replace", dtype=dtype_1_bis)
```

```python
# passage de la table 'quotidien' à la table 'mensuel'

query = """
SELECT
  SUM((value->>'quantite')::float) AS quantite,  
  SUM(((value->>'moyenne')::float) * (value->>'quantite')::float) / SUM((value->>'quantite')::float) AS moyenne,  
  crit_v,  code, query,  level,  val,  area
FROM
  quotidien_1_bis
GROUP BY
  crit_v,  code, query,  level,  val,  area
ORDER BY
  query,  level,  val,  area
"""

with engine.connect() as conn:
    mensuel = pd.read_sql_query(query, conn)

mensuel.to_sql('mensuel_1_bis', engine, if_exists='replace', index=False)

mensuel
```

```python
mensuel['value'] = pd.Series([{'quantite': quantite, 'moyenne': moyenne} for quantite, moyenne in zip(mensuel['quantite'], mensuel['moyenne'])])
mensuel_1_bis = mensuel.loc[:, ['value', 'crit_v', 'code', 'query', 'level',  'val',  'area']]
mensuel_1_bis
```

```python
mensuel_1_bis.to_sql('mensuel_1_bis', engine, if_exists='replace', index=False, dtype=dtype_1_bis)
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
    {   "department": "01",
        "operators": "Bouygues",
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

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

```python
import os
import sys
print(sys.path)
print(sys.executable)
# os.environ['PYTHONPATH']
```

```python
#sys.path.append('/home/phtquali/github/qualicharge/src') 
sys.path
```

```python
sys.path.append('/home/phtquali/github/qualicharge/src/prefect') 
```

```python
from models import Level
```

```python editable=true slideshow={"slide_type": ""}
import os
from datetime import datetime, timedelta
import json
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, types, dialects
from create_query import to_indicator
from string import Template

engine = create_engine(os.getenv("DATABASE_URL"))
```

## traitement pandas

```python
def to_histo_plus(indic, timest, period):

    index = ['code', 'level', 'target', 'category']
    histo = ['period', 'timestamp']
    value = ['value']
    add_value = ['quantity', 'mini', 'maxi', 'last', 'variance']
    fixe = index + value + add_value + histo
    
    # normalize the DataFrame
    df = indic.sort_values(by='timestamp').reset_index(drop=True)
    if 'add_value' in df.columns:
        df = pd.concat([df, pd.json_normalize(df['add_value'])], axis=1)
        del df['add_value']
    if 'quantity' not in df.columns:
        df['quantity'] = 1        
    if (df['quantity'] == 1).all():
        df['mini'] = df['value']
        df['maxi'] = df['value']
        df['last'] = df['value']
        df['variance'] = 0.0

    # decode specific additional values
    add_col = list(set(df.columns) - set(fixe))
    add_col_sum = [col for col in add_col if col[:4] == 'sum_']
    add_col_min = [col for col in add_col if col[:4] == 'min_']
    add_col_max = [col for col in add_col if col[:4] == 'max_']
    add_col_mean = [col for col in add_col if col[:5] == 'mean_']
    add_col_last = list(set(add_col) - set(add_col_sum + add_col_min + add_col_max + add_col_mean))

    # group the DataFrame
    for col in add_col_mean + ['value']:
        df[col + '_qua'] = df[col] * df['quantity']
    grp = df.groupby(index, sort=False)
    col_mean = [col + '_qua' for col in add_col_sum + add_col_mean + value]
    grp_sum = grp[col_mean + ['quantity']].sum()
    df_n1 = grp_sum[['quantity']].copy()
    for col in add_col_mean + ['value']:
        df_n1[col] = grp_sum[col + '_qua'] / df_n1['quantity']
    grp_max = grp[add_col_max + ['maxi']].max()
    for col in add_col_max + ['maxi']:
        df_n1[col] = grp_max[col]   
    grp_min = grp[add_col_min + ['mini']].min()
    for col in add_col_min + ['mini']:
        df_n1[col] = grp_min[col]   
    grp_last = grp[add_col_last + ['last']].last()
    for col in add_col_last + ['last']:
        df_n1[col] = grp_last[col]   
    df_n1['variance'] = 0.0
    pass # variance calculation to add

    # add the historization format
    df_n1['add_value'] = df_n1[add_value].to_dict(orient='records')    
    df_n1['timestamp'] = timest
    df_n1['period'] = period
    return df_n1.reset_index()[index + value + ['add_value'] + histo + add_col]
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
# simulation de l'historisation quotidienne de l'indicateur 'test'
ti = datetime.fromisoformat('2024-01-01')
period = 'd'
test = 'i1---01'
histo = to_indicator(engine, test, histo=True, format='table', histo_period=period, histo_timest= ti.isoformat())
for i in range(duree - 1):
    ti += dd
    indic = to_indicator(engine, test, histo=True, format='table', histo_period=period, histo_timest= ti.isoformat())
    indic['value'] += i
    histo = pd.concat([histo, indic], ignore_index=True)
histo
```

## tests traitement pandas

```python
mensuel = to_histo_plus(histo, '2024-01-31', 'm')
assert(mensuel[mensuel['target']=='11']['value'][0] == histo[histo['target']=='11']['value'].mean())
assert(mensuel[mensuel['target']=='01']['add_value'].iloc[0]['last'] == mensuel[mensuel['target']=='01']['add_value'].iloc[0]['maxi'])
assert(len(mensuel) == len(histo) / duree)
```

```python
mensuel_bis = to_histo_plus(mensuel, '2024-01-31', 'm')
mensuel_bis
assert(mensuel.equals(mensuel_bis))
```

```python
histo_t = histo.copy()
del histo_t['add_value']
mensuel_bis = to_histo_plus(histo_t, '2024-01-31', 'm')
assert(mensuel.equals(mensuel_bis))
```

```python
histo_t = histo.copy()
histo_t['add_value'] = [None] * len(histo_t)
mensuel = to_histo_plus(histo_t, '2024-01-31', 'm')
assert(mensuel[mensuel['target']=='11']['add_value'][0]['quantity'] == duree)
```

## traitement global

```python
# passage de la table 'quotidien' à la table 'mensuel' (chaque mois on retrouve un seul enregistrement de chaque indicateur)
# le traitement nécessite de reconstruire le JSON pour l'ensemble des lignes d'un même indicateur (à faire sous pandas ?)
# le traitement est le même pour passer de jour à mois que pour passer de mois à année

# requête pour générer un tableau "à plat" :
from datetime import datetime
from . import to_indicator
from indicators.models import IndicatorPeriod

HOUR = "h"
DAY = "d"
WEEK = "w"
MONTH = "m"
QUARTER = "q"
YEAR = "y"

def histo_plus(init_period, timest_histo, final_period, table='histo'):
    delta = {DAY: timedelta(days=1), WEEK: timedelta(days=7), MONTH: timedelta(month=1), QUARTER: timedelta(month=3), YEAR: timedelta(year=1)}
    param = {'histo_table': table, 'period': init_period, 'start': timest_histo, 'end': date_histo.fromtimestamp(timest_histo)}
    query = Template("""
    SELECT
      *
    FROM
      $histo_table
    WHERE
      period = $period AND
      timestamp >= $start   AND
      timestamp < $end
    """)

print(query.substitude(param))
'''with engine.connect() as conn:
    quotidien = pd.read_sql_query(query, conn)
quotidien['add_value'] = quotidien['add_value'].fillna('empty')
quotidien = quotidien.dropna().reset_index(drop=True)
print(quotidien)'''
```

```python
quotidien.columns
```

```python
mensuel = to_histo_plus(quotidien, '2024-01-31', 'm')
mensuel
```

```python
import numpy as np
df = pd.DataFrame({'code':[1,1,2,2], 'level':[4,4,4,4], 'c':[{'quantity':1, 'e':7}, {'quantity':5}, {'quantity':2, 'e':8}, {'quantity':3, 'e':6, 'f':9}]})
#print(df['c'])
df['c'] = df['c'].fillna('vide')
#print(df['c'])
mean = (df['a'] * df['b']).sum() / df['b'].sum()
mean
norm = pd.concat([df[['a', 'b']], pd.json_normalize(df['c'])], axis=1)
norm['bd'] = norm['b'] * norm['d']
print(norm)
grp_sum = norm.groupby(['a']).sum()
grp_max = norm.groupby(['a']).max()
grp = pd.concat([grp_sum[['b', 'bd']], grp_max['e']], axis=1)
grp['b_mean'] = grp['bd'] / grp['b']
grp
```

```python
max(pd.isna(norm['d']))
```

```python
min(norm['d'])
```

```python
1 - df['a']
```

```python
df=pd.DataFrame({'a':[1,2,3]})
df['b'] = 2
if (df['b'] == 2).all():
    print('ok')
```

```python
df = pd.DataFrame.from_records([(3, 'a'), (2, 'b'), (1, 'c'), (0, 'd')], columns=['col_1', 'col_2'])
```

```python
histo = pd.concat([mensuel, pd.json_normalize(mensuel['add_value'])], axis=1)
histo = histo.set_index(['code', 'level', 'target', 'category']).sort_index()
for idx in histo.index.unique()[0:1]:
    print(idx)
    data_n = histo.loc[idx].reset_index().sort_values(by='timestamp', ascending=False)
    quantity = data_n['quantity'].sum()
    last = data_n['value'].iloc[0]
    value = (data_n['quantity'] * data_n['value']).sum() / quantity
    if 'variance' not in data_n.columns or max(pd.isna(data_n['variance'])):
        variance = None
    else:
        variance = (data_n['quantity'] * (data_n['variance'] + (value - data_n['value'])**2)).sum() / quantity
    if 'mini' not in data_n.columns or max(pd.isna(data_n['mini'])):
        mini = None
    else:
        mini = min(data_n['mini'])
    if 'maxi' not in data_n.columns or max(pd.isna(data_n['maxi'])):
        maxi = None
    else:
        maxi = min(data_n['mini'])        
    add_value = {'quantity': quantity, 'last': last, 'variance': variance, 'mini': mini, 'maxi': maxi}
    print(last, quantity, value, variance, mini, maxi)
    #print(data_n)
```

```python
#%%timeit
with engine.connect() as conn:
    mensuel = pd.read_sql_query(query, conn)
```

```python
mensuel.to_sql('mensuel_0', engine, if_exists='replace', index=False)
```

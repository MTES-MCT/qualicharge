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
from dateutil.relativedelta import relativedelta
import json
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, types, dialects
from create_query import to_indicator
from string import Template
from models import Level, IndicatorPeriod, Indicator

engine = create_engine(os.getenv("DATABASE_URL"))

#from indicators.models import IndicatorPeriod
HOUR = "h"
DAY = "d"
WEEK = "w"
MONTH = "m"
QUARTER = "q"
YEAR = "y"

day_delta = timedelta(days=1)
type_histo = {'value': types.FLOAT, 'category': types.TEXT, 'code': types.TEXT, 'level': types.TEXT, 'target': types.TEXT, 
              'period': types.TEXT, 'timestamp': types.TIMESTAMP, 'extras': dialects.postgresql.JSONB}
```

```python
indic = Indicator(code='er', level=0, period='h', value=3, timestamp=datetime.now())
print(list(indic))
```

## traitement pandas

```python
def to_df_histo_up(indic, timest, period):
    
    index = ['code', 'level', 'target', 'category']
    histo = ['period', 'timestamp']
    value = ['value']
    add_val = ['quantity', 'mini', 'maxi', 'last', 'variance']
    fixe = index + value + add_val + histo
    
    # normalize the DataFrame
    df = indic.sort_values(by='timestamp').reset_index(drop=True)
    df['category'] = df['category'].fillna(' ')
    df['value'] = df['value'].astype('float')
    if 'extras' in df.columns:
        df = pd.concat([df, pd.json_normalize(df['extras'])], axis=1)
        del df['extras']
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
    col_mean = [col + '_qua' for col in add_col_mean + value]
    grp_sum = grp[col_mean + add_col_sum + ['quantity']].sum()
    df_n1 = grp_sum[['quantity']].copy()
    for col in add_col_mean + ['value']:
        df_n1[col] = grp_sum[col + '_qua'] / df_n1['quantity']
    for col in add_col_sum:
        df_n1[col] = grp_sum[col]
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
    df_n1['extras'] = df_n1[add_val + add_col].to_dict(orient='records')    
    df_n1['timestamp'] = timest
    df_n1['period'] = period
    return df_n1.reset_index()[index + value + ['extras'] + histo]
```

## traitement global

```python
def histo_up(engine, init_period, time_histo, final_period, init_table='histo', final_table='histo', if_exists='append'):
    delta = {DAY: timedelta(days=1), WEEK: timedelta(days=7), MONTH: relativedelta(months=1), QUARTER: relativedelta(months=3), YEAR: relativedelta(year=1)}
    param = {'histo_table': init_table, 'period': init_period, 'start': time_histo, 'end': time_histo + delta[final_period]}
    query = Template("""
    SELECT
      *
    FROM
      $histo_table
    WHERE
      period = '$period' AND
      timestamp >= '$start'   AND
      timestamp < '$end'
    """)
    with engine.connect() as connection:
        histo_df = pd.read_sql_query(query.substitute(param), connection)
    histo_up_df = to_df_histo_up(histo_df, time_histo, final_period)
    histo_up_df.to_sql(final_table, engine, if_exists=if_exists, index=False, dtype=type_histo)
    return histo_up_df
```

## indicateurs temporels

```python
def temporal_indicator(code, period, perim, val, level, interval_start, interval_end, h_level=None, table='histo'): 
    
    # level and h-level validation
    with engine.connect() as connection:
        query = f"""
            SELECT DISTINCT level 
            FROM {table} 
            WHERE code = {code} AND level = {level} and period = {period}"""
        h_levels = pd.read_sql_query(query, connection)
    if not h_level:
        h_levels = [lvl for lvl in list(h_levels['level'].astype('int')) if lvl >= level]
        if not h_levels:
            raise NotImplementedError("Unavailable level %d", level)
        h_level = min(h_levels)
    if h_level not in h_levels:
        raise NotImplementedError("Level not compatible with h_level %d", h_level)

    pass
    return h_level

```

## tests indicateurs temporels

```python
temporal_indicator(code, period, perim, val, level, interval_start, interval_end, h_level=None, table='histo')
```

## tests traitement pandas

```python
date_init = datetime.fromisoformat('2024-01-01')
```

```python
size = 8
value = list(range(size))
target = [str(i).rjust(2, '0') for i in range(size)]
code = ['ixx']*size
level = ['01']*size
timestamp = [date_init]*size
period = ['d']*size
category = None
data = {'value': value, 'target': target, 'category': category, 'code': code, 'level': level, 'timestamp': timestamp, 'period': period}
```

### tests calcul des valeurs

```python
duree = 3
histo = pd.DataFrame(data)
data2 = data.copy()
date_init2 = date_init
for i in range(1, duree):
    date_init2 += day_delta
    data2 |= {'timestamp': [date_init2]*size, 'value': list(range(i, size+i))}
    histo = pd.concat([histo, pd.DataFrame(data2)], ignore_index=True)
```

```python
mensuel = to_df_histo_up(histo, '2024-01-01', 'm')
df = pd.concat([mensuel, pd.json_normalize(mensuel['extras'])], axis=1)
del df['extras']
assert(df['value'].equals(pd.Series(range(1, size+1), dtype='float')))
assert(df['mini'].equals(pd.Series(range(size), dtype='float')))
assert(df['maxi'].equals(pd.Series(range(2, size+2), dtype='float')))
assert(df['last'].equals(df['maxi']))
assert(df['quantity'].equals(pd.Series([3]*size)))
```

### tests extras

```python
duree = 3
data_add = data.copy()
data_add['extras'] = [{'liste': ['a', 'b', 'c'], 'sum_val': i, 'max_val': float(i),
                          'min_val': float(i), 'last_val': float(i)} for i in range(size)]
histo = pd.DataFrame(data_add)
data2 = data_add.copy()
date_init2 = date_init
for j in range(1, duree):
    date_init2 += day_delta
    data2 |= {'timestamp': [date_init2]*size, 'value': list(range(j, size+j))}
    data2 |= {'extras': [{'sum_val': i+j, 'max_val': float(i+j),
                          'min_val': float(i+j), 'last_val': float(i+j)} for i in range(size)]}
    histo = pd.concat([histo, pd.DataFrame(data2)], ignore_index=True)
```

```python
mensuel = to_df_histo_up(histo, '2024-01-01', 'm')
df = pd.concat([mensuel, pd.json_normalize(mensuel['extras'])], axis=1)
del df['extras']
assert(df['value'].equals(pd.Series(range(1, size+1), dtype='float')))
assert(df['mini'].equals(pd.Series(range(size), dtype='float')))
assert(df['maxi'].equals(pd.Series(range(2, size+2), dtype='float')))
assert(df['last'].equals(df['maxi']))
assert(df['quantity'].equals(pd.Series([3]*size)))
#print(df['sum_val'], pd.Series(range(0, size*duree, duree)))
assert(df['sum_val'].equals(pd.Series(range(3, (size+1)*duree, duree))))
assert(df['max_val'].equals(df['maxi']))
assert(df['min_val'].equals(df['mini']))
assert(df['last_val'].equals(df['last']))
```

### test indicateur

```python
# simulation de l'historisation quotidienne d'un indicateur
duree = 5
period = DAY
test = 'i1---01'
histo = to_indicator(engine, test, histo=True, format='table', histo_period=period, 
                     histo_timest=date_init.isoformat())
for i in range(duree - 1):
    date_init += day_delta
    indic = to_indicator(engine, test, histo=True, format='table', histo_period=period, 
                         histo_timest=date_init.isoformat())
    indic['value'] += i
    histo = pd.concat([histo, indic], ignore_index=True)
```

```python
mensuel = to_df_histo_up(histo, '2024-01-01', 'm')
assert(mensuel[mensuel['target']=='11']['value'][0] == histo[histo['target']=='11']['value'].mean())
assert(mensuel[mensuel['target']=='01']['extras'].iloc[0]['last'] == mensuel[mensuel['target']=='01']['extras'].iloc[0]['maxi'])
assert(len(mensuel) == len(histo) / duree)
```

```python
mensuel_bis = to_df_histo_up(mensuel, '2024-01-01', 'm')
mensuel_bis
assert(mensuel.equals(mensuel_bis))
```

```python
histo_t = histo.copy()
del histo_t['extras']
mensuel_bis = to_df_histo_up(histo_t, '2024-01-01', 'm')
assert(mensuel.equals(mensuel_bis))
```

```python
histo_t = histo.copy()
histo_t['extras'] = [None] * len(histo_t)
mensuel = to_df_histo_up(histo_t, '2024-01-31', 'm')
assert(mensuel[mensuel['target']=='11']['extras'][0]['quantity'] == duree)
```

## Tests traitement global

```python
# simulation de l'historisation quotidienne de deux indicateurs
duree = 5
period = DAY
option = 'replace'
for test in ['i1---01', 't8---01']:
    date_init = datetime.fromisoformat('2024-01-01')
    histo = to_indicator(engine, test, histo=True, format='table', histo_period=period, histo_timest= date_init.isoformat(), 
                         table_name='histo', table_option=option, table_dtype=type_histo)
    option = 'append'
    for i in range(duree - 1):
        date_init += day_delta
        indic = to_indicator(engine, test, histo=True, format='table', histo_period=period, histo_timest= date_init.isoformat(), 
                             table_name='histo', table_option=option, table_dtype=type_histo)
    print(test)
```

```python
histo_df = histo_up(engine, DAY, datetime.fromisoformat('2024-01-01'), MONTH, final_table='histo_m', if_exists='replace')
histo_df
```

```python
histo_d = pd.read_sql_query('SELECT * FROM histo', engine)
histo_m = pd.read_sql_query('SELECT * FROM histo_m', engine)
histo_m_n = pd.concat([histo_m, pd.json_normalize(histo_m['extras'])], axis=1)

assert(len(histo_m) == len(histo_d) / duree)
```

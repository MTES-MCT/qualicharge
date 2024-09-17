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

## Présentation

### Principes d'historisation

L'historisation consisite à aggréger les valeurs d'une base temporelle en une seule valeur d'une autre base temporelle. Par exemple on aggrège toutes les valeurs quotidienne d'un mois en une valeur mensuelle.

Les fonctions d'aggrégation peuvent être :

- une somme (SUM),
- un comptage (COUNT),
- une moyenne (MEAN) (+ variance éventuellement),
- une des valeurs existantes (la dernière (LAST), la valeur minimale (MINI), la valeur maximale (MAXI))

La fonction d'aggrégation doit pouvoir être propagée. Par exemple, si on choisit pour fonction une moyenne, on doit pouvoir calculer la moyenne annuelle à partir des moyennes mensuelles. Les fonctions citées ci-dessus peuvent être propagées individuellement sauf la fonction de moyenne MEAN qui doit être couplée à la fonction de comptage COUNT.

### Application aux indicateurs

Les indicateurs actuels ne définissent pas les fonctions d'aggrégation qui leurs sont appliquées. Celles-ci dépendent de la restitution qui sera effectuée.

Par exemple :

- indicateur 'i4' (nombre de stations). On peut souhaiter représenter l'évolution annuelle du nombre de stations par une courbe avec un point par mois. Dans ce cas, la fonction LAST serait appropriée. On peut aussi représenter cette évolution par un diagramme en barres avec une barre par mois et pour cela la fonction MEAN est pertinente (nécessite en complément la fonction COUNT).
- indicateur 'u4' (énergie distribuée). Les représentations de l'évolution annuelle de cet indicateur peuvent être :
    - un diagramme en barres avec l'énergie moyenne quotidienne mois par mois (fonction MEAN),
    - un diagramme en barres avec l'énergie cumulée mois par mois (fonction SUM).

Pour le choix des fonctions à utiliser pour l'historisation, trois options sont possibles :

- Option 1 : on choisit pour chaque indicateur quelles fonctions on applique. Par exemple pour 'i4', on définirait LAST, MEAN et COUNT et pour 'u4', SUM, MEAN et COUNT.
- Option 2 : on applique l'ensemble des fonctions à chaque indicateur (SUM, COUNT, MEAN, LAST, MINI, MAXI)
- Option 3 : on applique les principales fonctions à chaque indicateur (SUM, COUNT, MEAN, LAST) et on choisit les autres pour chaque indicateur (MINI, MAXI, autres)

### Intégration à la structure d'historisation

La structure retenue pour l'historisation comporte deux champs : 'value'(float) et 'extras'(json) pour stocker les valeurs associées aux résultats des fonctions (un résultat pour le champs 'value', les autres dans le champ 'extras'.

Deux options sont possibles:

- option 1 : le même résultat dans le champ 'value' pour tous les indicateurs (ex. résultat de la fonction MEAN) et les autres dans le champ 'extras'.
- option 2 : un résultat défini pour chaque indicateur dans le champ 'value' et les autres dans le champ 'extras'

### Valeurs additionnelles

Des valeurs additionnelles peuvent être ajoutées au champ 'extras', par exemple pour l'indicateur 'e2' des stations actives, on ajoute la liste des stations dans le champ 'extras'. Il faut donc définir explicitement la fonction d'aggrégation choisie (pour une liste, on choisit la fonction LAST).

Deux options sont possibles :

- Option 1: la fonction est définie dans les paramètres associés à l'indicateur,
- Option 2: la fonction est défnie dans le nom de l'attribut associé


## Mise en oeuvre

Pour le test de ces fonctions, les options suivantes ont été retenues :

- Choix des fonctions : option 2
- Intégration dans la structure : option 1
- Valeurs additionnelles : option 2

Trois fonctions sont définies :

- passage d'un niveau à un autre ( 'to_df_histo_up' pour le calcul et 'histo_up' pour la fonction globale),
- calcul des indicateurs aux données historisées ('temporal_indicator').

```python
import sys
sys.path.append('/home/jovyan/work/src/prefect/indicators') 
```

```python editable=true slideshow={"slide_type": ""}
import os
from datetime import datetime, timedelta
from string import Template 
from dateutil.relativedelta import relativedelta
import json
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, types, dialects
from sqlalchemy.engine import Connection, Engine
from create_query import to_indicator
from string import Template
from models import Level, IndicatorPeriod, Indicator, IndicatorTimeSpan, PeriodDuration

engine = create_engine(os.getenv("DATABASE_URL"))

type_histo = {'value': types.FLOAT, 'category': types.TEXT, 'code': types.TEXT, 'level': types.TEXT, 'target': types.TEXT, 
              'period': types.TEXT, 'timestamp': types.TIMESTAMP, 'extras': dialects.postgresql.JSONB}
delta_period = { IndicatorPeriod.DAY: PeriodDuration.DAY, 
                 IndicatorPeriod.WEEK: PeriodDuration.WEEK, 
                 IndicatorPeriod.MONTH: PeriodDuration.MONTH, 
                 IndicatorPeriod.QUARTER: PeriodDuration.QUARTER, 
                 IndicatorPeriod.YEAR: PeriodDuration.YEAR}
```

### Changement de niveau (calcul des champs)

Points particuliers concernant le calcul des nouvelles données:

- Le champ 'extras' contient des données fixes ('quantity', 'mini', 'maxi', 'last', 'variance') et des données libres.
- Pour savoir traiter les données libres lors d'un changement de période, plusieurs options sont proposées pour la valeur à garder : somme, moyenne, mini, maxi ou bien la dernière (option par défaut).
- La proposition est d'indiquer le traitement à effectuer dans le nom de la donnée libre (ex. 'sum_ma_valeur' indique qu'on va conserver la somme) et si le début du nom n'indique aucune option on prend l'option par défaut (ex. 'ma_liste' sera traité en gardant la dernière valeur).

```python
def to_df_histo_up(indic: pd.DataFrame, 
                   timest: datetime, 
                   period: IndicatorPeriod) -> pd.DataFrame:
    '''return a converted historicization for a new period'''
    
    index = ['code', 'level', 'target', 'category']
    histo = ['period', 'timestamp']
    value = ['value']
    add_val = ['quantity', 'mini', 'maxi', 'last', 'variance']
    fixe = index + value + add_val + histo
    
    # normalize the DataFrame
    df = indic.sort_values(by='timestamp').reset_index(drop=True)
    df['category'] = df['category'].fillna(' ') # groupby daesn't work well with NA values
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

    # add fields to calculate mean values
    for col in add_col_mean + ['value']:
        df[col + '_qua'] = df[col] * df['quantity']

    # group the DataFrame
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

    # add the historicization format
    df_n1['extras'] = df_n1[add_val + add_col].to_dict(orient='records')    
    df_n1['timestamp'] = timest
    df_n1['period'] = period.value
    
    return df_n1.reset_index()[index + value + ['extras'] + histo]
```

### Changement de niveau (traitement global)

Points particuliers :

- Le timestamp est positionné sur le début de l'intervalle.

```python
def histo_up(engine: Engine, 
             from_histo: IndicatorTimeSpan, 
             final_period: IndicatorPeriod,
             init_table: str ='histo', 
             final_table: str ='histo', 
             if_exists: str ='append') -> pd.DataFrame:
    '''add new historicization with new period'''
    
    end_period = from_histo.start + delta_period[final_period].value
    param = {'histo_table': init_table, 'period': from_histo.period.value, 'start': from_histo.start, 'end': end_period}
    
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
    
    histo_up_df = to_df_histo_up(histo_df, from_histo.start, final_period)
    histo_up_df.to_sql(final_table, engine, if_exists=if_exists, index=False, dtype=type_histo)
    
    return histo_up_df
```

### Calcul des indicateurs

Points particuliers:

- les données sont fournies si l'historisation comporte bien le 'level' demandé (pas de recalcul)
- le nommage des champs est effectué à partir des données de configuration des indicateurs 'config_indicators.json'
- le périmètre demandé est appliqué s'il est 'supérieur ou égal' au 'level' des données

```python
def temporal_indicator(code: str,
                       level: Level,
                       period: IndicatorPeriod,
                       interval_start: datetime, 
                       interval_end: datetime, 
                       perim: Level = None, 
                       val: str = None,  
                       table: str ='histo') -> pd.DataFrame: 
    '''calculate indicator with historicized data'''
    
    with open('../indicators/config_indicators.json', 'r') as file:
        indicators_param = json.load(file)
    
    indic_param = indicators_param[code]
    query_params = {'table': table, 'code': code, 'level': level.value, 'period': period.value,
                    'start': interval_start, 'end': interval_end,
                    'value_name': indic_param['value'], 'target': level.name.lower()}    
    query_params['category'] = "" if not indic_param['category'] else f"category AS {indic_param['category']},"
    query_params['where_perim'] = f"AND {level.name.lower()}.code = '{val}'" if perim else ""
    match (perim, level) :
        case (Level.CITY, Level.CITY):
            query_params['inner_perim'] = "INNER JOIN City on target = City.code"
        case (Level.EPCI, Level.CITY):
            query_params['inner_perim'] = """
                INNER JOIN City on target = City.code
                INNER JOIN EPCI ON City.epci_id = EPCI.id"""    
        case (Level.DEPARTMENT, Level.CITY):
            query_params['inner_perim'] = """
                INNER JOIN city on target = city.code
                INNER JOIN Department ON City.department_id = Department.id"""    
        case (Level.REGION, Level.CITY):
            query_params['inner_perim'] = """
                INNER JOIN city on target = city.code
                INNER JOIN Department ON City.department_id = Department.id
                INNER JOIN Region ON Department.region_id = Region.id"""
        case (Level.DEPARTMENT, Level.DEPARTMENT):
            query_params['inner_perim'] = """
                INNER JOIN Department on target = Department.code"""
        case (Level.REGION, Level.DEPARTMENT):
            query_params['inner_perim'] = """
                INNER JOIN Department on target = Department.code
                INNER JOIN Region ON Department.region_id = Region.id"""    
        case (Level.REGION, Level.REGION):
            query_params['inner_perim'] = """
                INNER JOIN Region on target = Region.code"""      
        case _:
            query_params['inner_perim'] = ""
            query_params['where_perim'] = ""
    
    query_template = Template("""
        SELECT
          value AS $value_name, 
          $category
          target AS $target, 
          timestamp
        FROM
          $table
          $inner_perim
        WHERE
          $table.code = '$code' AND level::int = '$level' AND period = '$period' AND
          timestamp >= '$start' AND timestamp < '$end'
          $where_perim
        """)
    
    return pd.read_sql_query(query_template.substitute(query_params), engine.connect())
```

## Tests


### tests changement de niveau (calcul des champs)

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

#### tests calcul des valeurs

```python
# création jeu de tests
duree = 3
histo = pd.DataFrame(data)
data2 = data.copy()
date_init2 = date_init
for i in range(1, duree):
    date_init2 += PeriodDuration.DAY.value
    data2 |= {'timestamp': [date_init2]*size, 'value': list(range(i, size+i))}
    histo = pd.concat([histo, pd.DataFrame(data2)], ignore_index=True)
```

```python
# tests
mensuel = to_df_histo_up(histo, '2024-01-01', IndicatorPeriod.MONTH)
df = pd.concat([mensuel, pd.json_normalize(mensuel['extras'])], axis=1)
del df['extras']

assert(df['value'].equals(pd.Series(range(1, size+1), dtype='float')))
assert(df['mini'].equals(pd.Series(range(size), dtype='float')))
assert(df['maxi'].equals(pd.Series(range(2, size+2), dtype='float')))
assert(df['last'].equals(df['maxi']))
assert(df['quantity'].equals(pd.Series([3]*size)))
```

#### tests extras

```python
# création jeu de tests
duree = 3
data_add = data.copy()
data_add['extras'] = [{'liste': ['a', 'b', 'c'], 'sum_val': i, 'max_val': float(i),
                          'min_val': float(i), 'last_val': float(i)} for i in range(size)]
histo = pd.DataFrame(data_add)
data2 = data_add.copy()
date_init2 = date_init
for j in range(1, duree):
    date_init2 += PeriodDuration.DAY.value
    data2 |= {'timestamp': [date_init2]*size, 'value': list(range(j, size+j))}
    data2 |= {'extras': [{'sum_val': i+j, 'max_val': float(i+j),
                          'min_val': float(i+j), 'last_val': float(i+j)} for i in range(size)]}
    histo = pd.concat([histo, pd.DataFrame(data2)], ignore_index=True)
```

```python
# tests
mensuel = to_df_histo_up(histo, '2024-01-01', IndicatorPeriod.MONTH)
df = pd.concat([mensuel, pd.json_normalize(mensuel['extras'])], axis=1)
del df['extras']

assert(df['value'].equals(pd.Series(range(1, size+1), dtype='float')))
assert(df['mini'].equals(pd.Series(range(size), dtype='float')))
assert(df['maxi'].equals(pd.Series(range(2, size+2), dtype='float')))
assert(df['last'].equals(df['maxi']))
assert(df['quantity'].equals(pd.Series([3]*size)))
assert(df['sum_val'].equals(pd.Series(range(3, (size+1)*duree, duree))))
assert(df['max_val'].equals(df['maxi']))
assert(df['min_val'].equals(df['mini']))
assert(df['last_val'].equals(df['last']))
```

#### test indicateur

```python
# simulation de l'historisation quotidienne d'un indicateur
duree = 5
period = IndicatorPeriod.DAY
period = 'd'
test = 'i1---01'
histo = to_indicator(engine, test, histo=True, format='table', histo_period=period, 
                     histo_timest=date_init.isoformat())
for i in range(duree - 1):
    date_init += PeriodDuration.DAY.value
    indic = to_indicator(engine, test, histo=True, format='table', histo_period=period, 
                         histo_timest=date_init.isoformat())
    indic['value'] += i
    histo = pd.concat([histo, indic], ignore_index=True)
```

```python
# tests
mensuel = to_df_histo_up(histo, '2024-01-01', IndicatorPeriod.MONTH)

assert(mensuel[mensuel['target']=='11']['value'][0] == histo[histo['target']=='11']['value'].mean())
assert(mensuel[mensuel['target']=='01']['extras'].iloc[0]['last'] == mensuel[mensuel['target']=='01']['extras'].iloc[0]['maxi'])
assert(len(mensuel) == len(histo) / duree)
```

```python
mensuel_bis = to_df_histo_up(mensuel, '2024-01-01', IndicatorPeriod.MONTH)

assert(mensuel.equals(mensuel_bis))
```

```python
histo_t = histo.copy()
del histo_t['extras']
mensuel_bis = to_df_histo_up(histo_t, '2024-01-01', IndicatorPeriod.MONTH)

assert(mensuel.equals(mensuel_bis))
```

```python
histo_t = histo.copy()
histo_t['extras'] = [None] * len(histo_t)
mensuel = to_df_histo_up(histo_t, '2024-01-31', IndicatorPeriod.MONTH)

assert(mensuel[mensuel['target']=='11']['extras'][0]['quantity'] == duree)
```

### Tests changement de niveau (traitement global)

```python
# simulation de l'historisation quotidienne de deux indicateurs
duree = 5
period = 'd'
option = 'replace'
for test in ['i1---02', 't8---02']:
    date_init = datetime.fromisoformat('2024-01-01')
    histo = to_indicator(engine, test, histo=True, format='table', histo_period=period, histo_timest= date_init.isoformat(), 
                         table_name='histo', table_option=option, table_dtype=type_histo)
    option = 'append'
    for i in range(duree - 1):
        date_init += PeriodDuration.DAY.value
        indic = to_indicator(engine, test, histo=True, format='table', histo_period=period, histo_timest= date_init.isoformat(), 
                             table_name='histo', table_option=option, table_dtype=type_histo)
    print(test)
```

```python
from_histo = IndicatorTimeSpan(period=IndicatorPeriod.DAY, start=datetime.fromisoformat('2024-01-01'))
histo_df = histo_up(engine, from_histo, IndicatorPeriod.MONTH, final_table='histo_m', if_exists='replace')
histo_df
```

```python
histo_d = pd.read_sql_query('SELECT * FROM histo', engine)
histo_m = pd.read_sql_query('SELECT * FROM histo_m', engine)
histo_m_n = pd.concat([histo_m, pd.json_normalize(histo_m['extras'])], axis=1)

assert(len(histo_m) == len(histo_d) / duree)
```

### Tests calcul des indicateurs

```python
# simulation de l'historisation quotidienne de deux indicateurs
duree = 5
period = 'd'
option = 'replace'
for test in ['i1---02', 't8---02']:
    date_init = datetime.fromisoformat('2024-01-01')
    histo = to_indicator(engine, test, histo=True, format='table', histo_period=period, histo_timest= date_init.isoformat(), 
                         table_name='histo', table_option=option, table_dtype=type_histo)
    option = 'append'
    for i in range(duree - 1):
        date_init += PeriodDuration.DAY.value
        indic = to_indicator(engine, test, histo=True, format='table', histo_period=period, histo_timest= date_init.isoformat(), 
                             table_name='histo', table_option=option, table_dtype=type_histo)
    print(test)
```

```python
# test de 'i1-d-2-27-2 entre le 1/1/2024 et le 3/1/2024
interval_start = '2024-01-01'
interval_end = '2024-01-03'

indic = temporal_indicator('i1', Level.DEPARTMENT, IndicatorPeriod.DAY, interval_start, interval_end, perim=2, val=27)
assert(len(indic) == 2)
```

```python
# test de 't8-d-2-27-2' entre le 1/1/2024 et le 3/1/2024
interval_start = '2024-01-01'
interval_end = '2024-01-03'

indic = temporal_indicator('t8',Level.DEPARTMENT, IndicatorPeriod.DAY, interval_start, interval_end, perim=2, val=27)

assert(len(indic[indic['timestamp']=='2024-01-01']) == len(indic) / 2)
assert(indic[indic['timestamp']=='2024-01-01']['nom_operateur'].reset_index(drop=True).equals(
       indic[indic['timestamp']=='2024-01-02']['nom_operateur'].reset_index(drop=True)))
```

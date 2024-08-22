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

# QualiCharge data: Test of indicators creation
Example of indicators creation

```python
import os
import json
from sqlalchemy import create_engine
import pandas as pd
from util import indic_pandas, indic_to_table

# Get database URL from the environment
database_url = os.getenv("DATABASE_URL")

# Create a database engine that will be used to generate connections
engine = create_engine(database_url)

```

## T1 : Nombre de points de recharge par niveau de puissance

```python
t1_nat = indic_pandas(engine, 't1-00')
print(t1_nat['nb_pdc'].sum())
t1_nat
```

```python
indic_pandas(engine, 't1-02-75')
```

## T2 : Pourcentage de points de recharge par niveau de puissance

```python
t2_nat = indic_pandas(engine, 't2-00')
print(t2_nat['pct_nb_pdc'].sum())
t2_nat
```

```python
indic_pandas(engine, 't2-02-75')
```

## T3 : Nombre de stations par nombre de points de recharge

```python
t3_nat = indic_pandas(engine, 't3-00')
print(t3_nat.prod(axis=1).sum(), t3_nat['nb_stations'].sum())
t3_nat[:10]
```

```python
indic_pandas(engine, 't3-04-74012')
```

## T5 : Nombre de stations par type d’implantation

```python jupyter={"source_hidden": true}
t5_nat = indic_pandas(engine, 't5-00')
print(t5_nat['nb_stations'].sum())
t5_nat[:10]
```

```python
indic_pandas(engine, 't5-03-200023414')
```

## I1 : Nombre de points de recharge ouverts au public

```python
i1_nat = indic_pandas(engine, 'i1-00-00-01')
print(i1_nat['nb_pdc'].sum())
i1_nat[:10]
```

```python
paca_epci = 'i1-01-93-03'
i1_paca = indic_pandas(engine, paca_epci)
i1_paca[:10]
```

```python
indic_to_table(i1_paca, 'i1_paca_epci', engine)
```

## I4 : Nombre de stations ouvertes au public

```python
i4_nat = indic_pandas(engine, 'i4-00-00-01')
print(i4_nat['nb_stat'].sum())
i4_nat[:10]
```

```python
indic_pandas(engine, 'i4-01-93-03')[:10]
```

## I7 : Puissance installée

```python
i7_nat = indic_pandas(engine, 'i7-00-00-01')
print(i7_nat['p_nom'].sum())
i7_nat[:10]
```

```python
i7_paca_city = indic_pandas(engine, 'i7-01-93-04')
i7_paca_city[:10]
```

```python
indic_to_table(i7_paca_city, 'i7_paca_city', engine)
```

```python
with open('indics.json') as fp:
    indics_dict = json.load(fp)
indics_dict
```

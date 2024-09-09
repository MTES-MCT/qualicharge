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
# Indicateurs QualiCharge : Tests historisation

<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
import os
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
from create_query import to_indicator #, create_table_pop

# Connecteur à la base Qualicharge
engine = create_engine(os.getenv("DATABASE_URL"))

```

## Tests Solution 1

```python
to_indicator(engine, 't1-02-75')
```

```python
# ajout d'indicateurs dans la table 'quotidien'
# on simule plusieurs jours en répétant les indicateurs
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
with engine.connect() as conn:
    quotidien = pd.read_sql_table('quotidien', conn)
quotidien
```

```python
# passage de la table 'quotidien' à la table 'mensuel'

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

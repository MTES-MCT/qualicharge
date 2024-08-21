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
import pandas as pd
import util #, gen_indicators
```

```python
import os
import json
from sqlalchemy import create_engine

# Get database URL from the environment
database_url = os.getenv("DATABASE_URL")

# Create a database engine that will be used to generate connections
engine = create_engine(database_url)

# choix des indicateurs à mettre à jour
indics = ['t1-00']
```

```python
with open('indics.json') as fp:
    indics_dict = json.load(fp)
indics_dict
```

```python
'''WITH puissance(p_range, p_cat) AS (
    VALUES (numrange(0, 15.0), 1), (numrange(15.0, 26.0), 2), (numrange(26, 65.0), 3), (numrange(65, 175.0), 4), (numrange(175, 360.0), 5), (numrange(360, NULL), 6)
    ) 
SELECT count(id_pdc_itinerance) AS nb_pdc, p_cat, p_range, code
FROM region, pointdecharge LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id 
WHERE code = '04' AND ST_Within("coordonneesXY", geometry)
GROUP BY p_cat, p_range, code 
ORDER BY nb_pdc DESC'''

t1_pd = util.init_data_pandas('t1', indics_dict, engine)
t1_pd
```

```python
t3_pd = util.init_data_pandas('t3', indics_dict, engine)
t3_pd[:15]
```

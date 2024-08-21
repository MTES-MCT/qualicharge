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
t1_pd = util.init_data_pandas('t1', indics_dict, engine)
t1_pd
```

```python
t3_pd = util.init_data_pandas('t3', indics_dict, engine)
t3_pd[:15]
```

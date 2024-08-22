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
import util #, gen_indicators

# Get database URL from the environment
database_url = os.getenv("DATABASE_URL")

# Create a database engine that will be used to generate connections
engine = create_engine(database_url)

```

```python
util.init_data_pandas(engine, 't1-00')
```

```python
util.init_data_pandas(engine, 't1-02-75')
```

```python
with open('indics.json') as fp:
    indics_dict = json.load(fp)
indics_dict
```

```python
t3_pd = util.init_data_pandas('t3', indics_dict, engine)
t3_pd[:15]
```

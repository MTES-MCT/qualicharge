---
jupyter:
  jupytext:
    formats: ipynb,md
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

# Import French administrative boundaries


## Download official up-to-date geojson files

```python
import gzip
import tempfile
from dataclasses import dataclass
from pathlib import Path

import httpx

@dataclass
class AdministrativeBoundary:
    """An administrative boundary level."""
    path: Path
    url: str

# Define administrative boundaries files to download
levels = ("communes", "epci", "departements", "regions")
etalab_root_url = "https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/2024/geojson"
resolution = "100m"
boundaries = {}

tmp_dirname = tempfile.mkdtemp()
for level in levels:
    boundaries[level] = AdministrativeBoundary(
        path=Path(f"{tmp_dirname}/{level}.geojson.gz"),
        url=f"{etalab_root_url}/{level}-{resolution}.geojson.gz",
    )

# Download
for level, ab in boundaries.items():
    print(f"Downloading {level} file to {ab.path}...")
    response = httpx.get(ab.url)
    with open(ab.path, "wb") as output_file:
        output_file.write(gzip.decompress(response.content))
```

## Import administrative boundaries

```python
import os
from sqlalchemy import create_engine

# Get database URL from the environment
database_url = os.getenv("DATABASE_URL")

# Create a database engine that will be used to generate connections
engine = create_engine(database_url)
```

```python
import uuid
import geopandas as gp
import pandas as pd
```

### Regions

```python
regions = gp.read_file(f'GeoJSON:{boundaries["regions"].path}')

# Add missing columns to regions (to fit with the ORM)
regions["id"] = regions.apply(lambda x: uuid.uuid4(), axis=1)
now = pd.Timestamp("now")
regions['created_at'] = now
regions['updated_at'] = now

# Update column names (to fit with the ORM)
regions.rename(columns={"nom": "name"}, inplace=True)
regions
```

```python
regions.explore()
```

```python
import sqlalchemy

# Here we append to keep existing database schema for this table
with engine.connect() as conn:
    conn.execute(sqlalchemy.text("TRUNCATE TABLE region CASCADE"))
    conn.commit()
regions.to_postgis("region", engine, if_exists="append")
```

### Departments

```python
departments = gp.read_file(f'GeoJSON:{boundaries["departements"].path}')

# Add missing columns to regions (to fit with the ORM)
departments["id"] = departments.apply(lambda x: uuid.uuid4(), axis=1)
now = pd.Timestamp("now")
departments['created_at'] = now
departments['updated_at'] = now

# Update column names (to fit with the ORM)
departments.rename(columns={"nom": "name"}, inplace=True)
departments
```

```python
# Add foreign keys
departments = departments.merge(regions[["id", "code"]], how="outer", left_on="region", right_on="code", suffixes=("_dept", "_reg"))

# Remove extra columns and rename columns used for merging
departments.rename(columns={"code_dept": "code", "id_dept": "id", "id_reg": "region_id"}, inplace=True)
departments.drop(["code_reg", "region"], axis=1, inplace=True)
departments.sort_values(by=["code"])
```

```python
departments.explore()
```

```python
# Here we append to keep existing database schema for this table
with engine.connect() as conn:
    conn.execute(sqlalchemy.text("TRUNCATE TABLE department CASCADE"))
    conn.commit()
    
departments.to_postgis("department", engine, if_exists="append")
```

### EPCI

```python
epci = gp.read_file(f'GeoJSON:{boundaries["epci"].path}')

# Add missing columns to regions (to fit with the ORM)
epci["id"] = epci.apply(lambda x: uuid.uuid4(), axis=1)
now = pd.Timestamp("now")
epci['created_at'] = now
epci['updated_at'] = now

# Update column names (to fit with the ORM)
epci.rename(columns={"nom": "name"}, inplace=True)
epci
```

```python
epci.explore()
```

```python
# Here we append to keep existing database schema for this table
with engine.connect() as conn:
    conn.execute(sqlalchemy.text("TRUNCATE TABLE epci CASCADE"))
    conn.commit()
    
epci.to_postgis("epci", engine, if_exists="append")
```

### Cities

```python
cities = gp.read_file(f'GeoJSON:{boundaries["communes"].path}')

# Add missing columns to regions (to fit with the ORM)
cities["id"] = cities.apply(lambda x: uuid.uuid4(), axis=1)
now = pd.Timestamp("now")
cities['created_at'] = now
cities['updated_at'] = now

# Update column names (to fit with the ORM)
cities.rename(columns={"nom": "name"}, inplace=True)
cities
```

```python
# Add foreign keys

# -- Department --
cities = cities.merge(departments[["id", "code"]], how="outer", left_on="departement", right_on="code", suffixes=("_city", "_dept"))

# Remove extra columns and rename columns used for merging
cities.rename(columns={"code_city": "code", "id_city": "id", "id_dept": "department_id"}, inplace=True)
cities.drop(["code_dept", "region", "commune", "departement", "plm"], axis=1, inplace=True)

# -- EPCI --
cities = cities.merge(epci[["id", "code"]], how="outer", left_on="epci", right_on="code", suffixes=("_city", "_epci"))

# Remove extra columns and rename columns used for merging
cities.rename(columns={"code_city": "code", "id_city": "id", "id_epci": "epci_id"}, inplace=True)
cities.drop(["code_epci", "epci"], axis=1, inplace=True)
cities.sort_values(by=["code"])
```

```python
cities.explore()
```

```python
# Here we append to keep existing database schema for this table
with engine.connect() as conn:
    conn.execute(sqlalchemy.text("TRUNCATE TABLE city CASCADE"))
    conn.commit()
    
cities.to_postgis("city", engine, if_exists="append")
```

```python

```

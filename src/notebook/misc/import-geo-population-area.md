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

# Import administrative levels population and area


## Cities


### Population

```python
import pandas as pd

data_url = "https://unpkg.com/@etalab/decoupage-administratif/data/communes.json"
population = pd.read_json(data_url, dtype_backend="pyarrow")
population
```

```python
population[population.duplicated(["code"], keep=False)]
```

```python
population[population["type"] == "commune-actuelle"]
```

```python
population.loc[~population["population"].isna(), ["code", "population"]]
```

```python
import os
from sqlalchemy import create_engine

# Get database URL from the environment
database_url = os.getenv("DATABASE_URL")

# Create a database engine that will be used to generate connections
engine = create_engine(database_url)
```

```python
import geopandas as gp

with engine.connect() as conn:
    cities = gp.read_postgis("city", conn, geom_col='geometry', crs=4326)
cities
```

```python
right_cities_population = population.loc[~population["population"].isna(), ["code", "population"]]
cities_population = cities.merge(right_cities_population, how="left", on="code")
cities_population.drop(["population_x"], axis=1, inplace=True)
cities_population.rename(columns={"population_y": "population"}, inplace=True)
cities_population
```

```python
cities_population[cities_population["population"].isna()]
```

```python
population[population["code"] == "85165"]
```

### Area

```python
import numpy as np

crs = pd.DataFrame.from_records(
    [(f"{d:02d}", 9794) for d in range(1, 96) if d != 20] + [
    ("2A", 9794),
    ("2B", 9794)] + [
    ("971", 5490),
    ("972", 5490),
    ("973", 2972),
    ("974", 2975),
    ("975", 4467),
    ("976", 4471),
    ("977", 5490),
    ("978", 5490),
    ("984", 7080),
    ("986", 8903),
    ("987", 3296),
    ("988", 3163),
    ("989", pd.NA),
], columns=["departement", "crs"])
crs
```

```python
right_population = population.loc[~population["population"].isna(), ["code", "departement"]].merge(crs, how="left", on="departement")
cities_with_crs = cities_population.merge(right_population, how="left", on="code")
cities_with_crs
```

```python
# List of unique CRSs
ucrs = pd.unique(crs["crs"])
ucrs = ucrs[~pd.isnull(ucrs)].tolist()
ucrs
```

```python
area = pd.Series()
for c in ucrs:
    df = cities_with_crs.loc[cities_with_crs["crs"] == c]
    area = pd.concat([area, df["geometry"].to_crs(c).area])
area
```

```python
cities_population["area"] = area
cities_population.replace(np.nan, pd.NA, inplace=True)
cities_population
```

```python
# Write it back
with engine.connect() as conn:
    cities_population.to_postgis("city", conn, if_exists="replace")
```

## Departments

```python
with engine.connect() as conn:
    departments = gp.read_postgis("department", conn, geom_col='geometry', crs=4326)
departments
```

### Population

```python
department_population = population.loc[population["type"] == "commune-actuelle", ["departement", "population"]].groupby("departement", as_index=False).agg("sum")
department_population
```

```python
department_population.loc[department_population["departement"] == "63"]
```

```python
departments = departments.merge(department_population, how="left", left_on="code", right_on="departement")
departments.drop(["population_x", "departement"], axis=1, inplace=True)
departments.rename(columns={"population_y": "population"}, inplace=True)
departments
```

```python
departments.loc[departments["code"] == "63"]
```

### Area

```python
departments_with_crs = departments.merge(crs, how="left", left_on="code", right_on="departement")
departments_with_crs
```

```python
area = pd.Series()
for c in ucrs:
    df = departments_with_crs.loc[departments_with_crs["crs"] == c]
    area = pd.concat([area, df["geometry"].to_crs(c).area])
area
```

```python
departments["area"] = area
departments.replace(np.nan, pd.NA, inplace=True)
departments
```

```python
# Write it back
with engine.connect() as conn:
    departments.to_postgis("department", conn, if_exists="replace")
```

## EPCI

```python
with engine.connect() as conn:
    epcis = gp.read_postgis("epci", conn, geom_col='geometry', crs=4326)
epcis
```

### Population

```python
data_url = "https://unpkg.com/@etalab/decoupage-administratif/data/epci.json"
population = pd.read_json(data_url, dtype_backend="pyarrow")
population
```

```python
population["membres"].apply(lambda x: x[0]["code"])
```

```python
epcis = epcis.merge(population[["code", "populationMunicipale"]], how="left", on="code")
epcis.drop(["population"], axis=1, inplace=True)
epcis.rename(columns={"populationMunicipale": "population"}, inplace=True)
epcis
```

### Area

```python
epcis["area"] = epcis["geometry"].to_crs(9794).area
epcis
```

```python
# Write it back
with engine.connect() as conn:
    epcis.to_postgis("epci", conn, if_exists="replace")
```

## Region

```python
import pandas as pd

data_url = "https://unpkg.com/@etalab/decoupage-administratif/data/communes.json"
population = pd.read_json(data_url, dtype_backend="pyarrow")
population
```

```python
with engine.connect() as conn:
    regions = gp.read_postgis("region", conn, geom_col='geometry', crs=4326)
regions
```

### Population

```python
region_population = population.loc[population["type"] == "commune-actuelle", ["region", "population"]].groupby("region", as_index=False).agg("sum")
region_population
```

```python
regions = regions.merge(region_population, how="left", left_on="code", right_on="region")
regions.drop(["population_x", "region"], axis=1, inplace=True)
regions.rename(columns={"population_y": "population"}, inplace=True)
regions
```

### Area

```python
departments_region = population[["departement", "region"]].drop_duplicates().reset_index(drop=True)
region_crs = departments_region.merge(crs, how="left", on="departement")[["region", "crs"]].drop_duplicates().reset_index(drop=True)
region_crs
```

```python
regions_with_crs = regions.merge(region_crs, how="left", left_on="code", right_on="region")
regions_with_crs
```

```python
area = pd.Series()
for c in ucrs:
    df = regions_with_crs.loc[regions_with_crs["crs"] == c]
    area = pd.concat([area, df["geometry"].to_crs(c).area])
area
```

```python
regions["area"] = area
regions.replace(np.nan, pd.NA, inplace=True)
regions
```

```python
# Write it back
with engine.connect() as conn:
    regions.to_postgis("region", conn, if_exists="replace")
```

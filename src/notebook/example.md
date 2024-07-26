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

# QualiCharge data: an example notebook

This notebook aims to be an example notebook used as a starting point for a new analysis or indicator calculation. It provides code snippets and examples to fetch and record data from our PostgreSQL database.

## Create the database engine

```python
import os
from sqlalchemy import create_engine

# Get database URL from the environment
database_url = os.getenv("DATABASE_URL")

# Create a database engine that will be used to generate connections
engine = create_engine(database_url)
database_url
```

## Fetch data from the database

### Example 1: generate a stations map using GeoPandas

```python
from geopandas import GeoDataFrame

query = """
SELECT
  Station.nom_station,
  Station.id_station_itinerance,
  Amenageur.nom_amenageur as amenageur,
  Localisation."coordonneesXY" as geom
FROM
  Station
INNER JOIN Localisation ON Station.localisation_id = Localisation.id
INNER JOIN Amenageur ON Station.amenageur_id = Amenageur.id
"""


with engine.connect() as conn:
    # Query a PostgreSQL database using the PostGIS extension
    stations = GeoDataFrame.from_postgis(query, conn)

print(f"Loaded {len(stations.index)} stations")
stations.sample(10)
```

```python
# Display an interactive map of the stations
stations.explore(column="amenageur")
```

### Example 2: explore operators distribution

```python
import pandas as pd

query = """
SELECT
  Operateur.nom_operateur,
  PointDeCharge.id_pdc_itinerance
FROM
  PointDeCharge
  INNER JOIN Station ON PointDeCharge.station_id = Station.id
  INNER JOIN Operateur ON Station.operateur_id = Operateur.id
"""

with engine.connect() as conn:
    # Query a PostgreSQL database using the PostGIS extension
    pdcs = pd.read_sql_query(query, conn)

print(f"Loaded {len(pdcs.index)} points of charge")
pdcs.sample(10)
```

```python
import seaborn as sns

# Render a barplot with the number of points of charge by operator
sns.barplot(data=pdcs.value_counts("nom_operateur"))
```

## Write data to the database

### Example 1: create a new table with calculated indicator

In this example, we will calculate the number of points of charge per French department at a particular date/time (now) and store this stateful snapshot in the database.

```python
import uuid
import pandas as pd

# Get the city code insee for each point of charge
query = """
SELECT
  Localisation.code_insee_commune
FROM
  PointDeCharge
  INNER JOIN Station ON PointDeCharge.station_id = Station.id
  INNER JOIN Localisation ON Station.localisation_id = Localisation.id
"""
with engine.connect() as conn:
    # Query a PostgreSQL database using the PostGIS extension
    codes_insee = pd.read_sql_query(query, conn)

# Add a department column
codes_insee["department"] = codes_insee["code_insee_commune"].map(lambda x: int(x[:2]) if x else None)

# Calculate our indicator and add a timestamp to each department counts (row)
indicator = codes_insee.value_counts("department").to_frame().reset_index()
indicator["calculated_at"] = pd.Timestamp.now()

# Set UUIDs as the index
indicator["uuid"] = indicator.apply(lambda _: uuid.uuid4(), axis=1)
indicator.set_index("uuid", inplace=True)

# Explictly set the department column as integers
indicator = indicator.astype({"department": "int32"})
indicator
```

```python
# Save the indicator to a (new) table
indicator.to_sql("IDepartmentDynamic", engine, if_exists="append")
```

```python
# Check inserted results
query = 'SELECT * FROM "IDepartmentDynamic" WHERE department = 75'
paris = pd.read_sql_query(query, engine)
paris
```

## Metabase API


A large list of API endpoints is available in the [documentation](https://www.metabase.com/learn/administration/metabase-api).
See examples below.

```python
import requests
import pandas as pd

# Get metabase key from the environment
admin_key = os.getenv("ADMIN_KEY")

# Metabase server
METABASE_HOST = "metabase"
METABASE_PORT = 3000

# doc API : http://localhost:3000/api/docs
headers = {'x-api-key': API_ADMIN_KEY}
response = requests.get(f"http://{METABASE_HOST}:{METABASE_PORT}/api/permissions/group", headers=headers)
response.json()
```

Example : Search of Questions(card)

```python
response = requests.get(f"http://{METABASE_HOST}:{METABASE_PORT}/api/card", headers=headers)
cards = response.json()

# list of cards
my_card = [card for card in response if card['description'] and card['description'][:4] == 'test']
{card['id']: card['description'] for card in my_card}
```

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

# QualiCharge - CARBURE Integration

This notebook summarizes first integration tests to the CARBURE API to emit fourniture certificates for CPOs connected in QualiCharge production instance.

## Authentication: generate a JWT

```python
import os

CARBURE_ROOT_URL = os.environ.get("CARBURE_ROOT_URL")
CARBURE_USER_API_KEY = os.environ.get("CARBURE_USER_API_KEY")
CARBURE_USER_EMAIL = os.environ.get("CARBURE_USER_EMAIL")
CARBURE_USER_PASSWORD = os.environ.get("CARBURE_USER_PASSWORD")
```

```python
import requests

headers = {
    "X-Api-Key": CARBURE_USER_API_KEY,
}
payload = {
    "email": CARBURE_USER_EMAIL,
    "password": CARBURE_USER_PASSWORD,
}
token_url = f"{CARBURE_ROOT_URL}/api/token/"

response = requests.post(token_url, json=payload, headers=headers)
response.raise_for_status()
print(response)
token = response.json()
access_token = token["access"]
refresh_token = token["refresh"]
```

## List CARBURE entities 

```python
entities_url = f"{CARBURE_ROOT_URL}/api/resources/entities"

response = requests.get(entities_url, headers=headers)
entities = response.json()
entities[:10]
```

<!-- #region -->
## Send volumes

### Calculate production volumes

By using the following SQL request in metabase (on QualiCharge **production** database), we are able to extract volumes per station

```sql
SELECT
  nom_amenageur,
  siren_amenageur,
  substring(id_station_itinerance FOR 5) AS code,
  id_station_itinerance,
  SUM(energy)
FROM
  amenageur
  LEFT JOIN Station ON Station.amenageur_id = amenageur.id
  LEFT JOIN pointdecharge ON pointdecharge.station_id = Station.id
  LEFT JOIN SESSION ON SESSION.point_de_charge_id = PointDeCharge.id
WHERE
  START >= '2025-04-01'
  AND START < '2025-05-01'
GROUP BY
  nom_amenageur,
  siren_amenageur,
  code,
  id_station_itinerance
ORDER BY
  id_station_itinerance
```

### Load QualiCharge volumes
<!-- #endregion -->

```python
from pathlib import Path
import pandas as pd

tiruert_export_file = Path("/home/jovyan/work/data/20250401-20250430-CARBURE-TIRUERT.csv")
df = pd.read_csv(tiruert_export_file)
df.rename(columns={"nom_amenageur": "entity", "siren_amenageur": "siren", "id_station_itinerance": "id", "sum": "energy"}, inplace=True)
df["energy"] = df["energy"].astype(float)
```

```python
carbure_sirens = set(e["registration_id"] for e in entities)
qualicharge_sirens = set(df["siren"].astype(str))
qualicharge_sirens, len(qualicharge_sirens)
```

```python
qualicharge_sirens & carbure_sirens, len(qualicharge_sirens & carbure_sirens)
```

```python
qualicharge_sirens - carbure_sirens
```

```python
df[df["siren"] == 940861826]
```

```python
df[df["entity"] == "Tesla"][:10]
```

```python
# Add missing columns
df["from"] = "2025-04-01"
df["to"] = "2025-04-30"
df["is_controlled"] = False
df
```

```python
df[df["code"] == "FRTSL"]
```

```python
stations = df[df["code"] == "FRTSL"][["id", "energy", "is_controlled"]].to_dict(orient="records")
```

```python
payload = [{
    "entity": "Tesla",
    "siren": "524335262",
    "operational_units": [
      {
        "code": "FRTSL",
        "from": "2025-04-01",
        "to": "2025-04-01",
        "stations": stations[:10]
      },
    ]
}]
payload
```

```python
# Refresh access token
headers = {
    "X-Api-Key": CARBURE_USER_API_KEY,
}

refresh_token_url = f"{CARBURE_ROOT_URL}/api/token/refresh/"
response = requests.post(refresh_token_url, json={"refresh": refresh_token}, headers=headers)
token = response.json()
access_token = token["access"]
```

```python
# Send volumes for TESLA
headers = {
    "X-Api-Key": CARBURE_USER_API_KEY,
    "Authorization": f'Bearer {access_token}',
}

certificates_url = f"{CARBURE_ROOT_URL}/api/elec/provision-certificates/bulk-create/"
response = requests.post(certificates_url, json=payload, headers=headers)
response.json()
```

```python
# Check sent data
headers = {
    "X-Api-Key": CARBURE_USER_API_KEY,
    "Authorization": f'Bearer {access_token}',
}

check_certificates_url = f"{CARBURE_ROOT_URL}/api/elec/provision-certificates/?source=QUALICHARGE"
response = requests.get(check_certificates_url, headers=headers)
response.json()
```

## Session cleaning

```python
import os
from datetime import date
from string import Template

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Connecteur à la base Qualicharge
engine = create_engine(os.getenv("DATABASE_URL"))
```

```python
OPERATIONAL_UNIT_SESSIONS_FOR_A_DAY_TEMPLATE = Template(
    """
    WITH
      pdcs AS (
        SELECT
          Statique.nom_amenageur AS entity,
          Statique.siren_amenageur AS siren,
          OperationalUnit.code AS code,
          Statique.id_station_itinerance AS id_station_itinerance,
          Statique.id_pdc_itinerance AS id_pdc_itinerance,
          Statique.puissance_nominale AS max_power,
          Statique.pdc_id
        FROM
          Statique
          JOIN OperationalUnit ON Statique.id_pdc_itinerance LIKE OperationalUnit.code || '%%'
        WHERE
          OperationalUnit.code = '$operational_unit_code'
      ),
      sessions AS (
        SELECT
          SESSION.id AS session_id,
          SESSION.start AS "from",
          SESSION.end AS TO,
          SESSION.energy AS energy,
          SESSION.point_de_charge_id
        FROM
          SESSION
        WHERE
          SESSION.start >= '$from_date'
          AND SESSION.start < '$to_date'
      )
    SELECT
      entity,
      siren,
      code,
      id_station_itinerance,
      id_pdc_itinerance,
      max_power,
      session_id,
      "from",
      "to",
      energy
    FROM
      pdcs
      JOIN sessions ON pdcs.pdc_id = sessions.point_de_charge_id
    ORDER BY
      pdcs.id_pdc_itinerance,
      sessions."from"
    """
)
params = {"from_date": date(2024, 12, 27), "to_date": date(2024, 12, 28), "operational_unit_code": "FRPD1"}
query = OPERATIONAL_UNIT_SESSIONS_FOR_A_DAY_TEMPLATE.substitute(params)
print(query)
```

```python
with Session(engine) as session:
    qc_sessions = pd.read_sql_query(query, con=session.connection())
qc_sessions
```

### Detect abnormal sessions (NEGS, ENEU, ENEA, ODUS, ENEX)

```python
def negs(row):
    return (row["to"] - row["from"]).seconds < 0

def eneu(row):
    return row["energy"] > 1000.

def enea_max(row):
    return ((row["to"] - row["from"]).seconds / 3600) * row["max_power"]

def enea(row):
    return row["energy"] > enea_max(row) * 1.1

def odus(row):
    return negs(row) and row["energy"] > 1

def enex(row):
    return row["energy"] > 50. and row["energy"] > enea_max(row) * 2.0
    
qc_sessions["enea_max"] = qc_sessions.apply(enea_max, axis=1)
qc_sessions["negs"] = qc_sessions.apply(negs, axis=1)
qc_sessions["eneu"] = qc_sessions.apply(eneu, axis=1)
qc_sessions["enea"] = qc_sessions.apply(enea, axis=1)
qc_sessions["odus"] = qc_sessions.apply(odus, axis=1)
qc_sessions["enex"] = qc_sessions.apply(enex, axis=1)

abnormal_sessions = qc_sessions[ qc_sessions.negs | qc_sessions.eneu | qc_sessions.enea | qc_sessions.odus | qc_sessions.enex ]
abnormal_sessions
```

```python
filtered = qc_sessions.iloc[qc_sessions.index.difference(abnormal_sessions.index)]
filtered
```

### Detect duplicates

```python
# Non optimized version
qc_sessions["dups"] = False

for index, current in qc_sessions.iterrows():
    if index < 1:
        continue
    
    previous = qc_sessions.iloc[index -1]
    
    # Should compare the same charge point
    if current["id_pdc_itinerance"] != previous["id_pdc_itinerance"]:
        continue
        
    # Is there an overlap?
    if current["from"] < previous["to"]:
        current["dups"] = previous["dups"] = True

qc_sessions[qc_sessions["dups"]]
```

```python
# Ease comparison with previous row (and avoid iterating over dataframe rows)
qc_sessions["p_id_pdc_itinerance"] = pd.concat([pd.Series([None]), qc_sessions["id_pdc_itinerance"][:-1]]).reset_index(drop=True)
qc_sessions["p_from"] = pd.concat([pd.Series([None]), qc_sessions["from"][:-1]]).reset_index(drop=True)
qc_sessions["p_to"] = pd.concat([pd.Series([None]), qc_sessions["to"][:-1]]).reset_index(drop=True)

qc_sessions
```

```python
# Real duplicates
qc_sessions["duplicate"] = (
    (qc_sessions["from"] == qc_sessions["p_from"]) & 
    (qc_sessions["to"] == qc_sessions["p_to"]) & 
    (qc_sessions["id_pdc_itinerance"] == qc_sessions["p_id_pdc_itinerance"])
)
qc_sessions[qc_sessions["duplicate"]]
```

```python
# Overlaps
qc_sessions["overlap"] = (
    (qc_sessions["from"] < qc_sessions["p_to"]) & 
    (qc_sessions["id_pdc_itinerance"] == qc_sessions["p_id_pdc_itinerance"])
)
qc_sessions[qc_sessions["overlap"]]
```

```python
qc_sessions
```

## Send volumes to carbure

```python
from string import Template

ENERGY_BY_STATION_TEMPLATE = Template(
    """
    WITH
      energy_over_period AS (
        SELECT
          jsonb_path_query(extras, '$$.entity') ->> 0 as entity,
          jsonb_path_query(extras, '$$.siren') ->> 0 AS siren,
          target as code,
          jsonb_path_query(extras, '$$.id_station_itinerance') ->> 0 AS station,
          jsonb_path_query(extras, '$$.energy')::NUMERIC AS energy
        FROM
          $environment
        WHERE
          code = 'tirue'
          AND period = 'd'
          AND (extras @> '[{"siren": "$siren"}]')
          AND timestamp >= '$from_date'
          AND timestamp < '$to_date'
      )
    SELECT
      entity,
      siren,
      code,
      station,
      sum(energy) / 1000. AS energy_mwh
    FROM
      energy_over_period
    GROUP BY
      entity,
      siren,
      code,
      station
    ORDER BY
      siren,
      code,
      station
    """
    
)
```

```python
import os
from datetime import date

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

indicators_engine = create_engine("postgresql+psycopg://qualicharge:pass@postgresql:5432/qualicharge-indicators")
api_engine = create_engine(os.getenv("DATABASE_URL"))
```

```python
with Session(api_engine) as session:
    results = session.execute(
        text(
            """
            SELECT DISTINCT
              siren_amenageur
            FROM
              Amenageur
            ORDER BY
              siren_amenageur
            """
        )
    )
sirens = [row[0] for row in results.all()]
sirens
```

```python
with Session(engine) as session:
    energies = pd.read_sql_query(
        ENERGY_BY_STATION_TEMPLATE.substitute(
            {
                "environment": "development",
                "siren": "524335262",
                "from_date": date(2024, 12, 1),
                "to_date": date(2025, 1, 1),
            }
        ),
        con=session.connection(),
    )
energies
```

```python
from_date = date(2024, 12, 1)
to_date = date(2025, 1, 1)
with Session(engine) as session:
    energies = pd.read_sql_query(
        ENERGY_BY_STATION_TEMPLATE.substitute(
            {
                "environment": "development",
                "siren": "524335262",
                "from_date": from_date,
                "to_date": to_date,
            }
        ),
        con=session.connection(),
    )
energies["from"] = from_date 
energies["to"] = to_date
energies["is_controlled"] = False
energies.rename(columns={"station": "id", "energy_mwh": "energy"}, inplace=True)
energies
```

```python
by_index = energies.set_index(["entity", "siren", "code", "from", "to", "id"])
by_index
```

```python
payload = []
by_entity = energies.groupby(["entity", "siren"])
for entity_group in by_entity.groups:
    entity, siren = entity_group
    entity_payload = {
        "entity": entity,
        "siren": siren,
        "operational_units": []
    }
    by_code = by_entity.get_group(group).groupby(["code", "from", "to"])
    for code_group in by_code.groups:
        code, from_, to_ = code_group
        by_stations = by_code.get_group(code_group)
        code_payload = {
            "code": code,
            "from": str(from_),
            "to": str(to_),
            "stations": by_stations[["id", "energy", "is_controlled"]].to_dict(orient="records")
        }
        entity_payload["operational_units"].append(code_payload)
    payload.append(entity_payload)
payload
```

```python
import json

json.dumps(payload)
```

```python
energies["energy"].sum()
```

```python

```

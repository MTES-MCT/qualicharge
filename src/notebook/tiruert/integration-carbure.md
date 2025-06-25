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

```python

```

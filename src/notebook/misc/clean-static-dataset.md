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

# Clean static dataset


This notebook aims to clean the statique dataset generated using data7 `v0.6.0` along with qualicharge-api `v0.10.0` database schema. We discovered an issue related to Enum fields representation in database that uses the key and not the corresponding value. Hence exported dataset cannot be imported as we expect enum values in the official Statique data schema.


## Define Enums to fix

```python
from enum import StrEnum

class ImplantationStationEnum(StrEnum):
    """Statique.implantation_station field enum."""

    VOIRIE = "Voirie"
    PARKING_PUBLIC = "Parking public"
    PARKING_PRIVE_USAGE_PUBLIC = "Parking privé à usage public"
    PARKING_PRIVE_CLIENTELE = "Parking privé réservé à la clientèle"
    STATION_RECHARGE_RAPIDE = "Station dédiée à la recharge rapide"


class ConditionAccesEnum(StrEnum):
    """Statique.condition_acces field enum."""

    ACCESS_LIBRE = "Accès libre"
    ACCESS_RESERVE = "Accès réservé"


class AccessibilitePMREnum(StrEnum):
    """Statique.accessibilite_pmr field enum."""

    RESERVE_PMR = "Réservé PMR"
    NON_RESERVE = "Accessible mais non réservé PMR"
    NON_ACCESSIBLE = "Non accessible"
    INCONNUE = "Accessibilité inconnue"


class RaccordementEnum(StrEnum):
    """Statique.raccordement field enum."""

    DIRECT = "Direct"
    INDIRECT = "Indirect"

enum_to_replace = []
enum_value = []

for enm in (ImplantationStationEnum, ConditionAccesEnum, AccessibilitePMREnum, RaccordementEnum):
    for k in enm:
        enum_to_replace.append(str(k.name))
        enum_value.append(k.value)

print(f"{enum_to_replace=}")
print(f"{enum_value=}")
```

## Load dataset

```python
import pandas as pd

static = pd.read_parquet("../../data/statiques.parquet")
static
```

## Fix column names

```python
fixed = static.rename(columns={"coordonneesxy": "coordonneesXY"})
fixed.columns
```

## Fix enums representation

```python
fixed = fixed.replace(to_replace=enum_to_replace, value=enum_value)
fixed
```

## Save to json

```python
fixed.to_json("../../data/irve-statique.json.gz", orient="records", lines=True, compression="gzip")
```

```python
fixed.to_parquet("../../data/irve-statique.parquet", compression="gzip")
```

```python

```

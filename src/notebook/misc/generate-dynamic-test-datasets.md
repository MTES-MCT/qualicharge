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

<!-- #region -->
# Generate dynamic test datasets

The aim of this notebook is to create a realistic test dataset for dynamic data (sessions + statuses).

## Step 1 - Get data from the staging database

The first step is to download the latest Staging database backup from [Scalingo](https://dashboard.scalingo.com/apps/osc-fr1/qualicharge-api/db/postgresql/backups/list) and save this file to the `data/` directory of the QualiCharge project. Once done, we extract dynamic data.

In order to extract sessions, run the following command:

```sh
cat data/dump.pgsql | \
  bin/compose exec -T postgresql pg_restore -t session -a -f - \
  > data/dump-sessions.sql
```

For statuses, run the following command:

```sh
cat data/dump.pgsql | \
  bin/compose exec -T postgresql pg_restore -t status -a -f - \
  > data/dump-statuses.sql
```
<!-- #endregion -->

<!-- #region -->
## Step 2 - Convert SQL data to TSV

Convert to tsv the original SQL dump for sessions:

```sh
sed -n -e '/COPY/,$p' data/dump-sessions.sql | \
  sed 's/.*(\(.*\)).*/\1/' | \
  sed "s/, /\\t/g" | \
  head -n -7 \
  > data/dump-sessions.tsv
```

> The previous shell command will print each rows after the `COPY` SQL statement (which contains table columns data separated by a tab) and get the column names also separated by a tab. The last 7 lines are removed.

Apply the same command for statuses:

```sh
sed -n -e '/COPY/,$p' data/dump-statuses.sql | \
  sed 's/.*(\(.*\)).*/\1/' | \
  sed "s/, /\\t/g" | \
  head -n -7 \
  > data/dump-statuses.tsv
```
<!-- #endregion -->

## Step 3 - Sample data

The original dataset is too big for testing (> 3M rows for statuses). We will retain only 10% of the original dataset.

### Sessions

```python
import pandas as pd

sessions = pd.read_csv("../../../data/dump-sessions.tsv", sep="\t", dtype_backend="pyarrow")

# Fix dates
sessions["start"] = pd.to_datetime(sessions["start"], format='ISO8601')
sessions["end"] = pd.to_datetime(sessions["end"], format='ISO8601')
sessions
```

```python
# Remove ID column
sessions.drop(["id", "created_at", "updated_at"], axis=1, inplace=True)
sessions
```

```python
# Only keep 10% of original data
frac = 0.1
sessions_sample = sessions.sample(frac=frac, axis=0).reset_index()
sessions_sample.drop("index", axis=1, inplace=True)
sessions_sample
```

### Statuses

```python
statuses = pd.read_csv("../../../data/dump-statuses.tsv", sep="\t", dtype_backend="pyarrow")

# Fix dates
statuses["horodatage"] = pd.to_datetime(statuses["horodatage"], format='ISO8601')
statuses
```

```python
# Remove useless columns
statuses = statuses.drop(["id", "created_at", "updated_at"], axis=1)

# Set NA
statuses = statuses.replace("\\N", pd.NA)
statuses
```

```python
from enum import StrEnum

# Fix Enum values
class EtatPDCEnum(StrEnum):
    """Status.etat_pdc field enum."""

    EN_SERVICE = "en_service"
    HORS_SERVICE = "hors_service"
    INCONNU = "inconnu"


class OccupationPDCEnum(StrEnum):
    """Status.occupation_pdc field enum."""

    LIBRE = "libre"
    OCCUPE = "occupe"
    RESERVE = "reserve"
    INCONNU = "inconnu"


class EtatPriseEnum(StrEnum):
    """Status.etat_prise_* fields enum."""

    FONCTIONNEL = "fonctionnel"
    HORS_SERVICE = "hors_service"
    INCONNU = "inconnu"


enum_to_replace = []
enum_value = []

for enm in (EtatPDCEnum, OccupationPDCEnum, EtatPriseEnum):
    for k in enm:
        enum_to_replace.append(str(k.name))
        enum_value.append(k.value)
        
statuses = statuses.replace(to_replace=enum_to_replace, value=enum_value)
statuses
```

```python
# Only keep 10% of original data
frac = 0.1
statuses_sample = statuses.sample(frac=frac, axis=0).reset_index()
statuses_sample.drop("index", axis=1, inplace=True)
statuses_sample
```

## Mutate samples for static test dataset

The next step will assign statuses and sessions for the static dataset.

### Load static dataset to get `id_pdc_itinerance`

```python
static = pd.read_json(
    "../../../data/irve-statique.json.gz", 
    lines=True,
    orient="records",
    engine="pyarrow",
    dtype_backend="pyarrow"
)
static
```

```python
# Get all PDC ids
pdc_ids = pd.concat([statuses_sample["point_de_charge_id"], sessions_sample["point_de_charge_id"]], ignore_index=True).unique()

# Establish the corresponding table between "point_de_charge_id" and "id_pdc_itinerance"
corr_table = pd.DataFrame()
corr_table["point_de_charge_id"] = pdc_ids
corr_table["id_pdc_itinerance"] = static["id_pdc_itinerance"].sample(n=pdc_ids.size, axis=0, ignore_index=True)
corr_table
```

```python
values = corr_table.set_index("point_de_charge_id").to_dict()
values["id_pdc_itinerance"]
```

### Join sessions with statique data

```python
# Substitute point_de_charge_id by id_pdc_itinerance
sessions_sample.replace(values["id_pdc_itinerance"], inplace=True)
sessions_sample.rename(columns={"point_de_charge_id": "id_pdc_itinerance"}, inplace=True)
sessions_sample
```

```python
# Save to json
sessions_sample.to_json("../../../data/irve-dynamique-sessions.json.gz", orient="records", lines=True)
```

### Join statuses with statique data

```python
# Substitute point_de_charge_id by id_pdc_itinerance
statuses_sample.replace(values["id_pdc_itinerance"], inplace=True)
statuses_sample.rename(columns={"point_de_charge_id": "id_pdc_itinerance"}, inplace=True)
statuses_sample
```

```python
# Save to json
statuses_sample.to_json("../../../data/irve-dynamique-statuses.json.gz", orient="records", lines=True)
```

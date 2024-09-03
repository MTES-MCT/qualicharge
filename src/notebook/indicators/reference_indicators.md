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

<!-- #region editable=true slideshow={"slide_type": ""} -->
# Indicateurs QualiCharge : Structure

Ce Notebook présente une proposition de structuration et de représentation des indicateurs Qualicharge sous forme de requêtes SQL construites à partir d'une codification des indicateurs.

La liste des indicateurs est présentée sur [ce lien](https://loco-philippe.github.io/IRVE/files/indicateurs.html).

*Nota : La représentation visuelle des indicateurs (ex. diagramme circulaire, diagramme à barre, carte choroplèthe, courbe...) n'est pas abordée.*
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
import os
import pandas as pd
from sqlalchemy import create_engine

# Connecteur à la base Qualicharge
engine = create_engine(os.getenv("DATABASE_URL"))

TABLE = {'00': 'national', '01': 'region', '02': 'department', '03': 'epci', '04': 'city'}
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
## Structure des indicateurs
<!-- #endregion -->

<!-- #region -->
### Codification des indicateurs

Les indicateurs sont codifiés par une chaine de caractères *[type]-[périmètre]-[valeur de périmètre]-[critère]* avec :

- *type* : identifiant du type d'indicateur (ex. 'i1' : nombre de points de recharge)
- *périmètre et valeur de périmètre*: sous ensemble des données sur lequel appliquer l'indicateur. Les périmètres actuellement définis sont les suivants :
  - 00: national (sans valeur)
  - 01: région (valeur : code de la région)
  - 02: département (valeur : code du département)
  - 03: EPCI (valeur : code de l'EPCI)
  - 04: commune (valeur : code de la commune)
- *critère* : paramètre spécifique du type d'indicateur

Le périmètre par défaut est l'ensemble des données.


Exemples de codification :
- **t4-04-74012** : Pourcentage de stations par nombre de points de recharge (t4) pour la ville (04) d'Annemasse (74012)
- **i1-01-93** : Nombre de points de recharge (i1) pour la région (01) PACA (93)
- **i1-01-93-03** : Nombre de points de recharge (i1) pour la région (01) PACA (93) par EPCI (03)
- **t1** : Nombre de points de recharge par niveau de puissance (t1) pour l'ensemble des données (pas de périmètre choisi)

<!-- #endregion -->

### Exemples de mise en oeuvre


'i1' est l'indicateur qui fournit le nombre de points de recharge.

Les colonnes de gauche sont les valeurs calculées liées à l'indicateur (ici 'nb_pdc').

Les colonnes de droites sont des données complémentaires:

- 'level' indique le type de périmètre et 'code' indique la valeur pour ce périmètre,
- 'name' est une information optionnelle décrivant le 'code'

*Nota : L'appartenance à une zone géographique se fait par le test d'appartenance d'un point à un polygone (impact sur le temps de calcul de certains indicateurs).*


#### Ensemble des données

La codification est 'i1-00-00' (ou bien 'i1')

Le résultat est le suivant :

| nb_pdc | level |code|
|--------|-------|----|
| 13400	 | 00	 | 00 |



#### Ensemble des données avec une répartition par région (01)

La codification est 'i1-00-00-01' (ou bien 'i1---01')

Le résultat est le suivant :

| nb_pdc | level | code |
| :----- | :---- | :--- |
| 3538   | 01    | 84   |
| 2351   | 01    | 93   |
| 1391   | 01    | 11   |
| 1082   | 01    | 44   |
| 1027   | 01    | 75   |

*ex. ligne 1 : 'level' 01 indique un périmètre région, 'code' 84 indique le code de la région.*


#### Région (01) PACA (93)

La codification est 'i1-01-93' (équivalent à 'i1-01-93-00')

Le résultat est le suivant :

| nb_pdc | level |code|
|--------|-------|----|
| 2351	 | 01	 | 93 |



#### Région (1) PACA (93) par département (02)

La codification est 'i1-01-93-02'

Le résultat est le suivant :

| nb_pdc | level | code |
| :----- | :---- | :--- |
| 782    | 02    | 83   |
| 668    | 02    | 06   |
| 268    | 02    | 13   |
| 262    | 02    | 05   |
| 214    | 02    | 84   |
| 157    | 02    | 04   |


<!-- #region editable=true slideshow={"slide_type": ""} -->
## Présentation des indicateurs

Les sections suivantes présentent pour chaque indicateur :
- les valurs calculées pour l'indicateur,
- pour chacune des configurations:
    - la structure de la requête,
    - le résultat de la requête,
    - un exemple de requête

Les requêtes sont issues d'un [générateur de requêtes](../misc/create_query.py). Les exemples de générations sont présentés dans un [notebook spécifique](../misc/create_indicators.md)
<!-- #endregion -->

## Infrastructure - quantitatif

Indicateurs pris en compte : 'i1', 'i4', 'i7'

Les autres indicateurs sont dérivés ('i2', 'i5', 'i8' ramené à 100 000 habitants et 'i3', 'i6', 'i9' ramené à 100 km2).

<!-- #region editable=true slideshow={"slide_type": ""} -->
### I1 : Nombre de points de recharge ouverts au public

'nb_pdc' est le nombre de points de recharge.
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête globale : 'i1-00-00' ou 'i1'

perim = '00'
val   = '00'
zone  = '00'

query = f""" 
    WITH  national(code) AS (VALUES ('{perim}')) , perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT count(id_pdc_itinerance) AS nb_pdc, level , code  
    FROM perim_zon, pointdecharge, national
    GROUP BY level , code"""

# résultat
pd.read_sql_query(query, engine.connect())
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 'i1'

```sql
WITH
  NATIONAL (code) AS (
    VALUES
      ('00')
  ),
  perim_zon (LEVEL) AS (
    VALUES
      ('00')
  )
SELECT
  count(id_pdc_itinerance) AS nb_pdc,
  LEVEL,
  code
FROM
  perim_zon,
  pointdecharge,
  NATIONAL
GROUP BY
  LEVEL,
  code
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête globale avec critère : 

# ex. globale avec une répartition par région (01) 'i1-00-00-01' ou 'i1---01'
perim = '00'
val   = '00'
zone  = '01'

query = f""" 
    WITH national(code) AS (VALUES ('{perim}')) , perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT count(id_pdc_itinerance) AS nb_pdc, level , code  
    FROM perim_zon, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id  LEFT JOIN region ON ST_Within("coordonneesXY", geometry) 
    GROUP BY level , code  ORDER BY nb_pdc DESC"""

# résultat
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 'i1-00-00-01'

```sql
WITH
  NATIONAL (code) AS (
    VALUES
      ('00')
  ),
  perim_zon (LEVEL) AS (
    VALUES
      ('01')
  )
SELECT
  count(id_pdc_itinerance) AS nb_pdc,
  LEVEL,
  code
FROM
  perim_zon,
  pointdecharge
  LEFT JOIN station ON station.id = station_id
  LEFT JOIN localisation ON localisation_id = localisation.id
  LEFT JOIN region ON ST_Within ("coordonneesXY", geometry)
GROUP BY
  LEVEL,
  code
ORDER BY
  nb_pdc DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête locale : 

# ex. sur la région (01) PACA (93) 'i1-01-93-00' ou 'i1-01-93'
perim = '01'
val   = '93'
zone  = '00'

query = f""" 
    WITH pdc_loc AS (SELECT id_pdc_itinerance, "coordonneesXY"
                     FROM {TABLE[perim]}, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id 
                     WHERE  code = '{val}' AND ST_Within("coordonneesXY", geometry) ), perimeter(level) AS (VALUES ('{perim}')) , perim_zon(code) AS (VALUES ('{val}')) 
    SELECT count(id_pdc_itinerance) AS nb_pdc, level, code
    FROM perimeter, perim_zon, pdc_loc
    GROUP BY level, code ORDER BY nb_pdc DESC"""

# résultat
pd.read_sql_query(query, engine.connect())
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 'i1-01-93-00'

```sql
WITH
  pdc_loc AS (
    SELECT
      id_pdc_itinerance,
      "coordonneesXY"
    FROM
      region,
      pointdecharge
      LEFT JOIN station ON station.id = station_id
      LEFT JOIN localisation ON localisation_id = localisation.id
    WHERE
      code = '93'
      AND ST_Within ("coordonneesXY", geometry)
  ),
  perimeter (LEVEL) AS (
    VALUES
      ('01')
  ),
  perim_zon (code) AS (
    VALUES
      ('93')
  )
SELECT
  count(id_pdc_itinerance) AS nb_pdc,
  LEVEL,
  code
FROM
  perimeter,
  perim_zon,
  pdc_loc
GROUP BY
  LEVEL,
  code
ORDER BY
  nb_pdc DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête locale avec critère : 

# ex. sur la région (01) PACA (93) par département (02) 'i1-01-93-02'
perim = '01'
val   = '93'
zone  = '03'

query = f""" 
    WITH pdc_loc AS (SELECT id_pdc_itinerance, "coordonneesXY"
                            FROM {TABLE[perim]}, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id 
                            WHERE  code = '{val}' AND ST_Within("coordonneesXY", geometry) ), perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT count(id_pdc_itinerance) AS nb_pdc, level , code 
    FROM perim_zon, pdc_loc LEFT JOIN {TABLE[zone]} ON ST_Within("coordonneesXY", geometry) 
    GROUP BY level , code  ORDER BY nb_pdc DESC"""

# résultat
pd.read_sql_query(query, engine.connect())
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 'i1-01-93-02'

```sql
WITH
  pdc_loc AS (
    SELECT
      id_pdc_itinerance,
      "coordonneesXY"
    FROM
      region,
      pointdecharge
      LEFT JOIN station ON station.id = station_id
      LEFT JOIN localisation ON localisation_id = localisation.id
    WHERE
      code = '93'
      AND ST_Within ("coordonneesXY", geometry)
  ),
  perim_zon (LEVEL) AS (
    VALUES
      ('02')
  )
SELECT
  count(id_pdc_itinerance) AS nb_pdc,
  LEVEL,
  code
FROM
  perim_zon,
  pdc_loc
  LEFT JOIN department ON ST_Within ("coordonneesXY", geometry)
GROUP BY
  LEVEL,
  code
ORDER BY
  nb_pdc DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
### I4 : Nombre de stations ouvertes au public

'nb_stat' est le nombre de stations.
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête globale : 'i4-00-00' ou 'i4'

perim = '00'
val   = '00'
zone  = '00'

query = f""" 
    WITH  national(code) AS (VALUES ('{perim}')) , perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT count(id_station_itinerance) AS nb_stat, level , code  
    FROM perim_zon, station, {TABLE[perim]}
    GROUP BY level , code"""

# résultat
pd.read_sql_query(query, engine.connect())
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 'i4'

```sql
WITH
  NATIONAL (code) AS (
    VALUES
      ('00')
  ),
  perim_zon (LEVEL) AS (
    VALUES
      ('00')
  )
SELECT
  count(id_station_itinerance) AS nb_stat,
  LEVEL,
  code
FROM
  perim_zon,
  station,
  NATIONAL
GROUP BY
  LEVEL,
  code
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête globale avec critère : 

# ex. globale avec une répartition par région (01) 'i4-00-00-01' ou 'i4---01'
perim = '00'
val   = '00'
zone  = '01'

query = f""" 
    WITH national(code) AS (VALUES ('{perim}')) , perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT count(id_station_itinerance) AS nb_stat, level , code  
    FROM perim_zon, station LEFT JOIN localisation ON localisation_id = localisation.id  LEFT JOIN {TABLE[zone]} ON ST_Within("coordonneesXY", geometry) 
    GROUP BY level , code  ORDER BY nb_stat DESC"""

# résultat
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 'i4-00-00-01'

```sql
WITH
  NATIONAL (code) AS (
    VALUES
      ('00')
  ),
  perim_zon (LEVEL) AS (
    VALUES
      ('01')
  )
SELECT
  count(id_station_itinerance) AS nb_stat,
  LEVEL,
  code
FROM
  perim_zon,
  station
  LEFT JOIN localisation ON localisation_id = localisation.id
  LEFT JOIN region ON ST_Within ("coordonneesXY", geometry)
GROUP BY
  LEVEL,
  code
ORDER BY
  nb_stat DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête locale : 

# ex. sur la région (01) PACA (93) 'i4-01-93-00' ou 'i4-01-93'
perim = '01'
val   = '93'
zone  = '00'

query = f""" 
    WITH stat_loc AS (SELECT id_station_itinerance, "coordonneesXY"
                      FROM {TABLE[perim]}, station LEFT JOIN localisation ON localisation_id = localisation.id 
                      WHERE  code = '{val}' AND ST_Within("coordonneesXY", geometry) ), perimeter(level) AS (VALUES ('{perim}')) , perim_zon(code) AS (VALUES ('{val}')) 
    SELECT count(id_station_itinerance) AS nb_stat, level, code
    FROM perimeter, perim_zon, stat_loc
    GROUP BY level, code ORDER BY nb_stat DESC"""

# résultat
pd.read_sql_query(query, engine.connect())
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 'i4-01-93-00'

```sql
WITH
  stat_loc AS (
    SELECT
      id_station_itinerance,
      "coordonneesXY"
    FROM
      region,
      station
      LEFT JOIN localisation ON localisation_id = localisation.id
    WHERE
      code = '93'
      AND ST_Within ("coordonneesXY", geometry)
  ),
  perimeter (LEVEL) AS (
    VALUES
      ('01')
  ),
  perim_zon (code) AS (
    VALUES
      ('93')
  )
SELECT
  count(id_station_itinerance) AS nb_stat,
  LEVEL,
  code
FROM
  perimeter,
  perim_zon,
  stat_loc
GROUP BY
  LEVEL,
  code
ORDER BY
  nb_stat DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête locale avec critère : 

# ex. sur la région (01) PACA (93) par EPCI (03) 'i4-01-93-03'
perim = '01'
val   = '93'
zone  = '03'

query = f""" 
    WITH stat_loc AS (SELECT id_station_itinerance, "coordonneesXY"
                      FROM {TABLE[perim]}, station LEFT JOIN localisation ON localisation_id = localisation.id 
                      WHERE  code = '{val}' AND ST_Within("coordonneesXY", geometry) ), perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT count(id_station_itinerance) AS nb_stat, level , code 
    FROM perim_zon, stat_loc LEFT JOIN {TABLE[zone]} ON ST_Within("coordonneesXY", geometry) 
    GROUP BY level , code  ORDER BY nb_stat DESC"""

# résultat
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 'i4-01-93-03'

```sql
WITH
  stat_loc AS (
    SELECT
      id_station_itinerance,
      "coordonneesXY"
    FROM
      region,
      station
      LEFT JOIN localisation ON localisation_id = localisation.id
    WHERE
      code = '93'
      AND ST_Within ("coordonneesXY", geometry)
  ),
  perim_zon (LEVEL) AS (
    VALUES
      ('03')
  )
SELECT
  count(id_station_itinerance) AS nb_stat,
  LEVEL,
  code
FROM
  perim_zon,
  stat_loc
  LEFT JOIN epci ON ST_Within ("coordonneesXY", geometry)
GROUP BY
  LEVEL,
  code
ORDER BY
  nb_stat DESC
```
<!-- #endregion -->

### I7 : Puissance installée

'p_nom' est la puissance nominale cumulée

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête globale : 'i7-00-00' ou 'i7'

perim = '00'
val   = '00'
zone  = '00'

query = f""" 
    WITH  national(code) AS (VALUES ('{perim}')) , perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT count(id_station_itinerance) AS nb_stat, level , code  
    FROM perim_zon, station, {TABLE[perim]}
    GROUP BY level , code"""

# résultat
pd.read_sql_query(query, engine.connect())
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 'i7'

```sql
WITH
  NATIONAL (code) AS (
    VALUES
      ('00')
  ),
  perim_zon (LEVEL) AS (
    VALUES
      ('00')
  )
SELECT
  sum(puissance_nominale) AS p_nom,
  LEVEL,
  code
FROM
  perim_zon,
  pointdecharge,
  NATIONAL
GROUP BY
  LEVEL,
  code
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête globale avec critère : 

# ex. globale avec une répartition par région (01) 'i7-00-00-01' ou 'i7---01'
perim = '00'
val   = '00'
zone  = '01'

query = f""" 
    WITH national(code) AS (VALUES ('{perim}')) , perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT sum(puissance_nominale) AS p_nom, level , code  
    FROM perim_zon, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id  LEFT JOIN {TABLE[zone]} ON ST_Within("coordonneesXY", geometry) 
    GROUP BY level , code  ORDER BY p_nom DESC """

# résultat
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 'i7-00-00-01'

```sql
WITH
  NATIONAL (code) AS (
    VALUES
      ('00')
  ),
  perim_zon (LEVEL) AS (
    VALUES
      ('01')
  )
SELECT
  sum(puissance_nominale) AS p_nom,
  LEVEL,
  code
FROM
  perim_zon,
  pointdecharge
  LEFT JOIN station ON station.id = station_id
  LEFT JOIN localisation ON localisation_id = localisation.id
  LEFT JOIN region ON ST_Within ("coordonneesXY", geometry)
GROUP BY
  LEVEL,
  code
ORDER BY
  p_nom DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête locale : 

# ex. sur la région (01) PACA (93) 'i7-01-93-00' ou 'i7-01-93'
perim = '01'
val   = '93'
zone  = '00'

query = f""" 
    WITH pnom_loc AS (SELECT puissance_nominale, "coordonneesXY"
                   FROM {TABLE[perim]}, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id 
                   WHERE  code = '{val}' AND ST_Within("coordonneesXY", geometry) ), perimeter(level) AS (VALUES ('{perim}')) , perim_zon(code) AS (VALUES ('{val}')) 
    SELECT sum(puissance_nominale) AS p_nom, level, code
    FROM perimeter, perim_zon, pnom_loc
    GROUP BY level, code ORDER BY p_nom DESC"""

# résultat
pd.read_sql_query(query, engine.connect())
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 'i7-01-93-00'

```sql
WITH
  pnom_loc AS (
    SELECT
      puissance_nominale,
      "coordonneesXY"
    FROM
      region,
      pointdecharge
      LEFT JOIN station ON station.id = station_id
      LEFT JOIN localisation ON localisation_id = localisation.id
    WHERE
      code = '93'
      AND ST_Within ("coordonneesXY", geometry)
  ),
  perimeter (LEVEL) AS (
    VALUES
      ('01')
  ),
  perim_zon (code) AS (
    VALUES
      ('93')
  )
SELECT
  sum(puissance_nominale) AS p_nom,
  LEVEL,
  code
FROM
  perimeter,
  perim_zon,
  pnom_loc
GROUP BY
  LEVEL,
  code
ORDER BY
  p_nom DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête locale avec critère : 

# ex. sur la région (01) PACA (93) par department (04) 'i7-01-93-04'
perim = '01'
val   = '93'
zone  = '04'

query = f""" 
        WITH pnom_loc AS (SELECT puissance_nominale, "coordonneesXY"
                   FROM {TABLE[perim]}, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id 
                   WHERE  code = '{val}' AND ST_Within("coordonneesXY", geometry) ), perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT sum(puissance_nominale) AS p_nom, level , code 
    FROM perim_zon, pnom_loc LEFT JOIN {TABLE[zone]} ON ST_Within("coordonneesXY", geometry) 
    GROUP BY level , code  ORDER BY p_nom DESC"""

# résultat
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 'i7-01-93-04'

```sql
WITH
  pnom_loc AS (
    SELECT
      puissance_nominale,
      "coordonneesXY"
    FROM
      region,
      pointdecharge
      LEFT JOIN station ON station.id = station_id
      LEFT JOIN localisation ON localisation_id = localisation.id
    WHERE
      code = '93'
      AND ST_Within ("coordonneesXY", geometry)
  ),
  perim_zon (LEVEL) AS (
    VALUES
      ('04')
  )
SELECT
  sum(puissance_nominale) AS p_nom,
  LEVEL,
  code
FROM
  perim_zon,
  pnom_loc
  LEFT JOIN city ON ST_Within ("coordonneesXY", geometry)
GROUP BY
  LEVEL,
  code
ORDER BY
  p_nom DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
## Infrastructure - typologie

Les indicateurs 't1' à 't6' sont pris en compte.

L'indicateur 't7' reste à construire (non prioritaire).

Les autres indicateurs sont à définir (
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
### T1 : Nombre de points de recharge par niveau de puissance

'nb_pdc' est le nombre de points de recharge.

'p-range' est la plage de puissance (ex. [65, 175) -> de 65 inclus à 175 exclus)

'p-cat' est l'index de la catégorie (1 pour la catégorie la plus basse)
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête globale : 't1-00-00' ou 't1'

perim = '00'
zone  = '00'

query = f"""
    WITH puissance(p_range, p_cat) AS ( VALUES (numrange(0, 15.0), 1), (numrange(15.0, 26.0), 2), (numrange(26, 65.0), 3), (numrange(65, 175.0), 4), (numrange(175, 360.0), 5), (numrange(360, NULL), 6)) , 
         national(code) AS (VALUES ('{perim}')) , perimeter(level) AS (VALUES ('{perim}')) 
    SELECT count(id_pdc_itinerance) AS nb_pdc, p_cat, p_range, level, code 
    FROM perimeter, pointdecharge LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range , {TABLE[perim]}
    GROUP BY p_cat, p_range, level, code  ORDER BY nb_pdc DESC
"""

# résultat
pd.read_sql_query(query, engine.connect())
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 't1'

```sql
WITH
  puissance (p_range, p_cat) AS (
    VALUES
      (numrange (0, 15.0), 1),
      (numrange (15.0, 26.0), 2),
      (numrange (26, 65.0), 3),
      (numrange (65, 175.0), 4),
      (numrange (175, 360.0), 5),
      (numrange (360, NULL), 6)
  ),
  NATIONAL (code) AS (
    VALUES
      ('00')
  ),
  perimeter (LEVEL) AS (
    VALUES
      ('00')
  )
SELECT
  count(id_pdc_itinerance) AS nb_pdc,
  p_cat,
  p_range,
  LEVEL,
  code
FROM
  perimeter,
  pointdecharge
  LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range,
  NATIONAL
GROUP BY
  p_cat,
  p_range,
  LEVEL,
  code
ORDER BY
  nb_pdc DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête locale : 

# ex. sur la département (02) paris (75) 't1-02-75'
perim = '02'
zone  = '75'

query = f""" 
    WITH puissance(p_range, p_cat) AS ( VALUES (numrange(0, 15.0), 1), (numrange(15.0, 26.0), 2), (numrange(26, 65.0), 3), (numrange(65, 175.0), 4), (numrange(175, 360.0), 5), (numrange(360, NULL), 6)) , 
         perimeter(level) AS (VALUES ('{perim}')) 
    SELECT count(id_pdc_itinerance) AS nb_pdc, p_cat, p_range, level, code 
    FROM perimeter, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id  LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range , {TABLE[perim]}
    WHERE code = '{zone}' AND ST_Within("coordonneesXY", geometry) 
    GROUP BY p_cat, p_range, level, code  ORDER BY nb_pdc DESC
    """

# résultat
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region -->
Exemple requête : 't1-02-75'

```sql
WITH
  puissance (p_range, p_cat) AS (
    VALUES
      (numrange (0, 15.0), 1),
      (numrange (15.0, 26.0), 2),
      (numrange (26, 65.0), 3),
      (numrange (65, 175.0), 4),
      (numrange (175, 360.0), 5),
      (numrange (360, NULL), 6)
  ),
  perimeter (LEVEL) AS (
    VALUES
      ('02')
  )
SELECT
  count(id_pdc_itinerance) AS nb_pdc,
  p_cat,
  p_range,
  LEVEL,
  code
FROM
  perimeter,
  pointdecharge
  LEFT JOIN station ON station.id = station_id
  LEFT JOIN localisation ON localisation_id = localisation.id
  LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range,
  department
WHERE
  code = '75'
  AND ST_Within ("coordonneesXY", geometry)
GROUP BY
  p_cat,
  p_range,
  LEVEL,
  code
ORDER BY
  nb_pdc DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
### T2 : Pourcentage de points de recharge par niveau de puissance

Indicateur similaire à 't1' ( 'pct_nb_pdc' remplace 'nb_pdc').

'pct_nb_pdc' est le pourcentage de pdc pour le niveau de puissance.
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête globale : 't2-00-00' ou 't2'

perim = '00'
zone  = '00'

query = f"""
    WITH t1 AS (
        WITH puissance(p_range, p_cat) AS ( VALUES (numrange(0, 15.0), 1), (numrange(15.0, 26.0), 2), (numrange(26, 65.0), 3), (numrange(65, 175.0), 4), (numrange(175, 360.0), 5), (numrange(360, NULL), 6)) , 
             national(code) AS (VALUES ('{perim}')) , perimeter(level) AS (VALUES ('{perim}')) 
        SELECT count(id_pdc_itinerance) AS nb_pdc, p_cat, p_range, level, code 
        FROM perimeter, pointdecharge LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range , {TABLE[perim]}
        GROUP BY p_cat, p_range, level, code  ORDER BY nb_pdc DESC)
    SELECT nb_pdc / (SELECT sum(nb_pdc) FROM t1) * 100 AS pct_nb_pdc, p_cat, p_range, level, code 
    FROM t1
"""

# résultat
pd.read_sql_query(query, engine.connect())
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 't2'

```sql
WITH
  t1 AS (
    WITH
      puissance (p_range, p_cat) AS (
        VALUES
          (numrange (0, 15.0), 1),
          (numrange (15.0, 26.0), 2),
          (numrange (26, 65.0), 3),
          (numrange (65, 175.0), 4),
          (numrange (175, 360.0), 5),
          (numrange (360, NULL), 6)
      ),
      NATIONAL (code) AS (
        VALUES
          ('00')
      ),
      perimeter (LEVEL) AS (
        VALUES
          ('00')
      )
    SELECT
      count(id_pdc_itinerance) AS nb_pdc,
      p_cat,
      p_range,
      LEVEL,
      code
    FROM
      perimeter,
      pointdecharge
      LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range,
      NATIONAL
    GROUP BY
      p_cat,
      p_range,
      LEVEL,
      code
    ORDER BY
      nb_pdc DESC
  )
SELECT
  nb_pdc / (
    SELECT
      sum(nb_pdc)
    FROM
      t1
  ) * 100 AS pct_nb_pdc,
  p_cat,
  p_range,
  LEVEL,
  code
FROM
  t1
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête locale : 

# ex. sur la département (02) paris (75) 't2-02-75'
perim = '02'
zone  = '75'

query = f""" 
    WITH t1 AS (
        WITH puissance(p_range, p_cat) AS ( VALUES (numrange(0, 15.0), 1), (numrange(15.0, 26.0), 2), (numrange(26, 65.0), 3), (numrange(65, 175.0), 4), (numrange(175, 360.0), 5), (numrange(360, NULL), 6)) , 
             perimeter(level) AS (VALUES ('{perim}')) 
        SELECT count(id_pdc_itinerance) AS nb_pdc, p_cat, p_range, level, code 
        FROM perimeter, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id  LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range , {TABLE[perim]}
        WHERE code = '{zone}' AND ST_Within("coordonneesXY", geometry) 
        GROUP BY p_cat, p_range, level, code  ORDER BY nb_pdc DESC)
    SELECT nb_pdc / (SELECT sum(nb_pdc) FROM t1) * 100 AS pct_nb_pdc, p_cat, p_range, level, code 
    FROM t1
    """

# résultat
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête 't2-02-75' :

```sql
WITH
  t1 AS (
    WITH
      puissance (p_range, p_cat) AS (
        VALUES
          (numrange (0, 15.0), 1),
          (numrange (15.0, 26.0), 2),
          (numrange (26, 65.0), 3),
          (numrange (65, 175.0), 4),
          (numrange (175, 360.0), 5),
          (numrange (360, NULL), 6)
      ),
      perimeter (LEVEL) AS (
        VALUES
          ('02')
      )
    SELECT
      count(id_pdc_itinerance) AS nb_pdc,
      p_cat,
      p_range,
      LEVEL,
      code
    FROM
      perimeter,
      pointdecharge
      LEFT JOIN station ON station.id = station_id
      LEFT JOIN localisation ON localisation_id = localisation.id
      LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range,
      department
    WHERE
      code = '75'
      AND ST_Within ("coordonneesXY", geometry)
    GROUP BY
      p_cat,
      p_range,
      LEVEL,
      code
    ORDER BY
      nb_pdc DESC
  )
SELECT
  nb_pdc / (
    SELECT
      sum(nb_pdc)
    FROM
      t1
  ) * 100 AS pct_nb_pdc,
  p_cat,
  p_range,
  LEVEL,
  code
FROM
  t1
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
### T3 : Nombre de stations par nombre de points de recharge

'nb_stations' est le nombre de stations.

'nb_pdc' est le nombre de pdc.

ex. il y a 2790 stations (nb_stations) avec un seul pdc (nb_pdc).
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête globale : 't3-00-00' ou 't3'

perim = '00'
zone  = '00'

query = f"""
    WITH stat AS (SELECT count(station_id) AS nb_pdc
            FROM pointdecharge LEFT JOIN station ON station.id = station_id 
            GROUP BY station_id), national(code) AS (VALUES ('{perim}')) , perimeter(level) AS (VALUES ('{perim}')) 
    SELECT count(nb_pdc) AS nb_stations, nb_pdc, level, code 
    FROM perimeter, stat, {TABLE[perim]}
    GROUP BY nb_pdc, level, code  ORDER BY nb_stations DESC
"""

# résultat
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 't3'

```sql
WITH
  stat AS (
    SELECT
      count(station_id) AS nb_pdc
    FROM
      pointdecharge
      LEFT JOIN station ON station.id = station_id
    GROUP BY
      station_id
  ),
  NATIONAL (code) AS (
    VALUES
      ('00')
  ),
  perimeter (LEVEL) AS (
    VALUES
      ('00')
  )
SELECT
  count(nb_pdc) AS nb_stations,
  nb_pdc,
  LEVEL,
  code
FROM
  perimeter,
  stat,
  NATIONAL
GROUP BY
  nb_pdc,
  LEVEL,
  code
ORDER BY
  nb_stations DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête locale : 

# ex. sur la commune (04) d'Annemasse (74012) 't3-04-74012'
perim = '04'
zone  = '74012'

query = f""" 
    WITH stat AS (SELECT count(station_id) AS nb_pdc, code 
            FROM pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id , {TABLE[perim]} 
            WHERE code = '{zone}' AND ST_Within("coordonneesXY", geometry)  GROUP BY station_id, code ), 
        perimeter(level) AS (VALUES ('{perim}')) 
    SELECT count(nb_pdc) AS nb_stations, nb_pdc, level, code 
    FROM perimeter, stat
    GROUP BY nb_pdc, level, code  ORDER BY nb_stations DESC
    """

# résultat
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête 't3-04-74012' :

```sql
WITH
  stat AS (
    SELECT
      count(station_id) AS nb_pdc,
      code
    FROM
      pointdecharge
      LEFT JOIN station ON station.id = station_id
      LEFT JOIN localisation ON localisation_id = localisation.id,
      city
    WHERE
      code = '74012'
      AND ST_Within ("coordonneesXY", geometry)
    GROUP BY
      station_id,
      code
  ),
  perimeter (LEVEL) AS (
    VALUES
      ('04')
  )
SELECT
  count(nb_pdc) AS nb_stations,
  nb_pdc,
  LEVEL,
  code
FROM
  perimeter,
  stat
GROUP BY
  nb_pdc,
  LEVEL,
  code
ORDER BY
  nb_stations DESC
```
<!-- #endregion -->

### T4 : Pourcentage de stations par nombre de points de recharge

Indicateur similaire à 't3' ( 'pct_nb_stations' remplace 'nb_stations').

'pct_nb_stations' est le pourcentage de stations avec un nombre de pdc donné.

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête globale : 't4-00-00' ou 't4'

perim = '00'
zone  = '00'

query = f"""
    WITH t3 AS ( 
        WITH stat AS (SELECT count(station_id) AS nb_pdc
                FROM pointdecharge LEFT JOIN station ON station.id = station_id 
                GROUP BY station_id), national(code) AS (VALUES ('{perim}')) , perimeter(level) AS (VALUES ('{perim}')) 
        SELECT count(nb_pdc) AS nb_stations, nb_pdc, level, code 
        FROM perimeter, stat, {TABLE[perim]}
        GROUP BY nb_pdc, level, code  ORDER BY nb_stations DESC)
    SELECT nb_stations / (SELECT sum(nb_stations) FROM t3) * 100 AS pct_nb_stations, nb_pdc, level, code 
    FROM t3
"""

# résultat
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 't4'

```sql
WITH
  t3 AS (
    WITH
      stat AS (
        SELECT
          count(station_id) AS nb_pdc
        FROM
          pointdecharge
          LEFT JOIN station ON station.id = station_id
        GROUP BY
          station_id
      ),
      NATIONAL (code) AS (
        VALUES
          ('00')
      ),
      perimeter (LEVEL) AS (
        VALUES
          ('00')
      )
    SELECT
      count(nb_pdc) AS nb_stations,
      nb_pdc,
      LEVEL,
      code
    FROM
      perimeter,
      stat,
      NATIONAL
    GROUP BY
      nb_pdc,
      LEVEL,
      code
    ORDER BY
      nb_stations DESC
  )
SELECT
  nb_stations / (
    SELECT
      sum(nb_stations)
    FROM
      t3
  ) * 100 AS pct_nb_stations,
  nb_pdc,
  LEVEL,
  code
FROM
  t3
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête locale : 

# ex. sur la commune (04) annemasse (74012) 't4-04-74012'
perim = '04'
zone  = '74012'

query = f""" 
    WITH t3 AS (
    WITH stat AS (SELECT count(station_id) AS nb_pdc, code 
            FROM pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id , {TABLE[perim]} 
            WHERE code = '{zone}' AND ST_Within("coordonneesXY", geometry)  GROUP BY station_id, code ), 
        perimeter(level) AS (VALUES ('{perim}')) 
    SELECT count(nb_pdc) AS nb_stations, nb_pdc, level, code 
    FROM perimeter, stat
    GROUP BY nb_pdc, level, code  ORDER BY nb_stations DESC)
    SELECT nb_stations / (SELECT sum(nb_stations) FROM t3) * 100 AS pct_nb_stations, nb_pdc, level, code 
    FROM t3
    """

# résultat
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête 't4-04-74012' :

```sql
WITH
  t3 AS (
    WITH
      stat AS (
        SELECT
          count(station_id) AS nb_pdc,
          code
        FROM
          pointdecharge
          LEFT JOIN station ON station.id = station_id
          LEFT JOIN localisation ON localisation_id = localisation.id,
          city
        WHERE
          code = '74012'
          AND ST_Within ("coordonneesXY", geometry)
        GROUP BY
          station_id,
          code
      ),
      perimeter (LEVEL) AS (
        VALUES
          ('04')
      )
    SELECT
      count(nb_pdc) AS nb_stations,
      nb_pdc,
      LEVEL,
      code
    FROM
      perimeter,
      stat
    GROUP BY
      nb_pdc,
      LEVEL,
      code
    ORDER BY
      nb_stations DESC
  )
SELECT
  nb_stations / (
    SELECT
      sum(nb_stations)
    FROM
      t3
  ) * 100 AS pct_nb_stations,
  nb_pdc,
  LEVEL,
  code
FROM
  t3
```
<!-- #endregion -->

### T5 : Nombre de stations par type d’implantation

'nb_stations' est le nombre de stations.

'implantation' est le type d'implantation

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête globale : 't5-00-00' ou 't5'

perim = '00'
zone  = '00'

query = f"""
    WITH national(code) AS (VALUES ('{perim}')) , perimeter(level) AS (VALUES ('{perim}')) 
    SELECT count(id_station_itinerance) AS nb_stations, implantation_station AS implantation, level, code  
    FROM perimeter, station, {TABLE[perim]}
    GROUP BY implantation, level, code  ORDER BY nb_stations DESC
"""
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 't5'

```sql
WITH
  NATIONAL (code) AS (
    VALUES
      ('00')
  ),
  perimeter (LEVEL) AS (
    VALUES
      ('00')
  )
SELECT
  count(id_station_itinerance) AS nb_stations,
  implantation_station AS implantation,
  LEVEL,
  code
FROM
  perimeter,
  station,
  NATIONAL
GROUP BY
  implantation,
  LEVEL,
  code
ORDER BY
  nb_stations DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête locale : 

# ex. sur l'EPCI (03) Métropole Rouen Normandie (200023414) 't5-03-200023414'
perim = '03'
zone  = '200023414'

query = f""" 
    WITH perimeter(level) AS (VALUES ('{perim}')) 
    SELECT count(id_station_itinerance) AS nb_stations, implantation_station AS implantation, level, code 
    FROM perimeter, station LEFT JOIN localisation ON localisation_id = localisation.id , {TABLE[perim]}
    WHERE code = '{zone}' AND ST_Within("coordonneesXY", geometry) 
    GROUP BY implantation, level, code  ORDER BY nb_stations DESC
    """

pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête 't5-03-200023414' :

```sql
WITH
  perimeter (LEVEL) AS (
    VALUES
      ('03')
  )
SELECT
  count(id_station_itinerance) AS nb_stations,
  implantation_station AS implantation,
  LEVEL,
  code
FROM
  perimeter,
  station
  LEFT JOIN localisation ON localisation_id = localisation.id,
  epci
WHERE
  code = '200023414'
  AND ST_Within ("coordonneesXY", geometry)
GROUP BY
  implantation,
  LEVEL,
  code
ORDER BY
  nb_stations DESC
```
<!-- #endregion -->

### T6 : Pourcentage de stations par type d’implantation

Indicateur similaire à 't5' ( 'pct_nb_stations' remplace 'nb_stations').

'pct_nb_stations' est le pourcentage de stations avec un type d'implantation donné.

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête globale : 't6-00-00' ou 't6'

perim = '00'
zone  = '00'

query = f"""
    WITH t5 AS (
    WITH national(code) AS (VALUES ('{perim}')) , perimeter(level) AS (VALUES ('{perim}')) 
    SELECT count(id_station_itinerance) AS nb_stations, implantation_station AS implantation, level, code  
    FROM perimeter, station, {TABLE[perim]}
    GROUP BY implantation, level, code  ORDER BY nb_stations DESC)
    SELECT nb_stations / (SELECT sum(nb_stations) FROM t5) * 100 AS pct_nb_stations, implantation, level, code 
    FROM t5
"""
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête : 't6'

```sql
WITH
  t5 AS (
    WITH
      NATIONAL (code) AS (
        VALUES
          ('00')
      ),
      perimeter (LEVEL) AS (
        VALUES
          ('00')
      )
    SELECT
      count(id_station_itinerance) AS nb_stations,
      implantation_station AS implantation,
      LEVEL,
      code
    FROM
      perimeter,
      station,
      NATIONAL
    GROUP BY
      implantation,
      LEVEL,
      code
    ORDER BY
      nb_stations DESC
  )
SELECT
  nb_stations / (
    SELECT
      sum(nb_stations)
    FROM
      t5
  ) * 100 AS pct_nb_stations,
  implantation,
  LEVEL,
  code
FROM
  t5
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
# requête locale : 

# ex. sur l'EPCI (03) Métropole Rouen Normandie (200023414) 't6-03-200023414'
perim = '03'
zone  = '200023414'

query = f""" 
    WITH t5 AS (
    WITH perimeter(level) AS (VALUES ('{perim}')) 
    SELECT count(id_station_itinerance) AS nb_stations, implantation_station AS implantation, level, code 
    FROM perimeter, station LEFT JOIN localisation ON localisation_id = localisation.id , {TABLE[perim]}
    WHERE code = '{zone}' AND ST_Within("coordonneesXY", geometry) 
    GROUP BY implantation, level, code  ORDER BY nb_stations DESC)
    SELECT nb_stations / (SELECT sum(nb_stations) FROM t5) * 100 AS pct_nb_stations, implantation, level, code 
    FROM t5
    """

pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête 't6-03-200023414' :

```sql
WITH
  t5 AS (
    WITH
      perimeter (LEVEL) AS (
        VALUES
          ('03')
      )
    SELECT
      count(id_station_itinerance) AS nb_stations,
      implantation_station AS implantation,
      LEVEL,
      code
    FROM
      perimeter,
      station
      LEFT JOIN localisation ON localisation_id = localisation.id,
      epci
    WHERE
      code = '200023414'
      AND ST_Within ("coordonneesXY", geometry)
    GROUP BY
      implantation,
      LEVEL,
      code
    ORDER BY
      nb_stations DESC
  )
SELECT
  nb_stations / (
    SELECT
      sum(nb_stations)
    FROM
      t5
  ) * 100 AS pct_nb_stations,
  implantation,
  LEVEL,
  code
FROM
  t5
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
### Autres indicateurs de typologie

Les indicateurs liés à d'autres typologies (ex. opérateurs, accès deux roues, période d’ouverture, accès handicapés…) sont à définir.

Ceux concernant les opérateurs sont prioritaires.
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
## Autres indicateurs à prendre en compte

- Indicateurs d'historique (traitement des données historisées)
- Infrastructure - réseau autoroute (nécessite l'identification des stations de ce réseau)
- Usage - quantitatif (traitement des données dynamiques) 
- Usage - qualité de service (traitement des données dynamiques)
- Indicateurs étendus (en lien avec des données externes - ex. trafic, immatriculation, consommation ENEDIS)
<!-- #endregion -->

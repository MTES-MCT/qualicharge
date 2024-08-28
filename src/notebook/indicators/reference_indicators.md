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

Ce Notebook présente une proposition de structuration et de représentation des indicateurs Qualicharge.

La liste des indicateurs est présentée sur [ce lien](https://loco-philippe.github.io/IRVE/files/indicateurs.html).

*Nota : La représentation visuelle des indicateurs (ex. diagramme circulaire, diagramme à barre, carte choroplèthe, courbe...) n'est pas abordée.*
<!-- #endregion -->

```python
import os
import json
from sqlalchemy import create_engine
import pandas as pd
from util import to_indicator

# Connecteur à la base Qualicharge
engine = create_engine(os.getenv("DATABASE_URL"))

TABLE = {'00': 'national', '01': 'region', '02': 'department', '03': 'epci', '04': 'city'}
```

## Structure des indicateurs

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



#### ensemble des données avec une répartition par région (01)

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


#### Ensemble de la région (01) PACA (93) sans répartition

La codification est 'i1-01-93' (équivalent à 'i1-01-93-00')

Le résultat est le suivant :

| nb_pdc | level |code|
|--------|-------|----|
| 2351	 | 01	 | 93 |



#### ensemble de la région (1) PACA (93) par département (02)

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



## Infrastructure - quantitatif

Indicateurs pris en compte : 'i1', 'i4', 'i7'

Les autres indicateurs sont dérivés ('i2', 'i5', 'i8' ramené à 100 000 habitants et 'i3', 'i6', 'i9' ramené à 100 km2).


### I1 : Nombre de points de recharge ouverts au public

'nb_pdc' est le nombre de points de recharge.

```python
# requête globale : 'i1-00-00' ou 'i1'

perim = '00'
value = '00'
zone  = '00'

query = f""" 
    WITH national(code) AS (VALUES ({perim})), perimeter(level) AS (VALUES ({zone})) 
    SELECT count(id_pdc_itinerance) AS nb_pdc, level, code
    FROM perimeter, pointdecharge, national 
    GROUP BY level, code"""

pd.read_sql_query(query, engine.connect())
```

```python editable=true slideshow={"slide_type": ""}
# requête globale avec critère : 

# ex. globale avec une répartition par région (01) 'i1-00-00-01' ou 'i1---01'
perim = '00'
value = '00'
zone  = '01'

query = f""" 
    WITH national(code) AS (VALUES ('{perim}')) , perim_zon(level) AS (VALUES ('{zone}'))  
    SELECT count(id_pdc_itinerance) AS nb_pdc, level, code  
    FROM perim_zon, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id  LEFT JOIN region ON ST_Within("coordonneesXY", geometry)  
    GROUP BY level, code  ORDER BY nb_pdc DESC"""

pd.read_sql_query(query, engine.connect())[:5]
```

```python
# requête locale : 

# ex. sur la région (01) PACA (93) 'i1-01-93-00' ou 'i1-01-93'
perim = '01'
value = '93'
zone  = '00'

query = f""" 
    WITH  pdc_loc AS (SELECT id_pdc_itinerance, "coordonneesXY"  
                      FROM {TABLE[perim]}, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id 
                      WHERE  code = '{value}' AND ST_Within("coordonneesXY", geometry) ), 
          perimeter(level) AS (VALUES ('{perim}')) , perim_zon(code) AS (VALUES ('{value}'))  
    SELECT count(id_pdc_itinerance) AS nb_pdc, level, code 
    FROM perimeter, perim_zon, pdc_loc 
    GROUP BY level, code ORDER BY nb_pdc DESC"""

pd.read_sql_query(query, engine.connect())
```

```python editable=true slideshow={"slide_type": ""}
# requête locale avec critère : 

# ex. sur la région (01) PACA (93) par département (02) 'i1-01-93-02'
perim = '01'
value = '93'
zone  = '02'

query = f""" 
    WITH  pdc_loc AS (SELECT id_pdc_itinerance, "coordonneesXY"  
                      FROM {TABLE[perim]}, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id  
                      WHERE  code = '{value}' AND ST_Within("coordonneesXY", geometry) ), 
          perim_zon(level) AS (VALUES ('{zone}'))  
    SELECT count(id_pdc_itinerance) AS nb_pdc, level, code  
    FROM perim_zon, pdc_loc LEFT JOIN {TABLE[zone]} ON ST_Within("coordonneesXY", geometry)  
    GROUP BY level, code  ORDER BY nb_pdc DESC"""

pd.read_sql_query(query, engine.connect())
```

### I4 : Nombre de stations ouvertes au public

'nb_stat' est le nombre de stations.

```python
to_indicator(engine, 'i4-0', simple=True)
```

```python
i4_nat = to_indicator(engine, 'i4-0-xx-01')
print(i4_nat['nb_stat'].sum())
i4_nat[:10]
```

```python
to_indicator(engine, 'i4-01-93-0')
```

```python
to_indicator(engine, 'i4-01-93-03')[:10]
```

### I7 : Puissance installée

'p_nom' est la puissance nominale cumulée

```python
to_indicator(engine, 'i7', simple=True)
```

```python
i7_nat = to_indicator(engine, 'i7-0--01')
print(i7_nat['p_nom'].sum())
i7_nat[:10]
```

```python
i7_paca_city = to_indicator(engine, 'i7-01-93-04', simple=True)
i7_paca_city[:10]
```

## Infrastructure - typologie

Les indicateurs 't1' à 't6' sont pris en compte.

L'indicateur 't7' reste à construire (non prioritaire).

Les autres indicateurs sont à définir (


### T1 : Nombre de points de recharge par niveau de puissance

'nb_pdc' est le nombre de points de recharge.

'p-range' est la plage de puissance (ex. [65, 175) -> de 65 inclus à 175 exclus)

'p-cat' est l'index de la catégorie (1 pour la catégorie la plus basse)

```python
t1_nat = to_indicator(engine, 't1-00')
print(t1_nat['nb_pdc'].sum())
t1_nat
```

```python
to_indicator(engine, 't1', simple=True)
```

```python
to_indicator(engine, 't1-02-75')
```

```python
to_indicator(engine, 't1-02')
```

### T2 : Pourcentage de points de recharge par niveau de puissance

Indicateur similaire à 't1' ( 'pct_nb_pdc' remplace 'nb_pdc').

'pct_nb_pdc' est le pourcentage de pdc pour le niveau de puissance.

```python
to_indicator(engine, 't2')
```

```python
to_indicator(engine, 't2-02-75', simple=True)
```

### T3 : Nombre de stations par nombre de points de recharge

'nb_stations' est le nombre de stations.

'nb_pdc' est le nombre de pdc.

ex. il y a 2790 stations (nb_stations) avec un seul pdc (nb_pdc).

```python
to_indicator(engine, 't3-00')[:10]
```

```python
to_indicator(engine, 't3-04-74012')
```

### T4 : Pourcentage de stations par nombre de points de recharge

Indicateur similaire à 't3' ( 'pct_nb_stations' remplace 'nb_stations').

'pct_nb_stations' est le pourcentage de stations avec un nombre de pdc donné.

```python
to_indicator(engine, 't4')[:10]
```

```python
to_indicator(engine, 't4-04-74012', simple=True)
```

### T5 : Nombre de stations par type d’implantation

'nb_stations' est le nombre de stations.

'implantation' est le type d'implantation

```python
t5_nat = to_indicator(engine, 't5-00')
print(t5_nat['nb_stations'].sum())
t5_nat[:10]
```

```python
to_indicator(engine, 't5', simple=True)
```

```python
to_indicator(engine, 't5-03-200023414')
```

```python
to_indicator(engine, 't5-03-200023414', simple=True)
```

### T6 : Pourcentage de stations par type d’implantation

Indicateur similaire à 't5' ( 'pct_nb_stations' remplace 'nb_stations').

'pct_nb_stations' est le pourcentage de stations avec un type d'implantation donné.

```python
to_indicator(engine, 't6')
```

```python
to_indicator(engine, 't6-03-200023414')
```

```python
to_indicator(engine, 't6-03-200023414', simple=True)
```

### Autres indicateurs de typologie

Les indicateurs liés à d'autres typologies (ex. opérateurs, accès deux roues, période d’ouverture, accès handicapés…) sont à définir.

Ceux concernant les opérateurs sont prioritaires.


## Autres indicateurs à prendre en compte

- Indicateurs d'historique (traitement des données historisées)
- Infrastructure - réseau autoroute (nécessite l'identification des stations de ce réseau)
- Usage - quantitatif (traitement des données dynamiques) 
- Usage - qualité de service (traitement des données dynamiques)
- Indicateurs étendus (en lien avec des données externes - ex. trafic, immatriculation, consommation ENEDIS)

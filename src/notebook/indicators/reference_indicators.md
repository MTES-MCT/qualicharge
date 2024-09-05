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

*Nota 1 : La dimension temporelle des indicateurs n'est pas prise en compte, elle sera ajoutée dans une version ultérieure*

*Nota 2 : La représentation visuelle des indicateurs (ex. diagramme circulaire, diagramme à barre, carte choroplèthe, courbe...) n'est pas abordée.*
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
## Structure des indicateurs
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
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


Les exemples ci-dessous concerna l'indicateur 'i1' qui fournit le nombre de points de recharge.

Les colonnes de gauche sont les valeurs calculées liées à l'indicateur (ex. pour 'i1' :  'nb_pdc').

Les colonnes de droite sont des données complémentaires spécifiques à chaque indicateur (ex. pour 'i1' : 'code' indique un critère de regroupement associé à une zone géographique)


#### Ensemble des données

La codification est 'i1-00-00' (ou bien 'i1')

Le résultat est le suivant :

| nb_pdc | 
|--------|
| 13400	 |



#### Ensemble des données avec une répartition par région (01)

La codification est 'i1-00-00-01' (ou bien 'i1---01')

Le résultat est le suivant :

| nb_pdc | code |
| :----- | :--- |
| 3538   | 84   |
| 2351   | 93   |
| 1391   | 11   |
| 1082   | 44   |
| 1027   | 75   |

*ex. ligne 1 : 'code' 84 indique le code de la région.*


#### Région (01) PACA (93)

La codification est 'i1-01-93' (équivalent à 'i1-01-93-00')

Le résultat est le suivant :

| nb_pdc |code|
|--------|----|
| 2351	 | 93 |



#### Région (1) PACA (93) par département (02)

La codification est 'i1-01-93-02'

Le résultat est le suivant :

| nb_pdc | code |
| :----- | :--- |
| 782    | 83   |
| 668    | 06   |
| 268    | 13   |
| 262    | 05   |
| 214    | 84   |
| 157    | 04   |

*ex. ligne 1 : 'code' 84 indique le code du département.*

<!-- #region editable=true slideshow={"slide_type": ""} -->
## Présentation des indicateurs

Les sections suivantes présentent pour chaque indicateur la requête SQL associée pour plusieurs exemples de jeux de paramètres.

Les requêtes sont issues d'un [générateur de requêtes](../misc/create_query.py).

Les résultats de ces requêtes ou la structure paramétrée peuvent être consultés dans le [notebook associé](../misc/create_indicators.md).

Une solution provisoire est utilisée pour le point suivant :

- les catégories de regroupement des puissances nominales des point de recharge sont définies dans la requête. Une structure externe est utilisée dans la version définitive. 
<!-- #endregion -->

## Infrastructure - quantitatif

Indicateurs pris en compte : 'i1', 'i4', 'i7'

Les autres indicateurs dérivés ('i2', 'i5', 'i8' ramené à 100 000 habitants et 'i3', 'i6', 'i9' ramené à 100 km2) sont ajoutés dans la prochaine version.

<!-- #region editable=true slideshow={"slide_type": ""} -->
### I1 : Nombre de points de recharge ouverts au public

'nb_pdc' est le nombre de points de recharge.
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 'i1-00-00' ou 'i1'

```sql
SELECT
    count(id_pdc_itinerance) AS nb_pdc
FROM
    pointdecharge
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale avec une répartition par région (01) 'i1-00-00-01' ou 'i1---01'

```sql
SELECT
    count(id_pdc_itinerance) AS nb_pdc,
    region.code
FROM  
    pointdecharge 
    LEFT JOIN station ON station.id = station_id 
    LEFT JOIN localisation ON localisation_id = localisation.id
    LEFT JOIN city on city.code = code_insee_commune
    LEFT JOIN department on city.department_id = department.id
    LEFT JOIN region on department.region_id = region.id
GROUP BY   
    region.code
ORDER BY
    nb_pdc DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) 'i1-01-93-00' ou 'i1-01-93'

```sql
SELECT
    count(id_pdc_itinerance) AS nb_pdc,
    region.code
FROM 
    pointdecharge 
    LEFT JOIN station ON station.id = station_id 
    LEFT JOIN localisation ON localisation_id = localisation.id
    LEFT JOIN city on city.code = code_insee_commune
    LEFT JOIN department on city.department_id = department.id
    LEFT JOIN region on department.region_id = region.id
WHERE
    region.code = '93'
GROUP BY   
    region.code
ORDER BY
    nb_pdc DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) par département (02) 'i1-01-93-02'

```sql
SELECT
    count(id_pdc_itinerance) AS nb_pdc,
    department.code
FROM
    pointdecharge 
    LEFT JOIN station ON station.id = station_id 
    LEFT JOIN localisation ON localisation_id = localisation.id
    LEFT JOIN city on city.code = code_insee_commune
    LEFT JOIN department on city.department_id = department.id
    LEFT JOIN region on department.region_id = region.id
WHERE
    region.code = '93'
GROUP BY
    department.code
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

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 'i4-00-00' ou 'i4'

```sql
SELECT
    count(id_station_itinerance) AS nb_stat
FROM
    station
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale avec une répartition par région (01) 'i4-00-00-01' ou 'i4---01'

```sql
SELECT
    count(id_station_itinerance) AS nb_stat,
    region.code
FROM
    station 
    LEFT JOIN localisation ON localisation_id = localisation.id 
    LEFT JOIN city on city.code = code_insee_commune
    LEFT JOIN department on city.department_id = department.id
    LEFT JOIN region on department.region_id = region.id
GROUP BY
    region.code
ORDER BY
    nb_stat DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) 'i4-01-93-00' ou 'i4-01-93'

```sql
SELECT
    count(id_station_itinerance) AS nb_stat,
    region.code
FROM
    station 
    LEFT JOIN localisation ON localisation_id = localisation.id 
    LEFT JOIN city on city.code = code_insee_commune
    LEFT JOIN department on city.department_id = department.id
    LEFT JOIN region on department.region_id = region.id
WHERE
    region.code = '93'
GROUP BY
    region.code
ORDER BY
    nb_stat DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) par EPCI (03) 'i4-01-93-03'

```sql
SELECT
    count(id_station_itinerance) AS nb_stat,
    epci.code
FROM
    station 
    LEFT JOIN localisation ON localisation_id = localisation.id 
    LEFT JOIN city on city.code = code_insee_commune
    LEFT JOIN department on city.department_id = department.id
    LEFT JOIN region on department.region_id = region.id
WHERE
    region.code = '93'
GROUP BY
    epci.code
ORDER BY
    nb_stat DESC
```
<!-- #endregion -->

### I7 : Puissance installée

'p_nom' est la puissance nominale cumulée

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 'i7-00-00' ou 'i7'

```sql
SELECT
    sum(puissance_nominale) AS p_nom
FROM
    pointdecharge
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale avec une répartition par région (01) 'i7-00-00-01' ou 'i7---01'

```sql
SELECT
    sum(puissance_nominale) AS p_nom,
    region.code
FROM
    pointdecharge 
    LEFT JOIN station ON station.id = station_id 
    LEFT JOIN localisation ON localisation_id = localisation.id
    LEFT JOIN city on city.code = code_insee_commune
    LEFT JOIN department on city.department_id = department.id
    LEFT JOIN region on department.region_id = region.id
GROUP BY
    region.code
ORDER BY
    p_nom DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) 'i7-01-93-00' ou 'i7-01-93'

```sql
SELECT
    sum(puissance_nominale) AS p_nom,
    region.code
FROM
    pointdecharge 
    LEFT JOIN station ON station.id = station_id 
    LEFT JOIN localisation ON localisation_id = localisation.id
    LEFT JOIN city on city.code = code_insee_commune
    LEFT JOIN department on city.department_id = department.id
    LEFT JOIN region on department.region_id = region.id
WHERE
    region.code = '93'
GROUP BY
    region.code
ORDER BY
    p_nom DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) par department (04) 'i7-01-93-04'

```sql
SELECT
    sum(puissance_nominale) AS p_nom,
    city.code
FROM
    pointdecharge 
    LEFT JOIN station ON station.id = station_id 
    LEFT JOIN localisation ON localisation_id = localisation.id
    LEFT JOIN city on city.code = code_insee_commune
    LEFT JOIN department on city.department_id = department.id
    LEFT JOIN region on department.region_id = region.id
WHERE
    region.code = '93'
GROUP BY
    city.code
ORDER BY
    p_nom DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
## Infrastructure - typologie

Les indicateurs 't1' à 't6' sont pris en compte, les indicateurs 't8' et 't9' sont ajoutés dans la prochaine version.

L'indicateur 't7' reste à construire (non prioritaire).
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
### T1 : Nombre de points de recharge par niveau de puissance

'nb_pdc' est le nombre de points de recharge.

'p-range' est la plage de puissance (ex. [65, 175) -> de 65 inclus à 175 exclus)
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 't1-00-00' ou 't1'

```sql
WITH 
    puissance(p_range, p_cat) AS (
        VALUES 
            (numrange(0, 15.0), 1), 
            (numrange(15.0, 26.0), 2), 
            (numrange(26, 65.0), 3),
            (numrange(65, 175.0), 4),
            (numrange(175, 360.0), 5),
            (numrange(360, NULL), 6)
    )
SELECT
    count(id_pdc_itinerance) AS nb_pdc,
    p_range
FROM
    pointdecharge 
    LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range 
GROUP BY
    p_range
ORDER BY
    nb_pdc DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la département (02) de paris (75) 't1-02-75'

```sql
WITH 
    puissance(p_range, p_cat) AS (
        VALUES 
            (numrange(0, 15.0), 1), 
            (numrange(15.0, 26.0), 2), 
            (numrange(26, 65.0), 3),
            (numrange(65, 175.0), 4),
            (numrange(175, 360.0), 5),
            (numrange(360, NULL), 6)
    )
SELECT
    count(id_pdc_itinerance) AS nb_pdc,
    p_range,
    department.code
FROM
    pointdecharge 
    LEFT JOIN station ON station.id = station_id 
    LEFT JOIN localisation ON localisation_id = localisation.id
    LEFT JOIN city on city.code = code_insee_commune
    LEFT JOIN department on city.department_id = department.id
    LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range 
WHERE
    department.code = '75'
GROUP BY
    p_range,
    department.code
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

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 't2-00-00' ou 't2'

```sql
WITH 
    t1 AS (        
        WITH 
            puissance(p_range, p_cat) AS (
                VALUES 
                    (numrange(0, 15.0), 1), 
                    (numrange(15.0, 26.0), 2), 
                    (numrange(26, 65.0), 3),
                    (numrange(65, 175.0), 4),
                    (numrange(175, 360.0), 5),
                    (numrange(360, NULL), 6)
            )
        SELECT
            count(id_pdc_itinerance) AS nb_pdc,
            p_range    
        FROM
            pointdecharge 
            LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range 
        GROUP BY
            p_range
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
    p_range
FROM 
    t1
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la département (02) paris (75) 't2-02-75'

```sql
WITH 
    t1 AS (
        WITH 
            puissance(p_range, p_cat) AS (
                VALUES 
                    (numrange(0, 15.0), 1), 
                    (numrange(15.0, 26.0), 2), 
                    (numrange(26, 65.0), 3),
                    (numrange(65, 175.0), 4),
                    (numrange(175, 360.0), 5),
                    (numrange(360, NULL), 6)
            )
        SELECT
            count(id_pdc_itinerance) AS nb_pdc,
            p_range,
            department.code
        FROM
            department,
            pointdecharge 
            LEFT JOIN station ON station.id = station_id 
            LEFT JOIN localisation ON localisation_id = localisation.id
            LEFT JOIN city on city.code = code_insee_commune
            LEFT JOIN department on city.department_id = department.id
            LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range 
        WHERE
            department.code = '75'
        GROUP BY
            p_range,
            department.code
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
    p_range,
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

NOTA : 

- Le nombre de points de recharge par station (nb_pdc) est calculé en fonction des points de recharge présents dans la base 
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 't3-00-00' ou 't3'

```sql
WITH 
    stat_nb_pdc AS (
        SELECT
          count(station_id) AS nb_pdc,
          localisation_id
        FROM
          pointdecharge
          LEFT JOIN station ON station.id = station_id
        GROUP BY
          station_id,
          localisation_id
    )
SELECT
    count(nb_pdc) AS nb_stations,
    nb_pdc  
FROM
    stat_nb_pdc
GROUP BY   
    nb_pdc
ORDER BY
    nb_stations DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la commune (04) de Marseille 01 (13001) 't3-04-13001'

```sql
WITH 
    stat_nb_pdc AS (
        SELECT
          count(station_id) AS nb_pdc,
          localisation_id
        FROM
          pointdecharge
          LEFT JOIN station ON station.id = station_id
        GROUP BY
          station_id,
          localisation_id
    )
SELECT
    count(nb_pdc) AS nb_stations,
    nb_pdc,
    city.code
FROM
    stat_nb_pdc
    LEFT JOIN localisation ON localisation_id = localisation.id
    LEFT JOIN city on city.code = code_insee_commune
WHERE
    city.code = '13001'
GROUP BY
    nb_pdc,
    city.code
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

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 't4-00-00' ou 't4'

```sql
WITH 
    t3 AS (  
        WITH 
            stat_nb_pdc AS (
                SELECT
                  count(station_id) AS nb_pdc,
                  localisation_id
                FROM
                  pointdecharge
                  LEFT JOIN station ON station.id = station_id
                GROUP BY
                  station_id,
                  localisation_id
            )
        SELECT
            count(nb_pdc) AS nb_stations,
            nb_pdc  
        FROM
            stat_nb_pdc
        GROUP BY   
            nb_pdc
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
    nb_pdc
FROM 
    t3
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête  sur la commune (04) marseille 01 (13001) 't4-04-13001'

```sql
WITH 
    t3 AS ( 
        WITH 
            stat_nb_pdc AS (
                SELECT
                  count(station_id) AS nb_pdc,
                  localisation_id
                FROM
                  pointdecharge
                  LEFT JOIN station ON station.id = station_id
                GROUP BY
                  station_id,
                  localisation_id
            )
        SELECT
            count(nb_pdc) AS nb_stations,
            nb_pdc,
            city.code
        FROM
            stat_nb_pdc
            LEFT JOIN localisation ON localisation_id = localisation.id
            LEFT JOIN city on city.code = code_insee_commune
        WHERE
            city.code = '13001'
        GROUP BY
            nb_pdc,
            city.code
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

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 't5-00-00' ou 't5'

```sql
SELECT
    count(id_station_itinerance) AS nb_stations,
    implantation_station
FROM
    station 
GROUP BY
    implantation_station
ORDER BY
    nb_stations DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur l'EPCI (03) Métropole Rouen Normandie (200023414) 't5-03-200023414'
```sql
SELECT
    count(id_station_itinerance) AS nb_stations,
    implantation_station,
    epci.code
FROM
    station 
    LEFT JOIN localisation ON localisation_id = localisation.id
    LEFT JOIN city on city.code = code_insee_commune
    LEFT JOIN epci on city.epci_id = epci.id
WHERE
    epci.code = '200023414'
GROUP BY
    implantation_station,
    epci.code
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

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 't6-00-00' ou 't6'

```sql
WITH 
    t5 AS (
        SELECT
            count(id_station_itinerance) AS nb_stations,
            implantation_station
        FROM
            station 
        GROUP BY
            implantation_station
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
    implantation_station
FROM 
    t5
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur l'EPCI (03) Métropole Rouen Normandie (200023414) 't6-03-200023414'

```sql
WITH 
    t5 AS (
        SELECT
            count(id_station_itinerance) AS nb_stations,
            implantation_station,
            epci.code
        FROM
            station 
            LEFT JOIN localisation ON localisation_id = localisation.id
            LEFT JOIN city on city.code = code_insee_commune
            LEFT JOIN epci on city.epci_id = epci.id
        WHERE
            epci.code = '200023414'
        GROUP BY
            implantation_station,
            epci.code
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
    implantation_station,
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

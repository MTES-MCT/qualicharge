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
# Indicateurs QualiCharge : Génération des indicateurs et requêtes

Ce Notebook présente la fonction permettant de générer les indicateurs Qualicharge et les requêtes associées.

La liste des indicateurs est présentée sur [ce lien](https://loco-philippe.github.io/IRVE/files/indicateurs.html).

La présentation des requêtes associée est présentée sur [ce notebook](../indicators/reference_indicators.md)
<!-- #endregion -->

## Structure des indicateurs

<!-- #region jp-MarkdownHeadingCollapsed=true -->
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

```python editable=true slideshow={"slide_type": ""}
# calcul sur l'ensemble des données ('i1' est équivalent à 'i1-00-00-00')
to_indicator(engine, 'i1')
```

```python editable=true slideshow={"slide_type": ""}
# calcul sur l'ensemble des données avec une répartition par région (01) ('i1---01' est équivalent à 'i1-00-00-01')
# ex. ligne 1 : 'level' 01 indique un périmètre région, 'code' 84 indique le code de la région.
to_indicator(engine, 'i1---01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
# calcul sur l'ensemble de la région (01) PACA (93) sans répartition ('i1-01-93' est équivalent à 'i1-01-93-00')
to_indicator(engine, 'i1-01-93')
```

```python editable=true slideshow={"slide_type": ""}
# calcul sur l'ensemble de la région (01) PACA (93) par département (02)
to_indicator(engine, 'i1-01-93-02')
```

### Options de représentation

La représentation par défaut est sous la forme d'un DataFrame pandas (voir exemples ci-dessus). 

Les représentations complémentaires sont présentées ci-dessous.

```python
# Représentation sans les colonnes optionnelles (ici 'name')
to_indicator(engine, 'i1-01-93-02', simple=True)
```

Pour un indicateur donné (ex. 'i1'), la structure 'simple' est identique. L'historisation des données peut donc s'effectuer par indicateur (avec l'ajout d'un timestamp). 

Par exemple, on pourrait avoir une table 'i1-histo' et y stocker la valeur totale 'i1' quotidiennement et la valeur par région 'i1---01' mensuellement.

Pour avoir un historique sur le nombre de pdc en PACA, la table serait filtrée avec level=01 et code=93

```python
# représentation avec un timestamp.
to_indicator(engine, 'i1-01-93-02', histo=True)
```

```python
# représentation sous forme de JSON
to_indicator(engine, 'i1-01-93-02', simple=True, format='json', json_orient='records')
```

```python
# représentation sous forme de table
to_indicator(engine, 'i1-01-93-02', format='table')
```

```python
# représentation sous forme de requète PostgreSQL
print(to_indicator(engine, 'i1', format='query'))
```

## Infrastructure - typologie

Les indicateurs 't1' à 't6' sont pris en compte.

L'indicateur 't7' reste à construire (non prioritaire).

Les autres indicateurs sont à définir (


### T1 : Nombre de points de recharge par niveau de puissance

'nb_pdc' est le nombre de points de recharge.

'p-range' est la plage de puissance (ex. [65, 175) -> de 65 inclus à 175 exclus)

'p-cat' est l'index de la catégorie (1 pour la catégorie la plus basse)

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
t1_nat = to_indicator(engine, 't1-00')
print(t1_nat['nb_pdc'].sum())
t1_nat
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't1-00', simple=True, format='query')
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't1-00', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
perim = '00'
zone  = '00'

query = f"""
    WITH puissance(p_range, p_cat) AS ( VALUES (numrange(0, 15.0), 1), (numrange(15.0, 26.0), 2), (numrange(26, 65.0), 3), (numrange(65, 175.0), 4), (numrange(175, 360.0), 5), (numrange(360, NULL), 6)) , 
         national(code) AS (VALUES ('{perim}')) , perimeter(level) AS (VALUES ('{perim}')) 
    SELECT count(id_pdc_itinerance) AS nb_pdc, p_cat, p_range, level, code 
    FROM perimeter, pointdecharge LEFT JOIN puissance ON puissance_nominale::numeric <@ p_range , {TABLE[perim]}
    GROUP BY p_cat, p_range, level, code  ORDER BY nb_pdc DESC
"""
pd.read_sql_query(query, engine.connect())
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 't1-02-75')
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't1-02-75', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't1-02-75', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
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
pd.read_sql_query(query, engine.connect())
```

### T2 : Pourcentage de points de recharge par niveau de puissance

Indicateur similaire à 't1' ( 'pct_nb_pdc' remplace 'nb_pdc').

'pct_nb_pdc' est le pourcentage de pdc pour le niveau de puissance.

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 't2')
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't2', simple=True, format='query')
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't2', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
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
pd.read_sql_query(query, engine.connect())
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 't2-02-75', simple=True)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't2-02-75', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't2-02-75', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
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
pd.read_sql_query(query, engine.connect())
```

### T3 : Nombre de stations par nombre de points de recharge

'nb_stations' est le nombre de stations.

'nb_pdc' est le nombre de pdc.

ex. il y a 2790 stations (nb_stations) avec un seul pdc (nb_pdc).

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 't3-00')[:5]
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't3', simple=True, format='query')
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't3', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
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
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 't3-04-74012')
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't3-04-74012', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't3-04-74012', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
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
pd.read_sql_query(query, engine.connect())[:5]
```

### T4 : Pourcentage de stations par nombre de points de recharge

Indicateur similaire à 't3' ( 'pct_nb_stations' remplace 'nb_stations').

'pct_nb_stations' est le pourcentage de stations avec un nombre de pdc donné.

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 't4')[:5]
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't4', simple=True, format='query')
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't4', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
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
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 't4-04-74012', simple=True)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't4-04-74012', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't4-04-74012', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
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
pd.read_sql_query(query, engine.connect())[:5]
```

### T5 : Nombre de stations par type d’implantation

'nb_stations' est le nombre de stations.

'implantation' est le type d'implantation

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
t5_nat = to_indicator(engine, 't5-00')
print(t5_nat['nb_stations'].sum())
t5_nat[:10]
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't5', simple=True, format='query')
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't5', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
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
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 't5-03-200023414')
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't5-03-200023414', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't5-03-200023414', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
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

### T6 : Pourcentage de stations par type d’implantation

Indicateur similaire à 't5' ( 'pct_nb_stations' remplace 'nb_stations').

'pct_nb_stations' est le pourcentage de stations avec un type d'implantation donné.

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 't6')
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't6', simple=True, format='query')
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't6', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
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
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 't6-03-200023414')
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't6-03-200023414', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't6-03-200023414', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
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

### Autres indicateurs de typologie

Les indicateurs liés à d'autres typologies (ex. opérateurs, accès deux roues, période d’ouverture, accès handicapés…) sont à définir.

Ceux concernant les opérateurs sont prioritaires.


## Autres indicateurs à prendre en compte

- Indicateurs d'historique (traitement des données historisées)
- Infrastructure - réseau autoroute (nécessite l'identification des stations de ce réseau)
- Usage - quantitatif (traitement des données dynamiques) 
- Usage - qualité de service (traitement des données dynamiques)
- Indicateurs étendus (en lien avec des données externes - ex. trafic, immatriculation, consommation ENEDIS)


## Infrastructure - quantitatif

Indicateurs pris en compte : 'i1', 'i4', 'i7'

Les autres indicateurs sont dérivés ('i2', 'i5', 'i8' ramené à 100 000 habitants et 'i3', 'i6', 'i9' ramené à 100 km2).

*à préciser : Quelle population retenir (date fixe ?) ? Est-ce qu'on stocke en base la surface (à partir des polygones) ?*

<!-- #region editable=true slideshow={"slide_type": ""} -->
### I1 : Nombre de points de recharge ouverts au public

'nb_pdc' est le nombre de points de recharge.
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 'i1')
```

```python
to_indicator(engine, 'i1-00-00-00', simple=True)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i1', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i1', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python
perim = '00'
val   = '00'
zone  = '00'

query = f"""
    WITH  national(code) AS (VALUES ('{perim}')) , perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT count(id_pdc_itinerance) AS nb_pdc, level , code  
    FROM perim_zon, pointdecharge, {TABLE[perim]}
    GROUP BY level , code
"""
pd.read_sql_query(query, engine.connect())[:5]
```

#### requête globale avec critère

```python
i1_nat = to_indicator(engine, 'i1-00-00-01')
print(i1_nat['nb_pdc'].sum())
i1_nat[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i1-00-00-01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i1---01', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python
perim = '00'
val   = '00'
zone  = '01'

query = f"""
    WITH national(code) AS (VALUES ('{perim}')) , perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT count(id_pdc_itinerance) AS nb_pdc, level , code  
    FROM perim_zon, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id  LEFT JOIN {TABLE[zone]} ON ST_Within("coordonneesXY", geometry) 
    GROUP BY level , code  ORDER BY nb_pdc DESC
"""
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 'i1-01-93-00')
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i1-01-93-00', simple=True, format='query'))
```

```python
to_indicator(engine, 'i1-01-93')
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i1-01-93', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
perim = '01'
val   = '93'
zone  = '00'

query = f"""
    WITH pdc_loc AS (SELECT id_pdc_itinerance, "coordonneesXY"
                     FROM {TABLE[perim]}, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id 
                     WHERE  code = '{val}' AND ST_Within("coordonneesXY", geometry) ), perimeter(level) AS (VALUES ('{perim}')) , perim_zon(code) AS (VALUES ('{val}')) 
    SELECT count(id_pdc_itinerance) AS nb_pdc, level, code
    FROM perimeter, perim_zon, pdc_loc
    GROUP BY level, code ORDER BY nb_pdc DESC
"""
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
paca_epci = 'i1-01-93-02'
i1_paca = to_indicator(engine, paca_epci, simple=True)
i1_paca[:10]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i1-01-93-02', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i1-01-93-02', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i1-01-93-02', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
perim = '01'
val   = '93'
zone  = '02'

query = f"""
    WITH pdc_loc AS (SELECT id_pdc_itinerance, "coordonneesXY"
                     FROM {TABLE[perim]}, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id 
                     WHERE  code = '{val}' AND ST_Within("coordonneesXY", geometry) ), perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT count(id_pdc_itinerance) AS nb_pdc, level , code 
    FROM perim_zon, pdc_loc LEFT JOIN {TABLE[zone]} ON ST_Within("coordonneesXY", geometry) 
    GROUP BY level , code  ORDER BY nb_pdc DESC
"""
pd.read_sql_query(query, engine.connect())
```

### I4 : Nombre de stations ouvertes au public

'nb_stat' est le nombre de stations.

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 'i4-0', simple=True)
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i4', simple=True, format='query')
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i4', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
perim = '00'
val   = '00'
zone  = '00'

query = f"""
    WITH  national(code) AS (VALUES ('{perim}')) , perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT count(id_station_itinerance) AS nb_stat, level , code  
    FROM perim_zon, station, {TABLE[perim]}
    GROUP BY level , code
"""
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python
to_indicator(engine, 'i4-0-xx-01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i4-0-xx-01', simple=True, format='query')
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i4-0-xx-01', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
perim = '00'
val   = '00'
zone  = '01'

query = f"""
    WITH national(code) AS (VALUES ('{perim}')) , perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT count(id_station_itinerance) AS nb_stat, level , code  
    FROM perim_zon, station LEFT JOIN localisation ON localisation_id = localisation.id  LEFT JOIN {TABLE[zone]} ON ST_Within("coordonneesXY", geometry) 
    GROUP BY level , code  ORDER BY nb_stat DESC
"""
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 'i4-01-93-0')
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i4-01-93-0', simple=True, format='query')
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i4-01-93-0', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
perim = '01'
val   = '93'
zone  = '00'

query = f"""
    WITH stat_loc AS (SELECT id_station_itinerance, "coordonneesXY"
                         FROM {TABLE[perim]}, station LEFT JOIN localisation ON localisation_id = localisation.id 
                         WHERE  code = '{val}' AND ST_Within("coordonneesXY", geometry) ), perimeter(level) AS (VALUES ('{perim}')) , perim_zon(code) AS (VALUES ('{val}')) 
    SELECT count(id_station_itinerance) AS nb_stat, level, code
    FROM perimeter, perim_zon, stat_loc
    GROUP BY level, code ORDER BY nb_stat DESC
"""
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
to_indicator(engine, 'i4-01-93-03')[:5]
```

```python editable=true jupyter={"source_hidden": true} slideshow={"slide_type": ""}
print(to_indicator(engine, 'i4-01-93-03', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i4-01-93-03', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
perim = '01'
val   = '93'
zone  = '03'

query = f"""
    WITH stat_loc AS (SELECT id_station_itinerance, "coordonneesXY"
                         FROM {TABLE[perim]}, station LEFT JOIN localisation ON localisation_id = localisation.id 
                         WHERE  code = '{val}' AND ST_Within("coordonneesXY", geometry) ), perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT count(id_station_itinerance) AS nb_stat, level , code 
    FROM perim_zon, stat_loc LEFT JOIN {TABLE[zone]} ON ST_Within("coordonneesXY", geometry) 
    GROUP BY level , code  ORDER BY nb_stat DESC
"""
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
### I7 : Puissance installée

'p_nom' est la puissance nominale cumulée
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 'i7', simple=True)
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i7', simple=True, format='query')
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i7', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
perim = '00'
val   = '00'
zone  = '00'

query = f"""
    WITH  national(code) AS (VALUES ('{perim}')) , perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT sum(puissance_nominale) AS p_nom, level , code  
    FROM perim_zon, pointdecharge, {TABLE[perim]}
    GROUP BY level , code  
"""
pd.read_sql_query(query, engine.connect())
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python
i7_nat = to_indicator(engine, 'i7-0--01')
print(i7_nat['p_nom'].sum())
i7_nat[:5]
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i7-0--01', simple=True, format='query')
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i7-0--01', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
perim = '00'
val   = '00'
zone  = '01'

query = f"""
    WITH national(code) AS (VALUES ('{perim}')) , perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT sum(puissance_nominale) AS p_nom, level , code  
    FROM perim_zon, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id  LEFT JOIN {TABLE[zone]} ON ST_Within("coordonneesXY", geometry) 
    GROUP BY level , code  ORDER BY p_nom DESC 
"""
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 'i7-01-93-00', simple=True)
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i7-01-93-00', simple=True, format='query')
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i7-01-93-00', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
perim = '01'
val   = '93'
zone  = '00'

query = f"""
    WITH pnom_loc AS (SELECT puissance_nominale, "coordonneesXY"
                   FROM {TABLE[perim]}, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id 
                   WHERE  code = '{val}' AND ST_Within("coordonneesXY", geometry) ), perimeter(level) AS (VALUES ('{perim}')) , perim_zon(code) AS (VALUES ('{val}')) 
    SELECT sum(puissance_nominale) AS p_nom, level, code
    FROM perimeter, perim_zon, pnom_loc
    GROUP BY level, code ORDER BY p_nom DESC
"""
pd.read_sql_query(query, engine.connect())[:5]
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python
i7_paca_city = to_indicator(engine, 'i7-01-93-04', simple=True)
i7_paca_city[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i7-01-93-04', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i7-01-93-04', simple=True, format='query', query_gen=True)
print(query_gen)
```

```python editable=true slideshow={"slide_type": ""}
perim = '01'
val   = '93'
zone  = '04'

query = f"""
    WITH pnom_loc AS (SELECT puissance_nominale, "coordonneesXY"
                   FROM {TABLE[perim]}, pointdecharge LEFT JOIN station ON station.id = station_id LEFT JOIN localisation ON localisation_id = localisation.id 
                   WHERE  code = '{val}' AND ST_Within("coordonneesXY", geometry) ), perim_zon(level) AS (VALUES ('{zone}')) 
    SELECT sum(puissance_nominale) AS p_nom, level , code 
    FROM perim_zon, pnom_loc LEFT JOIN {TABLE[zone]} ON ST_Within("coordonneesXY", geometry) 
    GROUP BY level , code  ORDER BY p_nom DESC
"""
pd.read_sql_query(query, engine.connect())[:5]
```
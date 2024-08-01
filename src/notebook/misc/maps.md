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

# QualiCharge maps


## Introduction

L'utilisation de cartes choroplèthes pour la restitution d'indicateurs QualiCharge nécessite le chargement préalable des contours des zones affichées regroupées par cartes.

Pour des raisons de facilité de consultation, les cartes utilisées sont séparées par zone géographique :

- Territoire européen (régions européennes : 11, 24, 27, 28, 32, 44, 52, 53, 75, 76, 84, 93, 94)
- Territoire américain (régions Guadeloupe, Martinique, Guyane : 1, 2, 3)
- Territoire africain (régions La Réunion, Mayotte : 4, 6)

Quatre niveaux de découpage sont proposés :

- régions
- départements
- communes
- agglomérations

Le quatrième niveau est dérivé du découpage communal en intégrant les regroupements de communes définis dans les établissement public de coopération intercommunale (EPCI) à ficalité propre (métropoles, communautés urbaines, communautés d'agglomération, communautés de communes, Aix-Marseille et Grand Paris).

Les régions sont découpées en départements. Les régions ultramarines (hors territoire européen) ne comportent qu'un seul département (code '97x' avec 'x' code région).
Les départements sont découpés en communes.
Les agglomérations sont des regroupements de communes.



## Map utilisées

Les cartes utilisées pour restituer les indicateurs sont alors les suivantes (la métropole correspond au territoire européen):

- Territoire:
    - métropole par régions
    - métropole par départements
- 18 régions métropolitaines et ultramarines (pour chaque région):
    - région par départements
    - région par ECPI
    - région par commune

A ces cartes sont ajoutées les cartes des collectivités d'outre-mer (codes : 975, 977, 978, 986, 987) et des territoires à statut particulier (codes : 984, 988, 989). Ces structures ne disposent pas d'EPCI.


## Fichiers associés

Les fichiers GeoJson pour chaque map sont extraits des [contours administratifs Etalab](https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/2024/geojson/). 

  - metropole_reg.geojson
  - metropole_dep.geojson
  - region_xx_dep.geojson
  - region_xx_epci.geojson
  - region_xx_com.geojson

  avec xx : code région

Chaque contour (type : Polygon ou MultiPolygon) est associé à deux propriétés:
    - code : l'identifiant du contour,
    - nom : le nom du contour
    
La précision retenue pour les polygones est de 100 m.


## Génération des fichiers


### Initialisation des données

Les données sont issues des tables préalablement chargées sur QualiCharge (`region`, `department`, `city`, `epci`).

```python
import os
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    df = pd.read_sql_query("SELECT * FROM region", conn)
regions = list(df['code'])

query_reg = """SELECT region.code, region.name, ST_AsGeoJSON(region.geometry) :: json -> 'coordinates'  AS polygon
           FROM region""" 
query_dep = """SELECT department.code, department.name, ST_AsGeoJSON(department.geometry) :: json -> 'coordinates'  AS polygon, region.code AS reg_code
           FROM department INNER JOIN region ON department.region_id = region.id""" 
query_ecpi = """SELECT DISTINCT ON (epci.code) epci.code, epci.name, ST_AsGeoJSON(epci.geometry) :: json -> 'coordinates'  AS polygon, region.code AS reg_code
           FROM epci INNER JOIN city ON city.epci_id = epci.id INNER JOIN department ON city.department_id = department.id INNER JOIN region ON department.region_id = region.id""" 
query_city = """SELECT DISTINCT ON (city.code) city.code, city.name, ST_AsGeoJSON(city.geometry) :: json -> 'coordinates'  AS polygon, region.code AS reg_code
           FROM city INNER JOIN department ON city.department_id = department.id INNER JOIN region ON department.region_id = region.id""" 

maps_dir = '../../metabase/maps/'
```

### Métropole

```python
import json

code_reg = [1, 4]
queries_metro = [query_reg, query_dep]
extension = ['_reg', '_dep']
reg_metro = ['11', '24', '27', '28', '32', '44', '52', '53', '75', '76', '84', '93', '94']

for query, ext, reg in zip(queries_metro, extension, code_reg):
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn)
    map_geo = {'type': 'FeatureCollection', 
                       'features': [{'type': 'Feature', 
                                     'properties': {'code': row[1], 'nom': row[2]}, 
                                     'geometry': {'type': ('MultiPolygon' if str(row[3])[:4] == '[[[[' else 'Polygon'), 'coordinates': row[3]}} 
                                    for row in list(df.itertuples()) if row[reg] in reg_metro]}
    print(ext)
    file_metro = 'metropole' + ext +'.geojson'
    with open(maps_dir + file_metro, 'w', encoding ='utf8') as map_file:
        json.dump(map_geo, map_file)
    
    print(map_geo['features'][0]['properties'])
```

### Régions

```python
import pandas as pd

queries_reg = [query_dep, query_ecpi, query_city]
extension = ['_dep', '_epci', '_com']

with engine.connect() as conn:
    df = pd.read_sql_query(query_dep, conn)
for query, ext in zip(queries_reg, extension):
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn)
    for reg in regions:
        file_dep = 'region_' + reg + ext +'.geojson'
        map_geo = {'type': 'FeatureCollection', 
                   'features': [{'type': 'Feature', 
                                 'properties': {'code': row[1], 'nom': row[2]}, 
                                 'geometry': {'type': ('MultiPolygon' if str(row[3])[:4] == '[[[[' else 'Polygon'), 'coordinates': row[3]}} 
                                for row in list(df.itertuples()) if row[4] == reg]}
        print(reg, ext)
        if len(map_geo['features']):
            with open(maps_dir + file_dep, 'w', encoding ='utf8') as map_file:
                json.dump(map_geo, map_file)
            print(map_geo['features'][0]['properties'])

```

## Utilisation des fichiers

Les fichiers sont chargés dans MetaBase via les menus d'administration (`Admin settings / Maps / add a map`).

Les informations suivantes sont documentées:

- name (nom de la map équivalent au nom du fichier),
- URL du fichier (URL du fichier geojson de QualiCharge),
- id (lien avec les données à représenter - property geojson `code`),
- name (nom affiché - property geojson `nom`)

exemple d'URL: https://raw.githubusercontent.com/MTES-MCT/qualicharge/main/src/metabase/maps/region_03_epci.geojson

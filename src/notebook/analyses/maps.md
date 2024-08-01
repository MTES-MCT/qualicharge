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

L'utilisation de cartes choroplèthe pour la restitution d'indicateurs QualiCharge nécessite le chargement préalable des contours des zones affichées regroupées par cartes.

Pour des raisons de facilité de consultation, les cartes utilisées sont séparées par zone géographique:

- Territoire européen (régions européennes : 11, 24, 27, 28, 32, 44, 52, 53, 75, 76, 84, 93, 94)
- Territoire américain (régions Guadeloupe, Martinique, Guyane : 1, 2, 3)
- Territoire africain (régions La Réunion, Mayotte : 4, 6)

Quatre niveaux de découpage sont proposés:

- régions
- départements
- communes
- agglomérations

Le quatrième niveau est dérivé du découpage communal en intégrant les regroupements de communes définis dans les établissement public de coopération intercommunale (EPCI) à ficalité propre (métropoles, communautés urbaines, communautés d'agglomération, communautés de communes, Aix-Marseille et Grand Paris).

Les régions sont découpées en départements. Les régions ultramarines (hors territoire européen) ne comportent qu'un seul département (code '97x' avec 'x' code région).
Les départements sont découpés en communes.
Les agglomérations sont des regroupements de communes



## Map utilisées

Pour des raisons de lisibilité, les cartes associées à l'ensemble des territoires, au territoire américain et au territoire africain ne sont pas retenues.

Les cartes utilisées pour restituer les indicateurs sont alors les suivantes (la métropole correspond au territoire européen):

- Territoire:
    - métropole par régions
    - métropole par départements
- 18 régions (pour chaque région):
    - région par départements
    - région par ECPI
    - région par commune



## Génération des fichiers

Les fichiers GeoJson pour chaque map sont extraits des [contours administratifs Etalab](https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/2024/geojson/). 
Les régions sont identifiées par leur code [ISO 3166-2:FR](https://fr.wikipedia.org/wiki/ISO_3166-2:FR#R%C3%A9gions_m%C3%A9tropolitaines) :

  - metropole_reg
  - metropole_dep
  - region_xx_dep
  - region_xx_epci
  - region_xx_com

  avec xx : code région

La précision retenue est de 100 m.

```python
import os
from sqlalchemy import create_engine

engine = create_engine(os.getenv("DATABASE_URL"))
```

```python
with engine.connect() as conn:
    df = pd.read_sql_query("SELECT * FROM region", conn)
regions = list(df['code'])
```

```python
import pandas as pd

query_dep = """SELECT department.code, department.name, ST_AsGeoJSON(department.geometry) :: json -> 'coordinates'  AS polygon, region.code AS reg_code
           FROM department INNER JOIN region ON department.region_id = region.id""" 

query_ecpi = """SELECT DISTINCT ON (epci.code) epci.code, epci.name, ST_AsGeoJSON(epci.geometry) :: json -> 'coordinates'  AS polygon, region.code AS reg_code
           FROM epci INNER JOIN city ON city.epci_id = epci.id INNER JOIN department ON city.department_id = department.id INNER JOIN region ON department.region_id = region.id""" 
query_city = """SELECT DISTINCT ON (city.code) city.code, city.name, ST_AsGeoJSON(city.geometry) :: json -> 'coordinates'  AS polygon, region.code AS reg_code
           FROM city INNER JOIN department ON city.department_id = department.id INNER JOIN region ON department.region_id = region.id""" 

queries = [query_dep, query_ecpi, query_city]
extension = ['_dep', '_epci', '_com']
maps_dir = './maps/'

for query, ext in zip(queries, extension):
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn)
    for reg in regions:
        file_dep = 'region_' + reg + ext +'.geojson'
        contour = {'type': 'FeatureCollection', 
                   'features': [{'type': 'Feature', 
                                 'properties': {'code': row[1], 'nom': row[2]}, 
                                 'geometry': {'type': ('MultiPolygon' if str(row[3])[:4] == '[[[[' else 'Polygon'), 'coordinates': row[3]}} 
                                for row in list(df.itertuples()) if row[4] == reg]}
        print(reg, ext)
        if len(contour['features']):
            with open(maps_dir + file_dep, 'w', encoding ='utf8') as map_file:
                json.dump(contour, map_file)
            print(contour['features'][0]['properties'])

```

```python
data = requests.get(source_dir + 'epci-100m.geojson')
jsn = json.loads(data.content)
print([feature['properties'] for feature in jsn['features']])
```

```python
import json 
import requests

reg_metro = ['11', '24', '27', '28', '32', '44', '52', '53', '75', '76', '84', '93', '94']
dpt_metro = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '21', '22', '23', '24', '25', '26', '27', '28', '29',
             '2A', '2B', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55',
             '56', '57', '58', '59', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77', '78', '79', '80', '81', '82', '83', 
             '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95']
# ara_dep = 
source_dir = 'https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/2024/geojson/'
maps_dir = './maps/'

# une seule map pour l'instant -> à compléter
maps = [ ['regions-100m.geojson', reg_metro, 'metropole_reg.json'],
         ['departements-100m.geojson', dpt_metro, 'metropole_dep.json']
       ]
for map in maps[:1]:
    data = requests.get(source_dir + map[0])
    jsn = json.loads(data.content)
    # print([feature['properties']['code'] for feature in jsn['features']])
    print(jsn['features'][0])
    contour = {'type': 'FeatureCollection', 'features': [feature for feature in jsn['features'] if feature['properties']['code'] in map[1]]}
    #print([feature['properties']['code'] for feature in contour['features']])
    with open(maps_dir + map[2], 'w', encoding ='utf8') as map_file:
        json.dump(contour, map_file)

```

## Utilisation des fichiers

Dans le menu `Admin settings / Maps / add a map` de Metabase, les informations suivantes sont à documenter:

- name (nom de la map),
- URL du fichier (geojson),
- id (lien avec les données à représenter - property geojson),
- name (nom affiché - property geojson)

exemple : https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions-version-simplifiee.geojson (property_id = code_region)

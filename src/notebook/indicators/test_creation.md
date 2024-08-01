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

# QualiCharge data: Test of indicators creation
Example of indicators creation

```python
import pandas as pd
import util, gen_indicators
```

## Principes
Chaque indicateur est défini par un id (ex. 'i1'), un nom (ex. 'cumul de puissance par région'), une source (ex. 'static'), une table destination (ex. 'i1_indicator') et une fonction de calcul (ex. 'indic_i1').

Ces données de configuration sont gérées de façon séparée (ex. fichier .INI).

Les données sources (DataFrame) sont issues des tables présentes. Elles sont définies par une requète gérée également de façon séparée (ex. fichier .INI).

Les fonctions de calcul sont présentes dans un fichier python séparé pour ne pas encombrer les notebooks.


## Données de configuration


Exemples sous la forme de dictionnaires
- indicators_dict : liste des indicateurs avec les informations associées
- sql_sources_dict : liste des données source utilisées pour le calcul des indicateurs avec les requètes SQL associées

```python
# ou bien à lire dans un fichier de config (ex. .INI)
indicators_dict = {
    'i1': {
        'name': 'nombre de pdc par departement',
        'table': 'i1_indicator',
        'create': 'indic_i1',
        'source': 'static'}
}
```

```python
# ou bien à lire dans un fichier de config (ex. .INI)
sql_sources_dict = {
    'station': 'SELECT * FROM Station',
    'pdc': 'SELECT * FROM PointDeCharge',
    'static': """
        SELECT
          Amenageur.nom_amenageur,
          Amenageur.siren_amenageur,
          Amenageur.contact_amenageur,
          Operateur.nom_operateur,
          Operateur.contact_operateur,
          Operateur.telephone_operateur,
          Enseigne.nom_enseigne,
          Station.id_station_itinerance,
          Station.id_station_local,
          Station.nom_station,
          Station.implantation_station,
          Localisation.adresse_station,
          Localisation.code_insee_commune,
          ST_AsGeoJSON(Localisation."coordonneesXY") :: json -> 'coordinates'  as coordonneesXY,
          Station.nbre_pdc,
          PointDeCharge.id_pdc_itinerance,
          PointDeCharge.id_pdc_local,
          PointDeCharge.puissance_nominale,
          PointDeCharge.prise_type_ef,
          PointDeCharge.prise_type_2,
          PointDeCharge.prise_type_combo_ccs,
          PointDeCharge.prise_type_chademo,
          PointDeCharge.prise_type_autre,
          PointDeCharge.gratuit,
          PointDeCharge.paiement_acte,
          PointDeCharge.paiement_cb,
          PointDeCharge.paiement_autre,
          PointDeCharge.tarification,
          Station.condition_acces,
          PointDeCharge.reservation,
          Station.horaires,
          PointDeCharge.accessibilite_pmr,
          PointDeCharge.restriction_gabarit,
          Station.station_deux_roues,
          Station.raccordement,
          Station.num_pdl,
          Station.date_mise_en_service,
          PointDeCharge.observations,
          Station.date_maj,
          PointDeCharge.cable_t2_attache
        FROM
          PointDeCharge
          INNER JOIN Station ON PointDeCharge.station_id = Station.id
          INNER JOIN Amenageur ON Station.amenageur_id = Amenageur.id
          INNER JOIN Operateur ON Station.operateur_id = Operateur.id
          INNER JOIN Enseigne ON Station.enseigne_id = Enseigne.id
          INNER JOIN Localisation ON Station.localisation_id = Localisation.id
        """
}
```

## Génération des indicateurs

```python
import os
from sqlalchemy import create_engine

# Get database URL from the environment
database_url = os.getenv("DATABASE_URL")

# Create a database engine that will be used to generate connections
engine = create_engine(database_url)

# choix des indicateurs à mettre à jour
indics = ['i1']

# initialisation de la liste des DataFrame sources pour les indicateurs à mettre à jour
data_sources = util.init_data_sources(indics, indicators_dict, sql_sources_dict, engine)
print({name: len(data) for name, data in data_sources.items()})
```

```python
# creation des tables des indicateurs définis dans la liste 'indics'
for name in indics:
    print('\nindicator : ' + name + '\n')
    indic_att = indicators_dict['name']
    
    # DataFrame source
    indic_source = data_sources[indic_att['source']]

    # Génération de l'indicateur (DataFrame) par appel de la fonction définie par le paramètre 'create'
    indic_df = vars(gen_indicators)[indic_att['create']](indic_source)

    # Génération de la table définie par le paramètre 'table'
    util.indic_to_table(indic_df, indic_att['table'], engine, option="replace")

# ajouter/mettre à jour une table avec les indicateurs présents et leur date de mise à jour
```

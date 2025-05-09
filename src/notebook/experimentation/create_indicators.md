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

La liste des indicateurs est présentée dans le [notebook de présentation des indicateurs](../indicators/reference_indicators.md).
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
import os
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
from create_query import to_indicator #, create_table_pop

# Connecteur à la base Qualicharge
engine = create_engine(os.getenv("DATABASE_URL"))

```

<!-- #region editable=true slideshow={"slide_type": ""} -->
## Structure des indicateurs
<!-- #endregion -->

### Codification des indicateurs

Voir le notebook de présentation des indicateurs.


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
# Représentation avec les colonnes optionnelles associées aux paramètres de la requête
to_indicator(engine, 'i1-01-93-02', simple=False)
```

Pour tous les indicateurs, la structure est identique. L'historisation des données peut donc s'effectuer dans une table dédiée (avec l'ajout d'un timestamp). 

Par exemple, on pourrait avoir une table 'histo' et y stocker la valeur totale 'i1' quotidiennement et la valeur par région 'i1---01' mensuellement.

Pour avoir un historique sur le nombre de pdc en PACA, la table serait filtrée avec level=01 et area=93

```python
# représentation avec un timestamp.
to_indicator(engine, 'i1-01-93-02', histo=True)
```

```python
# représentation sous forme de JSON
to_indicator(engine, 'i1-01-93-02', format='json', json_orient='records')
```

```python
# représentation sous forme de table (retourne le nombre de lignes de la table)
to_indicator(engine, 'i1-01-93-02', format='table')
```

```python
# représentation sous forme de requète PostgreSQL
print(to_indicator(engine, 'i1', format='query'))
```

## Infrastructure - quantitatif

Indicateurs pris en compte : 'i1' à 'i9'

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
to_indicator(engine, 'i1-00-00-00', simple=False)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i1', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i1', simple=True, format='query', query_gen=True)
print(query_gen)
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
query_gen = to_indicator(engine, 'i1-01-93-02', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
### I2 : Nombre de points de recharge ouverts au public pour 100 000 habitants

'nb_pdc_pop' est le nombre de points de recharge pour 100 000 habitants.
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 'i2')
```

```python
to_indicator(engine, 'i2-00-00-00', simple=False)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i2', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i2', simple=True, format='query', query_gen=True)
print(query_gen)
```

#### requête globale avec critère

```python
to_indicator(engine, 'i2-00-00-01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i2-00-00-01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i2---01', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 'i2-01-93-00')
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i2-01-93-00', simple=True, format='query'))
```

```python
to_indicator(engine, 'i2-01-93')
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i2-01-93', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
paca_epci = 'i2-01-93-02'
to_indicator(engine, paca_epci, simple=True)[:10]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i2-01-93-02', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i2-01-93-02', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
### I3 : Nombre de points de recharge ouverts au public pour 100 km2

'nb_pdc_area' est le nombre de points de recharge pour 100 km2.
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 'i3')
```

```python
to_indicator(engine, 'i3-00-00-00', simple=False)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i3', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i3', simple=True, format='query', query_gen=True)
print(query_gen)
```

#### requête globale avec critère

```python
to_indicator(engine, 'i3-00-00-01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i3-00-00-01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i3---01', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 'i3-01-93-00')
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i3-01-93-00', simple=True, format='query'))
```

```python
to_indicator(engine, 'i3-01-93')
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i3-01-93', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
paca_epci = 'i3-01-93-02'
to_indicator(engine, paca_epci, simple=True)[:10]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i3-01-93-02', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i3-01-93-02', simple=True, format='query', query_gen=True)
print(query_gen)
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
print(to_indicator(engine, 'i4', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i4', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python
to_indicator(engine, 'i4-0-xx-01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i4-0-xx-01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i4-0-xx-01', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 'i4-01-93-0')
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i4-01-93-0', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i4-01-93-0', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
to_indicator(engine, 'i4-01-93-03')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i4-01-93-03', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i4-01-93-03', simple=True, format='query', query_gen=True)
print(query_gen)
```

### I5 : Nombre de stations ouvertes au public pour 100 000 habitants

'nb_stat_pop' est le nombre de stations pour 100 000 habitants.

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 'i5-0', simple=True)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i5', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i5', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python
to_indicator(engine, 'i5-0-xx-01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i5-0-xx-01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i5-0-xx-01', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 'i5-01-93-0')
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i5-01-93-0', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i5-01-93-0', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
to_indicator(engine, 'i5-01-93-03')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i5-01-93-03', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i5-01-93-03', simple=True, format='query', query_gen=True)
print(query_gen)
```

### I6 : Nombre de stations ouvertes au public pour 100 km2

'nb_stat_area' est le nombre de stations pour 100 km2.

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 'i6-0', simple=True)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i6', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i6', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python
to_indicator(engine, 'i6-0-xx-01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i6-0-xx-01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i6-0-xx-01', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 'i6-01-93-0')
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i6-01-93-0', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i6-01-93-0', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
to_indicator(engine, 'i6-01-93-03')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i6-01-93-03', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i6-01-93-03', simple=True, format='query', query_gen=True)
print(query_gen)
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
print(to_indicator(engine, 'i7', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i7', simple=True, format='query', query_gen=True)
print(query_gen)
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
print(to_indicator(engine, 'i7-0--01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i7-0--01', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 'i7-01-93-00', simple=True)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i7-01-93-00', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i7-01-93-00', simple=True, format='query', query_gen=True)
print(query_gen)
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

<!-- #region editable=true slideshow={"slide_type": ""} -->
### I8 : Puissance installée pour 100 000 habitants

'p_nom_pop' est la puissance nominale cumulée pour 100 000 habitants
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 'i8', simple=True)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i8', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i8', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python
to_indicator(engine, 'i8-0--01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i8-0--01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i8-0--01', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 'i8-01-93-00', simple=True)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i8-01-93-00', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i8-01-93-00', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python
i7_paca_city = to_indicator(engine, 'i8-01-93-04', simple=True)
i7_paca_city[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i8-01-93-04', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i8-01-93-04', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
### I9 : Puissance installée pour 100 km2

'p_nom_area' est la puissance nominale cumulée pour 100 km2.
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 'i9', simple=True)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i9', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i9', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python
to_indicator(engine, 'i9-0--01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i9-0--01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i9-0--01', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 'i9-01-93-00', simple=True)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i9-01-93-00', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i9-01-93-00', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python
i7_paca_city = to_indicator(engine, 'i9-01-93-04', simple=True)
i7_paca_city[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 'i9-01-93-04', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 'i9-01-93-04', simple=True, format='query', query_gen=True)
print(query_gen)
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
print(to_indicator(engine, 't1-00', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't1-00', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python
to_indicator(engine, 't1-0-xx-01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't1-0-xx-01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't1-0-xx-01', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 't1-02-75')
```

```python
to_indicator(engine, 't1-02-75', histo=True)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't1-02-75', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't1-02-75', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
to_indicator(engine, 't1-02-93-04')[:10]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't1-02-93-04', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't1-02-93-04', simple=True, format='query', query_gen=True)
print(query_gen)
```

### T2 : Pourcentage de points de recharge par niveau de puissance

Indicateur similaire à 't1' ( 'pct_nb_pdc' remplace 'nb_pdc').

'pct_nb_pdc' est le pourcentage de pdc pour le niveau de puissance.

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 't2', simple=False)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't2', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't2', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python
to_indicator(engine, 't2-0-xx-01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't2-0-xx-01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't2-0-xx-01', simple=True, format='query', query_gen=True)
print(query_gen)
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

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
to_indicator(engine, 't2-02-93-04')[:10]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't2-02-93-04', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't2-02-93-04', simple=True, format='query', query_gen=True)
print(query_gen)
```

### T3 : Nombre de stations par nombre de points de recharge

'nb_stations' est le nombre de stations.

'nb_pdc' est le nombre de pdc.

ex. il y a 2790 stations (nb_stations) avec un seul pdc (nb_pdc).

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
to_indicator(engine, 't3-00', simple=False)[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't3', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't3', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python
to_indicator(engine, 't3-0-xx-01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't3-0-xx-01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't3-0-xx-01', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
to_indicator(engine, 't3-04-13001', simple=False)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't3-04-13001', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't3-04-13001', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
to_indicator(engine, 't3-02-93-04')[:10]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't3-02-93-04', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't3-02-93-04', simple=True, format='query', query_gen=True)
print(query_gen)
```

### T4 : Pourcentage de stations par nombre de points de recharge

Indicateur similaire à 't3' ( 'pct_nb_stations' remplace 'nb_stations').

'pct_nb_stations' est le pourcentage de stations avec un nombre de pdc donné.

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 't4', simple=False)[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't4', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't4', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python
to_indicator(engine, 't4-0-xx-01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't4-0-xx-01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't4-0-xx-01', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
to_indicator(engine, 't4-04-13001', simple=False)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't4-04-13001', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't4-04-13001', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
to_indicator(engine, 't4-02-93-04')[:10]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't4-02-93-04', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't4-02-93-04', simple=True, format='query', query_gen=True)
print(query_gen)
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
print(to_indicator(engine, 't5', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't5', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python
to_indicator(engine, 't5-0-xx-01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't5-0-xx-01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't5-0-xx-01', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 't5-03-200023414', simple=False)
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't5-03-200023414', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't5-03-200023414', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
to_indicator(engine, 't5-03-200023414-04')[:10]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't5-03-200023414-04', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't5-03-200023414-04', simple=True, format='query', query_gen=True)
print(query_gen)
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
print(to_indicator(engine, 't6', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't6', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python
to_indicator(engine, 't6-0-xx-01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't6-0-xx-01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't6-0-xx-01', simple=True, format='query', query_gen=True)
print(query_gen)
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

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
to_indicator(engine, 't6-03-200023414-04')[:10]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't6-03-200023414-04', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't6-03-200023414-04', simple=True, format='query', query_gen=True)
print(query_gen)
```

### T8 : Nombre de stations par opérateur

'nb_stations' est le nombre de stations.

'nom_operateur' est le nom de l'opérateur.

ex. il y a 3010 stations (nb_stations) IZIVIA (nom-operateur).

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 't8')
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't8', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't8', simple=True, format='query', query_gen=True))
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python
to_indicator(engine, 't8-0-xx-01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't8-0-xx-01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't8-0-xx-01', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 't8-03-200023414')
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't8-03-200023414', simple=True, format='query'))
```

```python
print(to_indicator(engine, 't8-01-93', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't8-01-93', simple=True, format='query'))
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
to_indicator(engine, 't8-01-93-02')[:10]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't8-01-93-03', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't8-01-93-03', simple=True, format='query', query_gen=True)
print(query_gen)
```

### T9 : Pourcentage de stations par opérateur

'pct_nb_stations' est le nombre de stations.

'nom_operateur' est le nom de l'opérateur.

ex. il y a 3010 stations (nb_stations) IZIVIA (nom-operateur).

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

```python
to_indicator(engine, 't9')
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't9', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't9', simple=True, format='query', query_gen=True))
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

```python
to_indicator(engine, 't9-0-xx-01')[:5]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't9-0-xx-01', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't9-0-xx-01', simple=True, format='query', query_gen=True)
print(query_gen)
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

```python
to_indicator(engine, 't9-03-200023414')
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't9-03-200023414', simple=True, format='query'))
```

```python
print(to_indicator(engine, 't9-01-93', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't8-01-93', simple=True, format='query'))
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
to_indicator(engine, 't9-01-93-02')[:10]
```

```python editable=true slideshow={"slide_type": ""}
print(to_indicator(engine, 't9-01-93-03', simple=True, format='query'))
```

```python editable=true slideshow={"slide_type": ""}
query_gen = to_indicator(engine, 't9-01-93-03', simple=True, format='query', query_gen=True)
print(query_gen)
```

## Historisation

Concerne les indicateurs précédents pour un niveau d'historisation donné


### Indicateurs sans catégorie

```python
# 'i1-d-2-27-2 entre le 1/1/2024 et le 3/1/2024
interval_start = '2024-01-01'
interval_end = '2024-01-03'

#indic = temporal_indicator('i1', '27', 'd', interval_start, interval_end, perim=2, val=27)
```

<!-- #region -->
```sql
SELECT
  value AS nb_pdc, 
  target AS department, 
  timestamp
FROM
  histo
  INNER JOIN Department on target = Department.code
WHERE
  histo.code = 'i1' AND level::int = '2' AND period = 'd' AND
  timestamp >= '2024-01-01' AND timestamp < '2024-01-03'
  AND department.code = '27'
```
<!-- #endregion -->

### Indicateurs avec catégorie

```python
# 't8-d-2-27-2' entre le 1/1/2024 et le 3/1/2024
interval_start = '2024-01-01'
interval_end = '2024-01-03'

#indic = temporal_indicator('t8',Level.DEPARTMENT, IndicatorPeriod.DAY, interval_start, interval_end, perim=2, val=27)
```

<!-- #region -->
```sql
SELECT
  value AS nb_stations, 
  category AS nom_operateur,
  target AS department, 
  timestamp
FROM
  histo
  INNER JOIN Department on target = Department.code
WHERE
  histo.code = 't8' AND level::int = '2' AND period = 'd' AND
  timestamp >= '2024-01-01' AND timestamp < '2024-01-03'
  AND department.code = '27'
```
<!-- #endregion -->

### Autres indicateurs de typologie

Les indicateurs liés à d'autres typologies (ex. opérateurs, accès deux roues, période d’ouverture, accès handicapés…) sont à définir.

Ceux concernant les opérateurs sont prioritaires.

<!-- #region editable=true slideshow={"slide_type": ""} -->
## Autres indicateurs à prendre en compte

- Indicateurs d'historique (traitement des données historisées)
- Infrastructure - réseau autoroute (nécessite l'identification des stations de ce réseau)
- Usage - quantitatif (traitement des données dynamiques) 
- Usage - qualité de service (traitement des données dynamiques)
- Indicateurs étendus (en lien avec des données externes - ex. trafic, immatriculation, consommation ENEDIS)
<!-- #endregion -->

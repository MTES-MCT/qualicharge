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
# Indicateurs de référence QualiCharge

Ce Notebook présente les indicateurs de références gérés sous Qualicharge.

La première partie est une présentation générale des indicateurs.

La deuxième partie est la représentation de chaque indicateur sous forme de requête SQL.

*Nota 1 : La dimension temporelle des indicateurs n'est pas prise en compte, elle sera ajoutée dans une version ultérieure*

*Nota 2 : La représentation visuelle des indicateurs (ex. diagramme circulaire, diagramme à barre, carte choroplèthe, courbe...) n'est pas abordée.*
<!-- #endregion -->

# PARTIE 1 : Présentation générale

## Introduction

Les indicateurs sont constitués d'une liste de valeurs. On distingue les types suivants :

- scalaire (une seule valeur numérique)
- temporel (une liste de valeurs associées à un index temporel),
- catégorie (une liste de valeurs associées à un index catégoriel)
- multiple (multi-dimensionnel: une liste de valeurs associées à plusieurs index)

Les indicateurs peuvent être:

- dynamiques : générés dynamiquement à partir de l'état courant des données,
- historisés : générés périodiquement (heure, jour, mois ou année) et stockés pour être réutilisés.

Par exemple, le nombre de points de recharge est un indicateur dynamique mais si l'on souhaite disposer d'un indicateur de l'évolution du nombre de points de recharges, celui-ci doit être historisé.

Un indicateur peut être visualisé suivant différentes représentations. Par exemple, un indicateur de type 'catégorie' peut être représenté par :

- un tableau à deux colonnes,
- un diagramme en barres,
- un diagramme circulaire,
- une carte choroplèthe (si l'index de l'indicateur est associé à une carte).

Un [indicateur historisé](./historisation.md) peut être représenté en fonction de sa dimension temporelle. Par exemple:

- une moyenne sur une période,
- un historique sur une période,
- état courant.

Le mode de représentation d'un indicateur n'est pas abordé.

## Exemple - baromètre AVERE

Les indicateurs présentés dans le {term}`Baromètre AVERE` sont les suivants :

- chiffres clés :
  - Nombre total de points de recharge ouverts au public
  - Taux d'évolution sur 12 mois
  - Taux de disponibilité moyen d'un point de charge
  - Points de recharge en moyenne pour 100 000 habitants
- répartition spatiale (cartes choroplèthes) :
  - Nombre de stations de recharge par région
  - Nombre de points de recharge par région
  - Puissance totale installée par région
- typologie (diagrammes circulaires) :
  - Répartition des points de recharge par type de site d’implantation
  - Recharge selon la catégorie de puissance
  - Recharge selon la catégorie de puissance par région (diagramme en barres empilées)
- évolution (diagramme en barre)
  - Evolution du nombre de points de recharge par année
  - Évolution du nombre de points de recharge par mois
- usage (diagramme en barres)
  - Nombre de sessions moyen mensuel par point de recharge
  - Taux de disponibilité du mois par catégorie de puissance

## Structure des indicateurs

### Types d'indicateurs

Cinq types d'indicateurs sont définis:

- indicateurs d'infrastructure : Ils décrivent le parc installé (évolution temporelle, répartition géographiques, caratéristiques, dimensionnement)
- indicateurs d'usage : Ils décrivent l'utilisation effective des infrastructures (qualité de service, volumétrie, répartition)
- indicateurs temporels : Ils analysent l'évolution des deux catégories d'indicateurs précédent sur une période temporelle
- indicateurs d'état : Ils représentent un état d'une partie des données (ex. liste des stations du réseau autoroutier)
- indicateurs étendus : Ils concernent les indicateurs obtenus avec des jeux de données en lien (ex. relevés ENEDIS)

*Les indicateurs d'exploitation (liés aux aménageurs et enseignes) ainsi que les indicateurs liés à des attributs spécifiques (ex. accès deux roues, période d'ouverture, accès handicapés...) sont à ajouter.*

### Codification des indicateurs

Les indicateurs sont codifiés par une chaine de caractères : *[type]-[périmètre]-[valeur de périmètre]-[level]*

ou bien pour les indicateurs temporels : *[type]-[périodicité]-[périmètre]-[valeur de périmètre]-[level]*

avec:

- type : identifiant du type d'indicateur (ex. 'i1' : nombre de points de recharge)
- période : périodicité des données utilisées
  - y : données annuelles
  - m : données mensuelles
  - w : données hebdomadaires
  - d : données quotidiennes
- périmètre et valeur de périmètre: sous ensemble des données sur lequel appliquer l'indicateur. Les périmètres actuellement définis sont les découpages administratifs :
  - 0: national (valeur : 00 tout, 01 métropole, 02 DOM, 03 TOM, 04 métropole et DOM)
  - 1: région (valeur : code de la région)
  - 2: département (valeur : code du département)
  - 3: EPCI (valeur : code de l'EPCI)
  - 4: commune (valeur : code de la commune)
  - 5: métropole (sans valeur)
- level : niveau de découpage du résultat (découpage administratif - voir périmètre). Les valeurs associées à un 'level' sont dénommées 'target'.

Le périmètre par défaut est l'ensemble des données.

*Exemples*
- **t4-4-74012** : Pourcentage de stations par nombre de points de recharge (t4) pour la ville (4) d'Annemasse (74012)
- **i1-1-93** : Nombre de points de recharge (i1) pour la région (1) PACA (93)
- **i1-1-93-3** : Nombre de points de recharge (i1) pour la région (1) PACA (93) par EPCI (3)
- **i1-m-1-93-3** : Nombre de points de recharge (i1) mensuel (m) pour la région (1) PACA (93) par EPCI (3)
- **t1** : Nombre de points de recharge par niveau de puissance (t1) pour l'ensemble des données (pas de périmètre choisi)
- **e1** : liste des stations du réseau autoroutier (e1)

### Résultat des indicateurs

Le résultat d'un indicateur peut être représenté par une structure tabulaire composée des champs suivants :

- valeur : résultat de l'indicateur pour une catégorie et une target,
- valeur additionnelle : informations associées à la valeur
- catégorie (facultative) : décomposition associée à l'indicateur
- target (facultative) : découpage associé au level choisi

Le champ 'valeur additionnelle' est utilisé pour les données structurées associées au champ 'valeur'.

Ce champ est au format JSON et concerne les informations liées à l'historisation ainsi que les données des indicateurs d'état.

Si aucune catégorisation et aucun level ne sont définis, le résultat se réduit à une valeur.

*Exemple*

'i1' : le résultat est le nombre de points de recharge (valeur)

Si uniquement une catégorisation est définie, le résultat est une liste de valeurs associées à chaque catégorie.

*Exemple*

't1' : le résultat est le nombre de points de recharge (valeur : nb_pdc) par niveau de puissance (catégorie : p_range)

| nb_pdc | p_range      |
| ------ | ------------ |
| 10892  | [15.0, 26.0) |
| 4807   | [175, 360.0) |
| 3282   | [65, 175.0)  |
| 2359   | [26, 65.0)   |
| 2157   | [0, 15.0)    |
| 25     | [360, None)  |

Si uniquement un level est défini, le résultat est une liste de valeurs associées à chaque target.

*Exemple*

i1-1-93-2 : Nombre de points de recharge (i1) pour la région (1) PACA (93) par département (2)

Le résultat est le nombre de points de recharge (valeur : nb_pdc) par département (target : code du département).

| nb_pdc | code   |
| ------ | ------ |
| 473    | 13     |
| 450    | 06     |
| 175    | 83     |
| 170    | 84     |
| 105    | 04     |
| 57     | 05     |

Si une catégorisation et un level sont définis, le résultat est une liste de valeurs associées à chaque target et à chaque catégorie.

*Exemple*

t8-1-93-2 : Nombre de stations par opérateur (t8) pour la région (1) PACA (93) par département (2)

La 'target' est ici le département (représenté par son code) et la 'catégorie' est l'opérateur (nom_operateur).

| nb_stat | nom_operateur                   | code   |
| ------- | ------------------------------- | ------ |
| 273     | IZIVIA                          | 06     |
| 31      | IZIVIA                          | 13     |
| 28      | TotalEnergies Charging Services | 13     |
| 21      | LUMI'IN                         | 84     |
| 16      | Power Dot France                | 13     |
| 10      | LUMI'IN                         | 04     |
| 8       | Last Mile Solutions             | 13     |
| 7       | CAR2PLUG                        | 83     |
| 7       | Bump                            | 13     |
| 7       | Power Dot France                | 84     |

## Indicateurs d'infrastructure

### Infrastructure - typologie

Objectif :

- analyse de la typologie (comparaison des ratios)

| id          | nom                                                       | Pr  | type  | historisé             |
| ----------- | --------------------------------------------------------- | --- | ----- | --------------------- |
| t1-xx-yy-zz | Nombre de points de recharge par niveau de puissance      | 1   | infra | oui (national/région) |
| t2-xx-yy-zz | Pourcentage de points de recharge par niveau de puissance | 2   | infra | synthèse              |
| t3-xx-yy-zz | Nombre stations par nombre de points de recharge          | 1   | infra | non                   |
| t4-xx-yy-zz | Pourcentage de stations par nombre de points de recharge  | 2   | infra | non                   |
| t5-xx-yy-zz | Nombre de stations par type d'implantation                | 1   | infra | oui (national/région) |
| t6-xx-yy-zz | Pourcentage de stations par type d'implantation           | 2   | infra | synthèse              |
| t7-xx-yy-zz | Densité EPCI (nb EPCI avec / nb EPCI total)               | 3   | infra | oui (national/région) |
| t8-xx-yy-zz | Nombre stations par opérateur                             | 1   | infra | oui (national/région) |
| t9-xx-yy-zz | Pourcentage de stations par opérateur                     | 2   | infra | synthèse              |

L'identification des opérateurs (nom) est actuellment facultative (à rendre obligatoire).

La classification des niveaux de puissances nominale est à valider (en liaison avec le type d'alimentation AC/DC). La classification retenue actuellement est la suivante : 0-15 / 15-26 / 26-65 / 65-175 / 175-360 / > 360 (valeurs de seuil choisies à partir de l'existant Qualicharge).

### Infrastructure - quantitatif

Objectif:

- analyse de la répartition géographique (les ratios permettent les comparaisons)

| id          | nom                                              | Pr  | type  | historisé              |
| ----------- | ------------------------------------------------ | --- | ----- | ---------------------- |
| i1-xx-yy-zz | Nombre de points de recharge ouverts au public   | 1   | infra | oui (département/EPCI) |
| i2-xx-yy-zz | Ratio pour 100 000 habitants                     | 1   | infra | synthèse               |
| i3-xx-yy-zz | Ratio pour 100 km2                               | 2   | infra | synthèse               |
| i4-xx-yy-zz | Nombre de stations de recharge ouverts au public | 1   | infra | oui (département/EPCI) |
| i5-xx-yy-zz | Ratio pour 100 000 habitants                     | 1   | infra | synthèse               |
| i6-xx-yy-zz | Ratio pour 100 km2                               | 2   | infra | synthèse               |
| i7-xx-yy-zz | Puissance installée                              | 1   | infra | oui (département/EPCI) |
| i8-xx-yy-zz | Ratio pour 100 000 habitants                     | 1   | infra | synthèse               |
| i9-xx-yy-zz | Ratio pour 100 km2                               | 2   | infra | synthèse               |

zz : critère de répartition par périmètre (ex. 02 : répartition par département)

## Indicateurs d'infrastructure du réseau autoroutes

Objectif:

- analyse du niveau d'équipement des stations
- analyse de la couverture des trajets nationaux
- analyse de la répartition par station

### Indicateurs globaux

| id  | nom                                                                | Pr  | type  | historisé |
| --- | ------------------------------------------------------------------ | --- | ----- | --------- |
| a1  | Nombre de points de recharge (i1-xx)                               | 1   | infra | oui       |
| a2  | Nombre de stations de recharge (i4-xx)                             | 2   | infra | oui       |
| a3  | Puissance installée (i7-xx)                                        | 2   | infra | oui       |
| a4  | Nombre de points de recharge par niveau de puissance (t1-xx)       | 1   | infra | non       |
| a5  | Densité des stations équipées (nb stations équipées / nb stations) | 3   | infra | oui       |
| a6  | Distance moyenne inter-station de recharge                         | 3   | infra | oui       |

ex. Suivi du déploiement des IRVE dans les stations (nécessite de disposer du nombre de stations).

ex. Suivi temporel de la distance interstation (utilisation du graphe pour calculer les distances de recharge associée à chaque station).

### Indicateurs par station

| id  | nom                                    | Pr  | type  | historisé |
| --- | -------------------------------------- | --- | ----- | --------- |
| a7  | Puissance installée par station        | 2   | infra | non       |
| a8  | Nombre de points de charge par station | 2   | infra | non       |
| a9  | Distance de recharge par station       | 2   | infra | non       |

ex. Analyse de la distance interstation (zones blanches).

## Indicateurs d'usage

### Usage - quantitatif

- analyse de l'évolution temporelle de l'utilisation

| id          | nom                                  | Pr  | type  | historisé             |
| ----------- | ------------------------------------ | --- | ----- | --------------------- |
| u1-xx-yy-zz | Nombre de point de charge actif      | 2   | usage | oui (national/région) |
| u2-xx-yy-zz | Pourcentage de point de charge actif | 2   | usage | synthèse              |
| u3-xx-yy-zz | Nombre de sessions                   | 2   | usage | oui (national/région) |
| u4-xx-yy-zz | Energie distribuée                   | 2   | usage | oui (national/région) |

u1 est calculé sur une journée

u2 est calculé à partir de u1 et i1

u3 et u4 sont calculés par heure

exemple d'utilisation : Analyse du profil horaire de l'énergie fournie en fonction des périodes et de la localisation.

### Usage - qualité de service

- analyse de la disponibilité et de l'utilisation des points de recharge

| id           | nom                                                  | Pr  | type  | historisé             |
| ------------ | ---------------------------------------------------- | --- | ----- | --------------------- |
| q1-xx-yy-zz  | Durée de bon fonctionnement                          | 2   | usage | oui (national/région) |
| q2-xx-yy-zz  | Durée d'utilisation                                  | 2   | usage | oui (national/région) |
| q3-xx-yy-zz  | Durée d'ouverture                                    | 2   | usage | oui (national/région) |
| q4-xx-yy-zz  | Nombre de sessions réussies                          | 3   | usage | oui (national/région) |
| q5-xx-yy-zz  | Saturation                                           | 2   | usage | non                   |
| q6-xx-yy-zz  | Taux de disponibilité d'un point de charge actif     | 2   | usage | synthèse              |
| q7-xx-yy-zz  | Taux de disponibilité par catégorie de puissance     | 3   | usage | synthèse              |
| q8-xx-yy-zz  | Taux d'utilisation d'un point de charge actif        | 2   | usage | synthèse              |
| q9-xx-yy-zz  | Taux de sessions réussies d'un point de charge actif | 2   | usage | synthèse              |
| q10-xx-yy-zz | Taux de saturation d'une station                     | 3   | usage | non                   |

q1, q2, q3, q4 et q5 sont les valeurs cumulées sur une journée
q6, q7 sont calculé à partir de q1 et q3
q8 est calculé à partir de q2 et q3
q9 est calculé à partir de q4 et u3
q10 est calculé à partir de q5

## Indicateurs temporels

Les indicateurs temporels identifiés sont les suivants :

| id            | nom                                              | Pr  | base   | fonction       |
| ------------- | ------------------------------------------------ | --- | ------ | -------------- |
| d1-w-xx-yy-zz | Taux d'évolution du nombre de stations           | 1   | i4     | taux évolution |
| d2-w-xx-yy-zz | Evolution du nombre de points de recharge        | 1   | i1     | historique     |
| d3-w-xx-yy-zz | Nombre de sessions par point de recharge         | 2   | u3     | historique     |
| d4-w-xx-yy-zz | Taux de disponibilité par catégorie de puissance | 2   | q1, q3 | historique     |
| d5-w-xx-yy-zz | Taux de points de recharge avec indispo > 7 j    | 3   | q1, q3 | historique     |

Nota : Seule la périodicité est intégrée à la codification (voir chapitre 'codification'), l'intervalle doit donc être ajouté à l'indicateur.

*Exemple*

Evolution du nombre mensuel de points de recharge pour 2024 par département : (d2-m---4, entre 01/01/2023 et le 01/01/2024)

## Indicateurs d'état

Les indicateurs d'état identifiés sont les suivants :

| id          | nom                                      | Pr  |
| ----------- | ---------------------------------------- | --- |
| e1-xx-yy-zz | Liste des stations du réseau autoroutier | 2   |
| e2-xx-yy-zz | Liste des stations actives               | 2   |

Nota : La périodicité d'historisation n'est pas intégrée à la codification (voir chapitre 'codification'), la date doit donc être ajouté à l'indicateur.

*Exemple*

Liste des stations du réseau autoroutier (d2) au 31/12/2024 

## Indicateurs étendus

Ils concernent le couplage des données avec des jeux de données complémentaires (à définir dans un second temps):

- couplage consommation / trafic
- couplage nombre de véhicules électriques vendus/immatriculés
- couplage consommation / relevés ENEDIS des points de livraison


<!-- #region editable=true slideshow={"slide_type": ""} -->
# PARTIE 2 : Présentation des indicateurs

Les sections suivantes présentent pour chaque indicateur la requête SQL associée pour plusieurs exemples de jeux de paramètres.

Les requêtes sont issues d'un [générateur de requêtes](../misc/create_query.py).

Les résultats de ces requêtes ou la structure paramétrée peuvent être consultés dans le [notebook associé](../misc/create_indicators.md).

Une solution provisoire est utilisée pour le point suivant :

- les catégories de regroupement des puissances nominales des point de recharge sont définies dans la requête. Une structure externe est utilisée dans la version définitive. 
<!-- #endregion -->

## Infrastructure - quantitatif

Indicateurs pris en compte : 'i1', 'i2', 'i3', 'i4', 'i5', 'i6', 'i7', 'i8', 'i9'

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
### I2 : Nombre de points de recharge ouverts au public pour 100 000 habitants

'nb_pdc_pop' est le nombre de points de recharge pour 100 000 habitants.
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 'i2-0-00-0' ou 'i2'

```sql
SELECT 
    (        
        SELECT
            count(id_pdc_itinerance) AS nb_pdc
        FROM
            pointdecharge
    ) / (
        SELECT 
            sum(population) 
        FROM
            region
    ) * 100000 AS nb_pdc_pop
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale avec une répartition par région (01) 'i2-00-00-01' ou 'i2---01'

```sql
WITH
    i1 AS ( 
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
    )
SELECT
    i1.nb_pdc::float / region.population * 100000 AS nb_pdc_pop,
    region.code
FROM
    i1
    LEFT JOIN region on i1.code = region.code
ORDER by
    nb_pdc_pop DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) 'i2-01-93-00' ou 'i2-01-93'

```sql
SELECT 
    (
        SELECT
            count(id_pdc_itinerance) AS nb_pdc    
        FROM
            pointdecharge 
            LEFT JOIN station ON station.id = station_id 
            LEFT JOIN localisation ON localisation_id = localisation.id
            LEFT JOIN city on city.code = code_insee_commune
            LEFT JOIN department on city.department_id = department.id
            LEFT JOIN region on department.region_id = region.id
        WHERE
            region.code = '93'   
        ORDER BY
            nb_pdc DESC
    ) / (
        SELECT 
            sum(population) 
        FROM
            region
        WHERE
            region.code = '93'
    ) * 100000 AS nb_pdc_pop
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) par département (02) 'i2-01-93-02'

```sql
WITH
    i1 AS (        
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
    )
SELECT
    i1.nb_pdc::float / department.population * 100000 AS nb_pdc_pop,
    department.code
FROM
    i1
    LEFT JOIN department on i1.code = department.code
ORDER by
    nb_pdc_pop DESC```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
### I3 : Nombre de points de recharge ouverts au public pour 100 km2

'nb_pdc_area' est le nombre de points de recharge pour 100 km2.
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 'i3-0-00-0' ou 'i3'

```sql
SELECT 
    (        
        SELECT
            count(id_pdc_itinerance) AS nb_pdc
        FROM
            pointdecharge
    ) / (
        SELECT 
            sum(area::float) 
        FROM
        region
    ) * 100000000 AS nb_pdc_area
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale avec une répartition par région (01) 'i3-00-00-01' ou 'i3---01'

```sql
WITH
    i1 AS ( 
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
    )
SELECT
    i1.nb_pdc::float / region.area::float * 100000000 AS nb_pdc_area,
    region.code 
FROM
    i1
    LEFT JOIN region on i1.code = region.code
ORDER by
    nb_pdc_area DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) 'i3-01-93-00' ou 'i3-01-93'

```sql
SELECT 
    (
        SELECT
            count(id_pdc_itinerance) AS nb_pdc    
        FROM
            pointdecharge 
            LEFT JOIN station ON station.id = station_id 
            LEFT JOIN localisation ON localisation_id = localisation.id
            LEFT JOIN city on city.code = code_insee_commune
            LEFT JOIN department on city.department_id = department.id
            LEFT JOIN region on department.region_id = region.id
        WHERE
            region.code = '93'   
        ORDER BY
            nb_pdc DESC
    ) / (
        SELECT 
            sum(area::float) 
        FROM
            region
        WHERE
            region.code = '93'
    ) * 100000000 AS nb_pdc_area
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) par département (02) 'i3-01-93-02'

```sql
WITH
    i1 AS (        
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
    )
SELECT
    i1.nb_pdc::float / department.area::float * 100000000 AS nb_pdc_area,
    department.code
FROM
    i1
    LEFT JOIN department on i1.code = department.code
ORDER by
    nb_pdc_area DESC```
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

### I5 : Nombre de stations ouvertes au public pour 100 000 habitants

'nb_stat_pop' est le nombre de stations pour 100 000 habitants.

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 'i5-0-00-0' ou 'i5'

```sql
SELECT 
    (        
        SELECT
            count(id_station_itinerance) AS nb_stat  
        FROM
            station
    ) / (
        SELECT 
            sum(population) 
        FROM
            region    
    ) * 100000 AS nb_stat_pop
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale avec une répartition par région (01) 'i5-00-00-01' ou 'i5---01'

```sql
WITH
    i4 AS (  
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
    )
SELECT
    i4.nb_stat::float / region.population * 100000 AS nb_stat_pop,
    region.code  
FROM
    i4
    LEFT JOIN region on i4.code = region.code
ORDER by
    nb_stat_pop DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) 'i5-01-93-00' ou 'i5-01-93'

```sql
SELECT 
    (       
        SELECT
            count(id_station_itinerance) AS nb_stat    
        FROM
            station 
            LEFT JOIN localisation ON localisation_id = localisation.id
            LEFT JOIN city on city.code = code_insee_commune
            LEFT JOIN department on city.department_id = department.id
            LEFT JOIN region on department.region_id = region.id
        WHERE
            region.code = '93'
        ORDER BY
            nb_stat DESC
    ) / (
        SELECT 
            sum(population) 
        FROM
            region
        WHERE
            region.code = '93'
    ) * 100000 AS nb_stat_pop
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) par département (02) 'i5-01-93-03'

```sql
WITH
    i4 AS (    
        SELECT
            count(id_station_itinerance) AS nb_stat,
            epci.code
        FROM
            station 
            LEFT JOIN localisation ON localisation_id = localisation.id
            LEFT JOIN city on city.code = code_insee_commune
            LEFT JOIN epci on city.epci_id = epci.id
            LEFT JOIN department on city.department_id = department.id
            LEFT JOIN region on department.region_id = region.id
        WHERE
            region.code = '93'
        GROUP BY
            epci.code
        ORDER BY
            nb_stat DESC
    )
SELECT
    i4.nb_stat::float / epci.population * 100000 AS nb_stat_pop,
    epci.code
FROM
    i4
    LEFT JOIN epci on i4.code = epci.code
ORDER by
    nb_stat_pop DESC```
<!-- #endregion -->

### I6 : Nombre de stations ouvertes au public pour 100 km2

'nb_stat_area' est le nombre de stations pour 100 km2.

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 'i6-0-00-0' ou 'i6'

```sql
SELECT 
    (        
        SELECT
            count(id_station_itinerance) AS nb_stat  
        FROM
            station
    ) / (
        SELECT 
            sum(area::float) 
        FROM
        region
        
    ) * 100000000 AS nb_stat_area
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale avec une répartition par région (01) 'i6-00-00-01' ou 'i6---01'

```sql
WITH
    i4 AS (  
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
    )
SELECT
    i4.nb_stat::float / region.area::float * 100000000 AS nb_stat_area,
    region.code
FROM
    i4
    LEFT JOIN region on i4.code = region.code
ORDER by
    nb_stat_area DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) 'i6-01-93-00' ou 'i6-01-93'

```sql
SELECT 
    (       
        SELECT
            count(id_station_itinerance) AS nb_stat    
        FROM
            station 
            LEFT JOIN localisation ON localisation_id = localisation.id
            LEFT JOIN city on city.code = code_insee_commune
            LEFT JOIN department on city.department_id = department.id
            LEFT JOIN region on department.region_id = region.id
        WHERE
            region.code = '93'
        ORDER BY
            nb_stat DESC
    ) / (
        SELECT 
            sum(area::float) 
        FROM
            region
        WHERE
            region.code = '93'
    ) * 100000000 AS nb_stat_area
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) par département (02) 'i6-01-93-03'

```sql
WITH
    i4 AS (    
        SELECT
            count(id_station_itinerance) AS nb_stat,
            epci.code
        FROM
            station 
            LEFT JOIN localisation ON localisation_id = localisation.id
            LEFT JOIN city on city.code = code_insee_commune
            LEFT JOIN epci on city.epci_id = epci.id
            LEFT JOIN department on city.department_id = department.id
            LEFT JOIN region on department.region_id = region.id
        WHERE
            region.code = '93'
        GROUP BY
            epci.code
        ORDER BY
            nb_stat DESC
    )
SELECT
    i4.nb_stat::float / epci.area::float * 100000000 AS nb_stat_area,
    epci.code    
FROM
    i4
    LEFT JOIN epci on i4.code = epci.code
ORDER by
    nb_stat_area DESC
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
### I8 : Puissance installée pour 100 000 habitants

'p_nom_pop' est la puissance nominale cumulée pour 100 000 habitants
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 'i8-0-00-0' ou 'i8'

```sql
SELECT 
    (   
        SELECT
            sum(puissance_nominale) AS p_nom       
        FROM
            pointdecharge
    ) / (
        SELECT 
            sum(population) 
        FROM
            region
    ) * 100000 AS p_nom_pop
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale avec une répartition par région (01) 'i8-00-00-01' ou 'i8---01'

```sql
WITH
    i7 AS (    
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
    )
SELECT
    i7.p_nom::float / region.population * 100000 AS p_nom_pop,
    region.code
FROM
    i7
    LEFT JOIN region on i7.code = region.code
ORDER by
    p_nom_pop DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) 'i8-01-93-00' ou 'i8-01-93'

```sql
SELECT 
    (  
        SELECT
            sum(puissance_nominale) AS p_nom   
        FROM
            pointdecharge 
            LEFT JOIN station ON station.id = station_id 
            LEFT JOIN localisation ON localisation_id = localisation.id
            LEFT JOIN city on city.code = code_insee_commune
            LEFT JOIN department on city.department_id = department.id
            LEFT JOIN region on department.region_id = region.id
        WHERE
            region.code = '93'
        ORDER BY
            p_nom DESC
    ) / (
        SELECT 
            sum(population) 
        FROM
            region
        WHERE
            region.code = '93'
    ) * 100000 AS p_nom_pop
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) par commune (04) 'i8-01-93-04'

```sql
WITH
    i7 AS (        
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
    )
SELECT
    i7.p_nom::float / city.population * 100000 AS p_nom_pop,
    city.code
FROM
    i7
    LEFT JOIN city on i7.code = city.code
ORDER by
    p_nom_pop DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
### I9 : Puissance installée pour 100 km2

'p_nom_area' est la puissance nominale cumulée pour 100 km2.
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 'i9-0-00-0' ou 'i9'

```sql
SELECT 
    (   
        SELECT
            sum(puissance_nominale) AS p_nom       
        FROM
            pointdecharge
    ) / (
        SELECT 
            sum(area::float) 
        FROM
            region
    ) * 100000000 AS p_nom_area
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale avec une répartition par région (01) 'i9-00-00-01' ou 'i9---01'

```sql
WITH
    i7 AS (    
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
    )
SELECT
    i7.p_nom::float / region.area::float * 100000000 AS p_nom_area,
    region.code  
FROM
    i7
    LEFT JOIN region on i7.code = region.code
ORDER by
    p_nom_area DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) 'i9-01-93-00' ou 'i9-01-93'

```sql
SELECT 
    (  
        SELECT
            sum(puissance_nominale) AS p_nom   
        FROM
            pointdecharge 
            LEFT JOIN station ON station.id = station_id 
            LEFT JOIN localisation ON localisation_id = localisation.id
            LEFT JOIN city on city.code = code_insee_commune
            LEFT JOIN department on city.department_id = department.id
            LEFT JOIN region on department.region_id = region.id
        WHERE
            region.code = '93'
        ORDER BY
            p_nom DESC
    ) / (
        SELECT 
            sum(area::float) 
        FROM
            region
        WHERE
            region.code = '93'
    ) * 100000000 AS p_nom_area
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale avec critère
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur la région (01) PACA (93) par commune (04) 'i9-01-93-04'

```sql
WITH
    i7 AS (        
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
    )
SELECT
    i7.p_nom::float / city.area::float * 100000000 AS p_nom_area,
    city.code
FROM
    i7
    LEFT JOIN city on i7.code = city.code
ORDER by
    p_nom_area DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
## Infrastructure - typologie

Les indicateurs 't1' à 't6' ainsi que 't8' et 't9' sont pris en compte.

L'indicateur 't7' reste à construire.
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

### T8 : Nombre de stations par opérateur

'nb_stations' est le nombre de stations.

'nom_operateur' est le nom de l'opérateur.

ex. il y a 3010 stations (nb_stations) IZIVIA (nom-operateur).

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 't8-00-00' ou 't8'

```sql
SELECT
    count(id_station_itinerance) AS nb_stations,
    nom_operateur
FROM
    station 
    LEFT JOIN operateur ON operateur_id = operateur.id
GROUP BY
    nom_operateur
ORDER BY
    nb_stations DESC
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur l'EPCI (03) Métropole Rouen Normandie (200023414) 't8-03-200023414'
```sql
SELECT
    count(id_station_itinerance) AS nb_stations,
    nom_operateur
FROM
    station 
    LEFT JOIN localisation ON localisation_id = localisation.id
    LEFT JOIN city on city.code = code_insee_commune
    LEFT JOIN epci on city.epci_id = epci.id
    LEFT JOIN operateur ON operateur_id = operateur.id
WHERE
    epci.code = '200023414'
GROUP BY
    nom_operateur
ORDER BY
    nb_stations DESC
```
<!-- #endregion -->

### T9 : Pourcentage de stations par opérateur

'pct_nb_stations' est le nombre de stations.

'nom_operateur' est le nom de l'opérateur.

ex. il y a 3010 stations (nb_stations) IZIVIA (nom-operateur).

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête globale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête globale : 't9-00-00' ou 't9'

```sql
WITH 
    t8 AS (    
        SELECT
            count(id_station_itinerance) AS nb_stations,
            nom_operateur
        FROM
            station 
            LEFT JOIN operateur ON operateur_id = operateur.id
        GROUP BY            
            nom_operateur
        ORDER BY
            nb_stations DESC
    )
SELECT
    nb_stations / (
        SELECT 
            sum(nb_stations) 
        FROM 
            t8
    ) * 100 AS pct_nb_stations,
    nom_operateur
FROM 
    t8
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
#### requête locale
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Exemple requête sur l'EPCI (03) Métropole Rouen Normandie (200023414) 't9-03-200023414'

```sql
WITH 
    t8 AS (       
        SELECT
            count(id_station_itinerance) AS nb_stations,
            nom_operateur    
        FROM
            station 
            LEFT JOIN localisation ON localisation_id = localisation.id
            LEFT JOIN city on city.code = code_insee_commune
            LEFT JOIN epci on city.epci_id = epci.id
            LEFT JOIN operateur ON operateur_id = operateur.id
        WHERE
            epci.code = '200023414'
        GROUP BY
            nom_operateur
        ORDER BY
            nb_stations DESC
    )
SELECT
    nb_stations / (
        SELECT 
            sum(nb_stations) 
        FROM 
            t8
    ) * 100 AS pct_nb_stations,
    nom_operateur
FROM 
    t8
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

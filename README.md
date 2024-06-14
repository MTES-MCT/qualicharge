# QualiCharge

⚠️ Ce projet est en cours de développement. ⚠️

## Objectif du projet

Améliorer la qualité globale du service de recharge pour véhicules électriques
en analysant les données de supervision.

Plus d'information sur la page dédiée à notre startup d'état 👉
https://beta.gouv.fr/startups/qualicharge.html

## Dépendances

Pour travailler sur ce projet, vous aurez besoin d'installer les outils suivants
sur votre poste de travail :

- [Docker](https://www.docker.com)
- [Docker compose](https://docs.docker.com/compose/)
- [GNU Make](https://www.gnu.org/software/make/manual/make.html)

## Démarrage rapide pour les développeurs

Une fois le projet cloné, vous pouvez l'initialiser en utilisant la commande
suivante :

```
make bootstrap
```

> 👉 Cette commande doit préparer votre environnement et builder les images
> Docker nécessaires au démarrage de votre environnement.

Une fois votre environnement de travail initialisé, vous pouvez lancer le projet en
utilisant :

```
make run
```

Les services QualiCharge doivent maintenant tourner sur votre poste :

- la documentation de l'API est accessible sur :
  [http://localhost:8010/api/v1/docs](http://localhost:8010/api/v1/docs)

Pour linter le code source, le point d'entrée est :

```
make lint
```

Et enfin, pour lancer les tests du projet :

```
make test
```

## Utilisation du client d'API et du CLI `qcc`

Voir la documentation du projet : [./src/client/](./src/client/)

## Licence

QualiCharge est distribué selon les termes de la licence MIT (voir le fichier
[LICENSE](./LICENSE)).

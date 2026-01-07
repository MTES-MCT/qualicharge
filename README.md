# QualiCharge

## Objectif du projet

Améliorer la qualité globale du service de recharge pour véhicules électriques
en analysant les données de supervision.

Plus d'information sur la page dédiée à notre startup d'état 👉
https://beta.gouv.fr/startups/qualicharge.html

---

:loudspeaker: Si vous souhaitez vous **connecter** à l'API QualiCharge, nous
vous invitons à consulter notre
[documentation pour les opérateurs](https://fabrique-numerique.gitbook.io/qualicharge/).

---

## Dépendances

Pour travailler sur ce projet, vous aurez besoin d'installer les outils suivants
sur votre poste de travail :

- [Docker](https://www.docker.com)
- [Docker buildx](https://github.com/docker/buildx)
- [Docker compose](https://docs.docker.com/compose/)
- [GNU Make](https://www.gnu.org/software/make/manual/make.html)

## Démarrage rapide pour les développeurs

Vous devez tout d'abord récupérer les sources du projet :

```sh
# Cloner le projet avec SSH
git clone git@github.com:MTES-MCT/qualicharge.git

# Aller dans le repository local du projet
cd qualicharge
```

Une fois le projet cloné, vous pouvez l'initialiser en utilisant la commande
suivante :

```
make bootstrap
```

> 👉 Cette commande doit préparer votre environnement et builder les images
> Docker nécessaires au démarrage de votre environnement.

Une fois votre environnement de travail initialisé, vous pouvez lancer le projet
en utilisant :

```
make run-all
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

## Explorer les données collectées avec Metabase

Si vous avez utilisé la commande `make bootstrap` pour initialiser le projet,
vous devez avoir provisionné une instance de Metabase qui est accessible depuis
un navigateur sur l'URL suivante :
[http://localhost:3000](http://localhost:3000).

> :bulb: Vous pouvez vous connecter en utilisant le login `admin@example.com` et
> le mot de passe `supersecret`.

## Utilisation du client d'API et du CLI `qcc`

Voir la documentation du projet : [./src/client/](./src/client/)

## Utilisation du dashboard

Le dashboard qualicharge est disponible depuis l'url suivante :
[http://localhost:8030](http://localhost:8030).

Voir la documentation du projet dashboard : [./src/dashboard/](./src/dashboard/)

## Licence

QualiCharge est distribué selon les termes de la licence MIT (voir le fichier
[LICENSE](./LICENSE)).

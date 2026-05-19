# PR #997 - Analyse des commentaires de revue

Source : [MTES-MCT/qualicharge#997](https://github.com/MTES-MCT/qualicharge/pull/997)

Releve effectue le 18 mai 2026. Les commentaires portent principalement sur les
modeles tarifaires OCPI ajoutes dans cette PR.

## Synthese

La revue pousse le code vers un modele plus proche d'OCPI et du document metier
mis a jour. Globalement, c'est une bonne direction, mais plusieurs changements
ne sont pas de simples renommages : ils modifient le contrat public de
`POST /statique/tariff/`, la cle fonctionnelle stockee en base, et la semantique
de la date d'application d'un tarif.

Je classerais les changements en trois groupes :

- **A faire** : aligner les noms OCPI, rendre ``country_code`` et `party_id`
  obligatoires, ajouter `tariff_alt_url`, factoriser les champs calcules utiles,
  renforcer les tests.
- **A faire avec migration/contrat explicite** : remplacer `tariff_id` par
  `id` + `tariff_id` calcule, rendre `original_last_updated` et `start` non
  optionnels, changer la valeur stockee dans `raw`.
- **A discuter avant implementation** : forcer `last_updated <= end_date_time`,
  deduire `ocpi_version` de `tax_included`, ajouter une route de hard-delete.

## Contexte code actuel

- `TariffObject` garde aujourd'hui l'identifiant OCPI dans un champ Python
  `tariff_id`, expose sous l'alias JSON `id`
  ([code](../src/api/qualicharge/models/tariff.py#L111)).
- La creation verifie les doublons avec `payload.tariff.tariff_id` et
  `payload.tariff.last_updated`
  ([code](../src/api/qualicharge/api/v1/routers/static.py#L418)).
- `tariff_fields_from_object` persiste `raw.model_dump(by_alias=True, mode="json")`,
  donc le JSON stocke represente le `TariffObject`, pas le payload complet
  `TariffCreate` avec `targets`
  ([code](../src/api/qualicharge/schemas/tariff_utils.py#L28)).
- La table SQL autorise encore `original_last_updated` et `start` a `NULL`
  ([code](../src/api/qualicharge/schemas/tariff.py#L42)).

## Commentaires inline

### Issue 1
- [ ] 1. Payload `TariffCreate`

- Commentaire : [discussion_r3232480414](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3232480414)
- Code : [models/tariff.py](../src/api/qualicharge/models/tariff.py#L145)
- Demande : garder `TariffCreate` avec `targets: List[str] = Field(default_factory=list)`
  et `tariff: TariffObject`.
- Avis : **bonne idee, deja appliquee dans le code actuel**. La forme est claire :
  les cibles de rattachement restent au niveau payload API, tandis que l'objet
  tarifaire reste concentre sur OCPI. Le commentaire est marque outdated cote
  GitHub, ce qui confirme probablement que la PR a deja converge sur cette forme.

<!-- ### Issue 2
- [ ] 2. Renommer `PriceComponentTypeEnum`

- Commentaire : [discussion_r3258905585](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3258905585)
- Code : [models/tariff.py](../src/api/qualicharge/models/tariff.py#L16)
- Demande : utiliser le nom OCPI `TariffDimensionTypeEnum`.
- Avis : **bonne idee**. Le modele vise explicitement OCPI et le commentaire de
  fichier pointe vers un schema OCPI. Le nom actuel `PriceComponentTypeEnum`
  est comprehensible, mais moins standard. Il faudra mettre a jour les factories,
  tests et scripts qui importent `PriceComponentTypeEnum`, notamment
  `src/api/qualicharge/factories/tariff.py` et
  `src/api/scripts/populate_random_tariffs.py`. -->

<!-- ### Issue 3
- [ ] 3. Renommer `DisplayPrice`

- Commentaire : [discussion_r3258935481](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3258935481)
- Code : [models/tariff.py](../src/api/qualicharge/models/tariff.py#L60)
- Demande : utiliser le nom OCPI `PriceLimit`.
- Avis : **bonne idee**. Le type est utilise par `min_price` et `max_price`,
  donc `PriceLimit` decrit mieux son role metier que `DisplayPrice`. Le
  renommage est peu risque si tous les imports sont actualises. -->

<!-- ### Issue 4
- [ ] 4. Contraindre `vat` a 20 %

- Commentaire : [discussion_r3259003395](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3259003395)
- Code : [models/tariff.py](../src/api/qualicharge/models/tariff.py#L74)
- Demande : limiter `vat` autour de 20 %, soit via annotation
  `Ge(19.9), Le(20.1)`, soit via `model_validator`.
- Avis : **bonne idee sur le fond, je privilegierais un validator**. La contrainte
  est metier, pas seulement technique. Un validator permet un message d'erreur
  explicite et peut tenir compte des cas `vat is None`, `tax_included`, ou d'une
  future representation en `Decimal`. Si la regle est vraiment "TVA = 20",
  une plage flottante 19.9-20.1 est moins nette qu'une validation assumee. -->

<!-- ### Issue 5
- [ ] 5. Introduire `TariffElements`

- Commentaire : [discussion_r3259044106](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3259044106)
- Code : [models/tariff.py](../src/api/qualicharge/models/tariff.py#L104)
- Demande : ajouter un `RootModel[List[TariffElement]]` pour y attacher une
  methode de conversion texte.
- Avis : **idee acceptable, mais seulement si la methode est vraiment utilisee**.
  Le modele actuel est simple : `elements: List[TariffElement]`. Passer a un
  `RootModel` ajoute une indirection (`.root`) dans le code Python. Pydantic v2
  sait serialiser un `RootModel` comme une liste, donc le JSON peut rester propre,
  mais il faut des tests de dump/validate. Je l'eviterais tant que la conversion
  texte n'existe pas ou n'est pas appelee a plusieurs endroits. -->

<!-- ### Issue 6
- [ ] 6. Rendre `country_code` et `party_id` obligatoires

- Commentaire : [discussion_r3259081426](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3259081426)
- Code : [models/tariff.py](../src/api/qualicharge/models/tariff.py#L114)
- Demande : retirer `Optional` sur `country_code` et `party_id`.
- Avis : **bonne idee**. La factory les renseigne deja par defaut, et l'unicite
  OCPI depend du triplet `country_code`, `party_id`, `id`. Le seul impact visible
  est sur les tests ou payloads minimaux qui construisent un `TariffObject` sans
  ces champs, par exemple `test_tariff_object_alias`
  ([test](../src/api/tests/models/test_tariff.py#L50)). -->

<!-- ### Issue 7
- [ ] 7. Remplacer `tariff_id` par `id` et calculer `tariff_id`

- Commentaire : [discussion_r3259098512](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3259098512)
- Code : [models/tariff.py](../src/api/qualicharge/models/tariff.py#L120)
- Demande : faire de `id` le champ OCPI original, puis calculer `tariff_id` par
  concatenation `country_code + party_id + id`.
- Avis : **bonne idee metier, changement structurel cote codebase**. Aujourd'hui
  `tariff_id` est a la fois le nom Python du champ OCPI `id` et la valeur stockee
  dans `Tariff.original_id`. Si on adopte le triplet OCPI, `original_id` ne doit
  plus recevoir le seul `id`, mais le `tariff_id` calcule. Cela impacte
  `tariff_fields_from_object`, `get_tariff_by_original`, la detection de conflit
  dans la route de creation, les factories et les tests. Je le ferais, mais en
  ajoutant des tests explicites sur `id`, `tariff_id` calcule et `raw["id"]`. -->

<!-- ### Issue 8
- [ ] 8. Utiliser `TariffElements` dans `TariffObject`

- Commentaire : [discussion_r3259115890](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3259115890)
- Code : [models/tariff.py](../src/api/qualicharge/models/tariff.py#L124)
- Demande : si `TariffElements` est ajoute, typer `elements: TariffElements`.
- Avis : **meme avis que le point 5**. Cohérent si la classe existe, mais il faut
  verifier que `model_dump(by_alias=True, mode="json")` conserve bien une liste
  JSON sous `elements`, car cette sortie est stockee telle quelle en base. -->

<!-- ### Issue 9
- [ ] 9. Ajouter `tariff_alt_url`

- Commentaire : [discussion_r3259135750](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3259135750)
- Code : [models/tariff.py](../src/api/qualicharge/models/tariff.py#L125)
- Demande : ajouter `tariff_alt_url: Optional[Annotated[HttpUrl, MaxLen(255)]] = None`.
- Avis : **bonne idee**. Le champ complete naturellement `tariff_alt_text` et
  reste optionnel, donc faible risque fonctionnel. Il faudra importer `HttpUrl`
  et `MaxLen`, puis ajouter un test de validation/dump car `HttpUrl` doit etre
  serialise en string avec `mode="json"` avant stockage JSONB. -->

<!-- ### Issue 10
- [ ] 10. Verifier `end_date_time` par rapport a `last_updated`

- Commentaire : [discussion_r3259150841](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3259150841)
- Code : [models/tariff.py](../src/api/qualicharge/models/tariff.py#L133)
- Demande : rejeter un tarif dont `last_updated > end_date_time`.
- Avis : **a discuter**. Si QualiCharge considere que la date d'application
  effective est `max(start_date_time, last_updated)`, alors la verification est
  logique : un tarif ne peut pas commencer apres sa fin. En OCPI pur, en revanche,
  `last_updated` est souvent une date de modification de la ressource, pas une
  date de debut de validite ; on peut corriger un tarif deja termine. Je ne
  l'ajouterais qu'apres validation metier de cette interpretation. -->

<!-- ### Issue 11
- [ ] 11. Ajouter des validations sur les champs imposes

- Commentaire : [discussion_r3259175025](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3259175025)
- Code : [models/tariff.py](../src/api/qualicharge/models/tariff.py#L133)
- Demande : verifier que `type == AD_HOC_PAYMENT`, `currency == EUR`, et
  `tax_included != N/A`.
- Avis : **bonne idee, mais le snippet n'est pas directement applicable**. Le
  modele actuel n'a pas de champ `type`, donc il faut d'abord introduire le type
  tarifaire si le modele de donnees l'exige. Pour `currency`, la validation
  `EUR` est coherente avec le contexte francais. Pour `tax_included`, interdire
  `N/A` est coherent si les prix doivent toujours etre qualifies fiscalement.
  Ces validations doivent etre testees avec des erreurs explicites. -->
<!-- 
### Issue 12
- [ ] 12. Ajouter des proprietes calculees

- Commentaire : [discussion_r3259185201](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3259185201)
- Code : [models/tariff.py](../src/api/qualicharge/models/tariff.py#L133)
- Demande : ajouter `tariff_application_date`, `tariff_id`, `ocpi_version` et
  `is_tax_included`.
- Avis : **bonne idee pour `tariff_application_date`, `tariff_id` et
  `is_tax_included`; plus fragile pour `ocpi_version`**. Les trois premieres
  proprietes centralisent des regles qui sont autrement dupliquees dans le
  mapping SQL. En revanche, deduire la version OCPI uniquement de la presence de
  `tax_included` est pratique mais implicite ; je prefererais un commentaire ou
  un test qui documente cette convention. -->

### Issue 13
- [ ] 13. Clarifier le sens de `raw` / ajouter `original_tariff`

- Commentaire : [discussion_r3259300077](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3259300077)
- Code : [models/tariff.py](../src/api/qualicharge/models/tariff.py#L152)
- Demande : distinguer le payload original poste a l'API du JSON du
  `TariffObject`, eventuellement avec un champ/propriete `original_tariff`.
- Avis : **bonne question, a trancher avant de coder**. Le code actuel appelle
  `raw` le JSON du `TariffObject`, et `TariffRead.raw` est type comme
  `TariffObject`. Si `raw` doit devenir le payload complet `TariffCreate`, il
  faut changer `tariff_fields_from_object` pour recevoir le payload complet,
  reviser `TariffRead.raw`, et decider si `targets` doit etre historise. Si le
  besoin est seulement de stocker le tarif OCPI original avec alias `id`, une
  propriete `original_tariff` sur `TariffObject` est suffisante et moins
  disruptive.

### Issue 14
- [ ] 14. Mapper `raw` depuis `raw.original_tariff`

- Commentaire : [discussion_r3259327488](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3259327488)
- Code : [schemas/tariff_utils.py](../src/api/qualicharge/schemas/tariff_utils.py#L28)
- Demande : remplacer `"raw": raw.model_dump(...)` par `"raw": raw.original_tariff`.
- Avis : **bonne idee si `original_tariff` est defini comme sortie canonique du
  `TariffObject`**. Cela rendrait l'intention plus lisible. En revanche, si
  `original_tariff` signifie le payload complet `TariffCreate`, la fonction
  actuelle n'a pas assez d'information car elle ne recoit qu'un `TariffObject`.

<!-- ### Issue 15
- [ ] 15. Mapper `start` depuis `tariff_application_date`

- Commentaire : [discussion_r3259335632](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3259335632)
- Code : [schemas/tariff_utils.py](../src/api/qualicharge/schemas/tariff_utils.py#L34)
- Demande : utiliser `to_db_datetime(raw.tariff_application_date)` pour `start`.
- Avis : **bonne idee si la regle metier est bien que l'application commence au
  plus tot a `last_updated`**. Cela evite qu'un tarif nouvellement recu s'applique
  retrospectivement avant sa publication dans QualiCharge. Ce changement impacte
  directement `get_applicable_tariff`, les filtres de liste et plusieurs tests
  d'API qui attendent actuellement `start_date_time`. -->

<!-- ### Issue 16
- [ ] 16. Rendre `original_last_updated` et `start` non optionnels

- Commentaire : [discussion_r3259364219](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3259364219)
- Code : [schemas/tariff.py](../src/api/qualicharge/schemas/tariff.py#L42)
- Demande : `original_last_updated` et `start` ne doivent pas etre optionnels.
- Avis : **bonne idee, mais avec migration et nettoyage des tests**. Cote modele
  Pydantic, `last_updated` est deja obligatoire ; si `start` devient
  `tariff_application_date`, il est aussi toujours disponible. La base devrait
  donc pouvoir etre `NOT NULL`. Il faut toutefois mettre a jour la migration,
  supprimer le cas `get_tariff_by_original(..., None)` et verifier les donnees
  existantes avant d'imposer la contrainte. -->

<!-- ### Issue 17
- [ ] 17. Tester les tarifs issus de l'enquete

- Commentaire : [discussion_r3259571730](https://github.com/MTES-MCT/qualicharge/pull/997#discussion_r3259571730)
- Code : [tests/models/test_tariff.py](../src/api/tests/models/test_tariff.py#L20)
- Demande : valider les exemples de tarifs issus de l'enquete avec
  `TariffObject.model_validate(...)`.
- Avis : **tres bonne idee**. Ces tests donneraient une protection utile contre
  les regressions de schema. Ils sont particulierement importants si on rend
  `country_code`, `party_id`, `start` ou la TVA obligatoires. Il faut juste
  stocker les exemples dans un fixture stable et documenter les valeurs par
  defaut ajoutees pour les exemples incomplets.
 -->
## Commentaire general de revue

### Issue 18
- [ ] 18. DELETE `/statique/tariff`

- Commentaire : [pullrequestreview-4310156963](https://github.com/MTES-MCT/qualicharge/pull/997#pullrequestreview-4310156963)
- Note : le commentaire indique aussi que le document "Modele de donnees" a ete
  mis a jour, donc ces regles semblent venir d'un arbitrage metier recent.
- Code lie : la route `POST /statique/tariff/` existe
  ([code](../src/api/qualicharge/api/v1/routers/static.py#L406)), mais il n'y a
  pas encore de route `DELETE /statique/tariff/{id}`. Le modele d'association
  `PointDeChargeTariff` existe
  ([code](../src/api/qualicharge/schemas/tariff.py#L16)).
- Demande : pour `DELETE /statique/tariff`, faire un hard-delete si le tarif
  n'est lie a aucun PDC ou si sa date `start` est dans le futur.
- Avis : **bonne idee fonctionnelle, a traiter comme un sujet separe**. Le
  hard-delete est sain pour un tarif jamais utilise ou futur, car il evite de
  garder des brouillons inutiles. Pour un tarif deja applicable ou lie a des PDC,
  le soft-delete reste plus prudent pour l'audit et l'historique. Il faudra
  definir le comportement exact quand le tarif a des associations futures, quand
  l'utilisateur n'a acces qu'a une partie des PDC lies, et quand `start` devient
  non nullable.

## Ordre d'implementation recommande

1. Renommer les classes OCPI et ajouter les champs simples (`tariff_alt_url`,
   `country_code`, `party_id` obligatoires).
2. Introduire proprement `id` + `tariff_id` calcule, puis adapter
   `tariff_fields_from_object`, les factories et les tests.
3. Ajouter `tariff_application_date` et decider explicitement si `start` doit
   etre `max(start_date_time, last_updated)`.
4. Ajouter les validations metier (`currency`, `tax_included`, TVA, dates) avec
   tests d'erreur dedies.
5. Changer les contraintes SQL (`original_last_updated`, `start`) dans le schema
   et la migration seulement apres les points precedents.
6. Traiter le hard-delete dans une PR separee, car il touche les droits, les
   associations et la politique d'audit.

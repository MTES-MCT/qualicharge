QualiCharge works closely with
[transport.data.gouv.fr](https://transport.data.gouv.fr/) to design (Open) data
standards. As a first implementation, we've adopted already existing data schema
designed for static and dynamic EVSE-related data.

## Static data

Static data relates to EVSEs metadata to describe them, _e.g._ their location,
accessibility, operator, etc. The data schema is documented (in French 🇫🇷) here
👉
[schema.data.gouv.fr/etalab/schema-irve-statique](https://schema.data.gouv.fr/etalab/schema-irve-statique/2.3.1/documentation.html).

> :bulb: This schema will evolve in time as the European Commission is working
> on an interoperability standard, that we will adopt progressively as soon as
> it will be publicly available.

We require your attention on two fields that will be extensively used in
QualiCharge's API:

- `id_pdc_itinerance`: this field is a unique roaming-ready identifier used to
  refer to a particular charge point in a charging station, it uses an operating
  unit prefix that is delivered for operators by the French ID Registration
  Organization. We invite you to see the
  [AFIREV's list of identifiers](https://afirev.fr/en/list-of-assigned-identifiers/)
  and [rules to define them](https://afirev.fr/en/general-informations/).
- `id_station_itinerance`: similarly to `id_pdc_itinerance` this unique
  roaming-ready identifier applies for charging stations (not charge points).

The Qualicharge API **will not** accept \* nor any usual separator. Make sure to
remove all separators before sending IDs through the API.

### Consistency rules for batch submissions (bulk endpoint)

When sending a set of static data, using the dedicated `POST /statique/bulk` endpoint,
consistency rules applies!

- **Consistency rule one**: given a particular `id_station_itinerance`, we
  expect the following fields to be identical:

  - `nom_amenageur`
  - `siren_amenageur`
  - `contact_amenageur`
  - `nom_operateur`
  - `contact_operateur`
  - `telephone_operateur`
  - `nom_enseigne`
  - `nom_station`
  - `implantation_station`
  - `nbre_pdc`
  - `condition_acces`
  - `horaires`
  - `station_deux_roues`
  - `date_maj`
  - `num_pdl`
  - `id_station_local`
  - `raccordement`
  - `date_mise_en_service`
  - `coordonneesXY`

- **Consistency rule two**: given a `coordonneesXY` tuple, we expect the
  following fields to be identical:

  - `adresse_station`
  - `code_insee_commune`

:point_right: If one of those two rules is not respected using the bulk
endpoint, the API will raise an error.

> :bulb: Note that submitting batch items one by one using the `POST /statique`
> endpoint (or the `PUT /statique/{id_pdc_itinerance}`) endpoint, the API will
> not raise consistency errors as it will consider that you are updating
> statique data.

## Dynamic data

Dynamic data regroup two kinds of EVSE-related data: statuses, and charging
sessions (_aka_ sessions in the present documentation).

### Statuses

When a charge point status changes, an event is emitted. This event may be
serialized given the proposed standard we've adopted that is documented (in
French 🇫🇷) at:
[schema.data.gouv.fr/etalab/schema-irve-dynamique](https://schema.data.gouv.fr/etalab/schema-irve-dynamique/2.3.1/documentation.html).

> :bulb: This standard may also evolve in a near future. Stay tuned!

### Sessions

Charging sessions are used by QualiCharge along with statuses to assess the
charging network quality and calculate the amount of energy delivered by an
operator on a certain time period. For now expected data schema is quite
minimalist and documented in the
[API source code](https://github.com/MTES-MCT/qualicharge/blob/main/src/api/qualicharge/models/dynamic.py).

| Field               | Description                                                                                                                         | Example value                      |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| `id_pdc_itinerance` | Roaming identifier used for a charge point (see static data schema )                                                                | `FRXXXEYYY`                        |
| `start`             | Date and time at which the charging session started (as a timezone-aware [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) string) | `2024-06-04T14:26:44.562476+00:00` |
| `end`               | Date and time at which the charging session ended (as a timezone-aware [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) string)   | `2024-06-04T16:06:41.571435+00:00` |
| `energy`            | The amount (floating point number) of energy consumed (in kilowatt-hour)                                                            | `12.34567`                         |

An exemple JSON-formatted charging session may be serialized as follow:

```json
{
  "id_pdc_itinerance": "FRXXXEYYY",
  "start": "2024-06-04T14:26:44.562476+00:00",
  "end": "2024-06-04T16:06:41.571435+00:00",
  "energy": "12.34567"
}
```

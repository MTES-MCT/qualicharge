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

### Discrepencies with the official schema

For control-purpose, some optional fields of the official schema are
**required** for QualiCharge API. Discrepencies are listed in the table below:

| name                  | API type                                                        | Rule N° |                                                               Rule |
| --------------------- | --------------------------------------------------------------- | :-----: | -----------------------------------------------------------------: |
| `code_insee_commune`  | [Official dataset](https://www.insee.fr/fr/information/7766585) |    2    |                 Should be referenced in the official INSEE dataset |
| `nom_operateur`       | String                                                          |    6    |                                                Should not be empty |
| `telephone_operateur` | French phone number                                             |    6    |                                                Should not be empty |
| `contact_amenageur`   | Email string                                                    |    7    |                                                Should not be empty |
| `nom_amenageur`       | String                                                          |    7    |                                                Should not be empty |
| `siren_amenageur`     | 9-integers string                                               |    7    |                                                Should not be empty |
| `num_pdl`             | Max 64-characters string                                        |   20    |                * Should not be empty and should not contain spaces |
|                       |                                                                 |   34    | Should match energy supplier pattern (_e.g._ 14 digits for ENEDIS) |

> The rule number corresponds to our data-quality control referencial.
> (*) The rule n° 20 is active only for DC station with a null value or a `direct` value in the `raccordement` field

### Extra quality controls

Rules for statique data fields:

| name                    | API type                              | Rule N° |                                                   Rule |
| ----------------------- | ------------------------------------- | :-----: | -----------------------------------------------------: |
| `id_pdc_itinerance`     | EVSE AFIREV-based pattern             |   24    |              Must match AFIREV pattern (`FRXXXEXXXXX`) |
| `id_station_itinerance` | Pool AFIREV-based pattern             |   23    |              Must match AFIREV pattern (`FRXXXPXXXXX`) |
| `coordonneesXY`         | `"[longitude,latitude]"` array string |    3    | Coordinates should be included in the French territory |
| `puissance_nominale`    | Positive float                        |    1    |                         Must be **lower than 4000 kW** |
|                         |                                       |   39    |                        Must be **greater than 1.3 kW** |

Specific rules applies for submitted datasets consistency:

| Rule N° | Rule                                                                                                                                |
| :------ | :---------------------------------------------------------------------------------------------------------------------------------- |
| 30      | A station should associated with less than **50** charge points                                                                     |
| 46      | The number of stations per location should be less than **1.5**                                                                     |
| 47      | The number of charge points per station should be equal to (or greater than) the value `nbre_pdc`                                   |
| 48      | Two stations with identical first 5 characters of the `id_station_itinerance` should not be associated with two different operators |
| 51 - 52 | A charge point without statuses since one month should be decommissioned                                                            |
| 54      | Two `amenageur` with different `nom_amenageur` values can't have the same `siren_amenageur` value                                   |
| 55      | A SIREN number must be valid (correct checksum)                                                                                     |

> The rule number corresponds to our data-quality control referencial.

### Consistency rules for batch submissions (bulk endpoint)

When sending a set of static data, using the dedicated `POST /statique/bulk`
endpoint, consistency rules applies!

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

#### Extra quality controls

| name         | API type       | Rule N° |                                                                         Rule |
| ------------ | -------------- | :-----: | ---------------------------------------------------------------------------: |
| `horodatage` | Past date-time |   43    | Freshness should be lower than _5 minutes_ (compared to the submission date) |

Specific rules applies for submitted datasets consistency:

| Rule N° | Rule                                                                                                                                                    |
| :------ | :------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 21      | For DC stations with `raccordement="Direct"`, a status with `occupation_pdc="occupe"` should be associated with a session                               |
| 37      | A status with `etat_pdc="hors_service"` or `etat_pdc="inconnu"` cannot define `occupation_pdc="occupe"` (the later is reserved for charging activities) |
| 44      | Statuses cannot be duplicated (identical `horodatage` values for a target charge point)                                                                 |
| 53      | The number of statuses for a charge point should be less than **1 440 per day**                                                                         |

> The rule number corresponds to our data-quality control referencial.
> Rule 21 is only available for charge points where session flow is enabled

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

#### Extra quality controls

| name     | API type       | Rule N° |                                                                       Rule |
| -------- | -------------- | :-----: | -------------------------------------------------------------------------: |
| `energy` | Positive float |   11    |                                                Must be lower than 1000 kWh |
| `start`  | Past date-time |   42    | Freshness should be lower than _15 days_ (compared to the submission date) |

Specific rules applies for submitted datasets consistency:

| Rule N° | Rule                                                                                                                                        |
| :------ | :------------------------------------------------------------------------------------------------------------------------------------------ |
| 10      | Sessions cannot overlap                                                                                                                     |
| 13      | The number of sessions for a charge point should be less than **60 per day**                                                                |
| 14      | A session cannot end before it starts                                                                                                       |
| 15      | A session should not last more than **7 days**                                                                                              |
| 17      | Sessions cannot be duplicated (identical start/end dates and energy for a target charge point)                                              |
| 22      | A session should start when a status with `occupation_pdc="occupe"` is issued and end when a status with `occupation_pdc="libre"` is issued |
| 38      | The energy of a session should not exceed the charge point's nominal power multiplied by the session duration by more than 10 %             |
| 40      | A session of zero duration cannot have an energy greater than **1 kWh**                                                                     |
| 49      | For DC stations with `raccordement="Direct"`, the ratio of the number of statuses to the number of sessions must be between **1 and 30**    |

> The rule number corresponds to our data-quality control referencial.

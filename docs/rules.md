## Rule types

Two types of rules are applied in Qualicharge (intra-attribute and inter-attribute).

Rules are applied at the API level or retrospectively at the database level.

## Intra-attribute Rules

- Rules Related to the [transport.data.gouv.fr](https://transport.data.gouv.fr/) Data Schema
  - Rules related to the naming, format, and optionality of attributes are addressed in the APIs (see [Data schemas](schemas.md)).
- Additional Rules to the [transport.data.gouv.fr](https://transport.data.gouv.fr/) Data Schema
  - Additional rules are taken into account at the API level and also at the database level (see table below)

| name                                                                                | API level                   | database level                                                                   |
|-------------------------------------------------------------------------------------|-----------------------------|----------------------------------------------------------------------------------|
| contact_amenageur                                                                   | format emailStr             | 7 - the field is not empty                                                       |
| nom_amenageur                                                                       |                             | 7 - the field is not empty                                                       |
| siren_amenageur                                                                     |                             | 7 - the field is not empty                                                       |
| code_insee_commune                                                                  |                             | 2 - code referenced in the INSEE codes                                           |
| coordonneesXY                                                                       |                             | 3 - coordinates included in French territory                                     |
| contact_operateur                                                                   | format emailStr             | 6 - the field is not empty                                                       |
| nom_operateur                                                                       |                             | 6 - the field is not empty                                                       |
| telephone_operateur                                                                 | format FrenchPhoneNumber    | 6 - the field is not empty                                                       |
| id_pdc_itinerance                                                                   |                             | 24 - the AFIREV format is respected (FRxxxExxxxx)                                |
| puissance_nominale                                                                  | format PositiveFloat        | 1 - power < 4000 kW   / 39 - power > 1.3 kW                                      |
| num_pdl                                                                             | max_length=64               | 20 - the field is not empty / 34 - formats of energy managers (14 digits for ENEDIS and specific format for ELDs)|
| end                                                                                 | format PastDateTime         |                                                                                  |
| energy                                                                              | format PositiveFloat        | 11 - The session energy is less than 500 kWh                                     |
| start                                                                               | format PastDateTime         | 42 - The freshness is 15 days (difference with the date recorded in Qualicharge) |
| date_maj                                                                            | format NotFutureDate        |                                                                                  |
| date_mise_en_service                                                                | format NotFutureDate        |                                                                                  |
| id_station_itinerance                                                               |                             | 23 - The AFIREV format is respected (FRxxxPxxxxx)                                |
| nbre_pdc                                                                            | format PositiveInt          |                                                                                  |
| horodatage                                                                          | format PastDateTime         | 36 - The date cannot be later than today's date / 43 - The freshness is 5 minutes (difference with the date recorded in Qualicharge)|

## Inter-attribute rules related to static data

- Rules related to the data model
  - Rules related to relationships between entities are handled in the APIs (see [Data schemas](schemas.md))
- Specific rules (database level)
  - 30 - a station is associated with fewer than 50 charging points
  - 46 - the number of stations per location is less than 1.5
  - 47 - the difference between the number of charging points per station and the nbre_pdc value is less than 20%

## Inter-attribute rules related to dynamic data

- Rules related to sessions (database level)
  - 17 - sessions are not duplicated (identical start and end dates for the same charging point)
  - 10 - sessions do not overlap
  - 15 - a session has a duration of less than 3 days
  - 14 - a session has an end date later than the start date
  - 22 - a session starts when a status is issued with a status The occupancy status "occupies" and ends when a status is issued with an occupancy status of "free".
  - 38 - The energy of a session that exceeds the charging point's nominal power multiplied by the session duration is abnormal.
  - 41 - The energy cannot exceed twice the charging point's nominal power multiplied by the session duration and cannot exceed 50 kWh.
  - 40 - A session of zero duration cannot have an energy exceeding 1 kWh.
  - 13 - The number of sessions at a charging point is limited to 50 per day.
- Rules related to Status (database level)
  - 37 - A status cannot have a value of `occupied` for the `status_occupation` attribute and a value of `out_of_service` for the `status_pdc` attribute (the `occupied` value is reserved for actual charging activities).
  - 44 - Statuses are not duplicated (identical timestamps for the same charging point)
  - 21 - A status with a value of 'occupied' is associated with a session

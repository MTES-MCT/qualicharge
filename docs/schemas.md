QualiCharge works closely with
[transport.data.gouv.fr](https://transport.data.gouv.fr/) to design (Open) data
standards. As a first implementation, we've adopted already existing data schema
designed for static and dynamic EVSE-related data.

## Static data

Static data relates to EVSEs metadata to describe them, _e.g._ their location,
accessibility, operator, etc. The data schema is documented (in French :fr:) in
[schema.data.gouv.fr/etalab/schema-irve-statique](https://schema.data.gouv.fr/etalab/schema-irve-statique/2.3.1/documentation.html).

> :bulb: This schema may evolve in time as the European commission is working on
> an interoperability standard, that we will adopt progressively as soon as it
> will be publicly available.

We require your attention on two fields that will be extensively used in
QualiCharge's API:

- `id_pdc_itinerance`: this field is a unique roaming-ready identifier used to
  refer to a particular point of charge in a charging station, it uses a prefix
  that is delivered for operators by the AFIREV organism. We invite you to see
  the
  [AFIREV's list of identifiers](https://afirev.fr/en/list-of-assigned-identifiers/)
  and [rules to define them](https://afirev.fr/en/general-informations/).
- `id_station_itinerance`: similarly to `id_pdc_itinerance` this unique
  roaming-ready identifier applies for charging stations (not points of charge).

## Dynamic data

Dynamic data regroup two kinds of EVSE-related data: statuses, and charging
sessions (_aka_ sessions in the present documentation).

### Statuses

When a charging point status changes, an event is emitted. This event may be
serialized given the proposed standard we've adopted that is documented (in
French :fr:) at:
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
| `id_pdc_itinerance` | Roaming identifier used for a point of charge (see static data schema )                                                             | `FRXXXEYYY`                        |
| `start`             | Date and time at which the charging session started (as a timezone-aware [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) string) | `2024-06-04T14:26:44.562476+00:00` |
| `end`               | Date and time at which the charging session ended (as a timezone-aware [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) string)   | `2024-06-04T16:06:41.571435+00:00` |
| `energy`            | The amount (floating point number) of energy consumed (in Watts)                                                                    | `12345.67`                         |

An exemple JSON-formatted charging session may be serialized as follow:

```json
{
  "id_pdc_itinerance": "FRXXXEYYY",
  "start": "2024-06-04T14:26:44.562476+00:00",
  "end": "2024-06-04T16:06:41.571435+00:00",
  "energy": "12345.67"
}
```

# API usage

🙏 We ask you to be reasonable in your API usage or rate-limiting rules will
apply for your account. While working on the API integration, this document will
help you in your journey.

## Pro-tips™ for a smooth integration

1. Do not generate a new authentication token if it's not expired yet (it has a
   30 minutes lifetime).
2. Do not send too many concurrent requests with heavy payloads (particularly
   for static data). Prefer sending a new batch every _X_ seconds (see
   [rate-limiting](#rate-limiting) section).
3. Increase the request timeout to _30 seconds_. We know it's huge! The API will
   respond in less than a second in 99% cases, but as we say « _Shit happens!_ »
   🤷🏻‍♀️
4. Set your HTTP client's `user-agent` header to the company name that is
   holding the technical responsibility of API requests, e.g. `acme-charging`
   for the ACME Charging Inc. company or `foo-proxy` for the Foo Proxy company
   that is acting as a contractor for the ACME Charging Inc. company. This
   custom user-agent will be used for regulation / traceability purpose and is
   mandatory to switch to our production instance.
5. We invite you to store API response codes for traceability purpose.
6. We strongly advise you to store API responses for session-related data. Under
   normal circumstances, when a session is created, the API should provide an
   attributed UUID for this session in its response. This UUID should be stored
   on **your** side along with your internal session identifier so that we can
   trace submitted sessions on both sides.

## Rate-limiting

> ⚠️ Rate-limiting is still a
> [work-in-progress](https://github.com/MTES-MCT/qualicharge/pull/488). We will
> notice you when they will apply.

If your account is consuming too much resources, some restrictions may apply.
The following table sums them up.

| Endpoint                                        | Verb   |   Rate | Burst | Delay |
| :---------------------------------------------- | ------ | -----: | ----: | ----: |
| `/auth/whoami`                                  | `GET`  |  1 r/s |     2 |    no |
| `/auth/token`                                   | `POST` |  4 r/m |     2 |    no |
| `/statique/`                                    | `GET`  |        |       |       |
| `/statique/`                                    | `POST` |  1 r/s |       |       |
| `/statique/{id_pdc_itinerance}`                 | `GET`  |        |       |       |
| `/statique/{id_pdc_itinerance}`                 | `PUT`  |        |       |       |
| `/statique/bulk`                                | `POST` | 10 r/m |       |       |
| `/dynamique/session/`                           | `POST` |        |       |       |
| `/dynamique/session/bulk`                       | `POST` | 10 r/m |       |       |
| `/dynamique/session/check`                      | `GET`  |        |       |       |
| `/dynamique/status/`                            | `GET`  |        |       |       |
| `/dynamique/status/`                            | `POST` |        |       |       |
| `/dynamique/status/{id_pdc_itinerance}`         | `GET`  |        |       |       |
| `/dynamique/status/{id_pdc_itinerance}/history` | `GET`  |        |       |       |
| `/dynamique/status/bulk`                        | `POST` | 30 r/m |    10 |    no |

Rates are expressed in requests per-minute (`r/m`) or requests per-second
(`r/s`). The burst value correspond to an exceptional allowed rate extend for a
period. We generally afford no delay in requests (they are treated as they come,
not postponed). A blank cell means that no restriction applies at all.

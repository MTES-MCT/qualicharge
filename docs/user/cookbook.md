# Cookbook

## Decommissioning charge points or pools

QualiCharge API provides endpoints to decommission charge points and
recommission them if needed.

To do so, you will need to use the `DELETE /statique/{id_pdc_itinerance}` API
endpoint without any payload required for this request.

> ⚠️Your account should include the `static:delete` scope. If not, we invite
> you to contact an administrator to extend your permissions.

If all charge points of a station have been decommissioned, the station will
also be automatically decommissioned.

Once decommissioned a charge point will no longer be listed in static data
related to your account. This means that you will receive a 404 HTTP response
if you try to send dynamic data (status or session) for this charge point. This
also means that this charge point will no longer be listed in our [IRVE open
data
files](https://www.data.gouv.fr/datasets/infrastructures-de-recharge-pour-vehicules-electriques-donnees-ouvertes/).

Note that decommissioning a charge point (or a station) does not delete
concerned charge point (or station) nor related object in database (such as
sessions and statuses); it is "soft-deleted" instead. Thus, you can
recommission a charge point (and related station) using the `POST
/statique/{id_pdc_itinerance}/up` dedicated API endpoint (no payload is
expected in this request).

> Note that decommissioning an already decommissioned charge point has no
> effect. And the same rule applies when trying to recommissioned an already
> active charge point.

## Renaming charge points

If your naming convention evolves for your charge points, we invite you to
create charge points with new identifiers (_i.e._ `id_pdc_itinerance`) first,
and then, decommission charge points with old identifiers.

> 💡 We invite you to create renamed charge points first, to avoid
> decommissioning related pool/location (if its `id_station_itinerance`
> identifier stays identical; see previous section for a complete explanation).

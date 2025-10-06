"""Expectations for the dynamic data."""

from copy import copy
from datetime import date
from string import Template

import great_expectations as gx
import great_expectations.expectations as gxe

from .parameters import DUPS, DUPT, ENEA, ENERGY, ENEX, FRES, FRET, LONS, ODUR, OVRS

NAME: str = "dynamic"


def get_suite(date_start: date, date_end: date):
    """Get dynamic expectation suite."""
    date_params = {
        "start": f"'{date_start.isoformat()}'",
        "end": f"'{date_end.isoformat()}'",
    }
    energy_expectations = [
        # ENEU : Energy greater than highest_energy_kwh (rule 11)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  f_statique AS {batch}
SELECT
  energy,
  nom_amenageur,
  start,
  session.end,
  id_pdc_itinerance
FROM
  session
  INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
WHERE
  energy > $highest_energy_kwh
  AND start >= $start
  AND start < $end
                """
            ).substitute(
                date_params | ENERGY  # type: ignore
            ),
            meta={"code": "ENEU"},
        ),
        # ODUR : Session of zero duration (rule 40)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  f_statique AS {batch},
  sessions_instant AS (
    SELECT
      count(*) AS n_inst_ses
    FROM
      session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
    WHERE
      session.end = start
      AND energy > $lowest_energy_kwh
      AND energy <= $highest_energy_kwh
      AND start >= $start
      AND start < $end
  ),
  nb_sessions AS (
    SELECT
      count(session.id) AS n_ses
    FROM
      session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
    WHERE
      energy > $lowest_energy_kwh
      AND energy <= $highest_energy_kwh
      AND start >= $start
      AND start < $end
  )
SELECT
  *
FROM
  sessions_instant,
  nb_sessions
WHERE
  n_inst_ses::float > $threshold_percent * n_ses::float
                """
            ).substitute(date_params | ODUR.params | ENERGY),
            meta={"code": ODUR.code},
        ),
        # ENEA : Session with abnormal energy (rule 38)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  f_statique AS {batch},
  sessions_max AS (
    SELECT
      count(*) AS n_max_ses
    FROM
      session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
    WHERE
      session.end != session.start
      AND energy > $lowest_energy_kwh
      AND energy <= $highest_energy_kwh
      AND start >= $start
      AND start < $end
      AND energy > extract(
        'epoch' FROM (session.end - start)
      ) / 3600.0 * puissance_nominale * $abnormal_coef
      AND (
        energy < extract(
          'epoch' FROM (session.end - start)
        ) / 3600.0 * puissance_nominale * $excess_coef
        OR energy <= $excess_threshold_kWh
      )
  ),
  nb_sessions AS (
    SELECT
      count(session.id) AS n_ses
    FROM
      session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
    WHERE
      session.end != session.start
      AND energy > $lowest_energy_kwh
      AND energy <= $highest_energy_kwh
      AND start >= $start
      AND start < $end
  )
SELECT
  *
FROM
  sessions_max,
  nb_sessions
WHERE
  n_max_ses::float > $threshold_percent * n_ses::float
                """
            ).substitute(date_params | ENEA.params | ENEX.params | ENERGY),
            meta={"code": ENEA.code},
        ),
        # ENEX : Session with excessive energy (rule 41)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  f_statique AS {batch}
SELECT
  session.*,
  id_pdc_itinerance,
  puissance_nominale,
  nom_operateur,
  nom_amenageur
FROM
  session
  INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
WHERE
  session.end != start
  AND energy > $excess_threshold_kWh
  AND energy > extract(
    'epoch' FROM (session.end - start)
  ) / 3600.0 * puissance_nominale * $excess_coef
                """
            ).substitute(date_params | ENEX.params),
            meta={"code": ENEX.code},
        ),
    ]

    sessions_expectations = [
        # DUPS : Duplicate sessions (rule 17)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  f_statique AS {batch},
  nb_session AS (
    SELECT
      count(*) as nbre_session
    FROM
      session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
    WHERE
      START >= $start
      AND START < $end
  ),
  nb_session_unique AS (
    SELECT
      count(*) AS nbre_unique
    FROM
      (
        SELECT
          START,
          SESSION.end,
          point_de_charge_id
        FROM
          SESSION
          INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
        WHERE
          START >= $start
          AND START < $end
        GROUP BY
          START,
          SESSION.end,
          point_de_charge_id
      ) AS session_unique
  )
SELECT
  *
FROM
  nb_session_unique,
  nb_session
WHERE
  (nbre_session - nbre_unique)::float > $threshold_percent * nbre_session::float
                """
            ).substitute(date_params | DUPS.params),
            meta={"code": DUPS.code},
        ),
        # OVRS : Number of days-poc with more than max_sessions_per_day (rule 13)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  f_statique AS {batch}
SELECT
  nb_id,
  start,
  id_pdc_itinerance,
  nom_amenageur,
  nom_operateur
FROM
  (
    SELECT
      count(id) AS nb_id,
      start::date,
      point_de_charge_id
    FROM
      session
    WHERE
      START >= $start
      AND START < $end
    GROUP BY
      start::date, point_de_charge_id
  ) AS list_sessions
  INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
WHERE
  nb_id > $max_sessions_per_day
                """
            ).substitute(date_params | OVRS.params),
            meta={"code": OVRS.code},
        ),
        # LONS : Sessions of more than max_days_per_session (rule 15)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  f_statique AS {batch},
  long_sessions AS (
    SELECT
      count(*) AS n_long_ses
    FROM
      session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
    WHERE
      start >= $start
      AND start < $end
      AND session.end > start + interval '$max_days_per_session'
  ),
  nb_sessions AS (
    SELECT
      count(session.id) AS n_ses
    FROM
      session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
    WHERE
      start >= $start
      AND start < $end
  )
SELECT
  *
FROM
  long_sessions,
  nb_sessions
WHERE
  n_long_ses::float > $threshold_percent * n_ses::float
            """
            ).substitute(date_params | LONS.params),
            meta={"code": LONS.code},
        ),
        # NEGS : Sessions with negative duration (rule 14)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  f_statique AS {batch}
SELECT
  start,
  session.end,
  id_pdc_itinerance,
  energy,
  nom_amenageur,
  nom_operateur
FROM
  session
  INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
WHERE
  start >= $start
  AND start < $end
  AND start > session.end
                """
            ).substitute(date_params),
            meta={"code": "NEGS"},
        ),
        # FRES : freshness of sessions greater than max_duration days (rule 42)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  f_statique AS {batch},
  session_delay AS (
    SELECT
      updated_at,
      session.end as session_end
    FROM
      session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
    WHERE
      START >= $start
      AND START < $end
  )
SELECT
  max(EXTRACT(EPOCH FROM (updated_at - session_end))) / 3600 / 24
FROM
  session_delay
HAVING
  max(EXTRACT(EPOCH FROM (updated_at - session_end))) / 3600 / 24 > $max_duration_day
                """
            ).substitute(date_params | FRES.params),
            meta={"code": FRES.code},
        ),
    ]
    statuses_expectations = [
        # ERRT : Inconsistent statuses (rule 37)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  f_statique AS {batch}
SELECT
  status.id,
  occupation_pdc,
  etat_pdc
FROM
  status
  INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
WHERE
  horodatage >= $start
  AND horodatage < $end
  AND etat_pdc = 'hors_service'
  AND occupation_pdc = 'occupe'
                """
            ).substitute(date_params),
            meta={"code": "ERRT"},
        ),
        # FTRT : Timestamp in the future (rule 36)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  f_statique AS {batch}
SELECT
  horodatage,
  id_pdc_itinerance
FROM
  status
  INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
WHERE
  horodatage < timestamp '01-01-2024'
  OR horodatage > CURRENT_TIMESTAMP
  OR horodatage IS NULL
                """
            ).substitute(date_params),
            meta={"code": "FTRT"},
        ),
        # DUPT : Duplicate statuses (rule 44)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  f_statique AS {batch},
  nb_status AS (
    SELECT
      count(*) AS nbre_status
    FROM
      status
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
    WHERE
      horodatage >= $start
      AND horodatage < $end
  ),
  nb_status_unique AS (
    SELECT
      count(*) AS nbre_unique
    FROM
      (
        SELECT
          horodatage,
          point_de_charge_id
        FROM
          status
          INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
        WHERE
          horodatage >= $start
          AND horodatage < $end
        GROUP BY
          horodatage,
          point_de_charge_id
      ) AS status_unique
  )
SELECT
  *
FROM
  nb_status_unique,
  nb_status
WHERE
  (nbre_status - nbre_unique)::float > $threshold_percent * nbre_status::float
                """
            ).substitute(date_params | DUPT.params),
            meta={"code": "DUPT"},
        ),
        # FRET : Freshness of statuses greater than max_duration seconds (rule 43)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  f_statique AS {batch},
  status_delay AS (
    SELECT
      horodatage,
      updated_at
    FROM
      status
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
    WHERE
      horodatage >= $start
      AND horodatage < $end
  )
SELECT
  avg(extract(SECOND FROM updated_at - horodatage) +
      extract(MINUTE FROM updated_at - horodatage) * 60)
FROM
  status_delay
HAVING
  avg(extract(SECOND FROM updated_at - horodatage) +
      extract(MINUTE FROM updated_at - horodatage) * 60) > $mean_duration_second
                """
            ).substitute(date_params | FRET.params),
            meta={"code": "FRET"},
        ),
    ]
    suite = gx.ExpectationSuite(name=NAME)
    expectations = energy_expectations + sessions_expectations + statuses_expectations
    for expectation in expectations:
        # Make sure expectation is not already assigned to a suite…
        exp = copy(expectation)
        exp.id = None
        # …before adding it to the current suite.
        suite.add_expectation(exp)
    return suite

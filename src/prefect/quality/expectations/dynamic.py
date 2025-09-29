"""Expectations for the dynamic data."""

from copy import copy
from datetime import date
from string import Template

import great_expectations as gx
import great_expectations.expectations as gxe

from .parameters import (
    DUPS,
    DUPT,
    ENEA,
    ENERGY,
    ENEX,
    FRES,
    FRET,
    LONS,
    OCCT,
    ODUR,
    OVRS,
    RATS,
    SEST,
)

NAME: str = "dynamic"
INTERVAL_STATUS_TEMPLATE = """
   f_status AS (
    SELECT
      id,
      point_de_charge_id,
      etat_pdc,
      occupation_pdc,
      updated_at,
      horodatage
    FROM
      status
    WHERE
      horodatage >= $start
      AND horodatage < $end
  )
"""
INTERVAL_SESSION_TEMPLATE = """
  f_session AS (
    SELECT
      id,
      point_de_charge_id,
      energy,
      updated_at,
      start AS start_session,
      session.end AS end_session
    FROM
      session
    WHERE
      start >= $start
      AND start < $end
  )
"""
INTERVAL_ENERGY_SESSION_TEMPLATE = """
  f_session AS (
    SELECT
      id,
      point_de_charge_id,
      energy,
      start AS start_session,
      session.end AS end_session
    FROM
      session
    WHERE
      energy > $lowest_energy_kwh
      AND energy < $highest_energy_kwh
      AND start >= $start
      AND start < $end
  )
"""
FILTERED_STATIQUE = """
  f_statique AS (
    SELECT
      id_pdc_itinerance,
      nom_operateur,
      nom_amenageur,
      puissance_nominale,
      pdc_id
    FROM
      {batch} AS statique
  )
"""


def get_suite(date_start: date, date_end: date):
    """Get dynamic expectation suite."""
    date_params = {
        "start": f"'{date_start.isoformat()}'",
        "end": f"'{date_end.isoformat()}'",
    }
    f_status = {"f_status": Template(INTERVAL_STATUS_TEMPLATE).substitute(date_params)}
    f_session = {
        "f_session": Template(INTERVAL_SESSION_TEMPLATE).substitute(date_params)
    }
    f_energy_session = {
        "f_energy_session": Template(INTERVAL_ENERGY_SESSION_TEMPLATE).substitute(
            date_params | ENERGY  # type: ignore
        )
    }
    f_statique = {"f_statique": FILTERED_STATIQUE}

    energy_expectations = [
        # ENEU : Energy greater than highest_energy_kwh (rule 11)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_statique,
  $f_session
SELECT
  energy,
  nom_amenageur,
  start_session,
  end_session,
  id_pdc_itinerance
FROM
  f_session
  INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
WHERE
  energy > $highest_energy_kwh
                """
            ).substitute(
                f_statique | f_session | ENERGY  # type: ignore
            ),
            meta={"code": "ENEU"},
        ),
        # ODUR : Session of zero duration (rule 40)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_statique,
  $f_energy_session,
  sessions_instant AS (
    SELECT
      count(*) AS n_inst_ses
    FROM
      f_session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
    WHERE
      end_session = start_session
  ),
  nb_sessions AS (
    SELECT
      count(f_SESSION.id) AS n_ses
    FROM
      f_session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
  )
SELECT
  *
FROM
  sessions_instant,
  nb_sessions
WHERE
  n_inst_ses::float > $threshold_percent * n_ses::float
                """
            ).substitute(f_statique | f_energy_session | ODUR.params),
            meta={"code": ODUR.code},
        ),
        # ENEA : Session with abnormal energy (rule 38)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_statique,
  $f_energy_session,
  sessions_max AS (
    SELECT
      count(*) AS n_max_ses
    FROM
      f_session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
    WHERE
      end_session = start_session
      AND energy > extract(
        'epoch' FROM (end_session - start_session)
      ) / 3600.0 * puissance_nominale * $abnormal_coef
      AND (
        energy < extract(
          'epoch' FROM (end_session - start_session)
        ) / 3600.0 * puissance_nominale * $excess_coef
        OR energy <= $excess_threshold_kWh
      )
  ),
  nb_sessions AS (
    SELECT
      count(f_SESSION.id) AS n_ses
    FROM
      f_session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
  )
SELECT
  *
FROM
  sessions_max,
  nb_sessions
WHERE
  n_max_ses::float > $threshold_percent * n_ses::float
                """
            ).substitute(f_statique | f_energy_session | ENEA.params | ENEX.params),
            meta={"code": ENEA.code},
        ),
        # ENEX : Session with excessive energy (rule 41)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_statique,
  $f_energy_session
SELECT
  start_session,
  end_session,
  energy,
  id_pdc_itinerance,
  puissance_nominale,
  nom_operateur,
  nom_amenageur,
  energy / extract(
    'epoch' FROM (end_session - start_session)
  ) * 3600.0 / puissance_nominale AS ratio_max_energy
FROM
  f_session
  INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
WHERE
  end_session <> start_session
  AND energy > $excess_threshold_kWh
  AND energy > extract(
    'epoch' FROM (end_session - start_session)
  ) / 3600.0 * puissance_nominale * $excess_coef
                """
            ).substitute(f_statique | f_energy_session | ENEX.params),
            meta={"code": ENEX.code},
        ),
    ]

    sessions_expectations = [
        # DUPS : Duplicate sessions (rule 17)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_statique,
  $f_session,
  nb_session AS (
    SELECT
      count(*) as nbre_session
    FROM
      f_session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
  ),
  nb_session_duplicate AS (
    SELECT
      count(*) as nbre_duplicate
    FROM
      (
        SELECT
          nb_id,
          start_session,
          end_session,
          id_pdc_itinerance
        FROM
          (
            SELECT
              count(id) AS nb_id,
              start_session,
              end_session,
              point_de_charge_id
            FROM
              f_session
            GROUP BY
              start_session,
              end_session,
              point_de_charge_id
          ) AS list_session
          INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
        WHERE
          nb_id > 1
      ) AS duplicates
  )
SELECT
  *
FROM
  nb_session_duplicate,
  nb_session
WHERE
  nbre_duplicate::float > $threshold_percent * nbre_session::float
                """
            ).substitute(f_statique | f_session | DUPS.params),
            meta={"code": DUPS.code},
        ),
        # OVRS : Number of days-poc with more than max_sessions_per_day (rule 13)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_statique,
  $f_session
SELECT
  nb_id,
  start_session,
  id_pdc_itinerance,
  nom_amenageur,
  nom_operateur
FROM
  (
    SELECT
      count(id) AS nb_id,
      start_session::date,
      point_de_charge_id
    FROM
      f_session
    GROUP BY
      start_session::date, point_de_charge_id
  ) AS list_sessions
  INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
WHERE
  nb_id > $max_sessions_per_day
                """
            ).substitute(f_statique | f_session | OVRS.params),
            meta={"code": OVRS.code},
        ),
        # LONS : Sessions of more than max_days_per_session (rule 15)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_statique,
  $f_session,
  long_sessions AS (
    SELECT
      count(*) AS n_long_ses
    FROM
      f_session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
    WHERE
      end_session > start_session + interval '$max_days_per_session'
  ),
  nb_sessions AS (
    SELECT
      count(f_session.id) AS n_ses
    FROM
      f_session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
  )
SELECT
  *
FROM
  long_sessions,
  nb_sessions
WHERE
  n_long_ses::float > $threshold_percent * n_ses::float
            """
            ).substitute(f_statique | f_session | LONS.params),
            meta={"code": LONS.code},
        ),
        # NEGS : Sessions with negative duration (rule 14)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_statique,
  $f_session
SELECT
  start_session,
  end_session,
  id_pdc_itinerance,
  energy,
  nom_amenageur,
  nom_operateur
FROM
  f_session
  INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
WHERE
  start_session > end_session
                """
            ).substitute(f_statique | f_session),
            meta={"code": "NEGS"},
        ),
        # FRES : freshness of sessions greater than max_duration days (rule 42)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_statique,
  $f_session,
  session_delay AS (
    SELECT
      max(EXTRACT(EPOCH FROM (updated_at - end_session))) / 3600 / 24 AS max_delay
    FROM
      f_session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
  )
SELECT
  *
FROM
  session_delay
WHERE
  max_delay > $max_duration_day
                """
            ).substitute(f_statique | f_session | FRES.params),
            meta={"code": FRES.code},
        ),
    ]
    statuses_expectations = [
        # ERRT : Inconsistent statuses (rule 37)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_statique,
  $f_status
SELECT
  f_status.id,
  occupation_pdc,
  etat_pdc
FROM
  f_status
  INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
WHERE
  etat_pdc = 'hors_service'
  AND occupation_pdc = 'occupe'
                """
            ).substitute(f_statique | f_status),
            meta={"code": "ERRT"},
        ),
        # FTRT : Timestamp in the future (rule 36)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_statique,
  f_status AS (
    SELECT
      id,
      point_de_charge_id,
      etat_pdc,
      occupation_pdc,
      horodatage
    FROM
      status
    WHERE
      horodatage < timestamp '01-01-2024'
      OR horodatage > CURRENT_TIMESTAMP
      OR horodatage IS NULL
  )
SELECT
  horodatage,
  id_pdc_itinerance
FROM
  f_status
  INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
                """
            ).substitute(f_statique | f_status),
            meta={"code": "FTRT"},
        ),
        # DUPT : Duplicate statuses (rule 44)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_statique,
  $f_status,
  nb_status AS (
    SELECT
      count(*) AS nbre_status
    FROM
      f_status
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
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
          f_status
          INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
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
            ).substitute(f_statique | f_status | DUPT.params),
            meta={"code": DUPT.code},
        ),
        # FRET : Freshness of statuses greater than max_duration seconds (rule 43)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_statique,
  $f_status,
  status_delay AS (
    SELECT
      horodatage,
      extract(
        SECOND
        FROM
          f_status.updated_at - horodatage
      ) + extract(
        MINUTE
        FROM
          f_status.updated_at - horodatage
      ) * 60 AS delay,
      horodatage::date AS date_s
    FROM
      f_status
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
  )
SELECT
  avg(delay)
FROM
  status_delay
HAVING
  avg(delay) > $mean_duration_second
                """
            ).substitute(f_statique | f_status | FRET.params),
            meta={"code": FRET.code},
        ),
    ]
    statuses_sessions_expectations = [
        # RATS : Ratio number of statuses / number of sessions (rule 49)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_statique,
  $f_status,
  $f_session,
  n_session AS (
    SELECT
      COUNT(*) AS nb_session
    FROM
      f_session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
  ),
  n_status AS (
    SELECT
      COUNT(*) AS nb_status
    FROM
      f_status
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
  )
SELECT
  nb_status::float / nb_session::float AS ratio_status_session
FROM
  n_session,
  n_status
WHERE
  nb_status::float / nb_session::float > $ratio_statuses_per_session_max
  OR nb_status::float / nb_session::float < $ratio_statuses_per_session_min
                """
            ).substitute(f_statique | f_status | f_session | RATS.params),
            meta={"code": RATS.code},
        ),
        # OCCT : Number of days-poc with status 'occupe' and without session (rule 21)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_statique,
  $f_status,
  $f_session,
  nombre_status AS (
    SELECT
      count(f_status.id) AS nb_status,
      id_pdc_itinerance,
      point_de_charge_id AS status_pdc_id,
      horodatage::date AS date_status
    FROM
      f_status
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
    WHERE
      occupation_pdc = 'occupe'
    GROUP BY
      id_pdc_itinerance,
      status_pdc_id,
      date_status
  ),
  nombre_sessions AS (
    SELECT
      count(f_session.id) AS nb_sessions,
      point_de_charge_id AS session_pdc_id,
      start_session::date AS date_session
    FROM
      f_session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
    GROUP BY
      session_pdc_id,
      date_session
  ),
  nombre_status_session AS (
    SELECT
      nb_status,
      id_pdc_itinerance,
      date_status
    FROM
      nombre_status
      LEFT JOIN nombre_sessions ON (
        nombre_sessions.session_pdc_id = nombre_status.status_pdc_id
        AND date_status = date_session
      )
    WHERE
      nb_sessions IS NULL
  )
SELECT
  n_stat_ses::float / n_stat::float * 100 AS ratio_status,
  n_stat_ses,
  n_stat
FROM
  (
    SELECT
      count(*) AS n_stat_ses
    FROM
      nombre_status_session
    WHERE
      nb_status > 1
  ) AS nb_stat_ses,
  (
    SELECT
      count(*) AS n_stat
    FROM
      nombre_status
    WHERE
      nb_status > 1
  ) AS nb_stat
WHERE
  n_stat_ses::float / n_stat::float > $threshold_percent
                """
            ).substitute(f_statique | f_status | f_session | OCCT.params),
            meta={"code": OCCT.code},
        ),
        # SEST : Number of days-poc with session and without status 'occupe' (rule 22)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_statique,
  $f_status,
  $f_session,
  nombre_status AS (
    SELECT
      horodatage::date AS date_status,
      count(f_status.id) AS nb_status,
      point_de_charge_id AS status_pdc_id,
      id_pdc_itinerance
    FROM
      f_statique
    INNER JOIN f_status on point_de_charge_id = f_statique.pdc_id
    WHERE
      occupation_pdc = 'occupe'
    GROUP BY
      id_pdc_itinerance,
      status_pdc_id,
      date_status
  ),
  nombre_sessions AS (
    SELECT
      count(f_session.id) AS nb_sessions,
      id_pdc_itinerance,
      point_de_charge_id AS session_pdc_id,
      start_session::date AS date_session
    FROM
      f_session
    INNER JOIN f_statique on point_de_charge_id = f_statique.pdc_id
    GROUP BY
      id_pdc_itinerance,
      session_pdc_id,
      date_session
  ),
  nombre_status_session AS (
    SELECT
      nb_sessions,
      nombre_sessions.id_pdc_itinerance,
      date_session
    FROM
      nombre_sessions
      LEFT JOIN nombre_status ON (
        nombre_status.id_pdc_itinerance = nombre_sessions.id_pdc_itinerance
        AND date_status = date_session
      )
    WHERE
      nb_status IS NULL
  )
SELECT
  n_stat_ses::float / n_ses::float * 100 as ratio_sessions,
  n_stat_ses,
  n_ses
FROM
  (
    SELECT
      count(*) AS n_stat_ses
    FROM
      nombre_status_session
  ) AS nb_stat_ses,
  (
    SELECT
      count(*) AS n_ses
    FROM
      nombre_sessions
  ) AS nb_ses
WHERE
  n_stat_ses::float / n_ses::float > $threshold_percent
                """
            ).substitute(f_statique | f_status | f_session | SEST.params),
            meta={"code": SEST.code},
        ),
    ]
    suite = gx.ExpectationSuite(name=NAME)
    expectations = (
        energy_expectations
        + sessions_expectations
        + statuses_expectations
        + statuses_sessions_expectations
    )
    for expectation in expectations:
        # Make sure expectation is not already assigned to a suite…
        exp = copy(expectation)
        exp.id = None
        # …before adding it to the current suite.
        suite.add_expectation(exp)
    return suite

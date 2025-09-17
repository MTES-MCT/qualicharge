"""Expectations for the dynamic data."""

from copy import copy
from datetime import date
from string import Template

import great_expectations as gx
import great_expectations.expectations as gxe

from .parameters import DUPS, ENEA, ENERGY, ENEX, FRES, LONS, ODUR, OVRS

NAME: str = "dynamic"
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
            ).substitute(
                f_statique | f_energy_session | ODUR.params  # type: ignore
            ),
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
            ).substitute(
                f_statique | f_energy_session | ENEA.params | ENEX.params  # type: ignore
            ),
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
            ).substitute(
                f_statique | f_energy_session | ENEX.params  # type: ignore
            ),
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
            ).substitute(
                f_statique | f_session | DUPS.params  # type: ignore
            ),
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
            ).substitute(
                f_statique | f_session | OVRS.params  # type: ignore
            ),
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
            ).substitute(
                f_statique | f_session | LONS.params  # type: ignore
            ),
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
            ).substitute(
                f_statique | f_session | FRES.params
            ),  # type: ignore
            meta={"code": FRES.code},
        ),
    ]
    suite = gx.ExpectationSuite(name=NAME)
    expectations = energy_expectations + sessions_expectations
    for expectation in expectations:
        # Make sure expectation is not already assigned to a suite…
        exp = copy(expectation)
        exp.id = None
        # …before adding it to the current suite.
        suite.add_expectation(exp)
    return suite

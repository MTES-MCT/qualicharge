"""Expectations for the dynamic data."""

from copy import copy
from datetime import date
from string import Template

import great_expectations as gx
import great_expectations.expectations as gxe

from .parameters import DUPS, ENEU, FRES, LONS, OVRS

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
INTERVAL_SESSION_TEMPLATE_ENEU = """
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
      energy > $max_energy_kwh
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
    f_session_ENEU = {
        "f_session_ENEU": Template(INTERVAL_SESSION_TEMPLATE_ENEU).substitute(
            date_params | ENEU.params  # type: ignore
        )
    }
    f_statique = {"f_statique": FILTERED_STATIQUE}

    energy_expectations = [
        # ENEU : Energy greater than max_energy_kwh (rule 11)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  $f_session_ENEU
SELECT
  energy,
  nom_amenageur,
  start_session,
  end_session,
  id_pdc_itinerance
FROM
  f_session
  INNER JOIN ({batch}) AS statique_amenageur ON point_de_charge_id = pdc_id
                """
            ).substitute(f_session_ENEU),
            meta={"code": ENEU.code},
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
  delai_session AS (
    SELECT
      max(EXTRACT(EPOCH FROM (updated_at - end_session))) / 3600 / 24 AS max_delai
    FROM
      f_session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
  )
SELECT
  *
FROM
  delai_session
WHERE
  max_delai > $max_duration_day
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

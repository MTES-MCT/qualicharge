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
    ENEU,
    ENEX,
    ERRT,
    FRES,
    FRET,
    FTRT,
    LONS,
    NEGS,
    OCCT,
    ODUR,
    OVRS,
    RATS,
    SEST,
)

NAME: str = "dynamic"


def get_suite(date_start: date, date_end: date, parameters: list[str]):
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
            meta={"code": ENEU.code},
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
  n_inst_ses::float / n_ses as ratio
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
  n_max_ses::float / n_ses as ratio
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
  AND energy <= $highest_energy_kwh
  AND start >= $start
  AND start < $end
  AND energy > extract(
    'epoch' FROM (session.end - start)
  ) / 3600.0 * puissance_nominale * $excess_coef
                """
            ).substitute(date_params | ENEX.params | ENERGY),
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
  (nbre_session - nbre_unique)::float / nbre_session as ratio
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
  n_long_ses::float / n_ses AS ratio
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
            meta={"code": NEGS.code},
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
  max(EXTRACT(EPOCH FROM (updated_at - session_end))) / 3600 / 24 AS ratio
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
            meta={"code": ERRT.code},
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
            meta={"code": FTRT.code},
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
  (nbre_status - nbre_unique)::float / nbre_status AS ratio
FROM
  nb_status_unique,
  nb_status
WHERE
  (nbre_status - nbre_unique)::float > $threshold_percent * nbre_status::float
                """
            ).substitute(date_params | DUPT.params),
            meta={"code": DUPT.code},
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
      extract(MINUTE FROM updated_at - horodatage) * 60) AS ratio
FROM
  status_delay
HAVING
  avg(extract(SECOND FROM updated_at - horodatage) +
      extract(MINUTE FROM updated_at - horodatage) * 60) > $mean_duration_second
                """
            ).substitute(date_params | FRET.params),
            meta={"code": FRET.code},
        ),
    ]
    statuses_sessions_expectations = [
        # RATS : Ratio number of statuses / number of sessions (rule 49)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  f_statique AS {batch},
  n_session AS (
    SELECT
      COUNT(*) AS nb_session
    FROM
      session
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
	WHERE
      START >= $start
      AND START < $end
  ),
  n_status AS (
    SELECT
      COUNT(*) AS nb_status
    FROM
      status
      INNER JOIN f_statique ON point_de_charge_id = f_statique.pdc_id
	WHERE
      horodatage >= $start
      AND horodatage < $end
  )
SELECT
  nb_status::float / nb_session AS ratio
FROM
  n_session,
  n_status
WHERE
  nb_status::float / nb_session::float > $ratio_statuses_per_session_max
  OR nb_status::float / nb_session::float < $ratio_statuses_per_session_min
                """
            ).substitute(date_params | RATS.params),
            meta={"code": RATS.code},
        ),
        # OCCT : Number of days-poc with status 'occupe' and without session (rule 21)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  f_statique AS {batch},
  nombre_status AS (
    SELECT
      count(status.id) AS nb_status,
      status.point_de_charge_id AS status_pdc_id,
      status.horodatage::date AS date_status
    FROM
      status
      INNER JOIN f_statique on status.point_de_charge_id = f_statique.pdc_id
    WHERE
      status.occupation_pdc = 'occupe'
      AND horodatage >= $start
      AND horodatage < $end
    GROUP BY
      status_pdc_id,
      date_status
  ),
  nombre_sessions AS (
    SELECT
      count(SESSION.id) AS nb_sessions,
      SESSION.point_de_charge_id AS session_pdc_id,
      SESSION.start::date AS date_session
    FROM
      SESSION
      INNER JOIN f_statique on session.point_de_charge_id = f_statique.pdc_id
	WHERE
      SESSION.start >= $start
      AND SESSION.start < $end
    GROUP BY
      session_pdc_id,
      date_session
  ),
  nombre_status_session AS (
    SELECT
      nb_status
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
  n_stat_ses::float / n_stat AS ratio
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
            ).substitute(date_params | OCCT.params),
            meta={"code": OCCT.code},
        ),
        # SEST : Number of days-poc with session and without status 'occupe' (rule 22)
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query=Template(
                """
WITH
  f_statique AS {batch},
  nombre_status AS (
    SELECT
      horodatage::date AS date_status,
      count(status.id) AS nb_status,
      point_de_charge_id AS status_pdc_id,
      id_pdc_itinerance
    FROM
      f_statique
      INNER JOIN status on point_de_charge_id = f_statique.pdc_id
    WHERE
      occupation_pdc = 'occupe'
      AND horodatage >= $start
      AND horodatage < $end
    GROUP BY
      id_pdc_itinerance,
      status_pdc_id,
      date_status
  ),
  nombre_sessions AS (
    SELECT
      count(session.id) AS nb_sessions,
      id_pdc_itinerance,
      point_de_charge_id AS session_pdc_id,
      session.start::date AS date_session
    FROM
      session
      inner JOIN f_statique on point_de_charge_id = f_statique.pdc_id
    WHERE
      session.start >= $start
      AND session.start < $end
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
  n_stat_ses::float / n_ses AS ratio
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
            ).substitute(date_params | SEST.params),
            meta={"code": SEST.code},
        ),
    ]
    expectations = (
        energy_expectations
        + sessions_expectations
        + statuses_expectations
        + statuses_sessions_expectations
    )

    # build ExpectationSuite
    suite = gx.ExpectationSuite(name=NAME)
    for expectation in expectations:
        if expectation.meta["code"] in parameters:
            # Make sure expectation is not already assigned to a suite…
            exp = copy(expectation)
            exp.id = None
            # …before adding it to the current suite.
            suite.add_expectation(exp)
    return suite

"""Expectations for the `PointDeCharge` table."""

from copy import copy

import great_expectations as gx
import great_expectations.expectations as gxe

NAME: str = "static"

pdc_expectations = [
    gxe.ExpectColumnMinToBeBetween(
        column="puissance_nominale",
        min_value=1.3,
        meta={"code": "POWL"},
    ),
    gxe.ExpectColumnMaxToBeBetween(
        column="puissance_nominale",
        max_value=4000,
        meta={"code": "POWU"},
    ),
]
amenageur_expectations = [
    gxe.ExpectColumnValuesToNotBeNull(
        column="nom_amenageur",
        meta={"code": "AMEM1"},
    ),
    gxe.ExpectColumnValuesToNotBeNull(
        column="siren_amenageur",
        meta={"code": "AMEM2"},
    ),
    gxe.ExpectColumnValuesToNotBeNull(
        column="contact_amenageur",
        meta={"code": "AMEM3"},
    ),
]
operateur_expectations = [
    gxe.ExpectColumnValuesToNotBeNull(
        column="nom_operateur",
        meta={"code": "OPEM1"},
    ),
    gxe.ExpectColumnValuesToNotBeNull(
        column="telephone_operateur",
        meta={"code": "OPEM2"},
    ),
]
localisation_expectations = [
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query="""
SELECT
  id_station_itinerance,
  ST_X ("coordonneesXY"::geometry) AS longitude,
  ST_Y ("coordonneesXY"::geometry) AS latitude
FROM
  {batch}
WHERE
  (
    (
      ST_X ("coordonneesXY"::geometry) > 10
      OR ST_X ("coordonneesXY"::geometry) < -5
    )
    OR (
      ST_Y ("coordonneesXY"::geometry) > 52
      OR ST_Y ("coordonneesXY"::geometry) < 41
    )
  )
        """,
        meta={"code": "CRDS"},
    )
]
AFIREV_expectations = [
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query="""
SELECT
  id_station_itinerance
FROM
  {batch}
WHERE
  id_station_itinerance not like 'FR___P%'
        """,
        meta={"code": "AFIP"},
    ),
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query="""
SELECT
  id_pdc_itinerance
FROM
  {batch}
WHERE
  id_pdc_itinerance not like 'FR___E%'
        """,
        meta={"code": "AFIE"},
    ),
]
stations_50_pdc_expectations = [
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query="""
WITH
  nb_stations_50 AS (
    SELECT
      count(*) AS nbre_stat_50
    FROM
      (
        SELECT
          count(*) AS nb_pdc,
          id_station_itinerance
        FROM
          {batch}
        GROUP BY
          id_station_itinerance
      ) AS stat_nb_pdc
    WHERE
      nb_pdc > 50
  ),
  nb_stations AS (
    SELECT
      count(*) AS nbre_stat
    FROM
      {batch}
  )
SELECT
  *
FROM
  nb_stations_50,
  nb_stations
WHERE
  nbre_stat_50::float > 0.01 * nbre_stat
        """,
        meta={"code": "P50E"},
    )
]
nb_pdc_lower_nbre_pdc_expectations = [
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query="""
WITH
  nbrepdc AS (
    SELECT
      count(*) AS nb_pdc_calc,
      nbre_pdc,
      id_station_itinerance
    FROM
      {batch}
    GROUP BY
      nbre_pdc,
      id_station_itinerance
  )
SELECT
  *
FROM
  nbrepdc
WHERE
  nb_pdc_calc < nbre_pdc
  OR nbre_pdc < 1
        """,
        meta={"code": "PDCL"},
    )
]
insee_code_expectations = [
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query="""
SELECT DISTINCT ON (code_insee_commune)
  code_insee_commune
FROM
  {batch} AS statique
  LEFT JOIN city ON city.code = code_insee_commune
WHERE
  city.name IS NULL
        """,
        meta={"code": "INSE"},
    )
]
multiples_adresses_expectations = [
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query="""
WITH
  multiple_adresses AS (
    SELECT
      "coordonneesXY" AS multi_coord,
      id_station_itinerance,
      count(DISTINCT adresse_station) AS nb_adresses
    FROM
      {batch}
    GROUP BY
      "coordonneesXY",
      id_station_itinerance
  )
SELECT
  *
FROM
  multiple_adresses
WHERE
  nb_adresses > 1
        """,
        meta={"code": "ADDR"},
    )
]
stations_per_location_expectations = [
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query="""
WITH
  nb_localisation AS (
    SELECT
      count(DISTINCT "coordonneesXY") AS nbre_loc
    FROM
      {batch}
  ),
  nb_stations AS (
    SELECT
      count(DISTINCT id_station_itinerance) AS nbre_stat
    FROM
      {batch}
  )
SELECT
  *
FROM
  nb_localisation,
  nb_stations
WHERE
  nbre_stat::float > 1.5 * nbre_loc
        """,
        meta={"code": "LOCP"},
    )
]
num_PDL_expectations = [
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query="""
SELECT
  id_station_itinerance
FROM
  {batch}
WHERE
  raccordement <> 'Indirect'
  AND (
    puissance_nominale >= 50
    OR prise_type_combo_ccs
    OR prise_type_chademo
  ) IS TRUE
  AND (
    num_pdl IS NULL
    OR num_pdl = ''
    OR num_pdl = '00000000000000'
  )
        """,
        meta={"code": "PDLM"},
    ),
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query="""
WITH
  nb_station_dc AS (
    SELECT
      count(*) AS nbre_stat_dc
    FROM
      (
        SELECT DISTINCT
          ON (id_station_itinerance) id_station_itinerance
        FROM
          {batch}
        WHERE
          raccordement <> 'Indirect'
          AND (
            puissance_nominale >= 50
            OR prise_type_combo_ccs
            OR prise_type_chademo
          ) IS TRUE
      ) AS stat_dc
  ),
  nb_numpdl_not14 AS (
    SELECT
      count(*) AS nbre_numpdl_not14
    FROM
      (
        SELECT DISTINCT
          ON (id_station_itinerance) id_station_itinerance
        FROM
          {batch}
        WHERE
          raccordement <> 'Indirect'
          AND (
            puissance_nominale >= 50
            OR prise_type_combo_ccs
            OR prise_type_chademo
          ) IS TRUE
          AND (
            num_pdl NOT SIMILAR TO '[0-9]{14}'
            OR num_pdl = '00000000000000'
          )
      ) AS numpdl_dc
  )
SELECT
  *
FROM
  nb_station_dc,
  nb_numpdl_not14
WHERE
  nbre_numpdl_not14::float > 0.1 * nbre_stat_dc
        """,
        meta={"code": "NE10"},
    ),
]


def get_suite():
    """Get static expectation suite."""
    suite = gx.ExpectationSuite(name="static")
    expectations = (
        pdc_expectations
        + amenageur_expectations
        + operateur_expectations
        + localisation_expectations
        + AFIREV_expectations
        + stations_50_pdc_expectations
        + nb_pdc_lower_nbre_pdc_expectations
        + insee_code_expectations
        + multiples_adresses_expectations
        + stations_per_location_expectations
        + num_PDL_expectations
    )
    for expectation in expectations:
        # Make sure expectation is not already assigned to a suite…
        exp = copy(expectation)
        exp.id = None
        # …before adding it to the current suite.
        suite.add_expectation(exp)
    return suite

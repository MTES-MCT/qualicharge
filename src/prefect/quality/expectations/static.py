"""Expectations for the static data."""

from copy import copy
from string import Template

import great_expectations as gx
import great_expectations.expectations as gxe

NAME: str = "static"

POWU_PARAMETER: float = 4000  # max power kw
POWL_PARAMETER: float = 1.3  # min power kw
CRDS_PARAMETER: dict[str, float] = {
    "CRDS_LON_MAX": 10,
    "CRDS_LON_MIN": -5,
    "CRDS_LAT_MAX": 52,
    "CRDS_LAT_MIN": 41,
}

PDCM_PARAMETER: float = 50  # max number of pdc per station

PDCM_THRESHOLD: float = 0.01  # percentage 1 %
LOCP_THRESHOLD: float = 1.5  # ratio
NE10_THRESHOLD: float = 0.1  # percentage 10 %

IS_DC: str = """(
puissance_nominale >= 50
OR prise_type_combo_ccs
OR prise_type_chademo
)"""
FAKE_PDL: str = """(
'', '00000000000000', '012345678987654', '11111111111111', '99999999999999')
"""

pdc_expectations = [
    # Power less than POWL_PARAMETER (rule 39)
    gxe.ExpectColumnMinToBeBetween(
        column="puissance_nominale",
        min_value=POWL_PARAMETER,
        meta={"code": "POWL"},
    ),
    # Power greater than POWU_PARAMETER (rule 1)
    gxe.ExpectColumnMaxToBeBetween(
        column="puissance_nominale",
        max_value=POWU_PARAMETER,
        meta={"code": "POWU"},
    ),
]
amenageur_expectations = [
    # 'aménageur'(owner) fields not documented (rule 7)
    gxe.ExpectColumnValuesToNotBeNull(
        column="nom_amenageur",
        meta={"code": "AMEM1"},
    ),
    # 'aménageur'(owner) fields not documented (rule 7)
    gxe.ExpectColumnValuesToNotBeNull(
        column="siren_amenageur",
        meta={"code": "AMEM2"},
    ),
    # 'aménageur'(owner) fields not documented (rule 7)
    gxe.ExpectColumnValuesToNotBeNull(
        column="contact_amenageur",
        meta={"code": "AMEM3"},
    ),
]
operateur_expectations = [
    # 'operateur' fields not documented (rule 6)
    gxe.ExpectColumnValuesToNotBeNull(
        column="nom_operateur",
        meta={"code": "OPEM1"},
    ),
    # 'operateur' fields not documented (rule 6)
    gxe.ExpectColumnValuesToNotBeNull(
        column="telephone_operateur",
        meta={"code": "OPEM2"},
    ),
]
localisation_expectations = [
    # Geographic coordinates outside France (rule 3)
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query=Template(
            """
SELECT
  id_station_itinerance,
  ST_X ("coordonneesXY"::geometry) AS longitude,
  ST_Y ("coordonneesXY"::geometry) AS latitude
FROM
  {batch}
WHERE
  ST_X ("coordonneesXY"::geometry) > $CRDS_LON_MAX
  OR ST_X ("coordonneesXY"::geometry) < $CRDS_LON_MIN
  OR ST_Y ("coordonneesXY"::geometry) > $CRDS_LAT_MAX
  OR ST_Y ("coordonneesXY"::geometry) < $CRDS_LAT_MIN
        """
        ).substitute(CRDS_PARAMETER),
        meta={"code": "CRDS"},
    )
]
AFIREV_expectations = [
    # AFIREV format of stations not respected (rule 23)
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
    # AFIREV format of charging points not respected (rule 24)
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
stations_pdc_expectations = [
    # Stations with more than PDCM_PARAMETER charging points > PDCM_THRESHOLD (rule 30)  # noqa: E501
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query=Template(
            """
WITH
  nb_stations_max AS (
    SELECT
      count(*) AS nbre_stat_max
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
      nb_pdc > $PDCM_PARAMETER
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
  nb_stations_max,
  nb_stations
WHERE
  nbre_stat_max::float > $PDCM_THRESHOLD * nbre_stat
        """
        ).substitute(
            {"PDCM_PARAMETER": PDCM_PARAMETER, "PDCM_THRESHOLD": PDCM_THRESHOLD}
        ),
        meta={"code": "PDCM"},
    ),
    # number of pdc per station lower than nbre_pdc field (rule 47)
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
    ),
]
insee_code_expectations = [
    # INSEE municipality code not recognized (rule 2)
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
    # Addresses with identical geographic coordinates (rule 29)
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
    # Number of stations per location > LOCP_THRESHOLD (rule 46)
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query=Template(
            """
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
  nbre_stat::float > $LOCP_THRESHOLD * nbre_loc
        """
        ).substitute({"LOCP_THRESHOLD": LOCP_THRESHOLD}),
        meta={"code": "LOCP"},
    ),
]
num_PDL_expectations = [
    # PDL identifier not documented (rule 20)
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query=Template(
            """
SELECT
  id_station_itinerance
FROM
  {batch}
WHERE
  raccordement <> 'Indirect'
  AND $IS_DC
  AND (
    num_pdl IS NULL
    OR num_pdl IN $FAKE_PDL
  )
        """
        ).substitute({"IS_DC": IS_DC, "FAKE_PDL": FAKE_PDL}),
        meta={"code": "PDLM"},
    ),
    # ENEDIS format not respected (14 digits) > NE10_THRESHOLD (rule 34)
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query=Template(
            """
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
          AND $IS_DC
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
          AND $IS_DC
          AND num_pdl NOT SIMILAR TO '[0-9]{{14}}'
      ) AS numpdl_dc
  )
SELECT
  *
FROM
  nb_station_dc,
  nb_numpdl_not14
WHERE
  nbre_numpdl_not14::float > $NE10_THRESHOLD * nbre_stat_dc
        """
        ).substitute({"IS_DC": IS_DC, "NE10_THRESHOLD": NE10_THRESHOLD}),
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
        + stations_pdc_expectations
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

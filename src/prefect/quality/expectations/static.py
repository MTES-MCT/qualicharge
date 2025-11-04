"""Expectations for the static data."""

from copy import copy
from string import Template

import great_expectations as gx
import great_expectations.expectations as gxe

from .parameters import CRDF, LOCP, NE10, PDCM, POWL, POWU

NAME: str = "static"

IS_DC: str = """(
puissance_nominale >= 50
OR prise_type_combo_ccs
OR prise_type_chademo
)"""
FAKE_PDL: str = """(
'', '00000000000000', '012345678987654', '11111111111111', '99999999999999')
"""

pdc_expectations = [
    # POWL : Power less than POWL_PARAMETER (rule 39)
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query=Template(
            """
SELECT
  id_pdc_itinerance,
  puissance_nominale
FROM
  {batch}
WHERE
  puissance_nominale <= $min_power_kw
        """
        ).substitute(POWL.params),
        meta={"code": POWL.code},
    ),
    # POWU : Power greater than POWU_PARAMETER (rule 1)
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query=Template(
            """
SELECT
  id_pdc_itinerance,
  puissance_nominale
FROM
  {batch}
WHERE
  puissance_nominale >= $max_power_kw
        """
        ).substitute(POWU.params),
        meta={"code": POWU.code},
    ),
]
amenageur_expectations = [
    # AMEM1 : 'aménageur'(owner) fields not documented (rule 7)
    gxe.ExpectColumnValuesToNotBeNull(
        column="nom_amenageur",
        meta={"code": "AMEM1"},
    ),
    # AMEM2 : 'aménageur'(owner) fields not documented (rule 7)
    gxe.ExpectColumnValuesToNotBeNull(
        column="siren_amenageur",
        meta={"code": "AMEM2"},
    ),
    # AMEM3 : 'aménageur'(owner) fields not documented (rule 7)
    gxe.ExpectColumnValuesToNotBeNull(
        column="contact_amenageur",
        meta={"code": "AMEM3"},
    ),
]
operateur_expectations = [
    # OPEM1 : 'operateur' fields not documented (rule 6)
    gxe.ExpectColumnValuesToNotBeNull(
        column="nom_operateur",
        meta={"code": "OPEM1"},
    ),
    # OPEM2 : 'operateur' fields not documented (rule 6)
    gxe.ExpectColumnValuesToNotBeNull(
        column="telephone_operateur",
        meta={"code": "OPEM2"},
    ),
]
localisation_expectations = [
    # CRDF : Geographic coordinates outside France (rule 3)
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
  ST_X ("coordonneesXY"::geometry) > $max_lon
  OR ST_X ("coordonneesXY"::geometry) < $min_lon
  OR ST_Y ("coordonneesXY"::geometry) > $max_lat
  OR ST_Y ("coordonneesXY"::geometry) < $min_lat
        """
        ).substitute(CRDF.params),
        meta={"code": CRDF.code},
    )
]
AFIREV_expectations = [
    # AFIP : AFIREV format of stations not respected (rule 23)
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
    # AFIE : AFIREV format of charging points not respected (rule 24)
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
    # PDCM : Stations with more than PDCM_PARAMETER charging points > PDCM_THRESHOLD (rule 30)  # noqa: E501
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
      nb_pdc > $max_pdc_per_station
  ),
  nb_stations AS (
    SELECT
      count(*) AS nbre_stat
    FROM
      {batch}
  )
SELECT
  nbre_stat_max::float / nbre_stat AS ratio
FROM
  nb_stations_max,
  nb_stations
WHERE
  nbre_stat_max::float > $threshold_percent * nbre_stat
        """
        ).substitute(PDCM.params),
        meta={"code": PDCM.code},
    ),
    # PDCL : number of pdc per station lower than nbre_pdc field (rule 47)
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
    # INSE : INSEE municipality code not recognized (rule 2)
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
    # ADDR : Addresses with identical geographic coordinates (rule 29)
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
    # LOCP : Number of stations per location > LOCP_THRESHOLD (rule 46)
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
  nbre_stat::float / nbre_loc AS ratio
FROM
  nb_localisation,
  nb_stations
WHERE
  nbre_stat::float > $ratio_stations_per_location * nbre_loc
        """
        ).substitute(LOCP.params),
        meta={"code": LOCP.code},
    ),
]
num_PDL_expectations = [
    # PDLM : PDL identifier not documented (rule 20)
    gxe.UnexpectedRowsExpectation(
        unexpected_rows_query=Template(
            """
SELECT
  id_station_itinerance
FROM
  {batch}
WHERE
  (raccordement IS NULL OR raccordement = 'Direct')
  AND $IS_DC
  AND (
    num_pdl IS NULL
    OR num_pdl LIKE '% %'
    OR num_pdl LIKE '%NA%'
    OR num_pdl IN $FAKE_PDL
  )
        """
        ).substitute({"IS_DC": IS_DC, "FAKE_PDL": FAKE_PDL}),
        meta={"code": "PDLM"},
    ),
    # NE10 : ENEDIS format not respected (14 digits) > NE10_THRESHOLD (rule 34)
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
          (raccordement IS NULL OR raccordement = 'Direct')
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
          (raccordement IS NULL OR raccordement = 'Direct')
          AND $IS_DC
          AND num_pdl NOT SIMILAR TO '[0-9]{{14}}'
      ) AS numpdl_dc
  )
SELECT
  nbre_numpdl_not14::float / nbre_stat_dc AS ratio
FROM
  nb_station_dc,
  nb_numpdl_not14
WHERE
  nbre_numpdl_not14::float > $threshold_percent * nbre_stat_dc
        """
        ).substitute(
            {"IS_DC": IS_DC} | NE10.params  # type: ignore
        ),
        meta={"code": NE10.code},
    ),
]


def get_suite():
    """Get static expectation suite."""
    suite = gx.ExpectationSuite(name=NAME)
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

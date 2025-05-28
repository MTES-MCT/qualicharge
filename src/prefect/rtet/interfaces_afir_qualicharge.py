"""Qualicharge prefect rtet: file interfaces."""

import geo_nx as gnx
import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from shapely import Point

from .fonction_afir import (
    association_stations,
    get_parc_id_station,
    get_rtet_attr_station,
    propagation_attributs_core,
)

GEOM = "geometry"
NODE_ID = "node_id"
NATURE = "nature"
WEIGHT = "weight"
CORE = "core"


def creation_pandas_stations(
    data: str | pd.DataFrame, nature="station_irve", first_id=0, source="gireve"
) -> pd.DataFrame:
    """Generation d'un DataFrame des stations.

    Champs du DataFrame:
    - geometry : Point
    - amenageur : nom de l amenageur
    - operateur : nom de l operateur
    - p_cum : puissance cumulée de la station
    - p_max : puissance maxi des points de recharge
    - node_id : numéro de node
    - id_station : identifiant de la station
    - nature : type de station
    """
    if source == "gireve":
        # Chargement des points de recharge de la consolidation Gireve
        csl = (
            pd.read_csv(data, sep=";", encoding="latin")
            if isinstance(data, str)
            else data
        )
        if csl["puissance_nominale"].dtype != np.dtype("float64"):
            csl["puissance_nominale"] = (
                csl["puissance_nominale"].str.replace(",", ".").astype(float)
            )

        # Les stations sont obtenues après un groupby sur les coordonnées
        stations_csl = csl.groupby("coordonneesXY").agg(
            p_max=("puissance_nominale", "max"),
            p_cum=("puissance_nominale", "sum"),
            id_station=("id_pdc_regroupement", "first"),
            amenageur=("nom_amenageur", "first"),
            operateur=("nom_operateur", "first"),
        )
        stations = stations_csl.reset_index()
        stations[GEOM] = stations["coordonneesXY"].apply(
            lambda x: Point(str.split(x, ","))
        )
        stations = gpd.GeoDataFrame(stations, crs=4326).to_crs(2154)
    elif source == "qualicharge":
        csl = pd.read_csv(data, sep=",") if isinstance(data, str) else data
        geom = gpd.points_from_xy(csl.longitude, csl.latitude)
        stations = gpd.GeoDataFrame(csl, geometry=geom, crs=4326).to_crs(2154)
    stations[NODE_ID] = range(first_id, len(stations) + first_id)
    stations[NATURE] = nature

    return stations[
        [
            "p_cum",
            "p_max",
            "id_station",
            "operateur",
            "amenageur",
            GEOM,
            NODE_ID,
            NATURE,
        ]
    ]


def export_stations_parcs(graph: gnx.GeoGraph, simple: bool = False) -> pd.DataFrame:
    """Extraction et export des stations et parcs de recharge d'un graphe."""
    gr_stations = nx.subgraph_view(
        graph, filter_node=lambda x: graph.nodes[x][NATURE] == "station_irve"
    )
    stations = gr_stations.to_geopandas_nodelist()
    stations[CORE] = stations["node_id"].apply(
        get_rtet_attr_station, args=(graph, CORE)
    )
    stations["parc_nature"] = stations["node_id"].apply(
        get_rtet_attr_station, args=(graph, NATURE)
    )
    stations["parc_geometry"] = stations["node_id"].apply(
        get_rtet_attr_station, args=(graph, GEOM)
    )
    stations["parc_id"] = stations["node_id"].apply(get_parc_id_station, args=(graph,))
    stations["id_station_itinerance"] = stations["id_station"]

    if simple:
        return stations[
            [
                "id_station_itinerance",
                CORE,
                NODE_ID,
                "parc_nature",
                "parc_geometry",
                "parc_id",
            ]
        ]
    return stations


def filter_stations_parcs(  # noqa: PLR0913
    rtet_edges, rtet_nodes, stations, pmax=0, pcum=0, simple=False
) -> pd.DataFrame:
    """Extraction et export des stations et parcs de recharge d'un graphe."""
    # réseau rtet
    gr = gnx.from_geopandas_edgelist(
        rtet_edges, node_gdf=rtet_nodes, node_attr=True, edge_attr=True
    )

    # mise au format afir des stations
    first_id = max(gr.nodes) + 1
    stations_afir = creation_pandas_stations(
        stations, nature="station_irve", first_id=first_id, source="qualicharge"
    )
    stations_afir_p = stations_afir[
        (stations_afir["p_max"] > pmax) & (stations_afir["p_cum"] > pcum)
    ].reset_index()

    # réseau global
    gr_afir = association_stations(gr, stations_afir_p, log=True)
    propagation_attributs_core(gr_afir, "aire de recharge")

    # génération des stations liées au réseau RTET
    return export_stations_parcs(gr_afir, simple=simple)

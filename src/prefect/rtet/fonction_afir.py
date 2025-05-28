"""Qualicharge prefect rtet: rtet analysis."""

import geo_nx as gnx
import geopandas as gpd

GEOM = "geometry"
NODE_ID = "node_id"
NATURE = "nature"
WEIGHT = "weight"
CORE = "core"


def insertion_noeuds(  # noqa: PLR0913
    noeuds: gpd.GeoDataFrame,
    gr: gnx.GeoGraph,
    proxi: float,
    att_node: None | dict = None,
    troncons: None | gpd.GeoDataFrame = None,
    adjust: bool = False,
) -> list[int]:
    """Insere des 'noeuds' sur le graph 'gr' pour des troncons définis.

    retourne les 'noeuds' ajoutés.
    """
    gpd_troncons: gpd.GeoDataFrame = (
        troncons if troncons is not None else gr.to_geopandas_edgelist()
    )
    join = gpd.sjoin(
        noeuds, gpd_troncons.set_geometry(gpd_troncons.buffer(proxi))
    )  # filtrage des tronçons
    noeuds_ok = noeuds[noeuds.index.isin(join.index)].copy()
    noeuds_ok[NODE_ID] = range(max(gr.nodes) + 1, len(noeuds_ok) + max(gr.nodes) + 1)
    gs_noeuds = gnx.from_geopandas_nodelist(
        noeuds_ok, node_id=NODE_ID, node_attr=True
    )  # réseau des noeuds supplémentaires
    # à vectoriser
    added_nodes = []
    for noeud in gs_noeuds:
        geo_st = gs_noeuds.nodes[noeud][GEOM]
        id_edge = gr.find_nearest_edge(
            geo_st, proxi
        )  # recherche du troncon le plus proche
        att_noeud = (
            att_node
            if att_node is not None
            else {
                key: val
                for key, val in gs_noeuds.nodes[noeud].items()
                if key not in [NODE_ID, GEOM]
            }
        )
        dis = gr.insert_node(
            geo_st, noeud, id_edge, att_node=att_noeud, adjust=adjust
        )  # ajout du noeud
        if dis is not None:
            added_nodes.append(noeud)
    return added_nodes


def proximite(
    noeuds_ext: gpd.GeoDataFrame, cible: gpd.GeoDataFrame, proxi: float
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Sépare les noeuds proches (distance < proxi) et non proches."""
    st_join = gpd.sjoin(noeuds_ext, cible.set_geometry(cible.buffer(proxi)))
    st_ok = noeuds_ext.index.isin(st_join.index)
    return (noeuds_ext[st_ok], noeuds_ext[~st_ok])


def insertion_projection(  # noqa: PLR0913
    nodes_ext: gpd.GeoDataFrame,
    node_attr: bool | str | list[str],
    edge_attr: None | dict,
    gr: gnx.GeoGraph,
    proxi: float,
    att_insert_node: None | dict,
) -> tuple[gnx.GeoGraph, list]:
    """Création du graphe des stations avec projection sur des noeuds 'gr' inserés."""
    gr_ext = gnx.from_geopandas_nodelist(
        nodes_ext, node_id="node_id", node_attr=node_attr
    )
    stations = list(nodes_ext[NODE_ID])
    st_ko = []
    for station in stations:  # à vectoriser
        dist = gr_ext.project_node(station, gr, proxi, att_edge=edge_attr)
        if not dist:
            geo_st = gr_ext.nodes[station][GEOM]
            id_edge = gr.find_nearest_edge(geo_st, proxi)
            if not id_edge:
                st_ko.append(station)
                continue
            # on ajoute un noeud et on crée le lien
            id_node = max(gr.nodes) + 1
            dis = gr.insert_node(
                geo_st, id_node, id_edge, att_node=att_insert_node, adjust=False
            )
            if dis is None:
                dist0 = geo_st.distance(gr.nodes[id_edge[0]][GEOM])
                dist1 = geo_st.distance(gr.nodes[id_edge[1]][GEOM])
                id_node = id_edge[0] if dist0 <= dist1 else id_edge[1]
            gr_ext.project_node(station, gr, 0, target_node=id_node, att_edge=edge_attr)
    return gr_ext, st_ko


def association_stations(
    gr: gnx.GeoGraph, stations_afir: gpd.GeoDataFrame, log: bool = False
) -> None | gnx.GeoGraph:
    """Intègre les stations au graphe routier."""
    if gr is None or stations_afir is None:
        return None
    # high_proxi_t = 100
    high_proxi_n = 300
    low_proxi = 2000

    noeuds = gr.to_geopandas_nodelist()
    noeuds_station = noeuds.loc[noeuds[NATURE] == "aire de service"]
    troncons = gr.to_geopandas_edgelist()
    # troncons_hors_autoroute = troncons.loc[troncons[NATURE]=="troncon hors autoroute"]

    st_low_proxi, st_out = proximite(stations_afir, troncons, low_proxi)
    st_high_proxi_n, st_proxi_t = proximite(st_low_proxi, noeuds_station, high_proxi_n)
    # st_high_proxi_t, st_low_proxi = proximite(
    #    st_proxi_t, troncons_hors_autoroute, high_proxi_t
    # )
    if log:
        print(  # noqa: T201
            "Nb stations (st, pre_st, ext, out, total) : ",
            len(st_high_proxi_n),
            len(st_proxi_t),
            # len(st_high_proxi_t),
            # len(st_low_proxi),
            len(st_out),
            len(stations_afir),
        )
    node_attr = ["amenageur", "operateur", "p_cum", "p_max", "id_station", NATURE]

    # IRVE très proches des stations
    edge_attr = {NATURE: "liaison aire de service"}
    gs_station, st_ko = gnx.project_graph(
        st_high_proxi_n, noeuds_station, high_proxi_n, node_attr, edge_attr
    )

    # IRVE proches d'un tronçon
    edge_attr = {NATURE: "liaison exterieur"}
    filter = (noeuds[NATURE] == "echangeur") | (noeuds[NATURE] == "rond-point")
    gs_externe, st_ko = gnx.project_graph(
        # st_low_proxi, noeuds.loc[filter], low_proxi, node_attr, edge_attr
        st_proxi_t,
        noeuds.loc[filter],
        low_proxi,
        node_attr,
        edge_attr,
    )

    """# IRVE très proches d'un tronçon
    edge_attr = {NATURE: "liaison aire de recharge"}
    att_node_insert = {NATURE: "aire de recharge"}
    gs_pre_station, st_ko = insertion_projection(
        st_high_proxi_t, node_attr, edge_attr, gr, high_proxi_t, att_node_insert
    )"""
    # return gnx.compose_all([gr, gs_externe, gs_pre_station, gs_station])
    return gnx.compose_all([gr, gs_externe, gs_station])


def propagation_attributs_core(gr: gnx.GeoGraph, nature: str) -> None:
    """Propage l'attribut 'core' des tronçons sur les noeuds de type 'nature'."""
    for node in list(gr.nodes):
        if gr.nodes[node][NATURE] == nature:
            core = False
            for neighbors in gr.neighbors(node):
                if gr.edges[neighbors, node].get(CORE, False):
                    core = True
                    break
            gr.nodes[node][CORE] = core


def propagation_attributs_edges(gr: gnx.GeoGraph) -> None:
    """Crée les attributs 'core' et 'noeud autoroute' à partir des tronçons."""
    for node in list(gr.nodes):
        core = False
        for neighbors in gr.neighbors(node):
            if gr.edges[neighbors, node].get(CORE, False):
                core = True
                break
        gr.nodes[node][CORE] = core
        if gr.nodes[node][NATURE] == "noeud rtet":
            autoroute = True
            for neighbors in gr.neighbors(node):
                if gr.edges[neighbors, node][NATURE] != "troncon autoroute":
                    autoroute = False
                    break
            if autoroute:
                gr.nodes[node][NATURE] = "noeud autoroute"
    for edge in list(gr.edges):
        if gr.edges[edge][NATURE] == "liaison aire":
            core = gr.nodes[edge[0]].get(CORE, False) or gr.nodes[edge[1]].get(
                CORE, False
            )
            gr.edges[edge][CORE] = gr.nodes[edge[0]][CORE] = gr.nodes[edge[1]][CORE] = (
                core
            )


def get_rtet_attr_station(node, gr_station: gnx.GeoGraph, attr: str) -> bool:
    """Restitue la valeur d'un attribut du RTET."""
    return gr_station.nodes[list(gr_station.neighbors(node))[0]][attr]


def get_parc_id_station(node, gr_station: gnx.GeoGraph = None) -> str:
    """Restitue l'Id du parc associé à la station."""
    return "parc " + str(list(gr_station.neighbors(node))[0])

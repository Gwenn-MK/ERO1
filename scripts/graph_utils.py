"""
graph_utils.py
Auteurs: Gwenn Meku Kengne, Mariam Anu Akanni, Anna Bensammar, Hans Hookoom (EPITA)
"""

import networkx as nx
import random
import math

COUT_FIXE_JOUR = 500.0
COUT_KM        = 1.1
COUT_H_NORMAL  = 1.1
COUT_H_SUP     = 1.3
VITESSE_KMH    = 10.0
SEUIL_H_SUP    = 8.0

SCENARIO_WEIGHTS = {
    "economique": {
        "motorway": 0.90, "trunk": 0.90, "primary": 0.90,
        "secondary": 1.00, "tertiary": 1.00,
        "residential": 1.00, "living_street": 1.10,
        "service": 1.20, "unclassified": 1.00,
    },
    "social": {
        "motorway": 0.45, "trunk": 0.45, "primary": 0.45,
        "secondary": 0.60, "tertiary": 0.80,
        "residential": 1.20, "living_street": 1.40,
        "service": 1.80, "unclassified": 1.00,
    },
    "mixte": {
        "motorway": 0.60, "trunk": 0.60, "primary": 0.60,
        "secondary": 0.75, "tertiary": 0.90,
        "residential": 1.10, "living_street": 1.25,
        "service": 1.50, "unclassified": 1.00,
    },
}

POI_WEIGHTS = {
    "economique": {"hospital": 1.00, "school": 1.00, "bus_stop": 1.00, "none": 1.00},
    "social":     {"hospital": 0.50, "school": 0.60, "bus_stop": 0.70, "none": 1.00},
    "mixte":      {"hospital": 0.70, "school": 0.75, "bus_stop": 0.80, "none": 1.00},
}

SECTEURS_CONFIG = {
    "Outremont": {
        "osm_name"    : "Outremont, Montréal, Québec, Canada",
        "n_noeuds"    : 60,
        "densite"     : 0.06,
        "longueur_moy": 0.25,
        "description" : "Secteur résidentiel dense, rues en grille, faible circulation",
        "population"  : 24000,
        "km_routes"   : 45,
    },
    "Verdun": {
        "osm_name"    : "Verdun, Montréal, Québec, Canada",
        "n_noeuds"    : 80,
        "densite"     : 0.05,
        "longueur_moy": 0.30,
        "description" : "Secteur mixte résidentiel/commercial, bord du fleuve",
        "population"  : 70000,
        "km_routes"   : 110,
    },
    "Anjou": {
        "osm_name"    : "Anjou, Montréal, Québec, Canada",
        "n_noeuds"    : 70,
        "densite"     : 0.04,
        "longueur_moy": 0.40,
        "description" : "Secteur industriel et commercial, larges artères",
        "population"  : 42000,
        "km_routes"   : 85,
    },
    "RDP": {
        "osm_name"    : "Rivière-des-Prairies, Montréal, Québec, Canada",
        "n_noeuds"    : 100,
        "densite"     : 0.035,
        "longueur_moy": 0.50,
        "description" : "Rivière-des-Prairies-Pointe-aux-Trembles : secteur périphérique étendu",
        "population"  : 105000,
        "km_routes"   : 200,
    },
}


def compute_cost(distance_km: float, n_vehicles: int) -> dict:
    heures = distance_km / VITESSE_KMH
    cout_km = distance_km * COUT_KM
    if heures <= SEUIL_H_SUP:
        cout_h = heures * COUT_H_NORMAL
    else:
        cout_h = SEUIL_H_SUP * COUT_H_NORMAL + (heures - SEUIL_H_SUP) * COUT_H_SUP
    cout_total_vehicule = COUT_FIXE_JOUR + cout_km + cout_h
    cout_global = cout_total_vehicule * n_vehicles
    return {
        "distance_km"         : round(distance_km, 2),
        "heures"              : round(heures, 2),
        "cout_fixe"           : COUT_FIXE_JOUR,
        "cout_km"             : round(cout_km, 2),
        "cout_horaire"        : round(cout_h, 2),
        "cout_total_vehicule" : round(cout_total_vehicule, 2),
        "n_vehicles"          : n_vehicles,
        "cout_global"         : round(cout_global, 2),
    }


def get_real_graph(secteur: str) -> nx.DiGraph:
    import osmnx as ox
    cfg = SECTEURS_CONFIG[secteur]
    print(f"  [OSMnx] Téléchargement {secteur}...")
    G = ox.graph_from_place(cfg["osm_name"], network_type="drive")

    G_di = nx.DiGraph()
    for u, v, data in G.edges(data=True):
        length_km = data.get("length", 100) / 1000.0
        highway   = data.get("highway", "residential")
        if isinstance(highway, list):
            highway = highway[0]
        G_di.add_edge(u, v,
            length  = round(length_km, 4),
            highway = highway,
            poi     = "none",
            weight  = round(length_km, 4),
            street  = data.get("name", f"{u}-{v}"),
        )

    if not nx.is_strongly_connected(G_di):
        main = max(nx.strongly_connected_components(G_di), key=len)
        G_di = G_di.subgraph(main).copy()

    print(f"  [OSMnx] {secteur} : {G_di.number_of_nodes()} nœuds, "
          f"{G_di.number_of_edges()} arêtes (orienté)")
    return G_di


def generate_sector_graph(secteur: str, seed: int = 42) -> nx.DiGraph:
    cfg = SECTEURS_CONFIG[secteur]
    random.seed(seed)
    G_base = nx.erdos_renyi_graph(cfg["n_noeuds"], cfg["densite"], seed=seed)
    if not nx.is_connected(G_base):
        comps = list(nx.connected_components(G_base))
        for i in range(len(comps) - 1):
            u = list(comps[i])[0]
            v = list(comps[i + 1])[0]
            G_base.add_edge(u, v)

    highway_types = ["primary", "secondary", "tertiary", "residential", "service"]
    poi_types     = ["hospital", "school", "bus_stop", "none", "none", "none"]

    G_di = nx.DiGraph()
    for u, v in G_base.edges():
        length  = max(0.05, random.gauss(cfg["longueur_moy"], cfg["longueur_moy"] * 0.3))
        highway = random.choices(highway_types, weights=[0.10, 0.15, 0.20, 0.40, 0.15])[0]
        poi     = random.choices(poi_types, weights=[0.05, 0.10, 0.15, 0.35, 0.35, 0.00])[0]
        attrs = {
            "length"  : round(length, 3),
            "highway" : highway,
            "poi"     : poi,
            "weight"  : round(length, 3),
            "street"  : f"Rue {secteur[:3].upper()}-{u}-{v}",
        }
        G_di.add_edge(u, v, **attrs)
        G_di.add_edge(v, u, **attrs)

    if not nx.is_strongly_connected(G_di):
        main = max(nx.strongly_connected_components(G_di), key=len)
        G_di = G_di.subgraph(main).copy()

    return G_di


def get_graph(secteur: str, force_synthetic: bool = False) -> nx.DiGraph:
    if not force_synthetic:
        try:
            return get_real_graph(secteur)
        except Exception as e:
            print(f"  [OSMnx] Échec ({e}), bascule sur graphe synthétique.")
    return generate_sector_graph(secteur)


def apply_scenario_weights(G: nx.DiGraph, scenario: str) -> nx.DiGraph:
    type_factors = SCENARIO_WEIGHTS.get(scenario, SCENARIO_WEIGHTS["economique"])
    poi_factors  = POI_WEIGHTS.get(scenario, POI_WEIGHTS["economique"])
    G_w = G.copy()
    for u, v, data in G_w.edges(data=True):
        base    = data.get("length", 0.25)
        highway = data.get("highway", "residential")
        poi     = data.get("poi", "none")
        f_type  = type_factors.get(highway, 1.00)
        f_poi   = poi_factors.get(poi, 1.00)
        G_w[u][v]["weight"] = round(base * f_type * f_poi, 6)
    return G_w


def greedy_weighted_circuit(G, start_node=None) -> tuple[list, float]:
    if G.number_of_edges() == 0:
        return [], 0.0

    is_directed = G.is_directed()

    if start_node is None or start_node not in G:
        start_node = list(G.nodes())[0]

    unvisited = {}
    for u, v, data in G.edges(data=True):
        if is_directed:
            key = (u, v)
        else:
            key = (min(u, v), max(u, v))
        unvisited[key] = data.copy()

    route       = [start_node]
    distance_km = 0.0
    current     = start_node

    while unvisited:
        candidates = []
        for key, data in unvisited.items():
            if is_directed:
                u, v = key
                if u == current:
                    candidates.append((data.get("weight", 0.25), v, key, data))
            else:
                a, b = key
                if a == current:
                    candidates.append((data.get("weight", 0.25), b, key, data))
                elif b == current:
                    candidates.append((data.get("weight", 0.25), a, key, data))

        if candidates:
            candidates.sort(key=lambda x: x[0])
            _, neighbor, edge_key, data = candidates[0]
            route.append(neighbor)
            distance_km += data.get("length", 0.25)
            del unvisited[edge_key]
            current = neighbor
        else:
            reachable = set()
            for key in unvisited:
                if is_directed:
                    reachable.add(key[0])
                else:
                    reachable.add(key[0])
                    reachable.add(key[1])

            best_path = None
            best_cost = math.inf
            for target in reachable:
                try:
                    cost = nx.dijkstra_path_length(G, current, target, weight="weight")
                    if cost < best_cost:
                        best_cost = cost
                        best_path = nx.dijkstra_path(G, current, target, weight="weight")
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    pass

            if best_path and len(best_path) > 1:
                for node in best_path[1:]:
                    route.append(node)
                    if G.has_edge(current, node):
                        distance_km += G[current][node].get("length", 0.0)
                    current = node
            else:
                break

    return route, round(distance_km, 2)


def chinese_postman_route(G, start_node: int = 0) -> tuple[list, float]:
    return greedy_weighted_circuit(G, start_node)


def priority_route(G, scenario: str, start_node: int = 0) -> tuple[list, float]:
    G_w = apply_scenario_weights(G, scenario)
    return greedy_weighted_circuit(G_w, start_node)


def split_routes_multi_vehicle(G, n_vehicles: int, scenario: str) -> list:
    G_w = apply_scenario_weights(G, scenario)
    full_route, _ = greedy_weighted_circuit(G_w, list(G_w.nodes())[0])
    if not full_route:
        return []

    steps = []
    for a, b in zip(full_route[:-1], full_route[1:]):
        steps.append(G_w[a][b].get("length", 0.25) if G_w.has_edge(a, b) else 0.0)

    total   = sum(steps)
    target  = total / max(n_vehicles, 1)
    results = []
    current_route = [full_route[0]]
    current_dist  = 0.0
    vehicle_idx   = 0

    for i, step in enumerate(steps):
        current_dist += step
        current_route.append(full_route[i + 1])
        if current_dist >= target and vehicle_idx < n_vehicles - 1:
            cost_info = compute_cost(current_dist, 1)
            results.append({
                "vehicle_id" : vehicle_idx + 1,
                "route"      : current_route[:],
                "distance_km": round(current_dist, 2),
                **cost_info,
            })
            current_route = [full_route[i + 1]]
            current_dist  = 0.0
            vehicle_idx  += 1

    if current_route:
        cost_info = compute_cost(current_dist, 1)
        results.append({
            "vehicle_id" : vehicle_idx + 1,
            "route"      : current_route,
            "distance_km": round(current_dist, 2),
            **cost_info,
        })
    return results


def compute_indicators(G, routes: list, scenario: str) -> dict:
    total_dist   = sum(r["distance_km"] for r in routes)
    total_cost   = sum(r["cout_global"] for r in routes)
    total_time   = max((r["heures"] for r in routes), default=0)
    total_km_net = sum(d["length"] for _, _, d in G.edges(data=True))

    is_directed = G.is_directed()

    def edge_key(u, v):
        return (u, v) if is_directed else (min(u, v), max(u, v))

    all_edges     = set(edge_key(u, v) for u, v in G.edges())
    covered_edges = set()
    for r in routes:
        seq = r["route"]
        for a, b in zip(seq[:-1], seq[1:]):
            covered_edges.add(edge_key(a, b))
    coverage_pct = len(covered_edges & all_edges) / max(len(all_edges), 1) * 100

    priority_high = set(
        edge_key(u, v) for u, v, d in G.edges(data=True)
        if d.get("highway", "") in ("primary", "secondary", "trunk", "motorway")
    )
    priority_low = set(
        edge_key(u, v) for u, v, d in G.edges(data=True)
        if d.get("highway", "") in ("service", "living_street")
    )
    covered_early_high = set()
    covered_early_low  = set()
    for r in routes:
        seq  = r["route"]
        half = len(seq) // 2
        for a, b in zip(seq[:half], seq[1:half+1]):
            e = edge_key(a, b)
            if e in priority_high:
                covered_early_high.add(e)
            if e in priority_low:
                covered_early_low.add(e)

    pct_arteres = len(covered_early_high) / max(len(priority_high), 1) * 100
    pct_ruelles = len(covered_early_low)  / max(len(priority_low),  1) * 100

    return {
        "scenario"                        : scenario,
        "n_vehicules"                     : len(routes),
        "distance_totale_km"              : round(total_dist, 2),
        "cout_total_$"                    : round(total_cost, 2),
        "duree_max_h"                     : round(total_time, 2),
        "couverture_%"                    : round(coverage_pct, 1),
        "km_reseau"                       : round(total_km_net, 2),
        "ratio_cout_km"                   : round(total_cost / max(total_km_net, 1), 2),
        "arteres_couvertes_1ere_moitie_%" : round(pct_arteres, 1),
        "ruelles_couvertes_1ere_moitie_%" : round(pct_ruelles, 1),
        "delai_arteres_h"                 : round(total_time * (1 - pct_arteres / 100), 2),
        "delai_ruelles_h"                 : round(total_time * (1 - pct_ruelles / 100), 2),
    }


def compute_priority_delay(G, routes: list, scenario: str) -> dict:
    is_directed = G.is_directed()

    def edge_key(u, v):
        return (u, v) if is_directed else (min(u, v), max(u, v))

    priority_high = set(
        edge_key(u, v) for u, v, d in G.edges(data=True)
        if d.get("highway", "") in ("primary", "secondary", "trunk", "motorway")
    )
    priority_low = set(
        edge_key(u, v) for u, v, d in G.edges(data=True)
        if d.get("highway", "") in ("service", "living_street")
    )
    covered_early_high = set()
    covered_early_low  = set()
    for r in routes:
        seq  = r["route"]
        half = len(seq) // 2
        for a, b in zip(seq[:half], seq[1:half+1]):
            e = edge_key(a, b)
            if e in priority_high:
                covered_early_high.add(e)
            if e in priority_low:
                covered_early_low.add(e)

    return {
        "arteres_couvertes_1ere_moitie_%": round(len(covered_early_high) / max(len(priority_high), 1) * 100, 1),
        "ruelles_couvertes_1ere_moitie_%": round(len(covered_early_low)  / max(len(priority_low),  1) * 100, 1),
        "nb_arteres_total"               : len(priority_high),
        "nb_ruelles_total"               : len(priority_low),
    }

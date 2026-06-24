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
    "economique": {2: 1.0, 1: 1.0, 0: 1.0},
    "social":     {2: 0.5, 1: 1.0, 0: 1.8},
    "mixte":      {2: 0.7, 1: 1.0, 0: 1.3},
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


SECTEURS_CONFIG = {
    "Outremont": {
        "n_noeuds"    : 60,
        "densite"     : 0.06,
        "longueur_moy": 0.25,
        "description" : "Secteur résidentiel dense, rues en grille, faible circulation",
        "population"  : 24000,
        "km_routes"   : 45,
    },
    "Verdun": {
        "n_noeuds"    : 80,
        "densite"     : 0.05,
        "longueur_moy": 0.30,
        "description" : "Secteur mixte résidentiel/commercial, bord du fleuve",
        "population"  : 70000,
        "km_routes"   : 110,
    },
    "Anjou": {
        "n_noeuds"    : 70,
        "densite"     : 0.04,
        "longueur_moy": 0.40,
        "description" : "Secteur industriel et commercial, larges artères",
        "population"  : 42000,
        "km_routes"   : 85,
    },
    "RDP": {
        "n_noeuds"    : 100,
        "densite"     : 0.035,
        "longueur_moy": 0.50,
        "description" : "Rivière-des-Prairies-Pointe-aux-Trembles : secteur périphérique étendu",
        "population"  : 105000,
        "km_routes"   : 200,
    },
}


def generate_sector_graph(secteur: str, seed: int = 42) -> nx.Graph:
    cfg = SECTEURS_CONFIG[secteur]
    random.seed(seed)
    G = nx.erdos_renyi_graph(cfg["n_noeuds"], cfg["densite"], seed=seed)
    if not nx.is_connected(G):
        comps = list(nx.connected_components(G))
        for i in range(len(comps) - 1):
            u = list(comps[i])[0]
            v = list(comps[i + 1])[0]
            G.add_edge(u, v)
    for u, v in G.edges():
        length = max(0.05, random.gauss(cfg["longueur_moy"], cfg["longueur_moy"] * 0.3))
        prio   = random.choices([0, 1, 2], weights=[0.3, 0.5, 0.2])[0]
        G[u][v]["length"]   = round(length, 3)
        G[u][v]["priority"] = prio
        G[u][v]["weight"]   = round(length, 3)
        G[u][v]["street"]   = f"Rue {secteur[:3].upper()}-{u}-{v}"
    return G


def apply_scenario_weights(G: nx.Graph, scenario: str) -> nx.Graph:
    factors = SCENARIO_WEIGHTS.get(scenario, SCENARIO_WEIGHTS["economique"])
    G_w = G.copy()
    for u, v, data in G_w.edges(data=True):
        base = data.get("length", 0.25)
        prio = data.get("priority", 1)
        G_w[u][v]["weight"] = round(base * factors[prio], 6)
    return G_w


def greedy_weighted_circuit(G: nx.Graph, start_node=None) -> tuple[list, float]:
    """
    Parcours glouton pondéré : à chaque étape, choisit l'arête
    de poids le plus faible parmi les arêtes non encore visitées.
    Garantit que toutes les arêtes sont couvertes.
    Produit des circuits différents selon les poids → différencie les scénarios.
    """
    if G.number_of_edges() == 0:
        return [], 0.0

    if start_node is None or start_node not in G:
        start_node = list(G.nodes())[0]

    # Construire la liste des arêtes non visitées
    unvisited = {}
    for u, v, data in G.edges(data=True):
        key = (min(u, v), max(u, v))
        unvisited[key] = data.copy()

    route       = [start_node]
    distance_km = 0.0
    current     = start_node
    visited_set = set()

    while unvisited:
        # Trouver toutes les arêtes adjacentes non visitées
        candidates = []
        for (a, b), data in unvisited.items():
            if a == current or b == current:
                neighbor = b if a == current else a
                candidates.append((data.get("weight", 0.25), neighbor, (a, b), data))

        if candidates:
            # Choisir l'arête de poids le plus faible
            candidates.sort(key=lambda x: x[0])
            _, neighbor, edge_key, data = candidates[0]
            route.append(neighbor)
            distance_km += data.get("length", 0.25)
            del unvisited[edge_key]
            current = neighbor
        else:
            # Plus d'arêtes adjacentes directes → trouver le chemin
            # vers le nœud le plus proche ayant des arêtes non visitées
            reachable_nodes = set()
            for (a, b) in unvisited:
                reachable_nodes.add(a)
                reachable_nodes.add(b)

            best_path = None
            best_cost = math.inf
            for target in reachable_nodes:
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
                        distance_km += G[current][node].get("length", 0.25)
                    current = node
            else:
                break

    return route, round(distance_km, 2)


def chinese_postman_route(G: nx.Graph, start_node: int = 0) -> tuple[list, float]:
    """Utilise le parcours glouton pondéré pour différencier les scénarios."""
    return greedy_weighted_circuit(G, start_node)


def priority_route(G: nx.Graph, scenario: str, start_node: int = 0) -> tuple[list, float]:
    G_w = apply_scenario_weights(G, scenario)
    return greedy_weighted_circuit(G_w, start_node)


def split_routes_multi_vehicle(G: nx.Graph, n_vehicles: int, scenario: str) -> list[dict]:
    G_w = apply_scenario_weights(G, scenario)
    full_route, _ = greedy_weighted_circuit(G_w, list(G_w.nodes())[0])

    if not full_route:
        return []

    steps = []
    for a, b in zip(full_route[:-1], full_route[1:]):
        steps.append(G_w[a][b].get("length", 0.25) if G_w.has_edge(a, b) else 0.0)

    total  = sum(steps)
    target = total / max(n_vehicles, 1)
    results       = []
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


def compute_indicators(G: nx.Graph, routes: list[dict], scenario: str) -> dict:
    total_dist   = sum(r["distance_km"] for r in routes)
    total_cost   = sum(r["cout_global"] for r in routes)
    total_time   = max((r["heures"] for r in routes), default=0)
    total_km_net = sum(d["length"] for _, _, d in G.edges(data=True))

    all_edges     = set((min(u, v), max(u, v)) for u, v in G.edges())
    covered_edges = set()
    for r in routes:
        route_seq = r["route"]
        for a, b in zip(route_seq, route_seq[1:]):
            covered_edges.add((min(a, b), max(a, b)))

    coverage_pct = len(covered_edges & all_edges) / max(len(all_edges), 1) * 100

    priority2 = set((min(u,v), max(u,v)) for u,v,d in G.edges(data=True) if d.get("priority",0)==2)
    priority0 = set((min(u,v), max(u,v)) for u,v,d in G.edges(data=True) if d.get("priority",0)==0)
    covered_early_p2 = set()
    covered_early_p0 = set()
    for r in routes:
        seq  = r["route"]
        half = len(seq) // 2
        for a, b in zip(seq[:half], seq[1:half+1]):
            e = (min(a,b), max(a,b))
            if e in priority2:
                covered_early_p2.add(e)
            if e in priority0:
                covered_early_p0.add(e)

    pct_arteres = len(covered_early_p2) / max(len(priority2), 1) * 100
    pct_ruelles = len(covered_early_p0) / max(len(priority0), 1) * 100

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
    }


def compute_priority_delay(G: nx.Graph, routes: list[dict], scenario: str) -> dict:
    priority2 = set((min(u,v), max(u,v)) for u,v,d in G.edges(data=True) if d.get("priority",0)==2)
    priority0 = set((min(u,v), max(u,v)) for u,v,d in G.edges(data=True) if d.get("priority",0)==0)
    covered_early_p2 = set()
    covered_early_p0 = set()
    for r in routes:
        seq  = r["route"]
        half = len(seq) // 2
        for a, b in zip(seq[:half], seq[1:half+1]):
            e = (min(a,b), max(a,b))
            if e in priority2:
                covered_early_p2.add(e)
            if e in priority0:
                covered_early_p0.add(e)
    return {
        "arteres_couvertes_1ere_moitie_%": round(len(covered_early_p2)/max(len(priority2),1)*100, 1),
        "ruelles_couvertes_1ere_moitie_%": round(len(covered_early_p0)/max(len(priority0),1)*100, 1),
        "nb_arteres_total"               : len(priority2),
        "nb_ruelles_total"               : len(priority0),
    }

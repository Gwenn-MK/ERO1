"""
graph_utils.py
Module de modélisation du réseau routier et d'algorithmes de parcours pour le déneigement.

Auteurs: L.Blet & H.Paris (EPITA)
"""

import networkx as nx
import random
import math
from collections import defaultdict

# ─────────────────────────────────────────────
# Données de coût (section 4 de l'énoncé)
# ─────────────────────────────────────────────
COUT_FIXE_JOUR = 500.0          # $/jour/véhicule
COUT_KM        = 1.1             # $/km
COUT_H_NORMAL  = 1.1             # $/h (8 premières heures)
COUT_H_SUP     = 1.3             # $/h (au-delà de 8h)
VITESSE_KMH    = 10.0            # km/h (vitesse moyenne déneigeuse)
SEUIL_H_SUP    = 8.0             # heures avant surcoût


def compute_cost(distance_km: float, n_vehicles: int) -> dict:
    """
    Calcule le coût total d'une opération de déblaiement.

    Args:
        distance_km: Distance totale parcourue par un véhicule (km)
        n_vehicles:  Nombre de véhicules déployés

    Returns:
        dict avec coût fixe, kilométrique, horaire et total par véhicule et global.
    """
    heures = distance_km / VITESSE_KMH

    cout_km   = distance_km * COUT_KM
    if heures <= SEUIL_H_SUP:
        cout_h = heures * COUT_H_NORMAL
    else:
        cout_h = SEUIL_H_SUP * COUT_H_NORMAL + (heures - SEUIL_H_SUP) * COUT_H_SUP

    cout_total_vehicule = COUT_FIXE_JOUR + cout_km + cout_h
    cout_global         = cout_total_vehicule * n_vehicles

    return {
        "distance_km"          : round(distance_km, 2),
        "heures"               : round(heures, 2),
        "cout_fixe"            : COUT_FIXE_JOUR,
        "cout_km"              : round(cout_km, 2),
        "cout_horaire"         : round(cout_h, 2),
        "cout_total_vehicule"  : round(cout_total_vehicule, 2),
        "n_vehicles"           : n_vehicles,
        "cout_global"          : round(cout_global, 2),
    }


# ─────────────────────────────────────────────
# Génération de graphes synthétiques par secteur
# ─────────────────────────────────────────────

SECTEURS_CONFIG = {
    "Outremont": {
        "n_noeuds"      : 60,
        "densite"       : 0.06,
        "longueur_moy"  : 0.25,   # km
        "description"   : "Secteur résidentiel dense, rues en grille, faible circulation",
        "population"    : 24000,
        "km_routes"     : 45,
    },
    "Verdun": {
        "n_noeuds"      : 80,
        "densite"       : 0.05,
        "longueur_moy"  : 0.30,
        "description"   : "Secteur mixte résidentiel/commercial, bord du fleuve",
        "population"    : 70000,
        "km_routes"     : 110,
    },
    "Anjou": {
        "n_noeuds"      : 70,
        "densite"       : 0.04,
        "longueur_moy"  : 0.40,
        "description"   : "Secteur industriel et commercial, larges artères",
        "population"    : 42000,
        "km_routes"     : 85,
    },
    "RDP": {
        "n_noeuds"      : 100,
        "densite"       : 0.035,
        "longueur_moy"  : 0.50,
        "description"   : "Rivière-des-Prairies-Pointe-aux-Trembles : secteur périphérique étendu",
        "population"    : 105000,
        "km_routes"     : 200,
    },
}


def generate_sector_graph(secteur: str, seed: int = 42) -> nx.Graph:
    """
    Génère un graphe non orienté représentant le réseau routier d'un secteur.

    Chaque arête possède :
      - 'length'    : longueur en km
      - 'road_type' : type de voie parmi :
            'commercial'   → axes commerciaux, flux logistiques, zones d'activité
            'résidentiel'  → rues résidentielles, écoles, arrêts de bus
            'urgence'      → axes d'urgence : hôpitaux, pompiers, CIUSSS
            'secondaire'   → rues secondaires sans vocation particulière
      - 'priority'  : entier dérivé du road_type (rétrocompatibilité)
            commercial  → 2
            urgence     → 2
            résidentiel → 1
            secondaire  → 0
      - 'street'    : nom de rue synthétique

    La distribution des types varie selon la vocation du secteur :
      Outremont → majoritairement résidentiel
      Verdun    → mix résidentiel / commercial
      Anjou     → majoritairement commercial (zone industrielle/logistique)
      RDP       → mix résidentiel / secondaire, peu d'urgence
    """
    # Distribution road_type par secteur :
    # [commercial, résidentiel, urgence, secondaire]
    ROAD_TYPE_WEIGHTS = {
        "Outremont": [0.10, 0.55, 0.10, 0.25],
        "Verdun"   : [0.30, 0.35, 0.10, 0.25],
        "Anjou"    : [0.50, 0.15, 0.05, 0.30],
        "RDP"      : [0.20, 0.40, 0.08, 0.32],
    }
    ROAD_TYPES = ["commercial", "résidentiel", "urgence", "secondaire"]
    PRIORITY_MAP = {
        "commercial" : 2,
        "urgence"    : 2,
        "résidentiel": 1,
        "secondaire" : 0,
    }

    cfg     = SECTEURS_CONFIG[secteur]
    weights = ROAD_TYPE_WEIGHTS.get(secteur, [0.25, 0.35, 0.10, 0.30])

    random.seed(seed)

    G = nx.erdos_renyi_graph(cfg["n_noeuds"], cfg["densite"], seed=seed)
    # Assurer la connexité
    if not nx.is_connected(G):
        comps = list(nx.connected_components(G))
        for i in range(len(comps) - 1):
            u = list(comps[i])[0]
            v = list(comps[i + 1])[0]
            G.add_edge(u, v)

    # Ajouter attributs aux arêtes
    for u, v in G.edges():
        length    = max(0.05, random.gauss(cfg["longueur_moy"], cfg["longueur_moy"] * 0.3))
        road_type = random.choices(ROAD_TYPES, weights=weights)[0]
        G[u][v]["length"]    = round(length, 3)
        G[u][v]["road_type"] = road_type
        G[u][v]["priority"]  = PRIORITY_MAP[road_type]   # rétrocompatibilité
        G[u][v]["street"]    = f"Rue {secteur[:3].upper()}-{u}-{v}"

    return G


# ─────────────────────────────────────────────
# Algorithmes de parcours (Route Inspection / CPP)
# ─────────────────────────────────────────────

def chinese_postman_route(G: nx.Graph, start_node: int = 0, weight: str = "length") -> tuple[list, float]:
    """
    Implémentation simplifiée du Problème du Postier Chinois (Chinese Postman Problem).
    Trouve un circuit eulérien après avoir rendu le graphe eulérien (tous les degrés pairs).

    Args:
        G:          Graphe NetworkX (non orienté).
        start_node: Nœud de départ du circuit.
        weight:     Attribut d'arête utilisé comme poids pour le matching et Dijkstra.
                    Utiliser "weight" pour les scénarios social/mixte (poids pondérés),
                    "length" pour le scénario économique (distance brute).

    Retourne:
        (route, distance_totale_km)
    """
    # Trouver les noeuds de degré impair
    odd_nodes = [v for v, d in G.degree() if d % 2 == 1]

    # Ajouter des arêtes de poids minimal entre paires de noeuds impairs (matching parfait approché)
    G_euler = G.copy()
    if odd_nodes:
        # Matching glouton sur le poids du scénario courant
        matched = set()
        pairs   = []
        for i, u in enumerate(odd_nodes):
            if u in matched:
                continue
            best_v, best_w = None, math.inf
            for v in odd_nodes:
                if v == u or v in matched:
                    continue
                try:
                    sp = nx.dijkstra_path_length(G, u, v, weight=weight)
                    if sp < best_w:
                        best_w, best_v = sp, v
                except nx.NetworkXNoPath:
                    pass
            if best_v is not None:
                matched.add(u)
                matched.add(best_v)
                pairs.append((u, best_v, best_w))

        # Dupliquer les chemins les plus courts entre chaque paire
        for u, v, _ in pairs:
            try:
                path = nx.dijkstra_path(G, u, v, weight=weight)
                for a, b in zip(path, path[1:]):
                    edge_len = G[a][b]["length"]
                    if G_euler.has_edge(a, b):
                        G_euler[a][b]["length"] += edge_len  # doublon
                    else:
                        G_euler.add_edge(a, b, length=edge_len, priority=0, street="(transfert)")
            except nx.NetworkXNoPath:
                pass

    # Circuit eulérien
    if start_node not in G_euler:
        start_node = list(G_euler.nodes())[0]

    try:
        circuit = list(nx.eulerian_circuit(G_euler, source=start_node))
    except nx.NetworkXError:
        # Fallback : DFS simple
        circuit = list(nx.dfs_edges(G_euler, source=start_node))

    route       = [u for u, v in circuit] + [circuit[-1][1]] if circuit else []
    distance_km = sum(
        G_euler[u][v].get("length", 0.25)
        for u, v in circuit
    )
    return route, round(distance_km, 2)


def priority_route(G: nx.Graph, scenario: str, start_node: int = 0) -> tuple[list, float]:
    """
    Planifie un itinéraire selon le scénario choisi en pondérant les arêtes
    par leur attribut 'road_type'.

    Scénarios :
      'economique' → priorise les axes commerciaux (ouvrir les commerces,
                     flux logistiques, maintien de l'activité économique).
                     urgence/secondaire traités après.
      'social'     → priorise les axes d'urgence (hôpitaux, pompiers) puis
                     les zones résidentielles (écoles, arrêts de bus).
                     commercial traité en dernier.
      'mixte'      → compromis : urgence en premier, puis commercial et
                     résidentiel à égalité, secondaire en dernier.

    Un facteur < 1 rend l'arête "attractive" (traitée en priorité) ;
    un facteur > 1 la rend moins attractive (repoussée en fin de tournée).

    Retourne (route, distance_km).
    """
    # Facteurs de pondération par (scénario, road_type)
    FACTORS = {
        "economique": {
            "commercial" : 0.4,   # priorité maximale
            "résidentiel": 1.2,
            "urgence"    : 1.0,   # traité normalement
            "secondaire" : 1.8,   # repoussé en fin
        },
        "social": {
            "urgence"    : 0.3,   # priorité absolue
            "résidentiel": 0.6,   # priorité élevée
            "secondaire" : 1.2,
            "commercial" : 1.8,   # traité en dernier
        },
        "mixte": {
            "urgence"    : 0.4,   # toujours en premier
            "commercial" : 0.7,
            "résidentiel": 0.7,
            "secondaire" : 1.5,
        },
    }

    factors = FACTORS[scenario]
    G_w = G.copy()
    for u, v, data in G_w.edges(data=True):
        base      = data.get("length", 0.25)
        road_type = data.get("road_type", "secondaire")
        G_w[u][v]["weight"] = base * factors.get(road_type, 1.0)

    route, dist = chinese_postman_route(G_w, start_node, weight="weight")
    return route, dist


def split_routes_multi_vehicle(G: nx.Graph, n_vehicles: int, scenario: str) -> list[dict]:
    """
    Partitionne le graphe en sous-graphes pour affecter un véhicule par zone.
    La partition se fait par arêtes triées selon le scénario, de façon à ce que
    chaque véhicule couvre une portion cohérente du réseau.

    Retourne une liste de dicts {vehicle_id, route, distance_km, cost}.
    """
    # Ordre de priorité de traitement par scénario
    TYPE_ORDER = {
        "economique": ["commercial", "urgence", "résidentiel", "secondaire"],
        "social"    : ["urgence", "résidentiel", "commercial", "secondaire"],
        "mixte"     : ["urgence", "commercial", "résidentiel", "secondaire"],
    }
    order = TYPE_ORDER.get(scenario, ["commercial", "résidentiel", "urgence", "secondaire"])
    rank  = {rt: i for i, rt in enumerate(order)}

    edges = list(G.edges(data=True))
    edges.sort(key=lambda e: (rank.get(e[2].get("road_type", "secondaire"), 99),
                               e[2].get("length", 0)))

    # Répartir les arêtes en n_vehicles chunks
    chunk_size = max(1, len(edges) // n_vehicles)
    results    = []

    all_covered_edges = set()

    for i in range(n_vehicles):
        chunk = edges[i * chunk_size: (i + 1) * chunk_size]
        if not chunk:
            continue

        # Construire un sous-graphe à partir de ces arêtes
        subG = nx.Graph()
        for u, v, data in chunk:
            subG.add_edge(u, v, **data)

        if not nx.is_connected(subG):
            largest = max(nx.connected_components(subG), key=len)
            subG    = subG.subgraph(largest).copy()

        if len(subG.nodes()) < 2:
            continue

        route, dist = priority_route(subG, scenario, list(subG.nodes())[0])
        cost_info   = compute_cost(dist, 1)

        # Enregistrer les arêtes couvertes
        for a, b in zip(route, route[1:]):
            all_covered_edges.add((min(a, b), max(a, b)))

        results.append({
            "vehicle_id"    : i + 1,
            "route"         : route,
            "distance_km"   : dist,
            "covered_edges" : list(all_covered_edges),
            **cost_info,
        })

    return results


# ─────────────────────────────────────────────
# Indicateurs d'évaluation
# ─────────────────────────────────────────────

def compute_indicators(G: nx.Graph, routes: list[dict], scenario: str) -> dict:
    """Calcule les indicateurs clés pour un scénario donné."""
    total_dist   = sum(r["distance_km"] for r in routes)
    total_cost   = sum(r["cout_global"] for r in routes)
    total_time   = max((r["heures"] for r in routes), default=0)
    n_edges      = G.number_of_edges()
    total_km_net = sum(d["length"] for _, _, d in G.edges(data=True))

    # Couverture globale : agréger toutes les arêtes visitées par tous les véhicules
    covered_edges = set()
    for r in routes:
        route_seq = r["route"]
        for a, b in zip(route_seq, route_seq[1:]):
            covered_edges.add((min(a, b), max(a, b)))
        if "covered_edges" in r:
            for edge in r["covered_edges"]:
                covered_edges.add(tuple(edge))

    coverage_pct = len(covered_edges) / max(n_edges, 1) * 100

    # Couverture par type de voie
    type_edges   = {"commercial": set(), "résidentiel": set(),
                    "urgence": set(), "secondaire": set()}
    for u, v, d in G.edges(data=True):
        rt = d.get("road_type", "secondaire")
        type_edges[rt].add((min(u, v), max(u, v)))

    coverage_by_type = {}
    for rt, edge_set in type_edges.items():
        if edge_set:
            covered = len(edge_set & covered_edges)
            coverage_by_type[f"couverture_{rt}_%"] = round(covered / len(edge_set) * 100, 1)
        else:
            coverage_by_type[f"couverture_{rt}_%"] = 0.0

    return {
        "scenario"              : scenario,
        "n_vehicules"           : len(routes),
        "distance_totale_km"    : round(total_dist, 2),
        "cout_total_$"          : round(total_cost, 2),
        "duree_max_h"           : round(total_time, 2),
        "couverture_%"          : round(coverage_pct, 1),
        "km_reseau"             : round(total_km_net, 2),
        "ratio_cout_km"         : round(total_cost / max(total_km_net, 1), 2),
        **coverage_by_type,
    }

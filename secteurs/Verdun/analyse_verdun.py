"""
analyse_verdun.py
Auteurs: Meku · Akanni · Bensammar · Hookoom — ÉPITA
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import json
from scripts.graph_utils import get_graph, split_routes_multi_vehicle, compute_indicators
from scripts.visualizer  import plot_routes

SECTEUR    = "Verdun"
N_VEHICLES = 3
SCENARIOS  = ["economique", "social", "mixte"]
OUT_DIR    = os.path.dirname(os.path.abspath(__file__))

def main():
    G = get_graph(SECTEUR)
    print(f"\n=== Secteur {SECTEUR} ===")
    print(f"Nœuds : {G.number_of_nodes()} | Arêtes : {G.number_of_edges()}")
    for sc in SCENARIOS:
        routes = split_routes_multi_vehicle(G, N_VEHICLES, sc)
        indic  = compute_indicators(G, routes, sc)
        print(f"\n--- Scénario : {sc.upper()} ---")
        print(f"  Coût total       : ${indic['cout_total_$']:,.2f}")
        print(f"  Distance totale  : {indic['distance_totale_km']} km")
        print(f"  Couverture       : {indic['couverture_%']} %")
        print(f"  Durée max (h)    : {indic['duree_max_h']}")
        print(f"  Artères 1ère m.  : {indic['arteres_couvertes_1ere_moitie_%']} %")
        with open(os.path.join(OUT_DIR, f"itineraire_{sc}.json"), "w") as f:
            json.dump({"secteur": SECTEUR, "scenario": sc,
                       "indicateurs": indic,
                       "routes": [{"vehicle_id": r["vehicle_id"],
                                   "distance_km": r["distance_km"],
                                   "cout_global": r["cout_global"],
                                   "n_noeuds": len(r["route"])} for r in routes]
                       }, f, ensure_ascii=False, indent=2)
        print(f"  → JSON : itineraire_{sc}.json")
        plot_routes(G, [r["route"] for r in routes], SECTEUR, sc,
                    os.path.join(OUT_DIR, f"carte_{sc}.png"))

if __name__ == "__main__":
    main()

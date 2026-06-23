#!/usr/bin/env python3
"""
Analyse du secteur Outremont — Génération de l'itinéraire et des indicateurs.
Auteurs: L.Blet & H.Paris (EPITA)
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from scripts.graph_utils import generate_sector_graph, split_routes_multi_vehicle, compute_indicators
import json

SECTEUR    = "Outremont"
N_VEHICLES = 4   # 4 véhicules pour ce secteur résidentiel dense

def main():
    G = generate_sector_graph(SECTEUR)
    print(f"=== Secteur {SECTEUR} ===")
    print(f"Nœuds : {G.number_of_nodes()} | Arêtes : {G.number_of_edges()}")

    for scenario in ["economique", "social", "mixte"]:
        routes = split_routes_multi_vehicle(G, N_VEHICLES, scenario)
        indic  = compute_indicators(G, routes, scenario)
        print(f"\n--- Scénario : {scenario.upper()} ---")
        print(f"  Coût total       : ${indic['cout_total_$']:,.2f}")
        print(f"  Distance totale  : {indic['distance_totale_km']} km")
        print(f"  Couverture       : {indic['couverture_%']} %")
        print(f"  Durée max (h)    : {indic['duree_max_h']}")

        # Sauvegarder les itinéraires
        out = {"secteur": SECTEUR, "scenario": scenario, "indicateurs": indic,
               "routes": [{"vehicle_id": r["vehicle_id"], "distance_km": r["distance_km"],
                            "heures": r["heures"], "cout_global": r["cout_global"],
                            "route_apercu": r["route"][:10]} for r in routes]}
        fname = f"itineraire_{scenario}.json"
        with open(os.path.join(os.path.dirname(__file__), fname), "w") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print(f"  → Sauvegardé : {fname}")

if __name__ == "__main__":
    main()

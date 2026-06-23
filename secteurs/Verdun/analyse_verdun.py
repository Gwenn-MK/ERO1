#!/usr/bin/env python3
"""Analyse du secteur Verdun — Auteurs: L.Blet & H.Paris (EPITA)"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from scripts.graph_utils import generate_sector_graph, split_routes_multi_vehicle, compute_indicators

SECTEUR = "Verdun"
N_VEHICLES = 5

def main():
    G = generate_sector_graph(SECTEUR)
    print(f"=== Secteur {SECTEUR} === Noeuds: {G.number_of_nodes()} | Aretes: {G.number_of_edges()}")
    for scenario in ["economique", "social", "mixte"]:
        routes = split_routes_multi_vehicle(G, N_VEHICLES, scenario)
        indic  = compute_indicators(G, routes, scenario)
        print(f"--- {scenario.upper()} --- Cout: ${indic['cout_total_$']:,.2f} | Dist: {indic['distance_totale_km']} km")
        out = {"secteur": SECTEUR, "scenario": scenario, "indicateurs": indic}
        with open(os.path.join(os.path.dirname(__file__), f"itineraire_{scenario}.json"), "w") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()

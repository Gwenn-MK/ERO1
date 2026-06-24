#!/usr/bin/env python3
"""
demo.py
Script de démonstration de la solution d'optimisation des déneigeuses — Montréal.

Usage:
    python demo.py [--secteur SECTEUR] [--scenario SCENARIO] [--vehicules N]

Auteurs: L.Blet & H.Paris (EPITA)
"""

import argparse
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scripts.graph_utils import (
    SECTEURS_CONFIG,
    generate_sector_graph,
    priority_route,
    split_routes_multi_vehicle,
    compute_indicators,
    compute_cost,
)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers d'affichage
# ─────────────────────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BLUE   = "\033[94m"
WHITE  = "\033[97m"

def banner():
    print(f"""
{CYAN}{BOLD}╔══════════════════════════════════════════════════════════════╗
║        OPTIMISATION HIVERNALE — DÉNEIGEMENT MONTRÉAL         ║
║                     ÉPITA — L.Blet & H.Paris                 ║
╚══════════════════════════════════════════════════════════════╝{RESET}
""")

def section(title: str):
    print(f"\n{BLUE}{BOLD}{'─'*62}{RESET}")
    print(f"{BOLD}{WHITE}  {title}{RESET}")
    print(f"{BLUE}{'─'*62}{RESET}")

def kv(key: str, val, unit: str = ""):
    print(f"  {CYAN}{key:<30}{RESET} {YELLOW}{val}{RESET} {unit}")

def success(msg: str):
    print(f"  {GREEN}✔  {msg}{RESET}")

def warn(msg: str):
    print(f"  {YELLOW}⚠  {msg}{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# Démonstration par secteur / scénario
# ─────────────────────────────────────────────────────────────────────────────

SCENARIOS = {
    "economique": {
        "label"      : "Économique",
        "description": "Priorise les axes commerciaux et zones logistiques pour permettre "
                       "l'ouverture rapide des commerces et le maintien de l'activité économique "
                       "en hiver. Les axes d'urgence sont traités normalement ; "
                       "les rues résidentielles et secondaires en dernier.",
        "objectif"   : "Ouvrir les axes commerciaux et réduire les délais logistiques.",
        "cible"      : "Commerçants, livreurs, zones industrielles (ex. Anjou).",
        "risque"     : "Zones résidentielles et écoles déneigées en dernier.",
        "color"      : GREEN,
    },
    "social": {
        "label"      : "Social",
        "description": "Priorise d'abord les axes d'urgence (hôpitaux, pompiers, CIUSSS), "
                       "puis les zones résidentielles (écoles, arrêts de bus, rues de quartier). "
                       "Les axes commerciaux sont traités en dernier.",
        "objectif"   : "Garantir la sécurité des Montréalais et l'accès aux services d'urgence.",
        "cible"      : "Résidents, services d'urgence, usagers des transports en commun.",
        "risque"     : "Surcoût horaire si les déneigeuses dépassent 8h ; commerces ouverts tardivement.",
        "color"      : CYAN,
    },
    "mixte": {
        "label"      : "Mixte",
        "description": "Compromis équilibré : axes d'urgence en premier, puis axes commerciaux "
                       "et résidentiels à égalité, secondaires en dernier. "
                       "Optimise le service global sans sacrifier ni l'économie ni la sécurité.",
        "objectif"   : "Compromis coût/service optimal pour la ville.",
        "cible"      : "Municipalité + citoyens + commerçants.",
        "risque"     : "Moins optimal que chaque scénario pur sur son critère propre.",
        "color"      : YELLOW,
    },
}


def run_secteur(secteur: str, scenario: str, n_vehicles: int, verbose: bool = True) -> dict:
    """Lance l'optimisation pour un secteur et un scénario donnés."""
    cfg = SECTEURS_CONFIG[secteur]
    G   = generate_sector_graph(secteur)

    if verbose:
        section(f"SECTEUR : {secteur}")
        kv("Description"    , cfg["description"])
        kv("Population"     , f"{cfg['population']:,}", "habitants")
        kv("Réseau routier" , cfg["km_routes"], "km")
        kv("Nœuds (carref.)", G.number_of_nodes())
        kv("Arêtes (rues)"  , G.number_of_edges())
        kv("Scénario"       , SCENARIOS[scenario]["label"])
        kv("Véhicules"      , n_vehicles)

    routes = split_routes_multi_vehicle(G, n_vehicles, scenario)
    indic  = compute_indicators(G, routes, scenario)

    if verbose:
        print()
        for r in routes:
            apercu = " → ".join(str(n) for n in r["route"][:6])
            if len(r["route"]) > 6:
                apercu += " → ..."
            success(f"Véhicule {r['vehicle_id']} | {r['distance_km']} km | "
                    f"{r['heures']} h | {r['cout_global']} $/jour | Route: {apercu}")

        print()
        kv("Distance totale"     , indic["distance_totale_km"], "km")
        kv("Coût total"          , f"${indic['cout_total_$']:,.2f}")
        kv("Durée max (1 véh.)"  , indic["duree_max_h"], "h")
        kv("Couverture réseau"   , f"{indic['couverture_%']} %")
        kv("Ratio coût/km réseau", f"${indic['ratio_cout_km']}", "/km")

    return {
        "secteur"  : secteur,
        "scenario" : scenario,
        "routes"   : routes,
        "indicateurs": indic,
    }


def comparaison_scenarios(secteur: str, n_vehicles: int):
    """Compare les 3 scénarios sur un secteur donné."""
    section(f"COMPARAISON DES 3 SCÉNARIOS — {secteur}")
    results = {}
    for sc in ["economique", "social", "mixte"]:
        r = run_secteur(secteur, sc, n_vehicles, verbose=False)
        results[sc] = r
        ind = r["indicateurs"]
        sc_info = SCENARIOS[sc]
        col = sc_info["color"]
        print(f"\n  {col}{BOLD}[{sc_info['label'].upper()}]{RESET}")
        kv("  Coût total"         , f"${ind['cout_total_$']:,.2f}")
        kv("  Distance totale"    , f"{ind['distance_totale_km']} km")
        kv("  Couverture réseau"  , f"{ind['couverture_%']} %")
        kv("  Durée max / véhicule", f"{ind['duree_max_h']} h")
        kv("  Objectif"           , sc_info["objectif"])
        kv("  Risque principal"   , sc_info["risque"])

    # Recommandation
    couts = {sc: results[sc]["indicateurs"]["cout_total_$"] for sc in results}
    best_cost = min(couts, key=couts.get)
    print(f"\n  {GREEN}{BOLD}→ Scénario le moins coûteux : {SCENARIOS[best_cost]['label']} "
          f"(${couts[best_cost]:,.2f}){RESET}")
    print(f"  {CYAN}→ Pour la sécurité des citoyens : Scénario Social recommandé.{RESET}")
    print(f"  {YELLOW}→ Recommandation générale : Scénario Mixte (équilibre optimal).{RESET}")

    return results


def modele_cout_global(n_vehicles_list: list[int], km_par_vehicule: float = 50.0):
    """Affiche le modèle de coût en fonction du nombre de véhicules."""
    section("MODÈLE DE COÛT GLOBAL — ENSEMBLE DE LA VILLE")
    print(f"  Hypothèse : {km_par_vehicule} km/véhicule/jour (moyenne Montréal)\n")

    print(f"  {'Véhicules':>10} | {'Coût total ($)':>16} | {'Durée (h)':>10} | {'Remarque'}")
    print(f"  {'-'*70}")
    for n in n_vehicles_list:
        c = compute_cost(km_par_vehicule, n)
        duree = c["heures"]
        rem   = "⚠ Heures sup." if duree > 8 else "✔ Dans les 8h"
        print(f"  {n:>10} | {c['cout_global']:>16,.2f} | {duree:>10.1f} | {rem}")


# ─────────────────────────────────────────────────────────────────────────────
# Entrée principale
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Démonstration optimisation déneigement Montréal"
    )
    parser.add_argument("--secteur" , default="ALL",
                        choices=list(SECTEURS_CONFIG.keys()) + ["ALL"],
                        help="Secteur à étudier (défaut: ALL)")
    parser.add_argument("--scenario", default="ALL",
                        choices=["economique", "social", "mixte", "ALL"],
                        help="Scénario de priorisation (défaut: ALL)")
    parser.add_argument("--vehicules", type=int, default=3,
                        help="Nombre de véhicules par secteur (défaut: 3)")
    parser.add_argument("--export-json", action="store_true",
                        help="Exporter les résultats en JSON")
    args = parser.parse_args()

    banner()

    secteurs = list(SECTEURS_CONFIG.keys()) if args.secteur == "ALL" else [args.secteur]
    all_results = {}

    for secteur in secteurs:
        if args.scenario == "ALL":
            res = comparaison_scenarios(secteur, args.vehicules)
        else:
            res = run_secteur(secteur, args.scenario, args.vehicules)
        all_results[secteur] = res

    # Modèle de coût global
    modele_cout_global([5, 10, 20, 50, 100, 200, 500, 2000])

    # Projection ville entière
    section("PROJECTION VILLE ENTIÈRE — MONTRÉAL (10 000 km de routes)")
    km_total   = 10_000
    vitesse    = 10.0
    km_par_veh = 50.0
    n_veh_req  = math.ceil(km_total / km_par_veh)
    c_global   = compute_cost(km_par_veh, n_veh_req)
    kv("Véhicules nécessaires (estimation)"  , n_veh_req)
    kv("Coût estimé journalier"              , f"${c_global['cout_global']:,.0f}")
    kv("Comparaison budget annuel (200 M$)"  , f"~{round(c_global['cout_global'] * 150 / 1e6, 1)} M$ / saison (150 jours)")
    warn("Estimation basée sur 50 km/véhicule — à ajuster selon la réalité du terrain.")

    if args.export_json:
        out_path = "resultats_deneigement.json"
        # Simplify for JSON serialization
        export = {}
        for s, data in all_results.items():
            if isinstance(data, dict) and "indicateurs" in data:
                export[s] = data["indicateurs"]
            else:
                export[s] = {sc: v["indicateurs"] for sc, v in data.items() if isinstance(v, dict)}
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(export, f, ensure_ascii=False, indent=2)
        success(f"Résultats exportés → {out_path}")

    section("FIN DE LA DÉMONSTRATION")
    print(f"  {GREEN}Tous les secteurs ont été traités avec succès.{RESET}")
    print(f"  {CYAN}Pour un secteur spécifique : python demo.py --secteur Verdun --scenario social{RESET}\n")


import math
if __name__ == "__main__":
    main()

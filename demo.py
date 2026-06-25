#!/usr/bin/env python3
"""
demo.py
Script de démonstration de la solution d'optimisation des déneigeuses — Montréal.

Usage:
    python demo.py [--secteur SECTEUR] [--scenario SCENARIO] [--vehicules N]

Auteurs: Meku · Akanni · Bensammar · Hookoom — ÉPITA
"""

import argparse
import math
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scripts.graph_utils import (
    get_graph,
    SECTEURS_CONFIG,
    split_routes_multi_vehicle,
    compute_indicators,
    compute_cost,
    compute_priority_delay,
)

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
║              Meku · Akanni · Bensammar · Hookoom              ║
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


SCENARIOS = {
    "economique": {
        "label"      : "Économique",
        "description": "Minimise la distance totale parcourue. Réduit les coûts opérationnels "
                       "au maximum. Aucune priorisation par type de voie.",
        "objectif"   : "Réduire le coût journalier de déneigement.",
        "cible"      : "Municipalité / budget.",
        "risque"     : "Axes commerciaux et écoles traités en dernier.",
        "projection" : [
            "→ Les artères STM et axes commerciaux sont dégagés selon la distance optimale.",
            "→ Les livreurs et travailleurs bénéficient d'un réseau opérationnel rapidement.",
            "⚠ RISQUE : les quartiers résidentiels éloignés peuvent attendre jusqu'à 2x plus.",
            "✔ IMPACT : réduction estimée des pertes économiques liées au blocage hivernal.",
        ],
        "color"      : GREEN,
    },
    "social": {
        "label"      : "Social",
        "description": "Priorise les artères principales, hôpitaux, écoles et arrêts de bus. "
                       "Le coût peut être plus élevé mais l'impact citoyen est maximal.",
        "objectif"   : "Garantir la sécurité des Montréalais en < 4h sur les axes critiques.",
        "cible"      : "Citoyens, services d'urgence, usagers des transports.",
        "risque"     : "Surcoût horaire si les déneigeuses dépassent 8h de service.",
        "projection" : [
            "→ Les voies vers hôpitaux et CHSLD sont traitées en priorité absolue.",
            "→ Les ambulances peuvent atteindre les urgences dès la 1ère heure d'opération.",
            "⚠ RISQUE : les axes commerciaux sont dégagés plus tard, impact économique modéré.",
            "✔ IMPACT : réduction des délais d'intervention médicale pour les personnes vulnérables.",
        ],
        "color"      : CYAN,
    },
    "mixte": {
        "label"      : "Mixte",
        "description": "Équilibre entre coût et impact social. Les axes prioritaires sont "
                       "traités en premier, mais le routage global reste efficient.",
        "objectif"   : "Compromis coût/service optimal pour la ville.",
        "cible"      : "Municipalité + citoyens.",
        "risque"     : "Moins optimal que chaque scénario pur sur son critère propre.",
        "projection" : [
            "→ Les artères prioritaires sont traitées tôt sans sacrifier l'efficience globale.",
            "→ Convient aux opérations courantes (chutes modérées de 2,5 à 10 cm).",
            "⚠ RISQUE : moins performant que S1 sur le coût et que S2 sur l'accès aux soins.",
            "✔ IMPACT : service équilibré pour l'ensemble des habitants de l'arrondissement.",
        ],
        "color"      : YELLOW,
    },
}


def run_secteur(secteur: str, scenario: str, n_vehicles: int, verbose: bool = True) -> dict:
    cfg = SECTEURS_CONFIG[secteur]
    G   = get_graph(secteur)

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
        kv("Distance totale"               , indic["distance_totale_km"], "km")
        kv("Coût total"                    , f"${indic['cout_total_$']:,.2f}")
        kv("Durée max (1 véh.)"            , indic["duree_max_h"], "h")
        kv("Couverture réseau"             , f"{indic['couverture_%']} %")
        kv("Artères couvertes 1ère moitié" , f"{indic['arteres_couvertes_1ere_moitie_%']} %")
        kv("Ruelles couvertes 1ère moitié" , f"{indic['ruelles_couvertes_1ere_moitie_%']} %")
        kv("Délai couverture artères"      , f"{indic['delai_arteres_h']} h")
        kv("Ratio coût/km réseau"          , f"${indic['ratio_cout_km']}", "/km")

    return {
        "secteur"    : secteur,
        "scenario"   : scenario,
        "routes"     : routes,
        "indicateurs": indic,
    }


def comparaison_scenarios(secteur: str, n_vehicles: int):
    section(f"COMPARAISON DES 3 SCÉNARIOS — {secteur}")
    results = {}
    G = get_graph(secteur)

    for sc in ["economique", "social", "mixte"]:
        routes = split_routes_multi_vehicle(G, n_vehicles, sc)
        indic  = compute_indicators(G, routes, sc)
        results[sc] = {"secteur": secteur, "scenario": sc, "routes": routes, "indicateurs": indic}

        sc_info = SCENARIOS[sc]
        col     = sc_info["color"]
        print(f"\n  {col}{BOLD}[{sc_info['label'].upper()}]{RESET}")
        kv("  Coût total"                    , f"${indic['cout_total_$']:,.2f}")
        kv("  Distance totale"               , f"{indic['distance_totale_km']} km")
        kv("  Couverture réseau"             , f"{indic['couverture_%']} %")
        kv("  Durée max / véhicule"          , f"{indic['duree_max_h']} h")
        kv("  Artères couvertes 1ère moitié" , f"{indic['arteres_couvertes_1ere_moitie_%']} %")
        kv("  Ruelles couvertes 1ère moitié" , f"{indic['ruelles_couvertes_1ere_moitie_%']} %")
        kv("  Délai couverture artères"      , f"{indic['delai_arteres_h']} h")
        kv("  Objectif"                      , sc_info["objectif"])
        kv("  Cible"                         , sc_info["cible"])
        kv("  Risque principal"              , sc_info["risque"])

    section(f"PROJECTIONS RÉELLES — {secteur}")
    for sc in ["economique", "social", "mixte"]:
        sc_info = SCENARIOS[sc]
        col     = sc_info["color"]
        print(f"\n  {col}{BOLD}[{sc_info['label'].upper()}]{RESET}")
        for line in sc_info["projection"]:
            if line.startswith("⚠"):
                print(f"  {YELLOW}  {line}{RESET}")
            elif line.startswith("✔"):
                print(f"  {GREEN}  {line}{RESET}")
            else:
                print(f"  {WHITE}  {line}{RESET}")

    couts     = {sc: results[sc]["indicateurs"]["cout_total_$"] for sc in results}
    best_cost = min(couts, key=couts.get)
    print(f"\n  {GREEN}{BOLD}→ Scénario le moins coûteux : {SCENARIOS[best_cost]['label']} "
          f"(${couts[best_cost]:,.2f}){RESET}")
    print(f"  {CYAN}→ Pour la sécurité des citoyens : Scénario Social recommandé.{RESET}")
    print(f"  {YELLOW}→ Recommandation générale : Scénario Mixte (équilibre optimal).{RESET}")

    return results


def modele_cout_global(n_vehicles_list: list, km_par_vehicule: float = 50.0):
    section("MODÈLE DE COÛT GLOBAL — ENSEMBLE DE LA VILLE")
    print(f"  Hypothèse : {km_par_vehicule} km/véhicule/jour (moyenne Montréal)\n")
    print(f"  {'Véhicules':>10} | {'Coût total ($)':>16} | {'Durée (h)':>10} | {'Remarque'}")
    print(f"  {'-'*70}")
    for n in n_vehicles_list:
        c     = compute_cost(km_par_vehicule, n)
        duree = c["heures"]
        rem   = "⚠ Heures sup." if duree > 8 else "✔ Dans les 8h"
        print(f"  {n:>10} | {c['cout_global']:>16,.2f} | {duree:>10.1f} | {rem}")


def tests_sensibilite():
    section("TESTS DE SENSIBILITÉ — Verdun, Scénario Social (1 à 8 véhicules)")
    print(f"\n  {'Véhicules':>10} | {'Distance (km)':>14} | {'Coût ($)':>12} | "
          f"{'Durée (h)':>10} | {'Couverture':>11}")
    print(f"  {'─'*65}")
    G_test = get_graph("Verdun")
    for n in [1, 2, 3, 5, 8]:
        routes_test = split_routes_multi_vehicle(G_test, n, "social")
        indic_test  = compute_indicators(G_test, routes_test, "social")
        print(f"  {n:>10} | {indic_test['distance_totale_km']:>14.2f} | "
              f"{indic_test['cout_total_$']:>12,.2f} | "
              f"{indic_test['duree_max_h']:>10.2f} | "
              f"{indic_test['couverture_%']:>10.1f}%")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Démonstration optimisation déneigement Montréal"
    )
    parser.add_argument("--secteur",    default="ALL",
                        choices=list(SECTEURS_CONFIG.keys()) + ["ALL"],
                        help="Secteur à étudier (défaut: ALL)")
    parser.add_argument("--scenario",   default="ALL",
                        choices=["economique", "social", "mixte", "ALL"],
                        help="Scénario de priorisation (défaut: ALL)")
    parser.add_argument("--vehicules",  type=int, default=3,
                        help="Nombre de véhicules par secteur (défaut: 3)")
    parser.add_argument("--export-json", action="store_true",
                        help="Exporter les résultats en JSON")
    args = parser.parse_args()

    banner()

    secteurs    = list(SECTEURS_CONFIG.keys()) if args.secteur == "ALL" else [args.secteur]
    all_results = {}

    for secteur in secteurs:
        if args.scenario == "ALL":
            res = comparaison_scenarios(secteur, args.vehicules)
        else:
            res = run_secteur(secteur, args.scenario, args.vehicules)
        all_results[secteur] = res

    modele_cout_global([5, 10, 20, 50, 100, 200, 500, 2000])

    section("PROJECTION VILLE ENTIÈRE — MONTRÉAL (10 000 km de routes)")
    km_par_veh = 50.0
    n_veh_req  = math.ceil(10_000 / km_par_veh)
    c_global   = compute_cost(km_par_veh, n_veh_req)
    kv("Véhicules nécessaires (estimation)", n_veh_req)
    kv("Coût estimé journalier"            , f"${c_global['cout_global']:,.0f}")
    kv("Comparaison budget annuel (200 M$)", f"~{round(c_global['cout_global'] * 150 / 1e6, 1)} M$ / saison (150 jours)")
    warn("Estimation basée sur 50 km/véhicule — à ajuster selon la réalité du terrain.")

    tests_sensibilite()

    if args.export_json:
        out_path = "resultats_deneigement.json"
        export   = {}
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


if __name__ == "__main__":
    main()

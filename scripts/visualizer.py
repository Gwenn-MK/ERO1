"""
visualizer.py
Auteurs: Meku · Akanni · Bensammar · Hookoom — ÉPITA
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

VEHICLE_COLORS = ["#1565C0", "#FF6F00", "#2E7D32", "#C62828", "#4527A0", "#00695C"]

HIGHWAY_COLORS = {
    "motorway"    : "#C62828",
    "trunk"       : "#C62828",
    "primary"     : "#E65100",
    "secondary"   : "#F9A825",
    "tertiary"    : "#546E7A",
    "residential" : "#90A4AE",
    "living_street": "#B0BEC5",
    "service"     : "#CFD8DC",
    "unclassified": "#CFD8DC",
}

SCENARIO_LABELS = {
    "economique": "Priorisation Économique",
    "social"    : "Priorisation Sociale",
    "mixte"     : "Priorisation Mixte",
}

OSM_NAMES = {
    "Outremont": "Outremont, Montréal, Québec, Canada",
    "Verdun"   : "Verdun, Montréal, Québec, Canada",
    "Anjou"    : "Anjou, Montréal, Québec, Canada",
    "RDP"      : "Rivière-des-Prairies, Montréal, Québec, Canada",
}


def get_node_positions(G, secteur):
    pos = {}
    try:
        import osmnx as ox
        G_orig = ox.graph_from_place(OSM_NAMES[secteur], network_type="drive")
        for n in G.nodes():
            if n in G_orig.nodes:
                d = G_orig.nodes[n]
                pos[n] = (d.get("x", 0), d.get("y", 0))
    except Exception:
        pass
    missing = [n for n in G.nodes() if n not in pos or pos[n] == (0, 0)]
    if missing:
        import math
        total = len(missing)
        for i, n in enumerate(missing):
            angle = 2 * math.pi * i / max(total, 1)
            pos[n] = (math.cos(angle), math.sin(angle))
    return pos


def plot_routes(G, routes, secteur, scenario, output_path):
    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor("#F4F7FB")
    ax.set_facecolor("#F4F7FB")

    pos = get_node_positions(G, secteur)

    for u, v, data in G.edges(data=True):
        if u not in pos or v not in pos:
            continue
        x  = [pos[u][0], pos[v][0]]
        y  = [pos[u][1], pos[v][1]]
        hw = data.get("highway", "residential")
        lw = 2.5 if hw in ("primary", "secondary", "trunk", "motorway") else 0.8
        ax.plot(x, y, color=HIGHWAY_COLORS.get(hw, "#CFD8DC"),
                linewidth=lw, alpha=0.25, zorder=1)

    for vid, route in enumerate(routes):
        color  = VEHICLE_COLORS[vid % len(VEHICLE_COLORS)]
        seg_x, seg_y = [], []
        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            if u in pos and v in pos:
                seg_x += [pos[u][0], pos[v][0], None]
                seg_y += [pos[u][1], pos[v][1], None]
        parts_x, parts_y = [[]], [[]]
        for x, y in zip(seg_x, seg_y):
            if x is None:
                parts_x.append([])
                parts_y.append([])
            else:
                parts_x[-1].append(x)
                parts_y[-1].append(y)
        for px, py in zip(parts_x, parts_y):
            if px:
                ax.plot(px, py, color=color, linewidth=2.0,
                        alpha=0.80, zorder=3, solid_capstyle="round")
        if route and route[0] in pos:
            ax.scatter(*pos[route[0]], s=100, c=color, zorder=5,
                       edgecolors="white", linewidths=1.5)

    vehicle_patches = [
        mpatches.Patch(color=VEHICLE_COLORS[i % len(VEHICLE_COLORS)],
                       label=f"Déneigeuse {i+1}")
        for i in range(len(routes))
    ]
    road_patches = [
        mpatches.Patch(color="#E65100", alpha=0.6, label="Artère principale"),
        mpatches.Patch(color="#F9A825", alpha=0.6, label="Artère secondaire"),
        mpatches.Patch(color="#90A4AE", alpha=0.6, label="Voie résidentielle"),
        mpatches.Patch(color="#CFD8DC", alpha=0.6, label="Service / ruelle"),
    ]
    leg1 = ax.legend(handles=vehicle_patches, loc="upper left",
                     framealpha=0.92, fontsize=10, title="Véhicules")
    ax.add_artist(leg1)
    ax.legend(handles=road_patches, loc="lower left",
              framealpha=0.92, fontsize=9, title="Type de voie")

    ax.set_title(
        f"Parcours des déneigeuses — {secteur}\n"
        f"Scénario : {SCENARIO_LABELS.get(scenario, scenario)}",
        fontsize=14, fontweight="bold", pad=15
    )
    ax.set_xlabel("Longitude", fontsize=9)
    ax.set_ylabel("Latitude", fontsize=9)
    ax.tick_params(labelsize=7)
    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [Carte] Sauvegardée : {output_path}")

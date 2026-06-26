# Optimisation Hivernale — Déneigement Montréal

**Auteurs :** Mariam Anu Akanni · Anna Bensammar · Hans Hookoom · Gwenn Meku Kengne

---

## Description

Ce projet propose une solution d'optimisation des itinéraires des déneigeuses
de la ville de Montréal, basée sur le **Problème du Postier Chinois orienté**
(Chinese Postman Problem — CPP). Les données géographiques proviennent
d'**OpenStreetMap via OSMnx** — graphes routiers réels avec sens de circulation.
Trois scénarios de priorisation sont étudiés sur 4 arrondissements.

| Scénario   | Objectif principal                             | Cible                        |
|------------|------------------------------------------------|------------------------------|
| Économique | Minimiser les coûts opérationnels              | Municipalité, commerces, STM |
| Social     | Prioriser les axes critiques pour les citoyens | Personnes vulnérables, soins |
| Mixte      | Compromis coût/service (opérations courantes)  | Ensemble des habitants       |

---

## Structure du rendu

```
ERO1/
├── AUTHORS
├── README.md
├── demo.py
├── rapport/
│   └── rapport_formalisation_ERO1.pdf
├── scripts/
│   ├── graph_utils.py
│   ├── visualizer.py
│   └── generate_rapport.py
└── secteurs/
    ├── Outremont/
    │   ├── analyse_outremont.py
    │   ├── carte_economique.png
    │   ├── carte_social.png
    │   ├── carte_mixte.png
    │   └── itineraire_*.json
    ├── Verdun/
    │   ├── analyse_verdun.py
    │   ├── carte_*.png
    │   └── itineraire_*.json
    ├── Anjou/
    │   ├── analyse_anjou.py
    │   ├── carte_*.png
    │   └── itineraire_*.json
    └── RDP/
        ├── analyse_rdp.py
        ├── carte_*.png
        └── itineraire_*.json
```

---

## Installation

### Prérequis

- Python 3.10+
- Connexion internet (pour le téléchargement OSMnx au premier lancement)

### Dépendances

```bash
python -m venv .venv
source .venv/bin/activate
pip install networkx matplotlib numpy reportlab osmnx scipy
```

> **Note :** OSMnx télécharge les données OpenStreetMap au premier lancement
> et les met en cache automatiquement dans `cache/`. Les lancements suivants
> n'ont pas besoin de connexion internet.

---

## Exécution

### Démonstration complète (tous secteurs, tous scénarios)

```bash
python demo.py
```

### Démonstration ciblée

```bash
python demo.py --secteur Verdun --scenario social --vehicules 5
python demo.py --secteur Anjou  --scenario economique --vehicules 3
python demo.py --export-json
python demo.py --help
```

### Analyse et cartes par secteur

```bash
python secteurs/Outremont/analyse_outremont.py
python secteurs/Verdun/analyse_verdun.py
python secteurs/Anjou/analyse_anjou.py
python secteurs/RDP/analyse_rdp.py
```

Chaque script génère pour les 3 scénarios :
- `itineraire_<scenario>.json` — résultats et indicateurs
- `carte_<scenario>.png` — carte du parcours de chaque déneigeuse

---

## Paramètres de coût (énoncé section 4)

| Composante        | Valeur     |
|-------------------|------------|
| Coût fixe         | 500 $/jour |
| Coût kilométrique | 1,1 $/km   |
| Coût horaire ≤ 8h | 1,1 $/h    |
| Coût horaire > 8h | 1,3 $/h    |
| Vitesse moyenne   | 10 km/h    |

---

## Algorithme

### Chinese Postman Problem orienté

Le réseau routier de chaque arrondissement est modélisé comme un **graphe
orienté G = (V, E)** extrait via OSMnx depuis OpenStreetMap. Chaque arête
porte ses attributs réels : longueur (km), type de voie (highway OSMnx),
sens de circulation.

**Pipeline de résolution :**

1. **Extraction OSMnx** — graphe orienté réel (DiGraph NetworkX)
2. **Pondération** — `w(e) = longueur(e) × facteur_type(e) × facteur_poi(e)`
3. **Parcours glouton pondéré** — à chaque nœud, l'arête sortante de poids
   le plus faible est choisie parmi les arêtes non encore visitées
4. **Couverture totale** — lorsque plus d'arête directe, Dijkstra trouve
   le chemin le plus court vers la prochaine arête non visitée
5. **Partitionnement** — le circuit est découpé en n sous-routes équilibrées

> **Pourquoi le parcours glouton pondéré et non Hierholzer ?**
> Hierholzer construit un circuit eulérien sans tenir compte des poids lors
> du choix des arêtes. Les 3 scénarios produisaient des résultats identiques.
> Le parcours glouton pondéré choisit activement les arêtes par poids, ce qui
> différencie réellement les scénarios.

### Pondération par scénario

| Type OSM       | Éco  | Social | Mixte |
|----------------|------|--------|-------|
| primary/trunk  | 0,90 | 0,45   | 0,60  |
| secondary      | 1,00 | 0,60   | 0,75  |
| tertiary       | 1,00 | 0,80   | 0,90  |
| residential    | 1,00 | 1,20   | 1,10  |
| service/alley  | 1,20 | 1,80   | 1,50  |

| POI (rayon 50m) | Éco  | Social | Mixte |
|-----------------|------|--------|-------|
| Hôpital / CLSC  | 1,00 | 0,50   | 0,70  |
| École / garderie| 1,00 | 0,60   | 0,75  |
| Arrêt bus STM   | 1,00 | 0,70   | 0,80  |

---

## Résultats (3 véhicules, données OSMnx réelles)

| Arrondissement | Scénario   | Distance (km) | Coût ($)  | Couverture |
|----------------|------------|---------------|-----------|------------|
| Outremont      | Économique | 91,97         | 1 611,29  | 100%       |
| Outremont      | Social     | 92,93         | 1 612,46  | 100%       |
| Outremont      | Mixte      | 91,56         | 1 610,78  | 100%       |
| Verdun         | Économique | 121,63        | 1 647,18  | 100%       |
| Verdun         | Social     | 124,16        | 1 650,24  | 100%       |
| Verdun         | Mixte      | 122,21        | 1 647,86  | 100%       |
| Anjou          | Économique | 309,04        | 1 875,30  | 100%       |
| Anjou          | Social     | 313,25        | 1 880,50  | 100%       |
| Anjou          | Mixte      | 305,59        | 1 871,10  | 100%       |
| RDP–PAT        | Économique | 230,98        | 1 779,48  | 100%       |
| RDP–PAT        | Social     | 234,27        | 1 783,45  | 100%       |
| RDP–PAT        | Mixte      | 227,88        | 1 775,72  | 100%       |

---

## Références

- Ville de Montréal — Documentation déneigement officielle
- Marco Fortier, *La Presse*, novembre 2023
- Sarah-Maude Lefebvre, *Journal de Montréal*, décembre 2019
- Morgan Lowrie, *Le Devoir*, décembre 2025
- CBC News, février 2018
- Henri Ouellette Vézina, *Métro*, janvier 2020
- Vélo Québec — L'état du vélo au Québec, 2023
- Statistiques Canada — Enquête sur les transports des ménages, 2021
- CIUSSS Centre-Sud-de-l'Île de Montréal — Répertoire des établissements
- Boeing G. — OSMnx: New Methods for Acquiring Complex Street Networks, 2017
- OpenStreetMap contributors — Données sous licence ODbL

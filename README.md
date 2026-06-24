# Optimisation Hivernale — Déneigement Montréal
**Auteurs :** L.Blet & H.Paris — ÉPITA

---

## Description

Ce projet propose une solution d'optimisation des itinéraires des déneigeuses
de la ville de Montréal, basée sur le **Problème du Postier Chinois** (Chinese
Postman Problem — CPP). Trois scénarios de priorisation sont étudiés :

| Scénario    | Objectif principal                          |
|-------------|---------------------------------------------|
| Économique  | Minimiser les coûts opérationnels           |
| Social      | Prioriser les axes critiques pour les citoyens |
| Mixte       | Compromis coût/service                      |

---

## Structure du rendu

```
projet_deneigement/
├── AUTHORS                     # Liste des auteurs
├── README.md                   # Ce fichier
├── demo.py                     # Script de démonstration principal
├── rapport/
│   └── rapport_deneigement.pdf # Rapport (max 8 pages)
├── scripts/
│   ├── graph_utils.py          # Module principal : graphes, CPP, coûts
│   └── generate_rapport.py     # Génération du rapport PDF
└── secteurs/
    ├── Outremont/
    │   ├── analyse_outremont.py
    │   └── itineraire_*.json   # (générés à l'exécution)
    ├── Verdun/
    │   ├── analyse_verdun.py
    │   └── itineraire_*.json
    ├── Anjou/
    │   ├── analyse_anjou.py
    │   └── itineraire_*.json
    └── RDP/
        ├── analyse_rdp.py
        └── itineraire_*.json
```

---

## Installation

### Prérequis
- Python 3.10+
- pip

### Dépendances
```bash
pip install networkx matplotlib reportlab numpy
```

---

## Exécution

### Démonstration complète (tous secteurs, tous scénarios)
```bash
python demo.py
```

### Démonstration ciblée
```bash
# Un secteur spécifique, un scénario
python demo.py --secteur Verdun --scenario social --vehicules 5

# Exporter les résultats en JSON
python demo.py --export-json

# Aide
python demo.py --help
```

### Analyse par secteur
```bash
python secteurs/Outremont/analyse_outremont.py
python secteurs/Verdun/analyse_verdun.py
python secteurs/Anjou/analyse_anjou.py
python secteurs/RDP/analyse_rdp.py
```

### Regénérer le rapport PDF
```bash
python scripts/generate_rapport.py
```

---

## Paramètres de coût (énoncé section 4)

| Composante            | Valeur       |
|-----------------------|--------------|
| Coût fixe             | 500 $/jour   |
| Coût kilométrique     | 1,1 $/km     |
| Coût horaire ≤ 8h     | 1,1 $/h      |
| Coût horaire > 8h     | 1,3 $/h      |
| Vitesse moyenne       | 10 km/h      |

---

## Algorithme principal

Le **Problème du Postier Chinois** (CPP) est résolu en deux étapes :
1. Identification des nœuds de degré impair dans le graphe.
2. Appariement minimum parfait (approché de façon gloutonne via Dijkstra).
3. Duplication des arêtes de plus court chemin pour obtenir un graphe eulérien.
4. Calcul d'un circuit eulérien (algorithme de Hierholzer).

La pondération des arêtes varie selon le scénario :
- **Économique** : poids = longueur brute
- **Social** : poids = longueur × facteur_priorité (0,5 / 1,0 / 1,8)
- **Mixte** : poids = longueur × facteur_priorité (0,7 / 1,0 / 1,3)

---

## Références

- Ville de Montréal — Documentation déneigement officielle
- Marco Fortier, *La Presse*, novembre 2023
- Sarah-Maude Lefebvre, *Journal de Montréal*, décembre 2019
- Morgan Lowrie, *Le Devoir*, décembre 2025
- CBC News, février 2018
- Henri Ouellette Vézina, *Métro*, janvier 2020

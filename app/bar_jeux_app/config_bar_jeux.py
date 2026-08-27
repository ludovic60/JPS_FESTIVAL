"""Configuration de l'application Bar à jeux."""
from pathlib import Path
import os
import sys
# Ajoute le dossier parent à sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import commun.common_store as cs


VIEUX_KEY = "vieux"

_MOIS_FR = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
    7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
}


def month_keys():
    """Liste (clé, libellé) d'Octobre 2025 à Octobre 2026 inclus."""
    keys = []
    y, m = cs._secret("ANNEE_FESTIVAL")-1, cs._secret("MOIS_FESTIVAL")
    for _ in range(13):
        keys.append((f"{y}_{m:02d}", f"{_MOIS_FR[m]} {y}"))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return keys




# Champs d'un jeu (clé interne -> libellé affiché)
GAME_FIELDS = [
		

    ("_id","_id"), ("url_myludo", "URL myludo"), ("id_myludo", "ID myludo"), ("code_barre", "Code barre"),
    ("nom_jeu", "Nom jeu"), ("nom_jeu_fichier", "Nom jeu dans fichier"),
    ("sous_titre", "Sous-titre jeu"), ("nom_jeu_complet", "Nom jeu complet"),
    ("type_jeu", "Type du jeu"), ("type_financement", "Type de financement"),
    ("detail_financement", "Détail du financement"), ("langue_principale", "Langue principale"),
    ("langues", "Langues"), ("annee_parution", "Année de parution"), ("mois_sortie", "Mois de sortie"),("date_sortie", "Date de sortie"),
    ("est_selectionnable", "Est selectionnable"), ("nombre_joueurs", "Nombre de joueurs"),
    ("nbr_max_joueurs", "Nbr max joueurs"), ("age_boite", "Âge sur la boîte"), ("age_min", "Âge min"),
    ("duree", "Durée"), ("duree_min", "Durée min"), ("duree_max", "Durée max"),
    ("poids_boite", "Poids de la boîte"), ("dimension_boite", "Dimension boîte"),
    ("categorie", "Catégorie"), ("mecanismes", "Mécanismes"), ("gamme", "Gamme"),
    ("univers", "Univers"), ("thematiques", "Thématiques"),
    ("editeur_illustrateur_createur", "Éditeur/illustrateur/créateur"), ("recompenses", "Récompenses"),
    ("couverture", "Couverture"), ("description", "Description"), ("note_bgg", "Note BGG"),
    ("note_bgg_manuel", "Note BGG manuel (correctif)"), ("note_finale", "Note finale"),
    ("classement_jps_auto", "Classement JPS automatique"),
    ("classement_jps_correction", "Classement JPS correction manuelle"),
    ("classement_jps_final", "Classement JPS final"), ("classement_duree", "Classement par durée"),
    ("stat_myludo", "stat de myludo"),
]
GAME_KEYS = [k for k, _ in GAME_FIELDS]

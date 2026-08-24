"""Configuration de l'application Bar à jeux."""
from pathlib import Path
import common_store as cs

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "jeux"

USERS_FILE = DATA_DIR / "users.json"
ADMIN_SELECTED_FILE = DATA_DIR / "admin_selected.json"
SUGGESTIONS_FILE = DATA_DIR / "suggestions.json"
REQUESTS_FILE = DATA_DIR / "requests.json"
LOANS_FILE = DATA_DIR / "loans.json"

VIEUX_KEY = "vieux"

_MOIS_FR = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
    7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
}


def month_keys():
    """Liste (clé, libellé) d'Octobre 2025 à Octobre 2026 inclus."""
    keys = []
    y, m = _secrets("ANNEE_FESTIVAL"), _secrets("MOIS_FESTIVAL")
    for _ in range(13):
        keys.append((f"{y}_{m:02d}", f"{_MOIS_FR[m]} {y}"))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return keys


def games_file(list_key: str) -> Path:
    return DATA_DIR / f"jeux_{list_key}.json"


# Champs d'un jeu (clé interne -> libellé affiché)
GAME_FIELDS = [
    ("url", "URL"), ("id_myludo", "ID myludo"), ("code_barre", "Code barre"),
    ("url_myludo", "URL myludo"), ("nom_jeu", "Nom jeu"), ("nom_jeu_fichier", "Nom jeu dans fichier"),
    ("sous_titre", "Sous-titre jeu"), ("nom_jeu_complet", "Nom jeu complet"),
    ("type_jeu", "Type du jeu"), ("type_financement", "Type de financement"),
    ("detail_financement", "Détail du financement"), ("langue_principale", "Langue principale"),
    ("langues", "Langues"), ("annee_parution", "Année de parution"), ("date_sortie", "Date de sortie"),
    ("est_nouveaute", "Est nouveauté"), ("nombre_joueurs", "Nombre de joueurs"),
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
]
GAME_KEYS = [k for k, _ in GAME_FIELDS]

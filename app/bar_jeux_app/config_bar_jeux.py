"""Configuration de l'application Bar à jeux."""
from pathlib import Path
import os
import sys
# Ajoute le dossier parent à sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import commun.common_store as cs


VIEUX_KEY = "est_selectionnable"

_MOIS_FR = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
    7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
}


_CLS_FAMILLE = f"⚪⚪⚪ FAMILLE"
_CLS_INITIE  = f"🟡⚪⚪ INITIE"
_CLS_EXPERT  = f"🔴🔴⚪ EXPERT"
_CLS_EXPERT_PLUS = f"🔴🔴🔴 EXPERT+"
_CLS_ENFANT = f"🧸 ENFANT"                                        
_CLS_DUO  = f"👥 JEU DUO"                                       
_CLS_COOP   = f"🤝 COOP/SEMI COOP"                             
_CLS_ENQUETE_ESCAPE   = f"🕵️ ENQUETE/ESCAPE/ENIGME/CASSETETE"                            
_CLS_AMBIANCE = f"🎉 AMBIANCE"
_CLS_NON_CLASSE = f"🤔 NON CLASSE"


couleurs_classement = {"AMBIANCE": "#E655DA", ## rose
                           "COOP/SEMI COOP" :"#7A0EE3",####violet
                           "JEU DUO" :"#FF9224",          ##orange                 
                           "ENQUETE/ESCAPE/ENIGME/CASSETETE" :"#1FC7FF",##bleu clair
                           "NON CLASSE": "#C7C5C5", ### gris
                           "PBM CLASSEMENT": "#080808",   ### black                         
                           "FAMILLE": "#57B02C", ## vert 
                           "INITIE": "#F5E20C", ## jaune 
                           "EXPERT": "#E67A70", ### rouge  
                           "EXPERT+": "#8C0E07",   ### rouge   foncé                     
                           "ENFANT": "#1128D6" ### bleu foncé
                          }

couleurs_nouveaute = {"✨NOUVEAUTE": "#57B02C", "🏺ANCIEN": "#080808", "🧐 INCONNU": "#1128D6"}



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

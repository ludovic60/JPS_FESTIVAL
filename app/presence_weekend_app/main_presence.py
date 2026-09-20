"""Point d'entrée de l'application (déployable sur https://share.streamlit.io/deploy).

Lancement local :  streamlit run streamlit_app.py
"""

import streamlit as st
import sys
from pathlib import Path
import storage_presence
from views import  main_app


# Ajoute le dossier parent (la racine du projet) à sys.path
racine_projet = Path(__file__).resolve().parent.parent
sys.path.append(str(racine_projet))
from commun.design_system import inject
from commun.auth import require_auth, logout, current_user

import tomllib
#####------------------------------------------------------------------------------------------------------------
####force le mode d'affichage definie dans tomlib  dans les differents navigateur (opera et chrome par exemple)
# Charger le fichier de configuration Streamlit
try:
  with open(".streamlit/config.toml", "rb") as f:
    config = tomllib.load(f)
  bg_color = config.get("theme", {}).get("backgroundColor", "#FFFFFF")
  text_color = config.get("theme", {}).get("textColor", "#262730")
except Exception:
  # Valeurs par défaut de secours en cas d'erreur
  bg_color = "#FFFFFF"
  text_color = "#262730"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    </style>
""",
    unsafe_allow_html=True,
)


#####------------------------------------------------------------------------------------------------------------


# 1. Force l'authentification (stoppe l'exécution et affiche le login si non connecté)
require_auth()

# 2. Récupération des infos de l'utilisateur connecté
user = current_user()


st.set_page_config(page_title="Présence Week-end", page_icon="📅", layout="wide")
inject()

#storage_presence.init_storage()

# Lien de réinitialisation : ?token=...
params = st.query_params
token = params.get("token")


user = current_user()


main_app(user)

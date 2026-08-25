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
from commun.auth import require_auth, logout

# Exécute la vérification (affiche le formulaire si besoin, puis stoppe)
require_auth()

st.set_page_config(page_title="Présence Week-end", page_icon="📅", layout="wide")
inject()

storage_presence.init_storage()

# Lien de réinitialisation : ?token=...
params = st.query_params
token = params.get("token")


user = auth.current_user()

main_app(user)

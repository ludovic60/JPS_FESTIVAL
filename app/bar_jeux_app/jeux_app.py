"""Point d'entrée Bar à jeux (déployable sur share.streamlit.io).

Lancement local :  streamlit run jeux_app.py
"""
import streamlit as st
from pathlib import Path
from views import  main_app
import storage_jeux
import os
import sys


# Ajoute le dossier parent (la racine du projet) à sys.path
racine_projet = Path(__file__).resolve().parent.parent
sys.path.append(str(racine_projet))
from commun.design_system import inject
from commun.auth import require_auth, logout, current_user

# Exécute la vérification (affiche le formulaire si besoin, puis stoppe)
require_auth()

# Lien de réinitialisation : ?token=...
params = st.query_params
token = params.get("token")

user = current_user()

st.set_page_config(page_title="Bar à jeux", page_icon="🎲", layout="wide")
inject()

main_app(user)

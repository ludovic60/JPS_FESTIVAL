"""Point d'entrée Bar à jeux (déployable sur share.streamlit.io).

Lancement local :  streamlit run jeux_app.py
"""
import streamlit as st

from views import  main_app
import storage_jeux
import os
import sys
# Ajoute le dossier parent à sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from commun.design_system import inject

import commun.auth, commun.common_store


st.set_page_config(page_title="Bar à jeux", page_icon="🎲", layout="wide")
inject()


# Exécute la vérification (affiche le formulaire si besoin, puis stoppe)
require_auth()

main_app(user)

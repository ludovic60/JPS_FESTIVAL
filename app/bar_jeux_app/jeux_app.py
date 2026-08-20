"""Point d'entrée Bar à jeux (déployable sur share.streamlit.io).

Lancement local :  streamlit run jeux_app.py
"""
import streamlit as st

from ..design_system import inject
from . import auth, storage
from views import login_view, main_app

st.set_page_config(page_title="Bar à jeux", page_icon="🎲", layout="wide")
inject()
storage.init_storage()

user = auth.current_user()
if not user:
    login_view()
    st.stop()

main_app(user)

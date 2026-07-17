"""Point d'entrée de l'application (déployable sur https://share.streamlit.io/deploy).

Lancement local :  streamlit run streamlit_app.py
"""
import streamlit as st

from design_system import inject
from weekend_app import auth, storage
##from weekend_app.views import login_view, reset_password_view, main_app

st.set_page_config(page_title="Présence Week-end", page_icon="📅", layout="wide")
inject()

storage.init_storage()

# Lien de réinitialisation : ?token=...
params = st.query_params
token = params.get("token")

if token and not auth.current_user():
    reset_password_view(token)
    st.stop()

user = auth.current_user()
if not user:
    login_view()
    st.stop()

main_app(user)

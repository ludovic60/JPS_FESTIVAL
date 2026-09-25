"""Logique d'authentification basée sur st.session_state."""

import streamlit as st
from supabase import create_client, Client
import os
import sys
# Ajoute le dossier parent à sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import commun.config

import commun.common_store as cs
from commun.config import get_secret



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


# Initialisation du client Supabase (mis en cache pour optimiser les performances)
@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

def current_user():
    user_supabase = st.session_state.get("user")
    print(user_supabase)
    pseudo = user_supabase["pseudo"]
    print(pseudo)
  
    
    return cs.get_user_by_pseudo(pseudo)

def login(email, password):
    try:
        # Appel officiel de Supabase Auth
        response = supabase.auth.sign_in_with_password({
            "email": email.strip(),
            "password": password
        })
        
        # Stockage des données publiques de l'utilisateur en session Streamlit
        user_data = response.user
        st.session_state["user"] = {
            "id": user_data.id,
            "email": user_data.email,
            "role": user_data.user_metadata.get("role", "user"),
            "pseudo": user_data.user_metadata.get("pseudo", "")
        }
        st.session_state["authenticated"] = True
        st.session_state["access_token"] = response.session.access_token
        return None
        
    except Exception as e:
        # Retourne un message d'erreur générique pour la sécurité
        return "Email ou mot de passe incorrect."

def login_with_pseudo(pseudo, password):
    try:
        # Nettoyage du pseudo et création du faux email associé
        clean_pseudo = pseudo.strip().lower()
        dummy_email = f"{clean_pseudo}@festivaljeuxcrepy.local"
        
        # Appel à Supabase avec l'email reconstitué
        response = supabase.auth.sign_in_with_password({
            "email": dummy_email,
            "password": password
        })
        
        # Stockage de la session
        user_data = response.user
        st.session_state["user"] = {
            "id": user_data.id,
            "email": user_data.email,
            "role": user_data.user_metadata.get("role", "user"),
            "pseudo": user_data.user_metadata.get("pseudo", pseudo.strip()),
            "prete_jeu" : user_data.user_metadata.get("prete_jeu", pseudo.strip())
        }
        st.session_state["authenticated"] = True
        return None
        
    except Exception as e:
        return "Pseudo ou mot de passe incorrect."


def logout():
    try:
        supabase.auth.signOut()
    except Exception:
        pass
    
    # Nettoyage de la session
    st.session_state.pop("user", None)
    st.session_state.pop("authenticated", None)
    st.session_state.pop("access_token", None)
    st.rerun()

def require_auth():
    """Bloque l'accès à l'application si l'utilisateur n'est pas connecté."""
    if st.session_state.get("authenticated", False):
        return True

    # Affichage du formulaire de connexion si non authentifié
    st.subheader("Connexion requise")
    login_view()
    st.stop()

def login_view():
    st.title("FESTIVAL JEUX DE CREPY")
    st.caption("Connectez-vous pour accéder aux applications du festival.")

    with st.form("supabase_login_form"):
        # email = st.text_input("Email")
        texte_saisi = st.text_input("Pseudo ou Email")
        password = st.text_input("Mot de passe", type="password")

        if st.form_submit_button("Se connecter", type="primary"):
           # err = login(email, password)
            if "@" in texte_saisi :
                err = login(texte_saisi, password)
            else : 
                err = login_with_pseudo(texte_saisi, password)
            if err:
                st.error(err)
            else:
                st.rerun()

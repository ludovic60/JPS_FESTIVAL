"""Logique d'authentification basée sur st.session_state."""
import streamlit as st
from email_validator import validate_email, EmailNotValidError
from streamlit_cookies_controller import CookieController

import os
import sys
# Ajoute le dossier parent à sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from commun.security import hash_password, verify_password
import commun.config

import commun.common_store
from commun.config import get_secret
from commun.security import generate_token


controller = CookieController()


def current_user():
    return st.session_state.get("user")


def login(email: str, password: str):
    try:
        validate_email(email)
    except EmailNotValidError:
        return "Adresse email invalide"
    user = common_store.check_credentials(email.strip(), password)
    if not user:
        return "Email ou mot de passe incorrect"
    st.session_state["user"] = _public(user)
    return None


# def register(name: str, email: str, password: str):
#     if len(name.strip()) < 1:
#         return "Le nom est requis"
#     if len(password) < 6:
#         return "Le mot de passe doit contenir au moins 6 caractères"
#     try:
#         validate_email(email)
#     except EmailNotValidError:
#         return "Adresse email invalide"
#     user, err = storage.create_user(email.strip(), name, password)
#     if err:
#         return err
#     st.session_state["user"] = _public(user)
#     return None


def logout():
    st.session_state.pop("user", None)
    controller.remove("user_session")
    st.rerun()


# def request_reset(email: str):
#     """Retourne (message_public, lien_debug). Réponse générique pour éviter l'énumération."""
#     user = storage.get_user_by_email(email.strip())
#     debug_link = None
#     if user:
#         token = generate_token()
#         storage.create_reset_token(user["id"], token)
#         base = str(get_secret("APP_URL", "http://localhost:8501")).rstrip("/")
#         reset_url = f"{base}/?token={token}"
#        from .email_utils import smtp_configured, send_reset_email
#         if smtp_configured():
#             send_reset_email(user["email"], reset_url)
#         else:
#             debug_link = reset_url
#     return "Si le compte existe, un email de réinitialisation a été envoyé.", debug_link


# def reset_password(token: str, new_password: str):
#     if len(new_password) < 6:
#         return "Le mot de passe doit contenir au moins 6 caractères"
#     user_id, err = storage.consume_reset_token(token)
#     if err:
#         return err
#     storage.update_password(user_id, new_password)
#     return None


def _public(user: dict) -> dict:
    return {"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}


def check_credentials(mode, login, password):
    if mode == "email":
        u = common_store.get_user_by_email(login)
      
    elif mode == "pseudo":
        u = common_store.get_user_by_pseudo(login)
        
    else :
        u = None
    return u if u and verify_password(password, u["password_hash"]) else None



def require_auth():
    """
    Gère l'authentification automatique par cookie.
    Si non connecté, affiche le formulaire et stoppe l'exécution de l'application.
    """
    # 1. Vérification de la session en mémoire
    if st.session_state.get("authenticated", False):
        return True

    # 2. Vérification de l'existence du cookie
    user_from_cookie = controller.get("user_session")
    if user_from_cookie:
        st.session_state["authenticated"] = True
        st.session_state["user"] = user_from_cookie
        return True
    st.subheader("Connexion requise")
    login_view()
    # Stoppe le reste de l'application si non authentifié
    st.stop()

# ==========================================================================
# AUTHENTIFICATION
# ==========================================================================
def login_view():
    st.title("FESTIVAL JEUX DE CREPY")
    st.caption("Connectez-vous pour acceder aux applications du festival de jeux.")
    t1 = st.tabs(["Connexion"])
    with t1:
        with st.form("j_login"):
            ps = st.text_input("pseudo")
            if not ps :
                ps = " "
            e = st.text_input("Email")   
            if not e :
                e = " "
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter", type="primary"):
                err = auth.login(ps, e, p)
                st.error(err) if err else st.rerun()
   

# def reset_password_view(token: str):
#     st.title("Réinitialiser le mot de passe")
#     with st.form("reset_form"):
#         pwd1 = st.text_input("Nouveau mot de passe", type="password")
#         pwd2 = st.text_input("Confirmer le mot de passe", type="password")
#         if st.form_submit_button("Valider", type="primary"):
#             if pwd1 != pwd2:
#                 st.error("Les mots de passe ne correspondent pas")
#             else:
#                 err = auth.reset_password(token, pwd1)
#                 if err:
#                     st.error(err)
#                 else:
#                     st.success("Mot de passe réinitialisé. Vous pouvez vous connecter.")
#                     st.link_button("Aller à la connexion", url=str(auth.get_secret("APP_URL", "/")))












"""Logique d'authentification basée sur st.session_state."""
import json
import streamlit as st
from email_validator import validate_email, EmailNotValidError
from streamlit_cookies_controller import CookieController

import os
import sys
# Ajoute le dossier parent à sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from commun.security import hash_password, verify_password
import commun.config

import commun.common_store as cs
from commun.config import get_secret
from commun.security import generate_token


controller = CookieController()


def current_user():
    return st.session_state.get("user")


def login(pseudo, email, password):
    user = None  # évite le UnboundLocalError si aucun champ n'est rempli

    if not email == " ":
        try:
            validate_email(email)
        except EmailNotValidError:
            return "Adresse email invalide"
        user = check_credentials("email", email.strip(), password)
        if not user:
            return "Email ou mot de passe incorrect"
    elif not pseudo == " ":
        user = check_credentials("pseudo", pseudo.strip(), password)
        if not user:
            return "pseudo ou mot de passe incorrect"
    else:
        return "💡 Merci de renseigner soit votre pseudo, soit votre email"

    # Clés cohérentes avec require_auth() / logout()
    st.session_state["user"] = _public(user)
    st.session_state["authenticated"] = True
    return None


def logout():
    st.session_state.pop("user", None)
    st.session_state.pop("authenticated", None)
    controller.remove("user_session")
    st.rerun()


def _public(user: dict) -> dict:
    return {"id": user["_id"], "email": user["email"], "pseudo": user["pseudo"], "role": user["role"]}


def check_credentials(mode, login, password):
    if mode == "email":
        u = cs.get_user_by_email(login)
    elif mode == "pseudo":
        u = cs.get_user_by_pseudo(login)
    else:
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

    # 2. Vérification de l'existence du cookie (peut renvoyer None au tout
    #    premier chargement le temps que le composant JS se synchronise)
    user_from_cookie = controller.get("user_session")
    if user_from_cookie:
        try:
            user_dict = json.loads(user_from_cookie)
        except (TypeError, json.JSONDecodeError):
            user_dict = None
        if user_dict:
            st.session_state["authenticated"] = True
            st.session_state["user"] = user_dict
            return True

    # 3. Pas authentifié -> afficher le formulaire et ARRÊTER proprement
    #    (surtout pas de st.rerun() inconditionnel ici : ça boucle à l'infini
    #    et empêche toute interaction avec le bouton "Se connecter")
    st.subheader("Connexion requise")
    login_view()
    st.stop()


# ==========================================================================
# AUTHENTIFICATION
# ==========================================================================
def login_view():
    st.title("FESTIVAL JEUX DE CREPY")
    st.caption("Connectez-vous pour acceder aux applications du festival de jeux.")

    with st.form("j_login"):
        ps = st.text_input("pseudo")
        if not ps:
            ps = " "
        e = st.text_input("Email")
        if not e:
            e = " "
        p = st.text_input("Mot de passe", type="password")

        if st.form_submit_button("Se connecter", type="primary"):
            err = login(ps, e, p)
            if err:
                st.error(err)
            else:
                # On stocke l'utilisateur complet (JSON) dans le cookie,
                # pas juste le pseudo/email, pour restaurer une vraie session
                controller.set(
                    "user_session",
                    json.dumps(st.session_state["user"]),
                    max_age=86400 * 7,
                )
                st.rerun()

"""Logique d'authentification basée sur st.session_state."""
import streamlit as st
from email_validator import validate_email, EmailNotValidError

import storage
from config import get_secret
from security import generate_token


def current_user():
    return st.session_state.get("user")


def login(email: str, password: str):
    try:
        validate_email(email)
    except EmailNotValidError:
        return "Adresse email invalide"
    user = storage.check_credentials(email.strip(), password)
    if not user:
        return "Email ou mot de passe incorrect"
    st.session_state["user"] = _public(user)
    return None


def register(name: str, email: str, password: str):
    if len(name.strip()) < 1:
        return "Le nom est requis"
    if len(password) < 6:
        return "Le mot de passe doit contenir au moins 6 caractères"
    try:
        validate_email(email)
    except EmailNotValidError:
        return "Adresse email invalide"
    user, err = storage.create_user(email.strip(), name, password)
    if err:
        return err
    st.session_state["user"] = _public(user)
    return None


def logout():
    st.session_state.pop("user", None)


def request_reset(email: str):
    """Retourne (message_public, lien_debug). Réponse générique pour éviter l'énumération."""
    user = storage.get_user_by_email(email.strip())
    debug_link = None
    if user:
        token = generate_token()
        storage.create_reset_token(user["id"], token)
        base = str(get_secret("APP_URL", "http://localhost:8501")).rstrip("/")
        reset_url = f"{base}/?token={token}"
        from .email_utils import smtp_configured, send_reset_email
        if smtp_configured():
            send_reset_email(user["email"], reset_url)
        else:
            debug_link = reset_url
    return "Si le compte existe, un email de réinitialisation a été envoyé.", debug_link


def reset_password(token: str, new_password: str):
    if len(new_password) < 6:
        return "Le mot de passe doit contenir au moins 6 caractères"
    user_id, err = storage.consume_reset_token(token)
    if err:
        return err
    storage.update_password(user_id, new_password)
    return None


def _public(user: dict) -> dict:
    return {"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}





# ==========================================================================
# AUTHENTIFICATION
# ==========================================================================
def login_view():
    st.title("Présence Week-end")
    st.caption("Connectez-vous pour indiquer votre présence et vos tâches.")

    tab_login, tab_register, tab_forgot = st.tabs(
        ["Connexion", "Créer un compte", "Mot de passe oublié"]
    )

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Mot de passe", type="password", key="login_pwd")
            if st.form_submit_button("Se connecter", type="primary"):
                err = auth.login(email, password)
                if err:
                    st.error(err)
                else:
                    st.rerun()

    with tab_register:
        with st.form("register_form"):
            name = st.text_input("Nom", key="reg_name")
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Mot de passe (min. 6 caractères)", type="password", key="reg_pwd")
            if st.form_submit_button("S'inscrire", type="primary"):
                err = auth.register(name, email, password)
                if err:
                    st.error(err)
                else:
                    st.rerun()

    with tab_forgot:
        with st.form("forgot_form"):
            email = st.text_input("Votre email", key="forgot_email")
            if st.form_submit_button("Envoyer le lien de réinitialisation", type="primary"):
                msg, debug_link = auth.request_reset(email)
                st.success(msg)
                if debug_link:
                    st.warning("SMTP non configuré — lien de réinitialisation (mode dev) :")
                    st.code(debug_link)


def reset_password_view(token: str):
    st.title("Réinitialiser le mot de passe")
    with st.form("reset_form"):
        pwd1 = st.text_input("Nouveau mot de passe", type="password")
        pwd2 = st.text_input("Confirmer le mot de passe", type="password")
        if st.form_submit_button("Valider", type="primary"):
            if pwd1 != pwd2:
                st.error("Les mots de passe ne correspondent pas")
            else:
                err = auth.reset_password(token, pwd1)
                if err:
                    st.error(err)
                else:
                    st.success("Mot de passe réinitialisé. Vous pouvez vous connecter.")
                    st.link_button("Aller à la connexion", url=str(auth.get_secret("APP_URL", "/")))












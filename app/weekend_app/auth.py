"""Logique d'authentification basée sur st.session_state."""
import streamlit as st
from email_validator import validate_email, EmailNotValidError

from . import storage
from .config import get_secret
from .security import generate_token


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

"""Configuration & constantes de l'application."""
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

TASKS_FILE = DATA_DIR / "tasks.json"
USERS_FILE = DATA_DIR / "users.json"
PRESENCE_FILE = DATA_DIR / "presence.json"
RESET_TOKENS_FILE = DATA_DIR / "reset_tokens.json"



def get_secret(key: str, default=None):
    """Lit une valeur depuis st.secrets, sinon les variables d'environnement."""
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)

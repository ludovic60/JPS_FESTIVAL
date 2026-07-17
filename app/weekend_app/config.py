"""Configuration & constantes de l'application."""
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

TASKS_FILE = DATA_DIR / "tasks.json"
USERS_FILE = DATA_DIR / "users.json"
PRESENCE_FILE = DATA_DIR / "presence.json"
RESET_TOKENS_FILE = DATA_DIR / "reset_tokens.json"

DAYS = [("samedi", "Samedi"), ("dimanche", "Dimanche")]
PERIODS = [("matin", "Matinée"), ("apres_midi", "Après-midi"), ("soir", "Soirée")]
SLOT_KEYS = [f"{d}_{p}" for d, _ in DAYS for p, _ in PERIODS]

DAY_LABELS = dict(DAYS)
PERIOD_LABELS = dict(PERIODS)


def get_secret(key: str, default=None):
    """Lit une valeur depuis st.secrets, sinon les variables d'environnement."""
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)

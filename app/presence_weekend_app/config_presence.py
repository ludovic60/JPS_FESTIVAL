
"""Configuration & constantes de l'application."""
import os
from pathlib import Path


DAYS = [("samedi", "Samedi"), ("dimanche", "Dimanche")]
PERIODS = [("matin", "Matinée"), ("apres_midi", "Après-midi"), ("soir", "Soirée")]
SLOT_KEYS = [f"{d}_{p}" for d, _ in DAYS for p, _ in PERIODS]

DAY_LABELS = dict(DAYS)
PERIOD_LABELS = dict(PERIODS)


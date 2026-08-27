
"""Configuration & constantes de l'application."""
import os
from pathlib import Path

DAYS_INSTALL = [("vendredi", "Vendredi")]
PERIODS_INSTALL = [("apres_midi", "Après-midi")]
SLOT_KEYS_INSTALL = [f"{d}_{p}" for d, _ in DAYS_INSTALL for p, _ in PERIODS_INSTALL]
DAYS_ANIMATION = [("samedi", "Samedi"), ("dimanche", "Dimanche")]
PERIODS_ANIMATION = [("matin", "Matinée"), ("apres_midi", "Après-midi"), ("soir", "Soirée")]
SLOT_KEYS_ANIMATION = [f"{d}_{p}" for d, _ in DAYS_ANIMATION for p, _ in PERIODS_ANIMATION]

DAYS = DAYS_INSTALL + DAYS_ANIMATION
PERIODS = PERIODS_ANIMATION + PERIODS_INSTALL
SLOT_KEYS = SLOT_KEYS_ANIMATION + SLOT_KEYS_INSTALL

DAY_LABELS = dict(DAYS)
PERIOD_LABELS = dict(PERIODS)


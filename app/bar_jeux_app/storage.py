"""Stockage App2 (Bar à jeux) — utilisateurs & données mutables partagés via common_store.
Les listes de jeux restent des fichiers plats JSON nommés par mois (exigence)."""
import json
import uuid
from datetime import datetime, timezone
from threading import Lock

import common_store as cs
import os
import sys
# Ajoute le dossier parent à sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from weekend_app.security import hash_password, verify_password
import config

_lock = Lock()

_COVERS = [
    "https://images.unsplash.com/photo-1769288361029-187caa2a88a3?crop=entropy&cs=srgb&fm=jpg&q=85&w=400",
    "https://images.unsplash.com/photo-1637120149073-54319e6f9fc3?crop=entropy&cs=srgb&fm=jpg&q=85&w=400",
    "https://images.unsplash.com/photo-1772380405894-51b9728ecb88?crop=entropy&cs=srgb&fm=jpg&q=85&w=400",
    "https://images.pexels.com/photos/31916806/pexels-photo-31916806.jpeg?auto=compress&cs=tinysrgb&w=400",
]


def _read(path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def _make_game(**kw):
    g = {k: "" for k in config.GAME_KEYS}
    g.update(kw)
    g["id"] = kw.get("id_myludo") or uuid.uuid4().hex[:8]
    return g


def _sample(name, sub, players, age, duree, cover, note="7.8", nouv="Oui"):
    return _make_game(
        nom_jeu=name, nom_jeu_complet=f"{name}" + (f" — {sub}" if sub else ""),
        sous_titre=sub, nombre_joueurs=players, age_boite=age, duree=duree,
        couverture=cover, note_finale=note, est_nouveaute=nouv, langue_principale="Français",
        type_jeu="Jeu de société", url_myludo="https://www.myludo.fr/#!/games/news",
        description=f"{name} — un excellent jeu à découvrir au bar à jeux.",
    )


def init_storage():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    for key, _ in config.month_keys():
        if not config.games_file(key).exists():
            _write(config.games_file(key), [])
    if not _read(config.games_file("2025_10"), []):
        _write(config.games_file("2025_10"), [
            _sample("Wingspan", "Oiseaux", "1-5", "10+", "40-70 min", _COVERS[0], "8.1"),
            _sample("Ticket to Ride", "Europe", "2-5", "8+", "30-60 min", _COVERS[2], "7.9"),
            _sample("Tokyo Highway", "", "2-4", "8+", "30 min", _COVERS[1], "7.5", "Non"),
        ])
    if not _read(config.games_file("2025_11"), []):
        _write(config.games_file("2025_11"), [
            _sample("Splendor", "Duel", "2", "10+", "30 min", _COVERS[3], "7.6"),
        ])
    if not _read(config.games_file(config.VIEUX_KEY), []):
        _write(config.games_file(config.VIEUX_KEY), [
            _sample("Monopoly", "Classique", "2-6", "8+", "60-180 min", _COVERS[3], "5.5", "Non"),
            _sample("Carcassonne", "", "2-5", "7+", "35 min", _COVERS[0], "7.4", "Non"),
        ])




# ---- Jeux (fichiers plats) ----
def load_games(list_key):
    games = _read(config.games_file(list_key), [])
    for g in games:
        if "id" not in g:
            g["id"] = g.get("id_myludo") or uuid.uuid4().hex[:8]
    return games


# ---- Utilisateurs (partagés) ----
def get_users():
    return cs.get_users()


def get_user_by_email(email):
    return cs.get_user_by_email(email)

def get_user_by_pseudo(pseudo):
    return cs.get_user_by_pseudo(pseudo)

def _seed_user(email, pseudo, password, role="user"):
    u = {"id": uuid.uuid4().hex, "email": email.lower(), "pseudo": pseudo.strip(),
         "password_hash": hash_password(password), "role": role,
         "created_at": datetime.now(timezone.utc).isoformat()}
    cs.add_user(u)
    return u


def create_user(email, pseudo, password):
    if cs.get_user_by_email(email):
        return None, "Cet email est déjà utilisé"
    return _seed_user(email, pseudo, password), None


def check_credentials(mode, login, password):
    if mode == "email":
        u = cs.get_user_by_email(login)
    elif mode == "pseudo":
        u = cs.get_user_by_pseudo(login)
    else :
        u = None
    return u if u and verify_password(password, u["password_hash"]) else None


# ---- Sélection admin / suggestions / demandes / prêts (partagés) ----
def get_admin_selected():
    return set(cs.get_doc("jeux_admin_selected", []))


def toggle_admin_selected(ckey, value):
    sel = get_admin_selected()
    sel.add(ckey) if value else sel.discard(ckey)
    cs.put_doc("jeux_admin_selected", sorted(sel))


def get_suggestions():
    return cs.get_doc("jeux_suggestions", {})


def toggle_suggestion(ckey, user_id, value):
    s = get_suggestions()
    lst = set(s.get(ckey, []))
    lst.add(user_id) if value else lst.discard(user_id)
    s[ckey] = sorted(lst)
    cs.put_doc("jeux_suggestions", s)


def get_requests():
    return cs.get_doc("jeux_requests", [])


def add_request(name, myludo_url, list_key, by_name):
    reqs = get_requests()
    reqs.append({"id": uuid.uuid4().hex[:8], "name": name.strip(), "myludo_url": myludo_url.strip(),
                 "list_key": list_key, "by": by_name, "created_at": datetime.now(timezone.utc).isoformat()})
    cs.put_doc("jeux_requests", reqs)


def remove_request(req_id):
    cs.put_doc("jeux_requests", [r for r in get_requests() if r["id"] != req_id])


def all_list_keys():
    return [k for k, _ in config.month_keys()] + [config.VIEUX_KEY]


def final_games():
    sel = get_admin_selected()
    out = []
    for lk in all_list_keys():
        for g in load_games(lk):
            ckey = f"{lk}::{g['id']}"
            if ckey in sel:
                out.append((ckey, g))
    return out


def get_loans():
    return cs.get_doc("jeux_loans", {})


def toggle_loan(ckey, user_id, value):
    loans = get_loans()
    lst = set(loans.get(ckey, []))
    lst.add(user_id) if value else lst.discard(user_id)
    loans[ckey] = sorted(lst)
    cs.put_doc("jeux_loans", loans)


def set_loan(ckey, user_id, value):
    toggle_loan(ckey, user_id, value)

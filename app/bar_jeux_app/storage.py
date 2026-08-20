"""Stockage fichiers plats JSON pour Bar à jeux."""
import json
import uuid
from datetime import datetime, timezone
from threading import Lock

from weekend_app.security import hash_password, verify_password
from . import config

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
    for f, default in [
        (config.ADMIN_SELECTED_FILE, []),
        (config.SUGGESTIONS_FILE, {}),
        (config.REQUESTS_FILE, []),
        (config.LOANS_FILE, {}),
        (config.USERS_FILE, []),
    ]:
        if not f.exists():
            _write(f, default)

    # Fichiers mensuels + vieux
    for key, _ in config.month_keys():
        if not config.games_file(key).exists():
            _write(config.games_file(key), [])
    # Exemples de jeux
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
    if not config.games_file(config.VIEUX_KEY).exists() or not _read(config.games_file(config.VIEUX_KEY), []):
        _write(config.games_file(config.VIEUX_KEY), [
            _sample("Monopoly", "Classique", "2-6", "8+", "60-180 min", _COVERS[3], "5.5", "Non"),
            _sample("Carcassonne", "", "2-5", "7+", "35 min", _COVERS[0], "7.4", "Non"),
        ])

    admin_email = str(config.__dict__.get("_", "")) or "admin@barajeux.fr"
    from weekend_app.config import get_secret
    admin_email = str(get_secret("JEUX_ADMIN_EMAIL", "admin@barajeux.fr")).lower()
    admin_password = str(get_secret("JEUX_ADMIN_PASSWORD", "admin123"))
    if get_user_by_email(admin_email) is None:
        _add_user_raw(admin_email, "Administrateur", admin_password, role="admin")
    # Membres prédéterminés
    for nm, em in [("Alice", "alice@barajeux.fr"), ("Bob", "bob@barajeux.fr"), ("Chloé", "chloe@barajeux.fr")]:
        if get_user_by_email(em) is None:
            _add_user_raw(em, nm, "membre123", role="user")


# ---- Jeux ----
def load_games(list_key):
    games = _read(config.games_file(list_key), [])
    for g in games:
        if "id" not in g:
            g["id"] = g.get("id_myludo") or uuid.uuid4().hex[:8]
    return games


# ---- Utilisateurs ----
def get_users():
    return _read(config.USERS_FILE, [])


def get_user_by_email(email):
    email = email.lower()
    return next((u for u in get_users() if u["email"] == email), None)


def _add_user_raw(email, name, password, role="user"):
    users = get_users()
    u = {"id": uuid.uuid4().hex, "email": email.lower(), "name": name.strip(),
         "password_hash": hash_password(password), "role": role,
         "created_at": datetime.now(timezone.utc).isoformat()}
    users.append(u)
    _write(config.USERS_FILE, users)
    return u


def create_user(email, name, password):
    if get_user_by_email(email):
        return None, "Cet email est déjà utilisé"
    return _add_user_raw(email, name, password), None


def check_credentials(email, password):
    u = get_user_by_email(email)
    return u if u and verify_password(password, u["password_hash"]) else None


# ---- Sélection admin (clé composite "listkey::gameid") ----
def get_admin_selected():
    return set(_read(config.ADMIN_SELECTED_FILE, []))


def toggle_admin_selected(ckey, value):
    sel = get_admin_selected()
    sel.add(ckey) if value else sel.discard(ckey)
    _write(config.ADMIN_SELECTED_FILE, sorted(sel))


# ---- Suggestions utilisateurs ----
def get_suggestions():
    return _read(config.SUGGESTIONS_FILE, {})


def toggle_suggestion(ckey, user_id, value):
    s = get_suggestions()
    lst = set(s.get(ckey, []))
    lst.add(user_id) if value else lst.discard(user_id)
    s[ckey] = sorted(lst)
    _write(config.SUGGESTIONS_FILE, s)


# ---- Demandes d'ajout ----
def get_requests():
    return _read(config.REQUESTS_FILE, [])


def add_request(name, myludo_url, list_key, by_name):
    reqs = get_requests()
    reqs.append({"id": uuid.uuid4().hex[:8], "name": name.strip(), "myludo_url": myludo_url.strip(),
                 "list_key": list_key, "by": by_name, "created_at": datetime.now(timezone.utc).isoformat()})
    _write(config.REQUESTS_FILE, reqs)


def remove_request(req_id):
    _write(config.REQUESTS_FILE, [r for r in get_requests() if r["id"] != req_id])


# ---- Liste finale + prêts ----
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
    return _read(config.LOANS_FILE, {})


def toggle_loan(ckey, user_id, value):
    loans = get_loans()
    lst = set(loans.get(ckey, []))
    lst.add(user_id) if value else lst.discard(user_id)
    loans[ckey] = sorted(lst)
    _write(config.LOANS_FILE, loans)


def set_loan(ckey, user_id, value):
    toggle_loan(ckey, user_id, value)

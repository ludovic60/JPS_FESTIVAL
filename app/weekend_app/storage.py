"""Couche de stockage en fichiers plats JSON.

Abstraction volontairement simple : chaque entité est un fichier JSON.
Pour migrer vers MongoDB Atlas plus tard, il suffit de réimplémenter
ces fonctions avec pymongo sans toucher au reste de l'application.
"""
import json
import uuid
from datetime import datetime, timezone, timedelta
from threading import Lock

from . import config
from .security import hash_password, verify_password, token_hash

_lock = Lock()


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


# --------------------------------------------------------------------------
# Initialisation / seed
# --------------------------------------------------------------------------
def init_storage():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not config.TASKS_FILE.exists():
        _write(config.TASKS_FILE, [])
    if not config.USERS_FILE.exists():
        _write(config.USERS_FILE, [])
    if not config.PRESENCE_FILE.exists():
        _write(config.PRESENCE_FILE, {})
    if not config.RESET_TOKENS_FILE.exists():
        _write(config.RESET_TOKENS_FILE, {})

    admin_email = str(config.get_secret("ADMIN_EMAIL", "admin@weekend.fr")).lower()
    admin_password = str(config.get_secret("ADMIN_PASSWORD", "admin123"))
    if get_user_by_email(admin_email) is None:
        _add_user_raw(admin_email, "Administrateur", admin_password, role="admin")


# --------------------------------------------------------------------------
# Tâches (fichier plat lu par l'application)
# --------------------------------------------------------------------------
def get_tasks():
    return _read(config.TASKS_FILE, [])


def add_task(label: str):
    tasks = get_tasks()
    task = {"id": uuid.uuid4().hex[:8], "label": label.strip()}
    tasks.append(task)
    tasks.sort(key=lambda t: t["label"].lower())
    _write(config.TASKS_FILE, tasks)
    return task


def update_task(task_id: str, label: str):
    tasks = get_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["label"] = label.strip()
    tasks.sort(key=lambda t: t["label"].lower())
    _write(config.TASKS_FILE, tasks)


def delete_task(task_id: str):
    tasks = [t for t in get_tasks() if t["id"] != task_id]
    _write(config.TASKS_FILE, tasks)
    presence = get_all_presence()
    for p in presence.values():
        p["task_ids"] = [tid for tid in p.get("task_ids", []) if tid != task_id]
    _write(config.PRESENCE_FILE, presence)


# --------------------------------------------------------------------------
# Utilisateurs
# --------------------------------------------------------------------------
def get_users():
    return _read(config.USERS_FILE, [])


def get_user_by_email(email: str):
    email = email.lower()
    for u in get_users():
        if u["email"] == email:
            return u
    return None


def get_user_by_id(user_id: str):
    for u in get_users():
        if u["id"] == user_id:
            return u
    return None


def _add_user_raw(email, name, password, role="user"):
    users = get_users()
    user = {
        "id": uuid.uuid4().hex,
        "email": email.lower(),
        "name": name.strip(),
        "password_hash": hash_password(password),
        "role": role,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    users.append(user)
    _write(config.USERS_FILE, users)
    return user


def create_user(email, name, password):
    if get_user_by_email(email):
        return None, "Cet email est déjà utilisé"
    user = _add_user_raw(email, name, password, role="user")
    return user, None


def check_credentials(email, password):
    user = get_user_by_email(email)
    if user and verify_password(password, user["password_hash"]):
        return user
    return None


def update_password(user_id: str, new_password: str):
    users = get_users()
    for u in users:
        if u["id"] == user_id:
            u["password_hash"] = hash_password(new_password)
    _write(config.USERS_FILE, users)


# --------------------------------------------------------------------------
# Présence / votes
# --------------------------------------------------------------------------
def get_all_presence():
    return _read(config.PRESENCE_FILE, {})


def get_presence(user_id: str):
    p = get_all_presence().get(user_id)
    slots = {k: False for k in config.SLOT_KEYS}
    task_ids = []
    if p:
        slots.update({k: bool(v) for k, v in p.get("slots", {}).items() if k in config.SLOT_KEYS})
        task_ids = p.get("task_ids", [])
    return {"slots": slots, "task_ids": task_ids}


def set_presence(user_id: str, user_name: str, slots: dict, task_ids: list):
    presence = get_all_presence()
    clean = {k: bool(slots.get(k, False)) for k in config.SLOT_KEYS}
    presence[user_id] = {
        "user_name": user_name,
        "slots": clean,
        "task_ids": task_ids,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _write(config.PRESENCE_FILE, presence)


def clear_all_presence():
    _write(config.PRESENCE_FILE, {})


def clear_user_presence(user_id: str):
    presence = get_all_presence()
    presence.pop(user_id, None)
    _write(config.PRESENCE_FILE, presence)


# --------------------------------------------------------------------------
# Jetons de réinitialisation
# --------------------------------------------------------------------------
def create_reset_token(user_id: str, token: str, hours: int = 1):
    tokens = _read(config.RESET_TOKENS_FILE, {})
    tokens[token_hash(token)] = {
        "user_id": user_id,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat(),
        "used": False,
    }
    _write(config.RESET_TOKENS_FILE, tokens)


def consume_reset_token(token: str):
    tokens = _read(config.RESET_TOKENS_FILE, {})
    rec = tokens.get(token_hash(token))
    if not rec or rec.get("used"):
        return None, "Jeton invalide ou déjà utilisé"
    if datetime.now(timezone.utc) > datetime.fromisoformat(rec["expires_at"]):
        return None, "Jeton expiré"
    rec["used"] = True
    _write(config.RESET_TOKENS_FILE, tokens)
    return rec["user_id"], None

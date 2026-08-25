"""Stockage App1 (Présence Week-end) — utilisateurs & données partagés via common_store,
tâches conservées en fichier plat (data/tasks.json)."""
import json
import uuid
from datetime import datetime, timezone, timedelta
from threading import Lock


import sys
from pathlib import Path

# Ajoute le dossier parent (la racine du projet) à sys.path
racine_projet = Path(__file__).resolve().parent.parent
sys.path.append(str(racine_projet))
import commun.common_store as cs
from commun.design_system import inject
from commun.auth import require_auth, logout
import commun.config as cfg
from commun.security import hash_password, verify_password, token_hash



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


def init_storage():
    cfg.DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not config.TASKS_FILE.exists():
        _write(config.TASKS_FILE, [])
    admin_email = str(cfg.get_secret("ADMIN_EMAIL", "admin@weekend.fr")).lower()
    admin_password = str(cfg.get_secret("ADMIN_PASSWORD", "admin123"))
    if cs.get_user_by_email(admin_email) is None:
        _seed_user(admin_email, "Administrateur", admin_password, role="admin")


# ---- Tâches (fichier plat) ----
def get_tasks():
    return _read(config.TASKS_FILE, [])


def add_task(label):
    tasks = get_tasks()
    task = {"id": uuid.uuid4().hex[:8], "label": label.strip()}
    tasks.append(task)
    tasks.sort(key=lambda t: t["label"].lower())
    _write(config.TASKS_FILE, tasks)
    return task


def update_task(task_id, label):
    tasks = get_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["label"] = label.strip()
    tasks.sort(key=lambda t: t["label"].lower())
    _write(config.TASKS_FILE, tasks)


def delete_task(task_id):
    _write(config.TASKS_FILE, [t for t in get_tasks() if t["id"] != task_id])
    presence = get_all_presence()
    for p in presence.values():
        p["task_ids"] = [tid for tid in p.get("task_ids", []) if tid != task_id]
    cs.put_doc("weekend_presence", presence)


# ---- Utilisateurs (partagés) ----
def get_users():
    return cs.get_users()


def get_user_by_email(email):
    return cs.get_user_by_email(email)


def get_user_by_id(uid):
    return cs.get_user_by_id(uid)


def _seed_user(email, name, password, role="user"):
    u = {"id": uuid.uuid4().hex, "email": email.lower(), "name": name.strip(),
         "password_hash": hash_password(password), "role": role,
         "created_at": datetime.now(timezone.utc).isoformat()}
    cs.add_user(u)
    return u


def create_user(email, name, password):
    if cs.get_user_by_email(email):
        return None, "Cet email est déjà utilisé"
    return _seed_user(email, name, password, role="user"), None


def check_credentials(email, password):
    u = cs.get_user_by_email(email)
    return u if u and verify_password(password, u["password_hash"]) else None


def update_password(user_id, new_password):
    cs.update_password(user_id, hash_password(new_password))


# ---- Présence (partagée) ----
def get_all_presence():
    return cs.get_doc("weekend_presence", {})


def get_presence(user_id):
    p = get_all_presence().get(user_id)
    slots = {k: False for k in config.SLOT_KEYS}
    task_ids = []
    if p:
        slots.update({k: bool(v) for k, v in p.get("slots", {}).items() if k in config.SLOT_KEYS})
        task_ids = p.get("task_ids", [])
    return {"slots": slots, "task_ids": task_ids}


def set_presence(user_id, user_name, slots, task_ids):
    presence = get_all_presence()
    presence[user_id] = {"user_name": user_name,
                         "slots": {k: bool(slots.get(k, False)) for k in config.SLOT_KEYS},
                         "task_ids": task_ids,
                         "updated_at": datetime.now(timezone.utc).isoformat()}
    cs.put_doc("weekend_presence", presence)


def clear_all_presence():
    cs.put_doc("weekend_presence", {})


def clear_user_presence(user_id):
    presence = get_all_presence()
    presence.pop(user_id, None)
    cs.put_doc("weekend_presence", presence)


# ---- Jetons de réinitialisation (partagés) ----
def create_reset_token(user_id, token, hours=1):
    tokens = cs.get_doc("weekend_reset_tokens", {})
    tokens[token_hash(token)] = {
        "user_id": user_id,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat(),
        "used": False,
    }
    cs.put_doc("weekend_reset_tokens", tokens)


def consume_reset_token(token):
    tokens = cs.get_doc("weekend_reset_tokens", {})
    rec = tokens.get(token_hash(token))
    if not rec or rec.get("used"):
        return None, "Jeton invalide ou déjà utilisé"
    if datetime.now(timezone.utc) > datetime.fromisoformat(rec["expires_at"]):
        return None, "Jeton expiré"
    rec["used"] = True
    cs.put_doc("weekend_reset_tokens", tokens)
    return rec["user_id"], None

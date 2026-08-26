"""Couche de stockage partagée entre les applications.

- Si MONGO_URL est défini (secrets/env) -> MongoDB (Atlas ou local) : les UTILISATEURS
  et les DONNÉES applicatives sont partagés entre toutes les apps utilisant la même base.
- Sinon -> repli sur des fichiers plats JSON dans data/_store/ (utilisateurs partagés
  dans un même fichier).

Les utilisateurs sont dans la collection commune `users` ;
les données applicatives mutables dans `app_data` sous forme {_id: <nom>, data: <...>}.
"""
import json
import os
from pathlib import Path

from bson import ObjectId

try:
    import streamlit as st
except Exception:
    st = None

ROOT = Path(__file__).resolve().parent
FALLBACK_DIR = ROOT / "data" / "_store"


def _secret(key, default=None):
    if st is not None:
        try:
            if key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass
    return os.environ.get(key, default)


_client = None


def get_db():
    global _client
    url = _secret("MONGO_URL")
    if not url:
        return None
    if _client is None:
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi
        _client = MongoClient(url, server_api=ServerApi('1'), serverSelectionTimeoutMS=4000)
    return _client[_secret("DB_NAME", "shared_apps")]


def mongo_enabled():
    try:
        return get_db() is not None
    except Exception:
        return False


# --------------------------------------------------------------------------
# Données applicatives génériques (partagées quand Mongo est actif)
# --------------------------------------------------------------------------
# def get_doc(name, default):
#     db = get_db()
#     if db is not None:
#         d = db.app_data.find_one({"_id": name})
#         return d["data"] if d else default
#     p = FALLBACK_DIR / f"{name}.json"
#     if not p.exists():
#         return default
#     try:
#         with open(p, "r", encoding="utf-8") as f:
#             return json.load(f)
#     except (json.JSONDecodeError, OSError):
#         return default


# def put_doc(name, data):
#     db = get_db()
#     if db is not None:
#         db.app_data.update_one({"_id": name}, {"$set": {"data": data}}, upsert=True)
#         return
#     FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
#     with open(FALLBACK_DIR / f"{name}.json", "w", encoding="utf-8") as f:
#        json.dump(data, f, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------
# Utilisateurs (base commune)
# --------------------------------------------------------------------------
def _clean(u):
    u = dict(u)
    # u.pop("_id", None)
    return u


def get_users():
    db = get_db()
    if db is not None:
        return [_clean(u) for u in db.users.find()]
    return get_doc("shared_users", [])


def get_user_by_email(email):
    email = email.strip().lower()
    return next(
        (u for u in get_users() if u.get("email", "").strip().lower() == email),
        None,
    )


def get_user_by_pseudo(pseudo):
    pseudo = pseudo.strip().lower()
    return next(
        (u for u in get_users() if u.get("pseudo", "").strip().lower() == pseudo),
        None,
    )


def get_user_by_id(uid):
    return next((u for u in get_users() if str(u["_id"]) == str(uid)), None)


def add_user(user: dict):
    db = get_db()
    if db is not None:
        db.users.insert_one(dict(user))
        return
    users = get_doc("shared_users", [])
    users.append(user)
    put_doc("shared_users", users)


def update_password(uid, new_hash):
    db = get_db()
    if db is not None:
        db.users.update_one({"_id": ObjectId(uid)}, {"$set": {"password_hash": new_hash}})
        return
    users = get_doc("shared_users", [])
    for u in users:
        if str(u["_id"]) == str(uid):
            u["password_hash"] = new_hash
    put_doc("shared_users", users)

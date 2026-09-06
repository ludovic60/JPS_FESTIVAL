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
from datetime import datetime
from bson import ObjectId

try:
    import streamlit as st
except Exception:
    st = None

ROOT = Path(__file__).resolve().parent
FALLBACK_DIR = ROOT / "data" / "_store"




# Obtenir la date exacte au format complet du système
today = datetime.now()



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
# Utilisateurs (base commune)
# --------------------------------------------------------------------------
def _clean(u):
    u = dict(u)
    # u.pop("_id", None)
    return u



def get_users_loaner():
    db = get_db()
    if db is not None:
        filtre_tb = {"role": {"$ne":"admin"} ,
                     "prete_jeu" :"true" , 
                     "$or": [
                        {"desactived_at": ""},
                        {"desactived_at": None},  # Bonne pratique : inclure les valeurs nulles ou absentes
                        {"desactived_at": {"$gte": today}}
                       ]
                    }
        return [_clean(u) for u in db.users.find(filtre_tb)]
    return get_doc("shared_users", [])

def get_users_non_admin():
    db = get_db()
    if db is not None:
        filtre_tb = {"role": {"$ne":"admin"},         
                     "$or": [
                        {"desactived_at": ""},
                        {"desactived_at": None},  # Bonne pratique : inclure les valeurs nulles ou absentes
                        {"desactived_at": {"$gte": today}}
                       ]
                    }
                    
        return [_clean(u) for u in db.users.find(filtre_tb)]
    return get_doc("shared_users", [])

def get_users():
    db = get_db()
    if db is not None:
        filtre_tb = {"$or": [
                        {"desactived_at": ""},
                        {"desactived_at": None},  # Bonne pratique : inclure les valeurs nulles ou absentes
                        {"desactived_at": {"$gte": today}}
                       ]
                    }
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

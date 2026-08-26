"""Stockage App1 (Présence Week-end) — utilisateurs & données partagés via common_store,
tâches conservées en fichier plat (data/tasks.json)."""
import json
import uuid
from datetime import datetime, timezone, timedelta
from threading import Lock
from bson import ObjectId
import config_presence as cfg_pres


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


# def _read(path, default):
#     if not path.exists():
#         return default
#     try:
#         with open(path, "r", encoding="utf-8") as f:
#             return json.load(f)
#     except (json.JSONDecodeError, OSError):
#         return default


# def _write(path, data):
#     path.parent.mkdir(parents=True, exist_ok=True)
#     with _lock:
#         with open(path, "w", encoding="utf-8") as f:
#             json.dump(data, f, ensure_ascii=False, indent=2)


# def init_storage():
#     cfg.DATA_DIR.mkdir(parents=True, exist_ok=True)
#     if not cfg.TASKS_FILE.exists():
#         _write(cfg.TASKS_FILE, [])
#     admin_email = str(cfg._secret("ADMIN_EMAIL", "admin@weekend.fr")).lower()
#     admin_password = str(cfg.get_secret("ADMIN_PASSWORD", "admin123"))
#     if cs.get_user_by_email(admin_email) is None:
#         _seed_user(admin_email, "Administrateur", admin_password, role="admin")


# ----  gestion de la table Tâche  ----

def get_tasks():
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        tasks_tb = db.taches
        filtre_tb = {}
        selc_tb = {"tache": 1, "_id": 2}
        resultats = list(tasks_tb.find(filtre_tb, selc_tb))
       
    else :
        resultats ={}
    return resultats


def add_task(label):
    tasks = get_tasks()
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        tasks_tb = db.taches
        new_task = {"_id": str(ObjectId()), "tache": label.strip()}
        filtre_tb = {}
        ins_tb = {}
        resultat = tasks_tb.insert_one(new_task)
     



def update_task(task_id, label):
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        tasks_tb = db.taches
    
        upd_task_id = ObjectId(task_id)
    
        resultats =  tasks_tb.update_one({"_id": upd_task_id}, {"$set": {"tache": label}})
 


def delete_task(task_id):
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        tasks_tb = db.taches
    
        del_task_id = ObjectId(task_id)
        resultats =  tasks_tb.delete_one({"_id": del_task_id})
 


    



# ---- Présence (partagée) ----
def get_all_presence():
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        presence_tb = db.presence
      
        filtre_tb = {"annne": cs._secret("ANNEE_FESTIVAL")}
        selc_tb = { "user_id":1 ,"pseudo" :2,  "creneau": 3,"task_ids": 4, "_id": 0}
        resultats = list(presence_tb.find(filtre_tb, selc_tb))

    else :
        resultats ={}
    return resultats 


def get_presence(user_id):
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        presence_tb = db.presence
        filtre_tb = {"annne": cs._secret("ANNEE_FESTIVAL") , "user_id" : ObjectId(user_id)}
        selc_tb = { "creneau": 1,"task_ids": 2}
        resultats = list(presence_tb.find(filtre_tb, selc_tb))
 
    else :
        resultats ={}
    return resultats 
    
def set_presence(user_id, pseudo, slots, task_ids):
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        presence_tb = db.presence
        ## supprime ancienne presences en base au prealable
        clear_user_presence(user_id)
        new_presence= {"_id": ObjectId(), 
                     "annee" : cs._secret("ANNEE_FESTIVAL"), 
                     "user_id": ObjectId(user_id),
                     "pseudo" : pseudo,
                     "creneau": {k: bool(slots.get(k, False)) for k in cfg_pres.SLOT_KEYS},
                     "task_ids": task_ids,
                     "updated_at": datetime.now(timezone.utc).isoformat()}
    
    
        resultat = presence_tb.insert_one(new_presence)

    else :
        resultat ={}
    return resultat 
    

def clear_all_presence():
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        presence_tb = db.presence
        filtre_tb = {"annne": cs._secret("ANNEE_FESTIVAL") }
        
        resultats = presence_tb.delete_many(filtre_tb)




def clear_user_presence(user_id):
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        presence_tb = db.presence
    
        filtre_tb = {"annne": cs._secret("ANNEE_FESTIVAL"),"user_id" : ObjectId(user_id) }
        
        resultats = presence_tb.delete_many(filtre_tb)


    


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

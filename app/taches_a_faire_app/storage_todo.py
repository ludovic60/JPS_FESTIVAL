
"""Stockage App1 (Présence Week-end) — utilisateurs & données partagés via common_store,
tâches conservées en fichier plat (data/tasks.json)."""
import json
import uuid
from datetime import datetime, timezone, timedelta
from threading import Lock
from bson import ObjectId



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




# ----  gestion de la table Tâche  ----

def get_todo(mode):
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        todo_tb = db.todo
        filtre_tb = {}
        selc_tb = {"todo": 1, "_id": 1, "statut":1, "affecte":1, "pourcentage avancement":1}
        if mode == "CLOSED" :
            filtre_tb = {}
        elif mode == "OEND" :
        resultats = list(todo_tb.find(filtre_tb, selc_tb))
       
    else :
        resultats ={}
    return resultats


def add_todo(label):

    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        todo_tb = db.todo
        new_todo = {"_id": ObjectId(), "todo": label.strip() ,"affecte": "", "statut":"a faire"}
        filtre_tb = {}
        ins_tb = {}
        resultat = todo_tb.insert_one(new_todo)
     



def update_todo(todo_id, affectation, newstatut):
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        todo_tb = db.todo
    
        upd_todo_id = ObjectId(todo_id)
    
        resultats =  todo_tb.update_one({"_id": upd_todo_id}, {"$set": {"affecte": affectation, "statut": newstatut} })
 


def delete_todo(todo_id):
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        todo_tb = db.todo
    
        del_todo_id = ObjectId(todo_id)
        resultats =  todo_tb.delete_one({"_id": del_todo_id})
 


    

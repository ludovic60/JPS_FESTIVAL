"""Stockage App2 (Bar à jeux) — utilisateurs & données mutables partagés via common_store.
Les listes de jeux restent des fichiers plats JSON nommés par mois (exigence)."""
import json
import uuid
from datetime import datetime, timezone
from threading import Lock
import config_bar_jeux
from bson import ObjectId

import os
import sys
# Ajoute le dossier parent à sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import commun.common_store as cs
from commun.security import hash_password, verify_password
import commun.config as ccfg

_lock = Lock()

_COVERS = [
    "https://images.unsplash.com/photo-1769288361029-187caa2a88a3?crop=entropy&cs=srgb&fm=jpg&q=85&w=400",
    "https://images.unsplash.com/photo-1637120149073-54319e6f9fc3?crop=entropy&cs=srgb&fm=jpg&q=85&w=400",
    "https://images.unsplash.com/photo-1772380405894-51b9728ecb88?crop=entropy&cs=srgb&fm=jpg&q=85&w=400",
    "https://images.pexels.com/photos/31916806/pexels-photo-31916806.jpeg?auto=compress&cs=tinysrgb&w=400",
]





# ---- Jeux (fichiers plats) ----
def load_games(list_key):
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_tb = db.jeux
        if list_key == "est_selectionnable":
            filtre_tb = {"est_selectionnable": list_key}
        else :
            annee = list_key[:4]
            mois = list_key[5:]
            #gestion des numeros de mois avant octobre pour n'avoir qu'un chiffre
            if mois[0]=="0":
                mois = mois[1]
            print(annee)
            print(mois)
            filtre_tb = {"annee_parution" : annee , "mois_sortie" : mois }
        
        resultats = list(game_tb.find(filtre_tb))
    else :
        resultats ={}
    return resultats 
    

# ---- Sélection admin / suggestions / demandes / prêts (partagés) ----

def set_selection_game():
    #selection_jeux_festival
    return {}    
    
def get_admin_selected():
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_selec_tb = db.selection_jeux_festival
        filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL")  }
        
        resultats = list(game_selec_tb .find(filtre_tb))
    else :
        resultats ={}
    return resultats 


    

def toggle_admin_selected(ckey, value):
    #sel = get_admin_selected()
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_selec_tb = db.selection_jeux_festival

    if value :
        new_selection= {         
                     "annee" : cs._secret("ANNEE_FESTIVAL"), 
                     "id_jeux": str(ObjectId(ckey))
           }   
    
        resultat = game_selec_tb.insert_one(new_selection)
    else :  
        # deselectionne le jeu 

        filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL"), "id_jeux": str(ObjectId(ckey)) }
        resultat = game_selec_tb.delete_many(filtre_tb)
    

def get_suggestions():
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_suggest_tb = db.jeux_suggestions
        filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL")  }
        
        resultats = list(game_suggest_tb.find(filtre_tb))
    else :
        resultats ={}
    return resultats 


def toggle_suggestion(ckey, user_id, value):
    #s = get_suggestions()
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_suggest_tb = db.jeux_suggestions

    if value :
        new_selection= {         
            "annee" : cs._secret("ANNEE_FESTIVAL"), 
            "periode_jeu" : "",
            "id_jeux": str(ObjectId(ckey)),
            "user_id": str(ObjectId(user_id)),
            "statut" : "a traiter"
        
        }
         
        resultat = game_suggest_tb.insert_one(new_selection)
    else :  
        # deselectionne le jeu 
        filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL"), "periode_jeu" : "" , "id_jeux": str(ObjectId(ckey)),   "user_id": str(ObjectId(user_id)) }
        resultat = game_suggest_tb.delete_many(filtre_tb)
    
    
    


def get_requests(type_request):
    con_mongo = cs.mongo_enabled()
    if type_request == "ajout jeux" :
        if   con_mongo : 
            db = cs.get_db()
            resquest_tb = db.demandes
            filtre_tb = {"type" : "ajout jeux"  }
            
            resultats = list(resquest_tb.find(filtre_tb))
    elif type_request == "remarque fiche jeux" :
        if   con_mongo : 
            db = cs.get_db()
            resquest_tb = db.demandes
            filtre_tb = {"type" : "remarque fiche jeux"  }
            
            resultats = list(resquest_tb.find(filtre_tb))
    else :
         resultats ={}
    return resultats 


def add_request(type_request, game_name, myludo_url, comments, by_name):
    # reqs = get_requests()

    con_mongo = cs.mongo_enabled()
    if type_request == "ajout jeux" :
        if   con_mongo : 
            db = cs.get_db()
            resquest_tb = db.demandes
            new_request= {                    
                    "id_request": str(ObjectId()),
                    "annee" : cs._secret("ANNEE_FESTIVAL"), 
                    "type_request" : "ajout jeux", 
                    "game_name": name.strip(), 
                    "myludo_url": myludo_url.strip(),
                    "comments" : "",
                    "created_by": by_name,
                    "created_at": datetime.now(timezone.utc).isoformat()
            }   
            resultat = resquest_tb.insert_one(new_request)
    elif type_request == "remarque fiche jeux" :
        if   con_mongo : 
            db = cs.get_db()
            resquest_tb = db.demandes
            new_request= {                    
                    "id_request": str(ObjectId()),
                    "annee" : cs._secret("ANNEE_FESTIVAL"),
                    "type_request" : "remarque fiche jeux", 
                    "game_name": name.strip(), 
                    "myludo_url": "",
                    "comments" :comments,
                    "created_by": by_name,
                    "created_at": datetime.now(timezone.utc).isoformat()
            }   
            resultat = resquest_tb.insert_one(new_request)


def remove_request(type_request, req_id):
 con_mongo = cs.mongo_enabled()
 if   con_mongo : 
    db = cs.get_db()
    resquest_tb = db.demandes                                              
    filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL"), "type_request" : type_request,   "id_request": str(ObjectId(req_id)) }
    resultat = resquest_tb.delete_many(filtre_tb)
        


def all_list_keys():
    return [k for k, _ in config_bar_jeux.month_keys()] + [config_bar_jeux.VIEUX_KEY]


def final_games():
    sel = get_admin_selected()
    out = []
    for lk in all_list_keys():
        for g in load_games(lk):
            ckey = f"{lk}::{g["_id"]}"
            if ckey in sel:
                out.append((ckey, g))
    return out


def get_loans():
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_loan_tb = db.prets_jeux
        filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL") }  
        resultats = list(game_loan_tb.find(filtre_tb))


def toggle_loan(ckey, user_id, value):
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_loan_tb = db.prets_jeux

        if value :
            new_loan= {         
                         "annee" : cs._secret("ANNEE_FESTIVAL"), 
                         "id_jeux": str(ObjectId(ckey)),
                         "user_id": str(ObjectId(user_id))
               }   
        
            resultat = game_loan_tb.insert_one(new_loan)
        else :  
            # deselectionne le jeu 
    
            filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL"), "id_jeux": str(ObjectId(ckey)),"user_id":str((ObjectId(user_id)))}
            resultat = game_loan_tb.delete_many(filtre_tb)


def set_loan(ckey, user_id, value):
    return {}

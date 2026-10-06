"""Stockage App2 (Bar à jeux) — utilisateurs & données mutables partagés via common_store.
Les listes de jeux restent des fichiers plats JSON nommés par mois (exigence)."""
import logging
import json
import uuid
from datetime import datetime, timezone
from threading import Lock
import config_bar_jeux
from bson import ObjectId

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
import pandas as pd


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


import streamlit as st


##############################################################
# ---- requetes  sur la base de données des jeux : JEUX  ----
##############################################################
def load_games(list_key, search_query=None):
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_tb = db.jeux
        
        if search_query:
                regex_pattern = {"$regex": search_query, "$options": "i"}
                filtre_tb ={"$or": [  {"nom_jeu_complet": regex_pattern},
                                     {"nom_jeu": regex_pattern},
                                     {"url_myludo": regex_pattern}]}
         
        else :
        
            if list_key == "est_selectionnable":
                filtre_tb = {"est_selectionnable": list_key}
  
            elif list_key == "all":
                filtre_tb = {}    
               
            elif len(list_key) <=7 :
              
                if datetime.strptime(list_key, "%Y_%m"): 
                        annee = list_key[:4]
                        mois = list_key[5:]
                        #gestion des numeros de mois avant octobre pour n'avoir qu'un chiffre
                        if mois[0]=="0":
                            mois = mois[1]
            
                        filtre_tb = {"annee_parution" : annee , "mois_sortie" : mois }
                   
                else : 
                        filtre_tb= {"_id": {"$in": list_key}}
                       
            else :
                filtre_tb= {"_id": {"$in": list_key}}

        
        resultats = list(game_tb.find(filtre_tb).sort({"nom_jeu_fichier":1}))
    else :
        resultats ={}
    return resultats 

def get_info_games(id_game):
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_tb = db.jeux
        filtre_tb = {"_id" : (ObjectId(id_game))  }
        
        resultats = list(game_tb.find(filtre_tb))
    else :
        resultats ={}
    return resultats 
    

##########################################################################
# ---- requetes  sur les jeux selectionnés : selection_jeux_festival  ----
##########################################################################
def final_games():
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_selec_tb = db.selection_jeux_festival
        selc_tb = {"id_jeux": 1}
        filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL") }  
        resultats = list(game_selec_tb.find( filtre_tb, selc_tb ))
    return resultats 



def final_games_statut_plusieurs_exemplaire():
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_selec_tb = db.selection_jeux_festival
        selc_tb = {"id_jeux": 1}
        filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL") , "plusieurs_exemplaires_souhaites": str("True") }  
        resultats = list(game_selec_tb.find( filtre_tb, selc_tb ))
    return resultats 

    
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
        
        if value =="insert" :
            filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL"), "id_jeux": str(ObjectId(ckey)) }
            
            resultats = list(game_selec_tb.find(filtre_tb))
            if resultats :
                logging.info(f" jeux deja present")
            else : 
               
                new_selection= {         
                             "annee" : cs._secret("ANNEE_FESTIVAL"), 
                             "id_jeux": str(ObjectId(ckey)),
                             "plusieurs_exemplaires_souhaites": "False" 
                   }   
            
                resultat = game_selec_tb.insert_one(new_selection)
        elif value =="delete" :
            # deselectionne le jeu 
                
            filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL"), "id_jeux": str(ObjectId(ckey)) }
            resultat = game_selec_tb.delete_many(filtre_tb)
        else :
            filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL"), "id_jeux": ckey }
            resultat = game_selec_tb.update_many(filtre_tb, {"$set": {"plusieurs_exemplaires_souhaites": str(value) } })
            resultat = {}
        

##########################################################################
# ---- requetes  sur les jeux suggérés : jeux_suggestions  ----
##########################################################################
    
def get_suggestions(mode):
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_suggest_tb = db.jeux_suggestions
        if mode == "pret" :
             filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL") , "prete": str("True") }
        else :
             filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL") , "prete": str("False") }
        
        resultats = list(game_suggest_tb.find(filtre_tb))
    else :
        resultats ={}
    return resultats 

def get_game_suggestions(id_game, mode):
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_suggest_tb = db.jeux_suggestions
        if mode == "pret" :
            filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL") ,"id_jeux" :id_game ,"prete": str("True") }
        else :
            filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL") ,"id_jeux" :id_game, "prete": str("False")  }
        resultats = list(game_suggest_tb.find(filtre_tb))
    else :
        resultats ={}
    return resultats 


def get_game_suggestions_a_traiter ():
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_suggest_tb = db.jeux_suggestions
        filtre_tb = {
                "annee": cs._secret("ANNEE_FESTIVAL"),
                "statut": "a traiter"
            } 
        
        # distinct(field, filter) renvoie une liste de valeurs uniques
        resultats = list(game_suggest_tb.distinct("id_jeux", filtre_tb))

    else :
        resultats =[]
    return resultats 

def get_game_nb_suggestions(id_game, mode):
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_suggest_tb = db.jeux_suggestions
        if mode =="pret" :
            resultats = game_suggest_tb.count_documents({"annee": cs._secret("ANNEE_FESTIVAL") ,"id_jeux" :id_game, "prete": str("True")  })
        else :
            resultats = game_suggest_tb.count_documents({"annee": cs._secret("ANNEE_FESTIVAL") ,"id_jeux" :id_game, "prete": str("False")  })
    return resultats

def toggle_suggestion(ckey, user_id, value, mode):

    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_suggest_tb = db.jeux_suggestions

        if value == "insert" and mode=="pret" :
            new_selection= {         
                "annee" : cs._secret("ANNEE_FESTIVAL"), 
                "periode_jeu" : "",
                "id_jeux": str(ObjectId(ckey)),
                "user_id": str(user_id),
                "statut" : "a traiter",
                "prete": str("True")  
            }
             
            resultat = game_suggest_tb.insert_one(new_selection)


        elif value == "insert" and mode!="pret" :
            new_selection= {         
                "annee" : cs._secret("ANNEE_FESTIVAL"), 
                "periode_jeu" : "",
                "id_jeux": str(ObjectId(ckey)),
                "user_id": str(user_id),
                "statut" : "a traiter",
                "prete": str("False")   
            }
             
            resultat = game_suggest_tb.insert_one(new_selection)
       
        elif value == "delete" and mode=="pret" : 
            # deselectionne le jeu 
            filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL"), "periode_jeu" : "" , "id_jeux": str(ObjectId(ckey)),   "user_id": str(user_id) , "prete": str("True")  }
            resultat = game_suggest_tb.delete_many(filtre_tb)

        elif value == "delete" and mode!="pret" :
            # deselectionne le jeu 
            filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL"), "periode_jeu" : "" , "id_jeux": str(ObjectId(ckey)),   "user_id": str(user_id) , "prete": str("False")  }
            resultat = game_suggest_tb.delete_many(filtre_tb)
        
        else :  
            # change le statut de la request
            filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL"), "id_jeux": str(ObjectId(ckey)),"user_id":str(user_id)}
            resultat = game_suggest_tb.update_many(filtre_tb, {"$set": { "statut" : str(value) } })



def toggle_all_suggestion(ckey, value):

    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_suggest_tb = db.jeux_suggestions
        filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL"),  "id_jeux": ckey  }
  
        resultat = game_suggest_tb.update_many(filtre_tb, {"$set": { "statut" : value } })   
       

##########################################################################
# ---- requetes  sur les demandess : demande ajout et remarque    ----
##########################################################################

def get_requests(type_request):
    con_mongo = cs.mongo_enabled()
    if type_request == "ajout jeux" :
        if   con_mongo : 
            db = cs.get_db()
            resquest_tb = db.demandes
            filtre_tb = {"type_request" : "ajout jeux"  }
            
            resultats = list(resquest_tb.find(filtre_tb))
    elif type_request == "remarque fiche jeux" :
        if   con_mongo : 
            db = cs.get_db()
            resquest_tb = db.demandes
            filtre_tb = {"type_request" : "remarque fiche jeux"  }
            
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
                    "annee" : cs._secret("ANNEE_FESTIVAL"), 
                    "type_request" : "ajout jeux", 
                    "game_name": game_name.strip(), 
                    "myludo_url": myludo_url.strip(),
                    "comments" : "",
                    "created_by": by_name,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "statut" : "a traiter"
            }   
            resultat = resquest_tb.insert_one(new_request)
    elif type_request == "remarque fiche jeux" :
        if   con_mongo : 
            db = cs.get_db()
            resquest_tb = db.demandes
            new_request= {                    
                    "annee" : cs._secret("ANNEE_FESTIVAL"),
                    "type_request" : "remarque fiche jeux", 
                    "game_name": game_name.strip(), 
                    "myludo_url": "",
                    "comments" :comments,
                    "created_by": by_name,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "statut" : "a traiter"
            }   
            resultat = resquest_tb.insert_one(new_request)


def remove_request(type_request, req_id):
 con_mongo = cs.mongo_enabled()
 print( str(ObjectId(req_id)) )   
 print(  type_request)
 print(   cs._secret("ANNEE_FESTIVAL"))
 if   con_mongo : 
    db = cs.get_db()
    resquest_tb = db.demandes                                              
    filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL"), "type_request" : type_request,   "_id": ObjectId(str(req_id)) }
    resultat = resquest_tb.delete_many(filtre_tb)

def update_statut_request(type_request, req_id,statut):
 con_mongo = cs.mongo_enabled()
 print( str(ObjectId(req_id)) )   
 print(  type_request)
 print(   cs._secret("ANNEE_FESTIVAL"))
 if   con_mongo : 
    db = cs.get_db()
    resquest_tb = db.demandes                                              
    filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL"), "type_request" : type_request,   "_id": ObjectId(str(req_id)) }
    resultat = resquest_tb.update_many(filtre_tb, {"$set": {"statut" : statut} })





def all_list_keys():
    return [k for k, _ in config_bar_jeux.month_keys()] + [config_bar_jeux.VIEUX_KEY]



##########################################################################
# ---- requetes  sur les prets :   prets_jeux   ----
##########################################################################



def get_all_loans():
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_loan_tb = db.prets_jeux
        filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL") }  
        resultats = list(game_loan_tb.find(filtre_tb))
    return resultats 

def get_validated_loans():
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_loan_tb = db.prets_jeux
        filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL") , "valide_par_admin" : str("True")  }  
        resultats = list(game_loan_tb.find(filtre_tb))
    return resultats 

def toggle_loan(ckey, user_id, value):
    con_mongo = cs.mongo_enabled()
    if   con_mongo : 
        db = cs.get_db()
        game_loan_tb = db.prets_jeux

        if value :
            new_loan= {         
                         "annee" : cs._secret("ANNEE_FESTIVAL"), 
                         "id_jeux": ckey,
                         "user_id": user_id,
                		 "valide_par_admin" : str("False")
               }   
        
            resultat = game_loan_tb.insert_one(new_loan)
        else :  
            # deselectionne le jeu 
    
            filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL"), "id_jeux": ckey,"user_id":user_id}
            resultat = game_loan_tb.delete_many(filtre_tb)


def set_loan_valide_admin(ckey, user_id, value):
    con_mongo = cs.mongo_enabled()
    if con_mongo : 
            db = cs.get_db()
            game_loan_tb = db.prets_jeux    
            filtre_tb = {"annee": cs._secret("ANNEE_FESTIVAL"), "id_jeux": ckey,"user_id":user_id}
            resultat = game_loan_tb.update_many(filtre_tb, {"$set": {  "valide_par_admin": str(value) } })
            

    
    return {}

    

#############################################################################








import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
import pandas as pd


def export_excel( df , page_size , file_name) : 

        
        
        # Ajout de colonnes ne provenant pas du DataFrame initial
        df["Jeu01"] = ""
        df["Jeu02"] = ""
        df["Jeu03"] = ""
        df["Jeu04"] = ""
        df["Jeu05"] = ""
        df["Jeu06"] = ""
        df["Jeu07"] = ""
        df["Jeu08"] = ""
        df["Jeu09"] = ""
        df["Jeu10"] = ""
        df["Jeu11"] = ""
        df["Jeu12"] = ""
        df["Jeu13"] = ""
        df["Jeu14"] = ""
        df["Jeu15"] = ""
        df["Jeu16"] = ""
        df["Jeu17"] = ""
        df["Jeu18"] = ""
        df["Jeu19"] = ""
        df["Jeu20"] = ""
        
        # Export initial vers un fichier Excel
       
        df.to_excel(file_name, index=False, sheet_name="Liste_jeux")
        
        # 2. Chargement du fichier avec openpyxl pour la mise en forme avancée
        wb = openpyxl.load_workbook(file_name)
        ws = wb["Liste_jeux"]


        if  page_size == "A3" :
                # --- Largeur des colonnes ---
                column_widths = {"A": 10, ##classement
                                 "B": 20,  ##Jeu
                                 "C" : 1,
                                 "D" : 1,
                                 "E": 1,
                                 "F": 1,
                                 "G": 1,
                                 "H": 1,
                                 "I": 1,
                                 "J": 1,
                                 "K": 1,
                                 "L": 1,
                                 "M": 1,
                                 "N": 1,
                                 "O": 1,
                                 "P": 1,
                                 "Q": 1,
                                 "R": 1,
                                 "S": 1,
                                 "T": 1,
                                 "U": 1,
                                 "V": 1}
                for col, width in column_widths.items():
                    ws.column_dimensions[col].width = width
                
                # --- Hauteur des lignes ---
                ws.row_dimensions[1].height = 30  # Hauteur de la ligne d'en-tête
                for row in range(2, ws.max_row + 1):
                    ws.row_dimensions[row].height = 7  # Hauteur des lignes de données

                ws.page_setup.paperSize = ws.PAPERSIZE_A3  # Format A3
                ws.page_setup.orientation = (  
                   
                   ws.ORIENTATION_PORTRAIT
                )
        else  : ##---  page_size == A4 
                ws.page_setup.paperSize = ws.PAPERSIZE_A4  # Format A3
                ws.page_setup.orientation = (  
                    ws.ORIENTATION_LANDSCAPE
                   
                )
         
        # --- Définition des bordures (taille 'thin' et couleur grise) ---
        thin_border = Border(
            left=Side(style="thin", color="B0B0B0"),
            right=Side(style="thin", color="B0B0B0"),
            top=Side(style="thin", color="B0B0B0"),
            bottom=Side(style="thin", color="B0B0B0"),
        )
        
        # --- Couleurs conditionnelles et application des bordures ---
        fill_green = PatternFill(
            start_color="57B02C", end_color="57B02C", fill_type="solid"
        )  # FAMILLE
        fill_red = PatternFill(
            start_color="E67A70", end_color="E67A70", fill_type="solid"
        )  # EXPERT
        fill_red_fonce = PatternFill(
            start_color="8C0E07", end_color="8C0E07", fill_type="solid"
        )  # EXPERT +
        fill_grey = PatternFill(
            start_color="C7C5C5", end_color="C7C5C5", fill_type="solid"
        )  # NON CLASSE
        fill_orange = PatternFill(
            start_color="FF9224", end_color="FF9224", fill_type="solid"
        )  # JEU DUO
        fill_pink = PatternFill(
            start_color="E655DA", end_color="E655DA", fill_type="solid"
        )  # AMBIANCE
        fill_yellow = PatternFill(
            start_color="F5E20C", end_color="F5E20C", fill_type="solid"
        )  # INITIE
        fill_blue = PatternFill(
            start_color="1128D6", end_color="1128D6", fill_type="solid"
        )  # ENFANT
        fill_violet = PatternFill(
            start_color="7A0EE3", end_color="7A0EE3", fill_type="solid"
        )  # COOP/SEMI COOP
        fill_blue_light = PatternFill(
            start_color="1FC7FF", end_color="1FC7FF", fill_type="solid"
        )  # ENQUETE/ESCAPE/ENIGME/CASSETETE



        
        for row in range(2, ws.max_row + 1):
            # Appliquer les bordures à toute la ligne du tableau
            for col in range(1, ws.max_column + 1):
                ws.cell(row=row, column=col).border = thin_border
        
            # Condition sur la colonne "classement" (colonne 2 / B)
            cell_classement = ws.cell(row=row, column=1)
            if cell_classement.value == "ENQUETE/ESCAPE/ENIGME/CASSETETE":
                    cell_vente.fill = fill_blue_light  
            elif cell_classement.value == "COOP/SEMI COOP":
                    cell_classement.fill = fill_violet    
            elif cell_classement.value == "INITIE":
                    cell_classement.fill = fill_yellow  
            elif cell_classement.value == "ENFANT":
                    cell_classement.fill = fill_blue 
            elif cell_classement.value == "AMBIANCE":
                    cell_classement.fill = fill_green  
            elif cell_classement.value == "FAMILLE":
                    cell_classement.fill = fill_pink  
            elif cell_classement.value == "EXPERT":
                    cell_classement.fill = fill_red  
            elif cell_classement.value == "EXPERT +":
                    cell_classement.fill = fill_red_fonce  
            elif cell_classement.value == "NON CLASSE":
                    cell_classement.fill = fill_grey  
            elif cell_classement.value == "JEU DUO":
                    cell_classement.fill = fill_orange  




        # --- Configuration de l'impression au format A3 ---
 
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth = 1  # Ajuster à 1 page de largeur
        
        # Sauvegarde du fichier final
        wb.save(file_name)

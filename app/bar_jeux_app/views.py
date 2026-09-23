"""Vues Streamlit pour Bar à jeux."""
 

from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode , DataReturnMode , AgGridTheme       
import logging
import plotly.express as px
import pandas as pd
import streamlit as st
import bcrypt
import config_bar_jeux
import storage_jeux
import export
import os
import sys
import time
from bson import ObjectId
from config_game_card import _game_card , mise_forme_classement , nouveaute_def
# Ajoute le dossier parent à sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import commun.auth,  commun.config 
import commun.common_store as cs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def main_app(user):
    with st.sidebar:
        st.markdown("### 🎲 Bar à jeux")
        st.write(f"**{user['pseudo']}**")
        
        if user["role"] == "admin":
            st.markdown("<span class='ws-tag-admin'>Admin</span>", unsafe_allow_html=True)
            pages = ["Liste des jeux","Recherche jeu", "Demandes d'ajout / remarques","Liste suggestions", "Jeux sortis depuis dernier festival", "Jeux sortis avant dernier festival" ]
        else : 
            pages = ["Liste des jeux","Recherche jeu"]
        page = st.radio("Navigation", pages, label_visibility="collapsed")
        st.divider()
        if st.button("Déconnexion"):
            commun.auth.logout()
            st.rerun()

    if page == "Jeux sortis depuis dernier festival":
        months = config_bar_jeux.month_keys()
        label = st.selectbox("Mois", [l for _, l in months])
        key = next(k for k, l in months if l == label)
        _list_page(f"Jeux — {label}", key, user)
    elif page == "Jeux sortis avant dernier festival":
        _list_page("Vieux jeux", config_bar_jeux.VIEUX_KEY, user)
    elif page == "Demandes d'ajout / remarques":
        _requests_page(user)
    elif page == "Liste suggestions":
        _requests_suggestion_page(user)    
    elif page == "Recherche jeu":
         _list_page(f"Recherche jeu", "all", user)
    else:
        _final_page(user)






############################################################################################################
###-------------- page affichant les jeux 
############################################################################################################


def _list_page(title, list_key, user):
    st.title(title)
    
    with st.expander("➕ Demander l'ajout d'un jeu"):
        with st.form(f"req_{list_key}", clear_on_submit=True):
            n = st.text_input("Nom du jeu")
            u = st.text_input("URL myludo")
            if st.form_submit_button("Envoyer la demande", type="primary") and n.strip():
                storage_jeux.add_request("ajout jeux", n, u, list_key, user["pseudo"])
                st.success("Demande envoyée à l'administrateur")



    # Champ de saisie utilisateur
    raw_search = st.text_input(
       "🔎 Rechercher un jeu (nom ou URL)",
       placeholder="Ex: Catan, https://...",
       key=f"game_search_input_{list_key}"
    )
    search_query = (raw_search or "").strip().lower()

    # Filtrage de la liste de jeux
    filtered_games = []
    
    if list_key == "all" and not search_query:
        filtered_games = []
    else:
      
        # Passer le terme de recherche directement à MongoDB
        games = storage_jeux.load_games(list_key, search_query=search_query)
    
        if not games:
            st.info("Aucun jeu dans cette liste.")
            return
        
        filtered_games = games


 
    # Affichage des cartes filtrées 
    if filtered_games:
        per_row = 3
        # FIX : On utilise len(filtered_games) ici !
        for i in range(0, len(filtered_games), per_row):
            cols = st.columns(per_row)
            for j, g in enumerate(filtered_games[i:i + per_row]):
                with cols[j]:
                    _game_card(g, list_key, user,"normal")
    elif list_key !="all"  or ( list_key =="all" and search_query) :
        st.info("Aucun jeu ne correspond à votre recherche.")
  
############################################################################################################
###-------------- page des suggestion et remarque des joueur
############################################################################################################
   
def _requests_suggestion_page(user):
    st.title("liste des suggestions par les joueurs")
    list_suggest = storage_jeux.get_game_suggestions_a_traiter()
    list_games_tmp =[]
    for sugg in list_suggest : 
        
        list_games_tmp.append(storage_jeux.get_info_games(sugg))
    list_games = [elem for sous_liste in list_games_tmp for elem in sous_liste]
   
    if list_games:
        per_row = 3
        # FIX : On utilise len(list_games) ici !
        for i in range(0, len(list_games), per_row):
            cols = st.columns(per_row)
            for j, g in enumerate(list_games[i:i + per_row]):
                with cols[j]:
                    _game_card(g, "all", user,"suggestion")


############################################################################################################
###-------------- page des demandes d'ajout 
############################################################################################################


def _requests_page(user):
    ##st.title("Demandes d'ajout de jeux")
    st.subheader("Demandes d'ajout de jeux")
    reqs = storage_jeux.get_requests("ajout jeux")
    if not reqs: 
        st.info("Aucune demande.")
    else :
        c1, c2, c3, c4 , c5 ,c6,c7  = st.columns([3, 6, 1, 2 , 1, 2, 2])
        label = c1.text_input("t", value="NOM DU JEU", key=f"edit_game", label_visibility="collapsed")
        label = c2.text_input("t", value="MYLUDO URL", key=f"edit_myludo",label_visibility="collapsed") 
        label = c3.text_input("t", value="FAIT PAR", key=f"edit_by", label_visibility="collapsed")      
        label = c4.text_input("t", value="DEMANDE LE", key=f"edit_date", label_visibility="collapsed") 
        label = c5.text_input("t", value="STATUT", key=f"edit_statut", label_visibility="collapsed")
        label = c6.text_input("t", value="", key=f"edit_vide1", label_visibility="collapsed")
        label = c7.text_input("t", value="", key=f"edit_vide2", label_visibility="collapsed")
        for r in reqs:
              
                  label = c1.text_input("t", value=r["game_name"], key=f"edit_game_{str(r["_id"])}",
                                         label_visibility="collapsed")
         
                  label = c2.text_input("t", value=r["myludo_url"], key=f"edit_myludo_{str(r["_id"])}",
                                         label_visibility="collapsed")      
         
                  label = c3.text_input("t", value=r["created_by"], key=f"edit_by_{str(r["_id"])}",
                                         label_visibility="collapsed")      
                  label = c4.text_input("t", value=r["created_at"], key=f"edit_date_{str(r["_id"])}",
                                         label_visibility="collapsed") 
                  label = c5.text_input("t", value=r["statut"], key=f"edit_statut_{str(r["_id"])}",
                                         label_visibility="collapsed")
                  if user["role"] == "admin": 
                        if c6.button("traiter", key=f"modif_traiter_{r["_id"]}"):
                            storage_jeux.update_statut_request("ajout jeux", r["_id"],"traiter")
                           
                            print("traiter demande ajout")
                            st.rerun()
                        if c7.button("supprimer", key=f"modif_supp_{r["_id"]}"):
                            storage_jeux.remove_request("ajout jeux", r["_id"])
                            st.write("update supprimer ajout jeu faite")
                            st.rerun()


    st.subheader("liste des remarques par les joueurs")

    remarks = storage_jeux.get_requests("remarque fiche jeux")
    if not reqs:
        st.info("Aucune remarque.")
    else :
        c12, c22, c32, c42 , c52 ,c62, c72  = st.columns([3, 6, 1, 2 , 1, 2, 2])
        label = c12.text_input("t", value="NOM DU JEU", key=f"edit_game2", label_visibility="collapsed")
        label = c22.text_input("t", value="COMMENTAIRE", key=f"edit_myludo2",label_visibility="collapsed") 
        label = c32.text_input("t", value="FAIT PAR", key=f"edit_by2", label_visibility="collapsed")      
        label = c42.text_input("t", value="DEMANDE LE", key=f"edit_date2", label_visibility="collapsed") 
        label = c52.text_input("t", value="STATUT", key=f"edit_statut2", label_visibility="collapsed")
        label = c62.text_input("t", value="", key=f"edit_vide3", label_visibility="collapsed")
        label = c72.text_input("t", value="", key=f"edit_vide4", label_visibility="collapsed")
     
        for t in remarks:
              
                  label = c12.text_input("t", value=t["game_name"], key=f"edit_game_{str(t["_id"])}",
                                         label_visibility="collapsed")
                  label = c22.text_input("t", value=t["comments"], key=f"edit_comment_{str(t["_id"])}",
                                         label_visibility="collapsed")      
         
                  label = c32.text_input("t", value=t["created_by"], key=f"edit_by_{str(t["_id"])}",
                                         label_visibility="collapsed")      
                  label = c42.text_input("t", value=t["created_at"], key=f"edit_date_{str(t["_id"])}",
                                         label_visibility="collapsed") 
                  label = c52.text_input("t", value=t["statut"], key=f"edit_statut_{str(t["_id"])}",
                                         label_visibility="collapsed")


                  if user["role"] == "admin": 
                      if c62.button("traiter", key=f"modif_traiter_{t["_id"]}"):
                          storage_jeux.update_statut_request("remarque fiche jeux", t["_id"],"traiter")
                          st.write("update remarque faite")
                          st.rerun()
                      if c72.button("supprimer", key=f"modif_suppr_{t["_id"]}"):
                          storage_jeux.remove_request("remarque fiche jeux", t["_id"])
                          st.rerun()
############################################################################################################
###-------------- page où est affiché les jeux selectionné
############################################################################################################

def _final_page(user):
    st.title("Liste des jeux")
    st.write("Vous allez pouvoir remplir le tableau pour indiquer vos propositions de pret.   Les administrateurs valideront les différentes propositions pour définir votre liste de prêt définitive. ")

    
    # --- 1. CHARGEMENT GLOBAL DES DONNÉES EN AMONT (O(1) requêtes) ---
    finals = storage_jeux.final_games()
    if not finals:
        st.info("Aucun jeu retenu par l'admin pour l'instant.")
        return
    
    users = cs.get_users_loaner()
    user_map = {u['pseudo']: str(u['_id']) for u in users}  # Dict pseudo -> id_str
    pseudo_list = sorted(list(user_map.keys()))
    
    # Récupération en BATCH des infos de tous les jeux d'un coup
    game_ids = [g.get('id_jeux') for g in finals]
    liste_object_id = [ObjectId(id_str) for id_str in game_ids]
  
 
    games_info_list = storage_jeux.load_games(liste_object_id, None) 
 
    games_info_map = {str(g["_id"]): g for g in games_info_list}


    
    # Conversion des prêts sous forme de SETs pour recherche instantanée O(1)
    # Structure des tuples stockés dans le set : (game_id, user_id)
    list_jeu_propose = storage_jeux.get_all_loans()
    loans_set = {(p['id_jeux'], p['user_id']) for p in list_jeu_propose}
    
    list_jeu_propose_valide = storage_jeux.get_validated_loans()
    validated_loans_set = {(p['id_jeux'], p['user_id']) for p in list_jeu_propose_valide}
    
    liste_jeu_plusieurs = storage_jeux.final_games_statut_plusieurs_exemplaire()
    plusieurs_set = {x["id_jeux"] for x in liste_jeu_plusieurs}
    

    
    # --- 2. CONSTRUCTION ULTRA-RAPIDE DU DATAFRAME ---
    row_jeux = []
    
    for game in finals:
        game_id = str(game.get('id_jeux'))
        g = games_info_map.get(game_id, {})
        
        if not g:
            continue
    
        # Calculs directes en mémoire
        new_statut = nouveaute_def(game)
        is_several = game_id in plusieurs_set
    
        # Comptages rapides
        total_joueurs = sum(1 for p_id in user_map.values() if (game_id, p_id) in loans_set)
        total_valide = sum(1 for p_id in user_map.values() if (game_id, p_id) in validated_loans_set)
    
        row = {
            "_id": game_id,                           
            "nouveaute": new_statut,
            "Annee": g.get("annee_parution", ""),
            "Categorie jeu": mise_forme_classement(g.get("classement_jps_final")),
            "Couverture Jeu": g.get("couverture", ""),
            "Jeu": g.get("nom_jeu_complet", ""),
            "Plusieurs exemplaires souhaités": is_several,
            "Total coché par joueur": total_joueurs,
            "Total coché validé par admin": total_valide,
        }
    
        # Remplissage des colonnes dynamiques par joueur (Recherche instantanée dans un Set)
        for pseudo in pseudo_list:
            u_id = user_map[pseudo]
            row[f"{pseudo}_propose"] = (game_id, u_id) in loans_set
            row[f"{pseudo}_admin"] = (game_id, u_id) in validated_loans_set
    
        row_jeux.append(row)
    
    df_jeux = pd.DataFrame(row_jeux)

    # --- 3. FORMULAIRE STREAMLIT AVEC AGGRID ---
    # Utilisation d'un st.form pour regrouper le tableau et le bouton de validation en bas
    with st.form(key="loans_form"):
      image_renderer = JsCode("""
      class ImageRenderer {
          init(params) {
              this.eGui = document.createElement('img');
              this.eGui.setAttribute('src', params.value);
              this.eGui.setAttribute('style', 'height: 45px; width: auto; border-radius: 4px; vertical-align: middle;');
          }
          getGui() { return this.eGui; }
      }
      """)
      
      #  On liste explicitement les noms des colonnes souhaitées
      columns_to_show = [
          "nouveaute",
          "Annee",
          "Categorie jeu",
          "Couverture Jeu",
          "Jeu",
          "Plusieurs exemplaires souhaités",
          "Total coché par joueur",
          "Total coché validé par admin"
      ]
      
      # On passe la liste directement à partir du DataFrame
      gb = GridOptionsBuilder.from_dataframe(df_jeux[columns_to_show])
      gb.configure_column("_id", hide=True)
      gb.configure_column("nouveaute", editable=False, width=80, suppressSizeToFit=True, pinned=True)
      gb.configure_column("Annee", editable=False, width=80, suppressSizeToFit=True, pinned=True)
      gb.configure_column("Categorie jeu", editable=False, width=180, suppressSizeToFit=True, pinned=True)
      gb.configure_column("Couverture Jeu", editable=False, cellRenderer=image_renderer, width=100, suppressSizeToFit=True, pinned=True)
      gb.configure_column("Jeu", editable=False, width=150, suppressSizeToFit=True, pinned=True)
      
      gb.configure_column(
          "Plusieurs exemplaires souhaités",
          editable=(user["role"] == "admin"),
          cellRenderer="agCheckboxCellRenderer",
          cellEditor="agCheckboxCellEditor",
          width=90,
          suppressSizeToFit=True,
          pinned=True 
      )
      
      gb.configure_column("Total coché par joueur", editable=False, width=80, suppressSizeToFit=True, pinned=True)
      gb.configure_column("Total coché validé par admin", editable=False, width=90, suppressSizeToFit=True, pinned=True)
      
      gb.configure_grid_options(singleClickEdit=True, rowHeight=60)
      grid_options = gb.build()
      
      # En-têtes groupés par joueur
      for pseudo in pseudo_list:
          group_col = {
              "headerName": pseudo,
              "children": [
                  {
                      "field": f"{pseudo}_propose",
                      "headerName": "Je prête",
                      "editable": (user["pseudo"] == pseudo or user["role"] == "admin"),
                      "cellRenderer": "agCheckboxCellRenderer",
                      "cellEditor": "agCheckboxCellEditor",
                      "width": 100,
                      "suppressSizeToFit": True,
                  },
                  {
                      "field": f"{pseudo}_admin",
                      "headerName": "Validé",
                      "editable": (user["role"] == "admin"),
                      "cellRenderer": "agCheckboxCellRenderer",
                      "cellEditor": "agCheckboxCellEditor",
                      "width": 100,
                      "suppressSizeToFit": True,
                      "cellStyle": JsCode("""
                          function(params) {
                              return params.value === true ? {backgroundColor: '#d4edda', color: '#155724'} : null;
                          }
                      """),
                  },
              ],
          }
          grid_options["columnDefs"].append(group_col)
      
      # Hauteur dynamique
      dynamic_height = 650 ##min(max(40 + (len(df_jeux) * 70) + 20, 200), 800)
      if "grid_version" not in st.session_state:
         st.session_state.grid_version = 0
      gb.configure_grid_options(alwaysShowHorizontalScroll=True)

      # Bouton de soumission unique en haut du tableau
      col_btn1, col_btn2, col_btn3 , col_btn4  = st.columns(4)
      with col_btn1 : 
           submit_button = st.form_submit_button(
                  label="Enregistrer toutes les modifications"
            )      
      with col_btn2 : 
          export_list_perso_button = st.form_submit_button(
                label="export de votre liste")
      with col_btn3 :  
          export_list_valide_button = st.form_submit_button(
                label="Export de la liste validée")
      with col_btn4 :  
          export_list_initiale_button = st.form_submit_button(
                label="export de la liste initial")
          
     
      # le tableau
      grid_response = AgGrid(
          df_jeux,
          gridOptions=grid_options,
          update_mode=GridUpdateMode.NO_UPDATE,
          data_return_mode=DataReturnMode.AS_INPUT,
          allow_unsafe_jscode=True,
          fit_columns_on_grid_load=False,
          height=dynamic_height,
          key=f"aggrid_table_{st.session_state.grid_version}",
      ) 
   
 


     # --- Détection des changements ---
  
    if submit_button:
           updated_data = grid_response["data"]
           new_df = pd.DataFrame(updated_data)
     
           # Les colonnes à surveiller
           cols_to_check = [
               "Plusieurs exemplaires souhaités"
           ] + [
               col
               for col in new_df.columns
               if "_propose" in col or "_admin" in col
           ]
     
           # On fusionne pour comparer cellule par cellule via les suffixes _old et _new
           merged = df_jeux.merge(new_df, on="_id", suffixes=("_old", "_new"))
     
           modifications_count = 0
     
           for _, row in merged.iterrows():
             game_id = row["_id"]
     
             # On parcourt chaque colonne pour voir EXACTEMENT laquelle a changé
             for col in cols_to_check:
               val_old = row[f"{col}_old"]
               val_new = row[f"{col}_new"]
     
               # Si la valeur a changé pour cette cellule précise
               if val_old != val_new:
                 modifications_count += 1
     
                 # --- CAS 1 : "Plusieurs exemplaires" ---
                 if col == "Plusieurs exemplaires souhaités":
                   if user["role"] == "admin":
                     storage_jeux.toggle_admin_selected(game_id, val_new)
     
                 # --- CAS 2 : Colonne de prêt d'un utilisateur (ex: "pseudo_propose") ---
                 elif "_propose" in col:
                   # On extrait le pseudo du nom de la colonne (ex: "Alice_propose" -> "Alice")
                   pseudo = col.replace("_propose", "")
                   u_id = user_map[pseudo]
                   storage_jeux.toggle_loan(game_id, str(u_id), val_new)
     
                 # --- CAS 3 : Colonne de validation admin d'un utilisateur (ex: "pseudo_admin") ---
                 elif "_admin" in col:
                   pseudo = col.replace("_admin", "")
                   u_id = user_map[pseudo]
                   storage_jeux.set_loan_valide_admin(game_id, str(u_id), val_new)
     
           st.success(
               f"Enregistrement réussi : {modifications_count} cellule(s) modifiée(s)"
               " mise(s) à jour !"
           )
           st.session_state.grid_version += 1
           time.sleep(1)
           st.rerun()






    st.divider()
   
    # --- PARTIE inferieurs : GRAPHIQUES ---

    col_graph1, col_graph2, col_graph3 = st.columns(3)

    

    ###########---- 0 dataframe pour alimenter les graph 
    # 1. Optimisation : création d'un dictionnaire d'utilisateurs {str(id): pseudo}
    users_dict = {str(u["_id"]): u.get("pseudo", "Inconnu") for u in users}
     ###---------------------------------------------------- 
    liste_pret_validé = storage_jeux.get_validated_loans()
    liste_info_valide = []

 
    for game in  liste_pret_validé :
        id_jeu = game["id_jeux"]
        info_games_valide = storage_jeux.get_info_games(id_jeu)
        # Récupération sécurisée du pseudo (converti en str pour être sûr que les ID matchent)
        user_id_str = str(game["user_id"])
        pseudo = users_dict.get(user_id_str, "Utilisateur inconnu")
       
          
        liste_info_valide.append ({"classement":  info_games_valide[0]["classement_jps_final"] ,  "Nouveauté": nouveaute_def(game), "pseudo":pseudo , "nom": info_games_valide[0]["nom_jeu_complet"],"Nb_jeux_valide":1, "statut_valide":True})
     
    df_jeux_valide_graphique  = pd.DataFrame(liste_info_valide)



    ###---------------------------------------------------- 
    liste_info = []
    liste_pret_user = storage_jeux.get_all_loans()
    liste_game_preter = [ObjectId(game["id_jeux"]) for game in liste_pret_user ]
    print(liste_game_preter)      
    liste_detail32 = storage_jeux.load_games(liste_game_preter, None)

    print("liste_detail32")
    print(liste_detail32)
    print("liste_detail3233")
    liste__info_pret_user = pd.DataFrame(liste_detail32)
  
    liste__info_pret_user = liste__info_pret_user.rename(columns={'_id': 'id_jeux'})
    
    liste_pret_user_pd =pd.DataFrame(liste_pret_user)
    
 
  
   
    liste_pret_user_detail = pd.merge(
           liste__info_pret_user,
           liste_pret_user_pd,
           on="id_jeux",
           how="inner",  
       )
   # print("liste_detail pret user")
 
    #print( liste_pret_user_detail[liste_pret_user_detail["id_jeux"] == "9e705c422573f38168868b69"])
    #print("jeu prete")
    #print( liste_pret_user_pd[liste_pret_user_pd["id_jeux"] == "9e705c422573f38168868b69"])
    #print("info jeu prete")
    #print( liste__info_pret_user[liste__info_pret_user["id_jeux"] == "9e705c422573f38168868b69"])
    #print( liste__info_pret_user["id_jeux"] )


    if not liste__info_pret_user.empty:
         liste_pret_user_detail["Nouveauté"] = liste_pret_user_detail.apply(nouveaute_def, axis=1)
         liste_pret_user_detail["Nb_jeux_propose"] = 1

    df_jeux_pret_graphique  = liste_pret_user_detail   
    
    ###---------------------------------------------------- 
    liste_jeu_selectionne = []
    liste_jeu_selec = storage_jeux.final_games()


    liste_game_select = [ObjectId(game["id_jeux"]) for game in liste_jeu_selec ]
    
    liste__info_select = storage_jeux.load_games(liste_game_select, None)


    for game_selec in liste__info_select:

   
        # Récupération des infos du jeu
        id_jeu = game_selec.get("id_jeux")
        
    
        # Ajout à la liste
        liste_jeu_selectionne.append({
            "classement": game_selec.get("classement_jps_final"),
            "Nouveauté": nouveaute_def(game_selec),
            "nom": game_selec.get("nom_jeu_complet"),
            "Nb_jeux_selec": 1,
        })
    df_jeux_select_graphique  = pd.DataFrame(liste_jeu_selectionne)



    couleurs_classement = {"AMBIANCE": "#E655DA", ## rose
                           "COOP/SEMI COOP" :"#7A0EE3",####violet
                           "JEU DUO" :"#FF9224",          ##orange                 
                           "ENQUETE/ESCAPE/ENIGME/CASSETETE" :"#1FC7FF",##bleu clair
                           "NON CLASSE": "#C7C5C5", ### gris
                           "PBM CLASSEMENT": "#080808",   ### black                         
                           "FAMILLE": "#57B02C", ## vert 
                           "INITIE": "#F5E20C", ## jaune 
                           "EXPERT": "#E67A70", ### rouge  
                           "EXPERT+": "#8C0E07",   ### rouge   foncé                     
                           "ENFANT": "#1128D6" ### bleu foncé
                          }

    couleurs_nouveaute = {"✨NOUVEAUTE": "#57B02C", "🏺ANCIEN": "#080808", "🧐 INCONNU": "#1128D6"}
  

   ###########---- 1. Histogramme par joueur (Validés vs Cochés Utilisateur)
   
    with col_graph1:
          st.subheader("Nombre Jeux selectionnés")
       
          st.metric(    label="Nombre jeux sélectionnés", value=len(df_jeux_select_graphique),label_visibility="collapsed")
                    
          st.subheader("Jeux selectionnés par Classement")
       
          if not df_jeux_select_graphique.empty:
              df_cat = df_jeux_select_graphique["classement"].value_counts().reset_index()
              df_cat.columns = ["classement", "Nombre"]
              fig_pie_cat = px.pie(df_cat, names="classement", values="Nombre", hole=0.3, color="classement", color_discrete_map=couleurs_classement )
              fig_pie_cat.update_layout(height=250 , width=1000) 
              fig_pie_cat.update_layout(
                  legend=dict(
                      orientation="h",  # Légende horizontale (passe les éléments en ligne/grille en bas)
                      yanchor="top",
                      y=-0.2,  # Positionne la légende en dessous du graphique
                      xanchor="center",
                      x=0.5,
                      font=dict(size=10),  # Réduit légèrement la taille du texte si nécessaire
                  ),
                  margin=dict(
                      t=30, b=100, l=20, r=20
                  ),  # Augmente la marge du bas (b) pour laisser de la place à la légende
              )
              st.plotly_chart(fig_pie_cat, use_container_width=True)
          else:
              st.info("Aucun jeu coché pour le moment.")


          st.subheader("Jeux selectionnés  par nouveauté")
#          if not df_jeux_select_graphique.empty:
#              df_nov = df_jeux_select_graphique["Nouveauté"].value_counts().reset_index()
#              df_nov.columns = ["Nouveauté", "Nombre"]
#              fig_pie_nov = px.pie(df_nov, names="Nouveauté", values="Nombre", hole=0.3 , color="Nouveauté", color_discrete_map=couleurs_nouveaute  )
#              fig_pie_nov.update_layout(height=250 , width=1000)
#              st.plotly_chart(fig_pie_nov, use_container_width=True)
#          else:
#              st.info("Aucun jeu coché pour le moment.")


 
          
        
    ###########----2. Camembert Nouveautés (jeux cochés au moins une fois par un utilisateur)
       
    with col_graph2:
          st.subheader("Nombre Jeux proposés ")
       
          st.metric(    label="Nombre jeux proposés", value=len(df_jeux_pret_graphique),label_visibility="collapsed")
         
     
          st.subheader("Jeux proposés par Classement")
 #         if not df_jeux_pret_graphique.empty:
 #             df_cat = df_jeux_pret_graphique["classement"].value_counts().reset_index()
 #             df_cat.columns = ["classement", "Nombre"]
 #             fig_pie_cat = px.pie(df_cat, names="classement", values="Nombre", hole=0.3, color="classement", color_discrete_map=couleurs_classement )
 #             fig_pie_cat.update_layout(height=250 , width=1000) 
 #             fig_pie_cat.update_layout(
 #                 legend=dict(
 #                     orientation="h",  # Légende horizontale (passe les éléments en ligne/grille en bas)
 #                     yanchor="top",
 #                     y=-0.2,  # Positionne la légende en dessous du graphique
 #                     xanchor="center",
 #                     x=0.5,
 #                     font=dict(size=10),  # Réduit légèrement la taille du texte si nécessaire
 #                 ),
 #                 margin=dict(
 #                      t=30, b=100, l=20, r=20
 #                 ),  # Augmente la marge du bas (b) pour laisser de la place à la légende
 #             )
 #             st.plotly_chart(fig_pie_cat, use_container_width=True)
 #
 #          else:
 #             st.info("Aucun jeu proposé pour le moment.")

          st.subheader("Jeux proposés par Nouveauté")
 #         if not df_jeux_pret_graphique.empty:
 #             df_nov = df_jeux_pret_graphique["Nouveauté"].value_counts().reset_index()
 #             df_nov.columns = ["Nouveauté", "Nombre"]
 #v             fig_pie_nov = px.pie(df_nov, names="Nouveauté", values="Nombre", hole=0.3 , color="Nouveauté", color_discrete_map=couleurs_nouveaute )
 #             fig_pie_nov.update_layout(height=250 , width=1000)
 #             st.plotly_chart(fig_pie_nov, use_container_width=True)
 #         else:
 #             st.info("Aucun jeu proposé pour le moment.")

     



 

      ###########----3. Camembert Catégories (Produits cochés au moins une fois par un utilisateur)
    with col_graph3:
          st.subheader("Nombre Jeux validés")
       
          st.metric(    label="Nombre jeux validés", value=len(df_jeux_valide_graphique),label_visibility="collapsed")
         
     
          st.subheader("Jeux validés par Classement")
          if not df_jeux_valide_graphique.empty:
              df_cat2 = df_jeux_valide_graphique["classement"].value_counts().reset_index()
              df_cat2.columns = ["classement", "Nombre"]
              fig_pie_cat2 = px.pie(df_cat2, names="classement", values="Nombre", hole=0.3 ,  color="classement", color_discrete_map=couleurs_classement )
              fig_pie_cat2.update_layout(height=250 , width=1000) 
              fig_pie_cat2.update_layout(
                  legend=dict(
                      orientation="h",  # Légende horizontale (passe les éléments en ligne/grille en bas)
                      yanchor="top",
                      y=-0.2,  # Positionne la légende en dessous du graphique
                      xanchor="center",
                      x=0.5,
                      font=dict(size=10),  # Réduit légèrement la taille du texte si nécessaire
                  ),
                  margin=dict(
                      t=30, b=100, l=20, r=20
                  ),  # Augmente la marge du bas (b) pour laisser de la place à la légende
              )

              st.plotly_chart(fig_pie_cat2, use_container_width=True)
          else:
              st.info("Aucun jeu validé pour le moment.")


          st.subheader("Jeux validés par Nouveauté")
          if not df_jeux_valide_graphique.empty:
              df_nov2 = df_jeux_valide_graphique["Nouveauté"].value_counts().reset_index()
              df_nov2.columns = ["Nouveauté", "Nombre"]
              fig_pie_nov2 = px.pie(df_nov2, names="Nouveauté", values="Nombre", hole=0.3 ,color="Nouveauté", color_discrete_map=couleurs_nouveaute)
              fig_pie_nov2.update_layout(height=250 , width=1000)
              st.plotly_chart(fig_pie_nov2, use_container_width=True)
          else:
              st.info("Aucun jeu validé pour le moment.")     


 
    st.subheader("listes des prets  par Joueur")

    if df_jeux_pret_graphique.empty and df_jeux_valide_graphique.empty:
       df_jeux_histogramme = pd.DataFrame(
             columns=[
                 "classement",
                 "Nouveauté",
                 "pseudo",
                 "nom",
                 "Nb_jeux_propose",
                 "Nb_jeux_valide",
                 "statut_valide",
             ]
         )

    elif df_jeux_pret_graphique.empty:
        
       df_jeux_histogramme = df_jeux_valide_graphique.copy()     
       df_jeux_histogramme["Nb_jeux_propose"] = 0

    # 3. Cas où seules les validations sont vides
    elif df_jeux_valide_graphique.empty:
     
       df_jeux_histogramme = df_jeux_pret_graphique.copy()
       df_jeux_histogramme["Nb_jeux_valide"] = 0       
       df_jeux_histogramme["statut_valide"] = False
    else : 
       df_jeux_histogramme = pd.merge(
           df_jeux_pret_graphique,
           df_jeux_valide_graphique,
           on=["pseudo", "nom", "classement", "Nouveauté"],
           how="outer",  # 'outer' garde tout, même si un jeu n'est que dans l'un des deux tableaux
       )
       
       # Remplacer les valeurs manquantes (NaN) par 0 ou False selon les colonnes
       df_jeux_histogramme["Nb_jeux_propose"] = df_jeux_histogramme["Nb_jeux_propose"].fillna(0)
       df_jeux_histogramme["Nb_jeux_valide"] = df_jeux_histogramme["Nb_jeux_valide"].fillna(0)
       df_jeux_histogramme["statut_valide"] = df_jeux_histogramme["statut_valide"].fillna(False)

    #  Aggrégation des données pour obtenir la somme par pseudo
    df_jeux_histogramme["Nb_jeux_propose"] = pd.to_numeric(df_jeux_histogramme["Nb_jeux_propose"], errors="coerce").fillna(0).astype(int)   
    df_jeux_histogramme["Nb_jeux_valide"] = pd.to_numeric(df_jeux_histogramme["Nb_jeux_valide"], errors="coerce").fillna(0).astype(int)
    df_grouped = df_jeux_histogramme.groupby("pseudo")[["Nb_jeux_propose", "Nb_jeux_valide"]].sum().reset_index()
    if not df_jeux_histogramme.empty:
   
       fig_hist = px.bar( 
                 df_grouped,
                 x="pseudo",
                 # y="Nb_jeux_propose", 
                 y=["Nb_jeux_propose","Nb_jeux_valide"],
                 #color="Nb_jeux_propose", 
                 ###color=["Nb_jeux_propose","Nb_jeux_valide"],
                 barmode="group",
                 text_auto=True,
                 #color_discrete_map={"Nb_jeux_propose": "#636EFA"}, ###{"Nb_jeux_propose": "#636EFA", "Nb_jeux_valide": "#2CA02C"},
                 width=6000,
                 height=500
       )
       # Améliorer afficher les valeurs au survol dela souris
       fig_hist.update_traces(
           hovertemplate="<b>Pseudo :</b> %{x}<br><b>Type :</b> %{data.name}<br><b>Nombre :</b> %{y}<extra></extra>"
       )
       st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("Aucun jeu prété / validé pour le moment.")

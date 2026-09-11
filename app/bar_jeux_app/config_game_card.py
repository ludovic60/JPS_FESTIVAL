import config_bar_jeux
import storage_jeux
import streamlit as st
import os
import sys
import time
# Ajoute le dossier parent à sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import commun.auth,  commun.config 
import commun.common_store as cs

def nouveaute_def( id_game) :
        info_jeu= storage_jeux.get_info_games(id_game)       
        New = ""
        if ( info_jeu[0].get("mois_sortie")  and  info_jeu[0].get("annee_parution") ) :      
       
                periode_parution = int(str(info_jeu[0].get("annee_parution"))) *100 +  int(str(info_jeu[0].get("mois_sortie")) )
                periode_dernier_festival = (int( cs._secret("ANNEE_FESTIVAL"))-1) *100 + int(cs._secret("MOIS_FESTIVAL") )
                      
                if periode_parution  >  periode_dernier_festival :
                               New = "NOUVEAUTE"
                else :   
                               New = "Ancien"
        else :
                   New = "inconnu"
           
        return New            

def mise_forme_classement(classement) :
    if classement :
        if classement == "FAMILLE":
                  classement_formate = f"⚪⚪⚪ {classement}"
        elif classement == "INITIE":
                  classement_formate = f"🟡⚪⚪ {classement}"
        elif classement == "EXPERT":
                  classement_formate = f"🔴🔴⚪ {classement}"
        elif classement == "EXPERT+":
                  classement_formate = f"🔴🔴🔴 {classement}"
        elif classement == "ENFANT":
                  classement_formate = f"🧸 {classement}"                                        
        elif classement == "JEU DUO":
                  classement_formate = f"👥 {classement}"                                       
        elif classement == "COOP/SEMI COOP":
                  classement_formate = f"🤝 {classement}"                             
        elif classement == "ENQUETE/ESCAPE/ENIGME/CASSETETE":
                  classement_formate = f"🕵️ {classement}"                            
        elif classement == "AMBIANCE":
                  classement_formate = f"🎉 {classement}"
        elif classement == "NON CLASSE":
                  classement_formate = f"🤔 {classement}"
        elif classement == "PBM CLASSEMENT":
                  classement_formate = f"❓ {classement}"
        else : 
                  classement_formate = f"❓❓❓ {classement}"
    else :
                  classement_formate = ""           

    return classement_formate    

def _game_card(g, list_key, user):
    #ckey = f"{list_key}::{str(g['_id'])}"
    ckey_this_game = f"{str(g['_id'])}"
    is_admin = user["role"] == "admin"
    admin_sel = storage_jeux.get_admin_selected()
    
    sugg = storage_jeux.get_suggestions()
    has_selected_this_game=""  
    select_this_game=""

           
    with st.container(border=True):
        c1, c2 = st.columns([1, 3])
        with c1:
            if g.get("couverture"):
                st.image(g["couverture"], width="stretch")
        with c2:
            title = g.get("nom_jeu_complet") or g.get("nom_jeu") or "Jeu"

            st.markdown(f"#### {title}")

            ##### gestion du classement =      
            le_classement = mise_forme_classement(g.get("classement_jps_final"))
            print(f" le classement : {le_classement}")
            meta = " · ".join([x for x in [
                le_classement,
                f"👥 {g.get('nombre_joueurs','')}" if g.get("nombre_joueurs") else "",
                f"🎂 {g.get('age_boite','')}" if g.get("age_boite") else "",
                f"⏱ {g.get('duree','')}" if g.get("duree") else "",
                
            ] if x])
            if meta:
                st.caption(meta)
            cc = st.columns(2)
            with cc[0]:
                     
                if is_admin:
                    # 1
                    select_this_game = [adsel for adsel in admin_sel if str(adsel.get("id_jeux")) == ckey_this_game]
                    # 2.admin a deja retenu auparavant 
                    has_selected_this_game = [admin_sel[0]["id_jeux"] for sadmin in select_this_game]  

                    # Callback exécuté uniquement lors d'un VRAI clic utilisateur
                    def on_admin_change(game_id, currently_selected):
                        mode = "delete" if currently_selected else "insert"
                
                        storage_jeux.toggle_admin_selected(game_id, mode)
                        sugg_this_game = [s for s in sugg if str(s.get("id_jeux")) == ckey_this_game]

                        if sugg_this_game : 
                                if mode == "insert" :
                                        # 1. On ne garde que les suggestions spécifiques à CE jeu
                         
                                        storage_jeux.toggle_all_suggestion(ckey_this_game, "suggestion Retenue")        
                        
                                elif mode == "delete" :
                                       storage_jeux.toggle_all_suggestion(ckey_this_game, "suggestion refusée")        
                                                                   
                    # Passe la fonction SANS les parenthèses () et utilise args=
                    st.checkbox(
                        "Retenir (admin)",
                        value=has_selected_this_game,
                        key=f"s_admin_{ckey_this_game}",
                        on_change=on_admin_change,
                        args=(ckey_this_game, has_selected_this_game),
                    )                                
                       

                    
                else:

                    def on_admin_change(game_id, currently_selected):
                        mode = "delete" if currently_selected else "insert"   
                        storage_jeux.toggle_suggestion(ckey_this_game, user["id"],mode)
                        st.rerun()

                        
                     # 1. On ne garde que les suggestions spécifiques à CE jeu
                    select_this_game = [adsel for adsel in admin_sel if str(adsel.get("id_jeux")) == ckey_this_game]
                    
                    # 2.admin a retenu ce jeu ?
                    has_selected_this_game = [admin_sel[0]["id_jeux"] for sadmin in select_this_game]

                    if has_selected_this_game :
                        val_admin = st.markdown(":red[retenu dans selection final]")
                    
                    # 1. On ne garde que les suggestions spécifiques à CE jeu
                    sugg_this_game = [s for s in sugg if str(s.get("id_jeux")) == ckey_this_game]
                    
                    # 2. On extrait les IDs des utilisateurs ayant suggéré CE jeu
                    uids_this_game = [s["user_id"] for s in sugg_this_game]
                    
                    # 3. L'utilisateur a-t-il suggéré CE jeu ?
                    has_suggested = user["id"] in uids_this_game
                    
                    # 4. Affichage de la checkbox avec la bonne valeur
                    val_check_suggest = st.checkbox("Je suggère ce jeu", 
                                                    value=has_suggested, 
                                                    key=f"sug_{ckey_this_game}",
                                                     on_change=on_admin_change,
                                                     args=(ckey_this_game, has_suggested),)
                    
                  
            with cc[1]:

           
                # 2. Compter combien il y en a
                nb_sugg = storage_jeux.get_game_nb_suggestions(ckey_this_game)
                    
                st.caption(f"👍 {nb_sugg} suggestion(s)")
                if nb_sugg > 0  :
 
                    statut = storage_jeux.get_game_suggestions(ckey_this_game)[0].get("statut")
                   
 
                    if statut == "suggestion Retenue":
                               st.badge("✅ suggestion Retenu")
                    elif statut == "suggestion refusée":   
                       
                                st.badge("❌ suggestion refusée")
                    else :
                                st.badge("suggestion à traiter")
                               
            ################################################################################################################
            ################## generation d'une pop up pour saisir un commentaire
            ################################################################################################################

          
         
            with st.expander(" Ajouter un commentaire"): 
                    st.write(f"Ajouter une note pour : **{g.get("nom_jeu_complet")}**")
                            
                    # Champ de saisie
                    texte = st.text_area("Votre commentaire :", key=f"txt_{ckey_this_game}")
                            
                    if st.button("Enregistrer", type="primary", key=f"button_enreg_{ckey_this_game}" ):
                           if texte.strip():
                              # --- Traitement / Sauvegarde ---
                              storage_jeux.add_request( "remarque fiche jeux", g.get("nom_jeu_complet"), "",  texte, user["pseudo"])
                                         
                              st.success("Commentaire enregistré !")
                          
                    else:
                              st.warning("Veuillez saisir du texte.")
                                        

          
     
            
            with st.expander("Détails du jeu"):
                for fk, fl in config_bar_jeux.GAME_FIELDS:
                    v = g.get(fk, "")
                    if v not in ("", None):
                        st.markdown(f"**{fl}** : {v}")

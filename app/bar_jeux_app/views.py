"""Vues Streamlit pour Bar à jeux."""
 

from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode , DataReturnMode       
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
from config_game_card import _game_card , mise_forme_categorie
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
        st.caption(user["email"])
        if user["role"] == "admin":
            st.markdown("<span class='ws-tag-admin'>Admin</span>", unsafe_allow_html=True)
            pages = ["Jeux sortis depuis dernier festival", "Jeux sortis avant dernier festival", "Demandes d'ajout", "Liste suggestions", "Creation mot de passe", "Liste finale"]
        else : 
            pages = ["Jeux sortis depuis dernier festival", "Jeux sortis avant dernier festival", "Demandes d'ajout", "Liste finale"]
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
    elif page == "Demandes d'ajout":
        _requests_page(user)
    elif page == "Liste suggestions":
        _requests_suggestion_page(user)    
    elif page == "Creation mot de passe":
        _password_page(user)
    else:
        _final_page(user)

def _password_page(user):
     st.set_page_config(page_title="Générateur de Hash Bcrypt", page_icon="🔑")
    
     st.title("🔑 Générateur de Hash Bcrypt")
     st.write("Saisissez un mot de passe ci-dessous pour obtenir sa version hachée.")
    
     ## # Champ de saisie sécurisé
     password_input = st.text_input("Mot de passe à hacher", type="password")
    
     if st.button("Générer le hash"):
        if password_input:
             # Convertit le texte en octets
             password_bytes = password_input.encode('utf-8')
             # Génère un sel et hache le mot de passe
             salt = bcrypt.gensalt()
             hashed = bcrypt.hashpw(password_bytes, salt)
             # Retourne la chaîne encodée à stocker en base                 
             hashed_result = hashed.decode('utf-8') 
             st.success("Mot de passe haché avec succès !")
            
             # Affichage du résultat dans un bloc de code pour faciliter le copie-coller
             st.code(hashed_result, language="text")
              
             st.info("💡 **Remarque :** En raison du salage aléatoire de Bcrypt, chaque clic générera une empreinte différente, même pour un mot de passe identique.")
     else:
         st.warning("Veuillez saisir un mot de passe avant de cliquer.")




def _list_page(title, list_key, user):
    st.title(title)
    
    with st.expander("➕ Demander l'ajout d'un jeu"):
        with st.form(f"req_{list_key}", clear_on_submit=True):
            n = st.text_input("Nom du jeu")
            u = st.text_input("URL myludo")
            if st.form_submit_button("Envoyer la demande", type="primary") and n.strip():
                storage_jeux.add_request("ajout jeux", n, u, list_key, user["pseudo"])
                st.success("Demande envoyée à l'administrateur")

    games = storage_jeux.load_games(list_key)
    
    if not games:
        st.info("Aucun jeu dans cette liste.")
        return

    # Champ de saisie utilisateur
    search_query = st.text_input(
        "🔎 Rechercher un jeu (nom ou URL)",
        placeholder="Ex: Catan, https://...",
        key=f"game_search_input_{list_key}"  # Clé rendue unique par list_key
    ).strip().lower()

    # Filtrage de la liste de jeux
    filtered_games = []

    for g in games:
        title = (g.get("nom_jeu_complet") or g.get("nom_jeu") or "").lower()
        url = (g.get("url_myludo") or "").lower()  # Sécurisé avec str vide si None
        
        # Validation si le terme recherché est présent
        if not search_query or (search_query in title or search_query in url):
            filtered_games.append(g)

    # Affichage des cartes filtrées
    if filtered_games:
        per_row = 3
        # FIX : On utilise len(filtered_games) ici !
        for i in range(0, len(filtered_games), per_row):
            cols = st.columns(per_row)
            for j, g in enumerate(filtered_games[i:i + per_row]):
                with cols[j]:
                    _game_card(g, list_key, user)
    else:
        st.info("Aucun jeu ne correspond à votre recherche.")
  
   
def _requests_suggestion_page(user):
    st.title("liste des suggestions par les joueurs")


def _requests_page(user):
    st.title("Demandes d'ajout de jeux")
    reqs = storage_jeux.get_requests("ajout jeux")
    if not reqs:
        st.info("Aucune demande.")
        return
    for r in reqs:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{r['name']}** — demandé par {r['by']}")
            if r.get("myludo_url"):
                c1.markdown(f"[Lien myludo]({r['myludo_url']}) · liste : `{r['list_key']}`")
            if user["role"] == "admin":
                if c2.button("Retirer", key=f"rmreq_{r['id']}"):
                    storage_jeux.remove_request(r["id"])
                    st.rerun()


def _final_page(user):
    st.title("Liste finale — Prêts")



    # --- EXTRACTION DES DONNEES UTILES ---
        #--- liste des jeux
    finals = storage_jeux.final_games()
   
   
    users = cs.get_users_loaner()
    loans = storage_jeux.get_loans()
    current_user = user
    is_admin = current_user == "admin"
    

    pseudo_list = list(u["pseudo"] for u in users)

           
    # emplacement reservé pour le bouton de validation du pret par les utilisateurs
    if not finals:
        st.info("Aucun jeu retenu par l'admin pour l'instant.")
        return           
    
           
   # st.session_state.grid_state={}
   #           for ul in loans:   
   #                           if ul[0].get("_id") ==   u[0].get("_id") and    ul[0].get("_id")   == g[0].get("_id")  :  
   #                          row[u[0].get("pseudo")] = 1  
   # st.session_state.grid_state[(game, pseudo)] = (True, True)


   
    # --- PARTIE SUPERIEURE : GRAPHIQUES ---

    col_graph1, col_graph2, col_graph3 = st.columns(3)


    ###########---- 1. Histogramme par joueur (Validés vs Cochés Utilisateur)

    with col_graph1:
    
          st.subheader("Validations par Joueur")
          nb_jeux_histogramme = []
          for u in pseudo_list:
                   nb_jeux_histogramme.append(
                       {"Utilisateur": u, "Nb jeux": "pret par user", "Valeur":1}
                   )
                   nb_jeux_histogramme.append({"Utilisateur": u, "Nb jeux": "pret validé (Admin)", "Valeur":1})
          df_jeux_histogramme  = pd.DataFrame(nb_jeux_histogramme)
               
          fig_hist = px.bar(
              df_jeux_histogramme,
              x="Utilisateur",
              y="Valeur",
              color="Nb jeux",
              barmode="group",
              color_discrete_map={"pret par user": "#636EFA", "pret validé (Admin)": "#2CA02C"},
              width=1000,
              height=800 
          )
          st.plotly_chart(fig_hist, width=True)

    ###########----2. Camembert Nouveautés (jeux cochés au moins une fois par un utilisateur)
    with col_graph2:
          st.subheader("Produits cochés par Nouveauté")
          df_cochis = df_jeux_histogramme[df_jeux_histogramme["Valeur"] > 0]
          if not df_cochis.empty:
              df_nov = (
                  df_cochis["Nb jeux"]
                  .map({True: "Nouveauté", False: "Ancien"})
                  .value_counts()
                  .reset_index()
              )
              df_nov.columns = ["Type", "Nombre"]
              fig_pie_nov = px.pie(df_nov, names="Type", values="Nombre", hole=0.3, width=1000, height=800 )
              st.plotly_chart(fig_pie_nov, width=True)
          else:
              st.info("Aucun jeu coché pour le moment.")

      ###########----3. Camembert Catégories (Produits cochés au moins une fois par un utilisateur)
    with col_graph3:
          st.subheader("Jeux cochés par Catégorie")
          if not df_cochis.empty:
              df_cat = df_cochis["Nb jeux"].value_counts().reset_index()
              df_cat.columns = ["Catégorie", "Nombre"]
              fig_pie_cat = px.pie(df_cat, names="Catégorie", values="Nombre", hole=0.3, width=1000, height=800 )
              st.plotly_chart(fig_pie_cat, width=True)
          else:
              st.info("Aucun produit coché pour le moment.")

    st.divider()
    st.caption("Tableau croisé : jeux retenus par l'admin × personnes. Cochez les jeux que vous pouvez prêter.")


    ###################################################################################################
    ###########  gestion du tableau des prêts   
    ###################################################################################################
    # creation des lignes du futur tableau croisé         
    row_jeux = []

    def on_change_plusieurs_exemplaires(game_id, player_key, new_val):
          toggle_admin_selected(game_id, new_val)
    def on_change_prete(game_id, player_key, new_val):
           return 1        
    def on_change_admin(game_id, player_key, new_val):
           return 2         
 
    for game in finals:
        
        g = storage_jeux.get_info_games( game.get('id_jeux'))

        ######   gestion du staut de nouveauté
      
        if ( g[0].get("mois_sortie")  and  g[0].get("annee_parution") ) :      
       
                   periode_parution = int(str(g[0].get("annee_parution"))) *100 +  int(str(g[0].get("mois_sortie")) )
                   periode_dernier_festival = (int( cs._secret("ANNEE_FESTIVAL"))-1) *100 + int(cs._secret("MOIS_FESTIVAL") )
           
                      
                   if periode_parution  >  periode_dernier_festival :
                               New = "NOUVEAUTE"
                   else :   
                               New = "Ancien"
        else :
                   New = "inconnu"                    
        #####################       

       
        row = {"nouveaute" : New, "Annee": g[0].get("annee_parution"),
               "Categorie jeu": mise_forme_categorie(g[0].get("classement_jps_final")),
               "Couverture Jeu": g[0].get("couverture"),
               "Jeu": g[0].get("nom_jeu_complet"),
               "Plusieurs exmplaires souhaitées":"False",
               "Total coché par joueur": "" ,
               "Total coché validé par admin": "" }
        #####################  
        ### gestion des cases à coché 
        for idx, j in enumerate(pseudo_list):
               player_key = f"j{idx+1}"
               row[f"{player_key}_prete"] = 1 ## get_prete_value(game_id, player_key)
               row[f"{player_key}_admin"] = 1 ## get_admin_value(game_id, player_key)

        row_jeux.append(row)


    if "df_jeux" not in st.session_state:
          df_jeux = pd.DataFrame(row_jeux)
          st.session_state["df_jeux"] = df_jeux 
 
    
        
    # --- Colonnes ---
    gb = GridOptionsBuilder.from_dataframe(df_jeux)
    gb.configure_column("Plusieurs exmplaires souhaitées", editable=True, cellRenderer="agCheckboxCellRenderer")
        
    for idx, j in enumerate(pseudo_list):
            player_key = f"j{idx+1}"
            gb.configure_column(
                f"{player_key}_prete",
                headerName=j,
                editable=True,
                cellRenderer="agCheckboxCellRenderer",
            )
            gb.configure_column(
                f"{player_key}_admin",
                headerName="Validé",
                editable=(user["role"] == "admin"),
                cellRenderer="agCheckboxCellRenderer",
            )


    # --- CALCUL DES DONNÉES COMPLÉMENTAIRES ---
    # Traitement des compteurs

    for j in pseudo_list:
         st.session_state.df_jeux[f"{j}_user"] = df_jeux["Jeu"].apply(
            lambda pid: st.session_state.grid_state[(pid, j)][0]
         )
         st.session_state.df_jeux[f"{j}_admin"] = df_jeux["Jeu"].apply(
            lambda pid: st.session_state.grid_state[(pid, j)][1]
        )

    # Compteurs par jeux
    st.session_state.df_jeux["Total coché par joueur"] = st.session_state.df_jeux[[f"{j}_user" for j in pseudo_list]].sum(axis=1)
    st.session_state.df_jeux["Total coché validé par admin"] = st.session_state.df_jeux[[f"{j}_admin" for j in pseudo_list]].sum(axis=1) 

    # Compteurs par joueur
    user_by_player = {j: st.session_state.df_jeux[f"{j}_user"].sum() for j in pseudo_list}
    admin_by_player = {j: st.session_state.df_jeux[f"{j}_admin"].sum() for j in pseudo_list}





    image_renderer = JsCode(
        """
        class ImageRenderer {
                init(params) {
                    this.eGui = document.createElement('img');
                    this.eGui.setAttribute('src', params.value);
                    this.eGui.setAttribute('style', 'height: 45px; width: auto; border-radius: 4px; vertical-align: middle;');
                }
                getGui() {
                    return this.eGui;
                }
        }
        """
     )


    grid_options = gb.build()
        
    grid_response = AgGrid(
            df_jeux,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.VALUE_CHANGED,   # renvoie dès qu'une cellule change
            data_return_mode=DataReturnMode.AS_INPUT,
            allow_unsafe_jscode=True,
            fit_columns_on_grid_load=True,
        )

      









     # --- Détection des changements ---
    old_df = st.session_state.get("old_grid_df")
     
    if old_df is not None:
         checkbox_cols = [c for c in new_df.columns if c.endswith(("_prete", "_admin")) or c == "multi_exemplaires"]
         for i in df_jeux.index:
             game_id = new_df.at[i, "_id"]
             for col in checkbox_cols:
                 old_val = old_df.at[i, col]
                 new_val = new_df.at[i, col]
                 if old_val != new_val:
                     if col.endswith("_prete"):
                         player_key = col.replace("_prete", "")
                         on_change_prete(game_id, player_key, new_val)
                     elif col.endswith("_admin"):
                         player_key = col.replace("_admin", "")
                         on_change_admin(game_id, player_key, new_val)
                     elif col == "multi_exemplaires":
                         on_change_plusieurs_exemplaires(game_id, new_val)
     
    st.session_state["old_grid_df"] = df_jeux.copy()





  ###  # Colonnes fixes de gauche
  ###  column_defs = [
  ###      {"field": "nouveaute", "headerName": "nouveaute", "width": 150},
  ###      {"field": "Annee", "headerName": "Annee", "width": 80},
  ###      {"field": "Categorie jeu", "headerName": "Categorie jeu", "width": 110},
  ###      {"field": "Couverture Jeu", "cellRenderer": image_renderer,"headerName": "Couverture Jeu", "width": 110},
  ###      {"field": "Jeu", "headerName": "Jeu", "width": 110},
  ###      {"field": "Plusieurs exmplaires souhaitées", "headerName": "Plusieurs exmplaires souhaitées", "width": 110},
  ###      {"field": "Total coché par joueur", "headerName": "Total coché par joueur", "width": 110},
  ###      {"field": "Total coché validé par admi", "headerName": "Total coché validé par admi", "width": 110},
        
  ###  ]


  ### for idx, j in enumerate(pseudo_list):
  ###      player_key = f"j{idx+1}"
  ###      group_col = {
  ###          "headerName": j,  # Première ligne d'en-tête (Nom du Joueur)
  ###          "children": [
  ###              {
  ###                  "field": f"{player_key}_prete",
  ###                  "headerName": "Je prête",  # Seconde ligne d'en-tête
  ###                  "editable": True,
  ###                  "cellRenderer": "agCheckboxCellRenderer",  # Case à cocher native
  ###                  "width": 110,
  ###              },
  ###              {
  ###                  "field": f"{player_key}_admin",
  ###                  "headerName": "Validé",
  ###                  "editable": (user["role"] == "admin"),
  ###                  "cellRenderer": "agCheckboxCellRenderer",
  ###                 "width": 140,
  ###                 # Style conditionnel : Vert si la case est cochée
  ###                 "cellStyle": {
  ###                     "styleConditions": [
  ###                         {
  ###                             "condition": "x === true",
  ###                             "style": {
  ###                                 "backgroundColor": "#d4edda",
  ###                                 "color": "#155724",
  ###                             },
  ###                         }
  ###                     ]
  ###                 },
  ###              },
  ###          ],
  ###      }
  ###      column_defs.append(group_col)
    

  ###  # Configuration du tableau avec AgGrid
  ###  gb = GridOptionsBuilder.from_dataframe(df_jeux)
    
  ###  gb.configure_default_column(
  ###       resizable=True,
  ###       filterable=True,
  ###       editable=False,
  ###   )
  ###  gb.configure_grid_options(
  ###      wrapHeaderText=True,
  ###      autoHeaderHeight=True,
  ###      rowHeight=60,  # Augmente la hauteur des lignes pour bien voir les images
  ###  )
    


  ###  # Applique un thème complet avec bordures
  ##   grid_options = gb.build()

  ###   grid_options["columnDefs"] = column_defs
 
  ### custom_css = {
  ###      ".ag-header-group-cell": {
  ###         "border-right": "none !important",
  ###         "border-left": "none !important",
  ##     },
  ###     ".ag-cell": {
  ###         "border-right": "1px solid #c6c6c6 !important",
  ###     },
  ###     ".ag-header-cell, .ag-header-group-cell": {
  ###         "border-right": "1px solid #c6c6c6 !important",
  ###     },
  ### }

  ###  grid_response = AgGrid(
  ###     df_jeux,
  ###     gridOptions=grid_options,
  ###     custom_css=custom_css, 
  ###     theme="balham",  # Thème avec bordures et grille bien visibles
  ###     allow_unsafe_jscode=True, ## pour gerer l'affichage des images grace aux url
  ###     update_mode=GridUpdateMode.VALUE_CHANGED,  # Déclenche une mise à jour à chaque clic
  ###     # data_return_mode=DataReturnMode.AS_INPUT,
  ###     fit_columns_on_grid_load=True,
  ###  )

  ###  # Récupération du tableau mis à jour
  ###  updated_df = grid_response["data"]

  ###  # Comparaison avec l'état précédent pour identifier la modification
  ###  if "previous_df" in st.session_state:
  ###      prev_df = st.session_state["previous_df"]
    
  ###      # Détection des changements cellule par cellule
  ###      diff = (updated_df != prev_df) & ~(updated_df.isna() & prev_df.isna())
    
  ###      for col in diff.columns:
  ###          if diff[col].any():
  ###              # Une valeur a changé dans la colonne `col`
  ###              ligne_modifiee = diff[diff[col]].index[0]
  ###              nouvelle_valeur = updated_df.loc[ligne_modifiee, col]
            
  ###              # --- Action A : Coche "Je prête" ---
  ###              if col.endswith("_prete"):
  ###                  st.toast(f"Action Prêt ({col}) : nouvelle valeur = {nouvelle_valeur}")
  ###                  # Insérez ici votre fonction spécifique (ex: mise à jour BDD prêt)
                
  ###              # --- Action B : Coche "Validé" (Admin) ---
  ###              elif col.endswith("_admin"):
  ###                  st.toast(f"Action Validation Admin ({col}) : nouvelle valeur = {nouvelle_valeur}")
  ###                  # Insérez ici votre fonction spécifique (ex: envoi mail/validation)

  ###  # Sauvegarde de l'état actuel pour le prochain tour
  ###  st.session_state["previous_df"] = updated_df


     

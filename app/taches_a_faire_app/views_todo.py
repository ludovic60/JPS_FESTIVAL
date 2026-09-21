
"""Vues / écrans Streamlit."""
import html
import logging
import streamlit as st
from  storage_todo import  get_todo, add_todo, update_todo, delete_todo
import sys
from pathlib import Path
import time 

# Ajoute le dossier parent (la racine du projet) à sys.path
racine_projet = Path(__file__).resolve().parent.parent
sys.path.append(str(racine_projet))

import commun.auth
import commun.common_store

# ==========================================================================
# APPLICATION PRINCIPALE
# ==========================================================================
def main_app(user: dict):
    st.session_state["user_id_current"] = user["id"]
    with st.sidebar:
        st.markdown("### 📋 taches à faire ")
        st.write(f"**{user['pseudo']}**")
        st.caption(user["email"])
        if user["role"] == "admin":
            st.markdown("<span class='ws-tag-admin'>Admin</span>", unsafe_allow_html=True)

     

        st.divider()
        if st.button("Déconnexion"):
            commun.auth.logout()
            st.rerun()
 
    todo_page(user)







def todo_page(user):
     # ---- Tâches ----
       if user["role"] == "admin":
            st.markdown("<span class='ws-tag-admin'>Admin</span>", unsafe_allow_html=True)

            with st.form("add_todo_form", clear_on_submit=True):
                        c1, c2 = st.columns([4, 1])
                        new_label = c1.text_input("Nouveau todo", label_visibility="collapsed",
                                                  placeholder="Nom de la nouvelle tâche")
                        if c2.form_submit_button("Ajouter", type="primary") and new_label.strip():
                            add_todo(new_label)
                            st.rerun()
       c1, c2, c3,c4 ,c5, c6 , c7 = st.columns([4, 3, 2, 4, 2 , 2, 2])
       c1.write("nom de la tache")
       c2.write("affecte a ")
       c3.write("statut")
       c4.write("commentaire")
       c5.write("modifier")
       c6.write("terminer ")
       c7.write("supprimer ")                     
       for t in get_todo():

           
            label_todo = c1.text_input("t", value=t["todo"], key=f"edit_{t["_id"]}",
                                   label_visibility="collapsed")
            label_affecte = c2.text_input("t", value=t["affecte"], key=f"edit_qui_{t["_id"]}",
                                   label_visibility="collapsed")
            label_statut = c3.text_input("t", value=t["statut"], key=f"edit_statut_{t["_id"]}",
                                   label_visibility="collapsed")

            commentaire_statut = c4.text_input("t", value=t["commentaire"], key=f"edit_comment_{t["_id"]}",
                                   label_visibility="collapsed")
           
            if c5.button("modifier", key=f"termin_{t["_id"]}"):
                update_todo(t["_id"] ,label_affecte , label_statut,commentaire_statut)
                get_todo()
                st.rerun()
           
            if c6.button("terminer", key=f"modif_{t["_id"]}"):
                update_todo(t["_id"] ,label_affecte, "terminer")
                get_todo()
                st.rerun()
        
            if c7.button("Supprimer", key=f"supprim_{t["_id"]}"):
                delete_todo(t["_id"])              
                get_todo()
                st.rerun()


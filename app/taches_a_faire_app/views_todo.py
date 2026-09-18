
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
                            add_todo_tb(label)
                            st.rerun()
       for t in get_todo():
            c1, c2, c3,c4 = st.columns([4, 1, 4, 1])
            label_todo = c1.text_input("t", value=t["todo"], key=f"edit_{t["_id"]}",
                                   label_visibility="collapsed")
            label_affecte = c2.text_input("t", value=t["affecte"], key=f"edit_qui_{t["_id"]}",
                                   label_visibility="collapsed")
            label_statut = c3.text_input("t", value=t["statut"], key=f"edit_statut_{t["_id"]}",
                                   label_visibility="collapsed")
            
            if c3.button("terminer", key=f"modif_{t["_id"]}"):
                update_todo(t["_id"] ,label_affecte , label_statut)
     
                st.rerun()
           
            if c3.button("terminer", key=f"modif_{t["_id"]}"):
                update_todo(t["_id"] ,label_affecte, "terminer")
     
                st.rerun()
            # if c3.button("Supprimer"):
            if c4.button("Supprimer", key=f"supprim_{t["_id"]}"):
                delete_todo(t["_id"])
              
                st.rerun()



"""Vues / écrans Streamlit."""
import html
import logging
import streamlit as st
from  storage_presence import get_presence, clear_user_presence, clear_all_presence, get_all_presence, get_tasks, add_task, update_task, delete_task, set_presence
import sys
from pathlib import Path
from config_presence import DAYS, PERIODS, PERIOD_LABELS, SLOT_KEYS, DAYS_INSTALL, PERIODS_INSTALL,TYPE_TASK_INSTALL , TYPE_TASK_ANIMATION ,DAYS_ANIMATION , PERIODS_ANIMATION ,PERIODS_ENTIERE, SLOT_KEYS_INSTALL ,SLOT_KEYS_ANIMATION, LIST_TYPE_TASK
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

        pages = ["liste des taches"]

        st.divider()
        if st.button("Déconnexion"):
            commun.auth.logout()
            st.rerun()

    if page == "liste des taches":
       todo_page(user)







def todo_page():
     # ---- Tâches ----

        for t in get_todo():
            c1, c2, c3 = st.columns([4, 1, 1])
            label = c1.text_input("t", value=t["todo"], key=f"edit_{t["_id"]}",
                                   label_visibility="collapsed")
            label = c2.text_input("t", value=t["statut"], key=f"edit_{t["_id"]}",
                                   label_visibility="collapsed")
            
            if c3.button("terminer", key=f"modif_{t["_id"]}"):
                update_todo(t["_id"] "terminer)
     
                st.rerun()
            # if c3.button("Supprimer"):
            if c4.button("Supprimer", key=f"supprim_{t["_id"]}"):
                delete_todok(t["_id"])
              
                st.rerun()


                st.rerun()

"""Authentification (nom, email, mot de passe) pour Bar à jeux."""
import streamlit as st
from email_validator import validate_email, EmailNotValidError

import os
import sys
# Ajoute le dossier parent à sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from weekend_app.security import generate_token
import storage


def current_user():
    return st.session_state.get("jeux_user")


def login(pseudo , email, password):

    print("pseudo :"+pseudo+"fin")
    print("email :"+email+"fin")
    print("password :"+password+"fin")
    
    if not email == " ":
        try:
            validate_email(email)
        except EmailNotValidError:
            return "Adresse email invalide"
        user = storage.check_credentials("email", email.strip(), password)
        if not user:
            return "Email ou mot de passe incorrect"
    elif not pseudo == " ":
        user = storage.check_credentials("pseudo", pseudo.strip(), password)
        if not user:
            return "pseudo ou mot de passe incorrect"
    else :
       st.info("💡Merci de renseigner soit votre pseudo ou votre email ")

    if not user:
        return "Email ou pseudo ou mot de passe incorrect"
    st.session_state["jeux_user"] = _public(user)
    return None


def register(name, email, password):
    if len(name.strip()) < 1:
        return "Le nom est requis"
    if len(password) < 6:
        return "Mot de passe : 6 caractères minimum"
    try:
        validate_email(email)
    except EmailNotValidError:
        return "Adresse email invalide"
    user, err = storage.create_user(email.strip(), name, password)
    if err:
        return err
    st.session_state["jeux_user"] = _public(user)
    return None


def logout():
    st.session_state.pop("jeux_user", None)


def _public(u):
    return {"_id": str(u["_id"]), "email": u["email"], "pseudo": u["pseudo"], "role": u["role"]}

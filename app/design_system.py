"""Design System réutilisable (Streamlit) — « Swiss / High-Contrast ».

Fichier autonome, copiable tel quel dans vos autres applications Streamlit.
Usage :
    import streamlit as st
    from design_system import inject, THEME
    st.set_page_config(page_title="...", layout="wide")
    inject()

Le thème global (couleurs/police) se règle aussi dans .streamlit/config.toml.
"""
import streamlit as st

THEME = {
    "primary": "#002FA7",       # Klein Blue
    "primary_hover": "#002277",
    "accent": "#FF2A2A",
    "background": "#F3F4F6",
    "surface": "#FFFFFF",
    "border": "#E5E7EB",
    "text": "#0A0A0A",
    "muted": "#4B5563",
    "font_heading": "Outfit",
    "font_body": "IBM Plex Sans",
}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"], .stMarkdown, .stButton, input, textarea {{
    font-family: '{font_body}', sans-serif;
}}
h1, h2, h3, h4 {{
    font-family: '{font_heading}', sans-serif !important;
    letter-spacing: -0.02em;
    color: {text};
}}
.stApp {{ background: {background}; }}

/* Boutons */
.stButton > button {{
    border-radius: 2px;
    border: 1px solid {border};
    font-weight: 600;
    transition: background-color .18s ease, color .18s ease, border-color .18s ease;
}}
.stButton > button[kind="primary"] {{
    background: {primary};
    border-color: {primary};
    color: #fff;
}}
.stButton > button[kind="primary"]:hover {{
    background: {primary_hover};
    border-color: {primary_hover};
}}

/* Cartes / conteneurs bordés */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 2px !important;
}}

/* Badges */
.ws-badge {{
    display:inline-block; background:{primary}1A; color:{primary};
    border:1px solid {primary}33; border-radius:2px;
    padding:1px 8px; margin:2px; font-size:12px; font-weight:600;
}}
.ws-tag-admin {{
    background:{accent}; color:#fff; border-radius:2px;
    padding:1px 6px; font-size:10px; text-transform:uppercase; letter-spacing:.06em;
}}

/* Tableau récap */
.ws-recap {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
.ws-recap th, .ws-recap td {{
    border: 1px solid {border}; padding: 8px 10px; text-align: left; vertical-align: top;
}}
.ws-recap thead th {{ background: {text}; color: #fff; font-family: '{font_heading}', sans-serif; }}
.ws-recap tbody td:first-child {{ font-weight: 600; background: {surface}; }}
.ws-empty {{ color: #cbd5e1; }}
</style>
"""


def inject():
    st.markdown(_CSS.format(**THEME), unsafe_allow_html=True)

import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()
USER = os.getenv("APP_USER")
PASSWORD = os.getenv("APP_PASSWORD")

def login():
    st.title("3D.IEGO - Acceso")
    with st.form("login_form"):
        username = st.text_input("Usuario", placeholder="Usuario", key="username_input", label_visibility="collapsed")
        password = st.text_input("Contraseña", placeholder="Contraseña", type="password", key="password_input", label_visibility="collapsed")
        submit = st.form_submit_button("Ingresar")

        if submit:
            if username == USER and password == PASSWORD:
                st.session_state["logueado"] = True
            else:
                st.error("Credenciales incorrectas")

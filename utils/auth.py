import streamlit as st
import os
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()
USER = os.getenv("APP_USER")
PASSWORD = os.getenv("APP_PASSWORD")

def login():
    st.markdown("<br><br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])  # centrar el form

    with col2:
        st.markdown("### 3D.IEGO - Acceso")

        with st.form("login_form"):
            username = st.text_input(
                "Usuario",
                placeholder="Usuario",
                key="username_input"
            )
            password = st.text_input(
                "Contraseña",
                placeholder="Contraseña",
                type="password",
                key="password_input"
            )
            submit = st.form_submit_button("Ingresar")

            if submit:
                if username == USER and password == PASSWORD:
                    st.session_state["logueado"] = True
                else:
                    st.error("❌ Credenciales incorrectas")

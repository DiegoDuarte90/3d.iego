import streamlit as st
import os
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()
USER = os.getenv("APP_USER")
PASSWORD = os.getenv("APP_PASSWORD")

def login():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 3D.IEGO - Acceso")

        # Formulario
        with st.form("login_form", clear_on_submit=False):
            st.text_input(
                "Usuario",
                placeholder="Usuario",
                key="username_input",
            )
            st.text_input(
                "Contraseña",
                placeholder="Contraseña",
                type="password",
                key="password_input",
            )
            submit = st.form_submit_button("Ingresar", type="primary", use_container_width=True)

        # Validación (fuera del with del form) leyendo desde session_state
        if submit:
            username = st.session_state.get("username_input", "")
            password = st.session_state.get("password_input", "")

            if username == USER and password == PASSWORD:
                st.session_state["logueado"] = True
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas")


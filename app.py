import streamlit as st
from dotenv import load_dotenv
import os

from utils.auth import login
from utils.session import guardar_sesion, sesion_valida, eliminar_sesion
from modulos.costos import mostrar_costos
from modulos.pedidos import mostrar_pedidos
from modulos.cuentas import mostrar_cuentas
from utils.db import init_db


init_db()  # crea tablas si no existen

# Configuración general de la app
st.set_page_config(page_title="3D.IEGO", layout="wide")

# Cargar variables de entorno
load_dotenv()
USER = os.getenv("APP_USER")

# Control de sesión
if "logueado" not in st.session_state:
    st.session_state["logueado"] = sesion_valida()

# Si no está logueado, mostrar login
if not st.session_state["logueado"]:
    login()
    if st.session_state.get("logueado") is True:
        guardar_sesion(USER)

# Si está logueado, mostrar menú y secciones
else: 
    st.sidebar.title("Menú")
    opcion = st.sidebar.radio(
        label="Menú",  # obligatorio aunque después lo ocultes
        options=["Costos y tiempos", "Pedidos", "Cuentas", "Salir"],
        index=0,
        label_visibility="collapsed"
    )

    if opcion == "Costos y tiempos":
        mostrar_costos()

    elif opcion == "Pedidos":
        mostrar_pedidos()

    elif opcion == "Cuentas":
        mostrar_cuentas()

    elif opcion == "Salir":
        eliminar_sesion()
        st.session_state["logueado"] = False
        st.rerun()


import streamlit as st
from utils.auth import login
from pages.costos import mostrar_costos

# Control de login
if "logueado" not in st.session_state:
    st.session_state["logueado"] = False

if not st.session_state["logueado"]:
    login()
else:
    st.sidebar.title("Menú")
    opcion = st.sidebar.radio("Ir a:", ["Costos y tiempos", "Pedidos", "Cuentas", "Salir"], index=0)

    if opcion == "Costos y tiempos":
        mostrar_costos()

    elif opcion == "Pedidos":
        st.header("📦 Control de pedidos")
        st.info("Acá vas a cargar y ver todos los pedidos de impresión.")

    elif opcion == "Cuentas":
        st.header("💸 Registro de ingresos y gastos")
        st.info("Llevá el control de lo que entra y sale en 3D.IEGO.")

    elif opcion == "Salir":
        st.session_state["logueado"] = False
        st.experimental_rerun()

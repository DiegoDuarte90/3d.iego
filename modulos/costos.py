import streamlit as st
from utils.config import cargar_config, guardar_config

def mostrar_costos():
    st.title("⏱️ Cálculo de costos y tiempos")

    if "config" not in st.session_state:
        st.session_state["config"] = cargar_config()

    config = st.session_state["config"]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📥 Datos de impresión")

        with st.columns([1, 2, 1])[1]:
            horas = st.number_input("Horas de impresión", min_value=0, value=0, format="%d")

        with st.columns([1, 2, 1])[1]:
            minutos = st.number_input("Minutos de impresión", min_value=0, max_value=59, value=0, format="%d")

        with st.columns([1, 2, 1])[1]:
            gramos = st.number_input("Gramos usados", min_value=0, value=0, format="%d")

        with st.columns([1, 2, 1])[1]:
            margen_ganancia = st.number_input(
                "Margen de ganancia (ej: 2 = 100%)",
                min_value=1,
                value=int(config.get("margen_ganancia", 2)),
                format="%d"
            )
            config["margen_ganancia"] = margen_ganancia

    with col2:
        st.subheader("⚙️ Gastos fijos")

        with st.columns([1, 2, 1])[1]:
            config["precio_kg"] = st.number_input("Precio por KG", value=config["precio_kg"])

        with st.columns([1, 2, 1])[1]:
            config["precio_kwh"] = st.number_input("Precio KWh", value=config["precio_kwh"])

        with st.columns([1, 2, 1])[1]:
            config["consumo_watts"] = st.number_input("Consumo real por hora (W)", value=config["consumo_watts"])

        with st.columns([1, 2, 1])[1]:
            config["vida_util_horas"] = st.number_input("Vida útil de la máquina (horas)", value=config["vida_util_horas"])

        with st.columns([1, 2, 1])[1]:
            config["precio_repuestos"] = st.number_input("Precio total de repuestos", value=config["precio_repuestos"])

        with st.columns([1, 2, 1])[1]:
            config["margen_error_pct"] = st.number_input("% de margen de error", value=config["margen_error_pct"])

        guardar_config(config)

    if horas + minutos + gramos > 0:
        tiempo_horas = horas + (minutos / 60)
        costo_filamento = (gramos * config["precio_kg"]) / 1000
        costo_electricidad = ((config["precio_kwh"] * config["consumo_watts"]) / 1000) * tiempo_horas
        costo_desgaste = (config["precio_repuestos"] / config["vida_util_horas"]) * tiempo_horas
        margen_error = (costo_filamento + costo_electricidad + costo_desgaste) * (config["margen_error_pct"] / 100)
        costo_total = costo_filamento + costo_electricidad + costo_desgaste + margen_error
        precio_total = costo_total * config["margen_ganancia"]
        ganancia_total = precio_total - costo_total

        st.markdown("---")
        st.markdown("### 📊 Resultados")

        col1, col2 = st.columns(2)

        with col1:
            st.success(f"🎯 **Costo de filamento:** \n\n${costo_filamento:,.2f}")
            st.info(f"⚡ **Costo electricidad:** \n\n${costo_electricidad:,.2f}")
            st.warning(f"🛠️ **Costo desgaste:** \n\n${costo_desgaste:,.2f}")
            st.info(f"💸 **Margen de error:** \n\n${margen_error:,.2f}")

        with col2:
            st.success(f"🧮 **Costo total base:** \n\n${costo_total:,.2f}")
            st.warning(f"🤑 **Precio final sugerido:** \n\n${precio_total:,.2f}")
            st.success(f"📈 **Ganancia estimada:** \n\n${ganancia_total:,.2f}")

# modulos/entregas.py
from __future__ import annotations
import streamlit as st
from datetime import date
import pandas as pd

from utils.db_app import (
    get_session,
    upsert_cliente,
    search_clientes,
    get_cliente_by_nombre,
    crear_entrega,
    ultimas_entregas,
    Cliente,
    EntregaItem,
)

# ---------------- Helpers ----------------
def _ensure_items_state():
    if "ent_items_df" not in st.session_state:
        st.session_state["ent_items_df"] = pd.DataFrame(
            [{"pieza": "", "cantidad": 1, "precio_unitario": 0.0}]
        )

def _nombres_clientes(filtro: str) -> list[str]:
    clientes = search_clientes(filtro.strip() if filtro else "", limit=50)
    return [c.nombre for c in clientes]

@st.dialog("Nuevo cliente")
def _modal_nuevo_cliente(prefill: str = ""):
    st.write("Completá los datos del cliente:")
    nombre = st.text_input("Nombre *", value=prefill, key="dlg_nombre")
    col1, col2 = st.columns(2)
    tel = col1.text_input("Teléfono", key="dlg_tel")
    email = col2.text_input("Email", key="dlg_email")
    dire = st.text_input("Dirección", key="dlg_dir")

    if st.button("💾 Guardar", type="primary", use_container_width=True):
        if not nombre.strip():
            st.error("El nombre es obligatorio.")
            st.stop()
        cli = upsert_cliente(nombre=nombre, telefono=tel, email=email, direccion=dire)
        st.session_state["cliente_seleccionado"] = cli.nombre
        st.success("Cliente guardado.")
        st.rerun()

# ---------------- Pantalla principal ----------------
def mostrar_entregas():
    st.title("📦 Entregas")
    _ensure_items_state()

    # -------- Cliente --------
    st.subheader("Cliente")
    col_left, col_right = st.columns(2)

    with col_left:
        query = st.text_input("Buscar un cliente", placeholder="Escribí un nombre…", key="filtro_cli")

        resultados = _nombres_clientes(query)
        opciones = resultados + ["➕ Nuevo cliente…"] if resultados else ["➕ Nuevo cliente…"]

        eleccion = st.radio(
            label="Resultados",
            options=opciones,
            index=0,
            label_visibility="collapsed",
            key="radio_resultados",
        )

        if eleccion == "➕ Nuevo cliente…":
            if st.button("Crear cliente", use_container_width=True):
                _modal_nuevo_cliente(prefill=query.strip())
            if "cliente_seleccionado" not in st.session_state:
                st.session_state["cliente_seleccionado"] = ""
        else:
            if eleccion != st.session_state.get("cliente_seleccionado"):
                st.session_state["cliente_seleccionado"] = eleccion

    with col_right:
        seleccionado = st.session_state.get("cliente_seleccionado", "")
        if seleccionado:
            cli = get_cliente_by_nombre(seleccionado)
            if cli:
                st.markdown(f"### {cli.nombre}")
                c1, c2 = st.columns(2)
                c1.text_input("Teléfono", value=cli.telefono or "", disabled=True)
                c2.text_input("Email", value=cli.email or "", disabled=True)
                st.text_input("Dirección", value=cli.direccion or "", disabled=True)
                st.caption("Para editar, usá “➕ Nuevo cliente…” y guardá con el mismo nombre.")
        else:
            st.info("Seleccioná un cliente a la izquierda o creá uno nuevo.")

    cliente_ok = bool(st.session_state.get("cliente_seleccionado"))

    st.divider()

    # -------- Piezas --------
    st.subheader("Piezas")
    st.caption("Completá **pieza**, **cantidad** y **precio unitario**. Podés agregar filas con el +.")

    df_prev = st.session_state["ent_items_df"]
    df_edit = st.data_editor(
        df_prev,
        num_rows="dynamic",
        key="ent_items_editor",
        disabled=not cliente_ok,
        use_container_width=True,
        column_config={
            "pieza": st.column_config.TextColumn("Pieza", required=True),
            "cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1, format="%d"),
            "precio_unitario": st.column_config.NumberColumn("Precio unitario $", min_value=0.0, step=50.0, format="%.2f"),
        },
    )
    st.session_state["ent_items_df"] = df_edit

    try:
        df_calc = df_edit.copy()
        df_calc["subtotal"] = (
            df_calc["cantidad"].fillna(0).astype(int)
            * df_calc["precio_unitario"].fillna(0.0).astype(float)
        )
        total = float(df_calc["subtotal"].sum())
    except Exception:
        total = 0.0

    mt1, mt2 = st.columns(2)
    mt1.metric("Ítems", len(df_edit))
    mt2.metric("Total $", f"{total:,.2f}".replace(",", ""))

    st.divider()

    # -------- Confirmar --------
    st.subheader("Confirmar entrega")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        fecha_ent = st.date_input("Fecha", value=date.today())
    with c2:
        notas = st.text_input("Notas (opcional)")
    with c3:
        descuento = st.number_input("Descuento $", min_value=0.0, value=0.0, step=50.0)

    puede_guardar = cliente_ok and len(df_edit) > 0

    if st.button("✅ Guardar entrega", type="primary", disabled=not puede_guardar):
        items = (
            df_edit.fillna({"pieza": "", "cantidad": 0, "precio_unitario": 0.0})
            .to_dict(orient="records")
        )
        items = [
            {
                "pieza": (r.get("pieza") or "").strip(),
                "cantidad": int(r.get("cantidad") or 0),
                "precio_unitario": float(r.get("precio_unitario") or 0.0),
            }
            for r in items
            if (r.get("pieza") or "").strip() and int(r.get("cantidad") or 0) > 0
        ]
        if not items:
            st.warning("No hay piezas válidas para guardar.")
            st.stop()

        ent = crear_entrega(
            cliente_nombre=st.session_state["cliente_seleccionado"],
            fecha=fecha_ent,
            numero="",
            notas=notas,
            items=items,
            descuento=descuento,
        )

        st.session_state["ent_items_df"] = pd.DataFrame(
            [{"pieza": "", "cantidad": 1, "precio_unitario": 0.0}]
        )
        st.success(f"Entrega #{ent.id} guardada ✅ — Total ${ent.total:,.2f}".replace(",", ""))

    st.divider()

    # -------- Últimas entregas --------
    st.subheader("Últimas entregas")
    ult = ultimas_entregas(limit=10)
    if not ult:
        st.info("Todavía no hay entregas registradas.")
        return

    with get_session() as s:
        for ent in ult:
            cli = s.get(Cliente, ent.cliente_id)
            items = s.query(EntregaItem).filter(EntregaItem.entrega_id == ent.id).all()
            resumen = ", ".join(f"{it.pieza} x{it.cantidad}" for it in items[:4])
            if len(items) > 4:
                resumen += f" (+{len(items)-4} más)"

            with st.container(border=True):
                a, b, c = st.columns([2, 3, 1])
                a.write(f"**{ent.fecha.strftime('%Y-%m-%d')}** — ID #{ent.id}")
                b.write(f"**{cli.nombre if cli else 'Cliente'}** · {resumen}")
                c.write(f"${float(ent.total or 0.0):,.2f}".replace(",", "")) 

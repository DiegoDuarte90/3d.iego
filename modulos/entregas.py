# modulos/entregas.py
from __future__ import annotations
import streamlit as st
from datetime import datetime, date
import pandas as pd

from utils.db import SessionLocal, Cliente, Entrega

# ---------------- Helpers de acceso a datos ----------------
def _get_session():
    return SessionLocal()

def _get_cliente_por_nombre(nombre: str) -> Cliente | None:
    if not nombre:
        return None
    with _get_session() as s:
        return (
            s.query(Cliente)
            .filter(Cliente.nombre.ilike(nombre.strip()))
            .one_or_none()
        )

def _upsert_cliente(nombre: str, email: str, telefono: str, direccion: str) -> Cliente:
    with _get_session() as s:
        cli = s.query(Cliente).filter(Cliente.nombre.ilike(nombre.strip())).one_or_none()
        if cli:
            cli.email = email
            cli.telefono = telefono
            cli.direccion = direccion
        else:
            cli = Cliente(
                nombre=nombre.strip(),
                email=email.strip(),
                telefono=telefono.strip(),
                direccion=direccion.strip(),
            )
            s.add(cli)
        s.commit()
        s.refresh(cli)
        return cli

def _crear_entregas(cliente_id: int, fecha: datetime, notas: str, rows: list[dict]):
    """Crea una entrega por cada fila con pieza válida."""
    creadas = 0
    with _get_session() as s:
        for r in rows:
            pieza = (r.get("pieza") or "").strip()
            if not pieza:
                continue
            try:
                cantidad = int(r.get("cantidad") or 0)
            except Exception:
                cantidad = 0
            try:
                precio_unitario = float(r.get("precio_unitario") or 0.0)
            except Exception:
                precio_unitario = 0.0
            if cantidad <= 0:
                continue
            ent = Entrega(
                cliente_id=cliente_id,
                pieza=pieza,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                fecha=fecha,
                notas=(notas or "").strip(),
            )
            s.add(ent)
            creadas += 1
        s.commit()
    return creadas

def _ultimas_entregas_con_cliente(limit: int = 10):
    """Devuelve lista de tuplas (Entrega, Cliente) joineadas."""
    with _get_session() as s:
        return (
            s.query(Entrega, Cliente)
            .join(Cliente, Cliente.id == Entrega.cliente_id)
            .order_by(Entrega.fecha.desc(), Entrega.id.desc())
            .limit(limit)
            .all()
        )

# --------------------- UI principal -----------------------
def mostrar_entregas():
    st.title("📦 Entregas")

    # Estado inicial de la grilla
    if "ent_items" not in st.session_state:
        st.session_state["ent_items"] = pd.DataFrame(
            [{"pieza": "", "cantidad": 1, "precio_unitario": 0.0}]
        )

    # --- Cliente ---
    st.subheader("Cliente")
    colc1, colc2 = st.columns([2, 1])
    with colc1:
        nombre_cli = st.text_input("Nombre del cliente", placeholder="Ej: Juan Pérez")
    with colc2:
        st.write("")  # espacio
        crear_si_no = st.checkbox("Crear si no existe", value=True)

    existente = _get_cliente_por_nombre(nombre_cli)
    colA, colB, colC = st.columns(3)
    email = colA.text_input("Email", value=(existente.email if existente else ""))
    tel = colB.text_input("Teléfono", value=(existente.telefono if existente else ""))
    dire = colC.text_input("Dirección", value=(existente.direccion if existente else ""))

    if st.button("💾 Guardar cliente", disabled=not nombre_cli.strip()):
        cli = _upsert_cliente(nombre_cli, email, tel, dire)
        st.success(f"Cliente guardado/actualizado: {cli.nombre}")

    st.divider()

    # --- Ítems ---
    st.subheader("Ítems")
    st.caption("Completá **pieza**, **cantidad** y **precio unitario**. Podés agregar filas con el +.")
    df = st.data_editor(
        st.session_state["ent_items"],
        num_rows="dynamic",
        key="ent_items_editor",
        column_config={
            "pieza": st.column_config.TextColumn("Pieza", required=True),
            "cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1, format="%d"),
            "precio_unitario": st.column_config.NumberColumn("Precio unitario $", min_value=0.0, step=100.0, format="%.2f"),
        },
    )
    st.session_state["ent_items"] = df

    # Totales
    try:
        df_calc = df.copy()
        df_calc["subtotal"] = (
            df_calc["cantidad"].fillna(0).astype(int)
            * df_calc["precio_unitario"].fillna(0.0).astype(float)
        )
        total = float(df_calc["subtotal"].sum())
    except Exception:
        total = 0.0

    c1, c2 = st.columns(2)
    c1.metric("Ítems", len(df))
    c2.metric("Total $", f"{total:,.2f}".replace(",", ""))

    st.divider()

    # --- Confirmar y guardar ---
    st.subheader("Confirmar entrega")
    cc1, cc2 = st.columns([1, 3])
    with cc1:
        fecha_ent = st.date_input("Fecha", value=date.today())
    with cc2:
        notas = st.text_input("Notas (opcional)", placeholder="Observaciones…")

    puede_guardar = bool(nombre_cli.strip()) and len(df) > 0

    if st.button("✅ Guardar entrega(s)", type="primary", disabled=not puede_guardar):
        cli = _get_cliente_por_nombre(nombre_cli)
        if not cli:
            if crear_si_no:
                cli = _upsert_cliente(nombre_cli, email, tel, dire)
            else:
                st.error("El cliente no existe. Activá 'Crear si no existe' o guardalo primero.")
                st.stop()

        filas = df.fillna({"pieza": "", "cantidad": 0, "precio_unitario": 0.0}).to_dict(orient="records")
        creadas = _crear_entregas(
            cliente_id=cli.id,
            fecha=datetime.combine(fecha_ent, datetime.now().time()),
            notas=notas,
            rows=filas,
        )
        if creadas > 0:
            st.session_state["ent_items"] = pd.DataFrame(
                [{"pieza": "", "cantidad": 1, "precio_unitario": 0.0}]
            )
            st.success(f"Se guardaron {creadas} entrega(s) ✅")
        else:
            st.warning("No había ítems válidos para guardar.")

    st.divider()

    # --- Últimas entregas ---
    st.subheader("Últimas entregas")
    rows = _ultimas_entregas_con_cliente(limit=10)
    if not rows:
        st.info("Todavía no hay entregas registradas.")
        return

    for e, cli in rows:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"**{e.fecha.strftime('%Y-%m-%d')}** — ID #{e.id}")
            c2.write(f"**{cli.nombre if cli else 'Cliente'}** · {e.pieza} x{e.cantidad}")
            subtotal = (e.cantidad or 0) * (e.precio_unitario or 0.0)
            c3.write(f"${subtotal:,.2f}".replace(",", ""))

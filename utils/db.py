# utils/db.py
from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    create_engine, Integer, String, Float, Date, DateTime, ForeignKey, Text,
    func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

# DB en carpeta de usuario (evita permisos en /opt)
DATA_DIR = Path.home() / ".local" / "share" / "3d.iego"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "app.db"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

class Base(DeclarativeBase): ...

# --------- MODELOS ---------
class Cliente(Base):
    __tablename__ = "clientes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(200), index=True, unique=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    direccion: Mapped[Optional[str]] = mapped_column(String(300))
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    entregas: Mapped[List["Entrega"]] = relationship(back_populates="cliente", cascade="all, delete-orphan")


class Entrega(Base):
    __tablename__ = "entregas"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fecha: Mapped[datetime] = mapped_column(Date, default=func.current_date())
    numero: Mapped[Optional[str]] = mapped_column(String(100))
    notas: Mapped[Optional[str]] = mapped_column(Text)

    total: Mapped[float] = mapped_column(Float, default=0.0)
    descuento: Mapped[float] = mapped_column(Float, default=0.0)

    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"))
    cliente: Mapped["Cliente"] = relationship(back_populates="entregas")

    items: Mapped[List["EntregaItem"]] = relationship(back_populates="entrega", cascade="all, delete-orphan")


class EntregaItem(Base):
    __tablename__ = "entrega_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pieza: Mapped[str] = mapped_column(String(200))
    cantidad: Mapped[int] = mapped_column(Integer, default=1)
    precio_unitario: Mapped[float] = mapped_column(Float, default=0.0)
    subtotal: Mapped[float] = mapped_column(Float, default=0.0)

    entrega_id: Mapped[int] = mapped_column(ForeignKey("entregas.id"))
    entrega: Mapped["Entrega"] = relationship(back_populates="items")


class Movimiento(Base):
    __tablename__ = "movimientos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fecha: Mapped[datetime] = mapped_column(Date, default=func.current_date())
    tipo: Mapped[str] = mapped_column(String(20))         # "Ingreso" o "Gasto"
    categoria: Mapped[str] = mapped_column(String(100))   # p.ej. "Ventas", "Insumos", etc.
    monto: Mapped[float] = mapped_column(Float, default=0.0)
    descripcion: Mapped[Optional[str]] = mapped_column(String(300))
    medio: Mapped[Optional[str]] = mapped_column(String(100))  # efectivo/transferencia…

    creado_en: Mapped[datetime] = mapped_column(DateTime, default=func.now())


def init_db() -> None:
    Base.metadata.create_all(engine)

# --------- FUNCIONES CRUD BÁSICAS ---------
def get_session():
    return SessionLocal()

# Clientes
def upsert_cliente(nombre: str, telefono: str = "", email: str = "", direccion: str = "") -> Cliente:
    with get_session() as s:
        cli = s.query(Cliente).filter(Cliente.nombre.ilike(nombre.strip())).one_or_none()
        if cli:
            cli.telefono = telefono
            cli.email = email
            cli.direccion = direccion
        else:
            cli = Cliente(nombre=nombre.strip(), telefono=telefono, email=email, direccion=direccion)
            s.add(cli)
        s.commit()
        s.refresh(cli)
        return cli

def search_clientes(query: str, limit: int = 20) -> list[Cliente]:
    with get_session() as s:
        q = f"%{query.strip()}%"
        return s.query(Cliente).filter(Cliente.nombre.ilike(q)).order_by(Cliente.nombre).limit(limit).all()

def get_cliente_by_nombre(nombre: str) -> Optional[Cliente]:
    with get_session() as s:
        return s.query(Cliente).filter(Cliente.nombre.ilike(nombre.strip())).one_or_none()

# Entregas
def crear_entrega(cliente_nombre: str, fecha, numero: str, notas: str, items: list[dict], descuento: float = 0.0) -> Entrega:
    with get_session() as s:
        cli = s.query(Cliente).filter(Cliente.nombre.ilike(cliente_nombre.strip())).one_or_none()
        if not cli:
            cli = Cliente(nombre=cliente_nombre.strip())
            s.add(cli)
            s.flush()

        ent = Entrega(cliente=cli, fecha=fecha, numero=numero.strip() if numero else None, notas=notas or "", descuento=descuento)
        s.add(ent)
        total = 0.0
        for it in items:
            cant = int(it.get("cantidad", 0) or 0)
            pu = float(it.get("precio_unitario", 0.0) or 0.0)
            sub = cant * pu
            total += sub
            s.add(EntregaItem(entrega=ent, pieza=(it.get("pieza") or "").strip(), cantidad=cant, precio_unitario=pu, subtotal=sub))
        ent.total = max(total - float(descuento or 0.0), 0.0)
        s.commit()
        s.refresh(ent)
        return ent

def ultimas_entregas(limit: int = 10) -> list[Entrega]:
    with get_session() as s:
        return (
            s.query(Entrega)
            .order_by(Entrega.fecha.desc(), Entrega.id.desc())
            .limit(limit)
            .all()
        )

# Movimientos
def crear_movimiento(fecha, tipo: str, categoria: str, monto: float, descripcion: str = "", medio: str = "efectivo") -> Movimiento:
    with get_session() as s:
        mov = Movimiento(fecha=fecha, tipo=tipo, categoria=categoria, monto=float(monto or 0.0), descripcion=descripcion, medio=medio)
        s.add(mov)
        s.commit()
        s.refresh(mov)
        return mov

def listar_movimientos() -> list[Movimiento]:
    with get_session() as s:
        return s.query(Movimiento).order_by(Movimiento.fecha.desc(), Movimiento.id.desc()).all()

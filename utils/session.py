# utils/session.py
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

# Dónde guardar el archivo de sesión:
# - Por defecto usa /tmp (siempre escribible).
# - Podés sobrescribirlo con la variable de entorno SESSION_FILE.
SESSION_FILE = Path(os.getenv("SESSION_FILE", "/tmp/.session_3d_iego"))

# Tiempo de expiración en segundos (2 horas por defecto)
TIEMPO_EXPIRACION = int(os.getenv("SESSION_TTL_SECONDS", str(2 * 60 * 60)))


def _now() -> int:
    return int(time.time())


def _ensure_parent_dir(path: Path) -> None:
    """Crea el directorio padre si no existe (modo seguro)."""
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


def guardar_sesion(username: str) -> None:
    """
    Guarda la sesión de forma atómica: escribe en un archivo temporal y renombra.
    También fija permisos 600 para que sólo el usuario actual lo lea/escriba.
    """
    _ensure_parent_dir(SESSION_FILE)
    tmp = SESSION_FILE.with_suffix(SESSION_FILE.suffix + ".tmp")
    payload = f"{username}|{_now()}"
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, SESSION_FILE)  # operación atómica en el mismo FS
    try:
        os.chmod(SESSION_FILE, 0o600)
    except Exception:
        # En algunos FS puede no aplicar, lo ignoramos.
        pass


def _leer_sesion() -> Optional[tuple[str, int]]:
    """Devuelve (username, timestamp) o None si hay problema."""
    try:
        data = SESSION_FILE.read_text(encoding="utf-8").strip()
        if not data or "|" not in data:
            return None
        username, ts_str = data.split("|", 1)
        return username, int(ts_str)
    except Exception:
        return None


def sesion_valida() -> bool:
    """
    Verifica si existe el archivo y no está expirada.
    Si queda menos de 25% del TTL, renueva el timestamp (sliding expiration).
    """
    if not SESSION_FILE.exists():
        return False

    parsed = _leer_sesion()
    if not parsed:
        return False

    username, timestamp = parsed
    ahora = _now()
    if ahora - timestamp >= TIEMPO_EXPIRACION:
        # Expirada: eliminar para limpiar estado
        eliminar_sesion()
        return False

    # Sliding expiration: si pasó más del 75% del TTL, renovamos timestamp
    if ahora - timestamp > (TIEMPO_EXPIRACION * 3 // 4):
        guardar_sesion(username)

    return True


def eliminar_sesion() -> None:
    """Elimina el archivo de sesión si existe."""
    try:
        SESSION_FILE.unlink(missing_ok=True)
    except Exception:
        pass

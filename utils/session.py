import os
import time

SESSION_FILE = ".session_login"
TIEMPO_EXPIRACION = 2 * 60 * 60  # 2 horas en segundos

def guardar_sesion(username):
    with open(SESSION_FILE, "w") as f:
        f.write(f"{username}|{int(time.time())}")

def sesion_valida():
    if not os.path.exists(SESSION_FILE):
        return False
    with open(SESSION_FILE, "r") as f:
        data = f.read().strip()
    try:
        username, timestamp = data.split("|")
        timestamp = int(timestamp)
        ahora = int(time.time())
        if ahora - timestamp < TIEMPO_EXPIRACION:
            return True
    except:
        pass
    return False

def eliminar_sesion():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
        
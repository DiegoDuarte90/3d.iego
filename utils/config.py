import json
import os

CONFIG_PATH = "config.json"

def cargar_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "precio_kg": 15900.0,
            "precio_kwh": 83.94,
            "consumo_watts": 150.0,
            "vida_util_horas": 4320.0,
            "precio_repuestos": 75000.0,
            "margen_error_pct": 20.0
        }
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def guardar_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

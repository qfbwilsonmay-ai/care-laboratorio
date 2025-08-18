# utils.py
import json
import os
from datetime import datetime

# --- Lectura y escritura de archivos JSON ---
def cargar_datos(ruta):
    if os.path.exists(ruta):
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def guardar_datos(ruta, datos):
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# --- Generador de folio ---
def generar_folio():
    hoy = datetime.now()
    fecha_str = hoy.strftime("%y%m%d")
    pacientes = cargar_datos('datos/pacientes.json')
    hoy_pacientes = [p for p in pacientes if p['folio'].startswith(fecha_str)]
    consecutivo = len(hoy_pacientes) + 1
    consecutivo_str = str(consecutivo).zfill(3)
    return fecha_str + consecutivo_str

# --- Calcular edad ---
def calcular_edad(fecha_nac_str):
    fecha_nac = datetime.strptime(fecha_nac_str, "%Y-%m-%d")
    hoy = datetime.now()
    edad = hoy.year - fecha_nac.year
    if hoy.month < fecha_nac.month or (hoy.month == fecha_nac.month and hoy.day < fecha_nac.day):
        edad -= 1
    return edad
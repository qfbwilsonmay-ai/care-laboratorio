# app.py - Aplicación web CARE en Flask
from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)

# Rutas
RUTA_PACIENTES = 'datos/pacientes.json'
RUTA_RESULTADOS = 'datos/resultados.json'

# Aseguramos que la carpeta 'datos' exista
os.makedirs('datos', exist_ok=True)

def cargar_datos(ruta):
    if os.path.exists(ruta):
        with open(ruta, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def guardar_datos(ruta, datos):
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

@app.route('/')
def index():
    pacientes = cargar_datos(RUTA_PACIENTES)
    return render_template('index.html', pacientes=pacientes)

@app.route('/admin/pruebas', methods=['GET', 'POST'])
def admin_pruebas():
    if request.method == 'POST':
        nuevas_pruebas = []
        for key in request.form:
            if key.startswith('clave_'):
                idx = key.split('_')[1]
                try:
                    prueba = {
                        "clave": request.form[f'clave_{idx}'].strip(),
                        "nombre": request.form[f'nombre_{idx}'].strip(),
                        "tipo_muestra": request.form[f'tipo_muestra_{idx}'].strip(),
                        "id_contenedor": int(request.form[f'id_contenedor_{idx}']),
                        "unidad": request.form[f'unidad_{idx}'].strip(),
                        "valores_normales": request.form[f'valores_normales_{idx}'].strip(),
                        "tipo": "cuantitativa"
                    }
                    nuevas_pruebas.append(prueba)
                except Exception as e:
                    continue

        guardar_datos('datos/pruebas.json', nuevas_pruebas)
        return redirect(url_for('admin_pruebas'))

    pruebas = cargar_datos('datos/pruebas.json')
    contenedores = cargar_datos('datos/contenedores.json')
    return render_template('admin_pruebas.html', pruebas=pruebas, contenedores=contenedores)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
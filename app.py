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

def generar_folio():
    return datetime.now().strftime("%y%m%d%I")

def calcular_edad(fecha_nac):
    from datetime import datetime
    nac = datetime.strptime(fecha_nac, "%Y-%m-%d")
    hoy = datetime.now()
    edad = hoy.year - nac.year
    if hoy.month < nac.month or (hoy.month == nac.month and hoy.day < nac.day):
        edad -= 1
    return edad

@app.route('/')
def index():
    pacientes = cargar_datos(RUTA_PACIENTES)
    return render_template('index.html', pacientes=pacientes)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        fecha_nac = request.form['fecha_nac']
        sexo = request.form['sexo']
        diagnostico = request.form['diagnostico']
        medico = request.form['medico']

        folio = generar_folio()
        edad = calcular_edad(fecha_nac) if fecha_nac else int(request.form.get('edad_manual', 0))

        paciente = {
            "folio": folio,
            "nombre": nombre,
            "fecha_nacimiento": fecha_nac,
            "edad": edad,
            "sexo": sexo,
            "diagnostico": diagnostico,
            "medico": medico,
            "estudios": [],
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        pacientes = cargar_datos(RUTA_PACIENTES)
        pacientes.append(paciente)
        guardar_datos(RUTA_PACIENTES, pacientes)

        return redirect(url_for('index'))

    return render_template('registro.html')

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
                except:
                    continue

        with open('datos/pruebas.json', 'w', encoding='utf-8') as f:
            json.dump(nuevas_pruebas, f, indent=4, ensure_ascii=False)

        return redirect(url_for('admin_pruebas'))

    pruebas = cargar_datos('datos/pruebas.json')
    contenedores = cargar_datos('datos/contenedores.json')
    return render_template('admin_pruebas.html', pruebas=pruebas, contenedores=contenedores)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
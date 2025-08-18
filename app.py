# app.py - Aplicación web CARE en Flask
from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime
from utils import generar_folio, calcular_edad, cargar_datos, guardar_datos

app = Flask(__name__)

# Rutas
RUTA_PACIENTES = 'datos/pacientes.json'
RUTA_RESULTADOS = 'datos/resultados.json'

# Aseguramos que la carpeta 'datos' exista
os.makedirs('datos', exist_ok=True)

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
        edad = calcular_edad(fecha_nac)

        paciente = {
            "folio": folio,
            "nombre": nombre,
            "fecha_nacimiento": fecha_nac,
            "edad": edad,
            "sexo": sexo,
            "diagnostico": diagnostico,
            "medico": medico,
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        pacientes = cargar_datos(RUTA_PACIENTES)
        pacientes.append(paciente)
        guardar_datos(RUTA_PACIENTES, pacientes)

        return redirect(url_for('index'))

    return render_template('registro.html')

@app.route('/resultados/<folio>', methods=['GET', 'POST'])
def resultados(folio):
    pacientes = cargar_datos(RUTA_PACIENTES)
    paciente = next((p for p in pacientes if p['folio'] == folio), None)

    if not paciente:
        return "Paciente no encontrado", 404

    pruebas = [
        {"clave": "GLU", "nombre": "Glucosa", "unidad": "mg/dL", "valores_normales": "70-110"},
        {"clave": "CRE", "nombre": "Creatinina", "unidad": "mg/dL", "valores_normales": "0.7-1.3"},
        {"clave": "URO", "nombre": "Uroanálisis", "unidad": "", "valores_normales": "Negativo"}
    ]

    if request.method == 'POST':
        clave = request.form['prueba']
        prueba = next((p for p in pruebas if p['clave'] == clave), None)
        resultado = request.form['resultado']

        resultado_data = {
            "folio": folio,
            "clave": prueba['clave'],
            "nombre": prueba['nombre'],
            "resultado": resultado,
            "unidad": prueba['unidad'],
            "valores_normales": prueba['valores_normales'],
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        resultados = cargar_datos(RUTA_RESULTADOS)
        resultados.append(resultado_data)
        guardar_datos(RUTA_RESULTADOS, resultados)

        return redirect(url_for('resultados', folio=folio))

    resultados = [r for r in cargar_datos(RUTA_RESULTADOS) if r['folio'] == folio]
    return render_template('resultados.html', paciente=paciente, pruebas=pruebas, resultados=resultados)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Usa el puerto de Render
    app.run(host="0.0.0.0", port=port, debug=False)  # ¡Importante: 0.0.0.0 y debug=False!
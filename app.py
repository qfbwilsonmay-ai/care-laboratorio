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

# Cargar catálogos
PRUEBAS = cargar_datos('datos/pruebas.json')
CONTENEDORES = cargar_datos('datos/contenedores.json')
PRECIOS = cargar_datos('datos/precios.json')

# Crear diccionario de precios: tipo_elemento_id -> precio
precios_dict = {}
for p in PRECIOS:
    key = f"{p['tipo']}_{p['id_elemento']}"
    precios_dict[key] = p['precio']

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

        # Obtener estudios seleccionados
        pruebas_seleccionadas = request.form.getlist('pruebas')

        folio = generar_folio()
        edad = calcular_edad(fecha_nac)

        # Lista para guardar los estudios con su info
        estudios = []
        for clave in pruebas_seleccionadas:
            prueba = next((p for p in PRUEBAS if p['clave'] == clave), None)
            if prueba:
                precio = precios_dict.get(f"prueba_{clave}", 0)
                estudios.append({
                    "clave": clave,
                    "nombre": prueba['nombre'],
                    "precio": precio
                })

        paciente = {
            "folio": folio,
            "nombre": nombre,
            "fecha_nacimiento": fecha_nac,
            "edad": edad,
            "sexo": sexo,
            "diagnostico": diagnostico,
            "medico": medico,
            "estudios": estudios,
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        pacientes = cargar_datos(RUTA_PACIENTES)
        pacientes.append(paciente)
        guardar_datos(RUTA_PACIENTES, pacientes)

        return redirect(url_for('index'))

    # Pasar datos a la plantilla
    return render_template(
        'registro.html',
        pruebas=PRUEBAS,
        contenedores=CONTENEDORES,
        precios=precios_dict
    )

@app.route('/resultados/<folio>', methods=['GET', 'POST'])
def resultados(folio):
    pacientes = cargar_datos(RUTA_PACIENTES)
    paciente = next((p for p in pacientes if p['folio'] == folio), None)

    if not paciente:
        return "Paciente no encontrado", 404

    # Obtener solo las pruebas que se le asignaron
    claves_solicitadas = [e['clave'] for e in paciente.get('estudios', [])]
    pruebas_solicitadas = [p for p in PRUEBAS if p['clave'] in claves_solicitadas]

    if request.method == 'POST':
        clave = request.form['prueba']
        resultado = request.form['resultado']

        # Buscar la prueba
        prueba = next((p for p in PRUEBAS if p['clave'] == clave), None)
        if not prueba:
            return "Prueba no encontrada", 400

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
    return render_template(
        'resultados.html',
        paciente=paciente,
        pruebas=pruebas_solicitadas,
        resultados=resultados
    )

@app.route('/editar_resultado/<folio>/<clave>', methods=['GET', 'POST'])
def editar_resultado(folio, clave):
    resultados = cargar_datos(RUTA_RESULTADOS)
    resultado = next((r for r in resultados if r['folio'] == folio and r['clave'] == clave), None)

    if not resultado:
        return "Resultado no encontrado", 404

    if request.method == 'POST':
        nuevo_resultado = request.form['resultado']
        resultado['resultado'] = nuevo_resultado
        resultado['fecha'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        guardar_datos(RUTA_RESULTADOS, resultados)
        return redirect(url_for('resultados', folio=folio))

    return f'''
    <h3>Editar resultado: {resultado['nombre']}</h3>
    <form method="POST">
        <input type="text" name="resultado" value="{resultado['resultado']}" required>
        <button type="submit">Guardar</button>
        <a href="/resultados/{folio}">Cancelar</a>
    </form>
    '''

@app.route('/eliminar_paciente/<folio>')
def eliminar_paciente(folio):
    pacientes = cargar_datos(RUTA_PACIENTES)
    resultados = cargar_datos(RUTA_RESULTADOS)

    # Filtrar paciente
    pacientes = [p for p in pacientes if p['folio'] != folio]
    guardar_datos(RUTA_PACIENTES, pacientes)

    # También eliminar sus resultados
    resultados = [r for r in resultados if r['folio'] != folio]
    guardar_datos(RUTA_RESULTADOS, resultados)

    return redirect(url_for('index'))

@app.route('/admin/pruebas', methods=['GET', 'POST'])
def admin_pruebas():
    if request.method == 'POST':
        # Recibir datos del formulario
        nuevas_pruebas = []
        for key in request.form:
            if key.startswith('clave_'):
                idx = key.split('_')[1]
                prueba = {
                    "clave": request.form[f'clave_{idx}'],
                    "nombre": request.form[f'nombre_{idx}'],
                    "tipo_muestra": request.form[f'tipo_muestra_{idx}'],
                    "id_contenedor": int(request.form[f'id_contenedor_{idx}'])
                }
                # Si es multiparamétrica, manejar parámetros
                if 'multiparametrica' in request.form.getlist(f'tipo_{idx}'):
                    prueba["tipo"] = "multiparametrica"
                    prueba["parametros"] = []
                    param_keys = [k for k in request.form if k.startswith(f'param_clave_{idx}_')]
                    for pkey in param_keys:
                        pidx = pkey.split('_')[-1]
                        prueba["parametros"].append({
                            "clave": request.form[f'param_clave_{idx}_{pidx}'],
                            "nombre": request.form[f'param_nombre_{idx}_{pidx}'],
                            "unidad": request.form[f'param_unidad_{idx}_{pidx}'],
                            "valores_normales": request.form[f'param_rango_{idx}_{pidx}']
                        })
                else:
                    prueba["tipo"] = "cuantitativa"
                    prueba["unidad"] = request.form[f'unidad_{idx}']
                    prueba["valores_normales"] = request.form[f'valores_normales_{idx}']
                nuevas_pruebas.append(prueba)

        # Guardar en pruebas.json
        with open('datos/pruebas.json', 'w', encoding='utf-8') as f:
            json.dump(nuevas_pruebas, f, indent=4, ensure_ascii=False)

        return redirect(url_for('admin_pruebas'))

    # Si es GET, mostrar el formulario con los datos actuales
    pruebas = cargar_datos('datos/pruebas.json')
    contenedores = cargar_datos('datos/contenedores.json')
    return render_template('admin_pruebas.html', pruebas=pruebas, contenedores=contenedores)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
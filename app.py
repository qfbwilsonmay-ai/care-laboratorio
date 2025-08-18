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

def cargar_catalogos():
    """Carga los catálogos desde los archivos JSON cada vez que se llama"""
    pruebas = cargar_datos('datos/pruebas.json')
    contenedores = cargar_datos('datos/contenedores.json')
    precios = cargar_datos('datos/precios.json')
    
    # Crear diccionario de precios
    precios_dict = {}
    for p in precios:
        key = f"{p['tipo']}_{p['id_elemento']}"
        precios_dict[key] = p['precio']
    
    return pruebas, contenedores, precios_dict

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

        # Cargar pruebas para obtener info
        pruebas, contenedores, precios_dict = cargar_catalogos()

        # Lista para guardar los estudios con su info
        estudios = []
        for clave in pruebas_seleccionadas:
            prueba = next((p for p in pruebas if p['clave'] == clave), None)
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

    # Cargar datos para la plantilla
    pruebas, contenedores, precios_dict = cargar_catalogos()
    return render_template(
        'registro.html',
        pruebas=pruebas,
        contenedores=contenedores,
        precios=precios_dict
    )

@app.route('/editar_paciente/<folio>', methods=['GET', 'POST'])
def editar_paciente(folio):
    pacientes = cargar_datos(RUTA_PACIENTES)
    paciente = next((p for p in pacientes if p['folio'] == folio), None)

    if not paciente:
        return "Paciente no encontrado", 404

    if request.method == 'POST':
        # Actualizar datos básicos
        paciente['nombre'] = request.form['nombre']
        paciente['fecha_nacimiento'] = request.form['fecha_nac']
        paciente['sexo'] = request.form['sexo']
        paciente['diagnostico'] = request.form['diagnostico']
        paciente['medico'] = request.form['medico']

        # Obtener nuevos estudios seleccionados
        nuevos_estudios_claves = request.form.getlist('nuevos_estudios')

        # Cargar catálogos
        pruebas, contenedores, precios_dict = cargar_catalogos()

        # Crear lista de nuevos estudios (sin duplicados)
        nuevos_estudios = []
        claves_existentes = [e['clave'] for e in paciente.get('estudios', [])]
        for clave in nuevos_estudios_claves:
            if clave not in claves_existentes:
                prueba = next((p for p in pruebas if p['clave'] == clave), None)
                if prueba:
                    precio = precios_dict.get(f"prueba_{clave}", 0)
                    nuevos_estudios.append({
                        "clave": clave,
                        "nombre": prueba['nombre'],
                        "precio": precio
                    })

        # Añadir nuevos estudios
        if 'estudios' not in paciente:
            paciente['estudios'] = []
        paciente['estudios'].extend(nuevos_estudios)

        # Eliminar estudios marcados para borrar
        estudios_a_mantener = []
        for estudio in paciente['estudios']:
            if f"eliminar_{estudio['clave']}" not in request.form:
                estudios_a_mantener.append(estudio)
        paciente['estudios'] = estudios_a_mantener

        # Guardar cambios
        guardar_datos(RUTA_PACIENTES, pacientes)

        return redirect(url_for('index'))

    # Cargar datos para la plantilla
    pruebas, contenedores, precios_dict = cargar_catalogos()

    # Estudios ya asignados
    claves_asignadas = [e['clave'] for e in paciente.get('estudios', [])]
    estudios_asignados = paciente.get('estudios', [])

    # Pruebas disponibles (que no tenga el paciente)
    pruebas_disponibles = [p for p in pruebas if p['clave'] not in claves_asignadas]

    return render_template(
        'editar_paciente.html',
        paciente=paciente,
        pruebas=pruebas_disponibles,
        contenedores=contenedores,
        precios=precios_dict,
        estudios_asignados=estudios_asignados
    )

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

def cargar_catalogos():
    """Carga los catálogos desde los archivos JSON cada vez que se llama"""
    pruebas = cargar_datos('datos/pruebas.json')
    contenedores = cargar_datos('datos/contenedores.json')
    precios = cargar_datos('datos/precios.json')
    
    # Crear diccionario de precios
    precios_dict = {}
    for p in precios:
        key = f"{p['tipo']}_{p['id_elemento']}"
        precios_dict[key] = p['precio']
    
    return pruebas, contenedores, precios_dict

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

        # Cargar pruebas para obtener info
        pruebas, contenedores, precios_dict = cargar_catalogos()

        # Lista para guardar los estudios con su info
        estudios = []
        for clave in pruebas_seleccionadas:
            prueba = next((p for p in pruebas if p['clave'] == clave), None)
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

    # Cargar datos para la plantilla
    pruebas, contenedores, precios_dict = cargar_catalogos()
    return render_template(
        'registro.html',
        pruebas=pruebas,
        contenedores=contenedores,
        precios=precios_dict
    )

@app.route('/editar_paciente/<folio>', methods=['GET', 'POST'])
def editar_paciente(folio):
    pacientes = cargar_datos(RUTA_PACIENTES)
    paciente = next((p for p in pacientes if p['folio'] == folio), None)

    if not paciente:
        return "Paciente no encontrado", 404

    if request.method == 'POST':
        # Actualizar datos básicos
        paciente['nombre'] = request.form['nombre']
        paciente['fecha_nacimiento'] = request.form['fecha_nac']
        paciente['sexo'] = request.form['sexo']
        paciente['diagnostico'] = request.form['diagnostico']
        paciente['medico'] = request.form['medico']

        # Obtener nuevos estudios seleccionados
        nuevos_estudios_claves = request.form.getlist('nuevos_estudios')

        # Cargar catálogos
        pruebas, contenedores, precios_dict = cargar_catalogos()

        # Crear lista de nuevos estudios (sin duplicados)
        nuevos_estudios = []
        claves_existentes = [e['clave'] for e in paciente.get('estudios', [])]
        for clave in nuevos_estudios_claves:
            if clave not in claves_existentes:
                prueba = next((p for p in pruebas if p['clave'] == clave), None)
                if prueba:
                    precio = precios_dict.get(f"prueba_{clave}", 0)
                    nuevos_estudios.append({
                        "clave": clave,
                        "nombre": prueba['nombre'],
                        "precio": precio
                    })

        # Añadir nuevos estudios
        if 'estudios' not in paciente:
            paciente['estudios'] = []
        paciente['estudios'].extend(nuevos_estudios)

        # Eliminar estudios marcados para borrar
        estudios_a_mantener = []
        for estudio in paciente['estudios']:
            if f"eliminar_{estudio['clave']}" not in request.form:
                estudios_a_mantener.append(estudio)
        paciente['estudios'] = estudios_a_mantener

        # Guardar cambios
        guardar_datos(RUTA_PACIENTES, pacientes)

        return redirect(url_for('index'))

    # Cargar datos para la plantilla
    pruebas, contenedores, precios_dict = cargar_catalogos()

    # Estudios ya asignados
    claves_asignadas = [e['clave'] for e in paciente.get('estudios', [])]
    estudios_asignados = paciente.get('estudios', [])

    # Pruebas disponibles (que no tenga el paciente)
    pruebas_disponibles = [p for p in pruebas if p['clave'] not in claves_asignadas]

    return render_template(
        'editar_paciente.html',
        paciente=paciente,
        pruebas=pruebas_disponibles,
        contenedores=contenedores,
        precios=precios_dict,
        estudios_asignados=estudios_asignados
    )

@app.route('/resultados/<folio>', methods=['GET', 'POST'])
def resultados(folio):
    pruebas, contenedores, precios_dict = cargar_catalogos()
    pacientes = cargar_datos(RUTA_PACIENTES)
    paciente = next((p for p in pacientes if p['folio'] == folio), None)

    if not paciente:
        return "Paciente no encontrado", 404

    # Obtener solo las pruebas que se le asignaron
    claves_solicitadas = [e['clave'] for e in paciente.get('estudios', [])]
    pruebas_solicitadas = [p for p in pruebas if p['clave'] in claves_solicitadas]

    if request.method == 'POST':
        clave = request.form['prueba']
        resultado = request.form['resultado']

        # Buscar la prueba
        prueba = next((p for p in pruebas if p['clave'] == clave), None)
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
    <h3>Editar resultado: {resultado["nombre"]}</h3>
    <form method="POST">
        <input type="text" name="resultado" value="{resultado["resultado"]}" required>
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

        with open('datos/pruebas.json', 'w', encoding='utf-8') as f:
            json.dump(nuevas_pruebas, f, indent=4, ensure_ascii=False)

        return redirect(url_for('admin_pruebas'))

    pruebas, contenedores, _ = cargar_catalogos()
    return render_template('admin_pruebas.html', pruebas=pruebas, contenedores=contenedores)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
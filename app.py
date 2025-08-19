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
    
    # Crear diccionario de precios por clave
    precios_dict = {}
    for p in precios:
        key = f"{p['tipo']}_{p['id_elemento']}"
        precios_dict[key] = p
    
    return pruebas, contenedores, precios, precios_dict

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

        pruebas_seleccionadas = request.form.getlist('pruebas')
        laboratorios = {}
        for clave in pruebas_seleccionadas:
            lab = request.form.get(f'laboratorio_{clave}', 'matriz')
            laboratorios[clave] = lab

        folio = generar_folio()
        edad = calcular_edad(fecha_nac) if fecha_nac else request.form.get('edad_manual', 0)

        pruebas, contenedores, _, precios_dict = cargar_catalogos()

        estudios = []
        for clave in pruebas_seleccionadas:
            prueba = next((p for p in pruebas if p['clave'] == clave), None)
            if prueba:
                precio_data = precios_dict.get(f"prueba_{clave}")
                if not precio_data:
                    precio_final = 0
                else:
                    if laboratorios[clave] == 'sigma':
                        precio_final = precio_data.get('precio_publico_sigma', 0)
                    else:
                        precio_final = precio_data.get('precio_publico_matriz', 0)

                estudios.append({
                    "clave": clave,
                    "nombre": prueba['nombre'],
                    "precio": precio_final,
                    "procesado_en": laboratorios[clave]
                })

        paciente = {
            "folio": folio,
            "nombre": nombre,
            "fecha_nacimiento": fecha_nac,
            "edad": int(edad) if edad else 0,
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

    pruebas, contenedores, _, precios_dict = cargar_catalogos()
    return render_template(
        'registro.html',
        pruebas=pruebas,
        contenedores=contenedores,
        precios_dict=precios_dict
    )

@app.route('/resumen/<folio>')
def resumen(folio):
    pacientes = cargar_datos(RUTA_PACIENTES)
    paciente = next((p for p in pacientes if p['folio'] == folio), None)

    if not paciente:
        return "Paciente no encontrado", 404

    # Cargar precios
    _, _, _, precios_dict = cargar_catalogos()

    subtotal = 0
    maquila_matriz = 0
    maquila_sigma = 0
    materiales = 0
    envio = 0

    for estudio in paciente.get('estudios', []):
        clave = estudio['clave']
        procesado_en = estudio.get('procesado_en', 'matriz')
        
        # Precio público
        precio_data = precios_dict.get(f"prueba_{clave}")
        if precio_data:
            if procesado_en == 'sigma':
                precio_publico = precio_data.get('precio_publico_sigma', 0)
            else:
                precio_publico = precio_data.get('precio_publico_matriz', 0)
            subtotal += precio_publico

        # Costos detallados
        costo_matriz = precio_data.get('costos', {}).get('matriz', {}) if precio_data else {}
        costo_sigma = precio_data.get('costos', {}).get('sigma', {}) if precio_data else {}

        # Solo el costo de "maquila" (sin materiales ni envío)
        maquila_matriz += costo_matriz.get('maquila', 0)
        maquila_sigma += costo_sigma.get('maquila', 0)

        # Materiales: suma de ambos
        materiales += costo_matriz.get('materiales', 0) + costo_sigma.get('materiales', 0)

        # Envío: suma de ambos
        envio += costo_matriz.get('envio', 0) + costo_sigma.get('envio', 0)

    total_maquila = maquila_matriz + maquila_sigma
    ganancia = subtotal - (total_maquila + materiales + envio)
    iva = round(subtotal * 0.16, 2)
    total = subtotal + iva

    return render_template(
        'resumen.html',
        paciente=paciente,
        subtotal=round(subtotal, 2),
        iva=round(iva, 2),
        total=round(total, 2),
        maquila_matriz=round(maquila_matriz, 2),
        maquila_sigma=round(maquila_sigma, 2),
        total_maquila=round(total_maquila, 2),
        materiales=round(materiales, 2),
        envio=round(envio, 2),
        ganancia=round(ganancia, 2)
    )

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

        with open('datos/pruebas.json', 'w', encoding='utf-8') as f:
            json.dump(nuevas_pruebas, f, indent=4, ensure_ascii=False)

        return redirect(url_for('admin_pruebas'))

    pruebas, contenedores, _, _ = cargar_catalogos()
    return render_template('admin_pruebas.html', pruebas=pruebas, contenedores=contenedores)

@app.route('/admin/precios', methods=['GET', 'POST'])
def admin_precios():
    if request.method == 'POST':
        nuevos_precios = []
        for key in request.form:
            if key.startswith('tipo_'):
                idx = key.split('_')[1]
                tipo = request.form[f'tipo_{idx}']
                id_elemento = request.form[f'id_{idx}']
                
                try:
                    maquila_matriz = float(request.form.get(f'maquila_matriz_{idx}', 0))
                    materiales_matriz = float(request.form.get(f'materiales_matriz_{idx}', 0))
                    envio_matriz = float(request.form.get(f'envio_matriz_{idx}', 0))
                    maquila_sigma = float(request.form.get(f'maquila_sigma_{idx}', 0))
                    materiales_sigma = float(request.form.get(f'materiales_sigma_{idx}', 0))
                    envio_sigma = float(request.form.get(f'envio_sigma_{idx}', 0))
                    ganancia = float(request.form[f'ganancia_{idx}'])
                    precio_publico_matriz = float(request.form[f'precio_publico_matriz_{idx}'])
                    precio_publico_sigma = float(request.form[f'precio_publico_sigma_{idx}'])
                    validado = request.form.get(f'validado_{idx}') == '1'
                except:
                    continue

                costo_matriz = maquila_matriz + materiales_matriz + envio_matriz
                costo_sigma = maquila_sigma + materiales_sigma + envio_sigma
                precio_sugerido_matriz = round(costo_matriz * (1 + ganancia / 100), 2)
                precio_sugerido_sigma = round(costo_sigma * (1 + ganancia / 100), 2)

                nuevos_precios.append({
                    "tipo": tipo,
                    "id_elemento": id_elemento,
                    "costos": {
                        "matriz": {
                            "maquila": maquila_matriz,
                            "materiales": materiales_matriz,
                            "envio": envio_matriz
                        },
                        "sigma": {
                            "maquila": maquila_sigma,
                            "materiales": materiales_sigma,
                            "envio": envio_sigma
                        }
                    },
                    "ganancia_porcentaje": ganancia,
                    "precio_sugerido_matriz": precio_sugerido_matriz,
                    "precio_sugerido_sigma": precio_sugerido_sigma,
                    "precio_publico_matriz": precio_publico_matriz,
                    "precio_publico_sigma": precio_publico_sigma,
                    "validado": validado
                })

        with open('datos/precios.json', 'w', encoding='utf-8') as f:
            json.dump(nuevos_precios, f, indent=4, ensure_ascii=False)
        return redirect(url_for('admin_precios'))

    pruebas = cargar_datos('datos/pruebas.json')
    precios = cargar_datos('datos/precios.json')
    precios_dict = {f"{p['tipo']}_{p['id_elemento']}": p for p in precios}
    return render_template('admin_precios.html', pruebas=pruebas, precios_dict=precios_dict)

@app.route('/resultados/<folio>', methods=['GET', 'POST'])
def resultados(folio):
    pruebas, contenedores, _, precios_dict = cargar_catalogos()
    pacientes = cargar_datos(RUTA_PACIENTES)
    paciente = next((p for p in pacientes if p['folio'] == folio), None)

    if not paciente:
        return "Paciente no encontrado", 404

    claves_solicitadas = [e['clave'] for e in paciente.get('estudios', [])]
    pruebas_solicitadas = [p for p in pruebas if p['clave'] in claves_solicitadas]

    if request.method == 'POST':
        clave = request.form['prueba']
        resultado = request.form['resultado']
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

@app.route('/editar_paciente/<folio>', methods=['GET', 'POST'])
def editar_paciente(folio):
    pacientes = cargar_datos(RUTA_PACIENTES)
    paciente = next((p for p in pacientes if p['folio'] == folio), None)

    if not paciente:
        return "Paciente no encontrado", 404

    if request.method == 'POST':
        paciente['nombre'] = request.form['nombre']
        paciente['fecha_nacimiento'] = request.form['fecha_nac']
        paciente['sexo'] = request.form['sexo']
        paciente['diagnostico'] = request.form['diagnostico']
        paciente['medico'] = request.form['medico']

        if paciente['fecha_nacimiento']:
            paciente['edad'] = calcular_edad(paciente['fecha_nacimiento'])
        elif request.form.get('edad_manual'):
            paciente['edad'] = int(request.form['edad_manual'])

        nuevos_estudios_claves = request.form.getlist('nuevos_estudios')
        laboratorios = {}
        for clave in nuevos_estudios_claves:
            lab = request.form.get(f'laboratorio_nuevo_{clave}', 'matriz')
            laboratorios[clave] = lab

        pruebas, contenedores, _, precios_dict = cargar_catalogos()

        nuevos_estudios = []
        claves_existentes = [e['clave'] for e in paciente.get('estudios', [])]
        for clave in nuevos_estudios_claves:
            if clave not in claves_existentes:
                prueba = next((p for p in pruebas if p['clave'] == clave), None)
                if prueba:
                    precio_data = precios_dict.get(f"prueba_{clave}")
                    if not precio_data:
                        precio_final = 0
                    else:
                        if laboratorios[clave] == 'sigma':
                            precio_final = precio_data.get('precio_publico_sigma', 0)
                        else:
                            precio_final = precio_data.get('precio_publico_matriz', 0)

                    nuevos_estudios.append({
                        "clave": clave,
                        "nombre": prueba['nombre'],
                        "precio": precio_final,
                        "procesado_en": laboratorios[clave]
                    })

        if 'estudios' not in paciente:
            paciente['estudios'] = []
        paciente['estudios'].extend(nuevos_estudios)

        estudios_a_mantener = []
        for estudio in paciente['estudios']:
            if f"eliminar_{estudio['clave']}" not in request.form:
                estudios_a_mantener.append(estudio)
        paciente['estudios'] = estudios_a_mantener

        guardar_datos(RUTA_PACIENTES, pacientes)
        return redirect(url_for('index'))

    pruebas, contenedores, _, precios_dict = cargar_catalogos()

    claves_asignadas = [e['clave'] for e in paciente.get('estudios', [])]
    estudios_asignados = paciente.get('estudios', [])
    pruebas_disponibles = [p for p in pruebas if p['clave'] not in claves_asignadas]

    return render_template(
        'editar_paciente.html',
        paciente=paciente,
        pruebas=pruebas_disponibles,
        contenedores=contenedores,
        precios_dict=precios_dict,
        estudios_asignados=estudios_asignados
    )

@app.route('/eliminar_paciente/<folio>')
def eliminar_paciente(folio):
    pacientes = cargar_datos(RUTA_PACIENTES)
    resultados = cargar_datos(RUTA_RESULTADOS)
    pacientes = [p for p in pacientes if p['folio'] != folio]
    guardar_datos(RUTA_PACIENTES, pacientes)
    resultados = [r for r in resultados if r['folio'] != folio]
    guardar_datos(RUTA_RESULTADOS, resultados)
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
# app.py - Aplicación web CARE en Flask
from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from datetime import datetime
from utils import generar_folio, calcular_edad, cargar_datos, guardar_datos

app = Flask(__name__)
app.secret_key = 'care_laboratorio_2025'  # Necesario para usar sesiones
# 🔐 USUARIOS Y ROLES
USUARIOS = {
    'Wilson': {
        'clave': '4167',
        'rol': 'quimico_admin'
    },
    'Abelardo': {
        'clave': 'Abelardo25',
        'rol': 'quimico'
    },
    'Recepcion': {
        'clave': 'R123',
        'rol': 'recepcionista'
    }
}

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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']
        if usuario in USUARIOS and USUARIOS[usuario]['clave'] == clave:
            session['usuario'] = usuario
            session['rol'] = USUARIOS[usuario]['rol']
            return redirect(url_for('index_get'))
        else:
            return '''
                <h3 style="color:red">Usuario o contraseña incorrectos</h3>
                <a href="/">Intentar de nuevo</a>
            '''

    if 'usuario' not in session:
        return '''
            <h1>Inicio de Sesión - CARE</h1>
            <form method="post">
                <label>Usuario: <input type="text" name="usuario" required></label><br><br>
                <label>Contraseña: <input type="password" name="clave" required></label><br><br>
                <button type="submit">Entrar</button>
            </form>
        '''
    else:
        return redirect(url_for('index_get'))

@app.route('/index')
def index_get():
    if 'usuario' not in session:
        return redirect(url_for('index'))
    pacientes = cargar_datos(RUTA_PACIENTES)
    return render_template('index.html', pacientes=pacientes)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        fecha_nac = request.form.get('fecha_nac')
        sexo = request.form['sexo']
        diagnostico = request.form['diagnostico']
        medico = request.form['medico']

        pruebas_seleccionadas = request.form.getlist('pruebas')
        laboratorios = {}
        for clave in pruebas_seleccionadas:
            lab = request.form.get(f'laboratorio_{clave}', 'matriz')
            laboratorios[clave] = lab

        folio = generar_folio()

        # Calcular edad: si hay fecha de nacimiento, calcular con ella
        if fecha_nac and fecha_nac.strip():
            edad = calcular_edad(fecha_nac)
        else:
            # Si no, usar edad manual
            edad_manual = request.form.get('edad_manual', '').strip()
            if edad_manual.isdigit():
                edad = int(edad_manual)
            else:
                edad = 0

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

    # Cargar precios y pruebas
    pruebas, contenedores, _, precios_dict = cargar_catalogos()

    subtotal = 0
    maquila_matriz = 0
    maquila_sigma = 0
    envio = 0

    # Para envío: solo una vez por laboratorio
    laboratorios_con_envio = set()

    # Lista de estudios con maquila
    estudios_con_maquila = []

    for estudio in paciente.get('estudios', []):
        clave = estudio['clave']
        procesado_en = estudio.get('procesado_en', 'matriz')
        
        # === Precio público ===
        precio_data = precios_dict.get(f"prueba_{clave}")
        if precio_data:
            if procesado_en == 'sigma':
                precio_publico = precio_data.get('precio_publico_sigma', 0)
            else:
                precio_publico = precio_data.get('precio_publico_matriz', 0)
            subtotal += precio_publico

            # === Costos detallados ===
            costo = precio_data.get('costos', {}).get(procesado_en, {})

            # Solo el valor de "maquila"
            maquila = costo.get('maquila', 0)
            if procesado_en == 'matriz':
                maquila_matriz += maquila
            else:
                maquila_sigma += maquila

            # Registrar que este laboratorio tiene envío
            laboratorios_con_envio.add(procesado_en)

            # Guardar maquila por estudio
            estudios_con_maquila.append({
                "clave": clave,
                "nombre": estudio['nombre'],
                "procesado_en": procesado_en,
                "maquila": maquila,
                "precio": precio_publico
            })

    # Calcular envío: una vez por laboratorio
    for laboratorio in laboratorios_con_envio:
        for estudio in paciente.get('estudios', []):
            clave = estudio['clave']
            precio_data = precios_dict.get(f"prueba_{clave}")
            if precio_data:
                costo = precio_data.get('costos', {}).get(laboratorio, {})
                envio += costo.get('envio', 0)
            break

    total_maquila = maquila_matriz + maquila_sigma
    ganancia = subtotal - (total_maquila + envio)  # ❌ Ya no hay "materiales"
    iva = round(subtotal * 0.16, 2)
    total = subtotal + iva

    return render_template(
        'resumen.html',
        paciente=paciente,
        estudios_con_maquila=estudios_con_maquila,
        subtotal=round(subtotal, 2),
        iva=round(iva, 2),
        total=round(total, 2),
        maquila_matriz=round(maquila_matriz, 2),
        maquila_sigma=round(maquila_sigma, 2),
        total_maquila=round(total_maquila, 2),
        envio=round(envio, 2),
        ganancia=round(ganancia, 2)
    )

@app.route('/admin/pruebas', methods=['GET', 'POST'])
def admin_pruebas():
    if 'usuario' not in session or session['rol'] != 'quimico_admin':
        return "Acceso denegado. Solo el administrador puede acceder.", 403

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
    if 'usuario' not in session or session['rol'] != 'quimico_admin':
        return "Acceso denegado. Solo el administrador puede acceder.", 403

    if request.method == 'POST':
        nuevos_precios = []
        for key in request.form:
            if key.startswith('tipo_'):
                idx = key.split('_')[1]
                tipo = request.form[f'tipo_{idx}']
                id_elemento = request.form[f'id_{idx}']
                
                try:
                    maquila_matriz = float(request.form.get(f'maquila_matriz_{idx}', 0))
                    envio_matriz = float(request.form.get(f'envio_matriz_{idx}', 0))
                    maquila_sigma = float(request.form.get(f'maquila_sigma_{idx}', 0))
                    envio_sigma = float(request.form.get(f'envio_sigma_{idx}', 0))
                    ganancia = float(request.form[f'ganancia_{idx}'])
                    precio_publico_matriz = float(request.form[f'precio_publico_matriz_{idx}'])
                    precio_publico_sigma = float(request.form[f'precio_publico_sigma_{idx}'])
                    validado = request.form.get(f'validado_{idx}') == '1'
                except:
                    continue

                costo_matriz = maquila_matriz + envio_matriz
                costo_sigma = maquila_sigma + envio_sigma
                precio_sugerido_matriz = round(costo_matriz * (1 + ganancia / 100), 2)
                precio_sugerido_sigma = round(costo_sigma * (1 + ganancia / 100), 2)

                nuevos_precios.append({
                    "tipo": tipo,
                    "id_elemento": id_elemento,
                    "costos": {
                        "matriz": {
                            "maquila": maquila_matriz,
                            "envio": envio_matriz
                        },
                        "sigma": {
                            "maquila": maquila_sigma,
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

    # Asegurar que 'estudios' exista y sea una lista
    if 'estudios' not in paciente or paciente['estudios'] is None or not isinstance(paciente['estudios'], list):
        paciente['estudios'] = []

    if request.method == 'POST':
        # Actualizar datos básicos
        paciente['nombre'] = request.form['nombre']
        paciente['fecha_nacimiento'] = request.form.get('fecha_nac', '')
        paciente['sexo'] = request.form['sexo']
        paciente['diagnostico'] = request.form['diagnostico']
        paciente['medico'] = request.form['medico']

        # Calcular edad
        if paciente['fecha_nacimiento']:
            paciente['edad'] = calcular_edad(paciente['fecha_nacimiento'])
        else:
            edad_manual = request.form.get('edad_manual', '').strip()
            if edad_manual.isdigit():
                paciente['edad'] = int(edad_manual)
            else:
                paciente['edad'] = 0

        # Procesar nuevos estudios
        nuevos_estudios_claves = request.form.getlist('nuevos_estudios')
        laboratorios = {}
        for clave in nuevos_estudios_claves:
            lab = request.form.get(f'laboratorio_nuevo_{clave}', 'matriz')
            laboratorios[clave] = lab

        pruebas, contenedores, _, precios_dict = cargar_catalogos()

        nuevos_estudios = []
        claves_existentes = [e['clave'] for e in paciente['estudios']]
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

        # Añadir nuevos estudios
        paciente['estudios'].extend(nuevos_estudios)


        # ✅ ELIMINAR ESTUDIOS MARCADOS
        claves_a_eliminar = []
        for key in request.form:
            if key.startswith('eliminar_'):
                clave = key.replace('eliminar_', '')
                claves_a_eliminar.append(clave)

        # Conservar solo los estudios que NO están en claves_a_eliminar
        estudios_a_mantener = [e for e in paciente['estudios'] if e['clave'] not in claves_a_eliminar]
        paciente['estudios'] = estudios_a_mantener


        # Guardar cambios
        guardar_datos(RUTA_PACIENTES, pacientes)
        return redirect(url_for('index'))

    # GET: Mostrar formulario
    pruebas, contenedores, _, precios_dict = cargar_catalogos()

    # Asegurar que 'estudios' sea una lista válida
    if 'estudios' not in paciente or not isinstance(paciente['estudios'], list):
        paciente['estudios'] = []

    estudios_asignados = paciente['estudios']

    claves_asignadas = [e['clave'] for e in estudios_asignados]
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

@app.route('/descargar_datos/<archivo>')
def descargar_datos(archivo):
    import os
    from flask import send_file
    ruta = os.path.join('datos', archivo)
    if os.path.exists(ruta) and archivo in ['pacientes.json', 'precios.json', 'pruebas.json']:
        return send_file(ruta, as_attachment=True)
    return "Archivo no encontrado", 404

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('rol', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
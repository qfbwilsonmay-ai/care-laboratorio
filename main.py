# main.py
import os
import json
from datetime import datetime
from utils import generar_folio, calcular_edad, cargar_datos, guardar_datos
import config

# Rutas
RUTA_PACIENTES = 'datos/pacientes.json'
RUTA_RESULTADOS = 'datos/resultados.json'

# Asegurarnos que la carpeta datos exista
os.makedirs('datos', exist_ok=True)

# --- Función: Registrar paciente ---
def registrar_paciente():
    print("\n" + "="*50)
    print("REGISTRO DE PACIENTE")
    print("="*50)

    nombre = input("Nombre completo: ").strip()
    while True:
        fecha_nac = input("Fecha de nacimiento (AAAA-MM-DD): ").strip()
        try:
            datetime.strptime(fecha_nac, "%Y-%m-%d")
            break
        except ValueError:
            print("Formato inválido. Usa AAAA-MM-DD.")

    sexo = input("Sexo (M/F/O): ").strip().upper()
    while sexo not in ['M', 'F', 'O']:
        sexo = input("Sexo (M/F/O): ").strip().upper()

    diagnostico = input("Diagnóstico (opcional): ").strip()
    medico = input("Médico solicitante: ").strip()

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

    print(f"\n✅ Paciente registrado con éxito. Folio: {folio}")

# --- Función: Listar pacientes ---
def listar_pacientes():
    pacientes = cargar_datos(RUTA_PACIENTES)
    if not pacientes:
        print("\nNo hay pacientes registrados.")
        return

    print("\n" + "-"*80)
    print(f"{'FOLIO':<10} {'NOMBRE':<30} {'EDAD':<5} {'SEXO':<5} {'MÉDICO':<20}")
    print("-"*80)
    for p in pacientes:
        print(f"{p['folio']:<10} {p['nombre']:<30} {p['edad']:<5} {p['sexo']:<5} {p['medico']:<20}")

# --- Función: Registrar resultados ---
def registrar_resultados():
    folio = input("\nIngrese el folio del paciente: ").strip()
    pacientes = cargar_datos(RUTA_PACIENTES)
    paciente = next((p for p in pacientes if p['folio'] == folio), None)

    if not paciente:
        print("❌ Paciente no encontrado.")
        return

    print(f"\nPaciente: {paciente['nombre']} | Edad: {paciente['edad']} | Folio: {folio}")

    pruebas = [
        {"clave": "GLU", "nombre": "Glucosa", "unidad": "mg/dL", "valores_normales": "70-110"},
        {"clave": "CRE", "nombre": "Creatinina", "unidad": "mg/dL", "valores_normales": "0.7-1.3"},
        {"clave": "URO", "nombre": "Uroanálisis", "unidad": "", "valores_normales": "Negativo"}
    ]

    print("\nPruebas disponibles:")
    for i, p in enumerate(pruebas, 1):
        print(f"{i}. {p['clave']} - {p['nombre']} ({p['unidad']})")

    id_prueba = int(input("\nSeleccione el número de la prueba: ")) - 1
    if id_prueba < 0 or id_prueba >= len(pruebas):
        print("❌ Selección inválida.")
        return

    prueba = pruebas[id_prueba]
    resultado = input(f"Resultado para {prueba['nombre']} ({prueba['unidad']}): ").strip()

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

    print("✅ Resultado registrado con éxito.")

# --- Función: Ver reporte de paciente ---
def ver_reporte():
    folio = input("\nIngrese el folio del paciente: ").strip()
    pacientes = cargar_datos(RUTA_PACIENTES)
    paciente = next((p for p in pacientes if p['folio'] == folio), None)

    if not paciente:
        print("❌ Paciente no encontrado.")
        return

    resultados = [r for r in cargar_datos(RUTA_RESULTADOS) if r['folio'] == folio]

    print("\n" + "="*60)
    print("           REPORTE DE RESULTADOS - CARE")
    print("="*60)
    print(f"Laboratorio: {config.NOMBRE_LABORATORIO}")
    print(f"Sucursal: {config.SUCURSAL}")
    print(f"Dirección: {config.DIRECCION}")
    print(f"Teléfono: {config.TELEFONO}")
    print("-"*60)
    print(f"Paciente: {paciente['nombre']}")
    print(f"Folio: {paciente['folio']} | Edad: {paciente['edad']} | Sexo: {paciente['sexo']}")
    print(f"Médico: {paciente['medico']} | Fecha: {datetime.now().strftime('%d/%m/%Y')}")
    print("-"*60)

    if not resultados:
        print("No hay resultados registrados.")
    else:
        print(f"{'Prueba':<20} {'Resultado':<15} {'Unidad':<10} {'Normales'}")
        print("-"*60)
        for r in resultados:
            print(f"{r['nombre']:<20} {r['resultado']:<15} {r['unidad']:<10} {r['valores_normales']}")

    print("\nNota: Los valores fuera de rango deben ser revisados por el médico.")
    print("Firma del químico: _________________________")
    print("="*60)

# --- Menú Principal ---
def menu():
    while True:
        print("\n" + "#"*50)
        print(f"{config.NOMBRE_LABORATORIO:^50}")
        print("#"*50)
        print("1. Registrar paciente")
        print("2. Listar pacientes")
        print("3. Registrar resultados")
        print("4. Ver reporte de paciente")
        print("5. Salir")
        print("#"*50)

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            registrar_paciente()
        elif opcion == "2":
            listar_pacientes()
        elif opcion == "3":
            registrar_resultados()
        elif opcion == "4":
            ver_reporte()
        elif opcion == "5":
            print("👋 Gracias por usar CARE. ¡Hasta pronto!")
            break
        else:
            print("❌ Opción no válida.")

# --- Ejecución ---
if __name__ == "__main__":
    menu()
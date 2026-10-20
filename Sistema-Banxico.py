"""
Autor: Mario
Objetivo:
Obtener el interés simple con tasa de CETES a 28 días
haciendo request en tiempo real a las series oportunas de Banxico
y enviando por email el reporte de resultados mediante SMTP.
"""

import os
import time as t
import requests
from smtplib import SMTP
from dotenv import load_dotenv

# Carga de variables de entorno desde el archivo .env
load_dotenv()

TOKEN = os.getenv("BANXICO_TOKEN")

# ==========================================================
# FUNCIÓN 1
# ==========================================================
def consultar_serie_banxico(id_serie: str) -> float:
    """
    Función 1: Consulta una serie oportuna en Banxico en tiempo real.
    Valida la conectividad y el código de estado (status_code).
    """
    if not TOKEN:
        print("[Error] No se encontró el BANXICO_TOKEN en el archivo .env.")
        return 0.0

    headers = {"Bmx-Token": TOKEN}
    enlace = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{id_serie}/datos/oportuno"

    try:
        response = requests.get(url=enlace, headers=headers)

        if response.status_code == 200:
            datos = response.json()
            valor = float(datos['bmx']['series'][0]['datos'][0]['dato'])
            return valor
        else:
            print(f"[Error] Fallo en la respuesta de Banxico. Status: {response.status_code}")
            return 0.0
            
    except requests.exceptions.RequestException as e:
        print(f"[Error de conexión] No se pudo conectar a Banxico: {e}")
        return 0.0

# ==========================================================
# FUNCIÓN 2
# ==========================================================
def obtener_tasa_cetes_28d() -> float:
    """
    Función 2: Obtiene la tasa oportuna de CETES a 28 días (Serie SF43936).
    """
    serie_cetes = "SF43936"
    return consultar_serie_banxico(serie_cetes)

# ==========================================================
# FUNCIÓN 3
# ==========================================================
def calcular_interes(capital: float, plazo_meses: int, tasa_anual: float) -> tuple:
    """
    Función 3: Calcula el interés simple y compuesto a partir de una tasa anual.
    Retorna los intereses y montos finales.
    """
    tasa_decimal = tasa_anual / 100.0
    tasa_mensual = tasa_decimal / 12.0

    # Interés simple
    int_simple = capital * tasa_mensual * plazo_meses
    monto_simple = capital + int_simple

    # Interés compuesto
    monto_compuesto = capital * ((1 + tasa_mensual) ** plazo_meses)
    int_compuesto = monto_compuesto - capital

    return int_simple, monto_simple, int_compuesto, monto_compuesto

# ==========================================================
# FUNCIÓN 4
# ==========================================================
def enviar_reporte_email(destinatario: str, reporte_texto: str) -> bool:
    """
    Función 4: Conecta vía SMTP seguro y envía el reporte generado.
    Codifica el mensaje en UTF-8 para soportar acentos y caracteres especiales.
    """
    remitente = os.getenv("CORREO_REMITENTE")
    password = os.getenv("CORREO_PASSWORD")

    if not remitente or not password:
        print("[Error] Faltan credenciales de correo en el archivo .env.")
        return False

    mensaje = f"Subject: Reporte de Calculo ISC - Actuaria\n\n{reporte_texto}"

    try:
        print("Conectando con el servidor SMTP...")
        servidor = SMTP("smtp.gmail.com", 587)
        servidor.starttls()  # Conexión cifrada
        servidor.login(remitente, password)
        servidor.sendmail(remitente, destinatario, mensaje.encode('utf-8'))
        servidor.quit()
        print(f"¡El correo fue enviado exitosamente a {destinatario}!")
        return True
    except Exception as e:
        print(f"[Error SMTP] No se pudo enviar el email: {e}")
        return False

# ==========================================================
# FUNCIÓN 5: Menú Principal
# ==========================================================
def menu_principal():
    """
    Función 5: Menú interactivo con 3 opciones:
    1. Consulta Banxico tiempo real serie X (Fija a CETES 28 días)
    2. Calcular ISC con CETES 28 días y enviar reporte por email
    3. Salir con delay de 5 segundos
    """
    while True:
        print("\n=============================================")
        print("   SISTEMA FINANCIERO - BANXICO Y REPORTES   ")
        print("=============================================")
        print("1. Consulta Banxico tiempo real serie X (CETES 28 días)")
        print("2. Calcular ISC con CETES 28 días y enviar reporte")
        print("3. Salir")
        print("=============================================\n")

        opcion = input("Elige una opción (1, 2, 3): ").strip()

        if opcion == "1":
            print("\n--- Consulta Banxico (Serie X: CETES a 28 días) ---")
            serie_x = "SF43936"
            print(f"Consultando conectividad para la serie: {serie_x}...")
            
            valor = consultar_serie_banxico(serie_x)
            if valor > 0.0:
                print(f"Conexión exitosa. El valor oportuno en tiempo real es: {valor}%")

        elif opcion == "2":
            print("\n--- Cálculo de ISC con CETES 28 días ---")
            try:
                capital = float(input("Ingresa el capital inicial: $"))
                plazo_meses = int(input("Ingresa el plazo en meses: "))
            except ValueError:
                print("[Error] Ingresa solo números válidos.")
                continue

            print("\nConsultando tasa CETES a 28 días en Banxico...")
            tasa_cetes = obtener_tasa_cetes_28d()

            if tasa_cetes == 0.0:
                print("[Aviso] No se pudo obtener la tasa de CETES. Operación cancelada.")
                continue

            print(f"Tasa obtenida: {tasa_cetes}% anual")

            # Cálculo de interés
            i_simp, m_simp, i_comp, m_comp = calcular_interes(capital, plazo_meses, tasa_cetes)

            reporte = (
                f"REPORTE FINANCIERO AUTOMATIZADO\n"
                f"-----------------------------------\n"
                f"Capital: ${capital:,.2f}\n"
                f"Plazo: {plazo_meses} meses\n"
                f"Tasa CETES 28d (Banxico): {tasa_cetes}%\n\n"
                f"Interés Simple:\n"
                f"  - Rendimiento: ${i_simp:,.2f}\n"
                f"  - Monto Total: ${m_simp:,.2f}\n\n"
                f"Interés Compuesto:\n"
                f"  - Rendimiento: ${i_comp:,.2f}\n"
                f"  - Monto Total: ${m_comp:,.2f}\n"
            )

            print("\nReporte Generado:")
            print(reporte)

            correo_destinatario = input("Ingresa el correo para recibir el reporte: ").strip()

            print("Enviando...")
            t.sleep(3)  # Delay antes del envío

            enviar_reporte_email(correo_destinatario, reporte)

        elif opcion == "3":
            print("\nCerrando el sistema...")
            t.sleep(5) 
            print("¡Hasta luego!")
            break

        else:
            print("\n[Error] Opción no válida. Ingresa 1, 2 o 3.")

if __name__ == "__main__":
    menu_principal()
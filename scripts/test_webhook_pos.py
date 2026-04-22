"""
Script de prueba para simular webhooks de POS físicos
Útil para probar el sistema sin necesidad de un terminal real
"""

import requests
import json
import hmac
import hashlib
from datetime import datetime

# CONFIGURACIÓN
BASE_URL = "http://127.0.0.1:8000"  # Cambia según tu URL
PROVEEDOR = "cardnet"  # o "azul"
WEBHOOK_SECRET = "test_secret_123_para_pruebas"  # Debe coincidir con .env

# Datos del pago simulado
DATOS_PAGO = {
    "transaction_id": f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
    "terminal_id": "VF-TEST-001",
    "amount": 5000.00,  # RD$ 5,000
    "status": "approved",
    "reference_number": f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
    "card_last_4": "1234",
    "card_type": "Visa",
    "transaction_date": datetime.now().isoformat(),
    # Cédula de Lucy Aquino (estudiante real con factura pendiente)
    "custom_field_1": "01201012458"
}

def generar_firma(payload, secret):
    """Genera la firma HMAC para validar el webhook"""
    if isinstance(payload, dict):
        payload = json.dumps(payload, sort_keys=True)
    
    firma = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return firma

def simular_webhook_cardnet():
    """Simula un webhook de Cardnet"""
    url = f"{BASE_URL}/webhooks/pos/cardnet/"
    
    # Convertir payload a JSON
    payload = json.dumps(DATOS_PAGO, sort_keys=True)
    
    # Generar firma
    firma = generar_firma(payload, WEBHOOK_SECRET)
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "X-Cardnet-Signature": firma
    }
    
    print("=" * 60)
    print("SIMULADOR DE WEBHOOK CARDNET")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Payload: {payload}")
    print(f"Firma: {firma}")
    print("=" * 60)
    
    # Enviar request
    try:
        response = requests.post(url, data=payload, headers=headers)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("\n✅ ¡Webhook procesado exitosamente!")
        else:
            print("\n❌ Error procesando webhook")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

def simular_webhook_azul():
    """Simula un webhook de Azul"""
    url = f"{BASE_URL}/webhooks/pos/azul/"
    
    # Adaptar datos para formato Azul (PascalCase)
    datos_azul = {
        "TransactionId": DATOS_PAGO["transaction_id"],
        "TerminalId": DATOS_PAGO["terminal_id"],
        "Amount": DATOS_PAGO["amount"],
        "Status": DATOS_PAGO["status"],
        "ReferenceNumber": DATOS_PAGO["reference_number"],
        "CardLast4": DATOS_PAGO["card_last_4"],
        "CardType": DATOS_PAGO["card_type"],
        "TransactionDate": DATOS_PAGO["transaction_date"],
        "CustomField1": DATOS_PAGO["custom_field_1"]
    }
    
    # Convertir payload a JSON
    payload = json.dumps(datos_azul, sort_keys=True)
    
    # Generar firma
    firma = generar_firma(payload, WEBHOOK_SECRET)
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "X-Azul-Signature": firma
    }
    
    print("=" * 60)
    print("SIMULADOR DE WEBHOOK AZUL")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Payload: {payload}")
    print(f"Firma: {firma}")
    print("=" * 60)
    
    # Enviar request
    try:
        response = requests.post(url, data=payload, headers=headers)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("\n✅ ¡Webhook procesado exitosamente!")
        else:
            print("\n❌ Error procesando webhook")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 60)
    print("SCRIPT DE PRUEBA - WEBHOOKS POS FÍSICOS")
    print("=" * 60)
    print("\nIMPORTANTE:")
    print("1. Asegúrate de que el servidor Django esté corriendo")
    print("2. Cambia 'custom_field_1' por la cédula de un estudiante real")
    print("3. Configura el WEBHOOK_SECRET en este script")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\nUso:")
        print("  python test_webhook_pos.py cardnet")
        print("  python test_webhook_pos.py azul")
        sys.exit(1)
    
    proveedor = sys.argv[1].lower()
    
    if proveedor == "cardnet":
        simular_webhook_cardnet()
    elif proveedor == "azul":
        simular_webhook_azul()
    else:
        print(f"❌ Proveedor no válido: {proveedor}")
        print("Opciones: cardnet, azul")

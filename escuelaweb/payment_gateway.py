"""
Sistema de Integración con Pasarelas de Pago (POS Físico)
Soporta: Cardnet, Azul, y otros proveedores dominicanos

Este módulo maneja la integración con los servicios de pago físico (POS)
para recibir notificaciones de pagos realizados en dispositivos Verifone u otros.
"""

import requests
import base64
import hashlib
import hmac
import json
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class PaymentGatewayException(Exception):
    """Exception para errores de pasarela de pago"""
    pass


class CardnetPOSGateway:
    """
    Integración con Cardnet para pagos POS físicos
    
    Funcionalidades:
    - Verificar status de transacciones
    - Consultar pagos por terminal
    - Validar webhooks
    """
    
    def __init__(self):
        self.api_key = settings.CARDNET_API_KEY
        self.merchant_id = settings.CARDNET_MERCHANT_ID
        self.webhook_secret = settings.CARDNET_WEBHOOK_SECRET
        self.base_url = settings.CARDNET_API_URL
        
        if not all([self.api_key, self.merchant_id]):
            raise PaymentGatewayException("Cardnet: Credenciales no configuradas")
    
    def validate_webhook(self, payload, signature):
        """
        Valida que el webhook viene de Cardnet
        
        Args:
            payload: Datos del webhook (string o dict)
            signature: Firma enviada por Cardnet
            
        Returns:
            bool: True si la firma es válida
        """
        try:
            if isinstance(payload, dict):
                payload = json.dumps(payload, sort_keys=True)
            
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error validando webhook Cardnet: {str(e)}")
            return False
    
    def get_transaction_details(self, transaction_id):
        """
        Consulta detalles de una transacción
        
        Args:
            transaction_id: ID de la transacción en Cardnet
            
        Returns:
            dict: Detalles de la transacción
        """
        try:
            url = f"{self.base_url}/transactions/{transaction_id}"
            
            headers = {
                "Content-Type": "application/json",
                "Api-Key": self.api_key,
                "Merchant-Id": self.merchant_id
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error consultando transacción Cardnet: {str(e)}")
            raise PaymentGatewayException(f"Error consultando transacción: {str(e)}")
    
    def query_terminal_transactions(self, terminal_id, fecha_inicio=None, fecha_fin=None):
        """
        Consulta transacciones de un terminal específico
        
        Args:
            terminal_id: ID del terminal POS
            fecha_inicio: Fecha inicio (datetime)
            fecha_fin: Fecha fin (datetime)
            
        Returns:
            list: Lista de transacciones
        """
        try:
            url = f"{self.base_url}/terminals/{terminal_id}/transactions"
            
            headers = {
                "Content-Type": "application/json",
                "Api-Key": self.api_key,
                "Merchant-Id": self.merchant_id
            }
            
            params = {}
            if fecha_inicio:
                params['fecha_inicio'] = fecha_inicio.isoformat()
            if fecha_fin:
                params['fecha_fin'] = fecha_fin.isoformat()
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json().get('transactions', [])
            
        except requests.RequestException as e:
            logger.error(f"Error consultando terminal Cardnet: {str(e)}")
            return []


class AzulPOSGateway:
    """
    Integración con Azul para pagos POS físicos
    
    Similar a Cardnet pero con la API de Azul
    """
    
    def __init__(self):
        self.user = settings.AZUL_USER
        self.password = settings.AZUL_PASSWORD
        self.store_id = settings.AZUL_STORE_ID
        self.webhook_secret = settings.AZUL_WEBHOOK_SECRET
        self.base_url = settings.AZUL_API_URL
        
        if not all([self.user, self.password, self.store_id]):
            raise PaymentGatewayException("Azul: Credenciales no configuradas")
    
    def _get_auth_header(self):
        """Genera header de autenticación Basic"""
        credentials = f"{self.user}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def validate_webhook(self, payload, signature):
        """
        Valida que el webhook viene de Azul
        
        Args:
            payload: Datos del webhook
            signature: Firma enviada por Azul
            
        Returns:
            bool: True si la firma es válida
        """
        try:
            if isinstance(payload, dict):
                payload = json.dumps(payload, sort_keys=True)
            
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error validando webhook Azul: {str(e)}")
            return False
    
    def get_transaction_details(self, transaction_id):
        """
        Consulta detalles de una transacción
        
        Args:
            transaction_id: ID de la transacción en Azul
            
        Returns:
            dict: Detalles de la transacción
        """
        try:
            url = f"{self.base_url}/api/v1/Transaction/{transaction_id}"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": self._get_auth_header()
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error consultando transacción Azul: {str(e)}")
            raise PaymentGatewayException(f"Error consultando transacción: {str(e)}")
    
    def query_terminal_transactions(self, terminal_id, fecha_inicio=None, fecha_fin=None):
        """
        Consulta transacciones de un terminal específico
        
        Args:
            terminal_id: ID del terminal POS
            fecha_inicio: Fecha inicio (datetime)
            fecha_fin: Fecha fin (datetime)
            
        Returns:
            list: Lista de transacciones
        """
        try:
            url = f"{self.base_url}/api/v1/Terminal/{terminal_id}/Transactions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": self._get_auth_header()
            }
            
            params = {}
            if fecha_inicio:
                params['StartDate'] = fecha_inicio.strftime('%Y-%m-%d')
            if fecha_fin:
                params['EndDate'] = fecha_fin.strftime('%Y-%m-%d')
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json().get('Transactions', [])
            
        except requests.RequestException as e:
            logger.error(f"Error consultando terminal Azul: {str(e)}")
            return []


def get_payment_gateway(provider='cardnet'):
    """
    Factory function para obtener la pasarela de pago configurada
    
    Args:
        provider: 'cardnet' o 'azul'
        
    Returns:
        Instancia de la pasarela de pago
    """
    if provider.lower() == 'cardnet':
        return CardnetPOSGateway()
    elif provider.lower() == 'azul':
        return AzulPOSGateway()
    else:
        raise PaymentGatewayException(f"Proveedor no soportado: {provider}")

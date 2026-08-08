"""
Vistas para recibir webhooks de pagos POS físicos
Maneja notificaciones de Cardnet, Azul y otros proveedores
"""

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import json
import logging

from .models import (
    TransaccionPOS, Factura, PagoFactura, CustomUser
)
from .payment_gateway import get_payment_gateway, PaymentGatewayException
from .utils_impresion import imprimir_factura_pos, enviar_factura_email

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_cardnet(request):
    """
    Webhook para recibir notificaciones de pagos de Cardnet
    
    Cuando un cliente pasa su tarjeta en un POS Verifone conectado a Cardnet,
    Cardnet envía una notificación a este endpoint.
    
    Flujo:
    1. Recibe notificación
    2. Valida firma
    3. Busca factura pendiente del estudiante
    4. Crea registro de pago
    5. Marca factura como pagada
    6. Imprime factura
    """
    try:
        # Leer datos del webhook
        payload = request.body.decode('utf-8')
        data = json.loads(payload)
        
        # Obtener firma del header
        signature = request.headers.get('X-Cardnet-Signature', '')
        
        # Validar firma (solo si no estamos en modo prueba)
        api_key = getattr(settings, 'CARDNET_API_KEY', '')
        if api_key and api_key != 'PENDIENTE_SOLICITAR':
            # Modo producción: validar firma
            try:
                gateway = get_payment_gateway('cardnet')
                if not gateway.validate_webhook(payload, signature):
                    logger.warning(f"Webhook Cardnet con firma inválida: {data}")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Firma inválida'
                    }, status=401)
            except PaymentGatewayException as e:
                logger.error(f"Error validando webhook: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)
        else:
            # Modo prueba: solo verificar que el webhook_secret coincida
            webhook_secret = getattr(settings, 'CARDNET_WEBHOOK_SECRET', '')
            if webhook_secret and signature:
                import hmac
                import hashlib
                expected_signature = hmac.new(
                    webhook_secret.encode(),
                    payload.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                if not hmac.compare_digest(expected_signature, signature):
                    logger.warning(f"Webhook de prueba con firma inválida")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Firma inválida (modo prueba)'
                    }, status=401)
            else:
                logger.info("Webhook de prueba recibido (sin validación de firma)")
        
        # Procesar el pago
        resultado = procesar_pago_pos(data, 'cardnet')
        
        return JsonResponse(resultado)
        
    except Exception as e:
        logger.error(f"Error procesando webhook Cardnet: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_azul(request):
    """
    Webhook para recibir notificaciones de pagos de Azul
    
    Similar al de Cardnet pero para Azul
    """
    try:
        # Leer datos del webhook
        payload = request.body.decode('utf-8')
        data = json.loads(payload)
        
        # Obtener firma del header
        signature = request.headers.get('X-Azul-Signature', '')
        
        # Validar firma (solo si no estamos en modo prueba)
        azul_user = getattr(settings, 'AZUL_USER', '')
        if azul_user and azul_user != 'PENDIENTE_SOLICITAR':
            # Modo producción: validar firma
            try:
                gateway = get_payment_gateway('azul')
                if not gateway.validate_webhook(payload, signature):
                    logger.warning(f"Webhook Azul con firma inválida: {data}")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Firma inválida'
                    }, status=401)
            except PaymentGatewayException as e:
                logger.error(f"Error validando webhook: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)
        else:
            # Modo prueba: solo verificar que el webhook_secret coincida
            webhook_secret = getattr(settings, 'AZUL_WEBHOOK_SECRET', '')
            if webhook_secret and signature:
                import hmac
                import hashlib
                expected_signature = hmac.new(
                    webhook_secret.encode(),
                    payload.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                if not hmac.compare_digest(expected_signature, signature):
                    logger.warning(f"Webhook de prueba con firma inválida")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Firma inválida (modo prueba)'
                    }, status=401)
            else:
                logger.info("Webhook de prueba recibido (sin validación de firma)")
        
        # Procesar el pago
        resultado = procesar_pago_pos(data, 'azul')
        
        return JsonResponse(resultado)
        
    except Exception as e:
        logger.error(f"Error procesando webhook Azul: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@transaction.atomic
def procesar_pago_pos(data, proveedor):
    """
    Procesa un pago recibido de un POS físico
    
    Args:
        data: Datos del webhook
        proveedor: 'cardnet' o 'azul'
        
    Returns:
        dict: Resultado del procesamiento
    """
    try:
        # Extraer datos según el proveedor
        if proveedor == 'cardnet':
            transaction_id = data.get('transaction_id')
            terminal_id = data.get('terminal_id')
            monto = Decimal(str(data.get('amount', 0)))
            referencia = data.get('reference_number')
            estado = data.get('status')  # 'approved', 'declined', etc.
            tarjeta_ultimos_4 = data.get('card_last_4')
            tipo_tarjeta = data.get('card_type', 'Desconocido')
            fecha_transaccion_str = data.get('transaction_date')
            # Datos adicionales para identificar al estudiante
            cedula_estudiante = data.get('custom_field_1')  # ID del estudiante
            
        elif proveedor == 'azul':
            transaction_id = data.get('TransactionId')
            terminal_id = data.get('TerminalId')
            monto = Decimal(str(data.get('Amount', 0)))
            referencia = data.get('ReferenceNumber')
            estado = data.get('Status')
            tarjeta_ultimos_4 = data.get('CardLast4')
            tipo_tarjeta = data.get('CardType', 'Desconocido')
            fecha_transaccion_str = data.get('TransactionDate')
            cedula_estudiante = data.get('CustomField1')
        
        else:
            raise ValueError(f"Proveedor no soportado: {proveedor}")
        
        # Verificar que el pago fue aprobado
        if estado.lower() not in ['approved', 'aprobado', 'success', 'exitoso']:
            logger.info(f"Transacción {transaction_id} no aprobada: {estado}")
            return {
                'status': 'ignored',
                'message': f'Transacción no aprobada: {estado}'
            }
        
        # Verificar que no sea duplicada
        if TransaccionPOS.objects.filter(
            transaction_id=transaction_id,
            proveedor=proveedor
        ).exists():
            logger.warning(f"Transacción {transaction_id} duplicada")
            return {
                'status': 'duplicate',
                'message': 'Transacción ya procesada'
            }
        
        # BUSCAR AL ESTUDIANTE
        # Opción 1: Por cédula si viene en el webhook
        estudiante = None
        if cedula_estudiante:
            try:
                estudiante = CustomUser.objects.get(
                    cedula=cedula_estudiante,
                    rol='Estudiante',
                    is_active=True
                )
            except CustomUser.DoesNotExist:
                pass
        
        # Opción 2: Buscar por el terminal (cada terminal puede estar asignado a un estudiante)
        # Esto requiere configuración previa: TerminalEstudiante model
        if not estudiante:
            try:
                from .models import TerminalEstudiante
                asignacion = TerminalEstudiante.objects.get(
                    terminal_id=terminal_id,
                    activo=True
                )
                estudiante = asignacion.estudiante
            except:
                pass
        
        # Si no encontramos estudiante, registrar la transacción pero sin asociar
        if not estudiante:
            logger.warning(f"No se pudo identificar estudiante para transacción {transaction_id}")
            # Crear transacción sin estudiante para revisión manual
            TransaccionPOS.objects.create(
                transaction_id=transaction_id,
                proveedor=proveedor,
                terminal_id=terminal_id,
                monto=monto,
                referencia=referencia,
                estado='pendiente_revision',
                tarjeta_ultimos_4=tarjeta_ultimos_4,
                tipo_tarjeta=tipo_tarjeta,
                datos_webhook=data,
                observaciones='No se pudo identificar al estudiante automáticamente'
            )
            
            return {
                'status': 'pending_review',
                'message': 'Pago recibido pero requiere revisión manual',
                'transaction_id': transaction_id
            }
        
        # BUSCAR FACTURAS PENDIENTES DEL ESTUDIANTE
        facturas_pendientes = Factura.objects.filter(
            cliente=estudiante,
            estado__in=['pendiente', 'vencida', 'parcial']
        ).order_by('fecha_vencimiento')
        
        if not facturas_pendientes.exists():
            logger.warning(f"Estudiante {estudiante.email} no tiene facturas pendientes")
            # Crear transacción para revisión
            TransaccionPOS.objects.create(
                transaction_id=transaction_id,
                proveedor=proveedor,
                terminal_id=terminal_id,
                estudiante=estudiante,
                monto=monto,
                referencia=referencia,
                estado='sin_factura',
                tarjeta_ultimos_4=tarjeta_ultimos_4,
                tipo_tarjeta=tipo_tarjeta,
                datos_webhook=data,
                observaciones='El estudiante no tiene facturas pendientes'
            )
            
            return {
                'status': 'no_pending_invoices',
                'message': 'Estudiante sin facturas pendientes',
                'student': estudiante.get_full_name()
            }
        
        # APLICAR EL PAGO A LAS FACTURAS
        monto_restante = monto
        facturas_pagadas = []
        referencia_pago = f"POS-{proveedor.upper()}-{transaction_id}"
        
        for factura in facturas_pendientes:
            if monto_restante <= 0:
                break
            
            # Calcular cuánto falta por pagar en esta factura
            monto_pendiente = factura.total - factura.monto_pagado
            
            if monto_pendiente <= 0:
                continue
            
            # Determinar cuánto aplicar a esta factura
            monto_aplicar = min(monto_restante, monto_pendiente)
            
            # Crear registro de pago
            pago = PagoFactura.objects.create(
                factura=factura,
                monto=monto_aplicar,
                metodo_pago='tarjeta',
                referencia=referencia_pago,
                observaciones=f"Pago POS {proveedor} - Terminal {terminal_id} - Tarjeta {tipo_tarjeta} ****{tarjeta_ultimos_4}",
                registrado_por=None  # Pago automático
            )
            
            # Actualizar factura
            factura.monto_pagado += monto_aplicar
            factura.metodo_pago = 'tarjeta'
            
            if factura.monto_pagado >= factura.total:
                factura.estado = 'pagada'
                factura.fecha_pago_completo = timezone.now()
            else:
                factura.estado = 'parcial'
            
            factura.save()
            
            facturas_pagadas.append({
                'numero': factura.numero_factura,
                'monto': float(monto_aplicar)
            })
            
            monto_restante -= monto_aplicar
        
        # Crear registro de transacción POS
        transaccion_pos = TransaccionPOS.objects.create(
            transaction_id=transaction_id,
            proveedor=proveedor,
            terminal_id=terminal_id,
            estudiante=estudiante,
            monto=monto,
            referencia=referencia,
            estado='procesado',
            tarjeta_ultimos_4=tarjeta_ultimos_4,
            tipo_tarjeta=tipo_tarjeta,
            datos_webhook=data,
            observaciones=f"Pago procesado automáticamente. {len(facturas_pagadas)} factura(s) pagada(s)."
        )
        
        # IMPRIMIR FACTURA (si está configurado)
        try:
            if getattr(settings, 'AUTO_PRINT_INVOICES', True):
                for factura_info in facturas_pagadas:
                    factura = Factura.objects.get(numero_factura=factura_info['numero'])
                    imprimir_factura_pos(factura, transaccion_pos)
        except Exception as e:
            logger.error(f"Error imprimiendo factura: {str(e)}")
        
        # ENVIAR FACTURA POR EMAIL (si está configurado)
        try:
            if getattr(settings, 'AUTO_EMAIL_INVOICES', True) and estudiante.email:
                for factura_info in facturas_pagadas:
                    factura = Factura.objects.get(numero_factura=factura_info['numero'])
                    enviar_factura_email(factura, estudiante)
        except Exception as e:
            logger.error(f"Error enviando email: {str(e)}")
        
        logger.info(f"Pago POS procesado exitosamente: {transaction_id} - {estudiante.get_full_name()} - RD${monto}")
        
        return {
            'status': 'success',
            'message': 'Pago procesado exitosamente',
            'transaction_id': transaction_id,
            'student': estudiante.get_full_name(),
            'invoices_paid': facturas_pagadas,
            'total_amount': float(monto)
        }
        
    except Exception as e:
        logger.error(f"Error en procesar_pago_pos: {str(e)}", exc_info=True)
        raise


@require_http_methods(["GET"])
def consultar_transaccion_pos(request, transaction_id):
    """
    Consulta el estado de una transacción POS
    
    Útil para verificar manualmente el estado de un pago
    """
    try:
        transaccion = TransaccionPOS.objects.get(transaction_id=transaction_id)
        
        return JsonResponse({
            'status': 'success',
            'transaction': {
                'id': transaccion.transaction_id,
                'proveedor': transaccion.proveedor,
                'monto': float(transaccion.monto),
                'estado': transaccion.estado,
                'estudiante': transaccion.estudiante.get_full_name() if transaccion.estudiante else None,
                'fecha': transaccion.fecha_transaccion.isoformat()
            }
        })
        
    except TransaccionPOS.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Transacción no encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

"""
Tareas asíncronas de Celery para el sistema de suscripciones
"""
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import connection
from django_tenants.utils import get_tenant_model, get_public_schema_name
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def verificar_suscripciones_por_vencer():
    """
    Verifica las suscripciones que están por vencer en los próximos 3 días
    y envía notificaciones a los administradores
    """
    from ventasweb.models import Suscripcion
    
    # Cambiar al schema público donde están las suscripciones
    original_schema = connection.schema_name
    try:
        connection.set_schema(get_public_schema_name())
        
        # Buscar suscripciones que vencen en 3 días
        fecha_limite = timezone.now() + timedelta(days=3)
        
        suscripciones_por_vencer = Suscripcion.objects.filter(
            estado='ACTIVA',
            fecha_proximo_pago__lte=fecha_limite,
            fecha_proximo_pago__gte=timezone.now()
        ).select_related('tenant', 'plan')
        
        for suscripcion in suscripciones_por_vencer:
            try:
                enviar_recordatorio_pago.delay(suscripcion.id)
                logger.info(f"Recordatorio de pago programado para {suscripcion.tenant.nombre}")
            except Exception as e:
                logger.error(f"Error al programar recordatorio para {suscripcion.tenant.nombre}: {e}")
        
        logger.info(f"Verificadas {suscripciones_por_vencer.count()} suscripciones próximas a vencer")
        return suscripciones_por_vencer.count()
        
    except Exception as e:
        logger.error(f"Error en verificar_suscripciones_por_vencer: {e}")
        return 0
    finally:
        connection.set_schema(original_schema)


@shared_task
def enviar_recordatorios_pago():
    """
    Envía recordatorios de pago a todas las suscripciones en período de prueba
    que están próximas a expirar
    """
    from ventasweb.models import Suscripcion
    
    original_schema = connection.schema_name
    try:
        connection.set_schema(get_public_schema_name())
        
        # Suscripciones en trial que vencen en 7 días o menos
        fecha_limite = timezone.now() + timedelta(days=7)
        
        suscripciones_trial = Suscripcion.objects.filter(
            estado='TRIAL',
            fecha_fin_trial__lte=fecha_limite,
            fecha_fin_trial__gte=timezone.now()
        ).select_related('tenant', 'plan')
        
        contador = 0
        for suscripcion in suscripciones_trial:
            try:
                enviar_recordatorio_trial.delay(suscripcion.id)
                contador += 1
            except Exception as e:
                logger.error(f"Error al enviar recordatorio trial para {suscripcion.tenant.nombre}: {e}")
        
        logger.info(f"Enviados {contador} recordatorios de trial")
        return contador
        
    except Exception as e:
        logger.error(f"Error en enviar_recordatorios_pago: {e}")
        return 0
    finally:
        connection.set_schema(original_schema)


@shared_task
def actualizar_suscripciones_vencidas():
    """
    Actualiza el estado de las suscripciones que han vencido
    """
    from ventasweb.models import Suscripcion
    
    original_schema = connection.schema_name
    try:
        connection.set_schema(get_public_schema_name())
        
        ahora = timezone.now()
        
        # Actualizar trials vencidos
        trials_vencidos = Suscripcion.objects.filter(
            estado='TRIAL',
            fecha_fin_trial__lt=ahora
        )
        count_trials = trials_vencidos.update(estado='VENCIDA')
        
        # Actualizar suscripciones activas vencidas
        activas_vencidas = Suscripcion.objects.filter(
            estado='ACTIVA',
            fecha_proximo_pago__lt=ahora - timedelta(days=7)  # 7 días de gracia
        )
        count_activas = activas_vencidas.update(estado='VENCIDA')
        
        total = count_trials + count_activas
        logger.info(f"Actualizadas {total} suscripciones vencidas ({count_trials} trials, {count_activas} activas)")
        
        # Enviar notificaciones de vencimiento
        for suscripcion in Suscripcion.objects.filter(estado='VENCIDA'):
            try:
                enviar_notificacion_vencimiento.delay(suscripcion.id)
            except Exception as e:
                logger.error(f"Error al enviar notificación de vencimiento para {suscripcion.tenant.nombre}: {e}")
        
        return total
        
    except Exception as e:
        logger.error(f"Error en actualizar_suscripciones_vencidas: {e}")
        return 0
    finally:
        connection.set_schema(original_schema)


@shared_task
def generar_reporte_mensual_suscripciones():
    """
    Genera un reporte mensual de todas las suscripciones
    """
    from ventasweb.models import Suscripcion, HistorialPago
    
    original_schema = connection.schema_name
    try:
        connection.set_schema(get_public_schema_name())
        
        # Calcular estadísticas del mes anterior
        inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        inicio_mes = inicio_mes.replace(day=1)
        fin_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Suscripciones activas
        total_activas = Suscripcion.objects.filter(estado='ACTIVA').count()
        total_trial = Suscripcion.objects.filter(estado='TRIAL').count()
        total_vencidas = Suscripcion.objects.filter(estado='VENCIDA').count()
        
        # Pagos del mes
        pagos_mes = HistorialPago.objects.filter(
            fecha__gte=inicio_mes,
            fecha__lt=fin_mes,
            estado='COMPLETADO'
        )
        
        ingresos_totales = sum(pago.monto for pago in pagos_mes)
        total_pagos = pagos_mes.count()
        
        # Crear reporte
        reporte = f"""
        REPORTE MENSUAL DE SUSCRIPCIONES
        Período: {inicio_mes.strftime('%d/%m/%Y')} - {fin_mes.strftime('%d/%m/%Y')}
        
        SUSCRIPCIONES:
        - Activas: {total_activas}
        - En Trial: {total_trial}
        - Vencidas: {total_vencidas}
        - Total: {total_activas + total_trial + total_vencidas}
        
        PAGOS:
        - Total de pagos: {total_pagos}
        - Ingresos totales: ${ingresos_totales:.2f}
        - Promedio por pago: ${ingresos_totales/total_pagos if total_pagos > 0 else 0:.2f}
        """
        
        logger.info(reporte)
        
        # Enviar reporte por email a administradores
        if hasattr(settings, 'ADMIN_EMAIL'):
            send_mail(
                'Reporte Mensual de Suscripciones',
                reporte,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=True
            )
        
        return reporte
        
    except Exception as e:
        logger.error(f"Error en generar_reporte_mensual_suscripciones: {e}")
        return str(e)
    finally:
        connection.set_schema(original_schema)


@shared_task
def verificar_pagos_pendientes_stripe():
    """
    Verifica el estado de pagos pendientes en Stripe
    """
    from ventasweb.models import HistorialPago
    import stripe
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    original_schema = connection.schema_name
    try:
        connection.set_schema(get_public_schema_name())
        
        # Buscar pagos pendientes de más de 1 hora
        hace_una_hora = timezone.now() - timedelta(hours=1)
        
        pagos_pendientes = HistorialPago.objects.filter(
            estado='PENDIENTE',
            fecha__lt=hace_una_hora,
            stripe_payment_intent_id__isnull=False
        )
        
        actualizados = 0
        for pago in pagos_pendientes:
            try:
                # Verificar estado en Stripe
                intent = stripe.PaymentIntent.retrieve(pago.stripe_payment_intent_id)
                
                if intent.status == 'succeeded':
                    pago.estado = 'COMPLETADO'
                    pago.save()
                    actualizados += 1
                    logger.info(f"Pago {pago.numero_factura} actualizado a COMPLETADO")
                elif intent.status in ['canceled', 'failed']:
                    pago.estado = 'FALLIDO'
                    pago.save()
                    actualizados += 1
                    logger.info(f"Pago {pago.numero_factura} actualizado a FALLIDO")
                    
            except Exception as e:
                logger.error(f"Error al verificar pago {pago.numero_factura}: {e}")
        
        logger.info(f"Verificados y actualizados {actualizados} pagos pendientes")
        return actualizados
        
    except Exception as e:
        logger.error(f"Error en verificar_pagos_pendientes_stripe: {e}")
        return 0
    finally:
        connection.set_schema(original_schema)


@shared_task
def enviar_recordatorio_pago(suscripcion_id):
    """
    Envía un email de recordatorio de pago próximo
    """
    from ventasweb.models import Suscripcion, CustomUser
    
    original_schema = connection.schema_name
    try:
        connection.set_schema(get_public_schema_name())
        
        suscripcion = Suscripcion.objects.select_related('tenant', 'plan').get(id=suscripcion_id)
        
        # Cambiar al schema del tenant para obtener admins
        connection.set_schema(suscripcion.tenant.schema_name)
        
        # Obtener administradores del tenant
        admins = CustomUser.objects.filter(
            is_staff=True,
            is_active=True,
            email__isnull=False
        ).exclude(email='')
        
        if not admins.exists():
            logger.warning(f"No hay administradores con email para {suscripcion.tenant.nombre}")
            return False
        
        # Preparar email
        dias_restantes = (suscripcion.fecha_proximo_pago - timezone.now()).days
        
        asunto = f'Recordatorio: Tu pago vence en {dias_restantes} días'
        mensaje = f"""
        Hola,
        
        Te recordamos que tu suscripción al plan {suscripcion.plan.nombre} está próxima a vencer.
        
        Detalles:
        - Plan: {suscripcion.plan.nombre}
        - Próximo pago: {suscripcion.fecha_proximo_pago.strftime('%d/%m/%Y')}
        - Monto: ${suscripcion.precio_actual()}
        - Días restantes: {dias_restantes}
        
        Para asegurar la continuidad de tu servicio, asegúrate de que tu método de pago esté actualizado.
        
        Puedes revisar tu suscripción en: {settings.SITE_URL}/suscripcion/
        
        Saludos,
        Equipo de Soporte
        """
        
        # Enviar a todos los admins
        emails_admins = [admin.email for admin in admins]
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            emails_admins,
            fail_silently=False
        )
        
        logger.info(f"Recordatorio de pago enviado a {suscripcion.tenant.nombre}")
        return True
        
    except Exception as e:
        logger.error(f"Error en enviar_recordatorio_pago: {e}")
        return False
    finally:
        connection.set_schema(original_schema)


@shared_task
def enviar_recordatorio_trial(suscripcion_id):
    """
    Envía un email recordando que el período de prueba está por expirar
    """
    from ventasweb.models import Suscripcion, CustomUser
    
    original_schema = connection.schema_name
    try:
        connection.set_schema(get_public_schema_name())
        
        suscripcion = Suscripcion.objects.select_related('tenant', 'plan').get(id=suscripcion_id)
        
        if suscripcion.estado != 'TRIAL':
            return False
        
        # Cambiar al schema del tenant
        connection.set_schema(suscripcion.tenant.schema_name)
        
        # Obtener administradores
        admins = CustomUser.objects.filter(
            is_staff=True,
            is_active=True,
            email__isnull=False
        ).exclude(email='')
        
        if not admins.exists():
            return False
        
        # Calcular días restantes
        dias_restantes = suscripcion.dias_restantes_trial()
        
        asunto = f'Tu período de prueba expira en {dias_restantes} días'
        mensaje = f"""
        Hola,
        
        Tu período de prueba gratuito está próximo a expirar.
        
        Detalles:
        - Plan actual: {suscripcion.plan.nombre}
        - Días restantes: {dias_restantes}
        - Fecha de expiración: {suscripcion.fecha_fin_trial.strftime('%d/%m/%Y')}
        
        Para continuar disfrutando de nuestros servicios sin interrupciones, 
        activa tu suscripción ahora.
        
        Activar suscripción: {settings.SITE_URL}/suscripcion/planes/
        
        ¿Tienes preguntas? Contáctanos en cualquier momento.
        
        Saludos,
        Equipo de Soporte
        """
        
        emails_admins = [admin.email for admin in admins]
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            emails_admins,
            fail_silently=False
        )
        
        logger.info(f"Recordatorio de trial enviado a {suscripcion.tenant.nombre}")
        return True
        
    except Exception as e:
        logger.error(f"Error en enviar_recordatorio_trial: {e}")
        return False
    finally:
        connection.set_schema(original_schema)


@shared_task
def enviar_notificacion_vencimiento(suscripcion_id):
    """
    Envía notificación de que la suscripción ha vencido
    """
    from ventasweb.models import Suscripcion, CustomUser
    
    original_schema = connection.schema_name
    try:
        connection.set_schema(get_public_schema_name())
        
        suscripcion = Suscripcion.objects.select_related('tenant', 'plan').get(id=suscripcion_id)
        
        # Cambiar al schema del tenant
        connection.set_schema(suscripcion.tenant.schema_name)
        
        # Obtener administradores
        admins = CustomUser.objects.filter(
            is_staff=True,
            is_active=True,
            email__isnull=False
        ).exclude(email='')
        
        if not admins.exists():
            return False
        
        asunto = '⚠️ Tu suscripción ha vencido'
        mensaje = f"""
        Hola,
        
        Te informamos que tu suscripción al plan {suscripcion.plan.nombre} ha vencido.
        
        El acceso a tu cuenta ha sido suspendido. Para reactivar tu servicio, 
        por favor actualiza tu método de pago.
        
        Reactivar ahora: {settings.SITE_URL}/suscripcion/
        
        Si tienes problemas o preguntas, no dudes en contactarnos.
        
        Saludos,
        Equipo de Soporte
        """
        
        emails_admins = [admin.email for admin in admins]
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            emails_admins,
            fail_silently=False
        )
        
        logger.info(f"Notificación de vencimiento enviada a {suscripcion.tenant.nombre}")
        return True
        
    except Exception as e:
        logger.error(f"Error en enviar_notificacion_vencimiento: {e}")
        return False
    finally:
        connection.set_schema(original_schema)


@shared_task
def debug_celery():
    """
    Tarea de prueba para verificar que Celery está funcionando
    """
    logger.info("✅ Celery está funcionando correctamente!")
    return "OK"


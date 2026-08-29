"""
Sistema de notificaciones por email para el sistema de billing
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def enviar_email_html(asunto, template_name, context, destinatario_email):
    """
    Envía un email HTML usando una plantilla
    
    Args:
        asunto: Asunto del email
        template_name: Nombre del template HTML (ej: 'emails/limite_facturas.html')
        context: Diccionario con variables para el template
        destinatario_email: Email del destinatario
    
    Returns:
        Boolean indicando si el email se envió exitosamente
    """
    try:
        # Renderizar HTML
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)
        
        # Crear email con HTML
        email = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        print(f"✅ Email enviado a {destinatario_email}: {asunto}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando email a {destinatario_email}: {e}")
        return False


def notificar_limite_facturas(tenant):
    """Notificar cuando se alcanza el límite de facturas"""
    if not tenant.email_contacto:
        print(f"⚠️ Tenant {tenant.nombre} no tiene email de contacto")
        return False
    
    context = {
        'tenant': tenant,
        'plan_actual': tenant.get_plan_display(),
        'limite': tenant.max_facturas_mes,
        'url_upgrade': f"https://{tenant.schema_name}.misventasflash.com/planes/pricing/",
    }
    
    return enviar_email_html(
        asunto=f"⚠️ Límite de facturas alcanzado - {tenant.nombre}",
        template_name='emails/limite_facturas.html',
        context=context,
        destinatario_email=tenant.email_contacto
    )


def notificar_limite_usuarios(tenant):
    """Notificar cuando se alcanza el límite de usuarios"""
    if not tenant.email_contacto:
        return False
    
    context = {
        'tenant': tenant,
        'plan_actual': tenant.get_plan_display(),
        'limite': tenant.max_usuarios,
        'url_upgrade': f"https://{tenant.schema_name}.misventasflash.com/planes/pricing/",
    }
    
    return enviar_email_html(
        asunto=f"⚠️ Límite de usuarios alcanzado - {tenant.nombre}",
        template_name='emails/limite_usuarios.html',
        context=context,
        destinatario_email=tenant.email_contacto
    )


def notificar_uso_alto(tenant, tipo, porcentaje):
    """
    Notificar cuando el uso supera el 80%
    
    Args:
        tenant: Instancia del tenant
        tipo: 'facturas' o 'usuarios'
        porcentaje: Porcentaje de uso (ej: 85.5)
    """
    if not tenant.email_contacto:
        return False
    
    context = {
        'tenant': tenant,
        'tipo': tipo,
        'porcentaje': porcentaje,
        'plan_actual': tenant.get_plan_display(),
        'url_upgrade': f"https://{tenant.schema_name}.misventasflash.com/planes/pricing/",
    }
    
    tipo_texto = "facturas" if tipo == "facturas" else "usuarios"
    
    return enviar_email_html(
        asunto=f"⚠️ Uso alto de {tipo_texto} ({porcentaje:.0f}%) - {tenant.nombre}",
        template_name='emails/uso_alto.html',
        context=context,
        destinatario_email=tenant.email_contacto
    )


def notificar_proximo_vencimiento(tenant, dias_restantes):
    """Notificar cuando está cerca el vencimiento de la suscripción"""
    if not tenant.email_contacto:
        return False
    
    context = {
        'tenant': tenant,
        'dias_restantes': dias_restantes,
        'fecha_vencimiento': tenant.proximo_pago,
        'plan_actual': tenant.get_plan_display(),
        'precio': tenant.precio_mensual,
        'url_renovar': f"https://{tenant.schema_name}.misventasflash.com/planes/mi-plan/",
    }
    
    return enviar_email_html(
        asunto=f"⚠️ Tu suscripción vence en {dias_restantes} días - {tenant.nombre}",
        template_name='emails/proximo_vencimiento.html',
        context=context,
        destinatario_email=tenant.email_contacto
    )


def notificar_pago_exitoso(tenant):
    """Notificar cuando un pago se procesa exitosamente"""
    if not tenant.email_contacto:
        return False
    
    context = {
        'tenant': tenant,
        'plan_actual': tenant.get_plan_display(),
        'precio': tenant.precio_mensual,
        'proximo_pago': tenant.proximo_pago,
        'url_panel': f"https://{tenant.schema_name}.misventasflash.com/planes/mi-plan/",
    }
    
    return enviar_email_html(
        asunto=f"✅ Pago procesado exitosamente - {tenant.nombre}",
        template_name='emails/pago_exitoso.html',
        context=context,
        destinatario_email=tenant.email_contacto
    )


def notificar_pago_fallido(tenant):
    """Notificar cuando un pago falla"""
    if not tenant.email_contacto:
        return False
    
    context = {
        'tenant': tenant,
        'plan_actual': tenant.get_plan_display(),
        'precio': tenant.precio_mensual,
        'url_actualizar_pago': f"https://{tenant.schema_name}.misventasflash.com/planes/mi-plan/",
    }
    
    return enviar_email_html(
        asunto=f"❌ Error en el pago de tu suscripción - {tenant.nombre}",
        template_name='emails/pago_fallido.html',
        context=context,
        destinatario_email=tenant.email_contacto
    )


def notificar_cancelacion(tenant):
    """Notificar cuando se cancela una suscripción"""
    if not tenant.email_contacto:
        return False
    
    context = {
        'tenant': tenant,
        'url_reactivar': f"https://{tenant.schema_name}.misventasflash.com/planes/pricing/",
    }
    
    return enviar_email_html(
        asunto=f"Suscripción cancelada - {tenant.nombre}",
        template_name='emails/cancelacion.html',
        context=context,
        destinatario_email=tenant.email_contacto
    )


def notificar_plan_expirado(tenant):
    """Notificar cuando el plan ha expirado"""
    if not tenant.email_contacto:
        return False
    
    context = {
        'tenant': tenant,
        'url_renovar': f"https://{tenant.schema_name}.misventasflash.com/planes/pricing/",
    }
    
    return enviar_email_html(
        asunto=f"⚠️ Tu plan ha expirado - {tenant.nombre}",
        template_name='emails/plan_expirado.html',
        context=context,
        destinatario_email=tenant.email_contacto
    )


def notificar_upgrade_plan(tenant, plan_anterior, plan_nuevo):
    """Notificar cuando se actualiza el plan"""
    if not tenant.email_contacto:
        return False
    
    context = {
        'tenant': tenant,
        'plan_anterior': plan_anterior,
        'plan_nuevo': plan_nuevo,
        'precio_nuevo': tenant.precio_mensual,
        'url_panel': f"https://{tenant.schema_name}.misventasflash.com/planes/mi-plan/",
    }
    
    return enviar_email_html(
        asunto=f"✅ Plan actualizado exitosamente - {tenant.nombre}",
        template_name='emails/upgrade_plan.html',
        context=context,
        destinatario_email=tenant.email_contacto
    )

"""
Integración de Stripe para procesamiento de pagos
"""
import stripe
import json
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def checkout_plan(request, plan_nombre):
    """Crear sesión de checkout de Stripe"""
    if not hasattr(request, 'tenant') or request.tenant.schema_name == 'public':
        messages.error(request, 'Esta función solo está disponible para tenants.')
        return redirect('plataform')
    
    tenant = request.tenant
    
    # Mapeo de planes a price IDs de Stripe
    PRICE_IDS = {
        'basico': settings.STRIPE_PRICE_IDS.get('basico'),
        'plus': settings.STRIPE_PRICE_IDS.get('plus'),
        'pro': settings.STRIPE_PRICE_IDS.get('pro'),
    }
    
    if plan_nombre not in PRICE_IDS:
        messages.error(request, 'Plan no válido')
        return redirect('planes_pricing')
    
    price_id = PRICE_IDS[plan_nombre]
    
    if not price_id:
        messages.error(request, 'Configuración de Stripe incompleta. Contacta al administrador.')
        return redirect('planes_pricing')
    
    try:
        # Crear sesión de checkout
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.build_absolute_uri('/planes/pago-exitoso/') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri('/planes/pricing/'),
            customer_email=tenant.email_contacto if hasattr(tenant, 'email_contacto') else None,
            metadata={
                'tenant_id': str(tenant.id),
                'tenant_schema': tenant.schema_name,
                'plan': plan_nombre,
            }
        )
        
        return redirect(checkout_session.url)
    
    except Exception as e:
        print(f"ERROR Stripe Checkout: {e}")
        messages.error(request, f'Error al procesar el pago: {str(e)}')
        return redirect('planes_pricing')


@login_required
def pago_exitoso(request):
    """Página de confirmación después de pago exitoso"""
    session_id = request.GET.get('session_id')
    
    context = {
        'session_id': session_id,
    }
    
    return render(request, 'planes/pago_exitoso.html', context)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Webhook de Stripe para procesar eventos de pago
    
    IMPORTANTE: Esta ruta debe estar en CSRF_EXEMPT porque Stripe no puede enviar CSRF token
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Payload inválido
        print(f"WEBHOOK ERROR - Payload inválido: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Firma inválida
        print(f"WEBHOOK ERROR - Firma inválida: {e}")
        return HttpResponse(status=400)
    
    # Manejar el evento
    event_type = event['type']
    data = event['data']['object']
    
    print(f"WEBHOOK RECIBIDO: {event_type}")
    
    if event_type == 'checkout.session.completed':
        # Pago inicial completado
        manejar_pago_completado(data)
    
    elif event_type == 'invoice.payment_succeeded':
        # Renovación automática exitosa
        manejar_renovacion_exitosa(data)
    
    elif event_type == 'invoice.payment_failed':
        # Fallo en el pago
        manejar_pago_fallido(data)
    
    elif event_type == 'customer.subscription.deleted':
        # Suscripción cancelada
        manejar_cancelacion(data)
    
    else:
        print(f"WEBHOOK - Evento no manejado: {event_type}")
    
    return HttpResponse(status=200)


def manejar_pago_completado(session):
    """Procesar pago completado desde checkout"""
    from ventasweb.tenant_models import Client
    from django_tenants.utils import schema_context
    from ventasweb import notifications
    
    try:
        # Extraer metadata
        metadata = session.get('metadata', {})
        tenant_id = metadata.get('tenant_id')
        tenant_schema = metadata.get('tenant_schema')
        plan = metadata.get('plan')
        
        if not tenant_id or not plan:
            print("ERROR - Metadata incompleta en webhook")
            return
        
        # Obtener tenant desde public schema
        with schema_context('public'):
            tenant = Client.objects.get(id=tenant_id)
        
        # Actualizar plan
        tenant.plan = plan
        tenant.configurar_limites_plan()
        tenant.esta_activa = True
        tenant.stripe_customer_id = session.get('customer')
        tenant.stripe_subscription_id = session.get('subscription')
        
        # Calcular próximo pago (30 días)
        tenant.proximo_pago = datetime.now() + timedelta(days=30)
        
        tenant.save()
        
        print(f"✅ PAGO PROCESADO - Tenant {tenant.nombre} actualizado a plan {plan}")
        
        # Enviar email de confirmación
        try:
            notifications.notificar_pago_exitoso(tenant)
        except Exception as e:
            print(f"ERROR enviando email de confirmación: {e}")
        
    except Client.DoesNotExist:
        print(f"ERROR - Tenant {tenant_id} no encontrado")
    except Exception as e:
        print(f"ERROR procesando pago: {e}")


def manejar_renovacion_exitosa(invoice):
    """Procesar renovación automática exitosa"""
    from ventasweb.tenant_models import Client
    from django_tenants.utils import schema_context
    from ventasweb import notifications
    
    try:
        customer_id = invoice.get('customer')
        
        # Buscar tenant por customer_id
        with schema_context('public'):
            tenant = Client.objects.filter(stripe_customer_id=customer_id).first()
        
        if not tenant:
            print(f"ERROR - No se encontró tenant con customer_id {customer_id}")
            return
        
        # Renovar suscripción
        tenant.proximo_pago = datetime.now() + timedelta(days=30)
        tenant.esta_activa = True
        tenant.save()
        
        print(f"✅ RENOVACIÓN - Tenant {tenant.nombre} renovado exitosamente")
        
        # Enviar email de confirmación de renovación
        try:
            notifications.notificar_pago_exitoso(tenant)
        except Exception as e:
            print(f"ERROR enviando email de renovación: {e}")
        
    except Exception as e:
        print(f"ERROR procesando renovación: {e}")


def manejar_pago_fallido(invoice):
    """Procesar fallo en el pago"""
    from ventasweb.tenant_models import Client
    from django_tenants.utils import schema_context
    from ventasweb import notifications
    
    try:
        customer_id = invoice.get('customer')
        
        with schema_context('public'):
            tenant = Client.objects.filter(stripe_customer_id=customer_id).first()
        
        if not tenant:
            print(f"ERROR - No se encontró tenant con customer_id {customer_id}")
            return
        
        # Marcar como inactivo después de X días de gracia
        print(f"⚠️ PAGO FALLIDO - Tenant {tenant.nombre}")
        
        # Enviar email de advertencia
        try:
            notifications.notificar_pago_fallido(tenant)
        except Exception as e:
            print(f"ERROR enviando email de pago fallido: {e}")
        
        # TODO: Implementar lógica de días de gracia antes de desactivar
        
    except Exception as e:
        print(f"ERROR procesando pago fallido: {e}")


def manejar_cancelacion(subscription):
    """Procesar cancelación de suscripción"""
    from ventasweb.tenant_models import Client
    from django_tenants.utils import schema_context
    from ventasweb import notifications
    
    try:
        customer_id = subscription.get('customer')
        
        with schema_context('public'):
            tenant = Client.objects.filter(stripe_customer_id=customer_id).first()
        
        if not tenant:
            print(f"ERROR - No se encontró tenant con customer_id {customer_id}")
            return
        
        # Cambiar a plan gratuito
        tenant.plan = 'gratis'
        tenant.configurar_limites_plan()
        tenant.stripe_subscription_id = None
        tenant.save()
        
        print(f"🚫 CANCELACIÓN - Tenant {tenant.nombre} cambió a plan gratuito")
        
        # Enviar email de cancelación
        try:
            notifications.notificar_cancelacion(tenant)
        except Exception as e:
            print(f"ERROR enviando email de cancelación: {e}")
        
    except Exception as e:
        print(f"ERROR procesando cancelación: {e}")


@login_required
def cancelar_suscripcion(request):
    """Cancelar suscripción actual"""
    if not hasattr(request, 'tenant') or request.tenant.schema_name == 'public':
        return JsonResponse({'error': 'No disponible'}, status=400)
    
    tenant = request.tenant
    
    if not tenant.stripe_subscription_id:
        messages.error(request, 'No tienes una suscripción activa')
        return redirect('mi_plan')
    
    if request.method == 'POST':
        try:
            # Cancelar en Stripe
            stripe.Subscription.delete(tenant.stripe_subscription_id)
            
            # Actualizar tenant
            tenant.plan = 'gratis'
            tenant.configurar_limites_plan()
            tenant.stripe_subscription_id = None
            tenant.save()
            
            messages.success(request, 'Suscripción cancelada. Ahora estás en el plan gratuito.')
            return redirect('mi_plan')
        
        except Exception as e:
            print(f"ERROR cancelando suscripción: {e}")
            messages.error(request, 'Error al cancelar la suscripción')
            return redirect('mi_plan')
    
    return render(request, 'planes/cancelar_suscripcion.html')

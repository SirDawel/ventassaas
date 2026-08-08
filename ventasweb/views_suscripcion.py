# -*- coding: utf-8 -*-
"""
Vistas para gestión de suscripciones
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_tenants.utils import get_tenant_model, get_public_schema_name
from datetime import datetime, timedelta
import stripe
import json

from .models import Plan, Suscripcion, HistorialPago, CustomUser

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def suscripcion_dashboard(request):
    """
    Dashboard de suscripción - muestra el estado actual de la suscripción
    Requiere permisos de administrador
    """
    # Solo Administradores y Directores pueden ver esto
    if not request.user.is_staff or request.user.rol not in ['Administrador', 'Director']:
        messages.error(request, 'No tienes permisos para ver esta página. Solo administradores pueden acceder.')
        return redirect('plataform')
    
    # Obtener el tenant actual
    tenant = connection.tenant
    
    # Asegurar que estamos en schema public para obtener suscripción
    schema_actual = connection.schema_name
    connection.set_schema(get_public_schema_name())
    
    try:
        # Obtener suscripción del tenant con plan precargado
        suscripcion = Suscripcion.objects.select_related('plan', 'tenant').filter(tenant=tenant).first()
        
        # Obtener todos los planes disponibles
        planes = Plan.objects.filter(activo=True).order_by('orden')
        
        # Obtener historial de pagos
        historial_pagos = []
        if suscripcion:
            historial_pagos = HistorialPago.objects.filter(
                suscripcion=suscripcion
            ).order_by('-fecha_pago')[:10]
        
        # Calcular umbrales del 80% para las barras de progreso (MIENTRAS ESTAMOS EN SCHEMA PUBLIC)
        umbral_usuarios = int(suscripcion.plan.max_usuarios * 0.8) if suscripcion else 0
        umbral_estudiantes = int(suscripcion.plan.max_estudiantes * 0.8) if suscripcion else 0
        
        # Volver al schema del tenant
        connection.set_schema(schema_actual)
        
        # Contar usuarios actuales del tenant
        total_usuarios = CustomUser.objects.filter(is_active=True).count()
        total_estudiantes = CustomUser.objects.filter(is_active=True, rol='estudiante').count()
        
        # Volver al schema público para renderizar (para que suscripcion.plan funcione)
        connection.set_schema(get_public_schema_name())
        
        context = {
            'suscripcion': suscripcion,
            'planes': planes,
            'historial_pagos': historial_pagos,
            'total_usuarios': total_usuarios,
            'total_estudiantes': total_estudiantes,
            'umbral_usuarios': umbral_usuarios,
            'umbral_estudiantes': umbral_estudiantes,
        }
        
        return render(request, 'suscripcion/dashboard.html', context)
        
    except Exception as e:
        # Asegurar que volvemos al schema correcto en caso de error
        connection.set_schema(schema_actual)
        messages.error(request, f'Error al cargar suscripción: {str(e)}')
        return redirect('plataform')
    finally:
        # Siempre volver al schema original después de renderizar
        connection.set_schema(schema_actual)


@login_required
def planes_disponibles(request):
    """
    Muestra los planes disponibles para cambiar de suscripción
    """
    # Solo administradores pueden cambiar planes
    if not request.user.is_staff or request.user.rol not in ['Administrador', 'Director']:
        messages.error(request, 'No tienes permisos para ver esta página. Solo administradores pueden acceder.')
        return redirect('plataform')
    
    # Obtener el tenant actual
    tenant = connection.tenant
    schema_actual = connection.schema_name
    
    # Cambiar a schema public
    connection.set_schema(get_public_schema_name())
    
    try:
        # Obtener suscripción actual
        suscripcion_actual = Suscripcion.objects.filter(tenant=tenant).first()
        
        # Obtener todos los planes
        planes = Plan.objects.filter(activo=True).order_by('orden')
        
        # Volver al schema del tenant
        connection.set_schema(schema_actual)
        
        # Contar usuarios actuales
        total_usuarios = CustomUser.objects.filter(is_active=True).count()
        
        context = {
            'suscripcion_actual': suscripcion_actual,
            'planes': planes,
            'total_usuarios': total_usuarios,
        }
        
        return render(request, 'suscripcion/planes.html', context)
        
    except Exception as e:
        connection.set_schema(schema_actual)
        messages.error(request, f'Error al cargar planes: {str(e)}')
        return redirect('suscripcion_dashboard')


@login_required
def cambiar_plan(request, plan_id):
    """
    Cambia el plan de suscripción actual
    """
    # Solo administradores pueden cambiar planes
    if not request.user.is_staff or request.user.rol not in ['Administrador', 'Director']:
        messages.error(request, 'No tienes permisos para realizar esta acción. Solo administradores pueden acceder.')
        return redirect('plataform')
    
    if request.method != 'POST':
        return redirect('planes_disponibles')
    
    tenant = connection.tenant
    schema_actual = connection.schema_name
    
    # Cambiar a schema public
    connection.set_schema(get_public_schema_name())
    
    try:
        # Obtener plan seleccionado
        plan = get_object_or_404(Plan, id=plan_id, activo=True)
        
        # Obtener o crear suscripción
        suscripcion, created = Suscripcion.objects.get_or_create(
            tenant=tenant,
            defaults={
                'plan': plan,
                'estado': 'TRIAL',
                'periodo': 'MENSUAL',
                'fecha_fin_trial': datetime.now().date() + timedelta(days=30),
                'fecha_proximo_pago': datetime.now().date() + timedelta(days=30),
            }
        )
        
        if not created:
            # Actualizar plan existente
            suscripcion.plan = plan
            suscripcion.save()
            messages.success(request, f'Plan actualizado a {plan.nombre}')
        else:
            messages.success(request, f'Suscripción creada con plan {plan.nombre}')
        
        # Volver al schema del tenant
        connection.set_schema(schema_actual)
        
        return redirect('suscripcion_dashboard')
        
    except Exception as e:
        connection.set_schema(schema_actual)
        messages.error(request, f'Error al cambiar plan: {str(e)}')
        return redirect('planes_disponibles')


@login_required
def estado_suscripcion_api(request):
    """
    API endpoint que retorna el estado de la suscripción en formato JSON
    Útil para verificaciones en tiempo real
    """
    tenant = connection.tenant
    schema_actual = connection.schema_name
    
    connection.set_schema(get_public_schema_name())
    
    try:
        suscripcion = Suscripcion.objects.filter(tenant=tenant).first()
        
        connection.set_schema(schema_actual)
        
        if not suscripcion:
            return JsonResponse({
                'existe': False,
                'mensaje': 'No hay suscripción activa'
            })
        
        data = {
            'existe': True,
            'plan': suscripcion.plan.nombre,
            'estado': suscripcion.get_estado_display(),
            'estado_code': suscripcion.estado,
            'activa': suscripcion.esta_activa(),
            'periodo': suscripcion.get_periodo_display(),
            'fecha_proximo_pago': suscripcion.fecha_proximo_pago.strftime('%d/%m/%Y') if suscripcion.fecha_proximo_pago else None,
            'usuarios_disponibles': suscripcion.usuarios_disponibles(),
            'max_usuarios': suscripcion.plan.max_usuarios,
        }
        
        # Si está en trial, agregar días restantes
        if suscripcion.estado == 'TRIAL':
            dias_restantes = suscripcion.dias_restantes_trial()
            data['trial'] = {
                'dias_restantes': dias_restantes,
                'fecha_fin': suscripcion.fecha_fin_trial.strftime('%d/%m/%Y') if suscripcion.fecha_fin_trial else None
            }
        
        return JsonResponse(data)
        
    except Exception as e:
        connection.set_schema(schema_actual)
        return JsonResponse({
            'error': True,
            'mensaje': str(e)
        }, status=500)


@login_required
def checkout_suscripcion(request, plan_id):
    """
    Página de checkout para procesar el pago de una suscripción
    """
    # Solo administradores pueden procesar pagos
    if not request.user.is_staff or request.user.rol not in ['Administrador', 'Director']:
        messages.error(request, 'No tienes permisos para realizar esta acción. Solo administradores pueden acceder.')
        return redirect('plataform')
    
    tenant = connection.tenant
    schema_actual = connection.schema_name
    
    # Cambiar a schema public
    connection.set_schema(get_public_schema_name())
    
    try:
        # Obtener plan seleccionado
        plan = get_object_or_404(Plan, id=plan_id, activo=True)
        
        # Obtener o crear suscripción
        suscripcion, created = Suscripcion.objects.get_or_create(
            tenant=tenant,
            defaults={
                'plan': plan,
                'estado': 'TRIAL',
                'periodo': 'MENSUAL',
                'fecha_fin_trial': datetime.now().date() + timedelta(days=30),
                'fecha_proximo_pago': datetime.now().date() + timedelta(days=30),
            }
        )
        
        if not created and suscripcion.plan != plan:
            # Si ya existe, actualizar al nuevo plan
            suscripcion.plan = plan
            suscripcion.save()
        
        # Obtener período de facturación del request
        periodo = request.GET.get('periodo', 'MENSUAL')
        monto = plan.precio_por_periodo(periodo)
        
        # Volver al schema del tenant
        connection.set_schema(schema_actual)
        
        context = {
            'plan': plan,
            'suscripcion': suscripcion,
            'periodo': periodo,
            'monto': monto,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        }
        
        return render(request, 'suscripcion/checkout.html', context)
        
    except Exception as e:
        connection.set_schema(schema_actual)
        messages.error(request, f'Error al preparar checkout: {str(e)}')
        return redirect('planes_disponibles')


@login_required
@require_POST
def crear_checkout_session(request):
    """
    Crea una sesión de Stripe Checkout y retorna el ID
    """
    if not request.user.is_staff or request.user.rol not in ['Administrador', 'Director']:
        return JsonResponse({'error': 'No autorizado. Solo administradores pueden acceder.'}, status=403)
    
    tenant = connection.tenant
    schema_actual = connection.schema_name
    
    try:
        # Obtener datos del request
        plan_id = request.POST.get('plan_id')
        periodo = request.POST.get('periodo', 'MENSUAL')
        
        # Cambiar a schema public
        connection.set_schema(get_public_schema_name())
        
        # Obtener plan
        plan = get_object_or_404(Plan, id=plan_id, activo=True)
        
        # Obtener o crear suscripción
        suscripcion, created = Suscripcion.objects.get_or_create(
            tenant=tenant,
            defaults={
                'plan': plan,
                'estado': 'TRIAL',
                'periodo': periodo,
            }
        )
        
        # Calcular monto
        monto = plan.precio_por_periodo(periodo)
        
        # Crear o obtener customer de Stripe
        if not suscripcion.stripe_customer_id:
            customer = stripe.Customer.create(
                email=request.user.email,
                name=tenant.nombre,
                metadata={
                    'tenant_id': tenant.id,
                    'tenant_schema': tenant.schema_name,
                }
            )
            suscripcion.stripe_customer_id = customer.id
            suscripcion.save()
        
        # Crear sesión de checkout
        checkout_session = stripe.checkout.Session.create(
            customer=suscripcion.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': settings.STRIPE_CURRENCY,
                    'unit_amount': int(monto * 100),  # Stripe usa centavos
                    'product_data': {
                        'name': f'{plan.nombre} - {periodo.title()}',
                        'description': plan.descripcion,
                    },
                    'recurring': {
                        'interval': 'month' if periodo == 'MENSUAL' else 'year',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=settings.STRIPE_SUCCESS_URL + f'?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=settings.STRIPE_CANCEL_URL,
            metadata={
                'suscripcion_id': suscripcion.id,
                'tenant_id': tenant.id,
                'plan_id': plan.id,
                'periodo': periodo,
            }
        )
        
        # Volver al schema del tenant
        connection.set_schema(schema_actual)
        
        return JsonResponse({
            'sessionId': checkout_session.id,
            'publicKey': settings.STRIPE_PUBLIC_KEY,
        })
        
    except Exception as e:
        connection.set_schema(schema_actual)
        return JsonResponse({
            'error': str(e)
        }, status=500)


@login_required
def pago_exitoso(request):
    """
    Página de confirmación después de un pago exitoso
    """
    session_id = request.GET.get('session_id')
    
    if not session_id:
        messages.warning(request, 'No se pudo verificar el pago.')
        return redirect('suscripcion_dashboard')
    
    tenant = connection.tenant
    schema_actual = connection.schema_name
    
    try:
        # Obtener información de la sesión de Stripe
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Cambiar a schema public
        connection.set_schema(get_public_schema_name())
        
        # Obtener suscripción
        suscripcion_id = checkout_session.metadata.get('suscripcion_id')
        if suscripcion_id:
            suscripcion = Suscripcion.objects.filter(id=suscripcion_id, tenant=tenant).first()
            
            if suscripcion and checkout_session.payment_status == 'paid':
                # Actualizar estado de suscripción
                suscripcion.estado = 'ACTIVA'
                suscripcion.stripe_subscription_id = checkout_session.subscription
                suscripcion.fecha_proximo_pago = datetime.now().date() + timedelta(days=30)
                suscripcion.save()
                
                messages.success(request, '¡Pago procesado exitosamente! Tu suscripción está activa.')
        
        # Volver al schema del tenant
        connection.set_schema(schema_actual)
        
        return render(request, 'suscripcion/pago_exitoso.html', {
            'checkout_session': checkout_session,
        })
        
    except Exception as e:
        connection.set_schema(schema_actual)
        messages.error(request, f'Error al verificar el pago: {str(e)}')
        return redirect('suscripcion_dashboard')


@login_required
@require_POST
def procesar_pago_tarjeta(request):
    """
    Procesa el pago con tarjeta usando Stripe Payment Intent
    """
    if not request.user.is_staff or request.user.rol not in ['Administrador', 'Director']:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    tenant = connection.tenant
    schema_actual = connection.schema_name
    
    try:
        # Leer datos del request
        data = json.loads(request.body)
        payment_method_id = data.get('payment_method_id')
        plan_id = data.get('plan_id')
        periodo = data.get('periodo', 'MENSUAL')
        save_card = data.get('save_card', False)
        email = data.get('email')
        
        if not payment_method_id or not plan_id:
            return JsonResponse({'error': 'Faltan parámetros requeridos'}, status=400)
        
        # Cambiar a schema public
        connection.set_schema(get_public_schema_name())
        
        # Obtener plan
        plan = get_object_or_404(Plan, id=plan_id, activo=True)
        
        # Calcular monto
        monto = plan.precio_mensual if periodo == 'MENSUAL' else plan.precio_anual
        
        # Obtener o crear suscripción
        suscripcion, created = Suscripcion.objects.get_or_create(
            tenant=tenant,
            defaults={
                'plan': plan,
                'estado': 'TRIAL',
                'periodo': periodo
            }
        )
        
        # Crear o recuperar Customer en Stripe
        if not suscripcion.stripe_customer_id:
            customer = stripe.Customer.create(
                email=email,
                name=tenant.nombre,
                metadata={
                    'tenant_id': tenant.id,
                    'tenant_schema': tenant.schema_name
                }
            )
            suscripcion.stripe_customer_id = customer.id
            suscripcion.save()
        else:
            customer = stripe.Customer.retrieve(suscripcion.stripe_customer_id)
        
        # Adjuntar Payment Method al Customer si se desea guardar
        if save_card:
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer.id
            )
            
            # Establecer como método de pago predeterminado
            stripe.Customer.modify(
                customer.id,
                invoice_settings={'default_payment_method': payment_method_id}
            )
            
            # Guardar información de la tarjeta
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            suscripcion.metodo_pago_tipo = payment_method.card.brand.upper()
            suscripcion.metodo_pago_ultimo4 = payment_method.card.last4
            suscripcion.save()
        
        # Crear PaymentIntent
        payment_intent = stripe.PaymentIntent.create(
            amount=int(float(monto) * 100),  # Convertir a centavos
            currency='usd',
            customer=customer.id,
            payment_method=payment_method_id,
            confirm=True,
            metadata={
                'plan_id': plan.id,
                'plan_nombre': plan.nombre,
                'periodo': periodo,
                'tenant_id': tenant.id,
                'tenant_schema': tenant.schema_name,
                'suscripcion_id': suscripcion.id
            },
            return_url=request.build_absolute_uri('/suscripcion/pago-exitoso/')
        )
        
        # Registrar pago en historial
        HistorialPago.objects.create(
            suscripcion=suscripcion,
            monto=monto,
            estado='PENDIENTE' if payment_intent.status == 'requires_action' else 'EXITOSO',
            stripe_payment_intent_id=payment_intent.id,
            metodo_pago=suscripcion.metodo_pago_tipo if save_card else 'CARD'
        )
        
        # Volver al schema original
        connection.set_schema(schema_actual)
        
        # Verificar si requiere autenticación 3D Secure
        if payment_intent.status == 'requires_action':
            return JsonResponse({
                'requires_action': True,
                'payment_intent_client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id
            })
        
        # Pago exitoso
        if payment_intent.status == 'succeeded':
            # Actualizar suscripción
            connection.set_schema(get_public_schema_name())
            suscripcion.estado = 'ACTIVA'
            suscripcion.plan = plan
            suscripcion.periodo = periodo
            suscripcion.fecha_proximo_pago = datetime.now().date() + timedelta(days=30 if periodo == 'MENSUAL' else 365)
            suscripcion.save()
            connection.set_schema(schema_actual)
            
            return JsonResponse({
                'success': True,
                'session_id': payment_intent.id
            })
        
        return JsonResponse({'error': 'Estado de pago inesperado'}, status=400)
        
    except stripe.error.CardError as e:
        connection.set_schema(schema_actual)
        return JsonResponse({'error': f'Error de tarjeta: {e.user_message}'}, status=400)
    except Exception as e:
        connection.set_schema(schema_actual)
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def confirmar_pago_tarjeta(request):
    """
    Confirma el pago después de autenticación 3D Secure
    """
    if not request.user.is_staff or request.user.rol not in ['Administrador', 'Director']:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    tenant = connection.tenant
    schema_actual = connection.schema_name
    
    try:
        data = json.loads(request.body)
        payment_intent_id = data.get('payment_intent_id')
        
        if not payment_intent_id:
            return JsonResponse({'error': 'Falta payment_intent_id'}, status=400)
        
        # Recuperar PaymentIntent
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if payment_intent.status == 'succeeded':
            # Cambiar a schema public
            connection.set_schema(get_public_schema_name())
            
            # Actualizar historial de pago
            historial = HistorialPago.objects.filter(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            
            if historial:
                historial.estado = 'EXITOSO'
                historial.save()
                
                # Actualizar suscripción
                suscripcion = historial.suscripcion
                suscripcion.estado = 'ACTIVA'
                suscripcion.fecha_proximo_pago = datetime.now().date() + timedelta(
                    days=30 if suscripcion.periodo == 'MENSUAL' else 365
                )
                suscripcion.save()
            
            connection.set_schema(schema_actual)
            
            return JsonResponse({
                'success': True,
                'session_id': payment_intent.id
            })
        
        return JsonResponse({'error': 'Pago no completado'}, status=400)
        
    except Exception as e:
        connection.set_schema(schema_actual)
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Webhook para recibir eventos de Stripe
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Manejar diferentes tipos de eventos
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session_completed(session)
    
    elif event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        handle_invoice_paid(invoice)
    
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_invoice_payment_failed(invoice)
    
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)
    
    return JsonResponse({'status': 'success'})


def handle_checkout_session_completed(session):
    """
    Maneja el evento de sesión de checkout completada
    """
    try:
        suscripcion_id = session['metadata'].get('suscripcion_id')
        if suscripcion_id:
            suscripcion = Suscripcion.objects.filter(id=suscripcion_id).first()
            if suscripcion:
                suscripcion.estado = 'ACTIVA'
                suscripcion.stripe_subscription_id = session.get('subscription')
                suscripcion.stripe_customer_id = session.get('customer')
                suscripcion.save()
                
                # Registrar pago
                HistorialPago.objects.create(
                    suscripcion=suscripcion,
                    monto=session['amount_total'] / 100,  # Convertir de centavos
                    moneda=session['currency'].upper(),
                    estado='COMPLETADO',
                    stripe_payment_intent_id=session.get('payment_intent'),
                    descripcion=f'Pago de suscripción {suscripcion.plan.nombre}',
                    metodo_pago='TARJETA',
                    fecha_pago=datetime.now(),
                    fecha_procesado=datetime.now(),
                )
    except Exception as e:
        print(f"Error en handle_checkout_session_completed: {e}")


def handle_invoice_paid(invoice):
    """
    Maneja el evento de factura pagada
    """
    try:
        customer_id = invoice.get('customer')
        suscripcion = Suscripcion.objects.filter(stripe_customer_id=customer_id).first()
        
        if suscripcion:
            # Actualizar estado
            suscripcion.estado = 'ACTIVA'
            
            # Calcular próxima fecha de pago
            if suscripcion.periodo == 'MENSUAL':
                suscripcion.fecha_proximo_pago = datetime.now().date() + timedelta(days=30)
            else:
                suscripcion.fecha_proximo_pago = datetime.now().date() + timedelta(days=365)
            
            suscripcion.save()
            
            # Registrar pago
            HistorialPago.objects.create(
                suscripcion=suscripcion,
                monto=invoice['amount_paid'] / 100,
                moneda=invoice['currency'].upper(),
                estado='COMPLETADO',
                stripe_payment_intent_id=invoice.get('payment_intent'),
                stripe_invoice_id=invoice.get('id'),
                stripe_charge_id=invoice.get('charge'),
                descripcion=f'Renovación de suscripción {suscripcion.plan.nombre}',
                metodo_pago='TARJETA',
                fecha_pago=datetime.fromtimestamp(invoice['status_transitions']['paid_at']),
                fecha_procesado=datetime.now(),
                factura_url=invoice.get('hosted_invoice_url'),
            )
    except Exception as e:
        print(f"Error en handle_invoice_paid: {e}")


def handle_invoice_payment_failed(invoice):
    """
    Maneja el evento de fallo en el pago de factura
    """
    try:
        customer_id = invoice.get('customer')
        suscripcion = Suscripcion.objects.filter(stripe_customer_id=customer_id).first()
        
        if suscripcion:
            # Actualizar estado a vencida
            suscripcion.estado = 'VENCIDA'
            suscripcion.save()
            
            # Registrar intento de pago fallido
            HistorialPago.objects.create(
                suscripcion=suscripcion,
                monto=invoice['amount_due'] / 100,
                moneda=invoice['currency'].upper(),
                estado='FALLIDO',
                stripe_invoice_id=invoice.get('id'),
                descripcion=f'Pago fallido - {suscripcion.plan.nombre}',
                metodo_pago='TARJETA',
                fecha_pago=datetime.now(),
                fecha_procesado=datetime.now(),
            )
            
            # TODO: Enviar email al administrador notificando el fallo
    except Exception as e:
        print(f"Error en handle_invoice_payment_failed: {e}")


def handle_subscription_updated(subscription):
    """
    Maneja el evento de actualización de suscripción
    """
    try:
        customer_id = subscription.get('customer')
        suscripcion = Suscripcion.objects.filter(stripe_customer_id=customer_id).first()
        
        if suscripcion:
            # Actualizar información
            suscripcion.stripe_subscription_id = subscription.get('id')
            
            # Actualizar estado según el estado en Stripe
            stripe_status = subscription.get('status')
            if stripe_status == 'active':
                suscripcion.estado = 'ACTIVA'
            elif stripe_status in ['canceled', 'unpaid']:
                suscripcion.estado = 'CANCELADA'
            elif stripe_status == 'past_due':
                suscripcion.estado = 'VENCIDA'
            
            suscripcion.save()
    except Exception as e:
        print(f"Error en handle_subscription_updated: {e}")


def handle_subscription_deleted(subscription):
    """
    Maneja el evento de cancelación de suscripción
    """
    try:
        customer_id = subscription.get('customer')
        suscripcion = Suscripcion.objects.filter(stripe_customer_id=customer_id).first()
        
        if suscripcion:
            suscripcion.estado = 'CANCELADA'
            suscripcion.fecha_cancelacion = datetime.now()
            suscripcion.save()
            
            # TODO: Enviar email de confirmación de cancelación
    except Exception as e:
        print(f"Error en handle_subscription_deleted: {e}")

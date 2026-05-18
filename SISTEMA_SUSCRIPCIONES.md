# 💳 Sistema de Suscripciones - Arquitectura

## 📋 Descripción General

Sistema de facturación SaaS para cobro mensual basado en cantidad de usuarios por escuela (tenant).

---

## 🏗️ Componentes Principales

### 1. **Modelos de Base de Datos**

```python
# escuelaweb/models.py (agregar estos modelos)

class Plan(models.Model):
    """Planes de suscripción disponibles"""
    PLAN_TYPES = [
        ('BASICO', 'Básico - Hasta 50 usuarios'),
        ('ESTANDAR', 'Estándar - Hasta 200 usuarios'),
        ('PROFESIONAL', 'Profesional - Hasta 500 usuarios'),
        ('EMPRESARIAL', 'Empresarial - Sin límite'),
    ]
    
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    precio_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    precio_anual = models.DecimalField(max_digits=10, decimal_places=2)
    max_usuarios = models.IntegerField(help_text="0 = ilimitado")
    max_estudiantes = models.IntegerField(default=0, help_text="0 = ilimitado")
    
    # Características incluidas
    permite_reportes_avanzados = models.BooleanField(default=False)
    permite_integracion_api = models.BooleanField(default=False)
    permite_multiples_sedes = models.BooleanField(default=False)
    soporte_prioritario = models.BooleanField(default=False)
    
    activo = models.BooleanField(default=True)
    orden = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['orden', 'precio_mensual']
        verbose_name = 'Plan de Suscripción'
        verbose_name_plural = 'Planes de Suscripción'
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio_mensual}/mes"


class Suscripcion(models.Model):
    """Suscripción de cada escuela (tenant) a un plan"""
    ESTADO_CHOICES = [
        ('TRIAL', 'Periodo de Prueba'),
        ('ACTIVA', 'Activa'),
        ('VENCIDA', 'Vencida'),
        ('CANCELADA', 'Cancelada'),
        ('SUSPENDIDA', 'Suspendida'),
    ]
    
    PERIODO_CHOICES = [
        ('MENSUAL', 'Mensual'),
        ('ANUAL', 'Anual'),
    ]
    
    # Relación con el tenant
    tenant = models.OneToOneField(
        'Client',
        on_delete=models.CASCADE,
        related_name='suscripcion'
    )
    
    # Plan actual
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='suscripciones'
    )
    
    # Estado y periodo
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='TRIAL')
    periodo = models.CharField(max_length=20, choices=PERIODO_CHOICES, default='MENSUAL')
    
    # Fechas importantes
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin_trial = models.DateTimeField(null=True, blank=True)
    fecha_proximo_pago = models.DateTimeField(null=True, blank=True)
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)
    
    # Información de pago
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    metodo_pago_ultimo4 = models.CharField(max_length=4, blank=True)
    
    # Control
    auto_renovacion = models.BooleanField(default=True)
    notificacion_enviada = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
    
    def __str__(self):
        return f"{self.tenant.nombre} - {self.plan.nombre} ({self.estado})"
    
    def esta_activa(self):
        """Verifica si la suscripción permite acceso"""
        return self.estado in ['TRIAL', 'ACTIVA']
    
    def dias_restantes_trial(self):
        """Calcula días restantes de prueba"""
        if self.estado != 'TRIAL' or not self.fecha_fin_trial:
            return 0
        delta = self.fecha_fin_trial - timezone.now()
        return max(0, delta.days)
    
    def puede_agregar_usuario(self):
        """Verifica si puede agregar más usuarios según el plan"""
        if self.plan.max_usuarios == 0:  # ilimitado
            return True
        usuarios_actuales = self.tenant.contar_usuarios()
        return usuarios_actuales < self.plan.max_usuarios
    
    def usuarios_disponibles(self):
        """Cantidad de usuarios que puede agregar aún"""
        if self.plan.max_usuarios == 0:
            return "Ilimitado"
        usuarios_actuales = self.tenant.contar_usuarios()
        return max(0, self.plan.max_usuarios - usuarios_actuales)


class HistorialPago(models.Model):
    """Registro de todos los pagos realizados"""
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('COMPLETADO', 'Completado'),
        ('FALLIDO', 'Fallido'),
        ('REEMBOLSADO', 'Reembolsado'),
    ]
    
    suscripcion = models.ForeignKey(
        Suscripcion,
        on_delete=models.CASCADE,
        related_name='historial_pagos'
    )
    
    # Información del pago
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, default='USD')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    
    # IDs de pasarela
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True)
    stripe_invoice_id = models.CharField(max_length=100, blank=True)
    
    # Detalles
    descripcion = models.TextField(blank=True)
    metodo_pago = models.CharField(max_length=50, blank=True)
    
    # Fechas
    fecha_pago = models.DateTimeField(null=True, blank=True)
    fecha_procesado = models.DateTimeField(auto_now_add=True)
    
    # Facturación
    numero_factura = models.CharField(max_length=50, unique=True, blank=True)
    factura_url = models.URLField(blank=True)
    
    class Meta:
        ordering = ['-fecha_procesado']
        verbose_name = 'Historial de Pago'
        verbose_name_plural = 'Historial de Pagos'
    
    def __str__(self):
        return f"{self.suscripcion.tenant.nombre} - ${self.monto} ({self.estado})"
```

---

## 🔧 Implementación

### 2. **Middleware de Verificación de Suscripción**

```python
# escuelaweb/subscription_middleware.py

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django_tenants.utils import get_tenant_model

class SubscriptionMiddleware:
    """Verifica que el tenant tenga suscripción activa"""
    
    RUTAS_EXENTAS = [
        '/login/',
        '/logout/',
        '/suscripcion/',
        '/pagar/',
        '/webhook/stripe/',
        '/admin/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Solo verificar en subdominios de tenant
        if hasattr(request, 'tenant') and request.tenant.schema_name != 'public':
            
            # Verificar si la ruta está exenta
            ruta_exenta = any(request.path.startswith(ruta) for ruta in self.RUTAS_EXENTAS)
            
            if not ruta_exenta:
                # Verificar suscripción
                if not hasattr(request.tenant, 'suscripcion'):
                    messages.warning(request, '⚠️ Esta escuela no tiene una suscripción configurada.')
                    return redirect('configurar_suscripcion')
                
                suscripcion = request.tenant.suscripcion
                
                # Si está en trial y le quedan días, permitir acceso
                if suscripcion.estado == 'TRIAL':
                    dias_restantes = suscripcion.dias_restantes_trial()
                    if dias_restantes > 0:
                        if dias_restantes <= 5:
                            messages.warning(
                                request,
                                f'⏰ Tu periodo de prueba termina en {dias_restantes} días. '
                                f'<a href="{reverse("suscripcion_pagar")}">Activa tu suscripción</a>',
                                extra_tags='safe'
                            )
                    else:
                        # Trial expirado
                        messages.error(request, '❌ Tu periodo de prueba ha expirado.')
                        return redirect('suscripcion_pagar')
                
                # Si está vencida o suspendida, bloquear
                elif suscripcion.estado in ['VENCIDA', 'SUSPENDIDA']:
                    messages.error(
                        request,
                        f'❌ Tu suscripción está {suscripcion.estado.lower()}. '
                        f'Por favor actualiza tu método de pago.'
                    )
                    return redirect('suscripcion_pagar')
                
                # Si está cancelada
                elif suscripcion.estado == 'CANCELADA':
                    messages.error(request, '❌ Tu suscripción ha sido cancelada.')
                    return redirect('suscripcion_pagar')
        
        response = self.get_response(request)
        return response
```

### 3. **Vistas de Suscripción**

```python
# escuelaweb/views_suscripcion.py

import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Plan, Suscripcion, HistorialPago

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def suscripcion_dashboard(request):
    """Panel de gestión de suscripción"""
    tenant = request.tenant
    
    try:
        suscripcion = tenant.suscripcion
    except Suscripcion.DoesNotExist:
        # Crear suscripción en trial automáticamente
        plan_basico = Plan.objects.get(tipo='BASICO')
        suscripcion = Suscripcion.objects.create(
            tenant=tenant,
            plan=plan_basico,
            estado='TRIAL',
            fecha_fin_trial=timezone.now() + timedelta(days=30)
        )
    
    planes = Plan.objects.filter(activo=True)
    historial = suscripcion.historial_pagos.all()[:10]
    
    context = {
        'suscripcion': suscripcion,
        'planes': planes,
        'historial': historial,
        'usuarios_actuales': tenant.contar_usuarios(),
    }
    
    return render(request, 'suscripcion/dashboard.html', context)


@login_required
def cambiar_plan(request, plan_id):
    """Cambiar a otro plan"""
    if request.method != 'POST':
        return redirect('suscripcion_dashboard')
    
    tenant = request.tenant
    nuevo_plan = Plan.objects.get(id=plan_id)
    suscripcion = tenant.suscripcion
    
    # Verificar límites del nuevo plan
    usuarios_actuales = tenant.contar_usuarios()
    if nuevo_plan.max_usuarios > 0 and usuarios_actuales > nuevo_plan.max_usuarios:
        messages.error(
            request,
            f'❌ No puedes cambiar a este plan. Tienes {usuarios_actuales} usuarios '
            f'y el plan permite máximo {nuevo_plan.max_usuarios}.'
        )
        return redirect('suscripcion_dashboard')
    
    # Si tiene Stripe configurado, actualizar suscripción
    if suscripcion.stripe_subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(suscripcion.stripe_subscription_id)
            stripe.Subscription.modify(
                suscripcion.stripe_subscription_id,
                items=[{
                    'id': subscription['items']['data'][0].id,
                    'price': nuevo_plan.stripe_price_id,  # Necesitas configurar esto
                }]
            )
            messages.success(request, f'✅ Plan actualizado a {nuevo_plan.nombre}')
        except Exception as e:
            messages.error(request, f'❌ Error al actualizar plan: {str(e)}')
            return redirect('suscripcion_dashboard')
    
    # Actualizar plan
    suscripcion.plan = nuevo_plan
    suscripcion.save()
    
    messages.success(request, f'✅ Plan actualizado exitosamente a {nuevo_plan.nombre}')
    return redirect('suscripcion_dashboard')


@login_required
def checkout_pago(request):
    """Página de pago con Stripe"""
    tenant = request.tenant
    suscripcion = tenant.suscripcion
    
    if request.method == 'POST':
        try:
            # Crear o recuperar customer en Stripe
            if not suscripcion.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=request.user.email,
                    name=tenant.nombre,
                    metadata={'tenant_id': tenant.id}
                )
                suscripcion.stripe_customer_id = customer.id
                suscripcion.save()
            
            # Crear sesión de checkout
            precio = suscripcion.plan.precio_mensual if suscripcion.periodo == 'MENSUAL' else suscripcion.plan.precio_anual
            
            checkout_session = stripe.checkout.Session.create(
                customer=suscripcion.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'Plan {suscripcion.plan.nombre}',
                            'description': f'Suscripción {suscripcion.periodo.lower()}',
                        },
                        'unit_amount': int(precio * 100),
                        'recurring': {
                            'interval': 'month' if suscripcion.periodo == 'MENSUAL' else 'year',
                        },
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=request.build_absolute_uri(reverse('suscripcion_exito')),
                cancel_url=request.build_absolute_uri(reverse('suscripcion_dashboard')),
            )
            
            return redirect(checkout_session.url)
            
        except Exception as e:
            messages.error(request, f'❌ Error al procesar pago: {str(e)}')
            return redirect('suscripcion_dashboard')
    
    context = {
        'suscripcion': suscripcion,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    
    return render(request, 'suscripcion/checkout.html', context)


@login_required
def pago_exitoso(request):
    """Confirmación de pago exitoso"""
    tenant = request.tenant
    suscripcion = tenant.suscripcion
    
    # Activar suscripción
    suscripcion.estado = 'ACTIVA'
    suscripcion.fecha_proximo_pago = timezone.now() + timedelta(days=30)
    suscripcion.save()
    
    messages.success(request, '🎉 ¡Pago procesado exitosamente! Tu suscripción está activa.')
    return redirect('suscripcion_dashboard')
```

---

## 🔔 Webhooks de Stripe

```python
# escuelaweb/views_webhook.py

import stripe
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Suscripcion, HistorialPago
from django.utils import timezone

@csrf_exempt
def stripe_webhook(request):
    """Recibir eventos de Stripe"""
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    # Manejar eventos
    if event['type'] == 'invoice.payment_succeeded':
        handle_payment_success(event['data']['object'])
    
    elif event['type'] == 'invoice.payment_failed':
        handle_payment_failed(event['data']['object'])
    
    elif event['type'] == 'customer.subscription.deleted':
        handle_subscription_cancelled(event['data']['object'])
    
    return HttpResponse(status=200)


def handle_payment_success(invoice):
    """Pago exitoso"""
    customer_id = invoice['customer']
    
    try:
        suscripcion = Suscripcion.objects.get(stripe_customer_id=customer_id)
        suscripcion.estado = 'ACTIVA'
        suscripcion.fecha_proximo_pago = timezone.now() + timedelta(days=30)
        suscripcion.save()
        
        # Registrar pago
        HistorialPago.objects.create(
            suscripcion=suscripcion,
            monto=invoice['amount_paid'] / 100,
            moneda=invoice['currency'].upper(),
            estado='COMPLETADO',
            stripe_invoice_id=invoice['id'],
            fecha_pago=timezone.now(),
            descripcion=f'Pago mensual - {suscripcion.plan.nombre}'
        )
    except Suscripcion.DoesNotExist:
        pass


def handle_payment_failed(invoice):
    """Pago fallido"""
    customer_id = invoice['customer']
    
    try:
        suscripcion = Suscripcion.objects.get(stripe_customer_id=customer_id)
        suscripcion.estado = 'VENCIDA'
        suscripcion.save()
        
        # Registrar intento fallido
        HistorialPago.objects.create(
            suscripcion=suscripcion,
            monto=invoice['amount_due'] / 100,
            moneda=invoice['currency'].upper(),
            estado='FALLIDO',
            stripe_invoice_id=invoice['id'],
            descripcion='Pago fallido - tarjeta declinada'
        )
        
        # TODO: Enviar email notificando
    except Suscripcion.DoesNotExist:
        pass
```

---

## 📧 Notificaciones Automáticas

Usar **Celery** para tareas programadas:

```python
# escuelaweb/tasks.py

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Suscripcion
from django.core.mail import send_mail

@shared_task
def verificar_suscripciones_proximas_vencer():
    """Notificar suscripciones que vencen en 3 días"""
    fecha_limite = timezone.now() + timedelta(days=3)
    
    suscripciones = Suscripcion.objects.filter(
        estado='ACTIVA',
        fecha_proximo_pago__lte=fecha_limite,
        notificacion_enviada=False
    )
    
    for suscripcion in suscripciones:
        send_mail(
            subject=f'⏰ Tu suscripción vence pronto',
            message=f'Hola {suscripcion.tenant.nombre},\n\n'
                    f'Tu suscripción vence el {suscripcion.fecha_proximo_pago.strftime("%d/%m/%Y")}.\n'
                    f'Asegúrate de tener tu método de pago actualizado.',
            from_email='noreply@tuescuela.com',
            recipient_list=[suscripcion.tenant.email_contacto],
        )
        
        suscripcion.notificacion_enviada = True
        suscripcion.save()
```

---

## 🎨 Templates Necesarios

1. **`suscripcion/dashboard.html`** - Panel de gestión
2. **`suscripcion/planes.html`** - Selección de planes
3. **`suscripcion/checkout.html`** - Página de pago
4. **`suscripcion/exito.html`** - Confirmación

---

## ⚙️ Configuración de Settings

```python
# settings.py

# Stripe
STRIPE_PUBLIC_KEY = env('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET')

# Middleware
MIDDLEWARE = [
    # ... otros middlewares ...
    'escuelaweb.subscription_middleware.SubscriptionMiddleware',
]
```

---

## 📝 Pasos de Implementación

### **Fase 1: Base (Semana 1)**
1. ✅ Crear modelos Plan, Suscripcion, HistorialPago
2. ✅ Ejecutar migraciones
3. ✅ Crear planes iniciales en admin
4. ✅ Asignar suscripción trial a tenants existentes

### **Fase 2: Interfaz (Semana 2)**
5. ✅ Crear templates de suscripción
6. ✅ Implementar vistas de gestión
7. ✅ Agregar middleware de verificación

### **Fase 3: Pagos (Semana 3)**
8. ✅ Integrar Stripe/MercadoPago
9. ✅ Implementar checkout
10. ✅ Configurar webhooks

### **Fase 4: Automatización (Semana 4)**
11. ✅ Configurar Celery para tareas programadas
12. ✅ Implementar notificaciones por email
13. ✅ Testing completo

---

## 💰 Estimación de Costos

- **Stripe**: 2.9% + $0.30 por transacción
- **MercadoPago**: ~3.5% + comisión fija

Para $79/mes → Comisión ~$2.50

---

## 🔒 Seguridad

- ✅ Nunca almacenar números de tarjeta completos
- ✅ Usar tokens de Stripe para pagos
- ✅ Validar webhooks con firma
- ✅ HTTPS obligatorio en producción
- ✅ Logs de todos los eventos de pago

---

¿Quieres que implemente alguna parte específica ahora?

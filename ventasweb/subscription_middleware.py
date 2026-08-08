# -*- coding: utf-8 -*-
"""
Middleware para verificación de estado de suscripción
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.db import connection
from django_tenants.utils import get_public_schema_name
from .models import Suscripcion


class SubscriptionMiddleware:
    """
    Middleware que verifica el estado de la suscripción del tenant
    y redirige si está vencida o inactiva
    """
    
    # Rutas que siempre deben estar accesibles, incluso sin suscripción válida
    RUTAS_EXCLUIDAS = [
        '/logout/',
        '/suscripcion/',
        '/webhooks/',
        '/static/',
        '/media/',
        '/admin/',
        '/api/',
        '/password-reset/',
        '/activate/',
        '/activate-school/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Si estamos en el schema public, no verificar suscripción
        if connection.schema_name == get_public_schema_name() or connection.schema_name == 'public':
            return self.get_response(request)
        
        # Verificar si la ruta está excluida
        path = request.path
        if any(path.startswith(ruta) for ruta in self.RUTAS_EXCLUIDAS):
            return self.get_response(request)
        
        # Verificar estado de suscripción solo para usuarios autenticados
        if request.user.is_authenticated:
            # Solo verificar para usuarios staff (administradores)
            # Los usuarios normales pueden seguir usando el sistema
            if request.user.is_staff:
                tenant = connection.tenant
                schema_actual = connection.schema_name
                
                try:
                    # Cambiar a schema public para verificar suscripción
                    connection.set_schema(get_public_schema_name())
                    
                    # Obtener suscripción del tenant
                    suscripcion = Suscripcion.objects.filter(tenant=tenant).first()
                    
                    # Volver al schema del tenant
                    connection.set_schema(schema_actual)
                    
                    # Si no hay suscripción, redirigir a planes
                    if not suscripcion:
                        # Si no está ya en la página de suscripción, redirigir
                        if not path.startswith('/suscripcion/'):
                            messages.warning(
                                request, 
                                'No tienes una suscripción activa. Por favor, selecciona un plan.'
                            )
                            return redirect('planes_disponibles')
                    
                    # Si la suscripción está vencida y no se está accediendo a suscripciones
                    elif suscripcion.estado == 'VENCIDA' and not path.startswith('/suscripcion/'):
                        messages.error(
                            request,
                            'Tu suscripción ha expirado. Por favor, actualiza tu método de pago para continuar.'
                        )
                        return redirect('suscripcion_dashboard')
                    
                    # Si la suscripción está suspendida
                    elif suscripcion.estado == 'SUSPENDIDA' and not path.startswith('/suscripcion/'):
                        messages.error(
                            request,
                            'Tu suscripción está suspendida. Por favor, contacta con soporte.'
                        )
                        return redirect('suscripcion_dashboard')
                    
                    # Si está en trial y quedan pocos días, mostrar advertencia
                    elif suscripcion.estado == 'TRIAL':
                        dias_restantes = suscripcion.dias_restantes_trial()
                        if dias_restantes is not None and dias_restantes <= 7 and dias_restantes > 0:
                            # Solo mostrar una vez por sesión
                            if not request.session.get('trial_warning_shown', False):
                                messages.warning(
                                    request,
                                    f'Tu período de prueba expira en {dias_restantes} días. '
                                    'Configura un método de pago para continuar sin interrupciones.'
                                )
                                request.session['trial_warning_shown'] = True
                        elif dias_restantes is not None and dias_restantes <= 0:
                            if not path.startswith('/suscripcion/'):
                                messages.error(
                                    request,
                                    'Tu período de prueba ha expirado. Por favor, configura un método de pago.'
                                )
                                return redirect('suscripcion_dashboard')
                    
                    # Verificar límite de usuarios (advertencia, no bloqueo)
                    if not suscripcion.puede_agregar_usuario():
                        if path.startswith('/users/create/') or path.startswith('/register/'):
                            messages.warning(
                                request,
                                f'Has alcanzado el límite de usuarios de tu plan ({suscripcion.plan.max_usuarios}). '
                                'Considera actualizar a un plan superior.'
                            )
                
                except Exception as e:
                    # En caso de error, volver al schema correcto y continuar
                    connection.set_schema(schema_actual)
                    # Log del error pero no bloquear el acceso
                    print(f"Error en SubscriptionMiddleware: {e}")
        
        response = self.get_response(request)
        return response


class SubscriptionUsageMiddleware:
    """
    Middleware para registrar el uso del sistema (opcional)
    Puede ser usado para analytics y métricas
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Aquí se pueden registrar métricas de uso
        # Por ahora solo pasamos la request
        response = self.get_response(request)
        return response

"""
Middlewares personalizados para la aplicación escuelaweb
"""

import os
from django.utils.deprecation import MiddlewareMixin


class RoleBasedSessionMiddleware(MiddlewareMixin):
    """
    Middleware que ajusta el tiempo de expiración de sesión según el rol del usuario.
    
    Ideal para sistemas educativos donde diferentes roles requieren diferentes
    niveles de seguridad y conveniencia:
    - Administradores: sesiones cortas (alta seguridad)
    - Docentes: sesiones medias (balance)
    - Estudiantes: sesiones largas (conveniencia)
    """
    
    # Tiempos predeterminados por rol (en segundos)
    DEFAULT_TIMEOUTS = {
        'Administrador': 3600,      # 1 hora
        'Director': 3600,           # 1 hora
        'Secretaria': 7200,         # 2 horas
        'Coordinador': 7200,        # 2 horas
        'Profesor': 10800,          # 3 horas
        'Psicologo': 10800,         # 3 horas
        'Bibliotecario': 10800,     # 3 horas
        'Estudiante': 14400,        # 4 horas
        'Otro': 7200,               # 2 horas (default)
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Cargar timeouts desde variables de entorno o usar defaults
        self.timeouts = self._load_timeouts_from_env()
    
    def _load_timeouts_from_env(self):
        """Carga los timeouts desde variables de entorno si están definidos"""
        timeouts = {}
        for rol, default_timeout in self.DEFAULT_TIMEOUTS.items():
            env_key = f'SESSION_TIMEOUT_{rol.upper()}'
            timeouts[rol] = int(os.getenv(env_key, default_timeout))
        return timeouts
    
    def __call__(self, request):
        # Procesar el request antes de la vista
        if request.user.is_authenticated and hasattr(request.user, 'rol'):
            rol = request.user.rol
            timeout = self.timeouts.get(rol, self.DEFAULT_TIMEOUTS.get('Otro', 7200))
            
            # Establecer el timeout de sesión para este usuario
            request.session.set_expiry(timeout)
        
        response = self.get_response(request)
        return response


# ==============================================================================
# Middlewares para Sistema de Planes y Billing
# ==============================================================================

from django.http import JsonResponse
from django.shortcuts import render
from django.urls import resolve
from ventasweb import notifications


class PlanLimitsMiddleware:
    """
    Middleware que verifica los límites del plan antes de permitir acciones
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs que crean facturas (agregar más según tu app)
        self.factura_urls = [
            'ventasweb:crear_factura',
            'ventasweb:registrar_venta',
            'ventasweb:pos_crear_venta',
        ]
        
        # URLs que crean usuarios
        self.usuario_urls = [
            'ventasweb:crear_usuario',
            'ventasweb:registro_usuario',
        ]
    
    def __call__(self, request):
        # Obtener tenant actual
        if hasattr(request, 'tenant') and request.tenant and not request.tenant.schema_name == 'public':
            tenant = request.tenant
            
            # Verificar si el tenant está activo
            if not tenant.esta_activa():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': 'Suscripción expirada',
                        'message': 'Tu plan ha expirado. Por favor renueva tu suscripción.',
                        'plan': tenant.plan,
                        'fecha_vencimiento': tenant.fecha_vencimiento.isoformat() if tenant.fecha_vencimiento else None
                    }, status=403)
                
                return render(request, 'errors/plan_expirado.html', {
                    'tenant': tenant,
                    'plan': tenant.get_info_plan()
                }, status=403)
            
            # Obtener la URL actual
            try:
                url_name = resolve(request.path_info).url_name
                
                # Verificar límite de facturas
                if url_name in self.factura_urls and request.method == 'POST':
                    if not tenant.puede_crear_factura():
                        # Enviar notificación por email
                        try:
                            notifications.notificar_limite_facturas(tenant)
                        except Exception as e:
                            print(f"ERROR enviando notificación de límite de facturas: {e}")
                        
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'error': 'Límite alcanzado',
                                'message': f'Has alcanzado el límite de {tenant.max_facturas_mes} facturas para tu plan {tenant.get_plan_display()}.',
                                'facturas_usadas': tenant.contar_facturas_mes(),
                                'facturas_max': tenant.max_facturas_mes,
                                'sugerencia': 'Actualiza tu plan para crear más facturas.'
                            }, status=403)
                        
                        return render(request, 'errors/limite_facturas.html', {
                            'tenant': tenant,
                            'plan': tenant.get_info_plan()
                        }, status=403)
                
                # Verificar límite de usuarios
                if url_name in self.usuario_urls and request.method == 'POST':
                    if not tenant.puede_agregar_usuarios():
                        # Enviar notificación por email
                        try:
                            notifications.notificar_limite_usuarios(tenant)
                        except Exception as e:
                            print(f"ERROR enviando notificación de límite de usuarios: {e}")
                        
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'error': 'Límite alcanzado',
                                'message': f'Has alcanzado el límite de {tenant.max_usuarios} usuarios para tu plan {tenant.get_plan_display()}.',
                                'usuarios_actuales': tenant.contar_usuarios(),
                                'usuarios_max': tenant.max_usuarios,
                                'sugerencia': 'Actualiza tu plan para agregar más usuarios.'
                            }, status=403)
                        
                        return render(request, 'errors/limite_usuarios.html', {
                            'tenant': tenant,
                            'plan': tenant.get_info_plan()
                        }, status=403)
                        
            except Exception:
                pass  # Si no se puede resolver la URL, continuar normalmente
        
        response = self.get_response(request)
        return response


class BillingWarningMiddleware:
    """
    Middleware que muestra alertas cuando se acerca a límites del plan
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Solo para requests HTML (no AJAX ni API)
        if hasattr(request, 'tenant') and request.tenant and not request.tenant.schema_name == 'public':
            if 'text/html' in response.get('Content-Type', ''):
                tenant = request.tenant
                
                # Verificar alertas
                alertas = []
                
                # Alerta de usuarios
                porcentaje_usuarios = tenant.get_porcentaje_uso_usuarios()
                if porcentaje_usuarios >= 80:
                    alertas.append({
                        'tipo': 'warning' if porcentaje_usuarios < 100 else 'danger',
                        'mensaje': f'Estás usando {tenant.contar_usuarios()} de {tenant.max_usuarios} usuarios disponibles.'
                    })
                
                # Alerta de facturas
                porcentaje_facturas = tenant.get_porcentaje_uso_facturas()
                if porcentaje_facturas >= 80 and tenant.max_facturas_mes < 99999:
                    alertas.append({
                        'tipo': 'warning' if porcentaje_facturas < 100 else 'danger',
                        'mensaje': f'Has usado {tenant.contar_facturas_mes()} de {tenant.max_facturas_mes} facturas este mes.'
                    })
                
                # Alerta de vencimiento
                if tenant.fecha_vencimiento:
                    from django.utils import timezone
                    from datetime import timedelta
                    
                    dias_restantes = (tenant.fecha_vencimiento - timezone.now()).days
                    if 0 < dias_restantes <= 7:
                        alertas.append({
                            'tipo': 'danger',
                            'mensaje': f'Tu plan vence en {dias_restantes} días. Renueva para no perder acceso.'
                        })
                
                # Agregar alertas al contexto de la respuesta
                if alertas and hasattr(request, '_messages'):
                    from django.contrib import messages
                    for alerta in alertas:
                        nivel = messages.WARNING if alerta['tipo'] == 'warning' else messages.ERROR
                        messages.add_message(request, nivel, alerta['mensaje'])
        
        return response

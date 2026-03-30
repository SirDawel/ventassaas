"""
Middleware de seguridad para el sistema
"""
from django.core.cache import cache
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Middleware para limitar la tasa de solicitudes y prevenir ataques de fuerza bruta
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Configuración de rate limiting
        self.rate_limits = {
            'login': {
                'requests': 5,  # Máximo 5 intentos
                'window': 60,  # En 1 minutos
            },
            'api': {
                'requests': 100,  # Máximo 100 requests
                'window': 60,  # En 1 minuto
            },
            'general': {
                'requests': 500,  # Máximo 500 requests
                'window': 60,  # En 1 minutos
            }
        }
    
    def __call__(self, request):
        # Determinar el tipo de endpoint
        endpoint_type = 'general'
        if '/login/' in request.path or '/api/auth/' in request.path:
            endpoint_type = 'login'
        elif '/api/' in request.path:
            endpoint_type = 'api'
        
        # Obtener IP del cliente
        ip_address = self.get_client_ip(request)
        
        # Verificar rate limit
        if not self.check_rate_limit(ip_address, endpoint_type, request.path):
            logger.warning(f"Rate limit exceeded for IP {ip_address} on {request.path}")
            
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Demasiadas solicitudes. Por favor, intenta más tarde.',
                    'detail': 'Rate limit exceeded'
                }, status=429)
            else:
                return HttpResponseForbidden(
                    '<h1>429 Too Many Requests</h1>'
                    '<p>Has excedido el límite de solicitudes. '
                    'Por favor, espera unos minutos antes de intentar nuevamente.</p>'
                )
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Obtiene la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def check_rate_limit(self, ip_address, endpoint_type, path):
        """
        Verifica si la IP ha excedido el límite de solicitudes
        """
        config = self.rate_limits.get(endpoint_type, self.rate_limits['general'])
        cache_key = f'rate_limit:{endpoint_type}:{ip_address}'
        
        # Obtener contador actual
        request_count = cache.get(cache_key, 0)
        
        # Verificar límite
        if request_count >= config['requests']:
            return False
        
        # Incrementar contador
        cache.set(cache_key, request_count + 1, config['window'])
        return True


class SessionSecurityMiddleware:
    """
    Middleware para gestionar seguridad de sesiones
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.session_timeout = 14400  # 4 horas en segundos
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Verificar si la sesión ha expirado por inactividad
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                from datetime import datetime
                last_activity_time = datetime.fromisoformat(last_activity)
                now = timezone.now()
                
                # Si han pasado más de X horas sin actividad, cerrar sesión
                if (now - last_activity_time).total_seconds() > self.session_timeout:
                    from .models import SecurityLog
                    SecurityLog.log_event(
                        tipo_evento='SESSION_EXPIRED',
                        descripcion='Sesión expirada por inactividad',
                        usuario=request.user,
                        ip_address=self.get_client_ip(request),
                        nivel_severidad='INFO'
                    )
                    logout(request)
                    messages.warning(request, 'Tu sesión ha expirado por inactividad.')
                    return redirect('login')
            
            # Actualizar última actividad
            request.session['last_activity'] = timezone.now().isoformat()
            
            # Rastrear sesión activa
            self.track_session(request)
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Obtiene la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def track_session(self, request):
        """Rastrea la sesión activa del usuario"""
        try:
            from .models import UserSession
            session_key = request.session.session_key
            
            if not session_key:
                return
            
            # Crear o actualizar sesión
            session, created = UserSession.objects.get_or_create(
                session_key=session_key,
                defaults={
                    'usuario': request.user,
                    'ip_address': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                    'activa': True
                }
            )
            
            if not created:
                # Actualizar última actividad
                session.fecha_ultima_actividad = timezone.now()
                session.save()
        except Exception as e:
            logger.error(f"Error tracking session: {e}")


class SecurityAuditMiddleware:
    """
    Middleware para auditoría de acciones de seguridad
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs críticas que requieren auditoría
        self.critical_paths = [
            '/admin/',
            '/api/',
            '/usuarios/',
            '/exportar/',
            '/eliminar/',
            '/facturas/anular/',
            '/contabilidad/asientos/anular/',
        ]
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Auditar acciones en URLs críticas
        if request.user.is_authenticated:
            for critical_path in self.critical_paths:
                if request.path.startswith(critical_path):
                    self.log_critical_action(request, response)
                    break
        
        return response
    
    def log_critical_action(self, request, response):
        """Registra acciones en URLs críticas"""
        try:
            from .models import SecurityLog
            
            # Solo registrar si la respuesta es exitosa
            if 200 <= response.status_code < 400:
                SecurityLog.log_event(
                    tipo_evento='ADMIN_ACTION' if request.path.startswith('/admin/') else 'DATA_EXPORT',
                    descripcion=f"{request.method} {request.path}",
                    usuario=request.user,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    nivel_severidad='INFO',
                    metadata={
                        'method': request.method,
                        'path': request.path,
                        'status_code': response.status_code
                    }
                )
        except Exception as e:
            logger.error(f"Error logging critical action: {e}")
    
    def get_client_ip(self, request):
        """Obtiene la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LoginSecurityMiddleware:
    """
    Middleware específico para seguridad de login
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.max_failed_attempts = 5
        self.block_duration = 900  # 15 minutos
    
    def __call__(self, request):
        # Verificar bloqueos antes de permitir acceso al login
        if request.path == '/login/' and request.method == 'POST':
            email = request.POST.get('email', '').strip()
            
            if email:
                from .models import LoginAttempt
                
                # Verificar si la cuenta está bloqueada
                if LoginAttempt.is_blocked(email, self.max_failed_attempts, self.block_duration // 60):
                    logger.warning(f"Intento de login en cuenta bloqueada: {email}")
                    
                    from django.contrib import messages
                    messages.error(
                        request, 
                        f'Cuenta temporalmente bloqueada por múltiples intentos fallidos. '
                        f'Intenta nuevamente en {self.block_duration // 60} minutos.'
                    )
                    return redirect('login')
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Obtiene la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

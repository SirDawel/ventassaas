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
                'window': 60,  # En 1 minuto
                'block_minutes': 30,  # Bloquear IP por 30 minutos si excede
            },
            'api': {
                'requests': 100,  # Máximo 100 requests
                'window': 60,  # En 1 minuto
                'block_minutes': 15,
            },
            'general': {
                'requests': 500,  # Máximo 500 requests
                'window': 60,  # En 1 minuto
                'block_minutes': 10,
            }
        }
    
    def __call__(self, request):
        # Obtener IP del cliente
        ip_address = self.get_client_ip(request)
        
        # Verificar si la IP está en la blacklist (bloqueo persistente)
        if self.is_ip_blocked_in_db(ip_address):
            logger.warning(f"Blocked IP attempt: {ip_address} on {request.path}")
            return self.blocked_response(request)
        
        # Determinar el tipo de endpoint
        endpoint_type = 'general'
        if '/login/' in request.path or '/api/auth/' in request.path:
            endpoint_type = 'login'
        elif '/api/' in request.path:
            endpoint_type = 'api'
        
        # Verificar rate limit
        if not self.check_rate_limit(ip_address, endpoint_type, request.path):
            logger.warning(f"Rate limit exceeded for IP {ip_address} on {request.path}")
            
            # Bloquear IP temporalmente si excede rate limit
            self.auto_block_ip(ip_address, endpoint_type)
            
            # Crear alerta de seguridad
            self.create_security_alert(ip_address, endpoint_type, request)
            
            return self.rate_limit_response(request, endpoint_type)
        
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
    
    def is_ip_blocked_in_db(self, ip_address):
        """Verifica si la IP está bloqueada en la base de datos"""
        try:
            from .models import IPBlocklist
            return IPBlocklist.is_blocked(ip_address)
        except Exception as e:
            logger.error(f"Error checking IP blocklist: {str(e)}")
            return False
    
    def auto_block_ip(self, ip_address, endpoint_type):
        """Bloquea automáticamente una IP por exceder rate limit"""
        try:
            from .models import IPBlocklist
            
            config = self.rate_limits.get(endpoint_type, self.rate_limits['general'])
            minutos_bloqueo = config.get('block_minutes', 15)
            
            razon = f"Bloqueo automático por exceder rate limit en endpoint '{endpoint_type}'"
            
            IPBlocklist.block_ip(
                ip_address=ip_address,
                tipo_bloqueo='AUTO_RATE_LIMIT',
                razon=razon,
                es_temporal=True,
                minutos_bloqueo=minutos_bloqueo
            )
            
            logger.warning(f"Auto-blocked IP {ip_address} for {minutos_bloqueo} minutes")
            
        except Exception as e:
            logger.error(f"Error auto-blocking IP: {str(e)}")
    
    def create_security_alert(self, ip_address, endpoint_type, request):
        """Crea una alerta de seguridad por rate limit excedido"""
        try:
            from .models import SecurityAlert
            
            titulo = f"Rate Limit Excedido - {endpoint_type.upper()}"
            descripcion = f"""
Se ha detectado un exceso de solicitudes desde la IP {ip_address}.

Tipo de endpoint: {endpoint_type}
Path: {request.path}
User Agent: {request.META.get('HTTP_USER_AGENT', 'Desconocido')[:200]}
Método: {request.method}
            """
            
            SecurityAlert.create_alert(
                tipo_alerta='BRUTE_FORCE' if endpoint_type == 'login' else 'SUSPICIOUS_IP',
                titulo=titulo,
                descripcion=descripcion.strip(),
                nivel_prioridad='HIGH' if endpoint_type == 'login' else 'MEDIUM',
                ip_address=ip_address,
                metadata={
                    'endpoint_type': endpoint_type,
                    'path': request.path,
                    'method': request.method
                }
            )
            
        except Exception as e:
            logger.error(f"Error creating security alert: {str(e)}")
    
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
    
    def blocked_response(self, request):
        """Respuesta para IPs bloqueadas"""
        if request.path.startswith('/api/'):
            return JsonResponse({
                'error': 'Acceso denegado',
                'detail': 'Tu IP ha sido bloqueada por actividad sospechosa.'
            }, status=403)
        else:
            return HttpResponseForbidden(
                '<h1>403 Forbidden</h1>'
                '<p>Tu IP ha sido bloqueada por actividad sospechosa.</p>'
                '<p>Si crees que esto es un error, contacta al administrador.</p>'
            )
    
    def rate_limit_response(self, request, endpoint_type):
        """Respuesta para rate limit excedido"""
        config = self.rate_limits.get(endpoint_type, self.rate_limits['general'])
        minutos = config.get('block_minutes', 15)
        
        if request.path.startswith('/api/'):
            return JsonResponse({
                'error': 'Demasiadas solicitudes',
                'detail': f'Has excedido el límite de solicitudes. Tu IP ha sido bloqueada temporalmente por {minutos} minutos.'
            }, status=429)
        else:
            return HttpResponseForbidden(
                f'<h1>429 Too Many Requests</h1>'
                f'<p>Has excedido el límite de solicitudes.</p>'
                f'<p>Tu IP ha sido bloqueada temporalmente por {minutos} minutos.</p>'
                f'<p>Por favor, espera antes de intentar nuevamente.</p>'
            )


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

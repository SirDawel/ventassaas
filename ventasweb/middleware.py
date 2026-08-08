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

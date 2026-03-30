"""
Utilidades de seguridad y autenticación
"""
import jwt
import secrets
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone


class JWTTokenManager:
    """
    Gestor de tokens JWT para autenticación de APIs
    """
    
    @staticmethod
    def generate_access_token(user, expires_in=3600):
        """
        Genera un token de acceso JWT
        
        Args:
            user: Usuario para el cual generar el token
            expires_in: Tiempo de expiración en segundos (default: 1 hora)
        
        Returns:
            str: Token JWT
        """
        payload = {
            'user_id': user.id,
            'email': user.email,
            'rol': user.rol,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm='HS256'
        )
        
        return token
    
    @staticmethod
    def generate_refresh_token(user, expires_in=604800):
        """
        Genera un token de refresco JWT
        
        Args:
            user: Usuario para el cual generar el token
            expires_in: Tiempo de expiración en segundos (default: 7 días)
        
        Returns:
            str: Token de refresco
        """
        payload = {
            'user_id': user.id,
            'email': user.email,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow(),
            'type': 'refresh',
            'jti': secrets.token_urlsafe(32)  # Token ID único
        }
        
        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm='HS256'
        )
        
        return token
    
    @staticmethod
    def verify_token(token):
        """
        Verifica y decodifica un token JWT
        
        Args:
            token: Token JWT a verificar
        
        Returns:
            dict: Payload decodificado si es válido, None si no es válido
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None  # Token expirado
        except jwt.InvalidTokenError:
            return None  # Token inválido
    
    @staticmethod
    def get_user_from_token(token):
        """
        Obtiene el usuario desde un token JWT
        
        Args:
            token: Token JWT
        
        Returns:
            CustomUser: Usuario si el token es válido, None si no
        """
        payload = JWTTokenManager.verify_token(token)
        
        if not payload:
            return None
        
        try:
            from escuelaweb.models import CustomUser
            user = CustomUser.objects.get(id=payload['user_id'])
            return user
        except CustomUser.DoesNotExist:
            return None


class APIKeyManager:
    """
    Gestor de API Keys para autenticación de servicios externos
    """
    
    @staticmethod
    def generate_api_key():
        """
        Genera una API key única
        
        Returns:
            str: API key en formato 'sk_live_' o 'sk_test_' + token random
        """
        prefix = 'sk_live_' if not settings.DEBUG else 'sk_test_'
        key = secrets.token_urlsafe(32)
        return f"{prefix}{key}"
    
    @staticmethod
    def hash_api_key(api_key):
        """
        Hashea una API key para almacenamiento seguro
        
        Args:
            api_key: API key a hashear
        
        Returns:
            str: Hash de la API key
        """
        from django.contrib.auth.hashers import make_password
        return make_password(api_key)
    
    @staticmethod
    def verify_api_key(api_key, hashed_key):
        """
        Verifica una API key contra su hash
        
        Args:
            api_key: API key en texto plano
            hashed_key: Hash almacenado
        
        Returns:
            bool: True si coincide, False si no
        """
        from django.contrib.auth.hashers import check_password
        return check_password(api_key, hashed_key)


class PasswordSecurityHelper:
    """
    Helper para validaciones y operaciones de seguridad de contraseñas
    """
    
    @staticmethod
    def is_password_strong(password):
        """
        Verifica si una contraseña es fuerte
        
        Args:
            password: Contraseña a verificar
        
        Returns:
            tuple: (bool, list) - (Es fuerte?, lista de errores)
        """
        errors = []
        
        if len(password) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres")
        
        if not any(char.isdigit() for char in password):
            errors.append("La contraseña debe contener al menos un número")
        
        if not any(char.isupper() for char in password):
            errors.append("La contraseña debe contener al menos una mayúscula")
        
        if not any(char.islower() for char in password):
            errors.append("La contraseña debe contener al menos una minúscula")
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(char in special_chars for char in password):
            errors.append("La contraseña debe contener al menos un carácter especial")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def generate_secure_password(length=12):
        """
        Genera una contraseña segura aleatoria
        
        Args:
            length: Longitud de la contraseña (default: 12)
        
        Returns:
            str: Contraseña segura
        """
        import string
        import secrets
        
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Asegurar que cumple con los requisitos
        while not PasswordSecurityHelper.is_password_strong(password)[0]:
            password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        return password
    
    @staticmethod
    def check_password_history(user, new_password, last_n=5):
        """
        Verifica si la contraseña fue usada recientemente
        
        Args:
            user: Usuario
            new_password: Nueva contraseña a verificar
            last_n: Número de contraseñas anteriores a verificar
        
        Returns:
            bool: True si la contraseña ya fue usada, False si es nueva
        """
        # TODO: Implementar historial de contraseñas si es necesario
        # Por ahora retorna False (contraseña no usada)
        return False


class SecurityHelper:
    """
    Helper general de seguridad
    """
    
    @staticmethod
    def sanitize_input(text):
        """
        Sanitiza entrada de usuario para prevenir XSS
        
        Args:
            text: Texto a sanitizar
        
        Returns:
            str: Texto sanitizado
        """
        from django.utils.html import escape
        return escape(text)
    
    @staticmethod
    def is_safe_redirect(url, allowed_hosts=None):
        """
        Verifica si una URL es segura para redirección
        
        Args:
            url: URL a verificar
            allowed_hosts: Lista de hosts permitidos
        
        Returns:
            bool: True si es segura, False si no
        """
        from urllib.parse import urlparse
        
        if not url:
            return False
        
        # URLs relativas son seguras
        if url.startswith('/') and not url.startswith('//'):
            return True
        
        # Verificar host
        parsed = urlparse(url)
        if not parsed.netloc:
            return True  # URL relativa
        
        allowed_hosts = allowed_hosts or settings.ALLOWED_HOSTS
        return parsed.netloc in allowed_hosts
    
    @staticmethod
    def generate_csrf_token():
        """
        Genera un token CSRF manualmente
        
        Returns:
            str: Token CSRF
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def detect_suspicious_activity(request, user):
        """
        Detecta actividad sospechosa
        
        Args:
            request: Request actual
            user: Usuario
        
        Returns:
            tuple: (bool, str) - (Es sospechosa?, razón)
        """
        # Obtener IP actual
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            current_ip = x_forwarded_for.split(',')[0].strip()
        else:
            current_ip = request.META.get('REMOTE_ADDR')
        
        # Verificar cambio de IP en corto tiempo
        from escuelaweb.models import SecurityLog
        recent_logins = SecurityLog.objects.filter(
            usuario=user,
            tipo_evento='LOGIN',
            fecha__gte=timezone.now() - timedelta(minutes=30)
        ).exclude(
            ip_address=current_ip
        ).count()
        
        if recent_logins > 0:
            return True, "Cambio de IP en corto tiempo"
        
        return False, ""

"""
Modelos de seguridad para el sistema
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class LoginAttempt(models.Model):
    """
    Registra intentos de login exitosos y fallidos
    Permite implementar bloqueo de cuenta tras múltiples intentos fallidos
    """
    email = models.EmailField(verbose_name="Email del intento")
    ip_address = models.GenericIPAddressField(verbose_name="Dirección IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent del navegador")
    exitoso = models.BooleanField(default=False, verbose_name="Intento exitoso")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del intento")
    razon_fallo = models.CharField(max_length=255, blank=True, null=True, 
                                   verbose_name="Razón del fallo")
    
    # Usuario asociado (si existe)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='login_attempts'
    )
    
    class Meta:
        verbose_name = "Intento de Login"
        verbose_name_plural = "Intentos de Login"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['email', 'fecha']),
            models.Index(fields=['ip_address', 'fecha']),
            models.Index(fields=['-fecha']),
        ]
    
    def __str__(self):
        status = "Exitoso" if self.exitoso else "Fallido"
        return f"{self.email} - {status} ({self.fecha.strftime('%Y-%m-%d %H:%M:%S')})"
    
    @classmethod
    def get_recent_failed_attempts(cls, email, minutes=15):
        """
        Obtiene intentos fallidos recientes para un email
        """
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        return cls.objects.filter(
            email=email,
            exitoso=False,
            fecha__gte=cutoff_time
        ).count()
    
    @classmethod
    def is_blocked(cls, email, max_attempts=5, block_minutes=15):
        """
        Verifica si una cuenta está bloqueada por demasiados intentos fallidos
        """
        failed_attempts = cls.get_recent_failed_attempts(email, block_minutes)
        return failed_attempts >= max_attempts
    
    @classmethod
    def record_attempt(cls, email, ip_address, user_agent='', exitoso=False, 
                      razon_fallo=None, user=None):
        """
        Registra un intento de login
        """
        return cls.objects.create(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent[:500],  # Limitar longitud
            exitoso=exitoso,
            razon_fallo=razon_fallo,
            user=user
        )


class SecurityLog(models.Model):
    """
    Registro de auditoría de eventos de seguridad importantes
    """
    TIPO_EVENTO_CHOICES = [
        ('LOGIN', 'Login exitoso'),
        ('LOGOUT', 'Logout'),
        ('LOGIN_FAILED', 'Login fallido'),
        ('PASSWORD_CHANGE', 'Cambio de contraseña'),
        ('PASSWORD_RESET', 'Reseteo de contraseña'),
        ('ACCOUNT_LOCKED', 'Cuenta bloqueada'),
        ('ACCOUNT_UNLOCKED', 'Cuenta desbloqueada'),
        ('PERMISSION_DENIED', 'Permiso denegado'),
        ('PROFILE_UPDATE', 'Actualización de perfil'),
        ('SESSION_EXPIRED', 'Sesión expirada'),
        ('2FA_ENABLED', '2FA habilitado'),
        ('2FA_DISABLED', '2FA deshabilitado'),
        ('SUSPICIOUS_ACTIVITY', 'Actividad sospechosa'),
        ('DATA_EXPORT', 'Exportación de datos'),
        ('ADMIN_ACTION', 'Acción administrativa'),
    ]
    
    NIVEL_SEVERIDAD_CHOICES = [
        ('INFO', 'Información'),
        ('WARNING', 'Advertencia'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Crítico'),
    ]
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='security_logs',
        verbose_name="Usuario"
    )
    email = models.EmailField(blank=True, verbose_name="Email")
    tipo_evento = models.CharField(max_length=50, choices=TIPO_EVENTO_CHOICES, 
                                    verbose_name="Tipo de evento")
    nivel_severidad = models.CharField(max_length=20, choices=NIVEL_SEVERIDAD_CHOICES,
                                       default='INFO', verbose_name="Nivel de severidad")
    descripcion = models.TextField(verbose_name="Descripción")
    ip_address = models.GenericIPAddressField(null=True, blank=True, 
                                              verbose_name="Dirección IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    
    # Información adicional en JSON
    metadata = models.JSONField(default=dict, blank=True, 
                               verbose_name="Metadata adicional")
    
    class Meta:
        verbose_name = "Registro de Seguridad"
        verbose_name_plural = "Registros de Seguridad"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['usuario', '-fecha']),
            models.Index(fields=['tipo_evento', '-fecha']),
            models.Index(fields=['nivel_severidad', '-fecha']),
            models.Index(fields=['-fecha']),
        ]
    
    def __str__(self):
        user_str = self.email or (self.usuario.email if self.usuario else 'Desconocido')
        return f"{self.tipo_evento} - {user_str} ({self.fecha.strftime('%Y-%m-%d %H:%M:%S')})"
    
    @classmethod
    def log_event(cls, tipo_evento, descripcion, usuario=None, email='', 
                 ip_address=None, user_agent='', nivel_severidad='INFO', metadata=None):
        """
        Registra un evento de seguridad
        """
        return cls.objects.create(
            usuario=usuario,
            email=email or (usuario.email if usuario else ''),
            tipo_evento=tipo_evento,
            nivel_severidad=nivel_severidad,
            descripcion=descripcion,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else '',
            metadata=metadata or {}
        )


class UserSession(models.Model):
    """
    Rastrea sesiones activas de usuarios para auditoría y control
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_sessions',
        verbose_name="Usuario"
    )
    session_key = models.CharField(max_length=40, unique=True, 
                                   verbose_name="Clave de sesión")
    ip_address = models.GenericIPAddressField(verbose_name="Dirección IP")
    user_agent = models.TextField(verbose_name="User Agent")
    fecha_inicio = models.DateTimeField(auto_now_add=True, 
                                        verbose_name="Fecha de inicio")
    fecha_ultima_actividad = models.DateTimeField(auto_now=True,
                                                   verbose_name="Última actividad")
    activa = models.BooleanField(default=True, verbose_name="Sesión activa")
    fecha_cierre = models.DateTimeField(null=True, blank=True, 
                                        verbose_name="Fecha de cierre")
    
    class Meta:
        verbose_name = "Sesión de Usuario"
        verbose_name_plural = "Sesiones de Usuario"
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['usuario', '-fecha_inicio']),
            models.Index(fields=['session_key']),
            models.Index(fields=['activa', '-fecha_inicio']),
        ]
    
    def __str__(self):
        return f"{self.usuario.email} - {self.ip_address} ({self.fecha_inicio.strftime('%Y-%m-%d %H:%M:%S')})"
    
    def cerrar_sesion(self):
        """Marca la sesión como inactiva"""
        self.activa = False
        self.fecha_cierre = timezone.now()
        self.save()
    
    @classmethod
    def get_active_sessions(cls, usuario):
        """Obtiene sesiones activas de un usuario"""
        return cls.objects.filter(usuario=usuario, activa=True)
    
    @classmethod
    def cleanup_old_sessions(cls, days=30):
        """Limpia sesiones antiguas"""
        cutoff_date = timezone.now() - timedelta(days=days)
        cls.objects.filter(fecha_ultima_actividad__lt=cutoff_date).delete()


class TwoFactorAuth(models.Model):
    """
    Modelo para autenticación de dos factores (2FA)
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='two_factor_auth',
        verbose_name="Usuario"
    )
    habilitado = models.BooleanField(default=False, verbose_name="2FA Habilitado")
    secret_key = models.CharField(max_length=32, blank=True, 
                                  verbose_name="Clave secreta TOTP")
    backup_codes = models.JSONField(default=list, blank=True,
                                   verbose_name="Códigos de respaldo")
    fecha_habilitacion = models.DateTimeField(null=True, blank=True,
                                              verbose_name="Fecha de habilitación")
    ultimo_uso = models.DateTimeField(null=True, blank=True,
                                      verbose_name="Último uso")
    
    class Meta:
        verbose_name = "Autenticación de Dos Factores"
        verbose_name_plural = "Autenticaciones de Dos Factores"
    
    def __str__(self):
        status = "Habilitado" if self.habilitado else "Deshabilitado"
        return f"2FA - {self.usuario.email} ({status})"
    
    def habilitar_2fa(self):
        """Habilita 2FA para el usuario"""
        import pyotp
        import secrets
        
        if not self.secret_key:
            self.secret_key = pyotp.random_base32()
        
        # Generar códigos de respaldo
        self.backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        self.habilitado = True
        self.fecha_habilitacion = timezone.now()
        self.save()
        return self.backup_codes
    
    def deshabilitar_2fa(self):
        """Deshabilita 2FA para el usuario"""
        self.habilitado = False
        self.save()
    
    def verificar_token(self, token):
        """Verifica un token TOTP"""
        if not self.habilitado:
            return False
        
        import pyotp
        totp = pyotp.TOTP(self.secret_key)
        
        # Verificar token TOTP
        if totp.verify(token, valid_window=1):
            self.ultimo_uso = timezone.now()
            self.save()
            return True
        
        # Verificar código de respaldo
        if token.upper() in self.backup_codes:
            self.backup_codes.remove(token.upper())
            self.ultimo_uso = timezone.now()
            self.save()
            return True
        
        return False
    
    def get_qr_code_url(self):
        """Genera URL para código QR de Google Authenticator"""
        import pyotp
        totp = pyotp.TOTP(self.secret_key)
        return totp.provisioning_uri(
            name=self.usuario.email,
            issuer_name='Escuela Online'
        )

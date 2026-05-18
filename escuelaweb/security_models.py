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


class RegistroEscuelaAttempt(models.Model):
    """
    Registra intentos de registro de escuelas para prevenir abuso
    Implementa rate limiting basado en IP
    """
    ip_address = models.GenericIPAddressField(verbose_name="Dirección IP")
    nombre_corto_intentado = models.CharField(max_length=50, verbose_name="Subdominio Intentado", blank=True)
    exitoso = models.BooleanField(default=False, verbose_name="Registro Exitoso")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del Intento")
    razon_fallo = models.CharField(max_length=255, blank=True, null=True, verbose_name="Razón del Fallo")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    
    class Meta:
        verbose_name = "Intento de Registro de Escuela"
        verbose_name_plural = "Intentos de Registro de Escuelas"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['ip_address', 'fecha']),
            models.Index(fields=['-fecha']),
        ]
    
    def __str__(self):
        status = "Exitoso" if self.exitoso else "Fallido"
        return f"{self.ip_address} - {self.nombre_corto_intentado} - {status} ({self.fecha.strftime('%Y-%m-%d %H:%M:%S')})"
    
    @classmethod
    def get_recent_attempts_by_ip(cls, ip_address, hours=1):
        """
        Obtiene intentos de registro de una IP en las últimas N horas
        """
        from django.utils import timezone
        from datetime import timedelta
        cutoff_time = timezone.now() - timedelta(hours=hours)
        return cls.objects.filter(
            ip_address=ip_address,
            fecha__gte=cutoff_time
        ).count()
    
    @classmethod
    def is_ip_blocked(cls, ip_address, max_attempts=3, block_hours=1):
        """
        Verifica si una IP está bloqueada por exceder intentos permitidos
        """
        attempts = cls.get_recent_attempts_by_ip(ip_address, block_hours)
        return attempts >= max_attempts
    
    @classmethod
    def record_attempt(cls, ip_address, nombre_corto='', exitoso=False, razon_fallo=None, user_agent=''):
        """
        Registra un intento de registro de escuela
        """
        return cls.objects.create(
            ip_address=ip_address,
            nombre_corto_intentado=nombre_corto[:50],
            exitoso=exitoso,
            razon_fallo=razon_fallo,
            user_agent=user_agent[:500] if user_agent else ''
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
        ('SCHOOL_REGISTERED', 'Escuela registrada'),
        ('SCHOOL_ACTIVATED', 'Escuela activada'),
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


class IPBlocklist(models.Model):
    """
    Lista de IPs bloqueadas por actividad sospechosa
    """
    TIPO_BLOQUEO_CHOICES = [
        ('MANUAL', 'Bloqueo Manual'),
        ('AUTO_RATE_LIMIT', 'Automático - Rate Limit'),
        ('AUTO_FAILED_LOGIN', 'Automático - Login Fallido'),
        ('AUTO_SUSPICIOUS', 'Automático - Actividad Sospechosa'),
    ]
    
    ip_address = models.GenericIPAddressField(unique=True, db_index=True,
                                              verbose_name="Dirección IP")
    tipo_bloqueo = models.CharField(max_length=30, choices=TIPO_BLOQUEO_CHOICES,
                                    default='MANUAL', verbose_name="Tipo de Bloqueo")
    razon = models.TextField(verbose_name="Razón del Bloqueo")
    fecha_bloqueo = models.DateTimeField(auto_now_add=True, 
                                         verbose_name="Fecha de Bloqueo")
    bloqueado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ips_bloqueadas',
        verbose_name="Bloqueado Por"
    )
    
    # Control de bloqueo temporal
    es_temporal = models.BooleanField(default=False, verbose_name="Bloqueo Temporal")
    fecha_expiracion = models.DateTimeField(null=True, blank=True,
                                            verbose_name="Fecha de Expiración")
    activo = models.BooleanField(default=True, verbose_name="Bloqueo Activo")
    
    # Estadísticas
    intentos_durante_bloqueo = models.IntegerField(default=0,
                                                    verbose_name="Intentos Durante Bloqueo")
    ultima_actividad = models.DateTimeField(auto_now=True,
                                            verbose_name="Última Actividad")
    
    # Información adicional
    pais = models.CharField(max_length=100, blank=True,
                           verbose_name="País de Origen")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    metadata = models.JSONField(default=dict, blank=True,
                               verbose_name="Metadata Adicional")
    
    class Meta:
        verbose_name = "IP Bloqueada"
        verbose_name_plural = "IPs Bloqueadas"
        ordering = ['-fecha_bloqueo']
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['activo', '-fecha_bloqueo']),
            models.Index(fields=['es_temporal', 'fecha_expiracion']),
        ]
    
    def __str__(self):
        estado = "Activo" if self.activo else "Inactivo"
        return f"{self.ip_address} - {self.get_tipo_bloqueo_display()} ({estado})"
    
    @classmethod
    def is_blocked(cls, ip_address):
        """Verifica si una IP está bloqueada y activa"""
        now = timezone.now()
        
        # Buscar bloqueo activo
        try:
            bloqueo = cls.objects.get(ip_address=ip_address, activo=True)
            
            # Si es temporal, verificar expiración
            if bloqueo.es_temporal and bloqueo.fecha_expiracion:
                if now > bloqueo.fecha_expiracion:
                    # Bloqueo expirado, desactivar
                    bloqueo.activo = False
                    bloqueo.save()
                    return False
            
            # Incrementar contador de intentos
            bloqueo.intentos_durante_bloqueo += 1
            bloqueo.save(update_fields=['intentos_durante_bloqueo', 'ultima_actividad'])
            
            return True
            
        except cls.DoesNotExist:
            return False
    
    @classmethod
    def block_ip(cls, ip_address, tipo_bloqueo, razon, bloqueado_por=None,
                es_temporal=False, minutos_bloqueo=None):
        """
        Bloquea una IP
        """
        fecha_expiracion = None
        if es_temporal and minutos_bloqueo:
            fecha_expiracion = timezone.now() + timedelta(minutes=minutos_bloqueo)
        
        bloqueo, created = cls.objects.update_or_create(
            ip_address=ip_address,
            defaults={
                'tipo_bloqueo': tipo_bloqueo,
                'razon': razon,
                'bloqueado_por': bloqueado_por,
                'es_temporal': es_temporal,
                'fecha_expiracion': fecha_expiracion,
                'activo': True,
                'intentos_durante_bloqueo': 0
            }
        )
        
        return bloqueo
    
    @classmethod
    def unblock_ip(cls, ip_address):
        """Desbloquea una IP"""
        cls.objects.filter(ip_address=ip_address).update(activo=False)
    
    @classmethod
    def cleanup_expired_blocks(cls):
        """Limpia bloqueos temporales expirados"""
        now = timezone.now()
        cls.objects.filter(
            es_temporal=True,
            fecha_expiracion__lt=now,
            activo=True
        ).update(activo=False)


class SecurityAlert(models.Model):
    """
    Alertas de seguridad que requieren atención
    """
    TIPO_ALERTA_CHOICES = [
        ('BRUTE_FORCE', 'Intento de Fuerza Bruta'),
        ('MULTIPLE_FAILED_LOGIN', 'Múltiples Intentos Fallidos'),
        ('SUSPICIOUS_IP', 'IP Sospechosa'),
        ('UNUSUAL_LOCATION', 'Ubicación Inusual'),
        ('UNUSUAL_TIME', 'Hora Inusual'),
        ('ACCOUNT_COMPROMISE', 'Posible Cuenta Comprometida'),
        ('DATA_BREACH', 'Posible Filtración de Datos'),
        ('PRIVILEGE_ESCALATION', 'Escalada de Privilegios'),
        ('UNAUTHORIZED_ACCESS', 'Acceso No Autorizado'),
        ('OTHER', 'Otro'),
    ]
    
    NIVEL_PRIORIDAD_CHOICES = [
        ('LOW', 'Baja'),
        ('MEDIUM', 'Media'),
        ('HIGH', 'Alta'),
        ('CRITICAL', 'Crítica'),
    ]
    
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('REVISANDO', 'En Revisión'),
        ('RESUELTA', 'Resuelta'),
        ('FALSA_ALARMA', 'Falsa Alarma'),
        ('IGNORADA', 'Ignorada'),
    ]
    
    tipo_alerta = models.CharField(max_length=30, choices=TIPO_ALERTA_CHOICES,
                                   verbose_name="Tipo de Alerta")
    nivel_prioridad = models.CharField(max_length=10, choices=NIVEL_PRIORIDAD_CHOICES,
                                       default='MEDIUM', verbose_name="Prioridad")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES,
                             default='PENDIENTE', verbose_name="Estado")
    
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descripcion = models.TextField(verbose_name="Descripción")
    
    # Usuario afectado (si aplica)
    usuario_afectado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertas_seguridad',
        verbose_name="Usuario Afectado"
    )
    
    # IP relacionada
    ip_address = models.GenericIPAddressField(null=True, blank=True,
                                              verbose_name="Dirección IP")
    
    # Fechas
    fecha_alerta = models.DateTimeField(auto_now_add=True,
                                        verbose_name="Fecha de Alerta")
    fecha_revision = models.DateTimeField(null=True, blank=True,
                                          verbose_name="Fecha de Revisión")
    fecha_resolucion = models.DateTimeField(null=True, blank=True,
                                            verbose_name="Fecha de Resolución")
    
    # Gestión
    asignado_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertas_asignadas',
        verbose_name="Asignado A"
    )
    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertas_resueltas',
        verbose_name="Resuelto Por"
    )
    
    notas = models.TextField(blank=True, verbose_name="Notas")
    acciones_tomadas = models.TextField(blank=True,
                                        verbose_name="Acciones Tomadas")
    
    # Notificaciones
    email_enviado = models.BooleanField(default=False,
                                        verbose_name="Email Enviado")
    fecha_email = models.DateTimeField(null=True, blank=True,
                                       verbose_name="Fecha de Email")
    
    # Información adicional
    metadata = models.JSONField(default=dict, blank=True,
                               verbose_name="Metadata Adicional")
    
    class Meta:
        verbose_name = "Alerta de Seguridad"
        verbose_name_plural = "Alertas de Seguridad"
        ordering = ['-fecha_alerta']
        indexes = [
            models.Index(fields=['estado', '-fecha_alerta']),
            models.Index(fields=['nivel_prioridad', '-fecha_alerta']),
            models.Index(fields=['usuario_afectado', '-fecha_alerta']),
            models.Index(fields=['asignado_a', '-fecha_alerta']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_alerta_display()} - {self.titulo} ({self.get_nivel_prioridad_display()})"
    
    @classmethod
    def create_alert(cls, tipo_alerta, titulo, descripcion, nivel_prioridad='MEDIUM',
                    usuario_afectado=None, ip_address=None, metadata=None):
        """
        Crea una nueva alerta de seguridad
        """
        alerta = cls.objects.create(
            tipo_alerta=tipo_alerta,
            nivel_prioridad=nivel_prioridad,
            titulo=titulo,
            descripcion=descripcion,
            usuario_afectado=usuario_afectado,
            ip_address=ip_address,
            metadata=metadata or {}
        )
        
        # Si es crítica, enviar email inmediatamente
        if nivel_prioridad == 'CRITICAL':
            alerta.enviar_notificacion_email()
        
        return alerta
    
    def enviar_notificacion_email(self):
        """Envía notificación por email a los administradores"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        if self.email_enviado:
            return
        
        try:
            # Obtener emails de administradores
            from escuelaweb.models import CustomUser
            admins = CustomUser.objects.filter(
                rol__in=['Administrador', 'Director'],
                is_active=True
            ).values_list('email', flat=True)
            
            if not admins:
                return
            
            subject = f"🚨 Alerta de Seguridad: {self.titulo}"
            message = f"""
Alerta de Seguridad Detectada

Tipo: {self.get_tipo_alerta_display()}
Prioridad: {self.get_nivel_prioridad_display()}
Fecha: {self.fecha_alerta.strftime('%Y-%m-%d %H:%M:%S')}

Descripción:
{self.descripcion}

{'Usuario Afectado: ' + self.usuario_afectado.email if self.usuario_afectado else ''}
{'IP: ' + self.ip_address if self.ip_address else ''}

Por favor, revisa el panel de administración para más detalles.

---
Sistema de Seguridad - Escuela Online
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                list(admins),
                fail_silently=True
            )
            
            self.email_enviado = True
            self.fecha_email = timezone.now()
            self.save(update_fields=['email_enviado', 'fecha_email'])
            
        except Exception as e:
            # Log error pero no fallar
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error enviando alerta de seguridad: {str(e)}")
    
    def marcar_como_revisando(self, usuario):
        """Marca la alerta como en revisión"""
        self.estado = 'REVISANDO'
        self.asignado_a = usuario
        self.fecha_revision = timezone.now()
        self.save()
    
    def resolver(self, usuario, acciones_tomadas=''):
        """Marca la alerta como resuelta"""
        self.estado = 'RESUELTA'
        self.resuelto_por = usuario
        self.fecha_resolucion = timezone.now()
        self.acciones_tomadas = acciones_tomadas
        self.save()
    
    @classmethod
    def get_active_alerts(cls):
        """Obtiene alertas activas (pendientes o en revisión)"""
        return cls.objects.filter(
            estado__in=['PENDIENTE', 'REVISANDO']
        ).order_by('-nivel_prioridad', '-fecha_alerta')

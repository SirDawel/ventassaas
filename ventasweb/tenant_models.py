"""
Modelos Multi-Tenant con django-tenants
Cada escuela tendrá su propio schema de PostgreSQL
"""
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Client(TenantMixin):
    """
    Representa una institución (tenant) con su propio schema de PostgreSQL
    """
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Institución")
    nombre_corto = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Nombre Corto (Subdominio)",
        help_text="Se usará como subdominio: nombre-corto.misventasflash.com"
    )
    email_contacto = models.EmailField(verbose_name="Email de Contacto")
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    direccion = models.TextField(blank=True, verbose_name="Dirección")
    
    # Configuración de suscripción
    plan = models.CharField(
        max_length=20,
        choices=[
            ('prueba', 'Prueba (30 días)'),
            ('basico', 'Básico'),
            ('profesional', 'Profesional'),
            ('premium', 'Premium'),
            ('enterprise', 'Enterprise'),
        ],
        default='prueba',
        verbose_name="Plan de Suscripción"
    )
    max_usuarios = models.IntegerField(default=50, verbose_name="Máximo de Usuarios")
    activo = models.BooleanField(default=False, verbose_name="Activo")
    activation_token = models.UUIDField(null=True, blank=True, verbose_name="Token de Activación")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_vencimiento = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Vencimiento")
    
    # Personalización
    logo = models.ImageField(upload_to='escuela/logos/', null=True, blank=True, verbose_name="Logo")
    color_primario = models.CharField(max_length=7, default='#007bff', verbose_name="Color Primario")
    color_secundario = models.CharField(max_length=7, default='#6c757d', verbose_name="Color Secundario")
    
    auto_create_schema = True

    class Meta:
        verbose_name = "Escuela (Tenant)"
        verbose_name_plural = "Escuelas (Tenants)"

    def __str__(self):
        return self.nombre

    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            subdominio = f"{self.schema_name}.misventasflash.com"
            # Evita duplicados asignando el tenant como default
            Domain.objects.get_or_create(
                domain=subdominio,
                defaults={'tenant': self, 'is_primary': True}
            )

    def esta_activa(self):
        """Verifica si la escuela está activa y no ha expirado"""
        if not self.activo:
            return False
        if self.fecha_vencimiento:
            from django.utils import timezone
            return timezone.now() < self.fecha_vencimiento
        return True

    def contar_usuarios(self):
        """Cuenta usuarios activos de esta escuela"""
        from .models import CustomUser
        return CustomUser.objects.filter(is_active=True).count()

    def puede_agregar_usuarios(self):
        """Verifica si puede agregar más usuarios"""
        return self.contar_usuarios() < self.max_usuarios


class Domain(DomainMixin):
    """
    Dominios asociados a cada tenant/escuela
    """
    class Meta:
        verbose_name = "Dominio"
        verbose_name_plural = "Dominios"
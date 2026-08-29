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
            ('gratis', 'Gratis (30 días)'),
            ('basico', 'Básico - $5/mes'),
            ('plus', 'Plus - $12/mes'),
            ('pro', 'Pro - $25/mes'),
        ],
        default='gratis',
        verbose_name="Plan de Suscripción"
    )
    
    # Límites por plan
    max_usuarios = models.IntegerField(default=1, verbose_name="Máximo de Usuarios")
    max_facturas_mes = models.IntegerField(default=50, verbose_name="Máximo Facturas/Mes")
    max_sucursales = models.IntegerField(default=1, verbose_name="Máximo de Sucursales")
    
    # Características habilitadas
    reportes_avanzados = models.BooleanField(default=False, verbose_name="Reportes Avanzados")
    facturacion_electronica = models.BooleanField(default=False, verbose_name="Facturación Electrónica")
    
    # Estado de la suscripción
    activo = models.BooleanField(default=False, verbose_name="Activo")
    activation_token = models.UUIDField(null=True, blank=True, verbose_name="Token de Activación")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_vencimiento = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Vencimiento")
    
    # Uso actual (se resetea cada mes para billing)
    facturas_mes_actual = models.IntegerField(default=0, verbose_name="Facturas este mes")
    ultimo_reset_facturas = models.DateField(null=True, blank=True, verbose_name="Último reset de facturas")
    
    # Precio y billing
    precio_mensual = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="Precio Mensual (USD)"
    )
    proximo_pago = models.DateField(null=True, blank=True, verbose_name="Próximo Pago")
    
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
        """
        Guarda el Tenant y configura límites según el plan
        """
        # Configurar límites automáticos según el plan
        if not self.pk:  # Solo al crear
            self.configurar_limites_plan()
        super().save(*args, **kwargs)
    
    def configurar_limites_plan(self):
        """Configura límites y precios según el plan seleccionado"""
        planes_config = {
            'gratis': {
                'max_usuarios': 1,
                'max_facturas_mes': 50,
                'max_sucursales': 1,
                'reportes_avanzados': False,
                'facturacion_electronica': False,
                'precio_mensual': 0.00,
                'dias_trial': 30
            },
            'basico': {
                'max_usuarios': 2,
                'max_facturas_mes': 200,
                'max_sucursales': 1,
                'reportes_avanzados': False,
                'facturacion_electronica': True,
                'precio_mensual': 5.00,
                'dias_trial': 0
            },
            'plus': {
                'max_usuarios': 5,
                'max_facturas_mes': 1000,
                'max_sucursales': 2,
                'reportes_avanzados': True,
                'facturacion_electronica': True,
                'precio_mensual': 12.00,
                'dias_trial': 0
            },
            'pro': {
                'max_usuarios': 15,
                'max_facturas_mes': 99999,  # Ilimitado
                'max_sucursales': 5,
                'reportes_avanzados': True,
                'facturacion_electronica': True,
                'precio_mensual': 25.00,
                'dias_trial': 0
            },
        }
        
        config = planes_config.get(self.plan, planes_config['gratis'])
        
        self.max_usuarios = config['max_usuarios']
        self.max_facturas_mes = config['max_facturas_mes']
        self.max_sucursales = config['max_sucursales']
        self.reportes_avanzados = config['reportes_avanzados']
        self.facturacion_electronica = config['facturacion_electronica']
        self.precio_mensual = config['precio_mensual']
        
        # Configurar fechas
        from django.utils import timezone
        from datetime import timedelta
        
        if not self.fecha_creacion:
            self.fecha_creacion = timezone.now()
        
        if config['dias_trial'] > 0:
            self.fecha_vencimiento = timezone.now() + timedelta(days=config['dias_trial'])
        
        if not self.proximo_pago and self.precio_mensual > 0:
            self.proximo_pago = (timezone.now() + timedelta(days=30)).date()
        
    def esta_activa(self):
        """Verifica si la suscripción está activa y no ha expirado"""
        if not self.activo:
            return False
        if self.fecha_vencimiento:
            from django.utils import timezone
            return timezone.now() < self.fecha_vencimiento
        return True

    def contar_usuarios(self):
        """Cuenta usuarios activos de este tenant"""
        from .models import CustomUser
        return CustomUser.objects.filter(is_active=True).count()

    def puede_agregar_usuarios(self):
        """Verifica si puede agregar más usuarios según límite del plan"""
        return self.contar_usuarios() < self.max_usuarios
    
    def contar_facturas_mes(self):
        """Cuenta facturas del mes actual"""
        from django.utils import timezone
        from datetime import date
        
        # Resetear contador si cambió el mes
        hoy = date.today()
        if not self.ultimo_reset_facturas or self.ultimo_reset_facturas.month != hoy.month:
            self.facturas_mes_actual = 0
            self.ultimo_reset_facturas = hoy
            self.save(update_fields=['facturas_mes_actual', 'ultimo_reset_facturas'])
        
        return self.facturas_mes_actual
    
    def puede_crear_factura(self):
        """Verifica si puede crear más facturas este mes"""
        if self.max_facturas_mes >= 99999:  # Ilimitado
            return True
        return self.contar_facturas_mes() < self.max_facturas_mes
    
    def incrementar_facturas(self):
        """Incrementa contador de facturas del mes"""
        self.facturas_mes_actual += 1
        self.save(update_fields=['facturas_mes_actual'])
    
    def get_info_plan(self):
        """Retorna información del plan actual"""
        return {
            'plan': self.get_plan_display(),
            'precio': f'${self.precio_mensual}/mes',
            'usuarios': f'{self.contar_usuarios()}/{self.max_usuarios}',
            'facturas_mes': f'{self.contar_facturas_mes()}/{self.max_facturas_mes if self.max_facturas_mes < 99999 else "∞"}',
            'sucursales_max': self.max_sucursales,
            'activo': self.esta_activa(),
            'proximo_pago': self.proximo_pago,
        }
    
    def get_porcentaje_uso_usuarios(self):
        """Porcentaje de uso de usuarios"""
        if self.max_usuarios == 0:
            return 0
        return (self.contar_usuarios() / self.max_usuarios) * 100
    
    def get_porcentaje_uso_facturas(self):
        """Porcentaje de uso de facturas del mes"""
        if self.max_facturas_mes >= 99999:
            return 0
        return (self.contar_facturas_mes() / self.max_facturas_mes) * 100


class Domain(DomainMixin):
    """
    Dominios asociados a cada tenant/escuela
    """
    class Meta:
        verbose_name = "Dominio"
        verbose_name_plural = "Dominios"
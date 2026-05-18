#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para agregar los modelos de suscripción a models.py
"""

modelos_nuevos = '''

# ============================================================================
# SISTEMA DE SUSCRIPCIONES Y PAGOS (SaaS)
# ============================================================================

class Plan(models.Model):
    """Planes de suscripción disponibles para las escuelas"""
    PLAN_TYPES = [
        ('BASICO', 'Básico - Hasta 50 usuarios'),
        ('ESTANDAR', 'Estándar - Hasta 200 usuarios'),
        ('PROFESIONAL', 'Profesional - Hasta 500 usuarios'),
        ('EMPRESARIAL', 'Empresarial - Sin límite'),
    ]
    
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Plan')
    tipo = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True, verbose_name='Tipo de Plan')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    
    # Precios
    precio_mensual = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio Mensual (USD)')
    precio_anual = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio Anual (USD)')
    
    # Límites
    max_usuarios = models.IntegerField(default=50, help_text="0 = ilimitado", verbose_name='Máximo de Usuarios')
    max_estudiantes = models.IntegerField(default=0, help_text="0 = ilimitado", verbose_name='Máximo de Estudiantes')
    
    # Características incluidas
    permite_reportes_avanzados = models.BooleanField(default=False, verbose_name='Reportes Avanzados')
    permite_integracion_api = models.BooleanField(default=False, verbose_name='Integración API')
    permite_multiples_sedes = models.BooleanField(default=False, verbose_name='Múltiples Sedes')
    soporte_prioritario = models.BooleanField(default=False, verbose_name='Soporte Prioritario')
    
    # Configuración Stripe (opcional)
    stripe_price_id_mensual = models.CharField(max_length=100, blank=True, help_text='ID del precio mensual en Stripe')
    stripe_price_id_anual = models.CharField(max_length=100, blank=True, help_text='ID del precio anual en Stripe')
    
    # Control
    activo = models.BooleanField(default=True, verbose_name='Plan Activo')
    orden = models.IntegerField(default=0, verbose_name='Orden de Visualización')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['orden', 'precio_mensual']
        verbose_name = 'Plan de Suscripción'
        verbose_name_plural = 'Planes de Suscripción'
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio_mensual}/mes"
    
    def precio_por_periodo(self, periodo='MENSUAL'):
        """Retorna el precio según el periodo"""
        return self.precio_mensual if periodo == 'MENSUAL' else self.precio_anual


class Suscripcion(models.Model):
    """Suscripción de cada escuela (tenant) a un plan"""
    ESTADO_CHOICES = [
        ('TRIAL', 'Periodo de Prueba (30 días)'),
        ('ACTIVA', 'Activa'),
        ('VENCIDA', 'Vencida'),
        ('CANCELADA', 'Cancelada'),
        ('SUSPENDIDA', 'Suspendida por falta de pago'),
    ]
    
    PERIODO_CHOICES = [
        ('MENSUAL', 'Mensual'),
        ('ANUAL', 'Anual'),
    ]
    
    # Relación con el tenant (cada escuela tiene UNA suscripción)
    tenant = models.OneToOneField(
        Client,
        on_delete=models.CASCADE,
        related_name='suscripcion',
        verbose_name='Escuela'
    )
    
    # Plan actual
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='suscripciones',
        verbose_name='Plan Actual'
    )
    
    # Estado y periodo
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='TRIAL', verbose_name='Estado')
    periodo = models.CharField(max_length=20, choices=PERIODO_CHOICES, default='MENSUAL', verbose_name='Periodo de Facturación')
    
    # Fechas importantes
    fecha_inicio = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Inicio')
    fecha_fin_trial = models.DateTimeField(null=True, blank=True, verbose_name='Fecha Fin de Prueba')
    fecha_proximo_pago = models.DateTimeField(null=True, blank=True, verbose_name='Próximo Pago')
    fecha_cancelacion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Cancelación')
    
    # Información de pago (Stripe)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='Stripe Customer ID')
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='Stripe Subscription ID')
    metodo_pago_tipo = models.CharField(max_length=20, blank=True, verbose_name='Tipo de Tarjeta')
    metodo_pago_ultimo4 = models.CharField(max_length=4, blank=True, verbose_name='Últimos 4 dígitos')
    
    # Control
    auto_renovacion = models.BooleanField(default=True, verbose_name='Renovación Automática')
    notificacion_vencimiento_enviada = models.BooleanField(default=False, verbose_name='Notificación Enviada')
    
    # Notas internas
    notas = models.TextField(blank=True, verbose_name='Notas Administrativas')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.tenant.nombre} - {self.plan.nombre} ({self.get_estado_display()})"
    
    def esta_activa(self):
        """Verifica si la suscripción permite acceso al sistema"""
        return self.estado in ['TRIAL', 'ACTIVA']
    
    def dias_restantes_trial(self):
        """Calcula días restantes de prueba"""
        from django.utils import timezone
        
        if self.estado != 'TRIAL' or not self.fecha_fin_trial:
            return 0
        
        delta = self.fecha_fin_trial - timezone.now()
        return max(0, delta.days)
    
    def puede_agregar_usuario(self):
        """Verifica si puede agregar más usuarios según el plan"""
        if self.plan.max_usuarios == 0:  # ilimitado
            return True
        
        usuarios_actuales = self.tenant.contar_usuarios()
        return usuarios_actuales < self.plan.max_usuarios
    
    def usuarios_disponibles(self):
        """Cantidad de usuarios que puede agregar aún"""
        if self.plan.max_usuarios == 0:
            return "Ilimitado"
        
        usuarios_actuales = self.tenant.contar_usuarios()
        disponibles = self.plan.max_usuarios - usuarios_actuales
        return max(0, disponibles)
    
    def precio_actual(self):
        """Precio que se cobra actualmente"""
        return self.plan.precio_por_periodo(self.periodo)
    
    def get_color_estado(self):
        """Color para mostrar el estado en la UI"""
        colores = {
            'TRIAL': 'info',
            'ACTIVA': 'success',
            'VENCIDA': 'warning',
            'CANCELADA': 'secondary',
            'SUSPENDIDA': 'danger',
        }
        return colores.get(self.estado, 'secondary')


class HistorialPago(models.Model):
    """Registro de todos los pagos realizados por las escuelas"""
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente de Procesamiento'),
        ('COMPLETADO', 'Completado Exitosamente'),
        ('FALLIDO', 'Fallido'),
        ('REEMBOLSADO', 'Reembolsado'),
    ]
    
    # Relación con suscripción
    suscripcion = models.ForeignKey(
        Suscripcion,
        on_delete=models.CASCADE,
        related_name='historial_pagos',
        verbose_name='Suscripción'
    )
    
    # Información del pago
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto')
    moneda = models.CharField(max_length=3, default='USD', verbose_name='Moneda')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, verbose_name='Estado del Pago')
    
    # IDs de pasarela de pago (Stripe)
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, verbose_name='Payment Intent ID')
    stripe_invoice_id = models.CharField(max_length=100, blank=True, verbose_name='Invoice ID')
    stripe_charge_id = models.CharField(max_length=100, blank=True, verbose_name='Charge ID')
    
    # Detalles del pago
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    metodo_pago = models.CharField(max_length=50, blank=True, verbose_name='Método de Pago')
    
    # Fechas
    fecha_pago = models.DateTimeField(null=True, blank=True, verbose_name='Fecha del Pago')
    fecha_procesado = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Procesamiento')
    
    # Facturación
    numero_factura = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='Número de Factura')
    factura_url = models.URLField(blank=True, verbose_name='URL de Factura')
    
    # Metadata adicional (JSON)
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Metadata Adicional')
    
    class Meta:
        ordering = ['-fecha_procesado']
        verbose_name = 'Historial de Pago'
        verbose_name_plural = 'Historial de Pagos'
        indexes = [
            models.Index(fields=['suscripcion', '-fecha_procesado']),
            models.Index(fields=['estado', '-fecha_procesado']),
            models.Index(fields=['stripe_payment_intent_id']),
        ]
    
    def __str__(self):
        return f"{self.suscripcion.tenant.nombre} - ${self.monto} ({self.get_estado_display()})"
    
    def generar_numero_factura(self):
        """Genera un número de factura único"""
        from django.utils import timezone
        if not self.numero_factura:
            fecha = timezone.now().strftime('%Y%m%d')
            ultimo = HistorialPago.objects.filter(
                numero_factura__startswith=f'INV-{fecha}'
            ).count()
            self.numero_factura = f'INV-{fecha}-{ultimo + 1:04d}'
            self.save(update_fields=['numero_factura'])
        return self.numero_factura
'''

# Leer el archivo actual
with open('escuelaweb/models.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Agregar los nuevos modelos al final
with open('escuelaweb/models.py', 'w', encoding='utf-8') as f:
    f.write(contenido + modelos_nuevos)

print("✅ Modelos de suscripción agregados exitosamente!")

# -*- coding: utf-8 -*-
import uuid
# Create your models here.

from decimal import Decimal
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

# Importar modelos multi-tenant de django-tenants
from .tenant_models import Client, Domain


class CustomUserManager(BaseUserManager):
    """
    Manager para CustomUser - con django-tenants el filtrado es automÃ¡tico por schema
    """
    
    def create_user(self, email, password=None, **extra_fields):

        if not email:
            raise ValueError("El correo electrÃ³nico es obligatorio")
            
        email = self.normalize_email(email)
        
        user = self.model(email=email, **extra_fields)

        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):

        extra_fields.setdefault("is_staff", True)

        extra_fields.setdefault("is_superuser", True)

        extra_fields.setdefault("is_active", True)
        

        if extra_fields.get("is_staff") is not True:

            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:

            raise ValueError("Superuser must have is_superuser=True.")

        

        return self.create_user(email, password, **extra_fields)



from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from datetime import date, timedelta
import uuid
import os

def user_profile_picture_path(instance, filename):
    """Define la ruta donde se guardarÃ¡n las imÃ¡genes de perfil."""
    return os.path.join("uploads/profile_pictures/", f"user_{instance.id}_{filename}")

class CustomUser(AbstractBaseUser, PermissionsMixin):
    # Campos bÃ¡sicos de autenticaciÃ³n
    email = models.EmailField(unique=True, verbose_name="Correo electrÃ³nico")
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # InformaciÃ³n personal
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    genero = models.CharField(
        max_length=10,
        choices=[("M", "M"), ("F", "F"), ("Otro", "Otro")],
        null=True,
        blank=True
    )
    direccion = models.TextField(null=True, blank=True)
    telefono = models.CharField(max_length=15, null=True, blank=True)
    cedula = models.CharField(max_length=11, unique=True, null=True, blank=True)
    codigo_barras = models.CharField(max_length=50, unique=True, null=True, blank=True, 
                                     help_text='CÃ³digo de barras para ponchar asistencia')
    activation_token = models.CharField(max_length=100, blank=True, null=True)

    
    
        
    # Rol en el sistema de ventas
    rol = models.CharField(
        max_length=20,
        choices=[
            ("Cliente", "Cliente"),
            ("Vendedor", "Vendedor"),
            ("Gerente", "Gerente"),
            ("Secretaria", "Secretaria"),
            ("Administrador", "Administrador"),
            ("Supervisor", "Supervisor"),
            ("Almacenista", "Almacenista"),
            ("Asistente", "Asistente"),
            ("Otro", "Otro")
        ],
        default="Cliente"
    )
    
    # Tipo de cliente (para clientes)
    tipo_cliente = models.CharField(
        max_length=20,
        choices=[
            ("Minorista", "Minorista"),
            ("Mayorista", "Mayorista"),
            ("Corporativo", "Corporativo")
        ],
        null=True,
        blank=True,
        help_text="Tipo de cliente: Minorista, Mayorista o Corporativo"
    )
    
    # Campos para CLIENTES
    limite_credito = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Límite de Crédito",
        help_text="Monto máximo de crédito disponible para el cliente"
    )
    
    dias_credito = models.IntegerField(
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(365)],
        verbose_name="Días de Crédito",
        help_text="Cantidad de días de crédito otorgado al cliente"
    )
    
    descuento_cliente = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Descuento Cliente (%)",
        help_text="Porcentaje de descuento general para el cliente"
    )
    
    # Cliente corporativo (si aplica)
    cliente_corporativo = models.ForeignKey(
        'ClienteCorporativo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes',
        verbose_name="Cliente Corporativo",
        help_text="Empresa o grupo corporativo al que pertenece"
    )
    
    # Campos para VENDEDORES
    comision_vendedor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Comisión Vendedor (%)",
        help_text="Porcentaje de comisión sobre las ventas"
    )
    
    meta_mensual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Meta Mensual",
        help_text="Meta de ventas mensual para el vendedor"
    )
    
    zona_venta = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Zona de Venta",
        help_text="Zona geográfica asignada al vendedor"
    )
    
    # Campos para personal administrativo
    departamento = models.CharField(max_length=100, null=True, blank=True)
    cargo = models.CharField(max_length=100, null=True, blank=True)
    
    # InformaciÃ³n de contacto de emergencia
    contacto_emergencia_nombre = models.CharField(max_length=100, null=True, blank=True)
    contacto_emergencia_telefono = models.CharField(max_length=15, null=True, blank=True)
    contacto_emergencia_parentesco = models.CharField(max_length=50, null=True, blank=True)
    
    # Campos adicionales
    foto_perfil = models.ImageField(upload_to=user_profile_picture_path, null=True, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)
    fecha_salida = models.DateField(null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ("Activo", "Activo"),
            ("Inactivo", "Inactivo"),
            ("Suspendido", "Suspendido"),
            ("Moroso", "Moroso"),
            ("Bloqueado", "Bloqueado")
        ],
        default="Activo"
    )
    notas = models.TextField(null=True, blank=True)
    
    # Campos de seguridad
    activation_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    
    # Multi-Tenant: Empresa a la que pertenece
    
    # Multi-Tenant Manager con filtrado automÃ¡tico
    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "rol"]

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_descuento(self):
        """
        Obtiene el porcentaje de descuento aplicable al cliente.
        Si pertenece a un cliente corporativo, usa el descuento del grupo.
        Si no, usa el descuento individual.
        """
        if self.cliente_corporativo and self.cliente_corporativo.descuento_general > 0:
            return self.cliente_corporativo.descuento_general
        return self.descuento_cliente
    
    def get_limite_credito_disponible(self):
        """
        Calcula el crédito disponible restando el saldo pendiente.
        """
        if self.rol != 'Cliente':
            return 0
        
        # Calcular saldo pendiente de facturas
        from django.db.models import Sum, Q
        saldo_pendiente = self.facturas_cliente.filter(
            Q(estado='pendiente') | Q(estado='parcial')
        ).aggregate(
            total=Sum('saldo')
        )['total'] or 0
        
        return max(0, self.limite_credito - saldo_pendiente)
    
    def get_short_name(self):
        return self.first_name
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.rol})"
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["-date_joined"]

    def calcular_edad(self):
        if not self.fecha_nacimiento:
            return None  # o '--' si quieres mostrar directamente en el template
        today = date.today()
        edad = today.year - self.fecha_nacimiento.year
        # restar 1 si no ha cumplido aÃ±os este aÃ±o
        if (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day):
            edad -= 1
        return edad

class Tutor(models.Model):
    # Multi-Tenant: Escuela
    
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15, null=True, blank=True)
    parentesco = models.CharField(
        max_length=20,
        choices=[("Padre", "Padre"), ("Madre", "Madre"), ("Tutor", "Tutor"), ("Otro", "Otro")],
        default="Otro"
    )
    direccion = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.parentesco})"

class Persona(models.Model):  # Renombrado desde "Estudiante"
    # Multi-Tenant: Escuela
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="persona")
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    #fecha_nacimiento = models.DateField()
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexo = models.CharField(
        max_length=10,
        choices=[("M", "M"), ("F", "F"), ("Otro", "Otro")],
        default="Otro"
    )
    cedula = models.CharField(max_length=11, unique=True, null=True, blank=True)
    rne = models.CharField(max_length=20, unique=True, null=True, blank=True)  # Registro Nacional de Extranjeros
    direccion = models.TextField(null=True, blank=True)
    telefono = models.CharField(max_length=15, null=True, blank=True)
    grado = models.CharField(max_length=50, null=True, blank=True)  # Opcional si la persona no es estudiante
    fecha_registro = models.DateTimeField(auto_now_add=True)
    padre = models.ForeignKey(Tutor, on_delete=models.SET_NULL, null=True, blank=True, related_name="padre_de")
    madre = models.ForeignKey(Tutor, on_delete=models.SET_NULL, null=True, blank=True, related_name="madre_de")
    tutor = models.ForeignKey(Tutor, on_delete=models.SET_NULL, null=True, blank=True, related_name="tutor_de")
    contacto_emergencia = models.ForeignKey(Tutor, on_delete=models.SET_NULL, null=True, blank=True, related_name="contacto_emergencia_de")

            
    def __str__(self):
        return f"{self.nombre} {self.apellido}"



# ==============================

#   AÃ±o Escolar Modelo

# ==============================



class AnhoEscolar(models.Model):
    # Multi-Tenant: Escuela
    

    # Multi-Tenant Manager
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'AÃ±o Escolar'
        verbose_name_plural = 'AÃ±os Escolares'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if self.activo:
            # Desactivar otros aÃ±os escolares activos
            AnhoEscolar.objects.filter(activo=True).exclude(pk=self.pk).update(activo=False)
        super().save(*args, **kwargs)


class Mensualidad(models.Model):
    """Registro de cargos mensuales por estudiante (mensualidades).
    Se crea una entrada por (estudiante, aÃ±o escolar, mes) y puede vincularse a una factura cuando se cobra.
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('parcial', 'Pago Parcial'),
        ('pagada', 'Pagada'),
        ('anulada', 'Anulada'),
    ]

    # Multi-Tenant: Escuela
    
    estudiante = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='mensualidades', limit_choices_to={'rol': 'Estudiante'})
    anho_escolar = models.ForeignKey(AnhoEscolar, on_delete=models.PROTECT, related_name='mensualidades')
    from django.core.validators import MinValueValidator, MaxValueValidator
    mes = models.IntegerField(help_text='Mes numÃ©rico (1-12)', validators=[MinValueValidator(1), MaxValueValidator(12)])
    anio = models.IntegerField()
    concepto = models.ForeignKey('ConceptoPago', on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.CharField(max_length=255, blank=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', db_index=True)
    factura = models.ForeignKey('Factura', on_delete=models.SET_NULL, null=True, blank=True, related_name='mensualidades')
    fecha_vencimiento = models.DateField(null=True, blank=True)
    fecha_generada = models.DateTimeField(auto_now_add=True)
    fecha_pagado = models.DateTimeField(null=True, blank=True)
    creado_por = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='mensualidades_creadas')
    notas = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = (('estudiante', 'anho_escolar', 'mes', 'anio'),)
        ordering = ['-anio', '-mes']
        verbose_name = 'Mensualidad'
        verbose_name_plural = 'Mensualidades'

    def __str__(self):
        return f"{self.estudiante.get_full_name()} - {self.mes}/{self.anio} - RD${self.monto} ({self.estado})"

    def marcar_pagada(self, factura=None):
        from django.utils import timezone
        self.estado = 'pagada'
        self.fecha_pagado = timezone.now()
        if factura:
            self.factura = factura
        self.save()

#___________________ persona___________________________________








#____________________Estudiantes_______________________________


class Estudiante(models.Model):
    # Multi-Tenant: Escuela
    

    # Multi-Tenant Manager
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='estudiante', null=True, blank=True)
    grado = models.CharField(max_length=50)
    correo = models.EmailField(unique=True, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    nombre = models.CharField(max_length=50, null=True, blank=True)
    apellido = models.CharField(max_length=50, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.user.get_full_name()}"
    

#____________________Profesor_______________________________


class Profesor(models.Model):
    # Multi-Tenant: Escuela
    

    # Multi-Tenant Manager
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profesor')
    especialidad = models.CharField(max_length=100, null=True, blank=True)
    departamento = models.CharField(max_length=100, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()}"

class Curso(models.Model):
    # Multi-Tenant: Escuela
    

    # Multi-Tenant Manager
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    anho_escolar = models.ForeignKey(AnhoEscolar, on_delete=models.CASCADE, related_name='cursos')
    profesor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='cursos_impartidos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['nombre', 'anho_escolar']
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.anho_escolar.nombre}"

class Materia(models.Model):
    CATEGORIA_CHOICES = [
        ('periodo', 'Por PerÃ­odos'),
        ('modular', 'Modular'),
    ]
    
    # Multi-Tenant: Escuela
    

    # Multi-Tenant Manager
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    creditos = models.PositiveIntegerField(default=1)
    categoria = models.CharField(
        max_length=20, 
        choices=CATEGORIA_CHOICES, 
        default='periodo',
        verbose_name='CategorÃ­a de EvaluaciÃ³n',
        help_text='Por PerÃ­odos: calificaciones por perÃ­odo (P1, P2, P3). Modular: evaluaciÃ³n continua.'
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='materias')
    profesor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='materias_impartidas')
    estudiantes = models.ManyToManyField(CustomUser, through='Matricula', related_name='materias_inscritas')
    
    # DÃ­as en que se imparte la materia
    lunes = models.BooleanField(default=False, verbose_name='Lunes')
    martes = models.BooleanField(default=False, verbose_name='Martes')
    miercoles = models.BooleanField(default=False, verbose_name='MiÃ©rcoles')
    jueves = models.BooleanField(default=False, verbose_name='Jueves')
    viernes = models.BooleanField(default=False, verbose_name='Viernes')
    
    # ConfiguraciÃ³n de Resultados de Aprendizaje (RA) para materias modulares
    # Ejemplo: {"cantidad": 7, "valores": [15, 15, 15, 15, 10, 15, 15]} (suma debe ser 100)
    ra_configuracion = models.JSONField(null=True, blank=True, help_text="ConfiguraciÃ³n de RA: cantidad y valores en % (solo modular)")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"
    
    def dias_semana(self):
        """Retorna una lista de dÃ­as en que se imparte la materia"""
        dias = []
        if self.lunes: dias.append('Lunes')
        if self.martes: dias.append('Martes')
        if self.miercoles: dias.append('MiÃ©rcoles')
        if self.jueves: dias.append('Jueves')
        if self.viernes: dias.append('Viernes')
        return dias
    
    def se_imparte_hoy(self):
        """Verifica si la materia se imparte hoy segÃºn el dÃ­a de la semana"""
        from django.utils import timezone
        dia_semana = timezone.now().weekday()  # 0=Lunes, 1=Martes, ..., 4=Viernes
        dias_map = {
            0: self.lunes,
            1: self.martes,
            2: self.miercoles,
            3: self.jueves,
            4: self.viernes
        }
        return dias_map.get(dia_semana, False)


from django.db import models
from django.conf import settings

class Matricula(models.Model):
    # Multi-Tenant: Escuela
    
    estudiante = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='matriculas')
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='matriculas')
    anho_escolar = models.ForeignKey(AnhoEscolar, on_delete=models.CASCADE, related_name='matriculas')

    # ------------------------
    # Notas por competencia
    # ------------------------
    # Competencia Comunicativa
    com_p1 = models.FloatField(null=True, blank=True, verbose_name="Com P1")
    com_rp1 = models.FloatField(null=True, blank=True, verbose_name="Com RP1")
    com_p2 = models.FloatField(null=True, blank=True, verbose_name="Com P2")
    com_rp2 = models.FloatField(null=True, blank=True, verbose_name="Com RP2")
    com_p3 = models.FloatField(null=True, blank=True, verbose_name="Com P3")
    com_rp3 = models.FloatField(null=True, blank=True, verbose_name="Com RP3")
    com_p4 = models.FloatField(null=True, blank=True, verbose_name="Com P4")
    com_rp4 = models.FloatField(null=True, blank=True, verbose_name="Com RP4")
    com_rp = models.FloatField(null=True, blank=True, verbose_name="Com RP Final")

    # Competencia LÃ³gico-MatemÃ¡tica
    log_p1 = models.FloatField(null=True, blank=True, verbose_name="Mat P1")
    log_rp1 = models.FloatField(null=True, blank=True, verbose_name="Mat RP1")
    log_p2 = models.FloatField(null=True, blank=True, verbose_name="Mat P2")
    log_rp2 = models.FloatField(null=True, blank=True, verbose_name="Mat RP2")
    log_p3 = models.FloatField(null=True, blank=True, verbose_name="Mat P3")
    log_rp3 = models.FloatField(null=True, blank=True, verbose_name="Mat RP3")
    log_p4 = models.FloatField(null=True, blank=True, verbose_name="Mat P4")
    log_rp4 = models.FloatField(null=True, blank=True, verbose_name="Mat RP4")
    log_rp = models.FloatField(null=True, blank=True, verbose_name="Mat RP Final")

    # Competencia CientÃ­fica
    cie_p1 = models.FloatField(null=True, blank=True, verbose_name="Cie P1")
    cie_rp1 = models.FloatField(null=True, blank=True, verbose_name="Cie RP1")
    cie_p2 = models.FloatField(null=True, blank=True, verbose_name="Cie P2")
    cie_rp2 = models.FloatField(null=True, blank=True, verbose_name="Cie RP2")
    cie_p3 = models.FloatField(null=True, blank=True, verbose_name="Cie P3")
    cie_rp3 = models.FloatField(null=True, blank=True, verbose_name="Cie RP3")
    cie_p4 = models.FloatField(null=True, blank=True, verbose_name="Cie P4")
    cie_rp4 = models.FloatField(null=True, blank=True, verbose_name="Cie RP4")
    cie_rp = models.FloatField(null=True, blank=True, verbose_name="Cie RP Final")

    # Competencia Ã‰tica y Ciudadana
    eti_p1 = models.FloatField(null=True, blank=True, verbose_name="Eti P1")
    eti_rp1 = models.FloatField(null=True, blank=True, verbose_name="Eti RP1")
    eti_p2 = models.FloatField(null=True, blank=True, verbose_name="Eti P2")
    eti_rp2 = models.FloatField(null=True, blank=True, verbose_name="Eti RP2")
    eti_p3 = models.FloatField(null=True, blank=True, verbose_name="Eti P3")
    eti_rp3 = models.FloatField(null=True, blank=True, verbose_name="Eti RP3")
    eti_p4 = models.FloatField(null=True, blank=True, verbose_name="Eti P4")
    eti_rp4 = models.FloatField(null=True, blank=True, verbose_name="Eti RP4")
    eti_rp = models.FloatField(null=True, blank=True, verbose_name="Eti RP Final")

    # ------------------------
    # ExÃ¡menes finales
    # ------------------------
    ex_com = models.FloatField(null=True, blank=True)  # Completivo
    ex_ext = models.FloatField(null=True, blank=True)  # Extraordinario
    ex_esp = models.FloatField(null=True, blank=True)  # Especial

    # ------------------------
    # Resultados de Aprendizaje (RA) - Para materias modulares
    # Cada RA vale 10%, total 100%
    # ------------------------
    ra_1 = models.FloatField(null=True, blank=True, verbose_name="RA 1 (%)")
    ra_2 = models.FloatField(null=True, blank=True, verbose_name="RA 2 (%)")
    ra_3 = models.FloatField(null=True, blank=True, verbose_name="RA 3 (%)")
    ra_4 = models.FloatField(null=True, blank=True, verbose_name="RA 4 (%)")
    ra_5 = models.FloatField(null=True, blank=True, verbose_name="RA 5 (%)")
    ra_6 = models.FloatField(null=True, blank=True, verbose_name="RA 6 (%)")
    ra_7 = models.FloatField(null=True, blank=True, verbose_name="RA 7 (%)")
    ra_8 = models.FloatField(null=True, blank=True, verbose_name="RA 8 (%)")
    ra_9 = models.FloatField(null=True, blank=True, verbose_name="RA 9 (%)")
    ra_10 = models.FloatField(null=True, blank=True, verbose_name="RA 10 (%)")


    # ------------------------
    # FunciÃ³n interna con redondeo correcto
    # ------------------------
    def _to_float_safe(self, valor):
        """Convierte un valor a float de forma segura, retorna None si no es vÃ¡lido"""
        if valor is None:
            return None
        try:
            return float(valor)
        except (ValueError, TypeError):
            return None
    
    def _calc_promedio(self, notas):
        """Calcula el promedio de una lista de notas usando redondeo matemÃ¡tico estÃ¡ndar"""
        from .utils_notas import redondear_promedio
        return redondear_promedio(notas)

    # ------------------------
    # Promedios por competencia
    # ------------------------
    @property
    def prom_comunicativa(self):
        # Usar recuperaciÃ³n por perÃ­odo si la nota es menor a 70
        p1_val = self._to_float_safe(self.com_p1)
        rp1_val = self._to_float_safe(self.com_rp1)
        p1 = rp1_val if (p1_val is not None and p1_val < 70 and rp1_val is not None) else p1_val
        
        p2_val = self._to_float_safe(self.com_p2)
        rp2_val = self._to_float_safe(self.com_rp2)
        p2 = rp2_val if (p2_val is not None and p2_val < 70 and rp2_val is not None) else p2_val
        
        p3_val = self._to_float_safe(self.com_p3)
        rp3_val = self._to_float_safe(self.com_rp3)
        p3 = rp3_val if (p3_val is not None and p3_val < 70 and rp3_val is not None) else p3_val
        
        p4_val = self._to_float_safe(self.com_p4)
        rp4_val = self._to_float_safe(self.com_rp4)
        p4 = rp4_val if (p4_val is not None and p4_val < 70 and rp4_val is not None) else p4_val
        
        return self._calc_promedio([p1, p2, p3, p4])

    @property
    def prom_logico(self):
        # Usar recuperaciÃ³n por perÃ­odo si la nota es menor a 70
        p1_val = self._to_float_safe(self.log_p1)
        rp1_val = self._to_float_safe(self.log_rp1)
        p1 = rp1_val if (p1_val is not None and p1_val < 70 and rp1_val is not None) else p1_val
        
        p2_val = self._to_float_safe(self.log_p2)
        rp2_val = self._to_float_safe(self.log_rp2)
        p2 = rp2_val if (p2_val is not None and p2_val < 70 and rp2_val is not None) else p2_val
        
        p3_val = self._to_float_safe(self.log_p3)
        rp3_val = self._to_float_safe(self.log_rp3)
        p3 = rp3_val if (p3_val is not None and p3_val < 70 and rp3_val is not None) else p3_val
        
        p4_val = self._to_float_safe(self.log_p4)
        rp4_val = self._to_float_safe(self.log_rp4)
        p4 = rp4_val if (p4_val is not None and p4_val < 70 and rp4_val is not None) else p4_val
        
        return self._calc_promedio([p1, p2, p3, p4])

    @property
    def prom_cientifica(self):
        # Usar recuperaciÃ³n por perÃ­odo si la nota es menor a 70
        p1_val = self._to_float_safe(self.cie_p1)
        rp1_val = self._to_float_safe(self.cie_rp1)
        p1 = rp1_val if (p1_val is not None and p1_val < 70 and rp1_val is not None) else p1_val
        
        p2_val = self._to_float_safe(self.cie_p2)
        rp2_val = self._to_float_safe(self.cie_rp2)
        p2 = rp2_val if (p2_val is not None and p2_val < 70 and rp2_val is not None) else p2_val
        
        p3_val = self._to_float_safe(self.cie_p3)
        rp3_val = self._to_float_safe(self.cie_rp3)
        p3 = rp3_val if (p3_val is not None and p3_val < 70 and rp3_val is not None) else p3_val
        
        p4_val = self._to_float_safe(self.cie_p4)
        rp4_val = self._to_float_safe(self.cie_rp4)
        p4 = rp4_val if (p4_val is not None and p4_val < 70 and rp4_val is not None) else p4_val
        
        return self._calc_promedio([p1, p2, p3, p4])

    @property
    def prom_etica(self):
        # Usar recuperaciÃ³n por perÃ­odo si la nota es menor a 70
        p1_val = self._to_float_safe(self.eti_p1)
        rp1_val = self._to_float_safe(self.eti_rp1)
        p1 = rp1_val if (p1_val is not None and p1_val < 70 and rp1_val is not None) else p1_val
        
        p2_val = self._to_float_safe(self.eti_p2)
        rp2_val = self._to_float_safe(self.eti_rp2)
        p2 = rp2_val if (p2_val is not None and p2_val < 70 and rp2_val is not None) else p2_val
        
        p3_val = self._to_float_safe(self.eti_p3)
        rp3_val = self._to_float_safe(self.eti_rp3)
        p3 = rp3_val if (p3_val is not None and p3_val < 70 and rp3_val is not None) else p3_val
        
        p4_val = self._to_float_safe(self.eti_p4)
        rp4_val = self._to_float_safe(self.eti_rp4)
        p4 = rp4_val if (p4_val is not None and p4_val < 70 and rp4_val is not None) else p4_val
        
        return self._calc_promedio([p1, p2, p3, p4])

    # ------------------------
    # Promedio final
    # ------------------------
    @property
    def promedio_final(self):
        comps = [
            self.prom_comunicativa,
            self.prom_logico,
            self.prom_cientifica,
            self.prom_etica
        ]
        if None in comps:
            return None
        from .utils_notas import redondear_promedio
        return redondear_promedio(comps)
    

    # ------------------------
    # CÃ¡lculo COMPLETIVO final
    # ------------------------
    @property
    def calificacion_completiva_final(self):
        from .utils_notas import calcular_nota_completiva
        return calcular_nota_completiva(self.promedio_final, self.ex_com)
    

    # ------------------------
    # CÃ¡lculo EXTRAORDINARIO final
    # 30% promedio + 70% examen extraordinario
    # ------------------------
    @property
    def calificacion_extraordinario_final(self):
        from .utils_notas import calcular_nota_extraordinaria
        return calcular_nota_extraordinaria(self.promedio_final, self.ex_ext)
    

    # ------------------------
    # CÃ¡lculo ESPECIAL final
    # solo examen especial
    # ------------------------
    @property
    def calificacion_especial_final(self):
        return self.ex_esp if self.ex_esp is not None else None

    
    @property
    def estado(self):
        """
        Determina el estado del estudiante considerando exÃ¡menes especiales.
        Orden de prioridad:
        1. Examen Especial (reemplaza todo)
        2. Examen Extraordinario
        3. Examen Completivo
        4. Promedio Final regular
        """
        # 1. Si tiene examen especial, ese es el que cuenta
        if self.ex_esp is not None:
            calificacion_final = self.calificacion_especial_final
            if calificacion_final is not None:
                if calificacion_final >= 70:
                    return "Aprobado"
                else:
                    return "Reprobado"
        
        # 2. Si tiene examen extraordinario, usar ese
        if self.ex_ext is not None:
            calificacion_final = self.calificacion_extraordinario_final
            if calificacion_final is not None:
                if calificacion_final >= 70:
                    return "Aprobado"
                else:
                    return "Reprobado"
        
        # 3. Si tiene examen completivo, usar ese
        if self.ex_com is not None:
            calificacion_final = self.calificacion_completiva_final
            if calificacion_final is not None:
                if calificacion_final >= 70:
                    return "Aprobado"
                else:
                    return "Reprobado"
        
        # 4. Si no hay exÃ¡menes especiales, usar promedio final regular
        if self.promedio_final is None:
            return "En proceso"
        if self.promedio_final >= 70:
            return "Aprobado"
        return "Reprobado"

    @property
    def nota_final_efectiva(self):
        """
        Retorna la nota final que se usa para determinar el estado.
        Considera exÃ¡menes especiales en orden de prioridad.
        """
        # 1. Examen Especial tiene mÃ¡xima prioridad
        if self.ex_esp is not None and self.calificacion_especial_final is not None:
            return self.calificacion_especial_final
        
        # 2. Examen Extraordinario
        if self.ex_ext is not None and self.calificacion_extraordinario_final is not None:
            return self.calificacion_extraordinario_final
        
        # 3. Examen Completivo
        if self.ex_com is not None and self.calificacion_completiva_final is not None:
            return self.calificacion_completiva_final
        
        # 4. Promedio Final regular
        return self.promedio_final
    
    @property
    def tipo_calificacion(self):
        """
        Retorna el tipo de calificaciÃ³n que se estÃ¡ usando para la nota final.
        """
        if self.ex_esp is not None:
            return "Examen Especial"
        if self.ex_ext is not None:
            return "Examen Extraordinario"
        if self.ex_com is not None:
            return "Examen Completivo"
        return "Promedio Regular"

    def clean(self):
        """Validar que todas las notas estÃ©n entre 0 y 100"""
        from django.core.exceptions import ValidationError
        
        # Lista de todos los campos de notas
        campos_notas = [
            'com_p1', 'com_rp1', 'com_p2', 'com_rp2', 'com_p3', 'com_rp3', 'com_p4', 'com_rp4', 'com_rp',
            'log_p1', 'log_rp1', 'log_p2', 'log_rp2', 'log_p3', 'log_rp3', 'log_p4', 'log_rp4', 'log_rp',
            'cie_p1', 'cie_rp1', 'cie_p2', 'cie_rp2', 'cie_p3', 'cie_rp3', 'cie_p4', 'cie_rp4', 'cie_rp',
            'eti_p1', 'eti_rp1', 'eti_p2', 'eti_rp2', 'eti_p3', 'eti_rp3', 'eti_p4', 'eti_rp4', 'eti_rp',
            'ex_com', 'ex_ext', 'ex_esp'
        ]
        
        # Validar campos de notas por competencias (0-100)
        for campo in campos_notas:
            valor = getattr(self, campo)
            if valor is not None:
                if valor < 0 or valor > 100:
                    raise ValidationError(f"La nota '{campo}' debe estar entre 0 y 100. Valor actual: {valor}")
        
        # Validar RAs (0-10, ya que cada uno vale 10%)
        campos_ra = ['ra_1', 'ra_2', 'ra_3', 'ra_4', 'ra_5', 'ra_6', 'ra_7', 'ra_8', 'ra_9', 'ra_10']
        for campo in campos_ra:
            valor = getattr(self, campo)
            if valor is not None:
                if valor < 0 or valor > 10:
                    raise ValidationError(f"El {campo.upper()} debe estar entre 0 y 10. Valor actual: {valor}")

    def save(self, *args, **kwargs):
        """Sobrescribir save para ejecutar validaciÃ³n solo cuando sea necesario"""
        # Permitir skip de validaciÃ³n para cÃ¡lculos automÃ¡ticos
        skip_validation = kwargs.pop('skip_validation', False)
        
        if not skip_validation:
            self.clean()
        
        super().save(*args, **kwargs)

    # -------- META CORRECTA -------
    class Meta:
        indexes = [
            models.Index(fields=["estudiante"]),
            models.Index(fields=["materia"]),
            models.Index(fields=["anho_escolar"]),
        ]


# Signal para actualizar grado y secciÃ³n del estudiante cuando se crea/actualiza una matrÃ­cula
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Matricula)
def update_user_grade_section(sender, instance, created, **kwargs):
    try:
        curso = instance.materia.curso
        nombre = curso.nombre or ''
        parts = nombre.rsplit(' ', 1)
        if len(parts) == 2 and parts[1].isalpha() and len(parts[1]) == 1:
            grado_text = parts[0].strip()
            seccion_text = parts[1].upper()
        else:
            grado_text = nombre.strip()
            seccion_text = ''

        estudiante = instance.estudiante
        estudiante.grado = grado_text
        estudiante.seccion = seccion_text
        estudiante.save(update_fields=['grado', 'seccion'])
    except Exception:
        # No interrumpir si hay problemas (por ejemplo, datos incompletos)
        pass


# StudentGroup moved here to avoid interrupting Matricula class body
class StudentGroup(models.Model):
    # Multi-Tenant: Escuela
    
    nombre = models.CharField(max_length=150)
    grado = models.CharField(max_length=50)
    seccion = models.CharField(max_length=10)
    creado_por = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='grupos_creados')
    estudiantes = models.ManyToManyField(CustomUser, related_name='grupos', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Grupo de Estudiantes'
        verbose_name_plural = 'Grupos de Estudiantes'

    def __str__(self):
        return f"{self.nombre} - {self.grado} {self.seccion}"


class Asistencia(models.Model):
    ESTADO_CHOICES = [
        ('presente', 'Presente'),
        ('ausente', 'Ausente'),
        ('tardanza', 'Tardanza'),
    ]
    
    # Multi-Tenant: Escuela
    
    estudiante = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='asistencias')
    materia = models.ForeignKey('Materia', on_delete=models.CASCADE, related_name='asistencias')
    fecha = models.DateField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='presente')
    observaciones = models.TextField(blank=True, null=True)
    registrado_por = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='asistencias_registradas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'
        unique_together = ['estudiante', 'materia', 'fecha']
        indexes = [
            models.Index(fields=['fecha', 'materia']),
            models.Index(fields=['estudiante', 'fecha']),
        ]
        ordering = ['-fecha', 'estudiante__first_name']

    def __str__(self):
        return f"{self.estudiante.get_full_name()} - {self.materia.nombre} - {self.fecha} ({self.get_estado_display()})"


class AsistenciaPersonal(models.Model):
    """Modelo para registrar asistencia de profesores y personal administrativo"""
    ESTADO_CHOICES = [
        ('presente', 'Presente'),
        ('ausente', 'Ausente'),
        ('tardanza', 'Tardanza'),
        ('permiso', 'Permiso'),
    ]
    
    # Multi-Tenant: Escuela
    
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='asistencias_personal_usuarios', 
                                help_text='Usuario (Estudiante, Profesor o personal administrativo)')
    fecha = models.DateField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='presente')
    hora_entrada = models.TimeField(null=True, blank=True, help_text='Hora de entrada registrada')
    hora_salida = models.TimeField(null=True, blank=True, help_text='Hora de salida registrada')
    observaciones = models.TextField(blank=True, null=True)
    registrado_por = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, 
                                       related_name='asistencias_personal_registradas',
                                       help_text='Usuario que registrÃ³ la asistencia (Secretaria)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Asistencia Personal'
        verbose_name_plural = 'Asistencias Personal'
        unique_together = ['usuario', 'fecha']
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['usuario', 'fecha']),
            models.Index(fields=['estado']),
        ]
        ordering = ['-fecha', 'usuario__first_name']

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.fecha} ({self.get_estado_display()})"
    
    def get_horas_trabajadas(self):
        """Calcula las horas trabajadas si hay entrada y salida"""
        if self.hora_entrada and self.hora_salida:
            from datetime import datetime, timedelta
            entrada = datetime.combine(self.fecha, self.hora_entrada)
            salida = datetime.combine(self.fecha, self.hora_salida)
            if salida < entrada:
                salida += timedelta(days=1)
            delta = salida - entrada
            return delta.total_seconds() / 3600
        return None


# ===========================
# SISTEMA DE COBROS Y PAGOS
# ===========================

class ConceptoPago(models.Model):
    """Conceptos de pago: mensualidades, servicios, artÃ­culos, etc."""
    TIPO_CHOICES = [
        ('mensualidad', 'Mensualidad'),
        ('inscripcion', 'InscripciÃ³n'),
        ('transporte', 'Transporte'),
        ('articulo', 'ArtÃ­culo/PapelerÃ­a'),
        ('servicio', 'Servicio'),
        ('otro', 'Otro'),
    ]
    
    # Multi-Tenant: Escuela
    
    nombre = models.CharField(max_length=200, verbose_name="Nombre del concepto")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='mensualidad')
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto base")
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    es_estandar = models.BooleanField(default=False, verbose_name="Tarifa EstÃ¡ndar", 
                                       help_text="Se asignarÃ¡ automÃ¡ticamente a nuevos estudiantes")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Concepto de Pago"
        verbose_name_plural = "Conceptos de Pago"
        ordering = ['tipo', 'nombre']
    
    def __str__(self):
        # Para mensualidad, inscripciÃ³n y transporte, no mostrar el monto (viene de la tarifa del estudiante)
        if self.tipo in ['mensualidad', 'inscripcion', 'transporte']:
            return f"{self.get_tipo_display()} - {self.nombre}"
        return f"{self.get_tipo_display()} - {self.nombre} (RD${self.monto})"


class Pago(models.Model):
    """Registro de pagos realizados por estudiantes"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('parcial', 'Pago Parcial'),
        ('vencido', 'Vencido'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('tarjeta', 'Tarjeta'),
        ('cheque', 'Cheque'),
    ]
    
    # Multi-Tenant: Escuela
    
    estudiante = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='pagos',
        limit_choices_to={'rol': 'Estudiante'}
    )
    concepto = models.ForeignKey(ConceptoPago, on_delete=models.PROTECT, related_name='pagos')
    anho_escolar = models.ForeignKey(AnhoEscolar, on_delete=models.CASCADE, related_name='pagos')
    
    # InformaciÃ³n del pago
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, blank=True, null=True)
    
    # Fechas
    fecha_emision = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    fecha_pago = models.DateTimeField(blank=True, null=True)
    
    # Para mensualidades
    from django.core.validators import MinValueValidator, MaxValueValidator
    mes = models.IntegerField(blank=True, null=True, help_text="Mes del aÃ±o (1-12)", validators=[MinValueValidator(1), MaxValueValidator(12)])
    anio = models.IntegerField(blank=True, null=True)
    
    # InformaciÃ³n adicional
    observaciones = models.TextField(blank=True, null=True)
    recibo_numero = models.CharField(max_length=50, unique=True, blank=True, null=True)
    referencia = models.CharField(max_length=100, blank=True, null=True, help_text="NÃºmero de referencia/transacciÃ³n")
    
    # AuditorÃ­a
    registrado_por = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='pagos_registrados'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha_registro']
        indexes = [
            models.Index(fields=['estudiante', 'anho_escolar']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_emision']),
            models.Index(fields=['mes', 'anio']),
        ]
    
    def __str__(self):
        if self.mes:
            return f"{self.estudiante.get_full_name()} - {self.concepto.nombre} - Mes {self.mes}/{self.anio}"
        return f"{self.estudiante.get_full_name()} - {self.concepto.nombre}"
    
    def saldo_pendiente(self):
        """Calcula el saldo pendiente"""
        # El saldo pendiente nunca debe ser negativo
        return max(0, self.monto_total - self.monto_pagado)
    
    def esta_pagado(self):
        """Verifica si el pago estÃ¡ completado"""
        return self.monto_pagado >= self.monto_total
    
    def save(self, *args, **kwargs):
        # Actualizar estado segÃºn montos
        if self.monto_pagado >= self.monto_total:
            self.estado = 'pagado'
        elif self.monto_pagado > 0:
            self.estado = 'parcial'
        
        # Generar nÃºmero de recibo si no existe
        if not self.recibo_numero and self.estado == 'pagado':
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.recibo_numero = f"REC-{timestamp}-{self.id or ''}"
        
        super().save(*args, **kwargs)


class TarifaEstudiante(models.Model):
    """Tarifa personalizada asignada a un estudiante para mensualidades, inscripciÃ³n y transporte."""
    
    # Multi-Tenant: Escuela
    
    estudiante = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='tarifas', 
        limit_choices_to={'rol': 'Estudiante'}
    )
    concepto = models.ForeignKey(
        ConceptoPago, 
        on_delete=models.PROTECT,
        null=True,  # Temporal para migraciÃ³n
        blank=True,
        limit_choices_to={'tipo__in': ['mensualidad', 'inscripcion', 'transporte']},
        help_text='Solo conceptos de tipo mensualidad, inscripciÃ³n o transporte'
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='tarifas_creadas'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Campo para diferenciar distancias en transporte
    observaciones = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text='Ej: Transporte zona cercana, Transporte zona lejana'
    )
    
    # DÃ­a de vencimiento para cÃ¡lculo de mora (si null, usa el del grupo familiar)
    dia_vencimiento = models.IntegerField(
        default=None,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text='DÃ­a del mes para vencimiento de pago (1-31). Si no se especifica, usa el del grupo familiar.'
    )

    class Meta:
        unique_together = (('estudiante', 'concepto'),)
        verbose_name = 'Tarifa Estudiante'
        verbose_name_plural = 'Tarifas por Estudiante'
        ordering = ['estudiante', 'concepto']

    def __str__(self):
        obs = f" ({self.observaciones})" if self.observaciones else ""
        return f"{self.estudiante.get_full_name()} - {self.concepto.nombre} - RD${self.monto}{obs}"
    
    def get_dia_vencimiento(self):
        """Obtiene el dÃ­a de vencimiento, usa el del estudiante si estÃ¡ definido, sino el del grupo familiar."""
        if self.dia_vencimiento:
            return self.dia_vencimiento
        if self.estudiante.grupo_familiar:
            return self.estudiante.grupo_familiar.dia_vencimiento
        return 10  # Default si no tiene grupo familiar


# ===========================
# SISTEMA DE FACTURACIÃ“N
# ===========================

class Factura(models.Model):
    """Factura principal para ventas"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('parcial', 'Pago Parcial'),
        ('anulada', 'Anulada'),
        ('vencida', 'Vencida'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia Bancaria'),
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
        ('cheque', 'Cheque'),
        ('mixto', 'Mixto'),
    ]
    
    # Multi-Tenant: Empresa
    
    # Información básica
    numero_factura = models.CharField(max_length=50, unique=True, db_index=True)
    cliente = models.ForeignKey(
        CustomUser, 
        on_delete=models.PROTECT, 
        related_name='facturas_cliente',
        limit_choices_to={'rol': 'Cliente'},
        verbose_name="Cliente"
    )
    vendedor = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='facturas_vendedor',
        limit_choices_to={'rol': 'Vendedor'},
        verbose_name="Vendedor"
    )
    anho_escolar = models.ForeignKey(
        AnhoEscolar, 
        on_delete=models.CASCADE, 
        related_name='facturas',
        null=True,
        blank=True,
        help_text="DEPRECATED: Solo para compatibilidad con datos antiguos"
    )
    
    # Fechas
    fecha_emision = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    fecha_pago_completo = models.DateTimeField(blank=True, null=True)
    
    # Montos
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    impuesto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Estado y mÃ©todo de pago
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', db_index=True)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, blank=True, null=True)
    
    # InformaciÃ³n adicional
    observaciones = models.TextField(blank=True, null=True)
    notas_internas = models.TextField(blank=True, null=True)
    
    # AuditorÃ­a
    creado_por = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='facturas_creadas'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    anulado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='facturas_anuladas'
    )
    fecha_anulacion = models.DateTimeField(blank=True, null=True)
    motivo_anulacion = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['-fecha_emision']
        indexes = [
            models.Index(fields=['numero_factura']),
            models.Index(fields=['cliente', 'anho_escolar']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_emision']),
        ]
    
    def __str__(self):
        return f"Factura {self.numero_factura} - {self.cliente.get_full_name()}"
    
    @property
    def saldo_pendiente(self):
        """Calcula el saldo pendiente de la factura"""
        # El saldo pendiente nunca debe ser negativo
        # Si el monto pagado es mayor al total, el saldo es 0
        return max(0, self.total - self.monto_pagado)
    
    def esta_pagada(self):
        """Verifica si la factura estÃ¡ completamente pagada"""
        return self.monto_pagado >= self.total
    
    def esta_vencida(self):
        """Verifica si la factura estÃ¡ vencida"""
        if not self.fecha_vencimiento:
            return False
        from datetime import date
        return date.today() > self.fecha_vencimiento and self.estado not in ['pagada', 'anulada']
    
    def calcular_mora(self):
        """
        Calcula el monto de mora si la factura estÃ¡ vencida.
        Retorna un diccionario con el monto y el porcentaje aplicado.
        """
        if not self.esta_vencida():
            return {'monto': 0, 'porcentaje': 0}
        
        # Obtener el porcentaje de mora del estudiante
        porcentaje_mora = self.cliente.get_porcentaje_mora()
        if porcentaje_mora <= 0:
            return {'monto': 0, 'porcentaje': 0}
        
        # Calcular mora sobre el subtotal (antes de descuentos e impuestos)
        from decimal import Decimal
        monto_mora = (self.subtotal * porcentaje_mora) / Decimal('100')
        
        return {
            'monto': monto_mora,
            'porcentaje': porcentaje_mora
        }
    
    def calcular_totales(self):
        """Recalcula los totales de la factura basÃ¡ndose en los detalles"""
        detalles = self.detalles.all()
        self.subtotal = sum(detalle.get_total() for detalle in detalles)
        self.total = self.subtotal - self.descuento + self.impuesto
        # NO guardar aquÃ­ para evitar recursiÃ³n, el guardado debe hacerse desde donde se llama
        
    def actualizar_estado(self):
        """Actualiza el estado de la factura segÃºn el monto pagado"""
        if self.estado == 'anulada':
            return
        
        if self.monto_pagado >= self.total:
            self.estado = 'pagada'
            if not self.fecha_pago_completo:
                from django.utils import timezone
                self.fecha_pago_completo = timezone.now()
        elif self.monto_pagado > 0:
            self.estado = 'parcial'
        else:
            self.estado = 'pendiente'
    
    def save(self, *args, **kwargs):
        # Generar número de factura si no existe
        if not self.numero_factura:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            ultimo = Factura.objects.filter(numero_factura__startswith='FAC-').count()
            self.numero_factura = f"FAC-{timestamp}-{ultimo + 1:05d}"
        
        # Guardar la factura
        es_nueva = self.pk is None
        super().save(*args, **kwargs)
        
        # Calcular comisión automáticamente si hay vendedor y es factura nueva
        if es_nueva and self.vendedor and self.vendedor.comision_vendedor > 0:
            self.crear_comision()
    
    def crear_comision(self):
        """Crea registro de comisión para el vendedor"""
        if not self.vendedor or self.vendedor.comision_vendedor <= 0:
            return None
        
        # Verificar que no exista ya una comisión
        if self.comisiones.exists():
            return self.comisiones.first()
        
        monto_comision = (self.total * self.vendedor.comision_vendedor) / Decimal('100')
        
        comision = ComisionVendedor.objects.create(
            vendedor=self.vendedor,
            factura=self,
            monto_venta=self.total,
            porcentaje_comision=self.vendedor.comision_vendedor,
            monto_comision=monto_comision,
            estado='pendiente'
        )
        
        return comision


class DetalleFactura(models.Model):
    """Detalle de items/conceptos de una factura"""
    # Multi-Tenant: Escuela
    
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='detalles')
    mensualidad = models.ForeignKey('Mensualidad', on_delete=models.SET_NULL, null=True, blank=True, related_name='detalles')
    concepto = models.ForeignKey(ConceptoPago, on_delete=models.PROTECT, null=True, blank=True)
    articulo = models.ForeignKey('Articulo', on_delete=models.PROTECT, null=True, blank=True, 
                                  related_name='detalles_factura',
                                  help_text='ArtÃ­culo del inventario (si aplica)')
    
    # InformaciÃ³n del item
    descripcion = models.CharField(max_length=255, help_text="DescripciÃ³n del concepto")
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Para mensualidades
    mes = models.IntegerField(blank=True, null=True, help_text="Mes del aÃ±o (1-12)")
    anio = models.IntegerField(blank=True, null=True)
    
    # InformaciÃ³n adicional
    observaciones = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Detalle de Factura"
        verbose_name_plural = "Detalles de Factura"
        ordering = ['id']
    
    def __str__(self):
        mes_info = f" - Mes {self.mes}/{self.anio}" if self.mes else ""
        return f"{self.factura.numero_factura} - {self.descripcion}{mes_info}"
    
    def get_subtotal(self):
        """Calcula subtotal antes del descuento"""
        return self.cantidad * self.precio_unitario
    
    def get_total(self):
        """Calcula total del detalle con descuento aplicado"""
        return self.get_subtotal() - self.descuento
    
    def save(self, *args, **kwargs):
        # Si estÃ¡ vinculada a una Mensualidad, sincronizar mes/anio y validar
        if self.mensualidad:
            try:
                m = self.mensualidad
                # Si se proporcionaron mes/anio explÃ­citos y no coinciden, lanzar error
                if self.mes is not None and self.anio is not None:
                    if int(self.mes) != int(m.mes) or int(self.anio) != int(m.anio):
                        from django.core.exceptions import ValidationError
                        raise ValidationError('El mes/aÃ±o del detalle no coincide con la Mensualidad vinculada.')
                # Copiar valores desde Mensualidad
                self.mes = m.mes
                self.anio = m.anio
            except Exception:
                # No interrumpir el guardado por errores en la sincronizaciÃ³n; permitir que se loguee posteriormente
                pass

        # Usar descripciÃ³n del concepto o artÃ­culo si no se proporciona
        if not self.descripcion:
            if self.concepto:
                self.descripcion = self.concepto.nombre
            elif self.articulo:
                self.descripcion = self.articulo.nombre

        # Guardar primero el detalle
        super().save(*args, **kwargs)

        # Actualizar totales de la factura (sin recursiÃ³n)
        if hasattr(self, 'factura') and self.factura:
            self.factura.calcular_totales()
            # Usar update para evitar disparar save() de nuevo
            Factura.objects.filter(pk=self.factura.pk).update(
                subtotal=self.factura.subtotal,
                total=self.factura.total
            )


class PagoFactura(models.Model):
    """Registro de pagos/abonos realizados contra una factura"""
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia Bancaria'),
        ('tarjeta', 'Tarjeta de CrÃ©dito/DÃ©bito'),
        ('cheque', 'Cheque'),
    ]
    
    # Multi-Tenant: Escuela
    
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='pagos')
    
    # InformaciÃ³n del pago
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    
    # Detalles del pago
    referencia = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="NÃºmero de referencia/transacciÃ³n/cheque"
    )
    banco = models.CharField(max_length=100, blank=True, null=True)
    numero_recibo = models.CharField(max_length=50, unique=True, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    
    # AuditorÃ­a
    registrado_por = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='pagos_factura_registrados'
    )
    
    class Meta:
        verbose_name = "Pago de Factura"
        verbose_name_plural = "Pagos de Facturas"
        ordering = ['-fecha_pago']
        indexes = [
            models.Index(fields=['factura', 'fecha_pago']),
            models.Index(fields=['metodo_pago']),
        ]
    
    def __str__(self):
        return f"Pago {self.numero_recibo or self.id} - {self.factura.numero_factura} - RD${self.monto}"
    
    def save(self, *args, **kwargs):
        # Generar nÃºmero de recibo si no existe
        if not self.numero_recibo:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.numero_recibo = f"REC-{timestamp}-{self.id or ''}"
        
        super().save(*args, **kwargs)
        
        # Actualizar monto pagado en la factura
        self.factura.monto_pagado = sum(
            pago.monto for pago in self.factura.pagos.all()
        )
        self.factura.actualizar_estado()
        self.factura.save()

        # Si la factura quedÃ³ pagada, marcar mensualidades asociadas como pagadas
        try:
            from django.utils import timezone
            if self.factura.estado == 'pagada':
                for m in self.factura.mensualidades.all():
                    try:
                        m.marcar_pagada(self.factura)
                    except Exception:
                        m.estado = 'pagada'
                        m.fecha_pagado = timezone.now()
                        m.factura = self.factura
                        m.save()
            else:
                # Si factura parcial, marcar mensualidades como parcial
                if self.factura.monto_pagado and self.factura.monto_pagado > 0:
                    for m in self.factura.mensualidades.all():
                        m.estado = 'parcial'
                        m.save()
        except Exception:
            pass


class CodigoAnulacion(models.Model):
    """CÃ³digo de seguridad mensual para anular facturas"""
    # Multi-Tenant: Escuela
    
    mes = models.IntegerField()  # 1-12
    anio = models.IntegerField()  # 2026, 2027, etc.
    codigo = models.CharField(max_length=10)
    creado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "CÃ³digo de AnulaciÃ³n"
        verbose_name_plural = "CÃ³digos de AnulaciÃ³n"
        unique_together = ['mes', 'anio']
        ordering = ['-anio', '-mes']
    
    def __str__(self):
        from datetime import date
        try:
            mes_nombre = date(self.anio, self.mes, 1).strftime('%B %Y')
            return f"CÃ³digo {mes_nombre}: {self.codigo}"
        except:
            return f"CÃ³digo {self.mes}/{self.anio}: {self.codigo}"
    
    @staticmethod
    def generar_codigo():
        """Genera un cÃ³digo aleatorio de 8 caracteres (letras y nÃºmeros)"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    @staticmethod
    def obtener_codigo_actual():
        """Obtiene o crea el cÃ³digo del mes actual"""
        from datetime import date
        hoy = date.today()
        codigo, created = CodigoAnulacion.objects.get_or_create(
            mes=hoy.month,
            anio=hoy.year,
            defaults={'codigo': CodigoAnulacion.generar_codigo()}
        )
        return codigo
    
    @staticmethod
    def validar_codigo(codigo_ingresado):
        """Valida si el cÃ³digo ingresado es correcto para el mes actual"""
        codigo_actual = CodigoAnulacion.obtener_codigo_actual()
        return codigo_ingresado.upper().strip() == codigo_actual.codigo.upper().strip()


class CategoriaArticulo(models.Model):
    """CategorÃ­as para organizar artÃ­culos del inventario"""
    # Multi-Tenant: Escuela
    
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activa = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "CategorÃ­a de ArtÃ­culo"
        verbose_name_plural = "CategorÃ­as de ArtÃ­culos"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Articulo(models.Model):
    """ArtÃ­culos del inventario para usar en facturas"""
    TIPO_CHOICES = [
        ('producto', 'Producto'),
        ('servicio', 'Servicio'),
    ]
    
    # Multi-Tenant: Escuela
    
    codigo_barras = models.CharField(max_length=100, unique=True, blank=True, default='',
                                      help_text='CÃ³digo de barras para lector Ã³ptico')
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(CategoriaArticulo, on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='articulos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='producto')
    
    # Precios
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    precio_minimo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Inventario (solo para productos)
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)
    stock_maximo = models.IntegerField(null=True, blank=True)
    unidad_medida = models.CharField(max_length=20, default='unidad',
                                      help_text='Ej: unidad, caja, kg, litro')
    
    # Control
    activo = models.BooleanField(default=True)
    permite_descuento = models.BooleanField(default=True)
    aplica_itbis = models.BooleanField(default=False, verbose_name='Aplica ITBIS')
    
    # Fechas
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, 
                                    null=True, related_name='articulos_creados')
    
    class Meta:
        verbose_name = "ArtÃ­culo"
        verbose_name_plural = "ArtÃ­culos"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['codigo_barras']),
            models.Index(fields=['nombre']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.codigo_barras} - {self.nombre}"
    
    def save(self, *args, **kwargs):
        # Generar cÃ³digo de barras automÃ¡tico si no existe
        if not self.codigo_barras:
            from datetime import datetime
            import random
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_suffix = random.randint(100, 999)
            self.codigo_barras = f"ART{timestamp}{random_suffix}"
        super().save(*args, **kwargs)
    
    @property
    def stock_bajo(self):
        """Indica si el stock estÃ¡ por debajo del mÃ­nimo"""
        return self.stock_actual <= self.stock_minimo
    
    @property
    def margen_ganancia(self):
        """Calcula el margen de ganancia porcentual"""
        if self.precio_compra > 0:
            return ((self.precio_venta - self.precio_compra) / self.precio_compra) * 100
        return 0
    
    def ajustar_stock(self, cantidad, tipo='entrada'):
        """Ajusta el stock del artÃ­culo"""
        if tipo == 'entrada':
            self.stock_actual += cantidad
        elif tipo == 'salida':
            if self.stock_actual >= cantidad:
                self.stock_actual -= cantidad
            else:
                raise ValueError(f"Stock insuficiente. Disponible: {self.stock_actual}")
        self.save()


class MovimientoInventario(models.Model):
    """Registro de movimientos del inventario"""
    TIPO_MOVIMIENTO = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
        ('devolucion', 'DevoluciÃ³n'),
    ]
    
    # Multi-Tenant: Escuela
    
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO)
    cantidad = models.IntegerField()
    stock_anterior = models.IntegerField()
    stock_nuevo = models.IntegerField()
    motivo = models.TextField()
    
    # Referencia a factura si aplica
    factura = models.ForeignKey('Factura', on_delete=models.SET_NULL, 
                                 null=True, blank=True, related_name='movimientos_inventario')
    
    # Control
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, 
                                 null=True, related_name='movimientos_inventario')
    
    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.articulo.nombre} ({self.cantidad})"


# ==============================
#   MODELOS DE VENTAS
# ==============================

class Cotizacion(models.Model):
    """Cotizaciones para clientes antes de generar factura"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('convertida', 'Convertida a Factura'),
        ('vencida', 'Vencida'),
    ]
    
    # Multi-Tenant: Empresa
    
    numero_cotizacion = models.CharField(max_length=50, unique=True, db_index=True)
    cliente = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='cotizaciones_cliente',
        limit_choices_to={'rol': 'Cliente'}
    )
    vendedor = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cotizaciones_vendedor',
        limit_choices_to={'rol': 'Vendedor'}
    )
    
    fecha_cotizacion = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField()
    valida_hasta = models.DateField(help_text="Fecha hasta la cual es válida la cotización")
    
    # Montos
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    itbis = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', db_index=True)
    
    # Referencia a factura si se convierte
    factura_generada = models.ForeignKey(
        'Factura',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cotizacion_origen'
    )
    
    # Notas y observaciones
    notas = models.TextField(blank=True, null=True)
    condiciones_pago = models.TextField(blank=True, null=True)
    
    # Auditoría
    creado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cotizaciones_creadas'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        ordering = ['-fecha_cotizacion']
        indexes = [
            models.Index(fields=['numero_cotizacion']),
            models.Index(fields=['cliente', 'estado']),
            models.Index(fields=['vendedor', 'fecha_cotizacion']),
        ]
    
    def __str__(self):
        return f"COT-{self.numero_cotizacion} - {self.cliente.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.numero_cotizacion:
            # Generar número de cotización automático
            from datetime import datetime
            ultimo_numero = Cotizacion.objects.filter(
                numero_cotizacion__startswith=datetime.now().strftime('%Y')
            ).count() + 1
            self.numero_cotizacion = f"{datetime.now().strftime('%Y')}{ultimo_numero:05d}"
        
        # Calcular totales
        self.calcular_totales()
        super().save(*args, **kwargs)
    
    def calcular_totales(self):
        """Calcula subtotal, itbis y total"""
        detalles = self.detalles.all()
        self.subtotal = sum(detalle.subtotal for detalle in detalles)
        self.subtotal -= self.descuento
        self.itbis = self.subtotal * Decimal('0.18')  # 18% ITBIS
        self.total = self.subtotal + self.itbis
    
    def convertir_a_factura(self, usuario):
        """Convierte la cotización en factura"""
        from django.utils import timezone
        
        if self.estado == 'convertida':
            raise ValueError("Esta cotización ya fue convertida a factura")
        
        # Crear factura
        factura = Factura.objects.create(
            cliente=self.cliente,
            vendedor=self.vendedor,
            subtotal=self.subtotal,
            descuento=self.descuento,
            itbis=self.itbis,
            total=self.total,
            saldo=self.total,
            estado='pendiente',
            fecha_emision=timezone.now().date(),
            fecha_vencimiento=self.fecha_vencimiento,
            creado_por=usuario,
            notas=f"Generada desde cotización {self.numero_cotizacion}"
        )
        
        # Copiar detalles
        for detalle_cot in self.detalles.all():
            DetalleFactura.objects.create(
                factura=factura,
                articulo=detalle_cot.articulo,
                descripcion=detalle_cot.descripcion,
                cantidad=detalle_cot.cantidad,
                precio_unitario=detalle_cot.precio_unitario,
                descuento=detalle_cot.descuento,
                subtotal=detalle_cot.subtotal
            )
        
        # Actualizar cotización
        self.estado = 'convertida'
        self.factura_generada = factura
        self.save()
        
        return factura


class DetalleCotizacion(models.Model):
    """Detalle de productos/servicios en cotización"""
    # Multi-Tenant: Empresa
    
    cotizacion = models.ForeignKey(
        Cotizacion,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    articulo = models.ForeignKey(
        Articulo,
        on_delete=models.PROTECT,
        related_name='detalles_cotizacion'
    )
    descripcion = models.CharField(max_length=500)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        verbose_name = "Detalle de Cotización"
        verbose_name_plural = "Detalles de Cotización"
        ordering = ['id']
    
    def __str__(self):
        return f"{self.cotizacion.numero_cotizacion} - {self.articulo.nombre}"
    
    def save(self, *args, **kwargs):
        # Calcular subtotal
        self.subtotal = (self.cantidad * self.precio_unitario) - self.descuento
        super().save(*args, **kwargs)
        
        # Actualizar totales de la cotización
        self.cotizacion.calcular_totales()
        self.cotizacion.save()


class ComisionVendedor(models.Model):
    """Registro de comisiones de vendedores"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('pagada', 'Pagada'),
        ('cancelada', 'Cancelada'),
    ]
    
    # Multi-Tenant: Empresa
    
    vendedor = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='comisiones',
        limit_choices_to={'rol': 'Vendedor'}
    )
    factura = models.ForeignKey(
        'Factura',
        on_delete=models.CASCADE,
        related_name='comisiones'
    )
    
    monto_venta = models.DecimalField(max_digits=12, decimal_places=2)
    porcentaje_comision = models.DecimalField(max_digits=5, decimal_places=2)
    monto_comision = models.DecimalField(max_digits=12, decimal_places=2)
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    fecha_calculo = models.DateTimeField(auto_now_add=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    
    aprobado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comisiones_aprobadas'
    )
    
    notas = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Comisión de Vendedor"
        verbose_name_plural = "Comisiones de Vendedores"
        ordering = ['-fecha_calculo']
        indexes = [
            models.Index(fields=['vendedor', 'estado']),
            models.Index(fields=['factura']),
        ]
    
    def __str__(self):
        return f"{self.vendedor.get_full_name()} - RD${self.monto_comision}"
    
    def aprobar(self, usuario):
        """Aprueba la comisión"""
        from django.utils import timezone
        self.estado = 'aprobada'
        self.fecha_aprobacion = timezone.now()
        self.aprobado_por = usuario
        self.save()
    
    def marcar_pagada(self):
        """Marca la comisión como pagada"""
        from django.utils import timezone
        self.estado = 'pagada'
        self.fecha_pago = timezone.now()
        self.save()


class MetaVendedor(models.Model):
    """Metas mensuales de vendedores"""
    # Multi-Tenant: Empresa
    
    vendedor = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='metas',
        limit_choices_to={'rol': 'Vendedor'}
    )
    
    mes = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    anio = models.IntegerField()
    
    meta_monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Meta en Monto",
        help_text="Meta de ventas en dinero para el mes"
    )
    meta_cantidad = models.IntegerField(
        default=0,
        verbose_name="Meta en Cantidad",
        help_text="Meta de cantidad de facturas/ventas"
    )
    
    monto_alcanzado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Monto Alcanzado"
    )
    cantidad_alcanzada = models.IntegerField(
        default=0,
        verbose_name="Cantidad Alcanzada"
    )
    
    notas = models.TextField(blank=True, null=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Meta de Vendedor"
        verbose_name_plural = "Metas de Vendedores"
        unique_together = ('vendedor', 'mes', 'anio')
        ordering = ['-anio', '-mes']
        indexes = [
            models.Index(fields=['vendedor', 'anio', 'mes']),
        ]
    
    def __str__(self):
        return f"{self.vendedor.get_full_name()} - {self.mes}/{self.anio}"
    
    @property
    def porcentaje_cumplimiento_monto(self):
        """Calcula el porcentaje de cumplimiento en monto"""
        if self.meta_monto > 0:
            return (self.monto_alcanzado / self.meta_monto) * 100
        return 0
    
    @property
    def porcentaje_cumplimiento_cantidad(self):
        """Calcula el porcentaje de cumplimiento en cantidad"""
        if self.meta_cantidad > 0:
            return (self.cantidad_alcanzada / self.meta_cantidad) * 100
        return 0
    
    def actualizar_progreso(self):
        """Actualiza el progreso de ventas del mes"""
        from django.db.models import Sum, Count
        from datetime import date
        
        # Calcular ventas del mes
        inicio_mes = date(self.anio, self.mes, 1)
        if self.mes == 12:
            fin_mes = date(self.anio + 1, 1, 1)
        else:
            fin_mes = date(self.anio, self.mes + 1, 1)
        
        ventas = Factura.objects.filter(
            vendedor=self.vendedor,
            fecha_emision__gte=inicio_mes,
            fecha_emision__lt=fin_mes,
            estado__in=['pagada', 'pendiente', 'parcial']
        ).aggregate(
            total_monto=Sum('total'),
            total_cantidad=Count('id')
        )
        
        self.monto_alcanzado = ventas['total_monto'] or 0
        self.cantidad_alcanzada = ventas['total_cantidad'] or 0
        self.save()



class ClienteCorporativo(models.Model):
    """Clientes corporativos o empresas para ventas consolidadas"""
    # Multi-Tenant: Empresa
    

    # Multi-Tenant Manager
    codigo_cliente = models.CharField(
        max_length=50, 
        unique=True, 
        db_index=True,
        verbose_name="Código de Cliente",
        help_text="Código único para identificar el cliente corporativo (ej: CORP001, EMPRESA2024)"
    )
    nombre_empresa = models.CharField(
        max_length=200,
        verbose_name="Nombre de la Empresa",
        help_text="Razón social o nombre comercial"
    )
    rnc = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name="RNC",
        help_text="Registro Nacional de Contribuyentes"
    )
    contacto_principal = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empresas_contacto',
        verbose_name="Contacto Principal",
        help_text="Persona responsable de contacto y pagos"
    )
    
    # Información de contacto
    telefono_contacto = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        verbose_name="Teléfono de Contacto"
    )
    email_contacto = models.EmailField(
        blank=True, 
        null=True,
        verbose_name="Email de Contacto"
    )
    direccion = models.TextField(blank=True, null=True)
    sitio_web = models.URLField(blank=True, null=True)
    
    # Configuración comercial
    descuento_general = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Descuento General (%)",
        help_text="Descuento porcentual aplicado a todas las compras"
    )
    limite_credito = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Límite de Crédito",
        help_text="Límite de crédito corporativo"
    )
    dias_credito = models.IntegerField(
        default=30,
        verbose_name="Días de Crédito",
        help_text="Cantidad de días de crédito otorgado"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el cliente corporativo está activo"
    )
    
    # Información adicional
    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas",
        help_text="Información adicional sobre el cliente"
    )
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='clientes_corporativos_creados'
    )
    
    class Meta:
        verbose_name = "Cliente Corporativo"
        verbose_name_plural = "Clientes Corporativos"
        ordering = ['nombre_empresa', 'codigo_cliente']
        indexes = [
            models.Index(fields=['codigo_cliente']),
            models.Index(fields=['nombre_empresa']),
            models.Index(fields=['rnc']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.nombre_empresa} ({self.codigo_cliente})"
    
    @property
    def cantidad_clientes(self):
        """Retorna la cantidad de clientes asociados"""
        return self.clientes.filter(rol='Cliente', is_active=True).count()
    
    def get_clientes_activos(self):
        """Retorna queryset de clientes activos"""
        return self.clientes.filter(rol='Cliente', is_active=True)
    
    def get_credito_disponible(self):
        """Calcula el crédito disponible restando el saldo pendiente"""
        from django.db.models import Sum, Q
        
        # Sumar saldos pendientes de todos los clientes asociados
        saldo_pendiente = 0
        for cliente in self.get_clientes_activos():
            facturas_pendientes = cliente.facturas_cliente.filter(
                Q(estado='pendiente') | Q(estado='parcial')
            ).aggregate(total=Sum('saldo'))['total'] or 0
            saldo_pendiente += facturas_pendientes
        
        return max(0, self.limite_credito - saldo_pendiente)


class GrupoFamiliar(models.Model):
    """DEPRECATED: Usar ClienteCorporativo en su lugar.
    Se mantiene temporalmente para compatibilidad con datos existentes."""
    # Multi-Tenant: Escuela
    

    # Multi-Tenant Manager
    codigo_familia = models.CharField(
        max_length=50, 
        unique=True, 
        db_index=True,
        verbose_name="Código de Familia",
        help_text="Código único para identificar la familia (ej: FAM001, GONZALEZ2024)"
    )
    apellido_familia = models.CharField(
        max_length=100,
        verbose_name="Apellido de la Familia",
        help_text="Apellido principal o nombre de la familia"
    )
    responsable_pago = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='familias_responsable',
        verbose_name="Responsable de Pago",
        help_text="Persona responsable de realizar los pagos (padre/madre/tutor)"
    )
    
    # Información de contacto del responsable
    telefono_contacto = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        verbose_name="Teléfono de Contacto"
    )
    email_contacto = models.EmailField(
        blank=True, 
        null=True,
        verbose_name="Email de Contacto"
    )
    direccion = models.TextField(blank=True, null=True)
    
    # Configuración de pagos
    descuento_general = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Descuento General (%)",
        help_text="Descuento porcentual aplicado a todos los pagos de la familia"
    )
    porcentaje_mora = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Porcentaje de Mora (%)",
        help_text="Porcentaje de recargo aplicado cuando el pago está vencido"
    )
    dia_vencimiento = models.IntegerField(
        default=10,
        verbose_name="Día de Vencimiento",
        help_text="Día del mes en que vencen las mensualidades (1-31)"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el grupo familiar está activo"
    )
    
    # Información adicional
    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas",
        help_text="Información adicional sobre la familia"
    )
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='familias_creadas'
    )
    
    class Meta:
        verbose_name = "Grupo Familiar"
        verbose_name_plural = "Grupos Familiares"
        ordering = ['apellido_familia', 'codigo_familia']
        indexes = [
            models.Index(fields=['codigo_familia']),
            models.Index(fields=['apellido_familia']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.apellido_familia} ({self.codigo_familia})"
    
    @property
    def cantidad_estudiantes(self):
        """Retorna la cantidad de estudiantes en el grupo familiar"""
        return self.estudiantes.filter(rol='Estudiante', is_active=True).count()
    
    def get_estudiantes_activos(self):
        """Retorna queryset de estudiantes activos en la familia"""
        return self.estudiantes.filter(rol='Estudiante', is_active=True)
    
    def calcular_total_mensualidad(self, mes, anio):
        """Calcula el total de mensualidades para todos los estudiantes de la familia"""
        from decimal import Decimal
        total = Decimal('0.00')
        estudiantes = self.get_estudiantes_activos()
        
        for estudiante in estudiantes:
            # Obtener la tarifa de mensualidad del estudiante
            if hasattr(estudiante, 'mensualidad') and estudiante.mensualidad:
                total += estudiante.mensualidad
        
        # Aplicar descuento general si existe
        if self.descuento_general > 0:
            descuento = total * (self.descuento_general / 100)
            total -= descuento
        
        return total


# ============================================
# MÃ“DULO DE CONTABILIDAD
# ============================================

class PlanCuentas(models.Model):
    """
    Plan de Cuentas Contable - CatÃ¡logo de cuentas contables
    Este modelo representa el catÃ¡logo de cuentas utilizado para registrar
    todas las operaciones contables de la instituciÃ³n.
    """
    
    TIPO_CUENTA_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('PASIVO', 'Pasivo'),
        ('CAPITAL', 'Capital / Patrimonio'),
        ('INGRESO', 'Ingreso'),
        ('GASTO', 'Gasto'),
        ('COSTO', 'Costo'),
    ]
    
    NATURALEZA_CHOICES = [
        ('DEUDORA', 'Deudora'),
        ('ACREEDORA', 'Acreedora'),
    ]
    
    # Multi-Tenant: Escuela
    

    # Multi-Tenant Manager
    codigo = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name="CÃ³digo de Cuenta",
        help_text="CÃ³digo Ãºnico de la cuenta (ej: 1.1.01.001)"
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre de la Cuenta",
        help_text="Nombre descriptivo de la cuenta contable"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="DescripciÃ³n",
        help_text="DescripciÃ³n detallada del uso de esta cuenta"
    )
    
    tipo_cuenta = models.CharField(
        max_length=10,
        choices=TIPO_CUENTA_CHOICES,
        verbose_name="Tipo de Cuenta",
        help_text="ClasificaciÃ³n principal de la cuenta"
    )
    
    naturaleza = models.CharField(
        max_length=10,
        choices=NATURALEZA_CHOICES,
        verbose_name="Naturaleza",
        help_text="Naturaleza contable de la cuenta (Deudora o Acreedora)"
    )
    
    nivel = models.IntegerField(
        default=1,
        verbose_name="Nivel",
        help_text="Nivel jerÃ¡rquico de la cuenta (1=Mayor, 2=Submayer, 3=Auxiliar, etc.)"
    )
    
    cuenta_padre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcuentas',
        verbose_name="Cuenta Padre",
        help_text="Cuenta superior en la jerarquÃ­a"
    )
    
    es_detalle = models.BooleanField(
        default=True,
        verbose_name="Es Cuenta de Detalle",
        help_text="Indica si la cuenta acepta movimientos directos (True) o es solo agrupadora (False)"
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si la cuenta estÃ¡ activa para uso"
    )
    
    # Campos de control
    saldo_inicial = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Inicial",
        help_text="Saldo inicial de la cuenta al inicio del perÃ­odo contable"
    )
    
    saldo_actual = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Actual",
        help_text="Saldo actual de la cuenta"
    )
    
    # Campos de auditorÃ­a
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cuentas_creadas',
        verbose_name="Creado Por"
    )
    modificado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cuentas_modificadas',
        verbose_name="Modificado Por"
    )
    
    # Configuraciones especiales
    requiere_centro_costo = models.BooleanField(
        default=False,
        verbose_name="Requiere Centro de Costo",
        help_text="Indica si los movimientos en esta cuenta requieren especificar un centro de costo"
    )
    
    requiere_tercero = models.BooleanField(
        default=False,
        verbose_name="Requiere Tercero",
        help_text="Indica si los movimientos requieren especificar un tercero (cliente/proveedor)"
    )
    
    class Meta:
        verbose_name = "Cuenta Contable"
        verbose_name_plural = "Plan de Cuentas"
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['tipo_cuenta']),
            models.Index(fields=['activo']),
            models.Index(fields=['es_detalle']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def save(self, *args, **kwargs):
        """Override save para calcular el nivel automÃ¡ticamente basado en el cÃ³digo"""
        # Calcular nivel basado en los puntos en el cÃ³digo
        self.nivel = self.codigo.count('.') + 1
        
        # Establecer naturaleza por defecto segÃºn tipo de cuenta
        if not self.naturaleza:
            if self.tipo_cuenta in ['ACTIVO', 'GASTO', 'COSTO']:
                self.naturaleza = 'DEUDORA'
            else:
                self.naturaleza = 'ACREEDORA'
        
        super().save(*args, **kwargs)
    
    def get_codigo_completo(self):
        """Retorna el cÃ³digo completo con padding para ordenamiento"""
        return self.codigo.ljust(20, '0')
    
    def get_saldo_formateado(self):
        """Retorna el saldo formateado con el sÃ­mbolo de moneda"""
        return f"${self.saldo_actual:,.2f}"
    
    def tiene_movimientos(self):
        """Verifica si la cuenta tiene movimientos asociados"""
        return self.movimientos_debito.exists() or self.movimientos_credito.exists()
    
    def puede_eliminarse(self):
        """Verifica si la cuenta puede ser eliminada"""
        return not self.tiene_movimientos() and not self.subcuentas.exists()
    
    def get_ruta_completa(self):
        """Retorna la ruta completa de la cuenta en la jerarquÃ­a"""
        if self.cuenta_padre:
            return f"{self.cuenta_padre.get_ruta_completa()} > {self.nombre}"
        return self.nombre
    
    def get_subcuentas_activas(self):
        """Retorna todas las subcuentas activas"""
        return self.subcuentas.filter(activo=True)
    
    def calcular_saldo(self):
        """Calcula el saldo actual basado en los movimientos"""
        from django.db.models import Sum
        from decimal import Decimal
        
        # Obtener suma de dÃ©bitos y crÃ©ditos
        total_debito = self.movimientos_debito.aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        total_credito = self.movimientos_credito.aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        # Calcular saldo segÃºn naturaleza
        if self.naturaleza == 'DEUDORA':
            saldo = self.saldo_inicial + total_debito - total_credito
        else:
            saldo = self.saldo_inicial + total_credito - total_debito
        
        return saldo


class AsientoContable(models.Model):
    """
    Asiento Contable - Registro de transacciones contables
    Representa la cabecera de un asiento contable que agrupa varios movimientos
    bajo el principio de partida doble (dÃ©bitos = crÃ©ditos)
    """
    
    TIPO_ASIENTO_CHOICES = [
        ('APERTURA', 'Asiento de Apertura'),
        ('DIARIO', 'Asiento de Diario'),
        ('AJUSTE', 'Asiento de Ajuste'),
        ('CIERRE', 'Asiento de Cierre'),
        ('TRASPASO', 'Asiento de Traspaso'),
    ]
    
    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('CONTABILIZADO', 'Contabilizado'),
        ('ANULADO', 'Anulado'),
    ]
    
    # Multi-Tenant: Escuela
    

    # Multi-Tenant Manager
    numero_asiento = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name="NÃºmero de Asiento",
        help_text="NÃºmero Ãºnico del asiento (ej: ASI-2026-001)"
    )
    
    fecha_asiento = models.DateField(
        verbose_name="Fecha del Asiento",
        help_text="Fecha en que se registra el asiento contable",
        db_index=True
    )
    
    tipo_asiento = models.CharField(
        max_length=15,
        choices=TIPO_ASIENTO_CHOICES,
        default='DIARIO',
        verbose_name="Tipo de Asiento",
        help_text="ClasificaciÃ³n del asiento contable"
    )
    
    concepto = models.TextField(
        verbose_name="Concepto/DescripciÃ³n",
        help_text="DescripciÃ³n general del asiento contable"
    )
    
    referencia = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Referencia",
        help_text="Referencia externa (nÃºmero de factura, recibo, etc.)"
    )
    
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='BORRADOR',
        verbose_name="Estado",
        help_text="Estado actual del asiento"
    )
    
    # Totales del asiento
    total_debito = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Total DÃ©bito",
        help_text="Suma total de los dÃ©bitos"
    )
    
    total_credito = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Total CrÃ©dito",
        help_text="Suma total de los crÃ©ditos"
    )
    
    # Campos de auditorÃ­a
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    fecha_contabilizacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de ContabilizaciÃ³n",
        help_text="Fecha en que se contabilizÃ³ el asiento"
    )
    
    creado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='asientos_creados',
        verbose_name="Creado Por"
    )
    
    modificado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asientos_modificados',
        verbose_name="Modificado Por"
    )
    
    contabilizado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asientos_contabilizados',
        verbose_name="Contabilizado Por"
    )
    
    anulado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asientos_anulados',
        verbose_name="Anulado Por"
    )
    
    motivo_anulacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motivo de AnulaciÃ³n",
        help_text="RazÃ³n por la cual se anulÃ³ el asiento"
    )
    
    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas",
        help_text="Notas adicionales sobre el asiento"
    )
    
    class Meta:
        verbose_name = "Asiento Contable"
        verbose_name_plural = "Asientos Contables"
        ordering = ['-fecha_asiento', '-numero_asiento']
        indexes = [
            models.Index(fields=['numero_asiento']),
            models.Index(fields=['fecha_asiento']),
            models.Index(fields=['estado']),
            models.Index(fields=['tipo_asiento']),
        ]
    
    def __str__(self):
        return f"{self.numero_asiento} - {self.concepto[:50]}"
    
    def esta_cuadrado(self):
        """Verifica si el asiento estÃ¡ cuadrado (dÃ©bito = crÃ©dito)"""
        return self.total_debito == self.total_credito
    
    def puede_contabilizarse(self):
        """Verifica si el asiento puede ser contabilizado"""
        return (
            self.estado == 'BORRADOR' and
            self.esta_cuadrado() and
            self.detalles.exists() and
            self.total_debito > 0
        )
    
    def puede_anularse(self):
        """Verifica si el asiento puede ser anulado"""
        return self.estado == 'CONTABILIZADO'
    
    def puede_editarse(self):
        """Verifica si el asiento puede ser editado"""
        return self.estado == 'BORRADOR'
    
    def calcular_totales(self):
        """Calcula los totales de dÃ©bito y crÃ©dito del asiento"""
        from django.db.models import Sum
        from decimal import Decimal
        
        totales = self.detalles.aggregate(
            debito=Sum('debito'),
            credito=Sum('credito')
        )
        
        self.total_debito = totales['debito'] or Decimal('0.00')
        self.total_credito = totales['credito'] or Decimal('0.00')
    
    def contabilizar(self, usuario):
        """Contabiliza el asiento y actualiza los saldos de las cuentas"""
        from django.utils import timezone
        
        if not self.puede_contabilizarse():
            raise ValueError("El asiento no puede ser contabilizado")
        
        # Actualizar saldos de las cuentas
        for detalle in self.detalles.all():
            cuenta = detalle.cuenta
            
            if cuenta.naturaleza == 'DEUDORA':
                cuenta.saldo_actual += detalle.debito - detalle.credito
            else:
                cuenta.saldo_actual += detalle.credito - detalle.debito
            
            cuenta.save()
        
        # Marcar como contabilizado
        self.estado = 'CONTABILIZADO'
        self.fecha_contabilizacion = timezone.now()
        self.contabilizado_por = usuario
        self.save()
    
    def anular(self, usuario, motivo):
        """Anula el asiento y revierte los saldos de las cuentas"""
        from django.utils import timezone
        
        if not self.puede_anularse():
            raise ValueError("El asiento no puede ser anulado")
        
        # Revertir saldos de las cuentas
        for detalle in self.detalles.all():
            cuenta = detalle.cuenta
            
            if cuenta.naturaleza == 'DEUDORA':
                cuenta.saldo_actual -= detalle.debito - detalle.credito
            else:
                cuenta.saldo_actual -= detalle.credito - detalle.debito
            
            cuenta.save()
        
        # Marcar como anulado
        self.estado = 'ANULADO'
        self.anulado_por = usuario
        self.motivo_anulacion = motivo
        self.save()
    
    def get_diferencia(self):
        """Retorna la diferencia entre dÃ©bito y crÃ©dito"""
        return self.total_debito - self.total_credito
    
    def get_estado_badge_class(self):
        """Retorna la clase CSS para el badge de estado"""
        clases = {
            'BORRADOR': 'warning',
            'CONTABILIZADO': 'success',
            'ANULADO': 'danger',
        }
        return clases.get(self.estado, 'secondary')


class DetalleAsiento(models.Model):
    """
    Detalle del Asiento Contable - Movimiento individual de una cuenta
    Cada lÃ­nea representa un dÃ©bito o crÃ©dito en una cuenta especÃ­fica
    """
    
    # Multi-Tenant: Escuela
    

    # Multi-Tenant Manager
    asiento = models.ForeignKey(
        AsientoContable,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Asiento Contable"
    )
    
    linea = models.IntegerField(
        default=1,
        verbose_name="LÃ­nea",
        help_text="NÃºmero de lÃ­nea dentro del asiento"
    )
    
    cuenta = models.ForeignKey(
        PlanCuentas,
        on_delete=models.PROTECT,
        related_name='movimientos_asiento',
        verbose_name="Cuenta Contable",
        limit_choices_to={'es_detalle': True, 'activo': True}
    )
    
    descripcion = models.CharField(
        max_length=255,
        verbose_name="DescripciÃ³n",
        help_text="DescripciÃ³n especÃ­fica de este movimiento"
    )
    
    debito = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="DÃ©bito",
        help_text="Monto del dÃ©bito"
    )
    
    credito = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="CrÃ©dito",
        help_text="Monto del crÃ©dito"
    )
    
    # Campos opcionales para trazabilidad
    centro_costo = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Centro de Costo",
        help_text="Centro de costo asociado (opcional)"
    )
    
    tercero = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_como_tercero',
        verbose_name="Tercero",
        help_text="Tercero asociado (cliente/proveedor)"
    )
    
    referencia_interna = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Referencia Interna",
        help_text="Referencia a otro documento (factura, recibo, etc.)"
    )
    
    class Meta:
        verbose_name = "Detalle de Asiento"
        verbose_name_plural = "Detalles de Asientos"
        ordering = ['asiento', 'linea']
        indexes = [
            models.Index(fields=['asiento', 'linea']),
            models.Index(fields=['cuenta']),
        ]
        unique_together = [['asiento', 'linea']]
    
    def __str__(self):
        return f"{self.asiento.numero_asiento} - LÃ­nea {self.linea}: {self.cuenta.codigo}"
    
    def clean(self):
        """Validaciones del modelo"""
        from django.core.exceptions import ValidationError
        
        # No puede tener dÃ©bito y crÃ©dito al mismo tiempo
        if self.debito > 0 and self.credito > 0:
            raise ValidationError('Una lÃ­nea no puede tener dÃ©bito y crÃ©dito simultÃ¡neamente')
        
        # Debe tener dÃ©bito o crÃ©dito (no ambos en cero)
        if self.debito == 0 and self.credito == 0:
            raise ValidationError('Debe especificar un monto en dÃ©bito o crÃ©dito')
        
        # Verificar que la cuenta sea de detalle
        if not self.cuenta.es_detalle:
            raise ValidationError('Solo se pueden usar cuentas de detalle en los asientos')
        
        # Verificar que la cuenta estÃ© activa
        if not self.cuenta.activo:
            raise ValidationError('La cuenta no estÃ¡ activa')
        
        # Verificar requerimientos especiales de la cuenta
        if self.cuenta.requiere_centro_costo and not self.centro_costo:
            raise ValidationError(f'La cuenta {self.cuenta.codigo} requiere centro de costo')
        
        if self.cuenta.requiere_tercero and not self.tercero:
            raise ValidationError(f'La cuenta {self.cuenta.codigo} requiere especificar un tercero')
    
    def save(self, *args, **kwargs):
        """Override save para ejecutar validaciones y actualizar totales"""
        self.clean()
        super().save(*args, **kwargs)
        
        # Actualizar totales del asiento padre
        self.asiento.calcular_totales()
        self.asiento.save()
    
    def get_monto_formateado(self):
        """Retorna el monto formateado segÃºn sea dÃ©bito o crÃ©dito"""
        if self.debito > 0:
            return f"${self.debito:,.2f} (D)"
        else:
            return f"${self.credito:,.2f} (C)"
    
    def get_tipo_movimiento(self):
        """Retorna el tipo de movimiento (dÃ©bito o crÃ©dito)"""
        return 'DEBITO' if self.debito > 0 else 'CREDITO'


# ============================================
# MODELOS DE SEGURIDAD
# ============================================

class LoginAttempt(models.Model):
    """
    Registra intentos de login exitosos y fallidos
    Permite implementar bloqueo de cuenta tras mÃºltiples intentos fallidos
    """
    email = models.EmailField(verbose_name="Email del intento")
    ip_address = models.GenericIPAddressField(verbose_name="DirecciÃ³n IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent del navegador")
    exitoso = models.BooleanField(default=False, verbose_name="Intento exitoso")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del intento")
    razon_fallo = models.CharField(max_length=255, blank=True, null=True, 
                                   verbose_name="RazÃ³n del fallo")
    
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
        from django.utils import timezone
        from datetime import timedelta
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        return cls.objects.filter(
            email=email,
            exitoso=False,
            fecha__gte=cutoff_time
        ).count()
    
    @classmethod
    def is_blocked(cls, email, max_attempts=5, block_minutes=15):
        """
        Verifica si una cuenta estÃ¡ bloqueada por demasiados intentos fallidos
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
    ip_address = models.GenericIPAddressField(verbose_name="DirecciÃ³n IP")
    nombre_corto_intentado = models.CharField(max_length=50, verbose_name="Subdominio Intentado", blank=True)
    exitoso = models.BooleanField(default=False, verbose_name="Registro Exitoso")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del Intento")
    razon_fallo = models.CharField(max_length=255, blank=True, null=True, verbose_name="RazÃ³n del Fallo")
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
        Obtiene intentos de registro de una IP en las Ãºltimas N horas
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
        Verifica si una IP estÃ¡ bloqueada por exceder intentos permitidos
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
    Registro de auditorÃ­a de eventos de seguridad importantes
    """
    TIPO_EVENTO_CHOICES = [
        ('LOGIN', 'Login exitoso'),
        ('LOGOUT', 'Logout'),
        ('LOGIN_FAILED', 'Login fallido'),
        ('PASSWORD_CHANGE', 'Cambio de contraseÃ±a'),
        ('PASSWORD_RESET', 'Reseteo de contraseÃ±a'),
        ('ACCOUNT_LOCKED', 'Cuenta bloqueada'),
        ('ACCOUNT_UNLOCKED', 'Cuenta desbloqueada'),
        ('PERMISSION_DENIED', 'Permiso denegado'),
        ('PROFILE_UPDATE', 'ActualizaciÃ³n de perfil'),
        ('SESSION_EXPIRED', 'SesiÃ³n expirada'),
        ('2FA_ENABLED', '2FA habilitado'),
        ('2FA_DISABLED', '2FA deshabilitado'),
        ('SUSPICIOUS_ACTIVITY', 'Actividad sospechosa'),
        ('DATA_EXPORT', 'ExportaciÃ³n de datos'),
        ('ADMIN_ACTION', 'AcciÃ³n administrativa'),
    ]
    
    NIVEL_SEVERIDAD_CHOICES = [
        ('INFO', 'InformaciÃ³n'),
        ('WARNING', 'Advertencia'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'CrÃ­tico'),
    ]
    
    usuario = models.ForeignKey(
        CustomUser,
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
    descripcion = models.TextField(verbose_name="DescripciÃ³n")
    ip_address = models.GenericIPAddressField(null=True, blank=True, 
                                              verbose_name="DirecciÃ³n IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    
    # InformaciÃ³n adicional en JSON
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
    Rastrea sesiones activas de usuarios para auditorÃ­a y control
    """
    usuario = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='user_sessions',
        verbose_name="Usuario"
    )
    session_key = models.CharField(max_length=40, unique=True, 
                                   verbose_name="Clave de sesiÃ³n")
    ip_address = models.GenericIPAddressField(verbose_name="DirecciÃ³n IP")
    user_agent = models.TextField(verbose_name="User Agent")
    fecha_inicio = models.DateTimeField(auto_now_add=True, 
                                        verbose_name="Fecha de inicio")
    fecha_ultima_actividad = models.DateTimeField(auto_now=True,
                                                   verbose_name="Ãšltima actividad")
    activa = models.BooleanField(default=True, verbose_name="SesiÃ³n activa")
    fecha_cierre = models.DateTimeField(null=True, blank=True, 
                                        verbose_name="Fecha de cierre")
    
    class Meta:
        verbose_name = "SesiÃ³n de Usuario"
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
        """Marca la sesiÃ³n como inactiva"""
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
    Modelo para autenticaciÃ³n de dos factores (2FA)
    """
    usuario = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='two_factor_auth',
        verbose_name="Usuario"
    )
    habilitado = models.BooleanField(default=False, verbose_name="2FA Habilitado")
    secret_key = models.CharField(max_length=32, blank=True, 
                                  verbose_name="Clave secreta TOTP")
    backup_codes = models.JSONField(default=list, blank=True,
                                   verbose_name="CÃ³digos de respaldo")
    fecha_habilitacion = models.DateTimeField(null=True, blank=True,
                                              verbose_name="Fecha de habilitaciÃ³n")
    ultimo_uso = models.DateTimeField(null=True, blank=True,
                                      verbose_name="Ãšltimo uso")
    
    class Meta:
        verbose_name = "AutenticaciÃ³n de Dos Factores"
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
        
        # Generar cÃ³digos de respaldo
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
        
        # Verificar cÃ³digo de respaldo
        if token.upper() in self.backup_codes:
            self.backup_codes.remove(token.upper())
            self.ultimo_uso = timezone.now()
            self.save()
            return True
        
        return False
    
    def get_qr_code_url(self):
        """Genera URL para cÃ³digo QR de Google Authenticator"""
        import pyotp
        totp = pyotp.TOTP(self.secret_key)
        return totp.provisioning_uri(
            name=self.usuario.email,
            issuer_name='Escuela Online'
        )


# ====================================================================
#  SISTEMA DE LISTAS DE COTEJO
# ====================================================================

class ListaCotejo(models.Model):
    """
    Plantilla de lista de cotejo que puede ser reutilizada.
    Define los parÃ¡metros generales de la evaluaciÃ³n.
    """
    TIPO_EVALUACION_CHOICES = [
        ('actividad', 'Actividad EspecÃ­fica'),
        ('proceso', 'EvaluaciÃ³n de Proceso'),
        ('proyecto', 'Proyecto'),
        ('comportamiento', 'EvaluaciÃ³n de Comportamiento'),
        ('cuaderno', 'EvaluaciÃ³n de Cuaderno'),
        ('participacion', 'ParticipaciÃ³n'),
        ('otro', 'Otro'),
    ]
    
    # Multi-Tenant: Escuela
    

    # Multi-Tenant Manager
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre de la Lista",
        help_text="Ej: Lista de cotejo para evaluar la participaciÃ³n"
    )
    
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="DescripciÃ³n",
        help_text="DescripciÃ³n detallada del propÃ³sito de esta lista"
    )
    
    tipo_evaluacion = models.CharField(
        max_length=20,
        choices=TIPO_EVALUACION_CHOICES,
        default='actividad',
        verbose_name="Tipo de EvaluaciÃ³n"
    )
    
    materia = models.ForeignKey(
        Materia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='listas_cotejo',
        verbose_name="Materia",
        help_text="Dejar en blanco si es una lista general/reutilizable"
    )
    
    creador = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='listas_cotejo_creadas',
        verbose_name="Creador"
    )
    
    puntaje_total = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        verbose_name="Puntaje Total",
        help_text="Puntaje mÃ¡ximo que se puede obtener (usualmente 10)"
    )
    
    es_plantilla = models.BooleanField(
        default=True,
        verbose_name="Es Plantilla Reutilizable",
        help_text="Si es True, esta lista puede ser utilizada mÃºltiples veces"
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name="Activa"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de CreaciÃ³n"
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Ãšltima ModificaciÃ³n"
    )
    
    orden_criterios = models.CharField(
        max_length=20,
        choices=[('manual', 'Manual'), ('alfabetico', 'AlfabÃ©tico')],
        default='manual',
        verbose_name="Orden de Criterios"
    )
    
    class Meta:
        verbose_name = "Lista de Cotejo"
        verbose_name_plural = "Listas de Cotejo"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_evaluacion_display()})"
    
    def total_criterios(self):
        """Retorna el nÃºmero total de criterios"""
        return self.criterios.count()
    
    def validar_puntajes(self):
        """Valida que la suma de puntajes de los criterios sea igual al puntaje total"""
        suma = sum([c.puntaje_maximo for c in self.criterios.all()])
        return suma == float(self.puntaje_total)


class CriterioListaCotejo(models.Model):
    """
    Criterio individual dentro de una lista de cotejo.
    Puede ser de tipo binario (check), numÃ©rico o escala.
    """
    TIPO_CRITERIO_CHOICES = [
        ('binario', 'Binario (âœ“/âœ— - SÃ­/No)'),
        ('numerico', 'NumÃ©rico (0-10)'),
        ('escala_5', 'Escala 1-5'),
        ('escala_3', 'Escala 1-3'),
        ('porcentaje', 'Porcentaje (0-100%)'),
    ]
    
    lista_cotejo = models.ForeignKey(
        ListaCotejo,
        on_delete=models.CASCADE,
        related_name='criterios',
        verbose_name="Lista de Cotejo"
    )
    
    descripcion = models.CharField(
        max_length=300,
        verbose_name="DescripciÃ³n del Criterio",
        help_text="Ej: Completo las actividades en clase"
    )
    
    tipo_criterio = models.CharField(
        max_length=15,
        choices=TIPO_CRITERIO_CHOICES,
        default='binario',
        verbose_name="Tipo de Criterio"
    )
    
    puntaje_maximo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        verbose_name="Puntaje MÃ¡ximo",
        help_text="Puntos que vale este criterio"
    )
    
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden",
        help_text="Orden de apariciÃ³n en la lista (menor nÃºmero = primero)"
    )
    
    es_obligatorio = models.BooleanField(
        default=True,
        verbose_name="Es Obligatorio",
        help_text="Si debe ser evaluado obligatoriamente"
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )
    
    class Meta:
        verbose_name = "Criterio de Lista de Cotejo"
        verbose_name_plural = "Criterios de Listas de Cotejo"
        ordering = ['orden', 'id']
        unique_together = ['lista_cotejo', 'orden']
    
    def __str__(self):
        return f"{self.descripcion} ({self.get_tipo_criterio_display()})"
    
    def valor_maximo(self):
        """Retorna el valor mÃ¡ximo segÃºn el tipo de criterio"""
        tipos_valores = {
            'binario': 1,
            'numerico': 10,
            'escala_5': 5,
            'escala_3': 3,
            'porcentaje': 100,
        }
        return tipos_valores.get(self.tipo_criterio, 10)


class EvaluacionListaCotejo(models.Model):
    """
    AplicaciÃ³n de una lista de cotejo a un grupo especÃ­fico de estudiantes.
    Representa una evaluaciÃ³n concreta en una fecha determinada.
    """
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('en_progreso', 'En Progreso'),
        ('finalizada', 'Finalizada'),
        ('publicada', 'Publicada'),
    ]
    
    lista_cotejo = models.ForeignKey(
        ListaCotejo,
        on_delete=models.CASCADE,
        related_name='evaluaciones',
        verbose_name="Lista de Cotejo"
    )
    
    materia = models.ForeignKey(
        Materia,
        on_delete=models.CASCADE,
        related_name='evaluaciones_cotejo',
        verbose_name="Materia"
    )
    
    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='evaluaciones_cotejo',
        verbose_name="Curso"
    )
    
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre de la EvaluaciÃ³n",
        help_text="Ej: EvaluaciÃ³n de participaciÃ³n - Marzo 2026"
    )
    
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="DescripciÃ³n"
    )
    
    fecha_evaluacion = models.DateField(
        verbose_name="Fecha de EvaluaciÃ³n"
    )
    
    fecha_limite = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha LÃ­mite para Calificar"
    )
    
    evaluador = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='evaluaciones_cotejo_realizadas',
        verbose_name="Evaluador"
    )
    
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='borrador',
        verbose_name="Estado"
    )
    
    incluir_en_promedio = models.BooleanField(
        default=False,
        verbose_name="Incluir en Promedio Final",
        help_text="Si esta evaluaciÃ³n debe sumarse al promedio de la materia"
    )
    
    peso_en_promedio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="Peso en Promedio (%)",
        help_text="Porcentaje que representa en el promedio (0-100)"
    )
    
    observaciones_generales = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones Generales"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de CreaciÃ³n"
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Ãšltima ModificaciÃ³n"
    )
    
    fecha_publicacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de PublicaciÃ³n"
    )
    
    class Meta:
        verbose_name = "EvaluaciÃ³n con Lista de Cotejo"
        verbose_name_plural = "Evaluaciones con Listas de Cotejo"
        ordering = ['-fecha_evaluacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.curso.nombre}"
    
    def total_estudiantes(self):
        """Retorna el nÃºmero total de estudiantes en el curso para esta materia"""
        # Obtener estudiantes matriculados en la materia
        # La materia ya pertenece a un curso especÃ­fico
        return Matricula.objects.filter(
            materia=self.materia
        ).values('estudiante').distinct().count()
    
    def estudiantes_evaluados(self):
        """Retorna el nÃºmero de estudiantes con calificaciones completas"""
        total_criterios = self.lista_cotejo.criterios.filter(activo=True).count()
        if total_criterios == 0:
            return 0
        
        estudiantes_completos = 0
        
        # Obtener estudiantes Ãºnicos con calificaciones
        estudiantes_ids = self.calificaciones.values_list('estudiante_id', flat=True).distinct()
        
        for estudiante_id in estudiantes_ids:
            califs = self.calificaciones.filter(estudiante_id=estudiante_id).count()
            if califs >= total_criterios:
                estudiantes_completos += 1
        
        return estudiantes_completos
    
    def porcentaje_completado(self):
        """Retorna el porcentaje de evaluaciÃ³n completada"""
        total = self.total_estudiantes()
        if total == 0:
            return 0
        evaluados = self.estudiantes_evaluados()
        return round((evaluados / total) * 100, 2)
    
    def publicar(self):
        """Publica la evaluaciÃ³n y la hace visible para estudiantes"""
        self.estado = 'publicada'
        self.fecha_publicacion = timezone.now()
        self.save()


class CalificacionCotejo(models.Model):
    """
    CalificaciÃ³n individual de un criterio para un estudiante especÃ­fico.
    Guarda el valor obtenido por el estudiante en cada criterio.
    """
    evaluacion = models.ForeignKey(
        EvaluacionListaCotejo,
        on_delete=models.CASCADE,
        related_name='calificaciones',
        verbose_name="EvaluaciÃ³n"
    )
    
    estudiante = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='calificaciones_cotejo',
        verbose_name="Estudiante"
    )
    
    criterio = models.ForeignKey(
        CriterioListaCotejo,
        on_delete=models.CASCADE,
        related_name='calificaciones',
        verbose_name="Criterio"
    )
    
    valor = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor Obtenido",
        help_text="Valor segÃºn el tipo de criterio"
    )
    
    cumple = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Cumple (Para criterios binarios)"
    )
    
    observacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="ObservaciÃ³n",
        help_text="Comentario especÃ­fico sobre este criterio para este estudiante"
    )
    
    fecha_calificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de CalificaciÃ³n"
    )
    
    calificado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='calificaciones_cotejo_realizadas',
        verbose_name="Calificado Por"
    )
    
    class Meta:
        verbose_name = "CalificaciÃ³n de Cotejo"
        verbose_name_plural = "Calificaciones de Cotejo"
        unique_together = ['evaluacion', 'estudiante', 'criterio']
        ordering = ['estudiante', 'criterio__orden']
    
    def __str__(self):
        return f"{self.estudiante.get_full_name()} - {self.criterio.descripcion[:30]}"
    
    def puntaje_obtenido(self):
        """Calcula el puntaje real obtenido basado en el valor y el tipo de criterio"""
        if self.criterio.tipo_criterio == 'binario':
            if self.cumple:
                return float(self.criterio.puntaje_maximo)
            return 0.0
        elif self.valor is not None:
            # Calcular proporcionalmente
            valor_maximo = self.criterio.valor_maximo()
            proporcion = float(self.valor) / valor_maximo
            return round(float(self.criterio.puntaje_maximo) * proporcion, 2)
        return 0.0
    
    def save(self, *args, **kwargs):
        """Override save para manejar criterios binarios"""
        if self.criterio.tipo_criterio == 'binario':
            # Para binarios, si valor es 1, cumple=True, si es 0 o None, cumple=False
            if self.valor is not None:
                self.cumple = (float(self.valor) > 0)
            elif self.cumple is not None:
                self.valor = 1 if self.cumple else 0
        super().save(*args, **kwargs)


class ResumenEvaluacionCotejo(models.Model):
    """
    Resumen consolidado de la evaluaciÃ³n de un estudiante.
    Se calcula automÃ¡ticamente basado en las calificaciones individuales.
    """
    evaluacion = models.ForeignKey(
        EvaluacionListaCotejo,
        on_delete=models.CASCADE,
        related_name='resumenes',
        verbose_name="EvaluaciÃ³n"
    )
    
    estudiante = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='resumenes_cotejo',
        verbose_name="Estudiante"
    )
    
    puntaje_obtenido = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name="Puntaje Obtenido"
    )
    
    puntaje_maximo = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=10,
        verbose_name="Puntaje MÃ¡ximo"
    )
    
    porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Porcentaje (%)"
    )
    
    criterios_evaluados = models.PositiveIntegerField(
        default=0,
        verbose_name="Criterios Evaluados"
    )
    
    criterios_totales = models.PositiveIntegerField(
        default=0,
        verbose_name="Criterios Totales"
    )
    
    esta_completo = models.BooleanField(
        default=False,
        verbose_name="EvaluaciÃ³n Completa"
    )
    
    fecha_calculo = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de CÃ¡lculo"
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones Generales"
    )
    
    class Meta:
        verbose_name = "Resumen de EvaluaciÃ³n de Cotejo"
        verbose_name_plural = "ResÃºmenes de Evaluaciones de Cotejo"
        unique_together = ['evaluacion', 'estudiante']
        ordering = ['estudiante__first_name', 'estudiante__last_name']
    
    def __str__(self):
        return f"{self.estudiante.get_full_name()} - {self.puntaje_obtenido}/{self.puntaje_maximo}"
    
    def calcular_puntaje(self):
        """Calcula el puntaje total del estudiante en esta evaluaciÃ³n"""
        calificaciones = CalificacionCotejo.objects.filter(
            evaluacion=self.evaluacion,
            estudiante=self.estudiante
        )
        
        puntaje_total = 0
        criterios_evaluados = 0
        
        for calif in calificaciones:
            if calif.valor is not None or calif.cumple is not None:
                puntaje_total += calif.puntaje_obtenido()
                criterios_evaluados += 1
        
        self.puntaje_obtenido = round(puntaje_total, 2)
        self.puntaje_maximo = float(self.evaluacion.lista_cotejo.puntaje_total)
        self.criterios_evaluados = criterios_evaluados
        self.criterios_totales = self.evaluacion.lista_cotejo.criterios.filter(activo=True).count()
        self.esta_completo = (self.criterios_evaluados >= self.criterios_totales)
        
        if self.puntaje_maximo > 0:
            self.porcentaje = round((self.puntaje_obtenido / self.puntaje_maximo) * 100, 2)
        else:
            self.porcentaje = 0
        
        self.save()
        return self.puntaje_obtenido


class EvaluacionDiagnostica(models.Model):
    """
    EvaluaciÃ³n diagnÃ³stica para identificar conocimientos previos y nivel inicial del estudiante.
    Conforme al sistema educativo de la RepÃºblica Dominicana.
    """
    PERIODO_CHOICES = [
        ('inicio_anho', 'Inicio de AÃ±o Escolar'),
        ('inicio_periodo_1', 'Inicio Primer PerÃ­odo'),
        ('inicio_periodo_2', 'Inicio Segundo PerÃ­odo'),
        ('inicio_periodo_3', 'Inicio Tercer PerÃ­odo'),
        ('inicio_periodo_4', 'Inicio Cuarto PerÃ­odo'),
        ('inicio_unidad', 'Inicio de Unidad DidÃ¡ctica'),
    ]
    
    INSTRUMENTO_CHOICES = [
        ('prueba_escrita', 'Prueba Escrita'),
        ('prueba_oral', 'Prueba Oral'),
        ('observacion', 'ObservaciÃ³n Directa'),
        ('practica', 'Prueba PrÃ¡ctica'),
        ('mixta', 'Mixta'),
    ]
    
    # Multi-Tenant: Escuela
    

    # Multi-Tenant Manager
    materia = models.ForeignKey(
        'Materia',
        on_delete=models.CASCADE,
        related_name='evaluaciones_diagnosticas',
        verbose_name="Materia/Asignatura"
    )
    
    periodo = models.CharField(
        max_length=20,
        choices=PERIODO_CHOICES,
        verbose_name="PerÃ­odo de AplicaciÃ³n"
    )
    
    competencia = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Competencia a Evaluar",
        help_text="Ej: Competencia Comunicativa, Pensamiento LÃ³gico, ResoluciÃ³n de Problemas"
    )
    
    indicadores = models.TextField(
        blank=True,
        null=True,
        verbose_name="Indicadores de Logro",
        help_text="Lista de indicadores de logro que se evaluarÃ¡n"
    )
    
    fecha_aplicacion = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de AplicaciÃ³n"
    )
    
    instrumento = models.CharField(
        max_length=20,
        choices=INSTRUMENTO_CHOICES,
        default='prueba_escrita',
        verbose_name="Tipo de Instrumento"
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones/Notas",
        help_text="Anotaciones adicionales sobre la evaluaciÃ³n"
    )
    
    creado_por = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='evaluaciones_diagnosticas_creadas',
        verbose_name="Creado por"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de CreaciÃ³n"
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Ãšltima ModificaciÃ³n"
    )
    
    class Meta:
        verbose_name = "EvaluaciÃ³n DiagnÃ³stica"
        verbose_name_plural = "Evaluaciones DiagnÃ³sticas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.materia.nombre} - {self.get_periodo_display()} ({self.fecha_creacion.strftime('%d/%m/%Y')})"
    
    def get_curso(self):
        """Retorna el curso asociado a travÃ©s de la materia"""
        return self.materia.curso
    
    def total_estudiantes(self):
        """Retorna el nÃºmero total de estudiantes en el curso para esta materia"""
        return Matricula.objects.filter(materia=self.materia).values('estudiante').distinct().count()
    
    def estudiantes_evaluados(self):
        """Retorna el nÃºmero de estudiantes evaluados"""
        return self.resultados.values('estudiante').distinct().count()
    
    def porcentaje_completado(self):
        """Retorna el porcentaje de evaluaciÃ³n completada"""
        total = self.total_estudiantes()
        if total == 0:
            return 0
        evaluados = self.estudiantes_evaluados()
        return round((evaluados / total) * 100, 2)


class ResultadoEvaluacionDiagnostica(models.Model):
    """
    Resultado individual de un estudiante en una evaluaciÃ³n diagnÃ³stica.
    Registra el nivel de logro y observaciones especÃ­ficas.
    """
    NIVEL_LOGRO_CHOICES = [
        ('no_alcanzado', 'No Alcanzado'),
        ('en_proceso', 'En Proceso'),
        ('alcanzado', 'Alcanzado'),
        ('supera', 'Supera lo Esperado'),
    ]
    
    evaluacion = models.ForeignKey(
        EvaluacionDiagnostica,
        on_delete=models.CASCADE,
        related_name='resultados',
        verbose_name="EvaluaciÃ³n DiagnÃ³stica"
    )
    
    estudiante = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='resultados_diagnosticas',
        verbose_name="Estudiante"
    )
    
    nivel_logro = models.CharField(
        max_length=20,
        choices=NIVEL_LOGRO_CHOICES,
        verbose_name="Nivel de Logro"
    )
    
    puntaje_obtenido = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Puntaje Obtenido",
        help_text="Puntaje numÃ©rico obtenido (opcional)"
    )
    
    puntaje_total = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Puntaje Total",
        help_text="Puntaje total de la evaluaciÃ³n (opcional)"
    )
    
    fortalezas = models.TextField(
        blank=True,
        null=True,
        verbose_name="Fortalezas Identificadas",
        help_text="Aspectos en los que el estudiante demuestra dominio"
    )
    
    debilidades = models.TextField(
        blank=True,
        null=True,
        verbose_name="Ãreas de Mejora",
        help_text="Aspectos que requieren refuerzo o intervenciÃ³n"
    )
    
    recomendaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Recomendaciones",
        help_text="Estrategias pedagÃ³gicas sugeridas para este estudiante"
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones Generales"
    )
    
    fecha_evaluacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de EvaluaciÃ³n"
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Ãšltima ModificaciÃ³n"
    )
    
    evaluado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='evaluaciones_diagnosticas_realizadas',
        verbose_name="Evaluado Por"
    )
    
    class Meta:
        verbose_name = "Resultado de EvaluaciÃ³n DiagnÃ³stica"
        verbose_name_plural = "Resultados de Evaluaciones DiagnÃ³sticas"
        unique_together = ['evaluacion', 'estudiante']
        ordering = ['estudiante__first_name', 'estudiante__last_name']
    
    def __str__(self):
        return f"{self.estudiante.get_full_name()} - {self.get_nivel_logro_display()}"
    
    def porcentaje(self):
        """Calcula el porcentaje si hay puntajes. Si no hay puntaje_total, asume 100"""
        if self.puntaje_obtenido is not None:
            total = float(self.puntaje_total) if self.puntaje_total else 100.0
            return round((float(self.puntaje_obtenido) / total) * 100, 2)
        return None


# ==================== RÃšBRICAS DE EVALUACIÃ“N ====================

class Rubrica(models.Model):
    """
    RÃºbrica de evaluaciÃ³n: matriz de valoraciÃ³n con criterios y niveles de desempeÃ±o.
    Instrumento para evaluar competencias de forma objetiva y sistemÃ¡tica.
    """
    TIPO_ACTIVIDAD_CHOICES = [
        ('proyecto', 'Proyecto'),
        ('presentacion', 'PresentaciÃ³n Oral'),
        ('trabajo_escrito', 'Trabajo Escrito'),
        ('trabajo_grupo', 'Trabajo en Grupo'),
        ('experimentacion', 'ExperimentaciÃ³n/PrÃ¡ctica'),
        ('exposicion', 'ExposiciÃ³n'),
        ('debate', 'Debate'),
        ('otro', 'Otro'),
    ]
    
    # Multi-Tenant: Escuela
    

    # Multi-Tenant Manager
    materia = models.ForeignKey(
        'Materia',
        on_delete=models.CASCADE,
        related_name='rubricas',
        verbose_name="Materia/Asignatura",
        null=True,
        blank=True,
        help_text="Materia asociada (opcional para rÃºbricas genÃ©ricas)"
    )
    
    nombre = models.CharField(
        max_length=255,
        verbose_name="Nombre de la RÃºbrica",
        help_text="Ej: EvaluaciÃ³n de Proyecto de Ciencias"
    )
    
    tipo_actividad = models.CharField(
        max_length=20,
        choices=TIPO_ACTIVIDAD_CHOICES,
        default='proyecto',
        verbose_name="Tipo de Actividad"
    )
    
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="DescripciÃ³n",
        help_text="DescripciÃ³n general de la rÃºbrica"
    )
    
    creado_por = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='rubricas_creadas',
        verbose_name="Creado Por"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de CreaciÃ³n"
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Ãšltima ModificaciÃ³n"
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name="Activa",
        help_text="Indica si la rÃºbrica estÃ¡ activa para usar"
    )
    
    class Meta:
        verbose_name = "RÃºbrica"
        verbose_name_plural = "RÃºbricas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        if self.materia:
            return f"{self.nombre} - {self.materia.nombre}"
        return f"{self.nombre} (GenÃ©rica)"
    
    def total_criterios(self):
        """Retorna el nÃºmero total de criterios"""
        return self.criterios.count()
    
    def total_ponderacion(self):
        """Calcula la suma total de ponderaciones (deberÃ­a ser 100%)"""
        from django.db.models import Sum
        total = self.criterios.aggregate(Sum('ponderacion'))['ponderacion__sum']
        return total if total else 0
    
    def puntaje_maximo(self):
        """Calcula el puntaje mÃ¡ximo posible con esta rÃºbrica (escala 0-100)"""
        # Si todos los criterios tienen nivel Excelente (5), el puntaje mÃ¡ximo es
        # la suma de las ponderaciones (que deberÃ­a ser 100)
        # FÃ³rmula por criterio: (5/5) Ã— ponderaciÃ³n = 1 Ã— ponderaciÃ³n
        # Total: suma de todas las ponderaciones
        # Ejemplo: 5 criterios al 20% = 20+20+20+20+20 = 100 puntos
        total_ponderacion = self.total_ponderacion()
        return round(float(total_ponderacion), 2) if total_ponderacion > 0 else 0
    
    def ponderacion_valida(self):
        """Verifica si las ponderaciones suman 100%"""
        total = self.total_ponderacion()
        return abs(float(total) - 100.0) < 0.01  # Tolerancia de 0.01%


class CriterioRubrica(models.Model):
    """
    Criterio de evaluaciÃ³n dentro de una rÃºbrica.
    Define un aspecto especÃ­fico a evaluar.
    """
    rubrica = models.ForeignKey(
        Rubrica,
        on_delete=models.CASCADE,
        related_name='criterios',
        verbose_name="RÃºbrica"
    )
    
    nombre = models.CharField(
        max_length=255,
        verbose_name="Nombre del Criterio",
        help_text="Ej: Contenido y Profundidad, OrganizaciÃ³n, PresentaciÃ³n Visual"
    )
    
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="DescripciÃ³n",
        help_text="DescripciÃ³n detallada de quÃ© se evaluarÃ¡ en este criterio"
    )
    
    ponderacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.0,
        verbose_name="PonderaciÃ³n (%)",
        help_text="Peso del criterio en la evaluaciÃ³n final (ej: 20.00%)"
    )
    
    orden = models.IntegerField(
        default=0,
        verbose_name="Orden",
        help_text="Orden de visualizaciÃ³n del criterio"
    )
    
    class Meta:
        verbose_name = "Criterio de RÃºbrica"
        verbose_name_plural = "Criterios de RÃºbrica"
        ordering = ['rubrica', 'orden', 'id']
        unique_together = ['rubrica', 'nombre']
    
    def __str__(self):
        return f"{self.rubrica.nombre} - {self.nombre}"


class NivelDesempeno(models.Model):
    """
    Nivel de desempeÃ±o dentro de un criterio de rÃºbrica.
    Define la calidad del trabajo en ese criterio.
    """
    NIVEL_CHOICES = [
        ('excelente', 'Excelente (5)'),
        ('muy_bueno', 'Muy Bueno (4)'),
        ('bueno', 'Bueno (3)'),
        ('regular', 'Regular (2)'),
        ('necesita_mejorar', 'Necesita Mejorar (1)'),
    ]
    
    criterio = models.ForeignKey(
        CriterioRubrica,
        on_delete=models.CASCADE,
        related_name='niveles',
        verbose_name="Criterio"
    )
    
    nivel = models.CharField(
        max_length=20,
        choices=NIVEL_CHOICES,
        verbose_name="Nivel de DesempeÃ±o"
    )
    
    puntaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Puntaje",
        help_text="Puntaje numÃ©rico para este nivel (1-5)"
    )
    
    descriptor = models.TextField(
        verbose_name="Descriptor",
        help_text="DescripciÃ³n detallada de lo que caracteriza este nivel de desempeÃ±o"
    )
    
    class Meta:
        verbose_name = "Nivel de DesempeÃ±o"
        verbose_name_plural = "Niveles de DesempeÃ±o"
        ordering = ['-puntaje']
        unique_together = ['criterio', 'nivel']
    
    def __str__(self):
        return f"{self.criterio.nombre} - {self.get_nivel_display()}"


class EvaluacionRubrica(models.Model):
    """
    EvaluaciÃ³n aplicada a estudiantes usando una rÃºbrica
    Permite calificar desempeÃ±o en actividades/proyectos segÃºn criterios establecidos
    """
    rubrica = models.ForeignKey(
        Rubrica,
        on_delete=models.CASCADE,
        related_name='evaluaciones',
        verbose_name="RÃºbrica"
    )
    
    materia = models.ForeignKey(
        Materia,
        on_delete=models.CASCADE,
        related_name='evaluaciones_rubrica',
        verbose_name="Materia"
    )
    
    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='evaluaciones_rubrica',
        verbose_name="Curso"
    )
    
    titulo = models.CharField(
        max_length=200,
        verbose_name="TÃ­tulo de la EvaluaciÃ³n",
        help_text="Nombre descriptivo de la evaluaciÃ³n (ej: Proyecto Final, ExposiciÃ³n Oral)"
    )
    
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="DescripciÃ³n",
        help_text="Detalles de la actividad evaluada"
    )
    
    fecha_evaluacion = models.DateField(
        verbose_name="Fecha de EvaluaciÃ³n"
    )
    
    periodo = models.CharField(
        max_length=50,
        verbose_name="PerÃ­odo",
        help_text="Ej: Primer PerÃ­odo, Segundo PerÃ­odo"
    )
    
    creada_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='evaluaciones_rubrica_creadas',
        verbose_name="Creada Por"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de CreaciÃ³n"
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name="Activa"
    )
    
    class Meta:
        verbose_name = "EvaluaciÃ³n con RÃºbrica"
        verbose_name_plural = "Evaluaciones con RÃºbrica"
        ordering = ['-fecha_evaluacion']
    
    def __str__(self):
        return f"{self.titulo} - {self.materia.nombre} ({self.curso})"
    
    def total_estudiantes(self):
        """Retorna el total de estudiantes evaluados"""
        return self.calificaciones.values('estudiante').distinct().count()
    
    def puntaje_promedio(self):
        """Calcula el puntaje promedio de todos los estudiantes (escala 0-100)"""
        from django.db.models import Sum, Count
        estudiantes_puntajes = {}
        
        # Calcular puntaje de cada estudiante
        for cal in self.calificaciones.select_related('criterio', 'nivel_otorgado'):
            if cal.estudiante_id not in estudiantes_puntajes:
                estudiantes_puntajes[cal.estudiante_id] = 0
            # Usar puntaje_ponderado() que ya aplica la escala correcta
            estudiantes_puntajes[cal.estudiante_id] += cal.puntaje_ponderado()
        
        if not estudiantes_puntajes:
            return 0
        
        promedio = sum(estudiantes_puntajes.values()) / len(estudiantes_puntajes)
        return round(promedio, 2)


class CalificacionCriterio(models.Model):
    """
    CalificaciÃ³n de un estudiante en un criterio especÃ­fico de una rÃºbrica
    """
    evaluacion = models.ForeignKey(
        EvaluacionRubrica,
        on_delete=models.CASCADE,
        related_name='calificaciones',
        verbose_name="EvaluaciÃ³n"
    )
    
    estudiante = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='calificaciones_rubrica',
        verbose_name="Estudiante",
        limit_choices_to={'rol': 'Estudiante'}
    )
    
    criterio = models.ForeignKey(
        CriterioRubrica,
        on_delete=models.CASCADE,
        related_name='calificaciones',
        verbose_name="Criterio"
    )
    
    nivel_otorgado = models.ForeignKey(
        NivelDesempeno,
        on_delete=models.SET_NULL,
        null=True,
        related_name='calificaciones',
        verbose_name="Nivel Otorgado"
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
        help_text="Comentarios especÃ­ficos sobre el desempeÃ±o en este criterio"
    )
    
    fecha_calificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de CalificaciÃ³n"
    )
    
    class Meta:
        verbose_name = "CalificaciÃ³n de Criterio"
        verbose_name_plural = "Calificaciones de Criterios"
        unique_together = ['evaluacion', 'estudiante', 'criterio']
        ordering = ['criterio__orden']
    
    def __str__(self):
        return f"{self.estudiante} - {self.criterio.nombre}: {self.nivel_otorgado.get_nivel_display() if self.nivel_otorgado else 'Sin calificar'}"
    
    def puntaje_ponderado(self):
        """Calcula el puntaje ponderado para este criterio (escala 0-100)"""
        if not self.nivel_otorgado:
            return 0
        # FÃ³rmula: (nivel / 5) Ã— ponderaciÃ³n = puntaje del criterio
        # El nivel mÃ¡ximo es 5, por lo que normalizamos dividiÃ©ndolo entre 5
        # Ejemplo: nivel 5 con 20% = (5/5) Ã— 20 = 1 Ã— 20 = 20 puntos
        # Ejemplo: nivel 3 con 20% = (3/5) Ã— 20 = 0.6 Ã— 20 = 12 puntos
        # Si hay 5 criterios al 20% todos en nivel 5: 20+20+20+20+20 = 100 puntos
        nivel_normalizado = float(self.nivel_otorgado.puntaje) / 5.0
        return round(nivel_normalizado * float(self.criterio.ponderacion), 2)


# ===========================
# CONFIGURACIÃ“N DE LA ESCUELA
# ===========================

class ConfiguracionEscuela(models.Model):
    """
    ConfiguraciÃ³n general de la escuela/colegio
    Solo debe existir un registro en esta tabla
    """
    # Multi-Tenant: Escuela
    

    # Multi-Tenant Manager
    nombre_escuela = models.CharField(
        max_length=200,
        verbose_name="Nombre de la Escuela",
        help_text="Nombre oficial de la instituciÃ³n educativa"
    )
    
    rnc = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="RNC",
        help_text="Registro Nacional del Contribuyente"
    )
    
    direccion = models.TextField(
        blank=True,
        null=True,
        verbose_name="DirecciÃ³n",
        help_text="DirecciÃ³n fÃ­sica de la escuela"
    )
    
    telefono = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="TelÃ©fono",
        help_text="TelÃ©fono principal de contacto"
    )
    
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo ElectrÃ³nico",
        help_text="Email institucional"
    )
    
    sitio_web = models.URLField(
        blank=True,
        null=True,
        verbose_name="Sitio Web",
        help_text="URL del sitio web de la instituciÃ³n"
    )
    
    logo = models.ImageField(
        upload_to='escuela/logos/',
        blank=True,
        null=True,
        verbose_name="Logo",
        help_text="Logo oficial de la instituciÃ³n (tamaÃ±o recomendado: 200x200px)"
    )
    
    director_nombre = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Nombre del Director",
        help_text="Nombre completo del director(a)"
    )
    
    director_firma = models.ImageField(
        upload_to='escuela/firmas/',
        blank=True,
        null=True,
        verbose_name="Firma del Director",
        help_text="Imagen de la firma del director (fondo transparente)"
    )
    
    lema = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        verbose_name="Lema Institucional",
        help_text="Lema o eslogan de la instituciÃ³n"
    )
    
    mision = models.TextField(
        blank=True,
        null=True,
        verbose_name="MisiÃ³n",
        help_text="DeclaraciÃ³n de la misiÃ³n institucional"
    )
    
    vision = models.TextField(
        blank=True,
        null=True,
        verbose_name="VisiÃ³n",
        help_text="DeclaraciÃ³n de la visiÃ³n institucional"
    )
    
    codigo_centro = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="CÃ³digo del Centro",
        help_text="CÃ³digo oficial asignado por el MINERD u otra autoridad"
    )
    
    distrito_educativo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Distrito Educativo",
        help_text="Distrito educativo al que pertenece"
    )
    
    regional_educativa = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Regional Educativa",
        help_text="Regional educativa a la que pertenece"
    )
    
    nivel_educativo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Nivel Educativo",
        help_text="Ej: Inicial, BÃ¡sica, Media, TÃ©cnico-Profesional"
    )
    
    modalidad = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Modalidad",
        help_text="Ej: General, TÃ©cnico-Profesional, Artes"
    )
    
    horario_atencion = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Horario de AtenciÃ³n",
        help_text="Ej: Lunes a Viernes 7:00 AM - 4:00 PM"
    )
    
    anho_fundacion = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="AÃ±o de FundaciÃ³n",
        help_text="AÃ±o en que fue fundada la instituciÃ³n"
    )
    
    # InformaciÃ³n para reportes
    pie_pagina_reportes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Pie de PÃ¡gina para Reportes",
        help_text="Texto que aparecerÃ¡ al pie de los reportes oficiales"
    )
    
    mostrar_logo_reportes = models.BooleanField(
        default=True,
        verbose_name="Mostrar Logo en Reportes",
        help_text="Activar/desactivar el logo en los reportes"
    )
    
    # Control de registro Ãºnico
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de CreaciÃ³n"
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Ãšltima ActualizaciÃ³n"
    )
    
    class Meta:
        verbose_name = "ConfiguraciÃ³n de la Escuela"
        verbose_name_plural = "ConfiguraciÃ³n de la Escuela"
    
    def __str__(self):
        return self.nombre_escuela or "ConfiguraciÃ³n de la Escuela"
    
    def save(self, *args, **kwargs):
        """Asegurar que solo exista un registro de configuraciÃ³n"""
        if not self.pk and ConfiguracionEscuela.objects.exists():
            # Si no tiene pk (es nuevo) y ya existe un registro, usar el existente
            existing = ConfiguracionEscuela.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)
    
    @classmethod
    def get_configuracion(cls):
        """Obtener o crear la configuraciÃ³n de la escuela"""
        config, created = cls.objects.get_or_create(
            pk=1,
            defaults={'nombre_escuela': 'Mi Escuela'}
        )
        return config


# ============================================
# MODELOS DE SEGURIDAD ADICIONALES
# ============================================

class IPBlocklist(models.Model):
    """
    Lista de IPs bloqueadas por actividad sospechosa
    """
    TIPO_BLOQUEO_CHOICES = [
        ('MANUAL', 'Bloqueo Manual'),
        ('AUTO_RATE_LIMIT', 'AutomÃ¡tico - Rate Limit'),
        ('AUTO_FAILED_LOGIN', 'AutomÃ¡tico - Login Fallido'),
        ('AUTO_SUSPICIOUS', 'AutomÃ¡tico - Actividad Sospechosa'),
    ]
    
    ip_address = models.GenericIPAddressField(unique=True, db_index=True,
                                              verbose_name="DirecciÃ³n IP")
    tipo_bloqueo = models.CharField(max_length=30, choices=TIPO_BLOQUEO_CHOICES,
                                    default='MANUAL', verbose_name="Tipo de Bloqueo")
    razon = models.TextField(verbose_name="RazÃ³n del Bloqueo")
    fecha_bloqueo = models.DateTimeField(auto_now_add=True, 
                                         verbose_name="Fecha de Bloqueo")
    bloqueado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ips_bloqueadas',
        verbose_name="Bloqueado Por"
    )
    
    # Control de bloqueo temporal
    es_temporal = models.BooleanField(default=False, verbose_name="Bloqueo Temporal")
    fecha_expiracion = models.DateTimeField(null=True, blank=True,
                                            verbose_name="Fecha de ExpiraciÃ³n")
    activo = models.BooleanField(default=True, verbose_name="Bloqueo Activo")
    
    # EstadÃ­sticas
    intentos_durante_bloqueo = models.IntegerField(default=0,
                                                    verbose_name="Intentos Durante Bloqueo")
    ultima_actividad = models.DateTimeField(auto_now=True,
                                            verbose_name="Ãšltima Actividad")
    
    # InformaciÃ³n adicional
    pais = models.CharField(max_length=100, blank=True,
                           verbose_name="PaÃ­s de Origen")
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
        """Verifica si una IP estÃ¡ bloqueada y activa"""
        now = timezone.now()
        
        # Buscar bloqueo activo
        try:
            bloqueo = cls.objects.get(ip_address=ip_address, activo=True)
            
            # Si es temporal, verificar expiraciÃ³n
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
        from datetime import timedelta
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
    Alertas de seguridad que requieren atenciÃ³n
    """
    TIPO_ALERTA_CHOICES = [
        ('BRUTE_FORCE', 'Intento de Fuerza Bruta'),
        ('MULTIPLE_FAILED_LOGIN', 'MÃºltiples Intentos Fallidos'),
        ('SUSPICIOUS_IP', 'IP Sospechosa'),
        ('UNUSUAL_LOCATION', 'UbicaciÃ³n Inusual'),
        ('UNUSUAL_TIME', 'Hora Inusual'),
        ('ACCOUNT_COMPROMISE', 'Posible Cuenta Comprometida'),
        ('DATA_BREACH', 'Posible FiltraciÃ³n de Datos'),
        ('PRIVILEGE_ESCALATION', 'Escalada de Privilegios'),
        ('UNAUTHORIZED_ACCESS', 'Acceso No Autorizado'),
        ('OTHER', 'Otro'),
    ]
    
    NIVEL_PRIORIDAD_CHOICES = [
        ('LOW', 'Baja'),
        ('MEDIUM', 'Media'),
        ('HIGH', 'Alta'),
        ('CRITICAL', 'CrÃ­tica'),
    ]
    
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('REVISANDO', 'En RevisiÃ³n'),
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
    
    titulo = models.CharField(max_length=200, verbose_name="TÃ­tulo")
    descripcion = models.TextField(verbose_name="DescripciÃ³n")
    
    # Usuario afectado (si aplica)
    usuario_afectado = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertas_seguridad',
        verbose_name="Usuario Afectado"
    )
    
    # IP relacionada
    ip_address = models.GenericIPAddressField(null=True, blank=True,
                                              verbose_name="DirecciÃ³n IP")
    
    # Fechas
    fecha_alerta = models.DateTimeField(auto_now_add=True,
                                        verbose_name="Fecha de Alerta")
    fecha_revision = models.DateTimeField(null=True, blank=True,
                                          verbose_name="Fecha de RevisiÃ³n")
    fecha_resolucion = models.DateTimeField(null=True, blank=True,
                                            verbose_name="Fecha de ResoluciÃ³n")
    
    # GestiÃ³n
    asignado_a = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertas_asignadas',
        verbose_name="Asignado A"
    )
    resuelto_por = models.ForeignKey(
        CustomUser,
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
    
    # InformaciÃ³n adicional
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
        Crea una nueva alert a de seguridad
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
        
        # Si es crÃ­tica, enviar email inmediatamente
        if nivel_prioridad == 'CRITICAL':
            alerta.enviar_notificacion_email()
        
        return alerta
    
    def enviar_notificacion_email(self):
        """EnvÃ­a notificaciÃ³n por email a los administradores"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        if self.email_enviado:
            return
        
        try:
            # Obtener emails de administradores
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
"""
            
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                list(admins),
                fail_silently=True,
            )
            
            self.email_enviado = True
            self.save(update_fields=['email_enviado'])
            
        except Exception as e:
            # Log error pero no fallar
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error enviando email de alerta: {str(e)}")


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


# ============================================================================
# MODELOS POS (Stubs temporales para compatibilidad)
# ============================================================================

class TransaccionPOS(models.Model):
    """Stub temporal para transacciones POS"""
    transaction_id = models.CharField(max_length=100, unique=True)
    proveedor = models.CharField(max_length=50)
    terminal_id = models.CharField(max_length=50)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20)
    fecha_transaccion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Transacción POS"
        verbose_name_plural = "Transacciones POS"
        
    def __str__(self):
        return f"{self.transaction_id} - RDmakemigrations{self.monto}"


class TerminalEstudiante(models.Model):
    """Stub temporal para terminales POS"""
    terminal_id = models.CharField(max_length=50, unique=True)
    estudiante = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    proveedor = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Terminal-Estudiante"
        verbose_name_plural = "Terminales-Estudiantes"
    
    def __str__(self):
        return f"Terminal {self.terminal_id}"


# ============================================================================
# MODELOS POS (Stubs temporales para compatibilidad)
# ============================================================================

class TransaccionPOS(models.Model):
    """Stub temporal para transacciones POS"""
    transaction_id = models.CharField(max_length=100, unique=True)
    proveedor = models.CharField(max_length=50)
    terminal_id = models.CharField(max_length=50)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20)
    estudiante = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    factura_pagada = models.ForeignKey('Factura', on_delete=models.SET_NULL, null=True, blank=True)
    fecha_transaccion = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(auto_now=True)
    referencia = models.CharField(max_length=100, blank=True)
    datos_webhook = models.JSONField(default=dict, blank=True)
    tarjeta_ultimos_4 = models.CharField(max_length=4, blank=True)
    tipo_tarjeta = models.CharField(max_length=20, blank=True)
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Transacción POS"
        verbose_name_plural = "Transacciones POS"
        
    def __str__(self):
        return f"{self.transaction_id} - RD${self.monto}"


class TerminalEstudiante(models.Model):
    """Stub temporal para terminales POS"""
    terminal_id = models.CharField(max_length=50, unique=True)
    estudiante = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    proveedor = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Terminal-Estudiante"
        verbose_name_plural = "Terminales-Estudiantes"
    
    def __str__(self):
        return f"Terminal {self.terminal_id}"

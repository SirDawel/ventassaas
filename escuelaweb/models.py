import uuid
# Create your models here.

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):

        if not email:
            raise ValueError("El correo electrónico es obligatorio")
            
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
    """Define la ruta donde se guardarán las imágenes de perfil."""
    return os.path.join("uploads/profile_pictures/", f"user_{instance.id}_{filename}")

class CustomUser(AbstractBaseUser, PermissionsMixin):
    # Campos básicos de autenticación
    email = models.EmailField(unique=True, verbose_name="Correo electrónico")
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # Información personal
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
                                     help_text='Código de barras para ponchar asistencia')
    activation_token = models.CharField(max_length=100, blank=True, null=True)

    
    
        
    # Información escolar
    rol = models.CharField(
        max_length=20,
        choices=[
            ("Estudiante", "Estudiante"),
            ("Profesor", "Profesor"),
            ("Director", "Director"),
            ("Secretaria", "Secretaria"),
            ("Administrador", "Administrador"),
            ("Coordinador", "Coordinador"),
            ("Bibliotecario", "Bibliotecario"),
            ("Psicologo", "Psicólogo"),
            ("Otro", "Otro")
        ],
        default="Estudiante"
    )
    
    # Campos específicos por rol
    grado = models.CharField(max_length=50, null=True, blank=True)  # Para estudiantes
    seccion = models.CharField(max_length=10, null=True, blank=True)  # Para estudiantes
    especialidad = models.CharField(max_length=100, null=True, blank=True)  # Para profesores
    departamento = models.CharField(max_length=100, null=True, blank=True)  # Para profesores y personal administrativo
    cargo = models.CharField(max_length=100, null=True, blank=True)  # Para personal administrativo
    
    # Grupo familiar (para estudiantes)
    grupo_familiar = models.ForeignKey(
        'GrupoFamiliar',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='estudiantes',
        verbose_name="Grupo Familiar",
        help_text="Grupo familiar al que pertenece el estudiante"
    )
    
    # Configuración de mora para estudiantes individuales
    porcentaje_mora_individual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Porcentaje de Mora Individual (%)",
        help_text="Porcentaje de mora para este estudiante (solo si no está en un grupo familiar)"
    )
    
    dia_vencimiento_individual = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name="Día de Vencimiento Individual",
        help_text="Día del mes para vencimiento de pago (solo si no está en un grupo familiar)"
    )
    
    # Configuración de descuento para estudiantes individuales
    descuento_individual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Descuento Individual (%)",
        help_text="Porcentaje de descuento para este estudiante (solo si no está en un grupo familiar)"
    )
    
    # Información de contacto de emergencia
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
            ("Graduado", "Graduado"),
            ("Retirado", "Retirado")
        ],
        default="Activo"
    )
    notas = models.TextField(null=True, blank=True)
    
    # Campos de seguridad
    activation_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    
    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "rol"]

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_porcentaje_mora(self):
        """
        Obtiene el porcentaje de mora applicable al estudiante.
        Si está en un grupo familiar, usa el porcentaje del grupo.
        Si no, usa el porcentaje individual.
        """
        if self.grupo_familiar and self.grupo_familiar.porcentaje_mora > 0:
            return self.grupo_familiar.porcentaje_mora
        return self.porcentaje_mora_individual
    
    def get_dia_vencimiento(self):
        """
        Obtiene el día de vencimiento para calcular mora.
        Si está en un grupo familiar, usa el día del grupo.
        Si no, usa el día individual.
        """
        if self.grupo_familiar:
            return self.grupo_familiar.dia_vencimiento
        return self.dia_vencimiento_individual
    
    def get_descuento(self):
        """
        Obtiene el porcentaje de descuento aplicable al estudiante.
        Si está en un grupo familiar, usa el descuento del grupo.
        Si no, usa el descuento individual.
        """
        if self.grupo_familiar and self.grupo_familiar.descuento_general > 0:
            return self.grupo_familiar.descuento_general
        return self.descuento_individual
    
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
        # restar 1 si no ha cumplido años este año
        if (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day):
            edad -= 1
        return edad

class Tutor(models.Model):
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

#   Año Escolar Modelo

# ==============================



class AnhoEscolar(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Año Escolar'
        verbose_name_plural = 'Años Escolares'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if self.activo:
            # Desactivar otros años escolares activos
            AnhoEscolar.objects.filter(activo=True).exclude(pk=self.pk).update(activo=False)
        super().save(*args, **kwargs)


class Mensualidad(models.Model):
    """Registro de cargos mensuales por estudiante (mensualidades).
    Se crea una entrada por (estudiante, año escolar, mes) y puede vincularse a una factura cuando se cobra.
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('parcial', 'Pago Parcial'),
        ('pagada', 'Pagada'),
        ('anulada', 'Anulada'),
    ]

    estudiante = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='mensualidades', limit_choices_to={'rol': 'Estudiante'})
    anho_escolar = models.ForeignKey(AnhoEscolar, on_delete=models.PROTECT, related_name='mensualidades')
    from django.core.validators import MinValueValidator, MaxValueValidator
    mes = models.IntegerField(help_text='Mes numérico (1-12)', validators=[MinValueValidator(1), MaxValueValidator(12)])
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
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profesor')
    especialidad = models.CharField(max_length=100, null=True, blank=True)
    departamento = models.CharField(max_length=100, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()}"

class Curso(models.Model):
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
        ('periodo', 'Por Períodos'),
        ('modular', 'Modular'),
    ]
    
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    creditos = models.PositiveIntegerField(default=1)
    categoria = models.CharField(
        max_length=20, 
        choices=CATEGORIA_CHOICES, 
        default='periodo',
        verbose_name='Categoría de Evaluación',
        help_text='Por Períodos: calificaciones por período (P1, P2, P3). Modular: evaluación continua.'
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='materias')
    profesor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='materias_impartidas')
    estudiantes = models.ManyToManyField(CustomUser, through='Matricula', related_name='materias_inscritas')
    
    # Días en que se imparte la materia
    lunes = models.BooleanField(default=False, verbose_name='Lunes')
    martes = models.BooleanField(default=False, verbose_name='Martes')
    miercoles = models.BooleanField(default=False, verbose_name='Miércoles')
    jueves = models.BooleanField(default=False, verbose_name='Jueves')
    viernes = models.BooleanField(default=False, verbose_name='Viernes')
    
    # Configuración de Resultados de Aprendizaje (RA) para materias modulares
    # Ejemplo: {"cantidad": 7, "valores": [15, 15, 15, 15, 10, 15, 15]} (suma debe ser 100)
    ra_configuracion = models.JSONField(null=True, blank=True, help_text="Configuración de RA: cantidad y valores en % (solo modular)")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"
    
    def dias_semana(self):
        """Retorna una lista de días en que se imparte la materia"""
        dias = []
        if self.lunes: dias.append('Lunes')
        if self.martes: dias.append('Martes')
        if self.miercoles: dias.append('Miércoles')
        if self.jueves: dias.append('Jueves')
        if self.viernes: dias.append('Viernes')
        return dias
    
    def se_imparte_hoy(self):
        """Verifica si la materia se imparte hoy según el día de la semana"""
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
    estudiante = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='matriculas')
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='matriculas')
    anho_escolar = models.ForeignKey(AnhoEscolar, on_delete=models.CASCADE, related_name='matriculas')

    # ------------------------
    # Notas por competencia
    # ------------------------
    com_p1 = models.FloatField(null=True, blank=True)
    com_p2 = models.FloatField(null=True, blank=True)
    com_p3 = models.FloatField(null=True, blank=True)
    com_p4 = models.FloatField(null=True, blank=True)
    com_rp = models.FloatField(null=True, blank=True)

    log_p1 = models.FloatField(null=True, blank=True)
    log_p2 = models.FloatField(null=True, blank=True)
    log_p3 = models.FloatField(null=True, blank=True)
    log_p4 = models.FloatField(null=True, blank=True)
    log_rp = models.FloatField(null=True, blank=True)

    cie_p1 = models.FloatField(null=True, blank=True)
    cie_p2 = models.FloatField(null=True, blank=True)
    cie_p3 = models.FloatField(null=True, blank=True)
    cie_p4 = models.FloatField(null=True, blank=True)
    cie_rp = models.FloatField(null=True, blank=True)

    eti_p1 = models.FloatField(null=True, blank=True)
    eti_p2 = models.FloatField(null=True, blank=True)
    eti_p3 = models.FloatField(null=True, blank=True)
    eti_p4 = models.FloatField(null=True, blank=True)
    eti_rp = models.FloatField(null=True, blank=True)

    # ------------------------
    # Exámenes finales
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
    # Función interna con redondeo correcto
    # ------------------------
    def _calc_promedio(self, notas):
        """Calcula el promedio de una lista de notas usando redondeo matemático estándar"""
        from .utils_notas import redondear_promedio
        return redondear_promedio(notas)

    # ------------------------
    # Promedios por competencia
    # ------------------------
    @property
    def prom_comunicativa(self):
        prom = self._calc_promedio([self.com_p1, self.com_p2, self.com_p3, self.com_p4])
        if prom is None:
            return None
        # Si tiene recuperación y el promedio es menor a 70, usar la recuperación
        if prom < 70 and self.com_rp:
            from .utils_notas import redondear_nota
            return redondear_nota(float(self.com_rp), decimales=2)
        return prom

    @property
    def prom_logico(self):
        prom = self._calc_promedio([self.log_p1, self.log_p2, self.log_p3, self.log_p4])
        if prom is None:
            return None
        # Si tiene recuperación y el promedio es menor a 70, usar la recuperación
        if prom < 70 and self.log_rp:
            from .utils_notas import redondear_nota
            return redondear_nota(float(self.log_rp), decimales=2)
        return prom

    @property
    def prom_cientifica(self):
        prom = self._calc_promedio([self.cie_p1, self.cie_p2, self.cie_p3, self.cie_p4])
        if prom is None:
            return None
        # Si tiene recuperación y el promedio es menor a 70, usar la recuperación
        if prom < 70 and self.cie_rp:
            from .utils_notas import redondear_nota
            return redondear_nota(float(self.cie_rp), decimales=2)
        return prom

    @property
    def prom_etica(self):
        prom = self._calc_promedio([self.eti_p1, self.eti_p2, self.eti_p3, self.eti_p4])
        if prom is None:
            return None
        # Si tiene recuperación y el promedio es menor a 70, usar la recuperación
        if prom < 70 and self.eti_rp:
            from .utils_notas import redondear_nota
            return redondear_nota(float(self.eti_rp), decimales=2)
        return prom

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
    # Cálculo COMPLETIVO final
    # ------------------------
    @property
    def calificacion_completiva_final(self):
        from .utils_notas import calcular_nota_completiva
        return calcular_nota_completiva(self.promedio_final, self.ex_com)
    

    # ------------------------
    # Cálculo EXTRAORDINARIO final
    # 30% promedio + 70% examen extraordinario
    # ------------------------
    @property
    def calificacion_extraordinario_final(self):
        from .utils_notas import calcular_nota_extraordinaria
        return calcular_nota_extraordinaria(self.promedio_final, self.ex_ext)
    

    # ------------------------
    # Cálculo ESPECIAL final
    # solo examen especial
    # ------------------------
    @property
    def calificacion_especial_final(self):
        return self.ex_esp if self.ex_esp is not None else None

    
    @property
    def estado(self):
        if self.promedio_final is None:
            return "En proceso"
        if self.promedio_final >= 70:
            return "Aprobado"
        return "Reprobado"

    # -------- META CORRECTA -------
    class Meta:
        indexes = [
            models.Index(fields=["estudiante"]),
            models.Index(fields=["materia"]),
            models.Index(fields=["anho_escolar"]),
        ]


# Signal para actualizar grado y sección del estudiante cuando se crea/actualiza una matrícula
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
    
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='asistencias_personal', 
                                help_text='Usuario (Estudiante, Profesor o personal administrativo)')
    fecha = models.DateField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='presente')
    hora_entrada = models.TimeField(null=True, blank=True, help_text='Hora de entrada registrada')
    hora_salida = models.TimeField(null=True, blank=True, help_text='Hora de salida registrada')
    observaciones = models.TextField(blank=True, null=True)
    registrado_por = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, 
                                       related_name='asistencias_personal_registradas',
                                       help_text='Usuario que registró la asistencia (Secretaria)')
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
    """Conceptos de pago: mensualidades, servicios, artículos, etc."""
    TIPO_CHOICES = [
        ('mensualidad', 'Mensualidad'),
        ('inscripcion', 'Inscripción'),
        ('transporte', 'Transporte'),
        ('articulo', 'Artículo/Papelería'),
        ('servicio', 'Servicio'),
        ('otro', 'Otro'),
    ]
    
    nombre = models.CharField(max_length=200, verbose_name="Nombre del concepto")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='mensualidad')
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto base")
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    es_estandar = models.BooleanField(default=False, verbose_name="Tarifa Estándar", 
                                       help_text="Se asignará automáticamente a nuevos estudiantes")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Concepto de Pago"
        verbose_name_plural = "Conceptos de Pago"
        ordering = ['tipo', 'nombre']
    
    def __str__(self):
        # Para mensualidad, inscripción y transporte, no mostrar el monto (viene de la tarifa del estudiante)
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
    
    estudiante = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='pagos',
        limit_choices_to={'rol': 'Estudiante'}
    )
    concepto = models.ForeignKey(ConceptoPago, on_delete=models.PROTECT, related_name='pagos')
    anho_escolar = models.ForeignKey(AnhoEscolar, on_delete=models.CASCADE, related_name='pagos')
    
    # Información del pago
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
    mes = models.IntegerField(blank=True, null=True, help_text="Mes del año (1-12)", validators=[MinValueValidator(1), MaxValueValidator(12)])
    anio = models.IntegerField(blank=True, null=True)
    
    # Información adicional
    observaciones = models.TextField(blank=True, null=True)
    recibo_numero = models.CharField(max_length=50, unique=True, blank=True, null=True)
    referencia = models.CharField(max_length=100, blank=True, null=True, help_text="Número de referencia/transacción")
    
    # Auditoría
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
        """Verifica si el pago está completado"""
        return self.monto_pagado >= self.monto_total
    
    def save(self, *args, **kwargs):
        # Actualizar estado según montos
        if self.monto_pagado >= self.monto_total:
            self.estado = 'pagado'
        elif self.monto_pagado > 0:
            self.estado = 'parcial'
        
        # Generar número de recibo si no existe
        if not self.recibo_numero and self.estado == 'pagado':
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.recibo_numero = f"REC-{timestamp}-{self.id or ''}"
        
        super().save(*args, **kwargs)


class TarifaEstudiante(models.Model):
    """Tarifa personalizada asignada a un estudiante para mensualidades, inscripción y transporte."""
    
    estudiante = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='tarifas', 
        limit_choices_to={'rol': 'Estudiante'}
    )
    concepto = models.ForeignKey(
        ConceptoPago, 
        on_delete=models.PROTECT,
        null=True,  # Temporal para migración
        blank=True,
        limit_choices_to={'tipo__in': ['mensualidad', 'inscripcion', 'transporte']},
        help_text='Solo conceptos de tipo mensualidad, inscripción o transporte'
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
    
    # Día de vencimiento para cálculo de mora (si null, usa el del grupo familiar)
    dia_vencimiento = models.IntegerField(
        default=None,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text='Día del mes para vencimiento de pago (1-31). Si no se especifica, usa el del grupo familiar.'
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
        """Obtiene el día de vencimiento, usa el del estudiante si está definido, sino el del grupo familiar."""
        if self.dia_vencimiento:
            return self.dia_vencimiento
        if self.estudiante.grupo_familiar:
            return self.estudiante.grupo_familiar.dia_vencimiento
        return 10  # Default si no tiene grupo familiar


# ===========================
# SISTEMA DE FACTURACIÓN
# ===========================

class Factura(models.Model):
    """Factura principal para cobros de estudiantes"""
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
    
    # Información básica
    numero_factura = models.CharField(max_length=50, unique=True, db_index=True)
    cliente = models.ForeignKey(
        CustomUser, 
        on_delete=models.PROTECT, 
        related_name='facturas',
        limit_choices_to={'rol': 'Estudiante'},
        verbose_name="Cliente/Estudiante"
    )
    anho_escolar = models.ForeignKey(AnhoEscolar, on_delete=models.CASCADE, related_name='facturas')
    
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
    
    # Estado y método de pago
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', db_index=True)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, blank=True, null=True)
    
    # Información adicional
    observaciones = models.TextField(blank=True, null=True)
    notas_internas = models.TextField(blank=True, null=True)
    
    # Auditoría
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
        """Verifica si la factura está completamente pagada"""
        return self.monto_pagado >= self.total
    
    def esta_vencida(self):
        """Verifica si la factura está vencida"""
        if not self.fecha_vencimiento:
            return False
        from datetime import date
        return date.today() > self.fecha_vencimiento and self.estado not in ['pagada', 'anulada']
    
    def calcular_mora(self):
        """
        Calcula el monto de mora si la factura está vencida.
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
        """Recalcula los totales de la factura basándose en los detalles"""
        detalles = self.detalles.all()
        self.subtotal = sum(detalle.get_total() for detalle in detalles)
        self.total = self.subtotal - self.descuento + self.impuesto
        # NO guardar aquí para evitar recursión, el guardado debe hacerse desde donde se llama
        
    def actualizar_estado(self):
        """Actualiza el estado de la factura según el monto pagado"""
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
        
        super().save(*args, **kwargs)


class DetalleFactura(models.Model):
    """Detalle de items/conceptos de una factura"""
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='detalles')
    mensualidad = models.ForeignKey('Mensualidad', on_delete=models.SET_NULL, null=True, blank=True, related_name='detalles')
    concepto = models.ForeignKey(ConceptoPago, on_delete=models.PROTECT, null=True, blank=True)
    articulo = models.ForeignKey('Articulo', on_delete=models.PROTECT, null=True, blank=True, 
                                  related_name='detalles_factura',
                                  help_text='Artículo del inventario (si aplica)')
    
    # Información del item
    descripcion = models.CharField(max_length=255, help_text="Descripción del concepto")
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Para mensualidades
    mes = models.IntegerField(blank=True, null=True, help_text="Mes del año (1-12)")
    anio = models.IntegerField(blank=True, null=True)
    
    # Información adicional
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
        # Si está vinculada a una Mensualidad, sincronizar mes/anio y validar
        if self.mensualidad:
            try:
                m = self.mensualidad
                # Si se proporcionaron mes/anio explícitos y no coinciden, lanzar error
                if self.mes is not None and self.anio is not None:
                    if int(self.mes) != int(m.mes) or int(self.anio) != int(m.anio):
                        from django.core.exceptions import ValidationError
                        raise ValidationError('El mes/año del detalle no coincide con la Mensualidad vinculada.')
                # Copiar valores desde Mensualidad
                self.mes = m.mes
                self.anio = m.anio
            except Exception:
                # No interrumpir el guardado por errores en la sincronización; permitir que se loguee posteriormente
                pass

        # Usar descripción del concepto o artículo si no se proporciona
        if not self.descripcion:
            if self.concepto:
                self.descripcion = self.concepto.nombre
            elif self.articulo:
                self.descripcion = self.articulo.nombre

        # Guardar primero el detalle
        super().save(*args, **kwargs)

        # Actualizar totales de la factura (sin recursión)
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
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
        ('cheque', 'Cheque'),
    ]
    
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='pagos')
    
    # Información del pago
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    
    # Detalles del pago
    referencia = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="Número de referencia/transacción/cheque"
    )
    banco = models.CharField(max_length=100, blank=True, null=True)
    numero_recibo = models.CharField(max_length=50, unique=True, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    
    # Auditoría
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
        # Generar número de recibo si no existe
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

        # Si la factura quedó pagada, marcar mensualidades asociadas como pagadas
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
    """Código de seguridad mensual para anular facturas"""
    mes = models.IntegerField()  # 1-12
    anio = models.IntegerField()  # 2026, 2027, etc.
    codigo = models.CharField(max_length=10)
    creado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Código de Anulación"
        verbose_name_plural = "Códigos de Anulación"
        unique_together = ['mes', 'anio']
        ordering = ['-anio', '-mes']
    
    def __str__(self):
        from datetime import date
        try:
            mes_nombre = date(self.anio, self.mes, 1).strftime('%B %Y')
            return f"Código {mes_nombre}: {self.codigo}"
        except:
            return f"Código {self.mes}/{self.anio}: {self.codigo}"
    
    @staticmethod
    def generar_codigo():
        """Genera un código aleatorio de 8 caracteres (letras y números)"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    @staticmethod
    def obtener_codigo_actual():
        """Obtiene o crea el código del mes actual"""
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
        """Valida si el código ingresado es correcto para el mes actual"""
        codigo_actual = CodigoAnulacion.obtener_codigo_actual()
        return codigo_ingresado.upper().strip() == codigo_actual.codigo.upper().strip()


class CategoriaArticulo(models.Model):
    """Categorías para organizar artículos del inventario"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activa = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Categoría de Artículo"
        verbose_name_plural = "Categorías de Artículos"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Articulo(models.Model):
    """Artículos del inventario para usar en facturas"""
    TIPO_CHOICES = [
        ('producto', 'Producto'),
        ('servicio', 'Servicio'),
    ]
    
    codigo_barras = models.CharField(max_length=100, unique=True, blank=True, default='',
                                      help_text='Código de barras para lector óptico')
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
        verbose_name = "Artículo"
        verbose_name_plural = "Artículos"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['codigo_barras']),
            models.Index(fields=['nombre']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.codigo_barras} - {self.nombre}"
    
    def save(self, *args, **kwargs):
        # Generar código de barras automático si no existe
        if not self.codigo_barras:
            from datetime import datetime
            import random
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_suffix = random.randint(100, 999)
            self.codigo_barras = f"ART{timestamp}{random_suffix}"
        super().save(*args, **kwargs)
    
    @property
    def stock_bajo(self):
        """Indica si el stock está por debajo del mínimo"""
        return self.stock_actual <= self.stock_minimo
    
    @property
    def margen_ganancia(self):
        """Calcula el margen de ganancia porcentual"""
        if self.precio_compra > 0:
            return ((self.precio_venta - self.precio_compra) / self.precio_compra) * 100
        return 0
    
    def ajustar_stock(self, cantidad, tipo='entrada'):
        """Ajusta el stock del artículo"""
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
        ('devolucion', 'Devolución'),
    ]
    
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


class GrupoFamiliar(models.Model):
    """Grupos familiares para pagos consolidados de mensualidades"""
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
# MÓDULO DE CONTABILIDAD
# ============================================

class PlanCuentas(models.Model):
    """
    Plan de Cuentas Contable - Catálogo de cuentas contables
    Este modelo representa el catálogo de cuentas utilizado para registrar
    todas las operaciones contables de la institución.
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
    
    codigo = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name="Código de Cuenta",
        help_text="Código único de la cuenta (ej: 1.1.01.001)"
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre de la Cuenta",
        help_text="Nombre descriptivo de la cuenta contable"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
        help_text="Descripción detallada del uso de esta cuenta"
    )
    
    tipo_cuenta = models.CharField(
        max_length=10,
        choices=TIPO_CUENTA_CHOICES,
        verbose_name="Tipo de Cuenta",
        help_text="Clasificación principal de la cuenta"
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
        help_text="Nivel jerárquico de la cuenta (1=Mayor, 2=Submayer, 3=Auxiliar, etc.)"
    )
    
    cuenta_padre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcuentas',
        verbose_name="Cuenta Padre",
        help_text="Cuenta superior en la jerarquía"
    )
    
    es_detalle = models.BooleanField(
        default=True,
        verbose_name="Es Cuenta de Detalle",
        help_text="Indica si la cuenta acepta movimientos directos (True) o es solo agrupadora (False)"
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si la cuenta está activa para uso"
    )
    
    # Campos de control
    saldo_inicial = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Inicial",
        help_text="Saldo inicial de la cuenta al inicio del período contable"
    )
    
    saldo_actual = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Actual",
        help_text="Saldo actual de la cuenta"
    )
    
    # Campos de auditoría
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
        """Override save para calcular el nivel automáticamente basado en el código"""
        # Calcular nivel basado en los puntos en el código
        self.nivel = self.codigo.count('.') + 1
        
        # Establecer naturaleza por defecto según tipo de cuenta
        if not self.naturaleza:
            if self.tipo_cuenta in ['ACTIVO', 'GASTO', 'COSTO']:
                self.naturaleza = 'DEUDORA'
            else:
                self.naturaleza = 'ACREEDORA'
        
        super().save(*args, **kwargs)
    
    def get_codigo_completo(self):
        """Retorna el código completo con padding para ordenamiento"""
        return self.codigo.ljust(20, '0')
    
    def get_saldo_formateado(self):
        """Retorna el saldo formateado con el símbolo de moneda"""
        return f"${self.saldo_actual:,.2f}"
    
    def tiene_movimientos(self):
        """Verifica si la cuenta tiene movimientos asociados"""
        return self.movimientos_debito.exists() or self.movimientos_credito.exists()
    
    def puede_eliminarse(self):
        """Verifica si la cuenta puede ser eliminada"""
        return not self.tiene_movimientos() and not self.subcuentas.exists()
    
    def get_ruta_completa(self):
        """Retorna la ruta completa de la cuenta en la jerarquía"""
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
        
        # Obtener suma de débitos y créditos
        total_debito = self.movimientos_debito.aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        total_credito = self.movimientos_credito.aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        # Calcular saldo según naturaleza
        if self.naturaleza == 'DEUDORA':
            saldo = self.saldo_inicial + total_debito - total_credito
        else:
            saldo = self.saldo_inicial + total_credito - total_debito
        
        return saldo


class AsientoContable(models.Model):
    """
    Asiento Contable - Registro de transacciones contables
    Representa la cabecera de un asiento contable que agrupa varios movimientos
    bajo el principio de partida doble (débitos = créditos)
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
    
    numero_asiento = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name="Número de Asiento",
        help_text="Número único del asiento (ej: ASI-2026-001)"
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
        help_text="Clasificación del asiento contable"
    )
    
    concepto = models.TextField(
        verbose_name="Concepto/Descripción",
        help_text="Descripción general del asiento contable"
    )
    
    referencia = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Referencia",
        help_text="Referencia externa (número de factura, recibo, etc.)"
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
        verbose_name="Total Débito",
        help_text="Suma total de los débitos"
    )
    
    total_credito = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Crédito",
        help_text="Suma total de los créditos"
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    fecha_contabilizacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de Contabilización",
        help_text="Fecha en que se contabilizó el asiento"
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
        verbose_name="Motivo de Anulación",
        help_text="Razón por la cual se anuló el asiento"
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
        """Verifica si el asiento está cuadrado (débito = crédito)"""
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
        """Calcula los totales de débito y crédito del asiento"""
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
        """Retorna la diferencia entre débito y crédito"""
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
    Cada línea representa un débito o crédito en una cuenta específica
    """
    
    asiento = models.ForeignKey(
        AsientoContable,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Asiento Contable"
    )
    
    linea = models.IntegerField(
        default=1,
        verbose_name="Línea",
        help_text="Número de línea dentro del asiento"
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
        verbose_name="Descripción",
        help_text="Descripción específica de este movimiento"
    )
    
    debito = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Débito",
        help_text="Monto del débito"
    )
    
    credito = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Crédito",
        help_text="Monto del crédito"
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
        return f"{self.asiento.numero_asiento} - Línea {self.linea}: {self.cuenta.codigo}"
    
    def clean(self):
        """Validaciones del modelo"""
        from django.core.exceptions import ValidationError
        
        # No puede tener débito y crédito al mismo tiempo
        if self.debito > 0 and self.credito > 0:
            raise ValidationError('Una línea no puede tener débito y crédito simultáneamente')
        
        # Debe tener débito o crédito (no ambos en cero)
        if self.debito == 0 and self.credito == 0:
            raise ValidationError('Debe especificar un monto en débito o crédito')
        
        # Verificar que la cuenta sea de detalle
        if not self.cuenta.es_detalle:
            raise ValidationError('Solo se pueden usar cuentas de detalle en los asientos')
        
        # Verificar que la cuenta esté activa
        if not self.cuenta.activo:
            raise ValidationError('La cuenta no está activa')
        
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
        """Retorna el monto formateado según sea débito o crédito"""
        if self.debito > 0:
            return f"${self.debito:,.2f} (D)"
        else:
            return f"${self.credito:,.2f} (C)"
    
    def get_tipo_movimiento(self):
        """Retorna el tipo de movimiento (débito o crédito)"""
        return 'DEBITO' if self.debito > 0 else 'CREDITO'


# ============================================
# MODELOS DE SEGURIDAD
# ============================================

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
        CustomUser,
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
    def unblock_account(cls, email):
        """
        Desbloquea una cuenta eliminando todos los intentos fallidos recientes
        Retorna la cantidad de intentos eliminados
        """
        cutoff_time = timezone.now() - timedelta(minutes=15)
        deleted_count = cls.objects.filter(
            email=email,
            exitoso=False,
            fecha__gte=cutoff_time
        ).delete()[0]
        return deleted_count
    
    @classmethod
    def get_blocked_accounts(cls, max_attempts=5, block_minutes=15):
        """
        Retorna una lista de emails de cuentas actualmente bloqueadas
        """
        from django.db.models import Count
        cutoff_time = timezone.now() - timedelta(minutes=block_minutes)
        
        # Agrupar por email y contar intentos fallidos recientes
        blocked = cls.objects.filter(
            exitoso=False,
            fecha__gte=cutoff_time
        ).values('email').annotate(
            intentos_fallidos=Count('id')
        ).filter(
            intentos_fallidos__gte=max_attempts
        )
        
        return [item['email'] for item in blocked]
    
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
        CustomUser,
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
        CustomUser,
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


# ====================================================================
#  SISTEMA DE LISTAS DE COTEJO
# ====================================================================

class ListaCotejo(models.Model):
    """
    Plantilla de lista de cotejo que puede ser reutilizada.
    Define los parámetros generales de la evaluación.
    """
    TIPO_EVALUACION_CHOICES = [
        ('actividad', 'Actividad Específica'),
        ('proceso', 'Evaluación de Proceso'),
        ('proyecto', 'Proyecto'),
        ('comportamiento', 'Evaluación de Comportamiento'),
        ('cuaderno', 'Evaluación de Cuaderno'),
        ('participacion', 'Participación'),
        ('otro', 'Otro'),
    ]
    
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre de la Lista",
        help_text="Ej: Lista de cotejo para evaluar la participación"
    )
    
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
        help_text="Descripción detallada del propósito de esta lista"
    )
    
    tipo_evaluacion = models.CharField(
        max_length=20,
        choices=TIPO_EVALUACION_CHOICES,
        default='actividad',
        verbose_name="Tipo de Evaluación"
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
        help_text="Puntaje máximo que se puede obtener (usualmente 10)"
    )
    
    es_plantilla = models.BooleanField(
        default=True,
        verbose_name="Es Plantilla Reutilizable",
        help_text="Si es True, esta lista puede ser utilizada múltiples veces"
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name="Activa"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Modificación"
    )
    
    orden_criterios = models.CharField(
        max_length=20,
        choices=[('manual', 'Manual'), ('alfabetico', 'Alfabético')],
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
        """Retorna el número total de criterios"""
        return self.criterios.count()
    
    def validar_puntajes(self):
        """Valida que la suma de puntajes de los criterios sea igual al puntaje total"""
        suma = sum([c.puntaje_maximo for c in self.criterios.all()])
        return suma == float(self.puntaje_total)


class CriterioListaCotejo(models.Model):
    """
    Criterio individual dentro de una lista de cotejo.
    Puede ser de tipo binario (check), numérico o escala.
    """
    TIPO_CRITERIO_CHOICES = [
        ('binario', 'Binario (✓/✗ - Sí/No)'),
        ('numerico', 'Numérico (0-10)'),
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
        verbose_name="Descripción del Criterio",
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
        verbose_name="Puntaje Máximo",
        help_text="Puntos que vale este criterio"
    )
    
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden",
        help_text="Orden de aparición en la lista (menor número = primero)"
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
        """Retorna el valor máximo según el tipo de criterio"""
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
    Aplicación de una lista de cotejo a un grupo específico de estudiantes.
    Representa una evaluación concreta en una fecha determinada.
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
        verbose_name="Nombre de la Evaluación",
        help_text="Ej: Evaluación de participación - Marzo 2026"
    )
    
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción"
    )
    
    fecha_evaluacion = models.DateField(
        verbose_name="Fecha de Evaluación"
    )
    
    fecha_limite = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha Límite para Calificar"
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
        help_text="Si esta evaluación debe sumarse al promedio de la materia"
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
        verbose_name="Fecha de Creación"
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Modificación"
    )
    
    fecha_publicacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Publicación"
    )
    
    class Meta:
        verbose_name = "Evaluación con Lista de Cotejo"
        verbose_name_plural = "Evaluaciones con Listas de Cotejo"
        ordering = ['-fecha_evaluacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.curso.nombre}"
    
    def total_estudiantes(self):
        """Retorna el número total de estudiantes en el curso para esta materia"""
        # Obtener estudiantes matriculados en la materia
        # La materia ya pertenece a un curso específico
        return Matricula.objects.filter(
            materia=self.materia
        ).values('estudiante').distinct().count()
    
    def estudiantes_evaluados(self):
        """Retorna el número de estudiantes con calificaciones completas"""
        total_criterios = self.lista_cotejo.criterios.filter(activo=True).count()
        if total_criterios == 0:
            return 0
        
        estudiantes_completos = 0
        
        # Obtener estudiantes únicos con calificaciones
        estudiantes_ids = self.calificaciones.values_list('estudiante_id', flat=True).distinct()
        
        for estudiante_id in estudiantes_ids:
            califs = self.calificaciones.filter(estudiante_id=estudiante_id).count()
            if califs >= total_criterios:
                estudiantes_completos += 1
        
        return estudiantes_completos
    
    def porcentaje_completado(self):
        """Retorna el porcentaje de evaluación completada"""
        total = self.total_estudiantes()
        if total == 0:
            return 0
        evaluados = self.estudiantes_evaluados()
        return round((evaluados / total) * 100, 2)
    
    def publicar(self):
        """Publica la evaluación y la hace visible para estudiantes"""
        self.estado = 'publicada'
        self.fecha_publicacion = timezone.now()
        self.save()


class CalificacionCotejo(models.Model):
    """
    Calificación individual de un criterio para un estudiante específico.
    Guarda el valor obtenido por el estudiante en cada criterio.
    """
    evaluacion = models.ForeignKey(
        EvaluacionListaCotejo,
        on_delete=models.CASCADE,
        related_name='calificaciones',
        verbose_name="Evaluación"
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
        help_text="Valor según el tipo de criterio"
    )
    
    cumple = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Cumple (Para criterios binarios)"
    )
    
    observacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observación",
        help_text="Comentario específico sobre este criterio para este estudiante"
    )
    
    fecha_calificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Calificación"
    )
    
    calificado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='calificaciones_cotejo_realizadas',
        verbose_name="Calificado Por"
    )
    
    class Meta:
        verbose_name = "Calificación de Cotejo"
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
    Resumen consolidado de la evaluación de un estudiante.
    Se calcula automáticamente basado en las calificaciones individuales.
    """
    evaluacion = models.ForeignKey(
        EvaluacionListaCotejo,
        on_delete=models.CASCADE,
        related_name='resumenes',
        verbose_name="Evaluación"
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
        verbose_name="Puntaje Máximo"
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
        verbose_name="Evaluación Completa"
    )
    
    fecha_calculo = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Cálculo"
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones Generales"
    )
    
    class Meta:
        verbose_name = "Resumen de Evaluación de Cotejo"
        verbose_name_plural = "Resúmenes de Evaluaciones de Cotejo"
        unique_together = ['evaluacion', 'estudiante']
        ordering = ['estudiante__first_name', 'estudiante__last_name']
    
    def __str__(self):
        return f"{self.estudiante.get_full_name()} - {self.puntaje_obtenido}/{self.puntaje_maximo}"
    
    def calcular_puntaje(self):
        """Calcula el puntaje total del estudiante en esta evaluación"""
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
    Evaluación diagnóstica para identificar conocimientos previos y nivel inicial del estudiante.
    Conforme al sistema educativo de la República Dominicana.
    """
    PERIODO_CHOICES = [
        ('inicio_anho', 'Inicio de Año Escolar'),
        ('inicio_periodo_1', 'Inicio Primer Período'),
        ('inicio_periodo_2', 'Inicio Segundo Período'),
        ('inicio_periodo_3', 'Inicio Tercer Período'),
        ('inicio_periodo_4', 'Inicio Cuarto Período'),
        ('inicio_unidad', 'Inicio de Unidad Didáctica'),
    ]
    
    INSTRUMENTO_CHOICES = [
        ('prueba_escrita', 'Prueba Escrita'),
        ('prueba_oral', 'Prueba Oral'),
        ('observacion', 'Observación Directa'),
        ('practica', 'Prueba Práctica'),
        ('mixta', 'Mixta'),
    ]
    
    materia = models.ForeignKey(
        'Materia',
        on_delete=models.CASCADE,
        related_name='evaluaciones_diagnosticas',
        verbose_name="Materia/Asignatura"
    )
    
    periodo = models.CharField(
        max_length=20,
        choices=PERIODO_CHOICES,
        verbose_name="Período de Aplicación"
    )
    
    competencia = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Competencia a Evaluar",
        help_text="Ej: Competencia Comunicativa, Pensamiento Lógico, Resolución de Problemas"
    )
    
    indicadores = models.TextField(
        blank=True,
        null=True,
        verbose_name="Indicadores de Logro",
        help_text="Lista de indicadores de logro que se evaluarán"
    )
    
    fecha_aplicacion = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Aplicación"
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
        help_text="Anotaciones adicionales sobre la evaluación"
    )
    
    creado_por = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='evaluaciones_diagnosticas_creadas',
        verbose_name="Creado por"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Modificación"
    )
    
    class Meta:
        verbose_name = "Evaluación Diagnóstica"
        verbose_name_plural = "Evaluaciones Diagnósticas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.materia.nombre} - {self.get_periodo_display()} ({self.fecha_creacion.strftime('%d/%m/%Y')})"
    
    def get_curso(self):
        """Retorna el curso asociado a través de la materia"""
        return self.materia.curso
    
    def total_estudiantes(self):
        """Retorna el número total de estudiantes en el curso para esta materia"""
        return Matricula.objects.filter(materia=self.materia).values('estudiante').distinct().count()
    
    def estudiantes_evaluados(self):
        """Retorna el número de estudiantes evaluados"""
        return self.resultados.values('estudiante').distinct().count()
    
    def porcentaje_completado(self):
        """Retorna el porcentaje de evaluación completada"""
        total = self.total_estudiantes()
        if total == 0:
            return 0
        evaluados = self.estudiantes_evaluados()
        return round((evaluados / total) * 100, 2)


class ResultadoEvaluacionDiagnostica(models.Model):
    """
    Resultado individual de un estudiante en una evaluación diagnóstica.
    Registra el nivel de logro y observaciones específicas.
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
        verbose_name="Evaluación Diagnóstica"
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
        help_text="Puntaje numérico obtenido (opcional)"
    )
    
    puntaje_total = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Puntaje Total",
        help_text="Puntaje total de la evaluación (opcional)"
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
        verbose_name="Áreas de Mejora",
        help_text="Aspectos que requieren refuerzo o intervención"
    )
    
    recomendaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Recomendaciones",
        help_text="Estrategias pedagógicas sugeridas para este estudiante"
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones Generales"
    )
    
    fecha_evaluacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Evaluación"
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Modificación"
    )
    
    evaluado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='evaluaciones_diagnosticas_realizadas',
        verbose_name="Evaluado Por"
    )
    
    class Meta:
        verbose_name = "Resultado de Evaluación Diagnóstica"
        verbose_name_plural = "Resultados de Evaluaciones Diagnósticas"
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


# ==================== RÚBRICAS DE EVALUACIÓN ====================

class Rubrica(models.Model):
    """
    Rúbrica de evaluación: matriz de valoración con criterios y niveles de desempeño.
    Instrumento para evaluar competencias de forma objetiva y sistemática.
    """
    TIPO_ACTIVIDAD_CHOICES = [
        ('proyecto', 'Proyecto'),
        ('presentacion', 'Presentación Oral'),
        ('trabajo_escrito', 'Trabajo Escrito'),
        ('trabajo_grupo', 'Trabajo en Grupo'),
        ('experimentacion', 'Experimentación/Práctica'),
        ('exposicion', 'Exposición'),
        ('debate', 'Debate'),
        ('otro', 'Otro'),
    ]
    
    materia = models.ForeignKey(
        'Materia',
        on_delete=models.CASCADE,
        related_name='rubricas',
        verbose_name="Materia/Asignatura"
    )
    
    nombre = models.CharField(
        max_length=255,
        verbose_name="Nombre de la Rúbrica",
        help_text="Ej: Evaluación de Proyecto de Ciencias"
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
        verbose_name="Descripción",
        help_text="Descripción general de la rúbrica"
    )
    
    creado_por = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='rubricas_creadas',
        verbose_name="Creado Por"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Modificación"
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name="Activa",
        help_text="Indica si la rúbrica está activa para usar"
    )
    
    class Meta:
        verbose_name = "Rúbrica"
        verbose_name_plural = "Rúbricas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.materia.nombre}"
    
    def total_criterios(self):
        """Retorna el número total de criterios"""
        return self.criterios.count()
    
    def total_ponderacion(self):
        """Calcula la suma total de ponderaciones (debería ser 100%)"""
        from django.db.models import Sum
        total = self.criterios.aggregate(Sum('ponderacion'))['ponderacion__sum']
        return total if total else 0
    
    def puntaje_maximo(self):
        """Calcula el puntaje máximo posible con esta rúbrica"""
        # Cada criterio contribuye: puntaje_maximo_nivel (5.0) × ponderación
        # Luego se normaliza a escala de 10
        total = 0
        for criterio in self.criterios.all():
            # Puntaje máximo del criterio (nivel Excelente = 5.0)
            total += 5.0 * (float(criterio.ponderacion) / 100)
        # Normalizar a escala de 10
        return round(total * 2, 2) if total > 0 else 0
    
    def ponderacion_valida(self):
        """Verifica si las ponderaciones suman 100%"""
        total = self.total_ponderacion()
        return abs(float(total) - 100.0) < 0.01  # Tolerancia de 0.01%


class CriterioRubrica(models.Model):
    """
    Criterio de evaluación dentro de una rúbrica.
    Define un aspecto específico a evaluar.
    """
    rubrica = models.ForeignKey(
        Rubrica,
        on_delete=models.CASCADE,
        related_name='criterios',
        verbose_name="Rúbrica"
    )
    
    nombre = models.CharField(
        max_length=255,
        verbose_name="Nombre del Criterio",
        help_text="Ej: Contenido y Profundidad, Organización, Presentación Visual"
    )
    
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
        help_text="Descripción detallada de qué se evaluará en este criterio"
    )
    
    ponderacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.0,
        verbose_name="Ponderación (%)",
        help_text="Peso del criterio en la evaluación final (ej: 20.00%)"
    )
    
    orden = models.IntegerField(
        default=0,
        verbose_name="Orden",
        help_text="Orden de visualización del criterio"
    )
    
    class Meta:
        verbose_name = "Criterio de Rúbrica"
        verbose_name_plural = "Criterios de Rúbrica"
        ordering = ['rubrica', 'orden', 'id']
        unique_together = ['rubrica', 'nombre']
    
    def __str__(self):
        return f"{self.rubrica.nombre} - {self.nombre}"


class NivelDesempeno(models.Model):
    """
    Nivel de desempeño dentro de un criterio de rúbrica.
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
        verbose_name="Nivel de Desempeño"
    )
    
    puntaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Puntaje",
        help_text="Puntaje numérico para este nivel (1-5)"
    )
    
    descriptor = models.TextField(
        verbose_name="Descriptor",
        help_text="Descripción detallada de lo que caracteriza este nivel de desempeño"
    )
    
    class Meta:
        verbose_name = "Nivel de Desempeño"
        verbose_name_plural = "Niveles de Desempeño"
        ordering = ['-puntaje']
        unique_together = ['criterio', 'nivel']
    
    def __str__(self):
        return f"{self.criterio.nombre} - {self.get_nivel_display()}"


class EvaluacionRubrica(models.Model):
    """
    Evaluación aplicada a estudiantes usando una rúbrica
    Permite calificar desempeño en actividades/proyectos según criterios establecidos
    """
    rubrica = models.ForeignKey(
        Rubrica,
        on_delete=models.CASCADE,
        related_name='evaluaciones',
        verbose_name="Rúbrica"
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
        verbose_name="Título de la Evaluación",
        help_text="Nombre descriptivo de la evaluación (ej: Proyecto Final, Exposición Oral)"
    )
    
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
        help_text="Detalles de la actividad evaluada"
    )
    
    fecha_evaluacion = models.DateField(
        verbose_name="Fecha de Evaluación"
    )
    
    periodo = models.CharField(
        max_length=50,
        verbose_name="Período",
        help_text="Ej: Primer Período, Segundo Período"
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
        verbose_name="Fecha de Creación"
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name="Activa"
    )
    
    class Meta:
        verbose_name = "Evaluación con Rúbrica"
        verbose_name_plural = "Evaluaciones con Rúbrica"
        ordering = ['-fecha_evaluacion']
    
    def __str__(self):
        return f"{self.titulo} - {self.materia.nombre} ({self.curso})"
    
    def total_estudiantes(self):
        """Retorna el total de estudiantes evaluados"""
        return self.calificaciones.values('estudiante').distinct().count()
    
    def puntaje_promedio(self):
        """Calcula el puntaje promedio de todos los estudiantes (escala 0-10)"""
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
    Calificación de un estudiante en un criterio específico de una rúbrica
    """
    evaluacion = models.ForeignKey(
        EvaluacionRubrica,
        on_delete=models.CASCADE,
        related_name='calificaciones',
        verbose_name="Evaluación"
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
        help_text="Comentarios específicos sobre el desempeño en este criterio"
    )
    
    fecha_calificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Calificación"
    )
    
    class Meta:
        verbose_name = "Calificación de Criterio"
        verbose_name_plural = "Calificaciones de Criterios"
        unique_together = ['evaluacion', 'estudiante', 'criterio']
        ordering = ['criterio__orden']
    
    def __str__(self):
        return f"{self.estudiante} - {self.criterio.nombre}: {self.nivel_otorgado.get_nivel_display() if self.nivel_otorgado else 'Sin calificar'}"
    
    def puntaje_ponderado(self):
        """Calcula el puntaje ponderado para este criterio (escala 0-10)"""
        if not self.nivel_otorgado:
            return 0
        ponderacion_decimal = float(self.criterio.ponderacion) / 100
        # nivel.puntaje (1-5) × ponderación × 2 = escala 0-10
        return round(float(self.nivel_otorgado.puntaje) * ponderacion_decimal * 2, 2)


# ===========================
# CONFIGURACIÓN DE LA ESCUELA
# ===========================

class ConfiguracionEscuela(models.Model):
    """
    Configuración general de la escuela/colegio
    Solo debe existir un registro en esta tabla
    """
    nombre_escuela = models.CharField(
        max_length=200,
        verbose_name="Nombre de la Escuela",
        help_text="Nombre oficial de la institución educativa"
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
        verbose_name="Dirección",
        help_text="Dirección física de la escuela"
    )
    
    telefono = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Teléfono",
        help_text="Teléfono principal de contacto"
    )
    
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo Electrónico",
        help_text="Email institucional"
    )
    
    sitio_web = models.URLField(
        blank=True,
        null=True,
        verbose_name="Sitio Web",
        help_text="URL del sitio web de la institución"
    )
    
    logo = models.ImageField(
        upload_to='escuela/logos/',
        blank=True,
        null=True,
        verbose_name="Logo",
        help_text="Logo oficial de la institución (tamaño recomendado: 200x200px)"
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
        help_text="Lema o eslogan de la institución"
    )
    
    mision = models.TextField(
        blank=True,
        null=True,
        verbose_name="Misión",
        help_text="Declaración de la misión institucional"
    )
    
    vision = models.TextField(
        blank=True,
        null=True,
        verbose_name="Visión",
        help_text="Declaración de la visión institucional"
    )
    
    codigo_centro = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Código del Centro",
        help_text="Código oficial asignado por el MINERD u otra autoridad"
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
        help_text="Ej: Inicial, Básica, Media, Técnico-Profesional"
    )
    
    modalidad = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Modalidad",
        help_text="Ej: General, Técnico-Profesional, Artes"
    )
    
    horario_atencion = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Horario de Atención",
        help_text="Ej: Lunes a Viernes 7:00 AM - 4:00 PM"
    )
    
    anho_fundacion = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Año de Fundación",
        help_text="Año en que fue fundada la institución"
    )
    
    # Información para reportes
    pie_pagina_reportes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Pie de Página para Reportes",
        help_text="Texto que aparecerá al pie de los reportes oficiales"
    )
    
    mostrar_logo_reportes = models.BooleanField(
        default=True,
        verbose_name="Mostrar Logo en Reportes",
        help_text="Activar/desactivar el logo en los reportes"
    )
    
    # Control de registro único
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )
    
    class Meta:
        verbose_name = "Configuración de la Escuela"
        verbose_name_plural = "Configuración de la Escuela"
    
    def __str__(self):
        return self.nombre_escuela or "Configuración de la Escuela"
    
    def save(self, *args, **kwargs):
        """Asegurar que solo exista un registro de configuración"""
        if not self.pk and ConfiguracionEscuela.objects.exists():
            # Si no tiene pk (es nuevo) y ya existe un registro, usar el existente
            existing = ConfiguracionEscuela.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)
    
    @classmethod
    def get_configuracion(cls):
        """Obtener o crear la configuración de la escuela"""
        config, created = cls.objects.get_or_create(
            pk=1,
            defaults={'nombre_escuela': 'Mi Escuela'}
        )
        return config
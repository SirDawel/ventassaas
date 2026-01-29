import uuid
# Create your models here.

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
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
import uuid
import os

def user_profile_picture_path(instance, filename):
    """Define la ruta donde se guardarán las imágenes de perfil."""
    return os.path.join("uploads/profile_pictures/", f"user_{instance.id}_{filename}")

from datetime import date
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
    # Función interna
    # ------------------------
    def _calc_promedio(self, notas):
        valores = []
        for n in notas:
            if n is not None:
                try:
                    valores.append(float(str(n).replace(',', '.')))
                except ValueError:
                    pass

        if len(valores) < len(notas):
            return None

        return round(sum(valores) / len(valores), 2)

    # ------------------------
    # Promedios por competencia
    # ------------------------
    @property
    def prom_comunicativa(self):
        prom = self._calc_promedio([self.com_p1, self.com_p2, self.com_p3, self.com_p4])
        if prom is None:
            return None
        return float(self.com_rp) if prom < 70 and self.com_rp else prom

    @property
    def prom_logico(self):
        prom = self._calc_promedio([self.log_p1, self.log_p2, self.log_p3, self.log_p4])
        if prom is None:
            return None
        return float(self.log_rp) if prom < 70 and self.log_rp else prom

    @property
    def prom_cientifica(self):
        prom = self._calc_promedio([self.cie_p1, self.cie_p2, self.cie_p3, self.cie_p4])
        if prom is None:
            return None
        return float(self.cie_rp) if prom < 70 and self.cie_rp else prom

    @property
    def prom_etica(self):
        prom = self._calc_promedio([self.eti_p1, self.eti_p2, self.eti_p3, self.eti_p4])
        if prom is None:
            return None
        return float(self.eti_rp) if prom < 70 and self.eti_rp else prom

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
        return round(sum(comps) / 4, 2)
    

    # ------------------------
    # Cálculo COMPLETIVO final
    # ------------------------
    @property
    def calificacion_completiva_final(self):
        if self.promedio_final is None or self.ex_com is None:
            return None
        return round((self.promedio_final * 0.50) + (self.ex_com * 0.50), 2)
    

    # ------------------------
    # Cálculo EXTRAORDINARIO final
    # 30% promedio + 70% examen extraordinario
    # ------------------------
    @property
    def calificacion_extraordinario_final(self):
        if self.promedio_final is None or self.ex_ext is None:
            return None
        return round((self.promedio_final * 0.30) + (self.ex_ext * 0.70), 2)
    

    # ------------------------
    # Cálculo ESPECIAL final
    # solo examen especial
    # ------------------------
    @property
    def calificacion_especial_final(self):
        return self.ex_esp if self.ex_esp is not None else None

    
    @property
    def estado(self):
        if self.nota_final_oficial is None:
            return "En proceso"
        if self.nota_final_oficial >= 70:
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

    class Meta:
        unique_together = (('estudiante', 'concepto'),)
        verbose_name = 'Tarifa Estudiante'
        verbose_name_plural = 'Tarifas por Estudiante'
        ordering = ['estudiante', 'concepto']

    def __str__(self):
        obs = f" ({self.observaciones})" if self.observaciones else ""
        return f"{self.estudiante.get_full_name()} - {self.concepto.nombre} - RD${self.monto}{obs}"


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
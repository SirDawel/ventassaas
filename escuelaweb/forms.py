from django import forms
from django.contrib.auth.forms import UserCreationForm
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
#from Escuela.escuelaweb.models import CustomUser, CustomUserManager, Persona, AnhoEscolar, Curso, Materia, Matricula
from .models import (
    CustomUser, CustomUserManager, Persona, AnhoEscolar, Curso, Materia, Matricula,
    ListaCotejo, CriterioListaCotejo, EvaluacionListaCotejo, CalificacionCotejo
)

  # Importamos el modelo de usuario personalizado


class LoginForm(forms.Form):
    """
    Formulario de login con seguridad mejorada:
    - CAPTCHA después de 3 intentos fallidos
    - Honeypot field para detectar bots
    """
    email = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña',
            'autocomplete': 'current-password'
        })
    )
    
    # Honeypot field - Campo trampa para bots (invisible para humanos)
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'style': 'display:none !important;',
            'tabindex': '-1',
            'autocomplete': 'off'
        })
    )
    
    # CAPTCHA - Solo se muestra si show_captcha=True
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(),
        required=False  # Lo hacemos requerido dinámicamente en el __init__
    )
    
    def __init__(self, *args, **kwargs):
        # Recibir parámetro para mostrar CAPTCHA
        self.show_captcha = kwargs.pop('show_captcha', False)
        super().__init__(*args, **kwargs)
        
        # Si no se debe mostrar CAPTCHA, remover el campo
        if not self.show_captcha:
            del self.fields['captcha']
        else:
            # Hacer CAPTCHA requerido
            self.fields['captcha'].required = True
    
    def clean_website(self):
        """Validar honeypot - Si tiene valor, es un bot"""
        website = self.cleaned_data.get('website')
        if website:
            # Es un bot, lanzar error silencioso
            raise forms.ValidationError("Error de validación del formulario.")
        return website
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if not email or not password:
            raise forms.ValidationError("Por favor, completa todos los campos.")
        
        return cleaned_data



class SignupForm(UserCreationForm):

    email = forms.EmailField(required=True)





#Año Escolar



class AnhoEscolarForm(forms.ModelForm):

    class Meta:
        model = AnhoEscolar
        fields = ['nombre', 'fecha_inicio', 'fecha_fin', 'activo']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_inicio'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_fin'].input_formats = ['%Y-%m-%d']

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin and fecha_inicio >= fecha_fin:
            raise forms.ValidationError('La fecha de inicio debe ser anterior a la fecha de fin.')



#___________________estudiante__________________________________________________



class EstudianteForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EstudianteForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'fecha_nacimiento':  # Ya lo definimos en widgets
                self.fields[field].widget.attrs.update({"class": "form-control"})


#___________________________Usuario____________________________________
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, CustomUserManager
class UserRegistrationForm(UserCreationForm):

    # CHOICES POR DEFECTO (CREACIÓN)
    GENERO_CHOICES = (
        ("M", "Masculino"),
        ("F", "Femenino"),
        ("Otro", "Otro"),
    )


    ROL_CHOICES = (     
        ("Estudiante", "Estudiante"),
        ("Profesor", "Profesor"),
        ("Director", "Director"),
        ("Secretaria", "Secretaria"),
        ("Administrador", "Administrador"),
        ("Coordinador", "Coordinador"),
        ("Bibliotecario", "Bibliotecario"),
        ("Psicologo", "Psicólogo"),
        ("Otro", "Otro"),
    )
        

    GRADO_CHOICES = (
        ("1ro", "1ro"), ("2do", "2do"), ("3ro", "3ro"),
        ("4to", "4to"), ("5to", "5to"), ("6to", "6to"),
    )

    SECCION_CHOICES = (
        ("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"),
    )

    ESPECIALIDAD_CHOICES = (
        ("Matemáticas", "Matemáticas"),
        ("Informática", "Informática"),
        ("Lengua Española", "Lengua Española"),
        ("Ciencias Sociales", "Ciencias Sociales"),
        ("Ciencias Naturales", "Ciencias Naturales"),
        ("Otra", "Otra"),
    )

    DEPARTAMENTO_CHOICES = (
        ("Académico", "Académico"),
        ("Orientación", "Orientación"),
        ("Dirección", "Dirección"),
        ("Administración", "Administración"),
    )

    # SELECTS
    genero = forms.ChoiceField(choices=GENERO_CHOICES, required=True)
    rol = forms.ChoiceField(choices=ROL_CHOICES, required=True)

    grado = forms.ChoiceField(choices=GRADO_CHOICES, required=False)
    seccion = forms.ChoiceField(choices=SECCION_CHOICES, required=False)
    especialidad = forms.ChoiceField(choices=ESPECIALIDAD_CHOICES, required=False)
    departamento = forms.ChoiceField(choices=DEPARTAMENTO_CHOICES, required=False)

    # Contacto emergencia
    contacto_emergencia_nombre = forms.CharField(required=False)
    contacto_emergencia_telefono = forms.CharField(required=False)
    contacto_emergencia_parentesco = forms.CharField(required=False)
    
    # Configuración de mora individual (para estudiantes sin grupo familiar)
    porcentaje_mora_individual = forms.DecimalField(
        required=False,
        initial=0,
        min_value=0,
        max_value=100,
        decimal_places=2,
        help_text="Porcentaje de mora para estudiante sin grupo familiar"
    )
    dia_vencimiento_individual = forms.IntegerField(
        required=False,
        initial=10,
        min_value=1,
        max_value=31,
        label="Día de Vencimiento Individual",
        help_text="Día del mes para vencimiento de pagos (estudiante sin grupo)"
    )
    
    descuento_individual = forms.DecimalField(
        required=False,
        initial=0,
        min_value=0,
        max_value=100,
        decimal_places=2,
        label="Descuento Individual (%)",
        help_text="Porcentaje de descuento para estudiante sin grupo familiar"
    )

    class Meta:
        model = CustomUser
        fields = [
            "first_name", "last_name", "email", "fecha_nacimiento", "genero",
            "telefono", "direccion", "cedula",
            "rol", "grado", "seccion", "especialidad", "departamento",
            "contacto_emergencia_nombre", "contacto_emergencia_telefono",
            "contacto_emergencia_parentesco",
            "porcentaje_mora_individual", "dia_vencimiento_individual", "descuento_individual",
            "password1", "password2",
        ]

        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}),
            "dia_vencimiento_individual": forms.NumberInput(attrs={
                "type": "number",
                "min": "1",
                "max": "31",
                "placeholder": "10"
            }),
            "porcentaje_mora_individual": forms.NumberInput(attrs={
                "type": "number",
                "min": "0",
                "max": "100",
                "step": "0.01",
                "placeholder": "0.00"
            }),
            "descuento_individual": forms.NumberInput(attrs={
                "type": "number",
                "min": "0",
                "max": "100",
                "step": "0.01",
                "placeholder": "0.00"
            }),
        }

    # --------------------------------------------
    # INICIALIZACIÓN: CARGAR VALORES EN EDICIÓN
    # --------------------------------------------

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user = self.instance  # ← usuario actual en modo edición (puede estar vacío)

        # 1. Campos opcionales
        opcionales = [
            'grado', 'seccion', 'especialidad', 'departamento',
            'contacto_emergencia_nombre', 'contacto_emergencia_telefono',
            'contacto_emergencia_parentesco'
        ]
        for field in opcionales:
            self.fields[field].required = False

        # 2. Bootstrap CSS
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'

        # 3. Cargar el valor actual del usuario en edición
        if user and user.pk:
            # Esto asegura que los selects respeten el valor actual
            self.fields['genero'].initial = user.genero
            self.fields['rol'].initial = user.rol
            self.fields['grado'].initial = user.grado
            self.fields['seccion'].initial = user.seccion
            self.fields['especialidad'].initial = user.especialidad
            self.fields['departamento'].initial = user.departamento

    # ----------------------------
    # VALIDACIÓN POR ROL
    # ----------------------------

    def clean(self):
        cleaned = super().clean()
        rol = cleaned.get("rol")

        if rol == "Estudiante":
            if not cleaned.get("grado"):
                self.add_error("grado", "El grado es requerido para estudiantes")
            if not cleaned.get("seccion"):
                self.add_error("seccion", "La sección es requerida para estudiantes")

        if rol == "Profesor":
            if not cleaned.get("especialidad"):
                self.add_error("especialidad", "La especialidad es requerida para profesores")
            if not cleaned.get("departamento"):
                self.add_error("departamento", "El departamento es requerido para profesores")

        return cleaned

    # ----------------------------
    # EMAIL ÚNICO
    # ----------------------------
    def clean_email(self):
        email = self.cleaned_data.get("email")
        user_id = self.instance.pk

        if CustomUser.objects.filter(email=email).exclude(pk=user_id).exists():
            raise forms.ValidationError("Este correo electrónico ya existe.")

        return email

    # ----------------------------
    # CÉDULA ÚNICA
    # ----------------------------
    def clean_cedula(self):
        cedula = self.cleaned_data.get("cedula")
        user_id = self.instance.pk

        if cedula and CustomUser.objects.filter(cedula=cedula).exclude(pk=user_id).exists():
            raise forms.ValidationError("Esta cédula ya existe.")

        return cedula


from django import forms
from .models import CustomUser

from .models import TarifaEstudiante


class TarifaEstudianteForm(forms.ModelForm):
    class Meta:
        model = TarifaEstudiante
        fields = ['estudiante', 'concepto', 'monto', 'observaciones', 'dia_vencimiento', 'activo']
        widgets = {
            'estudiante': forms.Select(attrs={'class': 'form-select'}),
            'concepto': forms.Select(attrs={'class': 'form-select'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observaciones': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Zona cercana, Zona lejana'}),
            'dia_vencimiento': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1', 
                'max': '31', 
                'placeholder': 'Deja vacío para usar el del grupo familiar'
            }),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo conceptos de mensualidad, inscripción y transporte (excluyendo mensualidad test)
        from .models import ConceptoPago
        from django.db.models import Q
        self.fields['concepto'].queryset = ConceptoPago.objects.filter(
            tipo__in=['mensualidad', 'inscripcion', 'transporte'],
            activo=True
        ).exclude(
            Q(nombre__icontains='mensualidad tes') | Q(nombre__icontains='cuaderno')
        ).order_by('tipo', 'nombre')
        
        # Hacer los campos opcionales explícitamente
        self.fields['observaciones'].required = False
        self.fields['dia_vencimiento'].required = False
        self.fields['dia_vencimiento'].help_text = 'Día del mes para vencimiento (1-31). Si no se especifica, usa el del grupo familiar.'
        
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.Select, forms.CheckboxInput)):
                field.widget.attrs['class'] = 'form-control'


class ConceptoPagoForm(forms.ModelForm):
    """Formulario para crear y editar conceptos de pago (tarifas estándar)"""
    class Meta:
        from .models import ConceptoPago
        model = ConceptoPago
        fields = ['tipo', 'nombre', 'monto', 'descripcion', 'activo', 'es_estandar']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Mensualidad 2025, Inscripción Año Escolar'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del concepto (opcional)'
            }),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'es_estandar': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'tipo': 'Tipo de Concepto',
            'nombre': 'Nombre del Concepto',
            'monto': 'Monto Base',
            'descripcion': 'Descripción',
            'activo': 'Concepto Activo',
            'es_estandar': 'Tarifa Estándar (Auto-asignar a nuevos estudiantes)',
        }


class UserUpdateForm(forms.ModelForm):

    # IMPORTAMOS LOS MISMOS CHOICES
    GENERO_CHOICES = UserRegistrationForm.GENERO_CHOICES
    ROL_CHOICES = UserRegistrationForm.ROL_CHOICES
    GRADO_CHOICES = UserRegistrationForm.GRADO_CHOICES
    SECCION_CHOICES = UserRegistrationForm.SECCION_CHOICES
    ESPECIALIDAD_CHOICES = UserRegistrationForm.ESPECIALIDAD_CHOICES
    DEPARTAMENTO_CHOICES = UserRegistrationForm.DEPARTAMENTO_CHOICES

    genero = forms.ChoiceField(choices=GENERO_CHOICES)
    rol = forms.ChoiceField(choices=ROL_CHOICES)
    grado = forms.ChoiceField(choices=GRADO_CHOICES, required=False)
    seccion = forms.ChoiceField(choices=SECCION_CHOICES, required=False)
    especialidad = forms.ChoiceField(choices=ESPECIALIDAD_CHOICES, required=False)
    departamento = forms.ChoiceField(choices=DEPARTAMENTO_CHOICES, required=False)

    password1 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese nueva contraseña (opcional)',
        }),
        label="Contraseña (opcional)"
    )
    
    # Configuración de mora individual (para estudiantes sin grupo familiar)
    porcentaje_mora_individual = forms.DecimalField(
        required=False,
        initial=0,
        min_value=0,
        max_value=100,
        decimal_places=2,
        label="Porcentaje de Mora Individual (%)",
        help_text="Porcentaje de mora para estudiante sin grupo familiar"
    )
    dia_vencimiento_individual = forms.IntegerField(
        required=False,
        initial=10,
        min_value=1,
        max_value=31,
        label="Día de Vencimiento Individual",
        help_text="Día del mes para vencimiento de pagos (estudiante sin grupo)"
    )
    
    descuento_individual = forms.DecimalField(
        required=False,
        initial=0,
        min_value=0,
        max_value=100,
        decimal_places=2,
        label="Descuento Individual (%)",
        help_text="Porcentaje de descuento para estudiante sin grupo familiar"
    )

    class Meta:
        model = CustomUser
        fields = [
            'email', 'first_name', 'last_name', 'fecha_nacimiento', 'genero',
            'direccion', 'telefono', 'cedula', 'rol', 'grado', 'seccion',
            'especialidad', 'departamento', 'contacto_emergencia_nombre',
            'contacto_emergencia_telefono', 'contacto_emergencia_parentesco',
            'porcentaje_mora_individual', 'dia_vencimiento_individual', 'descuento_individual'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'dia_vencimiento_individual': forms.NumberInput(attrs={
                'type': 'number',
                'min': '1',
                'max': '31',
                'placeholder': '10'
            }),
            'porcentaje_mora_individual': forms.NumberInput(attrs={
                'type': 'number',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'descuento_individual': forms.NumberInput(attrs={
                'type': 'number',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': '0.00'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user = self.instance  # OBJETO DEL USUARIO A EDITAR

        # bootstrap
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'

        # Campos opcionales siempre
        opcionales = [
            'grado', 'seccion', 'especialidad', 'departamento',
            'contacto_emergencia_nombre', 'contacto_emergencia_telefono',
            'contacto_emergencia_parentesco',
        ]
        for f in opcionales:
            self.fields[f].required = False

        # CARGAR VALORES ACTUALES DEL USUARIO EN EDICIÓN
        if user and user.pk:
            self.fields['genero'].initial = user.genero
            self.fields['rol'].initial = user.rol
            self.fields['grado'].initial = user.grado
            self.fields['seccion'].initial = user.seccion
            self.fields['especialidad'].initial = user.especialidad
            self.fields['departamento'].initial = user.departamento
            self.fields['porcentaje_mora_individual'].initial = user.porcentaje_mora_individual
            self.fields['dia_vencimiento_individual'].initial = user.dia_vencimiento_individual
            self.fields['descuento_individual'].initial = user.descuento_individual

    # VALIDACIÓN POR ROL
    def clean(self):
        cleaned = super().clean()
        rol = cleaned.get("rol")

        if rol == "Estudiante":
            if not cleaned.get("grado"):
                self.add_error("grado", "El grado es requerido para estudiantes")
            if not cleaned.get("seccion"):
                self.add_error("seccion", "La sección es requerida para estudiantes")

        if rol == "Profesor":
            if not cleaned.get("especialidad"):
                self.add_error("especialidad", "La especialidad es requerida para profesores")
            if not cleaned.get("departamento"):
                self.add_error("departamento", "El departamento es requerido para profesores")

        return cleaned



class UserUpdateFormGood(forms.ModelForm):
    password1 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Nueva contraseña',
        help_text='Dejar en blanco para mantener la contraseña actual'
    )

    class Meta:
        model = CustomUser
        fields = [
            'email', 'first_name', 'last_name', 'fecha_nacimiento',
            'genero', 'direccion', 'telefono', 'cedula', 'rol',
            'grado', 'seccion', 'especialidad', 'departamento', 'cargo',
            'contacto_emergencia_nombre', 'contacto_emergencia_telefono',
            'contacto_emergencia_parentesco'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'genero': forms.Select(choices=CustomUser._meta.get_field('genero').choices),
            'rol': forms.Select(choices=CustomUser._meta.get_field('rol').choices),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos opcionales
        for field in ['grado', 'seccion', 'especialidad', 'departamento', 'cargo',
                     'contacto_emergencia_nombre', 'contacto_emergencia_telefono',
                     'contacto_emergencia_parentesco']:
            self.fields[field].required = False
        
        # Agregar clases CSS a todos los campos
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get('rol')
        
        # Validar campos específicos por rol
        if rol == 'Estudiante':
            if not cleaned_data.get('grado'):
                self.add_error('grado', 'El grado es requerido para estudiantes')
            if not cleaned_data.get('seccion'):
                self.add_error('seccion', 'La sección es requerida para estudiantes')
        elif rol == 'Profesor':
            if not cleaned_data.get('especialidad'):
                self.add_error('especialidad', 'La especialidad es requerida para profesores')
            if not cleaned_data.get('departamento'):
                self.add_error('departamento', 'El departamento es requerido para profesores')
        
        return cleaned_data

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        # Si el campo está vacío, no validar
        if not password1:
            return password1
        # Validar longitud mínima
        if len(password1) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        return password1

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if cedula and CustomUser.objects.filter(cedula=cedula).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError("Esta cédula ya está registrada.")
        return cedula

    def save(self, commit=True):
        user = super().save(commit=False)
        # Solo actualizar la contraseña si se proporcionó una nueva
        if self.cleaned_data.get('password1'):
            user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user





class UserRegistrationForm2(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Contraseña"}),
        label="Contraseña",
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirmar contraseña"}
    ),)

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password2
    
from django import forms
from .models import CustomUser  # Asegúrate de importar tu modelo de usuario personalizado

class UserCreateForm(UserCreationForm):
    class Meta:
        model = CustomUser  # Especificar el modelo
        fields = ["email", "first_name", "last_name", "is_staff", "password1", "password2"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({"class": "form-control", "placeholder": "Correo electrónico"})
        self.fields["first_name"].widget.attrs.update({"class": "form-control", "placeholder": "Nombre"})
        self.fields["last_name"].widget.attrs.update({"class": "form-control", "placeholder": "Apellido"})
        self.fields["password1"].widget.attrs.update({"class": "form-control", "placeholder": "Contraseña"})
        self.fields["password2"].widget.attrs.update({"class": "form-control", "placeholder": "Confirmar contraseña"})
        self.fields["is_staff"].widget.attrs.update({"class": "form-check-input"})
#___________________persona______________________________________
from django import forms
from .models import Persona

class PersonaForm(forms.ModelForm):
    # Campos para el padre
    padre_nombre = forms.CharField(max_length=100, required=False)
    padre_apellido = forms.CharField(max_length=100, required=False)
    padre_telefono = forms.CharField(max_length=15, required=False)
    padre_direccion = forms.CharField(widget=forms.Textarea, required=False)
    
    # Campos para la madre
    madre_nombre = forms.CharField(max_length=100, required=False)
    madre_apellido = forms.CharField(max_length=100, required=False)
    madre_telefono = forms.CharField(max_length=15, required=False)
    madre_direccion = forms.CharField(widget=forms.Textarea, required=False)
    
    # Campos para el tutor
    tutor_nombre = forms.CharField(max_length=100, required=False)
    tutor_apellido = forms.CharField(max_length=100, required=False)
    tutor_telefono = forms.CharField(max_length=15, required=False)
    tutor_direccion = forms.CharField(widget=forms.Textarea, required=False)
    
    # Campos para el contacto de emergencia
    contacto_nombre = forms.CharField(max_length=100, required=False)
    contacto_apellido = forms.CharField(max_length=100, required=False)
    contacto_telefono = forms.CharField(max_length=15, required=False)
    contacto_direccion = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = Persona
        fields = ["nombre", "apellido", "correo", "fecha_nacimiento", "sexo", "cedula", "rne", "direccion", "telefono", "grado"]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        
        if instance:
            # Pre-poblar campos del padre
            if instance.padre:
                self.fields['padre_nombre'].initial = instance.padre.nombre
                self.fields['padre_apellido'].initial = instance.padre.apellido
                self.fields['padre_telefono'].initial = instance.padre.telefono
                self.fields['padre_direccion'].initial = instance.padre.direccion
            
            # Pre-poblar campos de la madre
            if instance.madre:
                self.fields['madre_nombre'].initial = instance.madre.nombre
                self.fields['madre_apellido'].initial = instance.madre.apellido
                self.fields['madre_telefono'].initial = instance.madre.telefono
                self.fields['madre_direccion'].initial = instance.madre.direccion
            
            # Pre-poblar campos del tutor
            if instance.tutor:
                self.fields['tutor_nombre'].initial = instance.tutor.nombre
                self.fields['tutor_apellido'].initial = instance.tutor.apellido
                self.fields['tutor_telefono'].initial = instance.tutor.telefono
                self.fields['tutor_direccion'].initial = instance.tutor.direccion
            
            # Pre-poblar campos del contacto de emergencia
            if instance.contacto_emergencia:
                self.fields['contacto_nombre'].initial = instance.contacto_emergencia.nombre
                self.fields['contacto_apellido'].initial = instance.contacto_emergencia.apellido
                self.fields['contacto_telefono'].initial = instance.contacto_emergencia.telefono
                self.fields['contacto_direccion'].initial = instance.contacto_emergencia.direccion

#_______________________________________Profile picture_________________________
class ProfilePictureUpdateForm(forms.Form):
    foto_perfil = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    def clean_foto_perfil(self):
        picture = self.cleaned_data.get('foto_perfil')
        if picture:
            # Validar el tamaño del archivo (máximo 5MB)
            if picture.size > 5 * 1024 * 1024:
                raise forms.ValidationError("La imagen no puede ser mayor a 5MB")
            # Validar el tipo de archivo
            if not picture.content_type.startswith('image/'):
                raise forms.ValidationError("El archivo debe ser una imagen")
        return picture

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['nombre', 'descripcion', 'anho_escolar']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'anho_escolar': forms.Select(attrs={'class': 'form-control'})
        }



class MatriculaForm(forms.ModelForm):
    class Meta:
        model = Matricula
        fields = [
            'estudiante', 'materia', 'anho_escolar',
            'com_p1','com_p2','com_p3','com_p4',
            'log_p1','log_p2','log_p3','log_p4',
            'cie_p1','cie_p2','cie_p3','cie_p4',
            'eti_p1','eti_p2','eti_p3','eti_p4'
        ]
        widgets = { 
            'estudiante': forms.Select(attrs={'class':'form-control'}),
            'materia': forms.Select(attrs={'class':'form-control'}),
            'anho_escolar': forms.Select(attrs={'class':'form-control'}),
            **{f'{c}_{p}': forms.NumberInput(attrs={'class':'form-control','step':'0.01','min':'0','max':'100'}) 
               for c in ['com','log','cie','eti'] for p in ['p1','p2','p3','p4']}
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estudiante'].queryset = CustomUser.objects.filter(rol='Estudiante')
        self.fields['anho_escolar'].queryset = AnhoEscolar.objects.filter(activo=True)
   

class MatriculaForm2(forms.ModelForm):
    class Meta:
        model = Matricula
        fields = [
            'estudiante', 'materia', 'anho_escolar',
            # Comunicativa
            'com_p1', 'com_p2', 'com_p3', 'com_p4',
            # Lógica
            'log_p1', 'log_p2', 'log_p3', 'log_p4',
            # Científica
            'cie_p1', 'cie_p2', 'cie_p3', 'cie_p4',
            # Ética
            'eti_p1', 'eti_p2', 'eti_p3', 'eti_p4',
        ]
        widgets = {
            'estudiante': forms.Select(attrs={'class': 'form-control'}),
            'materia': forms.Select(attrs={'class': 'form-control'}),
            'anho_escolar': forms.Select(attrs={'class': 'form-control'}),

            # Comunicativa
            'com_p1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'com_p2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'com_p3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'com_p4': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),

            # Lógica
            'log_p1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'log_p2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'log_p3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'log_p4': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),

            # Científica
            'cie_p1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'cie_p2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'cie_p3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'cie_p4': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),

            # Ética
            'eti_p1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'eti_p2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'eti_p3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'eti_p4': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo usuarios con rol de estudiante
        self.fields['estudiante'].queryset = CustomUser.objects.filter(rol='Estudiante')
        # Filtrar solo años escolares activos
        self.fields['anho_escolar'].queryset = AnhoEscolar.objects.filter(activo=True)

    def clean(self):
        cleaned_data = super().clean()
        # Validar que TODAS las notas estén entre 0 y 100
        nota_fields = [
            'com_p1','com_p2','com_p3','com_p4',
            'log_p1','log_p2','log_p3','log_p4',
            'cie_p1','cie_p2','cie_p3','cie_p4',
            'eti_p1','eti_p2','eti_p3','eti_p4',
        ]
        for field in nota_fields:
            value = cleaned_data.get(field)
            if value is not None and (value < 0 or value > 100):
                self.add_error(field, 'La nota debe estar entre 0 y 100')
        return cleaned_data


from django import forms
from .models import Materia, CustomUser

class MateriaForm(forms.ModelForm):
    profesor = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(rol='Profesor'),
        required=False,
        label='Profesor'
    )

    class Meta:
        model = Materia
        fields = ['nombre', 'codigo', 'categoria', 'profesor', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes']

    def __init__(self, *args, **kwargs):
        super(MateriaForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})


# ============================================
# FORMULARIOS DE CONTABILIDAD
# ============================================

from .models import PlanCuentas

class PlanCuentasForm(forms.ModelForm):
    """
    Formulario para crear y editar cuentas contables
    """
    
    class Meta:
        model = PlanCuentas
        fields = [
            'codigo', 'nombre', 'descripcion', 'tipo_cuenta', 
            'naturaleza', 'cuenta_padre', 'es_detalle', 
            'saldo_inicial', 'activo', 'requiere_centro_costo', 
            'requiere_tercero'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1.1.01.001',
                'pattern': '[0-9.]+',
                'title': 'Formato: números separados por puntos'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la cuenta contable'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada del uso de esta cuenta (opcional)'
            }),
            'tipo_cuenta': forms.Select(attrs={
                'class': 'form-select'
            }),
            'naturaleza': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cuenta_padre': forms.Select(attrs={
                'class': 'form-select'
            }),
            'es_detalle': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'saldo_inicial': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'requiere_centro_costo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'requiere_tercero': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'codigo': 'Código de Cuenta',
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'tipo_cuenta': 'Tipo de Cuenta',
            'naturaleza': 'Naturaleza',
            'cuenta_padre': 'Cuenta Padre (opcional)',
            'es_detalle': '¿Es cuenta de detalle?',
            'activo': '¿Activo?',
            'saldo_inicial': 'Saldo Inicial',
            'requiere_centro_costo': '¿Requiere Centro de Costo?',
            'requiere_tercero': '¿Requiere Tercero?',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar solo cuentas activas y no de detalle como posibles padres
        self.fields['cuenta_padre'].queryset = PlanCuentas.objects.filter(
            activo=True,
            es_detalle=False
        ).order_by('codigo')
        
        # Hacer descripción opcional
        self.fields['descripcion'].required = False
        self.fields['cuenta_padre'].required = False
        
        # Marcar campos opcionales
        self.fields['requiere_centro_costo'].required = False
        self.fields['requiere_tercero'].required = False
        
        # Si estamos editando, excluir la cuenta actual de las opciones de padre
        if self.instance and self.instance.pk:
            self.fields['cuenta_padre'].queryset = self.fields['cuenta_padre'].queryset.exclude(
                pk=self.instance.pk
            )
    
    def clean_codigo(self):
        """Validar formato del código de cuenta"""
        codigo = self.cleaned_data.get('codigo')
        
        if not codigo:
            raise forms.ValidationError('El código es obligatorio')
        
        # Validar formato: solo números y puntos
        import re
        if not re.match(r'^[0-9.]+$', codigo):
            raise forms.ValidationError('El código solo puede contener números y puntos')
        
        # Validar que no empiece o termine con punto
        if codigo.startswith('.') or codigo.endswith('.'):
            raise forms.ValidationError('El código no puede empezar ni terminar con punto')
        
        # Validar que no tenga puntos consecutivos
        if '..' in codigo:
            raise forms.ValidationError('El código no puede tener puntos consecutivos')
        
        # Si estamos editando, excluir de la validación de duplicados la instancia actual
        qs = PlanCuentas.objects.filter(codigo=codigo)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise forms.ValidationError('Ya existe una cuenta con este código')
        
        return codigo
    
    def clean(self):
        cleaned_data = super().clean()
        cuenta_padre = cleaned_data.get('cuenta_padre')
        es_detalle = cleaned_data.get('es_detalle')
        codigo = cleaned_data.get('codigo')
        
        # Si tiene cuenta padre, validar jerarquía
        if cuenta_padre:
            # El código debe comenzar con el código del padre
            if not codigo.startswith(cuenta_padre.codigo):
                self.add_error(
                    'codigo',
                    f'El código debe comenzar con el código de la cuenta padre ({cuenta_padre.codigo})'
                )
            
            # La cuenta padre no puede ser de detalle
            if cuenta_padre.es_detalle:
                self.add_error(
                    'cuenta_padre',
                    'La cuenta padre no puede ser una cuenta de detalle'
                )
        
        # Si no es detalle, no puede tener saldo inicial
        if not es_detalle and cleaned_data.get('saldo_inicial', 0) != 0:
            self.add_error(
                'saldo_inicial',
                'Las cuentas de agrupación no pueden tener saldo inicial'
            )
        
        return cleaned_data


class PlanCuentasBusquedaForm(forms.Form):
    """
    Formulario para búsqueda y filtrado de cuentas contables
    """
    busqueda = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por código o nombre...',
        }),
        label='Buscar'
    )
    
    tipo_cuenta = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los tipos')] + PlanCuentas.TIPO_CUENTA_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Tipo de Cuenta'
    )
    
    activo = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todas'),
            ('true', 'Solo activas'),
            ('false', 'Solo inactivas'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
    
    es_detalle = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todas'),
            ('true', 'Solo cuentas de detalle'),
            ('false', 'Solo cuentas agrupadores'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Tipo'
    )


# ============================================
# FORMULARIOS DE ASIENTOS CONTABLES
# ============================================

from .models import AsientoContable, DetalleAsiento

class AsientoContableForm(forms.ModelForm):
    """
    Formulario para crear y editar asientos contables
    """
    
    class Meta:
        model = AsientoContable
        fields = [
            'numero_asiento', 'fecha_asiento', 'tipo_asiento',
            'concepto', 'referencia'
        ]
        widgets = {
            'numero_asiento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ASI-2026-001',
                'readonly': 'readonly'
            }),
            'fecha_asiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'tipo_asiento': forms.Select(attrs={
                'class': 'form-select'
            }),
            'concepto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción general del asiento contable'
            }),
            'referencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de factura, recibo, etc. (opcional)'
            }),
        }
        labels = {
            'numero_asiento': 'Número de Asiento',
            'fecha_asiento': 'Fecha',
            'tipo_asiento': 'Tipo de Asiento',
            'concepto': 'Concepto/Descripción',
            'referencia': 'Referencia Externa',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['referencia'].required = False
        
        # Si es nuevo, generar número automáticamente
        if not self.instance.pk:
            self.fields['numero_asiento'].initial = self.generar_numero_asiento()
    
    def generar_numero_asiento(self):
        """Genera el próximo número de asiento"""
        from django.utils import timezone
        anio_actual = timezone.now().year
        
        ultimo = AsientoContable.objects.filter(
            numero_asiento__startswith=f'ASI-{anio_actual}-'
        ).order_by('-numero_asiento').first()
        
        if ultimo:
            # Extraer el número secuencial
            try:
                ultimo_num = int(ultimo.numero_asiento.split('-')[-1])
                nuevo_num = ultimo_num + 1
            except:
                nuevo_num = 1
        else:
            nuevo_num = 1
        
        return f'ASI-{anio_actual}-{nuevo_num:04d}'


class DetalleAsientoForm(forms.ModelForm):
    """
    Formulario para las líneas del asiento contable
    """
    
    # Campos personalizados para mejor UX
    tipo_movimiento = forms.ChoiceField(
        choices=[
            ('DEBITO', 'Débito'),
            ('CREDITO', 'Crédito')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select tipo-movimiento'
        }),
        label='Tipo'
    )
    
    monto = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control monto-input',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00'
        }),
        label='Monto'
    )
    
    class Meta:
        model = DetalleAsiento
        fields = [
            'cuenta', 'descripcion', 'centro_costo',
            'tercero', 'referencia_interna'
        ]
        widgets = {
            'cuenta': forms.Select(attrs={
                'class': 'form-select cuenta-select'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del movimiento'
            }),
            'centro_costo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Centro de costo (opcional)'
            }),
            'tercero': forms.Select(attrs={
                'class': 'form-select'
            }),
            'referencia_interna': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Referencia (opcional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar solo cuentas de detalle activas
        self.fields['cuenta'].queryset = PlanCuentas.objects.filter(
            es_detalle=True,
            activo=True
        ).order_by('codigo')
        
        # Campos opcionales
        self.fields['centro_costo'].required = False
        self.fields['tercero'].required = False
        self.fields['referencia_interna'].required = False
        
        # Si hay instancia, establecer valores
        if self.instance and self.instance.pk:
            if self.instance.debito > 0:
                self.fields['tipo_movimiento'].initial = 'DEBITO'
                self.fields['monto'].initial = self.instance.debito
            else:
                self.fields['tipo_movimiento'].initial = 'CREDITO'
                self.fields['monto'].initial = self.instance.credito
    
    def save(self, commit=True):
        """Override save para asignar débito o crédito según tipo"""
        instance = super().save(commit=False)
        
        tipo = self.cleaned_data.get('tipo_movimiento')
        monto = self.cleaned_data.get('monto')
        
        if tipo == 'DEBITO':
            instance.debito = monto
            instance.credito = 0
        else:
            instance.credito = monto
            instance.debito = 0
        
        if commit:
            instance.save()
        
        return instance


class AsientoBusquedaForm(forms.Form):
    """
    Formulario para búsqueda y filtrado de asientos contables
    """
    busqueda = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por número, concepto o referencia...',
        }),
        label='Buscar'
    )
    
    tipo_asiento = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los tipos')] + AsientoContable.TIPO_ASIENTO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Tipo de Asiento'
    )
    
    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los estados')] + AsientoContable.ESTADO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Desde'
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Hasta'
    )


class AnularAsientoForm(forms.Form):
    """
    Formulario para anular un asiento contable
    """
    motivo_anulacion = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Explique el motivo de la anulación...'
        }),
        label='Motivo de Anulación',
        help_text='Debe proporcionar una razón válida para anular este asiento'
    )
    
    confirmar = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Confirmo que deseo anular este asiento contable'
    )


# ====================================================================
#  FORMULARIOS PARA LISTAS DE COTEJO
# ====================================================================

class ListaCotejoForm(forms.ModelForm):
    """Formulario para crear y editar listas de cotejo"""
    
    class Meta:
        from .models import ListaCotejo
        model = ListaCotejo
        fields = [
            'nombre', 'descripcion', 'tipo_evaluacion', 'materia',
            'puntaje_total', 'es_plantilla', 'orden_criterios', 'activa'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Lista de cotejo para evaluar cuaderno'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada (opcional)'
            }),
            'tipo_evaluacion': forms.Select(attrs={'class': 'form-select'}),
            'materia': forms.Select(attrs={
                'class': 'form-select',
            }),
            'puntaje_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'es_plantilla': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'orden_criterios': forms.Select(attrs={'class': 'form-select'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nombre': 'Nombre de la Lista',
            'descripcion': 'Descripción',
            'tipo_evaluacion': 'Tipo de Evaluación',
            'materia': 'Materia (opcional)',
            'puntaje_total': 'Puntaje Total',
            'es_plantilla': 'Es Plantilla Reutilizable',
            'orden_criterios': 'Orden de Criterios',
            'activa': 'Activa',
        }
        help_texts = {
            'materia': 'Dejar en blanco para lista general/reutilizable',
            'puntaje_total': 'Puntaje máximo (usualmente 10)',
            'es_plantilla': 'Si es plantilla, puede ser reutilizada múltiples veces'
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar materias según el usuario y año activo
        if user:
            from .models import AnhoEscolar
            anho_activo = AnhoEscolar.objects.filter(activo=True).first()
            
            if anho_activo:
                if user.rol == 'Profesor':
                    # Solo materias del profesor en el año activo
                    self.fields['materia'].queryset = Materia.objects.filter(
                        profesor=user,
                        curso__anho_escolar=anho_activo
                    ).distinct()
                else:
                    # Administradores y directores: todas las materias del año activo
                    self.fields['materia'].queryset = Materia.objects.filter(
                        curso__anho_escolar=anho_activo
                    ).distinct()
            else:
                # Si no hay año activo, filtrar según rol sin restricción de año
                if user.rol == 'Profesor':
                    self.fields['materia'].queryset = Materia.objects.filter(
                        profesor=user
                    ).distinct()
        
        # Hacer materia opcional (puede quedar en blanco)
        self.fields['materia'].required = False


class CriterioListaCotejoForm(forms.ModelForm):
    """Formulario para crear y editar criterios de lista de cotejo"""
    
    class Meta:
        from .models import CriterioListaCotejo
        model = CriterioListaCotejo
        fields = [
            'descripcion', 'tipo_criterio', 'puntaje_maximo',
            'orden', 'es_obligatorio', 'activo'
        ]
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Completo las actividades en clase'
            }),
            'tipo_criterio': forms.Select(attrs={'class': 'form-select'}),
            'puntaje_maximo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'es_obligatorio': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'descripcion': 'Descripción del Criterio',
            'tipo_criterio': 'Tipo de Criterio',
            'puntaje_maximo': 'Puntaje Máximo',
            'orden': 'Orden',
            'es_obligatorio': 'Es Obligatorio',
            'activo': 'Activo',
        }


# FormSet para gestionar múltiples criterios a la vez
from django.forms import inlineformset_factory
from .models import ListaCotejo, CriterioListaCotejo

CriterioFormSet = inlineformset_factory(
    ListaCotejo,
    CriterioListaCotejo,
    form=CriterioListaCotejoForm,
    extra=1,  # Solo 1 formulario vacío extra
    can_delete=True,
    min_num=1,  # Mínimo 1 criterio
    validate_min=True,
)


class EvaluacionListaCotejoForm(forms.ModelForm):
    """Formulario para crear y editar evaluaciones con lista de cotejo"""
    
    class Meta:
        from .models import EvaluacionListaCotejo
        model = EvaluacionListaCotejo
        fields = [
            'lista_cotejo', 'nombre', 'descripcion', 'materia', 'curso',
            'fecha_evaluacion', 'fecha_limite', 'estado',
            'incluir_en_promedio', 'peso_en_promedio', 'observaciones_generales'
        ]
        widgets = {
            'lista_cotejo': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Evaluación de cuaderno - Marzo 2026'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción (opcional)'
            }),
            'materia': forms.Select(attrs={'class': 'form-select'}),
            'curso': forms.Select(attrs={'class': 'form-select'}),
            'fecha_evaluacion': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_limite': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'incluir_en_promedio': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'peso_en_promedio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'observaciones_generales': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones generales (opcional)'
            }),
        }
        labels = {
            'lista_cotejo': 'Lista de Cotejo',
            'nombre': 'Nombre de la Evaluación',
            'descripcion': 'Descripción',
            'materia': 'Materia',
            'curso': 'Curso',
            'fecha_evaluacion': 'Fecha de Evaluación',
            'fecha_limite': 'Fecha Límite para Calificar',
            'estado': 'Estado',
            'incluir_en_promedio': 'Incluir en Promedio Final',
            'peso_en_promedio': 'Peso en Promedio (%)',
            'observaciones_generales': 'Observaciones Generales',
        }


class CalificacionCotejoForm(forms.ModelForm):
    """Formulario para calificar un criterio individual"""
    
    class Meta:
        from .models import CalificacionCotejo
        model = CalificacionCotejo
        fields = ['valor', 'cumple', 'observacion']
        widgets = {
            'valor': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01'
            }),
            'cumple': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observacion': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': 'Observación (opcional)'
            }),
        }


class BuscarListaCotejoForm(forms.Form):
    """Formulario para buscar y filtrar listas de cotejo"""
    
    buscar = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre...'
        }),
        label='Buscar'
    )
    
    tipo_evaluacion = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los tipos')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo'
    )
    
    materia = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Se define en __init__
        empty_label='Todas las materias',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Materia'
    )
    
    solo_plantillas = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Solo Plantillas'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Construir choices dinámicamente
        from .models import Materia, ListaCotejo
        self.fields['tipo_evaluacion'].choices = [('', 'Todos los tipos')] + ListaCotejo.TIPO_EVALUACION_CHOICES
        
        if user:
            if user.rol == 'Profesor':
                self.fields['materia'].queryset = Materia.objects.filter(profesor=user)
            else:
                self.fields['materia'].queryset = Materia.objects.all()


# ====================================================================
#  FORMULARIO PARA IMPORTACIÓN DE USUARIOS POR CSV
# ====================================================================

class ImportarUsuariosCSVForm(forms.Form):
    """Formulario para subir archivo CSV con usuarios"""
    archivo_csv = forms.FileField(
        label='Archivo CSV',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv',
        }),
        help_text='Seleccione un archivo CSV con los datos de los usuarios'
    )

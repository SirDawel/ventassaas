from django import forms
from django.contrib.auth.forms import UserCreationForm
#from Escuela.escuelaweb.models import CustomUser, CustomUserManager, Persona, AnhoEscolar, Curso, Materia, Matricula
from .models import CustomUser, CustomUserManager, Persona, AnhoEscolar, Curso, Materia, Matricula

  # Importamos el modelo de usuario personalizado



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

    class Meta:
        model = CustomUser
        fields = [
            "first_name", "last_name", "email", "fecha_nacimiento", "genero",
            "telefono", "direccion", "cedula",
            "rol", "grado", "seccion", "especialidad", "departamento",
            "contacto_emergencia_nombre", "contacto_emergencia_telefono",
            "contacto_emergencia_parentesco",
            "password1", "password2",
        ]

        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}),
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
        fields = ['estudiante', 'concepto', 'monto', 'observaciones', 'activo']
        widgets = {
            'estudiante': forms.Select(attrs={'class': 'form-select'}),
            'concepto': forms.Select(attrs={'class': 'form-select'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observaciones': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Zona cercana, Zona lejana'}),
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

    class Meta:
        model = CustomUser
        fields = [
            'email', 'first_name', 'last_name', 'fecha_nacimiento', 'genero',
            'direccion', 'telefono', 'cedula', 'rol', 'grado', 'seccion',
            'especialidad', 'departamento', 'contacto_emergencia_nombre',
            'contacto_emergencia_telefono', 'contacto_emergencia_parentesco'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
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


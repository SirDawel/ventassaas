from django.contrib import admin

# Register your models here.
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Admin personalizado para CustomUser
@admin.register(get_user_model())
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'rol', 'is_active', 'is_staff')
    list_filter = ('rol', 'is_active', 'is_staff', 'genero')
    search_fields = ('email', 'first_name', 'last_name', 'cedula')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'fecha_nacimiento', 'genero', 'cedula')}),
        ('Contacto', {'fields': ('telefono', 'direccion')}),
        ('Rol y Datos Académicos/Laborales', {'fields': ('rol', 'grado', 'seccion', 'especialidad', 'departamento')}),
        ('Grupo Familiar', {'fields': ('grupo_familiar',)}),
        ('Configuración de Mora Individual', {
            'fields': ('porcentaje_mora_individual', 'dia_vencimiento_individual'),
            'description': 'Esta configuración solo aplica si el estudiante NO está en un grupo familiar'
        }),
        ('Configuración de Descuento Individual', {
            'fields': ('descuento_individual',),
            'description': 'Este descuento solo aplica si el estudiante NO está en un grupo familiar'
        }),
        ('Contacto de Emergencia', {'fields': ('contacto_emergencia_nombre', 'contacto_emergencia_telefono', 'contacto_emergencia_parentesco')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined', 'fecha_ingreso', 'fecha_salida')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'rol', 'password1', 'password2'),
        }),
    )

from .models import Asistencia, AsistenciaPersonal, GrupoFamiliar
from .models import TarifaEstudiante
from .models import AsientoContable, DetalleAsiento
from .models import ConfiguracionEscuela

# Registro de Grupo Familiar
@admin.register(GrupoFamiliar)
class GrupoFamiliarAdmin(admin.ModelAdmin):
    list_display = ('codigo_familia', 'apellido_familia', 'cantidad_estudiantes', 'descuento_general', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('codigo_familia', 'apellido_familia', 'telefono_contacto', 'email_contacto')
    readonly_fields = ('fecha_creacion', 'actualizado', 'creado_por')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo_familia', 'apellido_familia', 'activo')
        }),
        ('Contacto', {
            'fields': ('telefono_contacto', 'email_contacto', 'direccion')
        }),
        ('Configuración de Pagos', {
            'fields': ('descuento_general',)
        }),
        ('Notas', {
            'fields': ('notas',)
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'fecha_creacion', 'actualizado'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'materia', 'fecha', 'estado', 'registrado_por', 'created_at')
    list_filter = ('estado', 'fecha', 'materia', 'materia__curso')
    search_fields = ('estudiante__first_name', 'estudiante__last_name', 'estudiante__email', 'materia__nombre')
    date_hierarchy = 'fecha'
    ordering = ('-fecha', 'estudiante__first_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('estudiante', 'materia', 'fecha', 'estado')
        }),
        ('Detalles', {
            'fields': ('observaciones', 'registrado_por')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AsistenciaPersonal)
class AsistenciaPersonalAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'get_rol', 'fecha', 'estado', 'hora_entrada', 'hora_salida', 'registrado_por', 'created_at')
    list_filter = ('estado', 'fecha', 'usuario__rol')
    search_fields = ('usuario__first_name', 'usuario__last_name', 'usuario__email')
    date_hierarchy = 'fecha'
    ordering = ('-fecha', 'usuario__first_name')
    readonly_fields = ('created_at', 'updated_at', 'get_horas_trabajadas_display')
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('usuario', 'fecha', 'estado')
        }),
        ('Horario', {
            'fields': ('hora_entrada', 'hora_salida', 'get_horas_trabajadas_display')
        }),
        ('Detalles', {
            'fields': ('observaciones', 'registrado_por')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_rol(self, obj):
        return obj.usuario.rol
    get_rol.short_description = 'Rol'
    get_rol.admin_order_field = 'usuario__rol'
    
    def get_horas_trabajadas_display(self, obj):
        horas = obj.get_horas_trabajadas()
        if horas:
            return f"{horas:.2f} horas"
        return "N/A"
    get_horas_trabajadas_display.short_description = 'Horas Trabajadas'

from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def admin_dashboard(request):
    return render(request, "admin/dashboard.html")

class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("dashboard/", self.admin_view(admin_dashboard), name="admin_dashboard"),
        ]
        return custom_urls + urls

admin_site = CustomAdminSite(name="custom_admin")

# Registrar TarifaEstudiante en admin
@admin.register(TarifaEstudiante)
class TarifaEstudianteAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'concepto', 'monto', 'observaciones', 'activo', 'fecha_creacion')
    list_filter = ('concepto__tipo', 'activo')
    search_fields = ('estudiante__first_name', 'estudiante__last_name', 'estudiante__email', 'concepto__nombre')
    ordering = ('-fecha_creacion',)


# ============================================
# ADMIN DE CONTABILIDAD - Plan de Cuentas
# ============================================

from .models import PlanCuentas

@admin.register(PlanCuentas)
class PlanCuentasAdmin(admin.ModelAdmin):
    list_display = (
        'codigo', 'nombre', 'tipo_cuenta', 'naturaleza', 
        'nivel', 'es_detalle', 'saldo_actual', 'activo'
    )
    list_filter = (
        'tipo_cuenta', 'naturaleza', 'nivel', 
        'es_detalle', 'activo', 'requiere_centro_costo', 'requiere_tercero'
    )
    search_fields = ('codigo', 'nombre', 'descripcion')
    ordering = ('codigo',)
    readonly_fields = (
        'nivel', 'fecha_creacion', 'fecha_modificacion', 
        'creado_por', 'modificado_por', 'saldo_calculado_display'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion')
        }),
        ('Clasificación Contable', {
            'fields': ('tipo_cuenta', 'naturaleza', 'nivel', 'cuenta_padre')
        }),
        ('Configuración', {
            'fields': ('es_detalle', 'activo', 'requiere_centro_costo', 'requiere_tercero')
        }),
        ('Saldos', {
            'fields': ('saldo_inicial', 'saldo_actual', 'saldo_calculado_display')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_modificacion', 'creado_por', 'modificado_por'),
            'classes': ('collapse',)
        }),
    )
    
    def saldo_calculado_display(self, obj):
        """Muestra el saldo calculado comparado con el saldo actual"""
        saldo_calc = obj.calcular_saldo()
        if saldo_calc != obj.saldo_actual:
            return f"${saldo_calc:,.2f} (Diferencia: ${saldo_calc - obj.saldo_actual:,.2f})"
        return f"${saldo_calc:,.2f} ✓"
    saldo_calculado_display.short_description = 'Saldo Calculado'
    
    def save_model(self, request, obj, form, change):
        """Guardar el usuario que crea o modifica la cuenta"""
        if not change:  # Si es nuevo
            obj.creado_por = request.user
        else:  # Si es modificación
            obj.modificado_por = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """Si la cuenta tiene movimientos, algunos campos no se pueden editar"""
        readonly = list(self.readonly_fields)
        if obj and obj.tiene_movimientos():
            readonly.extend(['codigo', 'tipo_cuenta', 'naturaleza', 'cuenta_padre'])
        return readonly

# ============================================
# ADMINISTRACIÓN DE ASIENTOS CONTABLES
# ============================================

class DetalleAsientoInline(admin.TabularInline):
    """Inline para mostrar las líneas del asiento"""
    model = DetalleAsiento
    extra = 0
    fields = ['linea', 'cuenta', 'descripcion', 'debito', 'credito', 'centro_costo']
    readonly_fields = ['linea']
    
    def has_add_permission(self, request, obj=None):
        # No permitir agregar líneas desde el admin si ya está contabilizado
        if obj and obj.estado != 'BORRADOR':
            return False
        return super().has_add_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar líneas desde el admin si ya está contabilizado
        if obj and obj.estado != 'BORRADOR':
            return False
        return super().has_delete_permission(request, obj)


@admin.register(AsientoContable)
class AsientoContableAdmin(admin.ModelAdmin):
    """Administración de asientos contables"""
    list_display = [
        'numero_asiento',
        'fecha_asiento',
        'tipo_asiento',
        'concepto_corto',
        'total_debito',
        'total_credito',
        'estado',
        'cuadrado_display',
        'creado_por',
    ]
    list_filter = [
        'estado',
        'tipo_asiento',
        'fecha_asiento',
    ]
    search_fields = [
        'numero_asiento',
        'concepto',
        'referencia',
    ]
    readonly_fields = [
        'numero_asiento',
        'total_debito',
        'total_credito',
        'cuadrado_display',
        'creado_por',
        'fecha_creacion',
        'contabilizado_por',
        'fecha_contabilizacion',
        'anulado_por',
    ]
    date_hierarchy = 'fecha_asiento'
    inlines = [DetalleAsientoInline]
    
    fieldsets = (
        ('Información del Asiento', {
            'fields': (
                'numero_asiento',
                'fecha_asiento',
                'tipo_asiento',
                'concepto',
                'referencia',
            )
        }),
        ('Totales', {
            'fields': (
                'total_debito',
                'total_credito',
                'cuadrado_display',
            )
        }),
        ('Estado', {
            'fields': (
                'estado',
                'notas',
            )
        }),
        ('Información de Auditoría', {
            'fields': (
                ('creado_por', 'fecha_creacion'),
                ('contabilizado_por', 'fecha_contabilizacion'),
                'anulado_por',
                'motivo_anulacion',
            ),
            'classes': ('collapse',),
        }),
    )
    
    def concepto_corto(self, obj):
        """Muestra un concepto recortado"""
        if len(obj.concepto) > 50:
            return f"{obj.concepto[:47]}..."
        return obj.concepto
    concepto_corto.short_description = 'Concepto'
    
    def cuadrado_display(self, obj):
        """Muestra si el asiento está cuadrado"""
        if obj.esta_cuadrado():
            return "✓ Cuadrado"
        return "✗ Descuadrado"
    cuadrado_display.short_description = 'Estado'
    cuadrado_display.boolean = True
    
    def get_readonly_fields(self, request, obj=None):
        """Campos de solo lectura según el estado"""
        readonly = list(self.readonly_fields)
        
        # Si el asiento está contabilizado o anulado, todo es readonly
        if obj and obj.estado in ['CONTABILIZADO', 'ANULADO']:
            readonly.extend([
                'fecha_asiento',
                'tipo_asiento',
                'concepto',
                'referencia',
                'notas',
                'estado',
            ])
        
        return readonly
    
    def has_delete_permission(self, request, obj=None):
        # Solo se pueden eliminar borradores
        if obj and obj.estado != 'BORRADOR':
            return False
        return super().has_delete_permission(request, obj)
    
    def save_model(self, request, obj, form, change):
        """Establecer el usuario que crea el asiento"""
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(DetalleAsiento)
class DetalleAsientoAdmin(admin.ModelAdmin):
    """Administración de detalles de asientos"""
    list_display = [
        'asiento',
        'linea',
        'cuenta',
        'descripcion_corta',
        'debito',
        'credito',
    ]
    list_filter = [
        'asiento__fecha_asiento',
        'asiento__estado',
    ]
    search_fields = [
        'asiento__numero_asiento',
        'cuenta__codigo',
        'cuenta__nombre',
        'descripcion',
    ]
    
    def descripcion_corta(self, obj):
        """Muestra una descripción recortada"""
        if len(obj.descripcion) > 40:
            return f"{obj.descripcion[:37]}..."
        return obj.descripcion
    descripcion_corta.short_description = 'Descripción'
    
    def has_delete_permission(self, request, obj=None):
        # Solo se pueden eliminar líneas de borradores
        if obj and obj.asiento.estado != 'BORRADOR':
            return False
        return super().has_delete_permission(request, obj)


# ============================================
# MODELOS DE SEGURIDAD
# ============================================

from .models import LoginAttempt, SecurityLog, UserSession, TwoFactorAuth


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('email', 'ip_address', 'exitoso', 'user', 'fecha', 'razon_fallo', 'esta_bloqueado')
    list_filter = ('exitoso', 'fecha')
    search_fields = ('email', 'ip_address', 'razon_fallo')
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)
    readonly_fields = ('email', 'ip_address', 'user_agent', 'exitoso', 'fecha', 'razon_fallo', 'user')
    actions = ['desbloquear_cuentas']
    
    def has_add_permission(self, request):
        return False  # No permitir crear manualmente
    
    def has_change_permission(self, request, obj=None):
        return False  # Solo lectura
    
    def esta_bloqueado(self, obj):
        """Indica si el email de este intento está actualmente bloqueado"""
        from django.utils.html import format_html
        if LoginAttempt.is_blocked(obj.email):
            return format_html('<span style="color: red; font-weight: bold;">🔒 BLOQUEADO</span>')
        return format_html('<span style="color: green;">✓ Activo</span>')
    esta_bloqueado.short_description = 'Estado de Cuenta'
    
    def desbloquear_cuentas(self, request, queryset):
        """Acción para desbloquear cuentas seleccionadas"""
        emails_unicos = queryset.values_list('email', flat=True).distinct()
        total_desbloqueados = 0
        
        for email in emails_unicos:
            count = LoginAttempt.unblock_account(email)
            if count > 0:
                total_desbloqueados += 1
                
                # Registrar evento de seguridad
                from .models import SecurityLog
                SecurityLog.log_event(
                    tipo_evento='ACCOUNT_UNLOCKED',
                    descripcion=f'Cuenta desbloqueada manualmente por {request.user.email}',
                    email=email,
                    usuario=None,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    nivel_severidad='INFO',
                    metadata={'admin_user': request.user.email}
                )
        
        self.message_user(
            request, 
            f'{total_desbloqueados} cuenta(s) desbloqueada(s) exitosamente.'
        )
    desbloquear_cuentas.short_description = 'Desbloquear cuentas seleccionadas'
    
    fieldsets = (
        ('Información del Intento', {
            'fields': ('email', 'user', 'exitoso', 'razon_fallo')
        }),
        ('Información de Red', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Fecha', {
            'fields': ('fecha',)
        }),
    )


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'usuario', 'email', 'tipo_evento', 'nivel_severidad', 'descripcion_corta', 'ip_address')
    list_filter = ('tipo_evento', 'nivel_severidad', 'fecha')
    search_fields = ('usuario__email', 'email', 'descripcion', 'ip_address')
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)
    readonly_fields = ('usuario', 'email', 'tipo_evento', 'nivel_severidad', 'descripcion', 
                      'ip_address', 'user_agent', 'fecha', 'metadata')
    
    def has_add_permission(self, request):
        return False  # No permitir crear manualmente
    
    def has_change_permission(self, request, obj=None):
        return False  # Solo lectura
    
    def descripcion_corta(self, obj):
        """Muestra una descripción recortada"""
        if len(obj.descripcion) > 50:
            return f"{obj.descripcion[:47]}..."
        return obj.descripcion
    descripcion_corta.short_description = 'Descripción'
    
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario', 'email')
        }),
        ('Evento', {
            'fields': ('tipo_evento', 'nivel_severidad', 'descripcion')
        }),
        ('Información de Red', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Fecha', {
            'fields': ('fecha',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'ip_address', 'fecha_inicio', 'fecha_ultima_actividad', 'activa', 'fecha_cierre')
    list_filter = ('activa', 'fecha_inicio')
    search_fields = ('usuario__email', 'ip_address', 'session_key')
    date_hierarchy = 'fecha_inicio'
    ordering = ('-fecha_inicio',)
    readonly_fields = ('usuario', 'session_key', 'ip_address', 'user_agent', 
                      'fecha_inicio', 'fecha_ultima_actividad', 'fecha_cierre')
    
    actions = ['cerrar_sesiones']
    
    def has_add_permission(self, request):
        return False  # No permitir crear manualmente
    
    def cerrar_sesiones(self, request, queryset):
        """Acción para cerrar sesiones seleccionadas"""
        for sesion in queryset.filter(activa=True):
            sesion.cerrar_sesion()
        self.message_user(request, f'{queryset.filter(activa=True).count()} sesiones cerradas.')
    cerrar_sesiones.short_description = 'Cerrar sesiones seleccionadas'
    
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario',)
        }),
        ('Sesión', {
            'fields': ('session_key', 'activa')
        }),
        ('Información de Red', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_ultima_actividad', 'fecha_cierre')
        }),
    )


@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'habilitado', 'fecha_habilitacion', 'ultimo_uso')
    list_filter = ('habilitado', 'fecha_habilitacion')
    search_fields = ('usuario__email',)
    readonly_fields = ('usuario', 'secret_key', 'backup_codes', 
                      'fecha_habilitacion', 'ultimo_uso')
    
    def has_add_permission(self, request):
        return False  # No permitir crear manualmente
    
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario', 'habilitado')
        }),
        ('Configuración 2FA', {
            'fields': ('secret_key', 'backup_codes'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('fecha_habilitacion', 'ultimo_uso')
        }),
    )


# ============================================
# Modelos de Evaluaciones con Rúbricas
# ============================================
from .models import EvaluacionRubrica, CalificacionCriterio, Rubrica, CriterioRubrica, NivelDesempeno

@admin.register(Rubrica)
class RubricaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'materia', 'tipo_actividad', 'total_criterios', 'total_ponderacion', 'puntaje_maximo', 'activa', 'fecha_creacion')
    list_filter = ('tipo_actividad', 'activa', 'fecha_creacion', 'materia__curso')
    search_fields = ('nombre', 'materia__nombre', 'descripcion', 'creado_por__email')
    date_hierarchy = 'fecha_creacion'
    ordering = ('-fecha_creacion',)
    readonly_fields = ('fecha_creacion', 'total_criterios', 'total_ponderacion', 'puntaje_maximo', 'ponderacion_valida')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'materia', 'tipo_actividad', 'descripcion')
        }),
        ('Estado', {
            'fields': ('activa',)
        }),
        ('Estadísticas', {
            'fields': ('total_criterios', 'total_ponderacion', 'puntaje_maximo', 'ponderacion_valida'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'fecha_creacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CriterioRubrica)
class CriterioRubricaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rubrica', 'ponderacion', 'orden')
    list_filter = ('rubrica__materia', 'rubrica')
    search_fields = ('nombre', 'descripcion', 'rubrica__nombre')
    ordering = ('rubrica', 'orden')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('rubrica', 'nombre', 'descripcion')
        }),
        ('Configuración', {
            'fields': ('ponderacion', 'orden')
        }),
    )


@admin.register(NivelDesempeno)
class NivelDesempenoAdmin(admin.ModelAdmin):
    list_display = ('criterio', 'nivel', 'puntaje', 'get_rubrica')
    list_filter = ('nivel', 'criterio__rubrica')
    search_fields = ('criterio__nombre', 'descriptor')
    ordering = ('criterio', '-puntaje')
    
    def get_rubrica(self, obj):
        return obj.criterio.rubrica.nombre
    get_rubrica.short_description = 'Rúbrica'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('criterio', 'nivel', 'puntaje')
        }),
        ('Descripción', {
            'fields': ('descriptor',)
        }),
    )


@admin.register(EvaluacionRubrica)
class EvaluacionRubricaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'rubrica', 'materia', 'curso', 'fecha_evaluacion', 'periodo', 'total_estudiantes', 'activa')
    list_filter = ('activa', 'periodo', 'fecha_evaluacion', 'materia__curso')
    search_fields = ('titulo', 'descripcion', 'rubrica__nombre', 'materia__nombre')
    date_hierarchy = 'fecha_evaluacion'
    ordering = ('-fecha_evaluacion',)
    readonly_fields = ('fecha_creacion', 'total_estudiantes', 'puntaje_promedio')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('titulo', 'descripcion', 'rubrica')
        }),
        ('Configuración Académica', {
            'fields': ('materia', 'curso', 'periodo', 'fecha_evaluacion')
        }),
        ('Estado', {
            'fields': ('activa',)
        }),
        ('Estadísticas', {
            'fields': ('total_estudiantes', 'puntaje_promedio'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('creada_por', 'fecha_creacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CalificacionCriterio)
class CalificacionCriterioAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'evaluacion', 'criterio', 'nivel_otorgado', 'puntaje_ponderado', 'fecha_calificacion')
    list_filter = ('evaluacion__periodo', 'evaluacion__materia', 'nivel_otorgado__nivel')
    search_fields = ('estudiante__first_name', 'estudiante__last_name', 'evaluacion__titulo', 'criterio__nombre')
    date_hierarchy = 'fecha_calificacion'
    ordering = ('-fecha_calificacion',)
    readonly_fields = ('fecha_calificacion', 'puntaje_ponderado')
    
    fieldsets = (
        ('Evaluación', {
            'fields': ('evaluacion', 'estudiante')
        }),
        ('Calificación', {
            'fields': ('criterio', 'nivel_otorgado', 'puntaje_ponderado')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
        ('Auditoría', {
            'fields': ('fecha_calificacion',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ConfiguracionEscuela)
class ConfiguracionEscuelaAdmin(admin.ModelAdmin):
    list_display = ('nombre_escuela', 'rnc', 'telefono', 'email', 'fecha_actualizacion')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre_escuela', 'rnc', 'direccion', 'telefono', 'email', 'sitio_web')
        }),
        ('Identidad Visual', {
            'fields': ('logo', 'lema')
        }),
        ('Misión y Visión', {
            'fields': ('mision', 'vision')
        }),
        ('Información Administrativa', {
            'fields': (
                'director_nombre', 'director_firma', 'codigo_centro',
                'distrito_educativo', 'regional_educativa', 'nivel_educativo',
                'modalidad', 'horario_atencion', 'anho_fundacion'
            )
        }),
        ('Configuración de Reportes', {
            'fields': ('mostrar_logo_reportes', 'pie_pagina_reportes')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Solo permitir crear si no existe ningún registro"""
        return not ConfiguracionEscuela.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar la configuración"""
        return False


# ============================================
# MODELOS DE SEGURIDAD ADICIONALES
# ============================================

from .models import IPBlocklist, SecurityAlert

@admin.register(IPBlocklist)
class IPBlocklistAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'tipo_bloqueo', 'es_temporal', 'fecha_expiracion', 
                    'activo', 'intentos_durante_bloqueo', 'fecha_bloqueo')
    list_filter = ('activo', 'tipo_bloqueo', 'es_temporal', 'fecha_bloqueo')
    search_fields = ('ip_address', 'razon', 'pais')
    readonly_fields = ('fecha_bloqueo', 'ultima_actividad', 'intentos_durante_bloqueo')
    date_hierarchy = 'fecha_bloqueo'
    ordering = ('-fecha_bloqueo',)
    
    fieldsets = (
        ('Información de Bloqueo', {
            'fields': ('ip_address', 'tipo_bloqueo', 'razon', 'bloqueado_por')
        }),
        ('Estado del Bloqueo', {
            'fields': ('activo', 'es_temporal', 'fecha_expiracion')
        }),
        ('Estadísticas', {
            'fields': ('intentos_durante_bloqueo', 'fecha_bloqueo', 'ultima_actividad')
        }),
        ('Información Adicional', {
            'fields': ('pais', 'user_agent', 'metadata'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activar_bloqueo', 'desactivar_bloqueo', 'limpiar_expirados']
    
    def activar_bloqueo(self, request, queryset):
        """Activar bloqueos seleccionados"""
        count = queryset.update(activo=True)
        self.message_user(request, f"{count} bloqueo(s) activado(s).")
    activar_bloqueo.short_description = "Activar bloqueos seleccionados"
    
    def desactivar_bloqueo(self, request, queryset):
        """Desactivar bloqueos seleccionados"""
        count = queryset.update(activo=False)
        self.message_user(request, f"{count} bloqueo(s) desactivado(s).")
    desactivar_bloqueo.short_description = "Desactivar bloqueos seleccionados"
    
    def limpiar_expirados(self, request, queryset):
        """Limpiar bloqueos temporales expirados"""
        IPBlocklist.cleanup_expired_blocks()
        self.message_user(request, "Bloqueos expirados limpiados correctamente.")
    limpiar_expirados.short_description = "Limpiar bloqueos expirados"


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo_alerta', 'nivel_prioridad', 'estado', 
                    'usuario_afectado', 'ip_address', 'fecha_alerta', 'email_enviado')
    list_filter = ('tipo_alerta', 'nivel_prioridad', 'estado', 'email_enviado', 'fecha_alerta')
    search_fields = ('titulo', 'descripcion', 'ip_address', 'usuario_afectado__email')
    readonly_fields = ('fecha_alerta', 'fecha_revision', 'fecha_resolucion', 'fecha_email')
    date_hierarchy = 'fecha_alerta'
    ordering = ('-fecha_alerta',)
    
    fieldsets = (
        ('Información de la Alerta', {
            'fields': ('tipo_alerta', 'nivel_prioridad', 'estado', 'titulo', 'descripcion')
        }),
        ('Datos del Incidente', {
            'fields': ('usuario_afectado', 'ip_address')
        }),
        ('Gestión de la Alerta', {
            'fields': ('asignado_a', 'resuelto_por', 'notas', 'acciones_tomadas')
        }),
        ('Fechas', {
            'fields': ('fecha_alerta', 'fecha_revision', 'fecha_resolucion')
        }),
        ('Notificaciones', {
            'fields': ('email_enviado', 'fecha_email')
        }),
        ('Información Adicional', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marcar_en_revision', 'marcar_resuelta', 'marcar_falsa_alarma', 
               'enviar_notificacion_email']
    
    def marcar_en_revision(self, request, queryset):
        """Marcar alertas como en revisión"""
        for alerta in queryset:
            alerta.marcar_como_revisando(request.user)
        self.message_user(request, f"{queryset.count()} alerta(s) marcada(s) en revisión.")
    marcar_en_revision.short_description = "Marcar como En Revisión"
    
    def marcar_resuelta(self, request, queryset):
        """Marcar alertas como resueltas"""
        for alerta in queryset:
            alerta.resolver(request.user, acciones_tomadas="Resuelta desde admin")
        self.message_user(request, f"{queryset.count()} alerta(s) marcada(s) como resuelta(s).")
    marcar_resuelta.short_description = "Marcar como Resuelta"
    
    def marcar_falsa_alarma(self, request, queryset):
        """Marcar alertas como falsa alarma"""
        count = queryset.update(estado='FALSA_ALARMA')
        self.message_user(request, f"{count} alerta(s) marcada(s) como falsa alarma.")
    marcar_falsa_alarma.short_description = "Marcar como Falsa Alarma"
    
    def enviar_notificacion_email(self, request, queryset):
        """Enviar notificación por email"""
        for alerta in queryset:
            alerta.enviar_notificacion_email()
        self.message_user(request, f"Notificación enviada para {queryset.count()} alerta(s).")
    enviar_notificacion_email.short_description = "Enviar Notificación Email"


# ============================================
# ADMIN PARA POS FÍSICOS
# ============================================

from .models import TransaccionPOS, TerminalEstudiante

@admin.register(TransaccionPOS)
class TransaccionPOSAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id', 
        'proveedor', 
        'terminal_id', 
        'estudiante_info',
        'monto', 
        'estado', 
        'fecha_transaccion'
    )
    list_filter = ('proveedor', 'estado', 'fecha_transaccion')
    search_fields = (
        'transaction_id', 
        'terminal_id', 
        'estudiante__first_name', 
        'estudiante__last_name',
        'estudiante__cedula'
    )
    readonly_fields = (
        'transaction_id', 
        'proveedor', 
        'terminal_id', 
        'monto', 
        'referencia',
        'fecha_transaccion',
        'fecha_procesamiento',
        'datos_webhook',
        'tarjeta_ultimos_4',
        'tipo_tarjeta'
    )
    fieldsets = (
        ('Información de la Transacción', {
            'fields': (
                'transaction_id', 
                'proveedor', 
                'terminal_id', 
                'referencia',
                'fecha_transaccion',
                'fecha_procesamiento'
            )
        }),
        ('Detalles del Pago', {
            'fields': (
                'monto', 
                'tipo_tarjeta', 
                'tarjeta_ultimos_4'
            )
        }),
        ('Asociación', {
            'fields': (
                'estudiante', 
                'factura_pagada',
                'estado'
            )
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
        ('Datos Técnicos', {
            'fields': ('datos_webhook',),
            'classes': ('collapse',)
        }),
    )
    
    def estudiante_info(self, obj):
        if obj.estudiante:
            return f"{obj.estudiante.get_full_name()} ({obj.estudiante.cedula})"
        return "Sin identificar"
    estudiante_info.short_description = "Estudiante"
    
    def has_add_permission(self, request):
        # No permitir crear transacciones manualmente
        return False
    
    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar transacciones
        return False


@admin.register(TerminalEstudiante)
class TerminalEstudianteAdmin(admin.ModelAdmin):
    list_display = (
        'terminal_id', 
        'proveedor',
        'estudiante_info', 
        'activo', 
        'fecha_asignacion'
    )
    list_filter = ('proveedor', 'activo', 'fecha_asignacion')
    search_fields = (
        'terminal_id', 
        'estudiante__first_name', 
        'estudiante__last_name',
        'estudiante__cedula'
    )
    fieldsets = (
        ('Terminal', {
            'fields': ('terminal_id', 'proveedor')
        }),
        ('Estudiante', {
            'fields': ('estudiante',)
        }),
        ('Estado', {
            'fields': ('activo', 'observaciones')
        }),
    )
    
    def estudiante_info(self, obj):
        return f"{obj.estudiante.get_full_name()} ({obj.estudiante.cedula})"
    estudiante_info.short_description = "Estudiante"

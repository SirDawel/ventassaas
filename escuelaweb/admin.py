from django.contrib import admin

# Register your models here.
from django.contrib.auth import get_user_model
admin.site.register(get_user_model())

from .models import Asistencia, AsistenciaPersonal
from .models import TarifaEstudiante

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


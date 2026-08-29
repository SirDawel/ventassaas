"""
URLs para el schema PUBLIC (dominio principal sin tenant)
Aquí va el registro de escuelas y login inicial
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from ventasweb import views
from ventasweb.views import (
    login_view, 
    crear_ano_escolar, 
    password_reset_request, 
    password_reset_confirm,
    user_list, 
    user_create, 
    user_update, 
    user_delete,
    admin_dashboard, 
    get_users_data
)
from ventasweb.views_health import health_check

urlpatterns = [
    # Health check para AWS ECS
    path('health/', health_check, name='health_check'),
    
    path('admin/', admin.site.urls),
    
    # Redirigir raíz directamente a login
    path("", RedirectView.as_view(url='/login/', permanent=False), name="root_redirect"),
    
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path("resetpass/", views.resetpass, name="resetpass"),
    path('password_reset/', password_reset_request, name='password_reset'),
    path('reset/<uidb64>/<token>/', password_reset_confirm, name='password_reset_confirm'),
    
    # Registro de empresas (multi-tenant)
    path('registrar-empresa/', views.registrar_empresa, name='registrar_empresa'),
    path('activate-school/<uidb64>/<token>/', views.activate_school, name='activate_school'),
    
    # Páginas principales - Solo para schema público
    # NOTA: /plataform está disponible SOLO en tenants (no en público)
    path('base/', views.base, name='base'),
    path("anhoescolar/", crear_ano_escolar, name="anhoescolar"),
    
    # Dashboard administrativo
    path("admin/dashboard/", admin_dashboard, name="admin_dashboard"),
    path("admin/dashboard/users-data/", get_users_data, name="get_users_data"),
    
    # Configuración
    path("configuracion/escuela/", views.configuracion_escuela, name="configuracion_escuela"),
    
    # Estudiantes
    path('estudiantes/', views.lista_estudiantes, name='lista_estudiantes'),
    path('estudiantes/agregar/', views.agregar_estudiante, name='agregar_estudiante'),
    path('estudiantes/editar/<int:id>/', views.editar_estudiante, name='editar_estudiante'),
    path('estudiantes/eliminar/<int:id>/', views.eliminar_estudiante, name='eliminar_estudiante'),
    
    # Matrículas
    path('matriculas/confirmar-eliminar/<int:matricula_id>/', views.confirmar_eliminar_matricula, name='confirmar_eliminar_matricula'),
    
    # Personas
    path("personas/", views.persona_list, name="persona_list"),
    path("persona_list", views.persona_list, name="persona_list"),
    path('nuevo/<int:user_id>/', views.persona_create, name='persona_create'),
    path("editar/<int:pk>/", views.persona_update, name="persona_update"),
    path("eliminar/<int:pk>/", views.persona_delete, name="persona_delete"),
    path("persona_update/editar/<int:persona_id>/", views.persona_update, name="persona_update"),
    
    # Años Escolares
    path('anhos-escolares/', views.lista_anhos_escolares, name='lista_anhos_escolares'),
    path('anhos-escolares/agregar/', views.agregar_anho_escolar, name='agregar_anho_escolar'),
    path('anhos-escolares/editar/<int:pk>/', views.editar_anho_escolar, name='editar_anho_escolar'),
    path('anhos-escolares/eliminar/<int:pk>/', views.eliminar_anho_escolar, name='eliminar_anho_escolar'),
    
    # Cursos
    path("cursos/agregar/<int:anho_id>/", views.agregar_curso, name="agregar_curso"),
    path('cursos/', views.lista_cursos, name='lista_cursos'),
    path('cursos/agregar/', views.agregar_curso, name='agregar_curso'),
    path('cursos/editar/<int:pk>/', views.editar_curso, name='editar_curso'),
    path('cursos/eliminar/<int:pk>/', views.eliminar_curso, name='eliminar_curso'),
    path('cursos/confirmar-eliminar/<int:pk>/', views.confirmar_eliminar_curso, name='confirmar_eliminar_curso'),
    
    # Materias
    path('materias/', views.lista_materias, name='lista_materias'),
    path("materia/<int:materia_id>/reporte/", views.reporte_notas_materia, name="reporte_notas_materia"),
    path("curso/<int:curso_id>/reporte_general/", views.reporte_general, name="reporte_general"),
    path('materias/agregar/', views.agregar_materia, name='agregar_materia'),
    path('materias/agregar/<int:curso_id>/', views.agregar_materia, name='agregar_materia'),
    path('materias/editar/<int:pk>/', views.editar_materia, name='editar_materia'),
    path('materias/eliminar/<int:pk>/', views.eliminar_materia, name='eliminar_materia'),
    path('materias/confirmar-eliminar/<int:pk>/', views.confirmar_eliminar_materia, name='confirmar_eliminar_materia'),
    
    # ============================================
    # IMPORTANTE: NO incluir ventasweb.urls aquí
    # El schema público solo debe tener rutas de registro/landing
    # Todas las funcionalidades operativas van en los TENANTS
    # ============================================
    # path('', include('ventasweb.urls')),  # DESHABILITADO - Solo para tenants
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Manejador personalizado para error 404
handler404 = 'ventasweb.views.custom_404'

"""
URL configuration for Escuela project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

from escuelaweb import views
from escuelaweb.views import (
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

urlpatterns = [
    path('admin/', admin.site.urls),
    # Redirigir raíz directamente a login
    path("", RedirectView.as_view(url='/login/', permanent=False), name="root_redirect"),
    path("index/", views.index, name="index"),  # Página principal/inicio
    path("login/", login_view, name="login"),
    path("anhoescolar/", crear_ano_escolar, name="anhoescolar"),
    path("plataform", views.plataform, name="plataform"),  # La plataforma
    path('base/', views.base, name='base'),  # Ruta para la vista base
    path('noticias/', views.noticias, name='noticias'),
    path("logout/", views.logout_view, name="logout"),
    
    # para resetear contrasena
    path("resetpass/", views.resetpass, name="resetpass"),
    path('password_reset/', password_reset_request, name='password_reset'),
    path('reset/<uidb64>/<token>/', password_reset_confirm, name='password_reset_confirm'),
    #______________________Matricula___________________________________
    path('matriculas/confirmar-eliminar/<int:matricula_id>/', views.confirmar_eliminar_matricula, name='confirmar_eliminar_matricula'),

     #_____________________estudiates___________________________________
    path('estudiantes/', views.lista_estudiantes, name='lista_estudiantes'),
    path('estudiantes/agregar/', views.agregar_estudiante, name='agregar_estudiante'),
    path('estudiantes/editar/<int:id>/', views.editar_estudiante, name='editar_estudiante'),
    path('estudiantes/eliminar/<int:id>/', views.eliminar_estudiante, name='eliminar_estudiante'),

  #  ______________usuario____________________
    path("users/", user_list, name="user_list"),
    path("users/create/", user_create, name="user_create"),
    path("users/update/<int:user_id>/", user_update, name="user_update"),
    path("update/<int:user_id>/", user_update, name="user_update"),
    path("users/delete/<int:user_id>/", user_delete, name="user_delete"),
    path("users/profile/<int:user_id>/", views.user_profile, name="user_profile"),
    path("users/profile/picture/", views.update_profile_picture, name="update_profile_picture"),

#____________dashboard__________________________
    path("admin/dashboard/", admin_dashboard, name="admin_dashboard"),
    path("admin/dashboard/users-data/", get_users_data, name="get_users_data"),
#_______________persona___________________________________________________
    path("personas/", views.persona_list, name="persona_list"),
    path("persona_list", views.persona_list, name="persona_list"),
    path('nuevo/<int:user_id>/', views.persona_create, name='persona_create'),
    path("editar/<int:pk>/", views.persona_update, name="persona_update"),
    path("eliminar/<int:pk>/", views.persona_delete, name="persona_delete"),
    path("persona_update/editar/<int:persona_id>/", views.persona_update, name="persona_update"),
    
    # URLs para A�o Escolar
    path('anhos-escolares/', views.lista_anhos_escolares, name='lista_anhos_escolares'),
    path('anhos-escolares/agregar/', views.agregar_anho_escolar, name='agregar_anho_escolar'),
    path('anhos-escolares/editar/<int:pk>/', views.editar_anho_escolar, name='editar_anho_escolar'),
    path('anhos-escolares/eliminar/<int:pk>/', views.eliminar_anho_escolar, name='eliminar_anho_escolar'),
    
    # URLs para Cursos
    # urls.py
    path("cursos/agregar/<int:anho_id>/", views.agregar_curso, name="agregar_curso"),
    path('cursos/', views.lista_cursos, name='lista_cursos'),
    path('cursos/agregar/', views.agregar_curso, name='agregar_curso'),
    path('cursos/editar/<int:pk>/', views.editar_curso, name='editar_curso'),
    path('cursos/eliminar/<int:pk>/', views.eliminar_curso, name='eliminar_curso'),
    path('cursos/confirmar-eliminar/<int:pk>/', views.confirmar_eliminar_curso, name='confirmar_eliminar_curso'),
    
    # URLs para Materias
    path('materias/', views.lista_materias, name='lista_materias'),
    
    path("materia/<int:materia_id>/reporte/", views.reporte_notas_materia, name="reporte_notas_materia"),
    #reporte de todos estudiantes uno a uno
    #path("materias/<int:materia_id>/reporte_general/", views.reporte_general, name="reporte_general"),
    path("curso/<int:curso_id>/reporte_general/", views.reporte_general, name="reporte_general"),

    path('materias/agregar/', views.agregar_materia, name='agregar_materia'),
    
    path('materias/agregar/<int:curso_id>/', views.agregar_materia, name='agregar_materia'),

    path('materias/editar/<int:pk>/', views.editar_materia, name='editar_materia'),
    path('materias/eliminar/<int:pk>/', views.eliminar_materia, name='eliminar_materia'),
    path('materias/confirmar-eliminar/<int:pk>/', views.confirmar_eliminar_materia, name='confirmar_eliminar_materia'),
    
    # Incluir las demás URLs de escuelaweb
    path('', include('escuelaweb.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

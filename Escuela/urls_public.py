"""
URLs para el schema PUBLIC (dominio principal sin tenant)
Aquí va el registro de escuelas y login inicial
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from escuelaweb import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_public, name='home_public'),
    path('registrar-escuela/', views.registrar_escuela, name='registrar_escuela'),
    path('activate-school/<uidb64>/<token>/', views.activate_school, name='activate_school'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

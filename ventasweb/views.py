# -*- coding: utf-8 -*-
import uuid
from datetime import datetime, timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.http import JsonResponse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import uuid

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db.models import Q, Count, F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.html import strip_tags
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password

from .forms import (
    SignupForm, EstudianteForm, UserRegistrationForm, UserUpdateForm,
    ProfilePictureUpdateForm, PersonaForm, AnhoEscolarForm, CursoForm, MateriaForm, MatriculaForm
)
from .forms import TarifaEstudianteForm
from .models import Estudiante, CustomUser, AnhoEscolar, Persona, Curso, Materia, Matricula
from .models import TarifaEstudiante, ConceptoPago
from .models import StudentGroup, Asistencia, AsistenciaPersonal
from .decorators import admin_required, coordinador_required, coordinador_required

# Define User model once
User = get_user_model()

# ========================================
# HELPER: Año Fiscal Opcional
# ========================================
def obtener_periodo_fiscal_actual():
    """
    Retorna el año fiscal activo si existe, None si no existe.
    El sistema puede funcionar sin año fiscal, usando el año calendario actual.
    """
    try:
        return AnhoEscolar.objects.get(activo=True)
    except AnhoEscolar.DoesNotExist:
        return None

def logins(request):
    return render(request, 'website/login.html')


def base(request):
    return render(request, 'website/base.html')


def index(request):
    return render(request, 'website/index.html')


def resetpass(request):
    return render(request, 'website/password_reset.html')


@login_required(login_url="login")  # Redirige a la página de login si no está autenticado

def plataform(request):
    return render(request, "website/plataform.html")

def noticias(request):
    return render(request, 'website/noticias.html')


def empty_response(request):
    """Vista para manejar peticiones a recursos no existentes sin generar error 404"""
    from django.http import HttpResponse
    return HttpResponse(status=204)  # 204 No Content


# user form views


def signup_view(request):

    if request.method == "POST":

        form = SignupForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)  # Autenticar al usuario después del registro

            return redirect("home")  # Redirige a la página de inicio o dashboard

    else:

        form = SignupForm()

    return render(request, "website/signup.html", {"form": form})

  # Para mostrar mensajes en la plantilla


from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import uuid

def registerold(request):
    if request.method != "POST":
        return render(request, "website/register.html")

    firstname = request.POST.get("firstname", "").strip()
    lastname = request.POST.get("lastname", "").strip()
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "").strip()
    confirm_password = request.POST.get("confirm_password", "").strip()

    if not all([firstname, lastname, email, password, confirm_password]):
        messages.error(request, "Todos los campos son obligatorios.")
        return render(request, "website/register.html", {
            "firstname": firstname, "lastname": lastname, "email": email
        })

    if password != confirm_password:
        messages.error(request, "Las contraseñas no coinciden.")
        return render(request, "website/register.html", {
            "firstname": firstname, "lastname": lastname, "email": email
        })

    if User.objects.filter(email=email).exists():
        messages.error(request, "Este correo ya está registrado.")
        return render(request, "website/register.html", {
            "firstname": firstname, "lastname": lastname, "email": email
        })

    try:
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=firstname,
            last_name=lastname,
            is_active=False
        )

        user.activation_token = uuid.uuid4()
        user.save()

        # ✓ ï¸ ESTE ES EL BLOQUE CLAVE
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        print("UID:", uid)  #  Mira en consola qué imprime
        print("TOKEN:", user.activation_token)

        current_site = get_current_site(request)
        activation_url = f"{request.scheme}://{current_site.domain}/activate/{uid}/{user.activation_token}/"
        print("DEBUG URL FINAL:", activation_url)  #  Comprueba en consola

        mail_subject = "Activa tu cuenta"
        message = render_to_string(
            "website/email_verification.html",
            {"user": user, "activation_url": activation_url},
        )

        from django.core.mail import EmailMessage
        email_message = EmailMessage(mail_subject, message, None, [email])
        email_message.content_subtype = "html"
        email_message.send()

        messages.success(request, "Registro exitoso. Revisa tu correo para activar tu cuenta.")
        return redirect("login")

    except Exception as e:
        messages.error(request, f"Error en el registro: {str(e)}")
        return render(request, "website/register.html", {
            "firstname": firstname, "lastname": lastname, "email": email
        })





def activate(request, uidb64, token):

    try:

        uid = urlsafe_base64_decode(uidb64).decode()

        user = get_user_model().objects.get(pk=uid)

    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):

        user = None

    if user is not None:

        user.is_active = True

        user.save()

        messages.success(request, "Tu cuenta ha sido activada. ¡Ya puedes iniciar sesión!")

        return redirect("login")
    messages.error(request, "El enlace de activación no es válido.")

    return redirect("register")


def activate_school(request, uidb64, token):
    """
    Vista pública para activar una escuela registrada mediante email
    Similar a activate() pero para el modelo Client (tenant)
    🔒 SEGURIDAD: Verifica token UUID antes de activar la empresa
    """
    from .tenant_models import Client
    
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    try:
        # Decodificar UID
        uid = urlsafe_base64_decode(uidb64).decode()
        tenant = Client.objects.get(pk=uid)
        
        # Verificar que el token coincida
        if str(tenant.activation_token) != str(token):
            logger.warning(f'Token de activación inválido para tenant {tenant.schema_name}')
            messages.error(
                request, 
                '❌ El enlace de activación no es válido o ha expirado. '
                'Por favor, contacta con soporte si necesitas ayuda.'
            )
            return redirect('login')
        
        # Verificar que no esté ya activado
        if tenant.activo:
            messages.info(
                request,
                f'✅ La empresa "{tenant.nombre}" ya está activada. Puedes iniciar sesión.'
            )
            return redirect('login')
        
        # ✅ ACTIVAR LA EMPRESA
        tenant.activo = True
        tenant.activation_token = None  # Limpiar token usado
        tenant.save()
        
        logger.info(f'Empresa activada: {tenant.schema_name} ({tenant.nombre})')
        
        # 🔒 Log de seguridad
        try:
            from .models import SecurityLog
            SecurityLog.objects.create(
                tipo_evento='SCHOOL_ACTIVATED',
                nivel_severidad='INFO',
                email=tenant.email_contacto,
                ip_address=ip_address,
                user_agent=user_agent,
                descripcion=f'Empresa activada por email: {tenant.nombre} ({tenant.schema_name})',
                metadata={
                    'nombre_empresa': tenant.nombre,
                    'nombre_corto': tenant.schema_name,
                    'email_contacto': tenant.email_contacto,
                    'tenant_id': tenant.id
                }
            )
        except Exception as e:
            logger.error(f'Error registrando SecurityLog: {e}')
        
        # Enviar email de bienvenida (ahora que está activo)
        try:
            from django.core.mail import EmailMessage
            
            url_acceso = f'http://{tenant.schema_name}.localhost:8000' if settings.DEBUG else f'https://{tenant.schema_name}.ventasenlinea.com'
            
            subject = f'🎉 ¡Bienvenido a Sistema de Ventas, {tenant.nombre}!'
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #1cc88a; border-bottom: 3px solid #1cc88a; padding-bottom: 10px;">
                        ✅ ¡Tu Escuela Está Activa!
                    </h2>
                    <p>Tu institución <strong>{tenant.nombre}</strong> ha sido activada exitosamente.</p>
                    
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                color: white; padding: 25px; border-radius: 10px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: white;">🚀 Datos de Acceso</h3>
                        <p style="margin: 10px 0;"><strong>URL:</strong> <a href="{url_acceso}" style="color: #fff;">{url_acceso}</a></p>
                        <p style="margin: 10px 0;"><strong>Plan:</strong> {tenant.plan.title()}</p>
                        <p style="margin: 10px 0;"><strong>Usuarios:</strong> {tenant.max_usuarios}</p>
                    </div>
                    
                    <div style="background: #d4edda; padding: 15px; border-radius: 10px; margin: 20px 0; border-left: 5px solid #28a745;">
                        <h3 style="color: #155724; margin-top: 0;">📚 Próximos Pasos</h3>
                        <ol style="color: #155724; margin: 10px 0;">
                            <li>Inicia sesión con tu correo y contraseña</li>
                            <li>Configura tu catálogo de productos</li>
                            <li>Agrega vendedores y clientes</li>
                            <li>Crea tu primer pedido</li>
                            <li>¡Comienza a gestionar tu negocio!</li>
                        </ol>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{url_acceso}/login/" 
                           style="background: linear-gradient(180deg, #1cc88a 10%, #17a673 100%); 
                                  color: white; 
                                  padding: 15px 40px; 
                                  text-decoration: none; 
                                  border-radius: 5px; 
                                  display: inline-block;
                                  font-weight: bold;
                                  font-size: 16px;
                                  box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            🔐 Iniciar Sesión Ahora
                        </a>
                    </div>
                    
                    <div style="background: #f8f9fc; padding: 15px; border-radius: 10px; margin: 20px 0;">
                        <p style="margin: 0; color: #5a5c69; font-size: 14px;">
                            <strong>🔒 Seguridad y Privacidad</strong><br>
                            Tu empresa opera en su propio schema PostgreSQL completamente aislado.
                            Ninguna otra empresa puede acceder a tus datos.
                        </p>
                    </div>
                    
                    <p style="color: #858796; font-size: 13px; margin-top: 30px;">
                        Si tienes alguna pregunta o necesitas asistencia, nuestro equipo está listo para ayudarte.
                    </p>
                    
                    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e3e6f0; color: #858796; font-size: 12px; text-align: center;">
                        <p><strong>Sistema de Ventas Online</strong> - Gestión Comercial Profesional</p>
                        <p>Soporte: soporte@ventasenlinea.com</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            email = EmailMessage(
                subject,
                html_message,
                settings.DEFAULT_FROM_EMAIL,
                [tenant.email_contacto],
            )
            email.content_subtype = 'html'
            email.send(fail_silently=True)
            
        except Exception as e:
            logger.error(f'Error enviando email de bienvenida: {e}')
        
        # Mensaje de éxito
        messages.success(
            request,
            f'🎉 ¡Felicidades! Tu empresa <strong>{tenant.nombre}</strong> ha sido activada exitosamente. '
            f'Ya puedes iniciar sesión.'
        )
        
        # Redirigir al login del subdominio de la empresa activada
        url_acceso = f'http://{tenant.schema_name}.localhost:8000' if settings.DEBUG else f'https://{tenant.schema_name}.ventasenlinea.com'
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(f'{url_acceso}/login/')
        
    except (TypeError, ValueError, OverflowError) as e:
        logger.error(f'Error decodificando UID de activación: {e}')
        messages.error(request, '❌ El enlace de activación no es válido.')
        return redirect('login')
        
    except Client.DoesNotExist:
        logger.error(f'Tenant no encontrado para activación: uid={uid}')
        messages.error(request, '❌ No se encontró la empresa. El enlace puede haber expirado.')
        return redirect('login')
        
    except Exception as e:
        logger.error(f'Error activando escuela: {e}', exc_info=True)
        messages.error(request, f'❌ Error al activar la empresa. Contacta con soporte.')
        return redirect('login')


def login_view(request):
    # Obtener IP y User Agent
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # 🔒 Verificar si estamos en un tenant y si está activo
    try:
        from django.db import connection
        if hasattr(connection, 'tenant') and connection.tenant:
            tenant = connection.tenant
            # Si no es el schema público y el tenant no está activo
            if tenant.schema_name != 'public' and not tenant.activo:
                messages.warning(
                    request,
                    f'⚠️ La empresa <strong>{tenant.nombre}</strong> aún no ha sido activada. '
                    f'<br><br>📧 Por favor, revisa el correo electrónico enviado a <strong>{tenant.email_contacto}</strong> '
                    f'y haz clic en el enlace de activación. '
                    f'<br><br>💡 Si no encuentras el correo, revisa la carpeta de spam.'
                )
                return render(request, 'website/login.html', {'form': None, 'tenant_inactive': True})
    except Exception as e:
        logger.error(f'Error verificando estado del tenant: {e}')
    
    # Verificar si la IP está bloqueada
    try:
        from ventasweb.models import IPBlocklist
        if IPBlocklist.is_blocked(ip_address):
            messages.error(request, 'Acceso denegado. Tu IP ha sido bloqueada.')
            return render(request, 'website/login.html', {'form': None})
    except Exception:
        pass
    
    # Verificar si debe mostrar CAPTCHA (después de 2 intentos fallidos)
    show_captcha = False
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if email:
            from ventasweb.models import LoginAttempt
            intentos_recientes = LoginAttempt.get_recent_failed_attempts(email, minutes=15)
            show_captcha = intentos_recientes >= 2
    
    if request.method != "POST":
        form = None  # Solo para GET, renderizar sin formulario (modo actual)
        return render(request, 'website/login.html', {'form': form})

    try:
        from django.conf import settings
        from ventasweb.models import LoginAttempt, SecurityLog, SecurityAlert
        from ventasweb.forms import LoginForm
        
        # Crear formulario con CAPTCHA si es necesario
        form = LoginForm(request.POST, show_captcha=show_captcha)
        
        # Validar formulario (incluye honeypot y CAPTCHA)
        if not form.is_valid():
            # Si falla el honeypot, es un bot
            if 'website' in form.errors:
                # Registrar intento de bot
                SecurityLog.log_event(
                    tipo_evento='SUSPICIOUS_ACTIVITY',
                    descripcion=f'Bot detectado por honeypot desde IP {ip_address}',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    nivel_severidad='WARNING'
                )
                # Bloquear IP automáticamente
                from ventasweb.models import IPBlocklist
                IPBlocklist.block_ip(
                    ip_address=ip_address,
                    tipo_bloqueo='AUTO_SUSPICIOUS',
                    razon='Bot detectado por honeypot field',
                    es_temporal=True,
                    minutos_bloqueo=60
                )
                # No dar pistas al bot
                messages.error(request, "Credenciales incorrectas.")
                return render(request, 'website/login.html', {'form': form})
            
            # Error en CAPTCHA u otros campos
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return render(request, 'website/login.html', {'form': form})
        
        # Obtener datos validados
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        
        # Verificar si la cuenta está bloqueada por múltiples intentos fallidos
        if LoginAttempt.is_blocked(email, max_attempts=5, block_minutes=15):
            SecurityLog.log_event(
                tipo_evento='ACCOUNT_LOCKED',
                descripcion=f'Intento de acceso a cuenta bloqueada: {email}',
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                nivel_severidad='WARNING'
            )
            
            # Crear alerta de seguridad si hay muchos intentos
            intentos_totales = LoginAttempt.objects.filter(
                email=email,
                exitoso=False
            ).count()
            
            if intentos_totales >= 10:
                SecurityAlert.create_alert(
                    tipo_alerta='BRUTE_FORCE',
                    titulo=f'Múltiples intentos fallidos en cuenta: {email}',
                    descripcion=f'Se han detectado {intentos_totales} intentos fallidos de login para {email}. IP: {ip_address}',
                    nivel_prioridad='HIGH',
                    ip_address=ip_address,
                    metadata={'email': email, 'intentos': intentos_totales}
                )
            
            messages.error(
                request, 
                'Cuenta temporalmente bloqueada por múltiples intentos fallidos. '
                'Intenta nuevamente en 15 minutos.'
            )
            return render(request, 'website/login.html', {'form': form})

        # Verificar si el usuario existe
        from ventasweb.models import CustomUser
        user_exists = CustomUser.objects.filter(email=email).first()

        # Intentar autenticar
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_active:
                # Registrar login exitoso
                LoginAttempt.record_attempt(
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    exitoso=True,
                    user=user
                )
                
                SecurityLog.log_event(
                    tipo_evento='LOGIN',
                    descripcion=f'Login exitoso desde {ip_address}',
                    usuario=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    nivel_severidad='INFO'
                )
                
                login(request, user)
                
                # Actualizar último acceso
                user.ultimo_acceso = timezone.now()
                user.save(update_fields=['ultimo_acceso'])
                
                # Inicializar sesión
                request.session['last_activity'] = timezone.now().isoformat()

                messages.success(request, f"Bienvenido, {user.get_full_name()}")
                return redirect("plataform")
            else:
                # Cuenta inactiva
                LoginAttempt.record_attempt(
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    exitoso=False,
                    razon_fallo='Cuenta inactiva',
                    user=user
                )
                
                SecurityLog.log_event(
                    tipo_evento='LOGIN_FAILED',
                    descripcion='Intento de login en cuenta inactiva',
                    usuario=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    nivel_severidad='WARNING'
                )
                
                messages.error(request, "Tu cuenta no está activa. Por favor, verifica tu correo electrónico para activarla.")
                return render(request, 'website/login.html', {'form': form})
        else:
            # Login fallido
            razon = 'Usuario no existe' if not user_exists else 'Contraseña incorrecta'
            
            LoginAttempt.record_attempt(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                exitoso=False,
                razon_fallo=razon,
                user=user_exists
            )
            
            SecurityLog.log_event(
                tipo_evento='LOGIN_FAILED',
                descripcion=f'Login fallido: {razon}',
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                nivel_severidad='WARNING'
            )
            
            # Verificar cuántos intentos fallidos lleva
            intentos_fallidos = LoginAttempt.get_recent_failed_attempts(email, minutes=15)
            intentos_restantes = 5 - intentos_fallidos
            
            if intentos_restantes > 0:
                messages.error(
                    request, 
                    f"Correo electrónico o contraseña incorrectos. "
                    f"Te quedan {intentos_restantes} intentos antes de bloquear la cuenta."
                )
            else:
                messages.error(
                    request, 
                    "Cuenta bloqueada temporalmente por múltiples intentos fallidos. "
                    "Intenta nuevamente en 15 minutos."
                )
            
            return render(request, 'website/login.html', {'form': form})

    except Exception as e:
        logger.error(f"Error en login_view: {str(e)}")
        messages.error(request, f"Error al iniciar sesión: {str(e)}")
        return render(request, 'website/login.html', {'form': None})


# Función auxiliar para obtener IP del cliente
def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def logout_view(request):
    """Vista mejorada de logout con auditoría"""
    if request.user.is_authenticated:
        from ventasweb.models import SecurityLog, UserSession
        
        # Registrar logout
        SecurityLog.log_event(
            tipo_evento='LOGOUT',
            descripcion=f'Logout desde {get_client_ip(request)}',
            usuario=request.user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            nivel_severidad='INFO'
        )
        
        # Cerrar sesión en base de datos
        try:
            session_key = request.session.session_key
            if session_key:
                user_session = UserSession.objects.filter(session_key=session_key).first()
                if user_session:
                    user_session.cerrar_sesion()
        except Exception as e:
            logger.error(f"Error cerrando sesión en DB: {e}")

    logout(request)
    return redirect("login")


# para resetear contrasena


from django.contrib.auth.tokens import default_token_generator


def password_reset_request(request):
    if request.method != "POST":
        return render(request, 'website/password_reset.html')

    email = request.POST.get("email", "").strip()
    user = User.objects.filter(email=email).first()

    if user:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{request.scheme}://{request.get_host()}/reset/{uid}/{token}/"

        # Enviar correo
        send_mail(
            "Recuperación de contraseña",
            f"Haz clic en el siguiente enlace para restablecer tu contraseña:\n{reset_link}",
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        messages.success(request, "Se ha enviado un correo con las instrucciones para restablecer tu contraseña.")
        return redirect("login")  # ✓ Ahora correctamente fuera del paréntesis

    else:
        messages.error(request, "No se encontró ninguna cuenta con ese correo.")

    return redirect("password_reset")


#confirmar correo


from django.http import HttpResponse, JsonResponse


def password_reset_confirm2(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        user = None

    if not (user and default_token_generator.check_token(user, token)):
        return HttpResponse("Enlace inválido o expirado.", status=400)
    if request.method == "POST":
        new_password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        if new_password == confirm_password:
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Tu contraseña ha sido restablecida con éxito.")
            return redirect("login")
        messages.error(request, "Las contraseñas no coinciden.")
    return render(request, "website/password_reset_confirm.html", {"valid": True})


def password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if not (user is not None and default_token_generator.check_token(user, token)):
        messages.error(request, "El enlace no es válido o ha expirado.")
        return render(request, "website/password_reset_confirm.html", {"valid": False})
    if request.method == "POST":
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]
        if password == confirm_password:
            user.set_password(password)
            user.save()
            messages.success(request, "Tu contraseña ha sido cambiada. Inicia sesión.")
            return redirect("login")
        messages.error(request, "Las contraseñas no coinciden.")
    return render(
        request,
        "website/password_reset_confirm.html",
        {"valid": True, "uid": uidb64, "token": token},
    )


#año Escolar

admin_required
def crear_ano_escolar(request):
    if request.method == "POST":
        form = AnhoEscolarForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_anos_escolares')  # Redirige a la lista de años escolares
    else:
        form = AnhoEscolarForm()
    return render(request, "website/crear_anho.html", {"form": form})


#__________________estudiantes_____________


def lista_estudiantes(request):
    """Muestra la lista de estudiantes y permite búsqueda por ID, nombre o apellido."""
    query = request.GET.get('q')

    if query:
        estudiantes = Estudiante.objects.filter(
            Q(id__iexact=query)
            | Q(nombre__icontains=query)  # Busca coincidencias exactas con ID
            | Q(apellido__icontains=query)  # Busca por nombre  # Busca por apellido
        )
    else:
        estudiantes = Estudiante.objects.all()
    return render(request, 'est_forder/estudiantes.html', {'estudiantes': estudiantes})


def agregar_estudiante(request):
    """Permite agregar un nuevo estudiante."""
    if request.method == "POST":
        form = EstudianteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estudiante agregado exitosamente.')
            return redirect('lista_estudiantes')
    else:
        form = EstudianteForm()
    return render(request, 'est_forder/form_estudiante.html', {
        "form": form,
        "titulo": "Agregar Estudiante"
    })


def editar_estudiante(request, id):
    """Permite editar un estudiante existente."""
    estudiante = get_object_or_404(Estudiante, id=id)
    if request.method == "POST":
        form = EstudianteForm(request.POST, instance=estudiante)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estudiante actualizado exitosamente.')
            return redirect('lista_estudiantes')
    else:
        form = EstudianteForm(instance=estudiante)
    return render(request, 'est_forder/form_estudiante.html', {
        "form": form,
        "titulo": "Editar Estudiante",
        "estudiante": estudiante
    })


def eliminar_estudiante(request, id):
    """Permite eliminar un estudiante con confirmación."""
    estudiante = get_object_or_404(Estudiante, id=id)
    if request.method == "POST":
        estudiante.delete()
        return redirect('lista_estudiantes')
    return render(request, 'est_forder/eliminar_estudiante.html', {'estudiante': estudiante})


#_________________________usuario_______________________________


from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView

#  Verifica si el usuario es superusuario (Definido UNA SOLA VEZ)
def is_superuser(user):
    return user.is_superuser

#  Mensaje y redirección para usuarios sin permisos
def custom_redirect(request):
    messages.warning(request, "No tienes permisos para acceder a esta página.")
    return redirect("home")

@login_required
def user_list(request):
    # Permitir acceso a Administrador, Director y Secretaria
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    query = request.GET.get('q', '').strip()
    per_page = int(request.GET.get('per_page', 25))
    page_number = request.GET.get('page')
    page_sizes = [25, 50, 75, 100]

    users = User.objects.all().order_by('-date_joined')
    if query:
        users = users.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(cedula__icontains=query)
        )

    # Estadísticas por rol
    cant_estudiantes = User.objects.filter(rol='Estudiante', is_active=True).count()
    cant_profesores = User.objects.filter(rol='Profesor', is_active=True).count()
    cant_directores = User.objects.filter(rol='Director', is_active=True).count()
    cant_secretarias = User.objects.filter(rol='Secretaria', is_active=True).count()
    cant_administradores = User.objects.filter(rol='Administrador', is_active=True).count()
    cant_coordinadores = User.objects.filter(rol='Coordinador', is_active=True).count()
    cant_bibliotecarios = User.objects.filter(rol='Bibliotecario', is_active=True).count()
    cant_psicologos = User.objects.filter(rol='Psicologo', is_active=True).count()
    cant_otros = User.objects.filter(rol='Otro', is_active=True).count()
    
    # Suma de todos los roles
    suma_roles = (cant_estudiantes + cant_profesores + cant_directores + 
                  cant_secretarias + cant_administradores + cant_coordinadores + 
                  cant_bibliotecarios + cant_psicologos + cant_otros)
    
    estadisticas_roles = {
        'estudiantes': cant_estudiantes,
        'profesores': cant_profesores,
        'directores': cant_directores,
        'secretarias': cant_secretarias,
        'administradores': cant_administradores,
        'coordinadores': cant_coordinadores,
        'bibliotecarios': cant_bibliotecarios,
        'psicologos': cant_psicologos,
        'otros': cant_otros,
        'suma_roles': suma_roles,
        'total_activos': User.objects.filter(is_active=True).count(),
        'total_inactivos': User.objects.filter(is_active=False).count(),
        'total_usuarios': User.objects.count(),
    }

    paginator = Paginator(users, per_page)
    page_obj = paginator.get_page(page_number)

    return render(request, 'users/user_list.html', {
        'users': page_obj,
        'per_page': per_page,
        'page_sizes': page_sizes,
        'query': query,
        'estadisticas': estadisticas_roles,
    })

@login_required
def user_create(request):
    # Administradores, Gerentes y Secretaria pueden crear usuarios
    if request.user.rol not in ['Administrador', 'Gerente', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    if request.method == "POST":
        form = UserRegistrationForm(request.POST, usuario_actual=request.user)
        
        # Validación adicional de seguridad: Secretaria solo puede crear Clientes
        if request.user.rol == 'Secretaria':
            rol_enviado = request.POST.get('rol')
            if rol_enviado != 'Cliente':
                messages.error(request, 'La secretaria solo puede crear usuarios con rol "Cliente".')
                form = UserRegistrationForm(usuario_actual=request.user)
                return render(request, "users/user_form.html", {"form": form, "editing_user": None})
        
        if form.is_valid():
            try:
                # Verificar si el email ya existe (si se proporcionó)
                email = form.cleaned_data.get('email')
                if email and CustomUser.objects.filter(email=email).exists():
                    messages.error(request, "Este correo electrónico ya está registrado.")
                    return render(request, "users/user_form.html", {"form": form, "editing_user": None})

                # Crear el usuario (el formulario maneja la contraseña temporal automáticamente)
                user = form.save()

                messages.success(request, f"Usuario {user.get_full_name()} creado exitosamente como {user.rol}.")
                
                # Si es un cliente, redirigir a crear factura con el cliente preseleccionado
                if user.rol == 'Cliente':
                    return redirect(f"/facturas/nueva/?cliente_id={user.id}")
                
                # Para otros roles, ir a la lista de usuarios
                return redirect("user_list")
                
            except Exception as e:
                messages.error(request, f"Error al crear usuario: {str(e)}")
                form = UserRegistrationForm(usuario_actual=request.user)
        else:
            # Formulario inválido - mostrar errores en consola para debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("=" * 80)
            logger.warning("ERRORES DE VALIDACIÓN EN user_create:")
            logger.warning(f"form.errors: {form.errors}")
            logger.warning(f"form.non_field_errors: {form.non_field_errors()}")
            logger.warning("=" * 80)
            
            # Agregar mensaje de error visible
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        # Crear un nuevo formulario vacío
        form = UserRegistrationForm(usuario_actual=request.user)

    return render(request, "users/user_form.html", {"form": form, "editing_user": None})

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import CustomUser
from .forms import UserUpdateForm

@login_required
def user_update(request, user_id=None):
    # ----------------------------------------------------
    # 1. ¿ES CREAR O ACTUALIZAR?
    # ----------------------------------------------------
    if user_id:
        user = get_object_or_404(CustomUser, id=user_id)
        editing = True
        
        # Verificar permisos: Administradores, Directores y Secretaria pueden editar a cualquiera,
        # Usuarios comunes solo pueden cambiar su propia foto
        if request.user.rol not in ['Administrador', 'Director', 'Secretaria'] and request.user.id != user_id:
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('plataform')
    else:
        # Administradores, Directores y Secretaria pueden crear usuarios
        if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('plataform')
        user = None
        editing = False

    # ----------------------------------------------------
    # 2. PETICIÃN POST
    # ----------------------------------------------------
    if request.method == "POST":

        # ----------- FOTO PERFIL SOLO EDITANDO -----------
        if editing and "foto_perfil" in request.FILES and not request.POST.get("email"):
            user.foto_perfil = request.FILES["foto_perfil"]
            user.save()
            messages.success(request, "Foto de perfil actualizada.")
            
            # Redirigir según el rol
            if request.user.rol == 'Administrador' and request.user.id != user.id:
                return redirect("update_user", user_id=user.id)
            else:
                return redirect("user_profile", user_id=user.id)
        
        # ----------- SOLO ADMINISTRADORES, DIRECTORES Y SECRETARIA PUEDEN EDITAR DATOS COMPLETOS -----------
        if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
            messages.error(request, 'Solo los administradores, directores y secretarias pueden editar información completa de usuarios.')
            return redirect('user_profile', user_id=user.id)

        # ------------- FORMULARIO PARA CREAR O EDITAR -------------
        form = (
            UserUpdateForm(request.POST, instance=user, usuario_actual=request.user)
            if editing
            else UserRegistrationForm(request.POST, usuario_actual=request.user)
        )

        # Validación dinámica por rol (solo si los campos existen en el formulario)
        rol = request.POST.get("rol")
        if rol != "Profesor":
            if "especialidad" in form.fields:
                form.fields["especialidad"].required = False
            if "departamento" in form.fields:
                form.fields["departamento"].required = False
        if rol != "Estudiante":
            if "grado" in form.fields:
                form.fields["grado"].required = False
            if "seccion" in form.fields:
                form.fields["seccion"].required = False

        if form.is_valid():
            # Validación de seguridad: Secretaria solo puede crear/editar Clientes
            rol_formulario = form.cleaned_data.get("rol")
            if request.user.rol == 'Secretaria' and rol_formulario != 'Cliente':
                messages.error(request, 'La secretaria solo puede crear usuarios con rol "Cliente".')
                return render(request, "users/user_form.html", {
                    "form": form,
                    "editing_user": user,
                    "editing": editing
                })
            
            email = form.cleaned_data["email"]

            # Evitar duplicados
            qs = CustomUser.objects.filter(email=email)
            if editing:
                qs = qs.exclude(id=user_id)
            if qs.exists():
                messages.error(request, "Este correo ya está registrado.")
                return render(request, "users/user_form.html", {
                    "form": form,
                    "editing_user": user,
                    "editing": editing
                })

            # ------------------------ CREAR ------------------------
            if not editing:
                user = form.save(commit=False)
                user.set_password(form.cleaned_data.get("password1"))
                user.save()
                messages.success(request, "Usuario creado exitosamente.")
                return redirect("user_list")
            if request.method == "POST":
                print("POST data:", request.POST)

                if form.is_valid():
                    print("FORM IS VALID")
                    user = form.save()
                    print("User saved:", user)
                else:
                    print("FORM ERRORS:", form.errors)

            # ------------------------ EDITAR ------------------------
            user = form.save(commit=False)

            if form.cleaned_data.get("password1"):
                user.set_password(form.cleaned_data.get("password1"))

            user.save()

            messages.success(request, "Usuario actualizado correctamente.")
            return redirect("user_list")

        # Si no es válido
        for f, errors in form.errors.items():
            for e in errors:
                messages.error(request, f"Error en {f}: {e}")

    else:
        # GET - formulario inicial
        form = (
            UserUpdateForm(instance=user, usuario_actual=request.user)
            if editing
            else UserRegistrationForm(usuario_actual=request.user)
        )

    return render(request, "users/user_form.html", {
        "form": form,
        "editing_user": user,
        "editing": editing
    })
    
def user_updateantes(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == "POST":
        # Si solo se está actualizando la foto de perfil
        if "foto_perfil" in request.FILES and not request.POST.get('email'):
            try:
                user.foto_perfil = request.FILES['foto_perfil']
                user.save()
                messages.success(request, "Foto de perfil actualizada correctamente.")
                return redirect("user_profile", user_id=user.id)
            except Exception as e:
                messages.error(request, f"Error al actualizar la foto: {str(e)}")
                return redirect("user_profile", user_id=user.id)

        # --- Lógica del formulario general ---
        form = UserUpdateForm(request.POST, instance=user)

        #  Ajustar obligatoriedad de campos según el rol
        if user.rol != 'Profesor':
            if 'especialidad' in form.fields:
                form.fields['especialidad'].required = False
            if 'departamento' in form.fields:
                form.fields['departamento'].required = False
        if user.rol != 'Estudiante':
            if 'grado' in form.fields:
                form.fields['grado'].required = False
            if 'seccion' in form.fields:
                form.fields['seccion'].required = False

        if form.is_valid():
            try:
                # Validar correo duplicado
                email = form.cleaned_data.get('email')
                if CustomUser.objects.filter(email=email).exclude(id=user_id).exists():
                    messages.error(request, "Este correo electrónico ya está registrado.")
                    return render(request, "users/user_form.html", {"form": form, "editing_user": user})

                # Campos comunes
                user.email = form.cleaned_data.get('email')
                user.first_name = form.cleaned_data.get('first_name')
                user.last_name = form.cleaned_data.get('last_name')
                user.fecha_nacimiento = form.cleaned_data.get('fecha_nacimiento')
                user.genero = form.cleaned_data.get('genero')
                user.direccion = form.cleaned_data.get('direccion')
                user.telefono = form.cleaned_data.get('telefono')
                user.cedula = form.cleaned_data.get('cedula')
                user.rol = form.cleaned_data.get('rol')

                #  Campos según rol
                if user.rol == 'Estudiante':
                    user.grado = form.cleaned_data.get('grado')
                    user.seccion = form.cleaned_data.get('seccion')
                    user.especialidad = None
                    user.departamento = None
                elif user.rol == 'Profesor':
                    user.especialidad = form.cleaned_data.get('especialidad')
                    user.departamento = form.cleaned_data.get('departamento')
                    user.grado = None
                    user.seccion = None
                else:
                    # Otros roles (Admin, etc.)
                    user.grado = None
                    user.seccion = None
                    user.especialidad = None
                    user.departamento = None

                # Contacto de emergencia
                user.contacto_emergencia_nombre = form.cleaned_data.get('contacto_emergencia_nombre')
                user.contacto_emergencia_telefono = form.cleaned_data.get('contacto_emergencia_telefono')
                user.contacto_emergencia_parentesco = form.cleaned_data.get('contacto_emergencia_parentesco')

                # Contraseña (opcional)
                if form.cleaned_data.get('password1'):
                    user.set_password(form.cleaned_data.get('password1'))

                user.save()
                messages.success(request, "Usuario actualizado exitosamente.")
                return redirect("user_list")

            except Exception as e:
                messages.error(request, f"Error al actualizar usuario: {str(e)}")
                return render(request, "users/user_form.html", {"form": form, "editing_user": user})

        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en {field}: {error}")
    else:
        form = UserUpdateForm(instance=user)

    return render(request, "users/user_form.html", {"form": form, "editing_user": user})

@login_required
def user_delete(request, user_id):
    # Solo Administradores y Secretaria pueden eliminar usuarios
    if request.user.rol not in ['Administrador', 'Secretaria']:
        messages.error(request, 'No tienes permiso para eliminar usuarios. Solo Administradores y Secretaria pueden realizar esta acción.')
        return redirect('plataform')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Validación adicional: no permitir eliminar superusuarios o el propio usuario
    if user.is_superuser:
        messages.error(request, 'No se puede eliminar un superusuario.')
        return redirect('user_list')
    
    if user.id == request.user.id:
        messages.error(request, 'No puedes eliminarte a ti mismo.')
        return redirect('user_list')
    
    from .models import CodigoAnulacion
    
    if request.method == "POST":
        password = request.POST.get('password', '').strip()
        codigo_anulacion = request.POST.get('codigo_anulacion', '').strip()
        
        if not password or not codigo_anulacion:
            messages.error(request, 'Debe ingresar la contraseña y el código de anulación.')
            return redirect('user_list')
        
        if not check_password(password, request.user.password):
            messages.error(request, 'Contraseña incorrecta.')
            return redirect('user_list')
        
        if not CodigoAnulacion.validar_codigo(codigo_anulacion):
            messages.error(request, 'Código de anulación incorrecto.')
            return redirect('user_list')
        
        try:
            # Registrar en log de seguridad antes de eliminar
            from .models import SecurityLog
            from django.db import IntegrityError
            
            # Preparar información detallada del usuario eliminado
            usuario_eliminado_info = {
                'id': user.id,
                'nombre_completo': user.get_full_name(),
                'email': user.email,
                'rol': user.rol,
                'cedula': user.cedula if hasattr(user, 'cedula') else None,
            }
            
            # Preparar información del usuario que eliminó
            usuario_elimino_info = {
                'id': request.user.id,
                'nombre_completo': request.user.get_full_name(),
                'email': request.user.email,
                'rol': request.user.rol,
            }
            
            # Intentar eliminar el usuario
            accion_realizada = 'eliminacion_fisica'
            mensaje_accion = ''
            
            try:
                user.delete()
                mensaje_accion = f"Usuario {user.get_full_name()} eliminado exitosamente."
                accion_realizada = 'eliminacion_fisica'
                
            except IntegrityError:
                # Si tiene relaciones (facturas, matrículas, etc.), marcar como inactivo
                user.is_active = False
                user.save()
                mensaje_accion = f"Usuario {user.get_full_name()} marcado como inactivo (tiene registros relacionados: facturas, matrículas, etc.)."
                accion_realizada = 'inactivacion'
            
            # Registrar en log de seguridad
            SecurityLog.log_event(
                tipo_evento='ADMIN_ACTION',
                descripcion=f"ELIMINACIÃN DE USUARIO - Usuario: {usuario_eliminado_info['nombre_completo']} ({usuario_eliminado_info['email']}, Rol: {usuario_eliminado_info['rol']}) | AcciÃ³n: {accion_realizada.upper()} | Eliminado por: {usuario_elimino_info['nombre_completo']} ({usuario_elimino_info['email']}, Rol: {usuario_elimino_info['rol']})",
                usuario=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                nivel_severidad='WARNING',
                metadata={
                    'usuario_eliminado': usuario_eliminado_info,
                    'usuario_que_elimino': usuario_elimino_info,
                    'accion': accion_realizada,
                    'requirio_codigo_anulacion': True
                }
            )
            
            messages.success(request, mensaje_accion)
        except Exception as e:
            messages.error(request, f"Error al procesar la eliminación: {str(e)}")
        return redirect("user_list")
    
    # Si es GET, redirigir a user_list (la eliminación ahora se hace desde el modal)
    messages.info(request, 'Use el botón de eliminar desde la lista de usuarios.')
    return redirect("user_list")

@login_required
def user_reactivate(request, user_id):
    """Reactivar un usuario inactivo - Solo Administradores y Secretaria"""
    # Solo Administradores y Secretaria pueden reactivar usuarios
    if request.user.rol not in ['Administrador', 'Secretaria']:
        messages.error(request, 'No tienes permiso para reactivar usuarios.')
        return redirect('plataform')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Validación: el usuario debe estar inactivo
    if user.is_active:
        messages.warning(request, 'Este usuario ya está activo.')
        return redirect('user_list')
    
    if request.method == "POST":
        password = request.POST.get('password', '').strip()
        
        if not password:
            messages.error(request, 'Debe ingresar su contraseña.')
            return redirect('user_list')
        
        if not check_password(password, request.user.password):
            messages.error(request, 'Contraseña incorrecta.')
            return redirect('user_list')
        
        try:
            # Reactivar el usuario
            user.is_active = True
            user.save()
            
            # Registrar en log de seguridad
            from .models import SecurityLog
            
            usuario_reactivado_info = {
                'id': user.id,
                'nombre_completo': user.get_full_name(),
                'email': user.email,
                'rol': user.rol,
                'cedula': user.cedula if hasattr(user, 'cedula') else None,
            }
            
            usuario_reactivo_info = {
                'id': request.user.id,
                'nombre_completo': request.user.get_full_name(),
                'email': request.user.email,
                'rol': request.user.rol,
            }
            
            SecurityLog.log_event(
                tipo_evento='ADMIN_ACTION',
                descripcion=f"REACTIVACIÃN DE USUARIO - Usuario reactivado: {user.get_full_name()} ({user.email}, Rol: {user.rol}) | Reactivado por: {request.user.get_full_name()} ({request.user.email}, Rol: {request.user.rol})",
                usuario=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                nivel_severidad='INFO',
                metadata={
                    'usuario_reactivado': usuario_reactivado_info,
                    'usuario_que_reactivo': usuario_reactivo_info,
                    'accion': 'reactivacion_usuario'
                }
            )
            
            messages.success(request, f"Usuario {user.get_full_name()} reactivado exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al reactivar usuario: {str(e)}")
        return redirect("user_list")
    
    # Si es GET, redirigir a user_list
    messages.info(request, 'Use el botón de reactivar desde la lista de usuarios.')
    return redirect("user_list")

#_______________________ Panel de AdministraciÃ³n _________________________


#  Vista protegida con clase (para vistas basadas en clases)

class SuperUserOnlyView(UserPassesTestMixin, TemplateView):

    template_name = "admin_template.html"

    def test_func(self):

        return self.request.user.is_superuser  # Solo superusuarios

    def handle_no_permission(self):

        return custom_redirect(self.request)


#  Dashboard de administrador con estadísticas

@login_required

@user_passes_test(is_superuser)

def admin_dashboard(request):

    total_users = User.objects.count()

    active_users = User.objects.filter(is_active=True).count()

   
    context = {

        "total_users": total_users,

        "active_users": active_users,

    }

    return render(request, "admin/dashboard.html", context)


# ===========================
# CONFIGURACIÃN DE LA ESCUELA
# ===========================

@login_required
@admin_required
def configuracion_escuela(request):
    """Vista para mostrar y editar la configuración de la escuela"""
    from .models import ConfiguracionEscuela
    
    # Verificar que sea Administrador o Director
    if request.user.rol not in ['Administrador', 'Director']:
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('index')
    
    config = ConfiguracionEscuela.get_configuracion()
    
    if request.method == 'POST':
        # Actualizar campos básicos
        config.nombre_escuela = request.POST.get('nombre_escuela', '')
        config.rnc = request.POST.get('rnc', '')
        config.direccion = request.POST.get('direccion', '')
        config.telefono = request.POST.get('telefono', '')
        config.email = request.POST.get('email', '')
        config.sitio_web = request.POST.get('sitio_web', '')
        config.lema = request.POST.get('lema', '')
        config.mision = request.POST.get('mision', '')
        config.vision = request.POST.get('vision', '')
        
        # Información administrativa
        config.director_nombre = request.POST.get('director_nombre', '')
        config.codigo_centro = request.POST.get('codigo_centro', '')
        config.distrito_educativo = request.POST.get('distrito_educativo', '')
        config.regional_educativa = request.POST.get('regional_educativa', '')
        config.nivel_educativo = request.POST.get('nivel_educativo', '')
        config.modalidad = request.POST.get('modalidad', '')
        config.horario_atencion = request.POST.get('horario_atencion', '')
        
        # Año de fundaciÃ³n
        anho_fundacion = request.POST.get('anho_fundacion', '')
        if anho_fundacion:
            try:
                config.anho_fundacion = int(anho_fundacion)
            except ValueError:
                config.anho_fundacion = None
        else:
            config.anho_fundacion = None
        
        # Configuración de reportes
        config.pie_pagina_reportes = request.POST.get('pie_pagina_reportes', '')
        config.mostrar_logo_reportes = request.POST.get('mostrar_logo_reportes') == 'on'
        
        # Manejo de archivos
        if 'logo' in request.FILES:
            config.logo = request.FILES['logo']
        
        if 'director_firma' in request.FILES:
            config.director_firma = request.FILES['director_firma']
        
        # Eliminar logo si se solicita
        if request.POST.get('eliminar_logo') == 'on' and config.logo:
            config.logo.delete()
            config.logo = None
        
        # Eliminar firma si se solicita
        if request.POST.get('eliminar_firma') == 'on' and config.director_firma:
            config.director_firma.delete()
            config.director_firma = None
        
        try:
            config.save()
            messages.success(request, 'Configuración de la escuela actualizada con éxito.')
        except Exception as e:
            messages.error(request, f'Error al guardar la configuración: {str(e)}')
        
        return redirect('configuracion_escuela')
    
    context = {
        'config': config,
        'titulo': 'Configuración de la Escuela',
    }
    
    return render(request, 'est_forder/configuracion_escuela.html', context)

#________________buscar user
from django.shortcuts import render
from django.db.models import Q  # Importa Q para la búsqueda
from .models import CustomUser  # Importa el modelo correctamente

def user_list1(request):
    query = request.GET.get("q")
    users = CustomUser.objects.all()

    if query:
        users = users.filter(
            Q(id__iexact=query) |  # Buscar por ID
            Q(email__icontains=query) |  # Buscar por correo
            Q(first_name__icontains=query) |  # Buscar por nombre
            Q(last_name__icontains=query)  # Buscar por apellido
        )

    return render(request, "users/user_list.html", {"users": users})

from django.core.paginator import Paginator
from django.shortcuts import render
from .models import CustomUser

# FUNCIÃN DUPLICADA COMENTADA - La función user_list correcta está mÃ¡s arriba (lÃ­nea ~426)
# Esta versión antigua solo permitÃ­a Administrador, ahora usamos la nueva que permite Secretaria también
"""
@login_required
def user_list(request):
    # Solo administradores pueden gestionar usuarios
    if request.user.rol != 'Administrador':
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    query = request.GET.get('q', '').strip()
    per_page = int(request.GET.get('per_page', 25))
    page_number = request.GET.get('page')
    page_sizes = [25, 50, 75, 100]

    users = CustomUser.objects.all().order_by('-date_joined')
    if query:
        users = users.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(cedula__icontains=query)
        )

    # Estadísticas por rol
    cant_estudiantes = CustomUser.objects.filter(rol='Estudiante', is_active=True).count()
    cant_profesores = CustomUser.objects.filter(rol='Profesor', is_active=True).count()
    cant_directores = CustomUser.objects.filter(rol='Director', is_active=True).count()
    cant_secretarias = CustomUser.objects.filter(rol='Secretaria', is_active=True).count()
    cant_administradores = CustomUser.objects.filter(rol='Administrador', is_active=True).count()
    cant_coordinadores = CustomUser.objects.filter(rol='Coordinador', is_active=True).count()
    cant_bibliotecarios = CustomUser.objects.filter(rol='Bibliotecario', is_active=True).count()
    cant_psicologos = CustomUser.objects.filter(rol='Psicologo', is_active=True).count()
    cant_otros = CustomUser.objects.filter(rol='Otro', is_active=True).count()
    
    # Suma de todos los roles
    suma_roles = (cant_estudiantes + cant_profesores + cant_directores + 
                  cant_secretarias + cant_administradores + cant_coordinadores + 
                  cant_bibliotecarios + cant_psicologos + cant_otros)
    
    estadisticas_roles = {
        'estudiantes': cant_estudiantes,
        'profesores': cant_profesores,
        'directores': cant_directores,
        'secretarias': cant_secretarias,
        'administradores': cant_administradores,
        'coordinadores': cant_coordinadores,
        'bibliotecarios': cant_bibliotecarios,
        'psicologos': cant_psicologos,
        'otros': cant_otros,
        'suma_roles': suma_roles,
        'total_activos': CustomUser.objects.filter(is_active=True).count(),
        'total_inactivos': CustomUser.objects.filter(is_active=False).count(),
        'total_usuarios': CustomUser.objects.count(),
    }

    paginator = Paginator(users, per_page)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'users/user_list.html', {
        'users': page_obj,
        'per_page': per_page,
        'page_sizes': page_sizes,
        'query': query,
        'estadisticas': estadisticas_roles,
    })
"""

@login_required
# user profile de Escuela urls.py
def user_profile(request, user_id):
    # Solo administradores pueden ver perfiles de otros usuarios
    if request.user.rol != 'Administrador' and request.user.id != user_id:
        messages.error(request, 'No tienes permiso para ver este perfil.')
        return redirect('plataform')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Si es Administrador, agregar código de anulación
    context = {"user": user}
    if user.rol == 'Administrador':
        from .models import CodigoAnulacion
        context['codigo_anulacion'] = CodigoAnulacion.obtener_codigo_actual()
    
    return render(request, "users/profile.html", context)

#_______________________

@login_required
@user_passes_test(is_superuser)
def get_users_data(request):
    today = datetime.today()
    labels = []
    data = []

    for i in range(6):  # Ãltimos 6 meses
        month = today - timedelta(days=i * 30)
        month_label = month.strftime("%Y-%m")
        user_count = User.objects.filter(
            date_joined__year=month.year, date_joined__month=month.month

        ).count()

        labels.append(month_label)
        data.append(user_count)
    return JsonResponse({"labels": labels[::-1], "data": data[::-1]})

#______________________________Persona_______________________________________
# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Persona
from .forms import PersonaForm


from django.contrib.auth.decorators import login_required
from .models import CustomUser, Persona
from .forms import PersonaForm

@login_required
def persona_create(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Verificar si ya existe una persona asociada a este usuario
    if hasattr(user, 'persona'):
        messages.info(request, "Este usuario ya tiene una persona asociada.")
        return redirect('persona_update', persona_id=user.persona.id)

    if request.method == "POST":
        form = PersonaForm(request.POST)
        if form.is_valid():
            try:
                # Verificar campos Ãºnicos
                correo = form.cleaned_data.get('correo')
                cedula = form.cleaned_data.get('cedula')
                rne = form.cleaned_data.get('rne')

                if Persona.objects.filter(correo=correo).exists():
                    messages.error(request, "Este correo ya está registrado.")
                    return render(request, "persona/persona_form.html", {"form": form, "user": user})

                if cedula and Persona.objects.filter(cedula=cedula).exists():
                    messages.error(request, "Esta cÃ©dula ya está registrada.")
                    return render(request, "persona/persona_form.html", {"form": form, "user": user})

                if rne and Persona.objects.filter(rne=rne).exists():
                    messages.error(request, "Este RNE ya está registrado.")
                    return render(request, "persona/persona_form.html", {"form": form, "user": user})

                # Crear o actualizar tutores
                padre_data = {
                    'nombre': request.POST.get('padre_nombre'),
                    'apellido': request.POST.get('padre_apellido'),
                    'telefono': request.POST.get('padre_telefono'),
                    'parentesco': 'Padre',
                    'direccion': request.POST.get('padre_direccion')
                }

                madre_data = {
                    'nombre': request.POST.get('madre_nombre'),
                    'apellido': request.POST.get('madre_apellido'),
                    'telefono': request.POST.get('madre_telefono'),
                    'parentesco': 'Madre',
                    'direccion': request.POST.get('madre_direccion')
                }

                tutor_data = {
                    'nombre': request.POST.get('tutor_nombre'),
                    'apellido': request.POST.get('tutor_apellido'),
                    'telefono': request.POST.get('tutor_telefono'),
                    'parentesco': 'Tutor',
                    'direccion': request.POST.get('tutor_direccion')
                }

                contacto_data = {
                    'nombre': request.POST.get('contacto_nombre'),
                    'apellido': request.POST.get('contacto_apellido'),
                    'telefono': request.POST.get('contacto_telefono'),
                    'parentesco': 'Otro',
                    'direccion': request.POST.get('contacto_direccion')
                }

                # Guardar tutores
                padre = Tutor.objects.create(**padre_data) if any(padre_data.values()) else None
                madre = Tutor.objects.create(**madre_data) if any(madre_data.values()) else None
                tutor = Tutor.objects.create(**tutor_data) if any(tutor_data.values()) else None
                contacto = Tutor.objects.create(**contacto_data) if any(contacto_data.values()) else None

                # Guardar persona
                persona = form.save(commit=False)
                persona.user = user
                persona.padre = padre
                persona.madre = madre
                persona.tutor = tutor
                persona.contacto_emergencia = contacto
                persona.save()

                messages.success(request, "Persona creada exitosamente.")
                return redirect("persona_list")

            except Exception as e:
                messages.error(request, f"Error al crear persona: {str(e)}")
                return render(request, "persona/persona_form.html", {"form": form, "user": user})
    else:
        form = PersonaForm()

    return render(request, "persona/persona_form.html", {"form": form, "user": user})

from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Persona

@login_required
def persona_list(request):
    personas = Persona.objects.all().order_by("id")  # Obtener todas las personas ordenadas por ID

    # Obtener el número de elementos por página desde la URL (default: 50)
    items_per_page = request.GET.get("items", 50)

    paginator = Paginator(personas, items_per_page)  # Configurar paginaciÃ³n
    page_number = request.GET.get("page")  # Obtener número de página desde la URL
    page_obj = paginator.get_page(page_number)  # Obtener la página actual

    return render(request, "persona/persona_list.html", {"page_obj": page_obj})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import CustomUser
from .forms import UserUpdateForm  # ¨ AsegÃºrate de importar correctamente el formulario

def is_superuser(user):
    return user.is_superuser

@login_required
def persona_delete(request, pk):
    persona = get_object_or_404(Persona, pk=pk)
    if request.method == "POST":
        persona.delete()
        return redirect("persona_list")
    return render(request, "persona/delete.html", {"persona": persona})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Persona
from .forms import PersonaForm

@login_required
def persona_update(request, persona_id):
    persona = get_object_or_404(Persona, id=persona_id)  # Obtener la persona por ID

    if request.method == "POST":
        form = PersonaForm(request.POST, instance=persona)
        if form.is_valid():
            form.save()
            return redirect("persona_list")  # Redirigir a la lista después de editar
    else:
        form = PersonaForm(instance=persona)  # Al cargar la página, pre-poblar con los datos existentes

    return render(request, "persona/persona_form.html", {"form": form, "persona": persona})

#____________________________________________________________________________

import uuid
import logging
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from .models import CustomUser

logger = logging.getLogger(__name__)

def register_user(request):
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            fecha_nacimiento = request.POST.get('fecha_nacimiento')
            genero = request.POST.get('genero')
            direccion = request.POST.get('direccion')
            telefono = request.POST.get('telefono')
            cedula = request.POST.get('cedula')
            rol = request.POST.get('rol')

            # Campos especÃ­ficos por rol
            grado = request.POST.get('grado')
            seccion = request.POST.get('seccion')
            especialidad = request.POST.get('especialidad')
            departamento = request.POST.get('departamento')
            cargo = request.POST.get('cargo')

            # Información de contacto de emergencia
            contacto_emergencia_nombre = request.POST.get('contacto_emergencia_nombre')
            contacto_emergencia_telefono = request.POST.get('contacto_emergencia_telefono')
            contacto_emergencia_parentesco = request.POST.get('contacto_emergencia_parentesco')

            # Crear usuario inactivo con token
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                fecha_nacimiento=fecha_nacimiento,
                genero=genero,
                direccion=direccion,
                telefono=telefono,
                cedula=cedula,
                rol=rol,
                grado=grado,
                seccion=seccion,
                especialidad=especialidad,
                departamento=departamento,
                cargo=cargo,
                contacto_emergencia_nombre=contacto_emergencia_nombre,
                contacto_emergencia_telefono=contacto_emergencia_telefono,
                contacto_emergencia_parentesco=contacto_emergencia_parentesco,
                is_active=False
            )

            #  Generar token de activación
            user.activation_token = uuid.uuid4()
            user.save()

            # ✓ Generar UID codificado
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # ✓ Construir URL con uid y token
            current_site = get_current_site(request)
            activation_url = f"{request.scheme}://{current_site.domain}/activate/{uid}/{user.activation_token}/"

            # Log para depuraciÃ³n
            logger.warning(f"DEBUG Activation URL: {activation_url}")

            #  Construir mensaje
            html_message = render_to_string('emails/activation_email.html', {
                'user': user,
                'activation_url': activation_url,
            })
            plain_message = strip_tags(html_message)

            # ✓ Enviar correo HTML
            email_message = EmailMessage(
                'Activa tu cuenta',
                html_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
            email_message.content_subtype = "html"
            email_message.send()

            messages.success(
                request,
                'Usuario registrado exitosamente. Por favor, revisa tu correo para activar tu cuenta.'
            )
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Error al registrar usuario: {str(e)}')
            logger.error(f"Error en registro: {e}")
            return redirect('register')

    return render(request, 'registration/register.html')


@login_required
# urls de escuelaweb/urls.py
@login_required
def update_profile_picture(request):
    if request.method == 'POST':
        form = ProfilePictureUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            if 'foto_perfil' in request.FILES:
                # Obtener el ID del usuario de la URL
                user_id = request.GET.get('user_id')
                if user_id:
                    user = get_object_or_404(CustomUser, id=user_id)
                    # Solo administradores pueden cambiar foto de otros usuarios
                    if request.user.rol != 'Administrador' and user.id != request.user.id:
                        messages.error(request, 'No tienes permiso para cambiar la foto de otro usuario.')
                        return redirect('plataform')
                else:
                    user = request.user

                user.foto_perfil = request.FILES['foto_perfil']
                user.save()
                messages.success(request, 'Foto de perfil actualizada exitosamente')

                # Redirigir a la lista de usuarios si es administrador, sino al perfil
                if request.user.rol == 'Administrador' and user.id != request.user.id:
                    return redirect('user_list')
                else:
                    return redirect('user_profile', user_id=user.id)
            else:
                messages.error(request, 'No se ha seleccionado ninguna imagen')
        else:
            messages.error(request, 'Error al actualizar la foto de perfil')
    else:
        form = ProfilePictureUpdateForm()

    return render(request, 'website/update_profile_picture.html', {
        'form': form,
        'user': request.user
    })

@login_required
def lista_anhos_escolares(request):
    anhos = AnhoEscolar.objects.all()
    return render(request, 'est_forder/anhos_escolares.html', {'anhos': anhos})

@admin_required
def agregar_anho_escolar(request):
    if request.method == 'POST':
        form = AnhoEscolarForm(request.POST)
        if form.is_valid():
            anho = form.save()
            messages.success(request, 'Año escolar agregado exitosamente.')
            return redirect('lista_anhos_escolares')
    else:
        form = AnhoEscolarForm()
    return render(request, 'est_forder/form_anho_escolar.html', {
        'form': form,
        'titulo': 'Agregar Año Escolar'
    })

@admin_required
def editar_anho_escolar(request, pk):
    anho_escolar = get_object_or_404(AnhoEscolar, pk=pk)
    if request.method == 'POST':
        form = AnhoEscolarForm(request.POST, instance=anho_escolar)
        if form.is_valid():
            form.save()
            messages.success(request, 'Año escolar actualizado exitosamente.')
            return redirect('lista_anhos_escolares')
    else:
        form = AnhoEscolarForm(instance=anho_escolar)
    return render(request, 'est_forder/form_anho_escolar.html', {
        'form': form,
        'titulo': 'Editar Año Escolar'
    })

@admin_required
def eliminar_anho_escolar(request, pk):
    anho = get_object_or_404(AnhoEscolar, pk=pk)

    # Solo admin/director/superuser
    if not (request.user.is_superuser or getattr(request.user, 'rol', None) in ['Administrador', 'Director']):
        messages.error(request, 'Solo administradores y directores pueden eliminar años escolares.')
        return redirect('lista_anhos_escolares')

    from .models import CodigoAnulacion
    if request.method == 'POST':
        password = request.POST.get('password', '').strip()
        codigo_anulacion = request.POST.get('codigo_anulacion', '').strip()
        if not password or not codigo_anulacion:
            messages.error(request, 'Debe ingresar la contraseña y el código de anulación.')
            return redirect('confirmar_eliminar_anho', pk=pk)

        if not check_password(password, request.user.password):
            messages.error(request, 'Contraseña incorrecta.')
            return redirect('confirmar_eliminar_anho', pk=pk)

        if not CodigoAnulacion.validar_codigo(codigo_anulacion):
            messages.error(request, 'Código de anulación incorrecto.')
            return redirect('confirmar_eliminar_anho', pk=pk)

        try:
            anho.delete()
            messages.success(request, 'Año escolar eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el año escolar: {str(e)}')
        return redirect('lista_anhos_escolares')

    return render(request, 'est_forder/confirmar_eliminar_anho.html', {'anho': anho})

# Vistas para Cursos
@login_required
def lista_cursosAntigua(request):
    anho_id = request.GET.get('anho')

    if request.user.rol == 'Administrador':
        # Administradores ven todos los cursos
        if anho_id:
            cursos = Curso.objects.filter(anho_escolar_id=anho_id).select_related('anho_escolar', 'profesor')
            anho = get_object_or_404(AnhoEscolar, id=anho_id)
            titulo = f"Cursos del año escolar: {anho.nombre}"
        else:
            cursos = Curso.objects.all().select_related('anho_escolar', 'profesor')
            titulo = "Lista de Cursos"

    elif request.user.rol == 'Profesor':
        # Profesores ven solo los cursos donde tienen materias asignadas
        if anho_id:
            cursos = Curso.objects.filter(
                anho_escolar_id=anho_id,
                materias__profesor=request.user
            ).distinct().select_related('anho_escolar', 'profesor')
            anho = get_object_or_404(AnhoEscolar, id=anho_id)
            titulo = f"Mis Cursos - {anho.nombre}"
        else:
            # Agrupar cursos por año escolar
            anhos_escolares = AnhoEscolar.objects.filter(
                cursos__materias__profesor=request.user
            ).distinct().order_by('-nombre')

            cursos_por_anho = {}
            for anho in anhos_escolares:
                cursos_por_anho[anho] = Curso.objects.filter(
                    anho_escolar=anho,
                    materias__profesor=request.user
                ).distinct().select_related('anho_escolar', 'profesor')

            return render(request, 'est_forder/cursos_estudiante.html', {
                'cursos_por_anho': cursos_por_anho,
                'titulo': "Mis Cursos"
            })

    else:  # Estudiante
        # Estudiantes ven solo los cursos en los que están matriculados
        if anho_id:
            cursos = Curso.objects.filter(
                anho_escolar_id=anho_id,
                materias__matriculas__estudiante=request.user
            ).distinct().select_related('anho_escolar', 'profesor')
            anho = get_object_or_404(AnhoEscolar, id=anho_id)
            titulo = f"Mis Cursos - {anho.nombre}"
        else:
            # Agrupar cursos por año escolar
            anhos_escolares = AnhoEscolar.objects.filter(
                cursos__materias__matriculas__estudiante=request.user
            ).distinct().order_by('-nombre')

            cursos_por_anho = {}
            for anho in anhos_escolares:
                cursos_por_anho[anho] = Curso.objects.filter(
                    anho_escolar=anho,
                    materias__matriculas__estudiante=request.user
                ).distinct().select_related('anho_escolar', 'profesor')

            return render(request, 'est_forder/cursos_estudiante.html', {
                'cursos_por_anho': cursos_por_anho,
                'titulo': "Mis Cursos"
            })

    return render(request, 'est_forder/cursos.html', {
        'cursos': cursos,
        'titulo': titulo
    })

@login_required
def lista_cursos(request):
    anho_id = request.GET.get('anho')
    q = request.GET.get('q', '').strip()
    anho = None
    
    # Valores usados para parsear nombre de curso en grado + sección
    grados_list = [
        'Primero grado (1er Nivel Primario)',
        'Segundo grado (1er Nivel Primario)',
        'Tercero grado (1er Nivel Primario)',
        'Cuarto grado (2do. Nivel Medio)',
        'Quinto grado (2do. Nivel Medio)',
        'Sexto grado (2do. Nivel Medio)',
        'Primero de Secundaria (1er Nivel Secundario)',
        'Segundo de Secundaria (2do Nivel Secundario)',
        'Tercero de Secundaria (3er Nivel Secundario)',
        'Cuarto de Secundaria (4to Nivel Secundario)',
        'Quinto de Secundaria (5to Nivel Secundario)',
        'Sexto de Secundaria (6to Nivel Secundario)',
        '4to de InformÃ¡tica (Nivel Medio)',
        '5to de InformÃ¡tica (Nivel Medio)',
        '6to de InformÃ¡tica (Nivel Medio)',
        'Otros'
    ]
    secciones_list = ['A', 'B', 'C', 'D', 'E','F','G','H','I','J']
    
    # Administrador, Director y Coordinador ven todo
    if request.user.rol in ['Administrador', 'Director', 'Coordinador']:
        if anho_id:
            anho = get_object_or_404(AnhoEscolar, id=anho_id)
            cursos = Curso.objects.filter(
                anho_escolar=anho
            ).select_related('anho_escolar', 'profesor')
            titulo = f"Cursos del año escolar: {anho.nombre}"
        else:
            cursos = Curso.objects.all().select_related('anho_escolar', 'profesor')
            titulo = "Lista de Cursos"

        # Búsqueda por nombre, descripción o profesor
        if q:
            from django.db.models import Q
            cursos = cursos.filter(
                Q(nombre__icontains=q) |
                Q(descripcion__icontains=q) |
                Q(profesor__first_name__icontains=q) |
                Q(profesor__last_name__icontains=q)
            )

        # Anotar cada curso con grade/section parsed para la plantilla
        for c in cursos:
            nombre = c.nombre or ''
            parsed_grade = None
            parsed_section = 'AUTO'
            for g in grados_list:
                if nombre.startswith(g):
                    parsed_grade = g
                    tail = nombre[len(g):].strip()
                    if tail:
                        first = tail.split()[0]
                        if len(first) == 1 and first.isalpha():
                            parsed_section = first.upper()
                        else:
                            parsed_section = 'AUTO'
                    break
            if not parsed_grade:
                parsed_grade = 'Otros'
                parsed_section = ''
            c.parsed_grade = parsed_grade
            c.parsed_section = parsed_section

        cursos_con_profesor = sum(1 for c in cursos if c.profesor)
        return render(request, 'est_forder/cursos.html', {
            'cursos': cursos,
            'titulo': titulo,
            'anho': anho,
            'anho_id': anho_id,
            'cursos_con_profesor': cursos_con_profesor,
            'q': q,
        })




    # Profesor
    elif request.user.rol == 'Profesor':
        if anho_id:
            anho = get_object_or_404(AnhoEscolar, id=anho_id)
            cursos = Curso.objects.filter(
                anho_escolar=anho,
                materias__profesor=request.user
            ).distinct().select_related('anho_escolar', 'profesor')
            titulo = f"Mis Cursos - {anho.nombre}"

            for c in cursos:
                nombre = c.nombre or ''
                parsed_grade = None
                parsed_section = 'AUTO'
                for g in grados_list:
                    if nombre.startswith(g):
                        parsed_grade = g
                        tail = nombre[len(g):].strip()
                        if tail:
                            first = tail.split()[0]
                            if len(first) == 1 and first.isalpha():
                                parsed_section = first.upper()
                            else:
                                parsed_section = 'AUTO'
                        break
                if not parsed_grade:
                    parsed_grade = 'Otros'
                    parsed_section = ''
                c.parsed_grade = parsed_grade
                c.parsed_section = parsed_section

            # Búsqueda para Profesor
            if q:
                from django.db.models import Q
                cursos = cursos.filter(
                    Q(nombre__icontains=q) |
                    Q(descripcion__icontains=q)
                )
            cursos_con_profesor = sum(1 for c in cursos if c.profesor)
            return render(request, 'est_forder/cursos.html', {
                'cursos': cursos,
                'titulo': titulo,
                'anho': anho,
                'anho_id': anho_id,
                'cursos_con_profesor': cursos_con_profesor,
                'q': q,
            })
        else:
            cursos_por_anho = {}
            anhos = AnhoEscolar.objects.filter(
                cursos__materias__profesor=request.user
            ).distinct()
            for a in anhos:
                cursos_por_anho[a] = Curso.objects.filter(
                    anho_escolar=a,
                    materias__profesor=request.user
                ).distinct()

            return render(request, 'est_forder/cursos_estudiante.html', {
                'cursos_por_anho': cursos_por_anho,
                'titulo': "Mis Cursos"
            })

    # Estudiante
    else:
        if anho_id:
            anho = get_object_or_404(AnhoEscolar, id=anho_id)
            cursos = Curso.objects.filter(
                anho_escolar=anho,
                materias__estudiantes=request.user
            ).distinct().select_related('anho_escolar', 'profesor')
            titulo = f"Mis Cursos - {anho.nombre}"

            for c in cursos:
                nombre = c.nombre or ''
                parsed_grade = None
                parsed_section = 'AUTO'
                for g in grados_list:
                    if nombre.startswith(g):
                        parsed_grade = g
                        tail = nombre[len(g):].strip()
                        if tail:
                            first = tail.split()[0]
                            if len(first) == 1 and first.isalpha():
                                parsed_section = first.upper()
                            else:
                                parsed_section = 'AUTO'
                        break
                if not parsed_grade:
                    parsed_grade = 'Otros'
                    parsed_section = ''
                c.parsed_grade = parsed_grade
                c.parsed_section = parsed_section

            # Búsqueda para Estudiante
            if q:
                from django.db.models import Q
                cursos = cursos.filter(
                    Q(nombre__icontains=q) |
                    Q(descripcion__icontains=q)
                )
            cursos_con_profesor = sum(1 for c in cursos if c.profesor)
            return render(request, 'est_forder/cursos.html', {
                'cursos': cursos,
                'titulo': titulo,
                'anho': anho,
                'anho_id': anho_id,
                'cursos_con_profesor': cursos_con_profesor,
                'q': q,
            })

        else:
            cursos_por_anho = {}
            anhos = AnhoEscolar.objects.filter(
                cursos__materias__estudiantes=request.user
            ).distinct()
            for a in anhos:
                cursos_por_anho[a] = Curso.objects.filter(
                    anho_escolar=a,
                    materias__estudiantes=request.user
                ).distinct()

            return render(request, 'est_forder/cursos_estudiante.html', {
                'cursos_por_anho': cursos_por_anho,
                'titulo': "Mis Cursos"
            })


@admin_required
def agregar_cursoantiguo(request):
    if request.method == 'POST':
        form = CursoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso agregado exitosamente.')
            return redirect('lista_cursos')
    else:
        form = CursoForm()
    return render(request, 'est_forder/form_curso.html', {
        'form': form,
        'titulo': 'Agregar Curso'
    })


@admin_required
def inscribir_estudiante_curso(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    
    # Regular POST handling
    if request.method == 'POST':
        estudiante_id = request.POST.get('estudiante')
        if not estudiante_id:
            messages.error(request, 'Debe seleccionar un estudiante.')
            return redirect(request.path)
            
        estudiante = get_object_or_404(CustomUser, pk=estudiante_id)

        materias = Materia.objects.filter(curso=curso)
        created = 0
        for materia in materias:
            # crear matrÃ­cula si no existe
            if not Matricula.objects.filter(estudiante=estudiante, materia=materia).exists():
                Matricula.objects.create(estudiante=estudiante, materia=materia, anho_escolar=curso.anho_escolar)
                created += 1

        if created > 0:
            messages.success(request, f'Se inscribiÃ³ a {estudiante.get_full_name()} en {created} materias del curso.')
        else:
            messages.warning(request, f'{estudiante.get_full_name()} ya estaba inscrito en todas las materias del curso.')
        return redirect(f"{reverse('lista_cursos')}?anho={curso.anho_escolar.id}")

    # GET: Buscar estudiantes
    query = request.GET.get('q', '').strip()
    estudiantes = []
    total_resultados = 0
    resultados_limitados = False
    LIMITE_RESULTADOS = 50
    
    # Solo buscar si hay al menos 2 caracteres
    if query and len(query) >= 2:
        estudiantes_query = CustomUser.objects.filter(
            rol='Estudiante', 
            is_active=True
        ).filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(cedula__icontains=query) |
            Q(codigo_barras__icontains=query)
        ).order_by('first_name', 'last_name')
        
        # Contar total de resultados
        total_resultados = estudiantes_query.count()
        
        # Limitar a 50 resultados
        estudiantes = list(estudiantes_query[:LIMITE_RESULTADOS])
        
        # Verificar si hay mÃ¡s resultados
        if total_resultados > LIMITE_RESULTADOS:
            resultados_limitados = True

    return render(request, 'est_forder/inscribir_estudiante_curso.html', {
        'curso': curso,
        'estudiantes': estudiantes,
        'titulo': f'Inscribir estudiante en {curso.nombre}',
        'query': query,
        'total_estudiantes': CustomUser.objects.filter(rol='Estudiante', is_active=True).count(),
        'total_resultados': total_resultados,
        'resultados_limitados': resultados_limitados,
        'limite_resultados': LIMITE_RESULTADOS
    })
    

@admin_required
def desinscribir_estudiante_curso(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    # Listar sÃ³lo los estudiantes que están matriculados en alguna materia de este curso
    estudiantes = CustomUser.objects.filter(matriculas__materia__curso=curso).distinct().order_by('first_name', 'last_name')

    if request.method == 'POST':
        estudiante_id = request.POST.get('estudiante')
        estudiante = get_object_or_404(CustomUser, pk=estudiante_id)

        matriculas = Matricula.objects.filter(estudiante=estudiante, materia__curso=curso)
        count = matriculas.count()
        matriculas.delete()

        messages.success(request, f'Se eliminaron {count} matricula(s) del estudiante {estudiante.get_full_name()} en el curso {curso.nombre}.')
        return redirect(f"{reverse('lista_cursos')}?anho={curso.anho_escolar.id}")

    return render(request, 'est_forder/desinscribir_estudiante_curso.html', {
        'curso': curso,
        'estudiantes': estudiantes,
        'titulo': f'Desinscribir estudiante de {curso.nombre}'
    })


@login_required
def agregar_curso(request):
    # Obtener el id del año escolar desde GET
    anho_id = request.GET.get('anho')
    if not anho_id:
        messages.error(request, 'Debe seleccionar un año escolar antes de agregar un curso.')
        return redirect('lista_cursos')

    anho = get_object_or_404(AnhoEscolar, id=anho_id)
    # Lista de grados según currÃ­culum escolar dominicano (etiquetas legibles)
    grados = [
        'Primero grado (1ero Nivel Primario)',
        'Segundo grado (2do Nivel Primario)',
        'Tercero grado (3ro Nivel Primario)',
        'Cuarto grado (4to. Nivel Primario)',
        'Quinto grado (5to. Nivel Primario)',
        'Sexto grado (6to. Nivel Primario)',
        'Primero de Secundaria (7mo Nivel Basico)',
        'Segundo de Secundaria (8vo Nivel Basico)',
        'Tercero de Secundaria (1ro Nivel Medio)',
        'Cuarto de Secundaria (2do Nivel Medio)',
        'Quinto de Secundaria (3ro Nivel Medio)',
        'Sexto de Secundaria (4to Nivel Medio)',
        '4to de InformÃ¡tica (Nivel Medio)',
        '5to de InformÃ¡tica (Nivel Medio)',
        '6to de InformÃ¡tica (Nivel Medio)',
        'Otros'
    ]

    secciones = ['A', 'B', 'C', 'D', 'E','F','G','H','I','J']

    if request.method == 'POST':
        grade = request.POST.get('grade')
        section = request.POST.get('section')  # puede ser 'AUTO' o letra
        custom_name = request.POST.get('custom_name', '').strip()

        # Si el usuario proporcionÃ³ un nombre personalizado o eligiÃ³ 'Otros'
        if grade == 'Otros' or custom_name:
            nombre_final = custom_name if custom_name else 'Otros'
            descripcion = request.POST.get('descripcion', '')
            curso = Curso(nombre=nombre_final, descripcion=descripcion, anho_escolar=anho)
            try:
                curso.save()
                # No crear materias automÃ¡ticas para 'Otros' a menos que se especifique
                messages.success(request, 'Curso agregado exitosamente.')
                return redirect(f"{reverse('lista_cursos')}?anho={anho.id}")
            except Exception as e:
                messages.error(request, f'Error al guardar el curso: {e}')
                form = CursoForm(request.POST)
        else:
            # Construir nombre con grado y sección
            existing = Curso.objects.filter(nombre__startswith=grade + ' ')
            used = set()
            for c in existing:
                tail = c.nombre[len(grade):].strip()
                parts = tail.split()
                if parts:
                    last = parts[-1]
                    if len(last) == 1 and last.isalpha():
                        used.add(last.upper())

            # Determinar sección a usar
            chosen = None
            if section and section != 'AUTO':
                sec = section.upper()
                if sec in used:
                    for s in secciones:
                        if s not in used:
                            chosen = s
                            break
                else:
                    chosen = sec
            else:
                for s in secciones:
                    if s not in used:
                        chosen = s
                        break
            if not chosen:
                chosen = 'B'

            nombre_final = f"{grade} {chosen}"
            descripcion = request.POST.get('descripcion', '')
            curso = Curso(nombre=nombre_final, descripcion=descripcion, anho_escolar=anho)
            try:
                curso.save()

                # Crear materias automáticamente según tipo de grado
                from django.utils.text import slugify

                primary_subjects = [
                    'Español', 'MatemÃ¡ticas', 'Ciencias Sociales', 'Ciencias Naturales',
                    'InglÃ©s', 'EducaciÃ³n ArtÃ­stica', 'EducaciÃ³n FÃ­sica', 'TecnologÃ­a'
                ]
                secondary_subjects = [
                    'Español', 'MatemÃ¡ticas', 'InglÃ©s', 'BiologÃ­a', 'FÃ­sica', 'QuÃ­mica',
                    'Historia y GeografÃ­a', 'TecnologÃ­a e InformÃ¡tica', 'EducaciÃ³n ArtÃ­stica', 'EducaciÃ³n FÃ­sica'
                ]
                informatica_subjects_4t0 = [
                    'OfimÃ¡tica ', 'Análisis y diseÃ±o de sistemas informÃ¡ticos',
                    ':DiseÃ±o y desarrollo de base de datos.', ' DiseÃ±o de portales web y recursos multimedia'
                ]
                informatica_subjects_5t0 = [
                    ' FormaciÃ³n y OrientaciÃ³n Laboral','Desarrollo de aplicaciones y sistemas de informaciónSistemas operativos', 'Administracion de base de datoss',
                    'Analisis y diseÃ±os de reporte'
                ]
                informatica_subjects_6t0 = ['Emprendimiento','ImplementaciÃ³n y mantenimiento de aplicaciones y sistemas informÃ¡ticos',
                    'Desarrollo e implementaciÃ³n de soluciones web y multimedia'
                ]
                subjects_to_create = []
                if 'Primario' in grade or 'Primaria' in grade:
                    subjects_to_create = primary_subjects
                elif '4to de InformÃ¡tica' in grade:
                    # Para informÃ¡tica: materias de secundaria + materias especÃ­ficas de informÃ¡tica
                    subjects_to_create = secondary_subjects + informatica_subjects_4t0
                elif '5to de InformÃ¡tica' in grade:
                    subjects_to_create = secondary_subjects + informatica_subjects_5t0
                elif '6to de InformÃ¡tica' in grade:
                    subjects_to_create = secondary_subjects + informatica_subjects_6t0
                elif 'Medio' in grade or 'Basico' in grade:
                    subjects_to_create = secondary_subjects

                created = 0
                for i, sname in enumerate(subjects_to_create, start=1):
                    code = f"{slugify(sname)[:10]}-{curso.id}-{i}"
                    # Evitar duplicados
                    if not Materia.objects.filter(nombre=sname, curso=curso).exists():
                        materia = Materia(
                            nombre=sname,
                            codigo=code,
                            descripcion='',
                            creditos=1,
                            curso=curso
                        )
                        materia.save()
                        created += 1

                messages.success(request, f'Curso agregado exitosamente. Materias creadas: {created}')
                return redirect(f"{reverse('lista_cursos')}?anho={anho.id}")
            except Exception as e:
                messages.error(request, f'Error al guardar el curso: {e}')
                form = CursoForm(request.POST)
    else:
        form = CursoForm()

    return render(request, 'est_forder/form_curso.html', {
        'form': form,
        'titulo': f'Agregar Curso - Año {anho.nombre}',
        'anho': anho,
        'anho_id': anho.id,
        'grados': grados,
        'secciones': secciones,
    })




def editar_curso(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    anho = curso.anho_escolar  # <-- guardamos el año escolar
    # Mismos listados que en agregar_curso
    grados = [
        'Primero grado (1er Nivel Primario)',
        'Segundo grado (1er Nivel Primario)',
        'Tercero grado (1er Nivel Primario)',
        'Cuarto grado (2do. Nivel Medio)',
        'Quinto grado (2do. Nivel Medio)',
        'Sexto grado (2do. Nivel Medio)',
        'Primero de Secundaria (1er Nivel Secundario)',
        'Segundo de Secundaria (2do Nivel Secundario)',
        'Tercero de Secundaria (3er Nivel Secundario)',
        'Cuarto de Secundaria (4to Nivel Secundario)',
        'Quinto de Secundaria (5to Nivel Secundario)',
        'Sexto de Secundaria (6to Nivel Secundario)',
        'Otros'
    ]
    secciones = ['A', 'B', 'C', 'D', 'E','F','G','H','I','J']

    # Determinar valores iniciales para selects / nombre personalizado
    grade_selected = None
    section_selected = 'AUTO'
    custom_name = ''

    for g in grados:
        if curso.nombre.startswith(g):
            grade_selected = g
            tail = curso.nombre[len(g):].strip()
            if tail:
                first = tail.split()[0]
                if len(first) == 1 and first.isalpha():
                    section_selected = first.upper()
                else:
                    section_selected = 'AUTO'
            break

    if not grade_selected:
        # nombre no coincide con ningÃºn grado -> tratar como personalizado/Otros
        grade_selected = 'Otros'
        custom_name = curso.nombre

    if request.method == 'POST':
        form = CursoForm(request.POST, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso actualizado exitosamente.')
            return redirect(f"{reverse('lista_cursos')}?anho={anho.id}")
    else:
        form = CursoForm(instance=curso)

    return render(request, 'est_forder/form_curso.html', {
        'form': form,
        'titulo': 'Editar Curso',
        'anho': anho,
        'grados': grados,
        'secciones': secciones,
        'grade_selected': grade_selected,
        'section_selected': section_selected,
        'custom_name': custom_name,
    })

@admin_required
def eliminar_cursoAntiguo(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    if request.method == 'POST':
        password = request.POST.get('password')
        if not password:
            messages.error(request, 'Debe ingresar la contraseña de confirmación.')
            return redirect('confirmar_eliminar_curso', pk=pk)

        if not check_password(password, request.user.password):
            messages.error(request, 'Contraseña incorrecta.')
            return redirect('confirmar_eliminar_curso', pk=pk)

        try:
            curso.delete()
            messages.success(request, 'Curso eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el curso: {str(e)}')
        return redirect('lista_cursos')

    return render(request, 'est_forder/confirmar_eliminar_curso.html', {'curso': curso})

from django.urls import reverse

from django.urls import reverse

from django.urls import reverse

from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password

@admin_required
def eliminar_curso(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    # Capturar anho_id: prioridad GET, luego el del curso
    anho_id = request.GET.get('anho')
    if not anho_id and curso.anho_escolar:
        anho_id = curso.anho_escolar.id

    # Solo admin/director/superuser
    if not (request.user.is_superuser or getattr(request.user, 'rol', None) in ['Administrador', 'Director']):
        messages.error(request, 'Solo administradores y directores pueden eliminar cursos.')
        return redirect('lista_cursos')

    from .models import CodigoAnulacion
    if request.method == 'POST':
        post_anho_id = request.POST.get('anho_id')
        if post_anho_id:
            anho_id = post_anho_id

        password = request.POST.get('password', '').strip()
        codigo_anulacion = request.POST.get('codigo_anulacion', '').strip()
        if not password or not codigo_anulacion:
            messages.error(request, 'Debe ingresar la contraseña y el código de anulación.')
            if anho_id:
                return redirect(f"{reverse('confirmar_eliminar_curso', args=[pk])}?anho={anho_id}")
            return redirect('confirmar_eliminar_curso', pk=pk)

        if not check_password(password, request.user.password):
            messages.error(request, 'Contraseña incorrecta.')
            if anho_id:
                return redirect(f"{reverse('confirmar_eliminar_curso', args=[pk])}?anho={anho_id}")
            return redirect('confirmar_eliminar_curso', pk=pk)

        if not CodigoAnulacion.validar_codigo(codigo_anulacion):
            messages.error(request, 'Código de anulación incorrecto.')
            if anho_id:
                return redirect(f"{reverse('confirmar_eliminar_curso', args=[pk])}?anho={anho_id}")
            return redirect('confirmar_eliminar_curso', pk=pk)

        try:
            curso_nombre = curso.nombre
            curso.delete()
            messages.success(request, f'Curso "{curso_nombre}" eliminado exitosamente.')
            if anho_id:
                return redirect(f'{reverse("lista_cursos")}?anho={anho_id}')
            return redirect('lista_cursos')
        except Exception as e:
            messages.error(request, f'Error al eliminar el curso: {str(e)}')
            if anho_id:
                return redirect(f'{reverse("lista_cursos")}?anho={anho_id}')
            return redirect('lista_cursos')

    return render(request, 'est_forder/confirmar_eliminar_curso.html', {
        'curso': curso,
        'anho_id': anho_id
    })


# ----------------------
# StudentGroup Views
# ----------------------

@admin_required
def lista_grupos(request):
    # Obtener parámetros de búsqueda
    query_nombre = request.GET.get('nombre', '').strip()
    query_grado = request.GET.get('grado', '').strip()
    query_seccion = request.GET.get('seccion', '').strip()
    
    # Filtrar grupos
    grupos = StudentGroup.objects.select_related('creado_por').all()
    
    if query_nombre:
        grupos = grupos.filter(nombre__icontains=query_nombre)
    if query_grado:
        grupos = grupos.filter(grado__icontains=query_grado)
    if query_seccion:
        grupos = grupos.filter(seccion__icontains=query_seccion)
    
    grupos = grupos.order_by('-created_at')
    
    # Obtener valores Ãºnicos para filtros
    grados = StudentGroup.objects.values_list('grado', flat=True).distinct().order_by('grado')
    secciones = StudentGroup.objects.values_list('seccion', flat=True).distinct().order_by('seccion')
    
    anho_id = request.GET.get('anho')  # Capturar anho_id si viene en la URL
    
    return render(request, 'est_forder/grupos_list.html', {
        'grupos': grupos,
        'titulo': 'Grupos de Estudiantes',
        'anho_id': anho_id,
        'query_nombre': query_nombre,
        'query_grado': query_grado,
        'query_seccion': query_seccion,
        'grados': [g for g in grados if g],
        'secciones': [s for s in secciones if s],
    })


@admin_required
def crear_grupo(request):
    # Crear grupo por grado y seccion: toma estudiantes del sistema con esos valores
    grados = CustomUser.objects.filter(rol='Estudiante').values_list('grado', flat=True).distinct()
    secciones = CustomUser.objects.filter(rol='Estudiante').values_list('seccion', flat=True).distinct()

    # Allow pre-filling from GET params (used when creating from a course)
    initial_grade = request.GET.get('grado', '')
    initial_section = request.GET.get('seccion', '')
    initial_name = request.GET.get('nombre', '')

    if request.method == 'POST':
        nombre = request.POST.get('nombre') or ''
        grado = request.POST.get('grado')
        seccion = request.POST.get('seccion')

        if not grado or not seccion:
            messages.error(request, 'Debe seleccionar grado y sección.')
            return redirect('crear_grupo')

        grupo = StudentGroup.objects.create(nombre=nombre or f'Grupo {grado} {seccion}', grado=grado, seccion=seccion, creado_por=request.user)
        # AÃ±adir estudiantes que coincidan con grado y sección
        estudiantes = CustomUser.objects.filter(rol='Estudiante', grado=grado, seccion=seccion)
        grupo.estudiantes.set(estudiantes)
        messages.success(request, f'Grupo creado con {estudiantes.count()} estudiante(s).')
        return redirect('lista_grupos')

    return render(request, 'est_forder/grupos_form.html', {
        'titulo': 'Crear Grupo',
        'grados': sorted([g for g in grados if g]),
        'secciones': sorted([s for s in secciones if s]),
        'initial_grade': initial_grade,
        'initial_section': initial_section,
        'initial_name': initial_name,
    })


@admin_required
def crear_grupo_por_usuarios(request):
    """
    Vista para buscar `CustomUser` (estudiantes) por nombre, apellido, grado, seccion
    y crear un `StudentGroup` seleccionando manualmente usuarios.
    """
    query_nombre = request.GET.get('nombre', '').strip()
    query_apellido = request.GET.get('apellido', '').strip()
    query_grado = request.GET.get('grado', '').strip()
    query_seccion = request.GET.get('seccion', '').strip()
    query_email = request.GET.get('email', '').strip()
    query_cedula = request.GET.get('cedula', '').strip()

    estudiantes_qs = CustomUser.objects.filter(rol='Estudiante')

    if query_nombre:
        estudiantes_qs = estudiantes_qs.filter(first_name__icontains=query_nombre)
    if query_apellido:
        estudiantes_qs = estudiantes_qs.filter(last_name__icontains=query_apellido)
    if query_grado:
        estudiantes_qs = estudiantes_qs.filter(grado__icontains=query_grado)
    if query_seccion:
        estudiantes_qs = estudiantes_qs.filter(seccion__iexact=query_seccion)
    if query_email:
        estudiantes_qs = estudiantes_qs.filter(email__icontains=query_email)
    if query_cedula:
        estudiantes_qs = estudiantes_qs.filter(cedula__icontains=query_cedula)

    # PaginaciÃ³n
    try:
        per_page = int(request.GET.get('per_page', 25))
    except ValueError:
        per_page = 25

    page = request.GET.get('page', 1)
    estudiantes_ordered = estudiantes_qs.order_by('first_name', 'last_name')
    paginator = Paginator(estudiantes_ordered, per_page)
    page_obj = paginator.get_page(page)
    estudiantes = page_obj.object_list

    if request.method == 'POST':
        nombre_grupo = request.POST.get('nombre', '').strip()
        grado = request.POST.get('grado', '').strip()
        seccion = request.POST.get('seccion', '').strip()
        selected_ids = request.POST.getlist('estudiantes')

        if not selected_ids:
            messages.error(request, 'Debe seleccionar al menos un estudiante para crear el grupo.')
            return redirect('crear_grupo_por_usuarios')

        grupo = StudentGroup.objects.create(
            nombre=(nombre_grupo or (f'Grupo {grado} {seccion}' if (grado or seccion) else 'Grupo')).strip(),
            grado=grado or '',
            seccion=seccion or '',
            creado_por=request.user
        )
        estudiantes_sel = CustomUser.objects.filter(id__in=selected_ids, rol='Estudiante')
        grupo.estudiantes.set(estudiantes_sel)
        messages.success(request, f'Grupo creado con {estudiantes_sel.count()} estudiante(s).')
        return redirect('lista_grupos')

    # obtener listas Ãºnicas para filtros
    grados = CustomUser.objects.filter(rol='Estudiante').values_list('grado', flat=True).distinct()
    secciones = CustomUser.objects.filter(rol='Estudiante').values_list('seccion', flat=True).distinct()

    return render(request, 'est_forder/grupos_create_from_users.html', {
        'titulo': 'Crear Grupo por Usuarios',
        'estudiantes': estudiantes,
        'grados': sorted([g for g in grados if g]),
        'secciones': sorted([s for s in secciones if s]),
        'query_nombre': query_nombre,
        'query_apellido': query_apellido,
        'query_grado': query_grado,
        'query_seccion': query_seccion,
        'query_email': query_email,
        'query_cedula': query_cedula,
        'page_obj': page_obj,
        'per_page': per_page,
    })


@admin_required
def ver_grupo(request, pk):
    grupo = get_object_or_404(StudentGroup, pk=pk)
    anho_id = request.GET.get('anho')  # Capturar anho_id si viene en la URL
    
    # Obtener parámetros de búsqueda
    query_nombre = request.GET.get('nombre', '').strip()
    query_apellido = request.GET.get('apellido', '').strip()
    query_email = request.GET.get('email', '').strip()
    query_cedula = request.GET.get('cedula', '').strip()
    
    # Filtrar estudiantes del grupo
    estudiantes = grupo.estudiantes.all()
    
    if query_nombre:
        estudiantes = estudiantes.filter(first_name__icontains=query_nombre)
    if query_apellido:
        estudiantes = estudiantes.filter(last_name__icontains=query_apellido)
    if query_email:
        estudiantes = estudiantes.filter(email__icontains=query_email)
    if query_cedula:
        estudiantes = estudiantes.filter(cedula__icontains=query_cedula)
    
    # Ordenar alfabÃ©ticamente por nombre
    estudiantes_ordenados = estudiantes.order_by('first_name', 'last_name')
    
    return render(request, 'est_forder/grupos_detail.html', {
        'grupo': grupo,
        'estudiantes': estudiantes_ordenados,
        'titulo': grupo.nombre,
        'anho_id': anho_id,
        'query_nombre': query_nombre,
        'query_apellido': query_apellido,
        'query_email': query_email,
        'query_cedula': query_cedula,
    })


@admin_required
def agregar_estudiantes_grupo(request, pk):
    grupo = get_object_or_404(StudentGroup, pk=pk)
    
    query_nombre = request.GET.get('nombre', '').strip()
    query_apellido = request.GET.get('apellido', '').strip()
    query_grado = request.GET.get('grado', '').strip()
    query_seccion = request.GET.get('seccion', '').strip()
    query_email = request.GET.get('email', '').strip()
    query_cedula = request.GET.get('cedula', '').strip()

    # Excluir estudiantes ya en el grupo
    estudiantes_qs = CustomUser.objects.filter(rol='Estudiante').exclude(id__in=grupo.estudiantes.all())

    if query_nombre:
        estudiantes_qs = estudiantes_qs.filter(first_name__icontains=query_nombre)
    if query_apellido:
        estudiantes_qs = estudiantes_qs.filter(last_name__icontains=query_apellido)
    if query_grado:
        estudiantes_qs = estudiantes_qs.filter(grado__icontains=query_grado)
    if query_seccion:
        estudiantes_qs = estudiantes_qs.filter(seccion__iexact=query_seccion)
    if query_email:
        estudiantes_qs = estudiantes_qs.filter(email__icontains=query_email)
    if query_cedula:
        estudiantes_qs = estudiantes_qs.filter(cedula__icontains=query_cedula)

    try:
        per_page = int(request.GET.get('per_page', 25))
    except ValueError:
        per_page = 25

    page = request.GET.get('page', 1)
    estudiantes_ordered = estudiantes_qs.order_by('first_name', 'last_name')
    paginator = Paginator(estudiantes_ordered, per_page)
    page_obj = paginator.get_page(page)
    estudiantes = page_obj.object_list

    if request.method == 'POST':
        selected_ids = request.POST.getlist('estudiantes')
        if not selected_ids:
            messages.error(request, 'Debe seleccionar al menos un estudiante para agregar al grupo.')
            return redirect('agregar_estudiantes_grupo', pk=pk)

        estudiantes_sel = CustomUser.objects.filter(id__in=selected_ids, rol='Estudiante')
        grupo.estudiantes.add(*estudiantes_sel)
        messages.success(request, f'{estudiantes_sel.count()} estudiante(s) agregado(s) al grupo.')
        return redirect('ver_grupo', pk=pk)

    grados = CustomUser.objects.filter(rol='Estudiante').values_list('grado', flat=True).distinct()
    secciones = CustomUser.objects.filter(rol='Estudiante').values_list('seccion', flat=True).distinct()

    return render(request, 'est_forder/grupos_agregar_estudiantes.html', {
        'titulo': f'Agregar estudiantes a {grupo.nombre}',
        'grupo': grupo,
        'estudiantes': estudiantes,
        'grados': sorted([g for g in grados if g]),
        'secciones': sorted([s for s in secciones if s]),
        'query_nombre': query_nombre,
        'query_apellido': query_apellido,
        'query_grado': query_grado,
        'query_seccion': query_seccion,
        'query_email': query_email,
        'query_cedula': query_cedula,
        'page_obj': page_obj,
        'per_page': per_page,
    })


@admin_required
def inscribir_grupo_en_curso(request, pk):
    grupo = get_object_or_404(StudentGroup, pk=pk)
    # Capturar anho_id desde la URL
    anho_id = request.GET.get('anho')
    
    # Seleccionar curso destino por query param o mostrar selector
    if request.method == 'POST':
        curso_id = request.POST.get('curso')
        curso = get_object_or_404(Curso, pk=curso_id)
        created = 0
        materias = Materia.objects.filter(curso=curso)
        for estudiante in grupo.estudiantes.all():
            for materia in materias:
                if not Matricula.objects.filter(estudiante=estudiante, materia=materia).exists():
                    Matricula.objects.create(estudiante=estudiante, materia=materia, anho_escolar=curso.anho_escolar)
                    created += 1
        messages.success(request, f'Se inscribieron {created} matrículas para el grupo en {curso.nombre}.')
        
        # Redirigir a ver_grupo manteniendo el anho_id
        if anho_id:
            return redirect(f"{reverse('ver_grupo', args=[grupo.pk])}?anho={anho_id}")
        else:
            return redirect('ver_grupo', pk=grupo.pk)

    # Obtener anho_id - PRIORIZAR el que viene en la URL
    anho_id = request.GET.get('anho')
    
    if anho_id:
        # Si hay anho_id en la URL, usarlo directamente
        cursos = Curso.objects.filter(anho_escolar_id=anho_id).order_by('nombre')
        anho = get_object_or_404(AnhoEscolar, id=anho_id)
    else:
        # Si no hay anho_id, obtener el año escolar mÃ¡s reciente
        anho_reciente = AnhoEscolar.objects.order_by('-nombre').first()
        if anho_reciente:
            cursos = Curso.objects.filter(anho_escolar=anho_reciente).order_by('nombre')
            anho = anho_reciente
            anho_id = anho_reciente.id
        else:
            cursos = Curso.objects.all().order_by('-anho_escolar__nombre', 'nombre')
            anho = None
    
    # Obtener todos los años escolares para el selector
    anhos_escolares = AnhoEscolar.objects.all().order_by('-nombre')
    
    return render(request, 'est_forder/grupos_inscribir.html', {
        'grupo': grupo,
        'cursos': cursos,
        'anhos_escolares': anhos_escolares,
        'anho_seleccionado': anho,
        'anho_id': anho_id,
        'titulo': f'Inscribir grupo {grupo.nombre} en curso'
    })


@admin_required
def eliminar_grupo(request, pk):
    grupo = get_object_or_404(StudentGroup, pk=pk)
    
    if request.method == 'POST':
        password = request.POST.get('password')
        if not password:
            messages.error(request, 'Debe ingresar la contraseña de confirmación.')
            return redirect('confirmar_eliminar_grupo', pk=pk)

        if not check_password(password, request.user.password):
            messages.error(request, 'Contraseña incorrecta.')
            return redirect('confirmar_eliminar_grupo', pk=pk)

        try:
            grupo.delete()
            messages.success(request, 'Grupo eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el grupo: {str(e)}')
        return redirect('lista_grupos')

    return render(request, 'est_forder/grupos_confirmar_eliminar.html', {'grupo': grupo})


# Vistas para Materias
@login_required
def lista_materiasFUNCIONALANTIGUA(request):
    curso_id = request.GET.get('curso')

    if request.user.rol == 'Administrador':
        # Administradores ven todas las materias
        if curso_id:
            materias = Materia.objects.filter(curso_id=curso_id).select_related('curso', 'profesor')
            curso = get_object_or_404(Curso, id=curso_id)
            titulo = f"Materias del curso: {curso.nombre}"
            anho = curso.anho_escolar  # <--- agregamos esto
        else:
            materias = Materia.objects.all().select_related('curso', 'profesor')
            titulo = "Lista de Materias"

    elif request.user.rol == 'Profesor':
        # Profesores ven solo las materias que imparten
        if curso_id:
            materias = Materia.objects.filter(
                curso_id=curso_id,
                profesor=request.user
            ).select_related('curso', 'profesor')
            curso = get_object_or_404(Curso, id=curso_id)
            titulo = f"Mis Materias - {curso.nombre}"
        else:
            materias = Materia.objects.filter(
                profesor=request.user
            ).select_related('curso', 'profesor')
            titulo = "Mis Materias"

    else:  # Estudiante
        # Estudiantes ven solo las materias en las que están matriculados
        if curso_id:
            curso = get_object_or_404(Curso, id=curso_id)
            materias = Materia.objects.filter(
                curso=curso,
                matriculas__estudiante=request.user
            ).distinct().select_related('curso', 'profesor')
            titulo = f"Materias de {curso.nombre} - {curso.anho_escolar.nombre}"
        else:
            # Agrupar materias por curso y año escolar
            cursos = Curso.objects.filter(
                materias__matriculas__estudiante=request.user
            ).distinct().select_related('anho_escolar')

            materias_por_curso = {}
            for curso in cursos:
                materias_por_curso[curso] = Materia.objects.filter(
                    curso=curso,
                    matriculas__estudiante=request.user
                ).distinct().select_related('profesor')

            return render(request, 'est_forder/materias_estudiante.html', {
                'materias_por_curso': materias_por_curso,
                'titulo': "Mis Materias",
                'curso_id': curso_id  # Agregar curso_id al contexto
            })

    # Agregar información de matrÃ­cula para estudiantes
    if request.user.rol == 'Estudiante':
        for materia in materias:
            matricula = Matricula.objects.filter(
                materia=materia,
                estudiante=request.user
            ).first()
            materia.matricula = matricula

    return render(request, 'est_forder/materias.html', {
        'materias': materias,
        'titulo': titulo,
        'curso_id': curso_id  # Asegurar que curso_id estÃ© en el contexto
    })

@login_required
def lista_materias(request):
    curso_id = request.GET.get('curso')
    q = request.GET.get('q', '').strip()
    curso = get_object_or_404(Curso, id=curso_id)
    materias = Materia.objects.filter(curso_id=curso_id)
    anho = None

    # Administrador, Director y Coordinador ven todo
    if request.user.rol in ['Administrador', 'Director', 'Coordinador']:
        if curso_id:
            curso = get_object_or_404(Curso, id=curso_id)
            materias = Materia.objects.filter(curso=curso).select_related('curso', 'profesor')
            titulo = f"Materias del curso: {curso.nombre}"
            anho = curso.anho_escolar
        else:
            materias = Materia.objects.all().select_related('curso', 'profesor')
            titulo = "Lista de Materias"

    elif request.user.rol == 'Profesor':
        if curso_id:
            curso = get_object_or_404(Curso, id=curso_id)
            materias = Materia.objects.filter(curso=curso, profesor=request.user).select_related('curso', 'profesor')
            titulo = f"Mis Materias - {curso.nombre}"
            anho = curso.anho_escolar
        else:
            materias = Materia.objects.filter(profesor=request.user).select_related('curso', 'profesor')
            titulo = "Mis Materias"

    else:  # Estudiante
        if curso_id:
            curso = get_object_or_404(Curso, id=curso_id)
            materias = Materia.objects.filter(curso=curso, matriculas__estudiante=request.user).distinct().select_related('profesor')
            titulo = f"Materias de {curso.nombre} - {curso.anho_escolar.nombre}"
            anho = curso.anho_escolar
        else:
            cursos = Curso.objects.filter(materias__matriculas__estudiante=request.user).distinct().select_related('anho_escolar')
            materias_por_curso = {}
            for curso in cursos:
                materias_curso = Materia.objects.filter(curso=curso, matriculas__estudiante=request.user).distinct().select_related('profesor')
                # Preparar info de matrÃ­cula y recuperaciones para cada materia
                for materia in materias_curso:
                    matricula = Matricula.objects.filter(materia=materia, estudiante=request.user).first()
                    if matricula:
                        # Preparar información de recuperaciones para el template
                        matricula.mostrar_com_rp1 = matricula.com_p1 is not None and matricula.com_p1 < 70 and matricula.com_rp1 is not None
                        matricula.mostrar_com_rp2 = matricula.com_p2 is not None and matricula.com_p2 < 70 and matricula.com_rp2 is not None
                        matricula.mostrar_com_rp3 = matricula.com_p3 is not None and matricula.com_p3 < 70 and matricula.com_rp3 is not None
                        matricula.mostrar_com_rp4 = matricula.com_p4 is not None and matricula.com_p4 < 70 and matricula.com_rp4 is not None
                        
                        matricula.mostrar_log_rp1 = matricula.log_p1 is not None and matricula.log_p1 < 70 and matricula.log_rp1 is not None
                        matricula.mostrar_log_rp2 = matricula.log_p2 is not None and matricula.log_p2 < 70 and matricula.log_rp2 is not None
                        matricula.mostrar_log_rp3 = matricula.log_p3 is not None and matricula.log_p3 < 70 and matricula.log_rp3 is not None
                        matricula.mostrar_log_rp4 = matricula.log_p4 is not None and matricula.log_p4 < 70 and matricula.log_rp4 is not None
                        
                        matricula.mostrar_cie_rp1 = matricula.cie_p1 is not None and matricula.cie_p1 < 70 and matricula.cie_rp1 is not None
                        matricula.mostrar_cie_rp2 = matricula.cie_p2 is not None and matricula.cie_p2 < 70 and matricula.cie_rp2 is not None
                        matricula.mostrar_cie_rp3 = matricula.cie_p3 is not None and matricula.cie_p3 < 70 and matricula.cie_rp3 is not None
                        matricula.mostrar_cie_rp4 = matricula.cie_p4 is not None and matricula.cie_p4 < 70 and matricula.cie_rp4 is not None
                        
                        matricula.mostrar_eti_rp1 = matricula.eti_p1 is not None and matricula.eti_p1 < 70 and matricula.eti_rp1 is not None
                        matricula.mostrar_eti_rp2 = matricula.eti_p2 is not None and matricula.eti_p2 < 70 and matricula.eti_rp2 is not None
                        matricula.mostrar_eti_rp3 = matricula.eti_p3 is not None and matricula.eti_p3 < 70 and matricula.eti_rp3 is not None
                        matricula.mostrar_eti_rp4 = matricula.eti_p4 is not None and matricula.eti_p4 < 70 and matricula.eti_rp4 is not None
                    materia.matricula = matricula
                materias_por_curso[curso] = materias_curso
            return render(request, 'est_forder/materias_estudiante.html', {
                'materias_por_curso': materias_por_curso,
                'titulo': "Mis Materias",
                'curso_id': curso_id,
                'anho': None
            })

    # Filtro de búsqueda
    if q:
        materias = materias.filter(
            Q(nombre__icontains=q) |
            Q(codigo__icontains=q) |
            Q(profesor__first_name__icontains=q) |
            Q(profesor__last_name__icontains=q)
        )

    # Agregar info de matrÃ­cula para estudiantes
    if request.user.rol == 'Estudiante':
        for materia in materias:
            matricula = Matricula.objects.filter(materia=materia, estudiante=request.user).first()
            if matricula:
                # Preparar información de recuperaciones para el template
                matricula.mostrar_com_rp1 = matricula.com_p1 is not None and matricula.com_p1 < 70 and matricula.com_rp1 is not None
                matricula.mostrar_com_rp2 = matricula.com_p2 is not None and matricula.com_p2 < 70 and matricula.com_rp2 is not None
                matricula.mostrar_com_rp3 = matricula.com_p3 is not None and matricula.com_p3 < 70 and matricula.com_rp3 is not None
                matricula.mostrar_com_rp4 = matricula.com_p4 is not None and matricula.com_p4 < 70 and matricula.com_rp4 is not None
                
                matricula.mostrar_log_rp1 = matricula.log_p1 is not None and matricula.log_p1 < 70 and matricula.log_rp1 is not None
                matricula.mostrar_log_rp2 = matricula.log_p2 is not None and matricula.log_p2 < 70 and matricula.log_rp2 is not None
                matricula.mostrar_log_rp3 = matricula.log_p3 is not None and matricula.log_p3 < 70 and matricula.log_rp3 is not None
                matricula.mostrar_log_rp4 = matricula.log_p4 is not None and matricula.log_p4 < 70 and matricula.log_rp4 is not None
                
                matricula.mostrar_cie_rp1 = matricula.cie_p1 is not None and matricula.cie_p1 < 70 and matricula.cie_rp1 is not None
                matricula.mostrar_cie_rp2 = matricula.cie_p2 is not None and matricula.cie_p2 < 70 and matricula.cie_rp2 is not None
                matricula.mostrar_cie_rp3 = matricula.cie_p3 is not None and matricula.cie_p3 < 70 and matricula.cie_rp3 is not None
                matricula.mostrar_cie_rp4 = matricula.cie_p4 is not None and matricula.cie_p4 < 70 and matricula.cie_rp4 is not None
                
                matricula.mostrar_eti_rp1 = matricula.eti_p1 is not None and matricula.eti_p1 < 70 and matricula.eti_rp1 is not None
                matricula.mostrar_eti_rp2 = matricula.eti_p2 is not None and matricula.eti_p2 < 70 and matricula.eti_rp2 is not None
                matricula.mostrar_eti_rp3 = matricula.eti_p3 is not None and matricula.eti_p3 < 70 and matricula.eti_rp3 is not None
                matricula.mostrar_eti_rp4 = matricula.eti_p4 is not None and matricula.eti_p4 < 70 and matricula.eti_rp4 is not None
            materia.matricula = matricula

    return render(request, 'est_forder/materias.html', {
        'curso_id': curso_id,
        'curso': curso,
        'materias': materias,
        'titulo': f"Materias del curso {curso.nombre}",
        'anho': anho,
        'q': q
    })

from django.shortcuts import render, get_object_or_404
from .models import Materia, Matricula

def reporte_notas_materia(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    matriculas = Matricula.objects.filter(materia=materia).select_related("estudiante")

    context = {
        "materia": materia,
        "matriculas": matriculas,
    }
    return render(request, "est_forder/reporte_notas_materia.html", context)

from django.shortcuts import render, get_object_or_404
from django.db.models import Avg
from .models import Curso, Matricula

@login_required
def reporte_general(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    # Todas las matrículas del curso ORDENADAS POR nombre (first_name)
    matriculas = (
        Matricula.objects
        .filter(materia__curso=curso)
        .select_related("estudiante", "materia", "materia__curso", "materia__profesor")
        .order_by(
            "estudiante__first_name",
            "estudiante__last_name",
            "materia__nombre"  #  Ordena las materias alfabÃ©ticamente
        )
    )
    # ===========================================
    #   ¥ CALCULAR NOTAS PARA CADA MATRÃCULA
    # ===========================================
    for m in matriculas:
        try:
            prom_com = float(m.prom_comunicativa) if m.prom_comunicativa is not None else None
            prom_log = float(m.prom_logico) if m.prom_logico is not None else None
            prom_cie = float(m.prom_cientifica) if m.prom_cientifica is not None else None
            prom_eti = float(m.prom_etica) if m.prom_etica is not None else None

            ex_com = float(m.ex_com) if m.ex_com is not None else None
            ex_ext = float(m.ex_ext) if m.ex_ext is not None else None
            ex_esp = float(m.ex_esp) if m.ex_esp is not None else None

            m.nota_final = None
            m.nota_final_completivo = None
            m.nota_final_extraordinario = None
            m.nota_final_especial = None
            m.nota_final_oficial = None

            # -------------------------
            #   1ï¸✓£ FINAL DIRECTO (NO MODULAR)
            # -------------------------
            if hasattr(m.materia, 'categoria') and m.materia.categoria != 'modular':
                if None not in (prom_com, prom_log, prom_cie, prom_eti):
                    m.nota_final = round((prom_com + prom_log + prom_cie + prom_eti) / 4, 2)

                    # COMPLETIVO
                    if m.nota_final < 70 and ex_com is not None:
                        m.nota_final_completivo = round((m.nota_final * 0.5) + (ex_com * 0.5), 2)

                    # EXTRAORDINARIO
                    if (
                        m.nota_final_completivo is not None and
                        m.nota_final_completivo < 70 and
                        ex_ext is not None
                    ):
                        m.nota_final_extraordinario = round((m.nota_final * 0.3) + (ex_ext * 0.7), 2)

                    # ESPECIAL
                    if (
                        m.nota_final_extraordinario is not None and
                        m.nota_final_extraordinario < 70 and
                        ex_esp is not None
                    ):
                        m.nota_final_especial = round(ex_esp, 2)

                    # NOTA FINAL OFICIAL
                    if m.nota_final >= 70:
                        m.nota_final_oficial = int(m.nota_final + 0.5)
                    elif m.nota_final < 70:
                        if ex_com is None:
                            m.nota_final_oficial = None
                        elif m.nota_final_completivo >= 70:
                            m.nota_final_oficial = int(m.nota_final_completivo + 0.5)
                        else:
                            if ex_ext is None:
                                m.nota_final_oficial = None
                            elif m.nota_final_extraordinario >= 70:
                                m.nota_final_oficial = int(m.nota_final_extraordinario + 0.5)
                            else:
                                if ex_esp is None:
                                    m.nota_final_oficial = None
                                else:
                                    m.nota_final_oficial = int(m.nota_final_especial + 0.5)
            # -------------------------
            #   ¥ PROMEDIO PORCENTUAL MODULAR (RA)
            # -------------------------
            if hasattr(m.materia, 'categoria') and m.materia.categoria == 'modular':
                if m.materia.ra_configuracion:
                    valores = m.materia.ra_configuracion.get('valores', [])
                    porcentajes = []
                    for idx, peso in enumerate(valores):
                        ra_val = getattr(m, f'ra_{idx+1}', None)
                        if ra_val is not None:
                            # Calcular el porcentaje de completitud: (valor_obtenido / peso_mÃ¡ximo) * 100
                            porcentaje_completitud = (ra_val / peso) * 100
                            porcentajes.append(porcentaje_completitud)
                    # Promedio de los porcentajes de RAs completados
                    if porcentajes:
                        m.total_ra = round(sum(porcentajes) / len(porcentajes), 2)
                    else:
                        m.total_ra = None
                else:
                    # Sistema antiguo: cada RA vale 10% mÃ¡ximo
                    porcentajes = []
                    for i in range(1, 11):
                        ra_val = getattr(m, f'ra_{i}', None)
                        if ra_val is not None:
                            # Calcular porcentaje: (valor / 10) * 100
                            porcentaje_completitud = (ra_val / 10.0) * 100
                            porcentajes.append(porcentaje_completitud)
                    # Promedio de los RAs completados
                    if porcentajes:
                        m.total_ra = round(sum(porcentajes) / len(porcentajes), 2)
                    else:
                        m.total_ra = None
            else:
                m.total_ra = None

            m.save(skip_validation=True)

        except Exception as e:
            print(f"ERROR calculando notas en matrÃ­cula {m.id}: {e}")

    # ===========================================
    #   ¥ AGRUPAR POR ESTUDIANTE
    # ===========================================
    reporte_estudiantes = {}

    for m in matriculas:
        est = m.estudiante

        if est not in reporte_estudiantes:
            reporte_estudiantes[est] = {
                "matriculas": [],
                "total_materias": 0,
                "materias_aprobadas": 0,
                "materias_reprobadas": 0,
                "materias_en_progreso": 0,
                "promedio_general": None,
            }

        datos = reporte_estudiantes[est]

        datos["matriculas"].append(m)
        datos["total_materias"] += 1

        if m.nota_final_oficial is None:
            datos["materias_en_progreso"] += 1
        elif m.nota_final_oficial >= 70:
            datos["materias_aprobadas"] += 1
        else:
            datos["materias_reprobadas"] += 1

    # ===========================================
    #   ¥ PROMEDIO GENERAL POR ESTUDIANTE
    # ===========================================
    for est, datos in reporte_estudiantes.items():
        finales = [
            m.nota_final_oficial
            for m in datos["matriculas"]
            if m.nota_final_oficial is not None
        ]

        if finales:
            datos["promedio_general"] = sum(finales) / len(finales)

    from .models import ConfiguracionEscuela
    config = ConfiguracionEscuela.get_configuracion()
    return render(request, "est_forder/reporte_general.html", {
        "curso": curso,
        "reporte_estudiantes": reporte_estudiantes,
        "config": config,
    })


# --- NUEVA VISTA PDF ---
from django.http import HttpResponse
from django.template.loader import get_template
import io
from xhtml2pdf import pisa
import base64

@login_required
def reporte_general_pdf(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    matriculas = (
        Matricula.objects
        .filter(materia__curso=curso)
        .select_related("estudiante", "materia", "materia__curso", "materia__profesor")
        .order_by(
            "estudiante__first_name",
            "estudiante__last_name",
            "materia__nombre"
        )
    )

    # --- Lógica igual que en reporte_general, pero NO guardar en DB ---
    for m in matriculas:
        try:
            prom_com = float(m.prom_comunicativa) if m.prom_comunicativa is not None else None
            prom_log = float(m.prom_logico) if m.prom_logico is not None else None
            prom_cie = float(m.prom_cientifica) if m.prom_cientifica is not None else None
            prom_eti = float(m.prom_etica) if m.prom_etica is not None else None

            ex_com = float(m.ex_com) if m.ex_com is not None else None
            ex_ext = float(m.ex_ext) if m.ex_ext is not None else None
            ex_esp = float(m.ex_esp) if m.ex_esp is not None else None

            m.nota_final = None
            m.nota_final_completivo = None
            m.nota_final_extraordinario = None
            m.nota_final_especial = None
            m.nota_final_oficial = None

            if hasattr(m.materia, 'categoria') and m.materia.categoria != 'modular':
                if None not in (prom_com, prom_log, prom_cie, prom_eti):
                    m.nota_final = round((prom_com + prom_log + prom_cie + prom_eti) / 4, 2)
                    if m.nota_final < 70 and ex_com is not None:
                        m.nota_final_completivo = round((m.nota_final * 0.5) + (ex_com * 0.5), 2)
                    if (
                        m.nota_final_completivo is not None and
                        m.nota_final_completivo < 70 and
                        ex_ext is not None
                    ):
                        m.nota_final_extraordinario = round((m.nota_final * 0.3) + (ex_ext * 0.7), 2)
                    if (
                        m.nota_final_extraordinario is not None and
                        m.nota_final_extraordinario < 70 and
                        ex_esp is not None
                    ):
                        m.nota_final_especial = round(ex_esp, 2)
                    if m.nota_final >= 70:
                        m.nota_final_oficial = int(m.nota_final + 0.5)
                    elif m.nota_final < 70:
                        if ex_com is None:
                            m.nota_final_oficial = None
                        elif m.nota_final_completivo >= 70:
                            m.nota_final_oficial = int(m.nota_final_completivo + 0.5)
                        else:
                            if ex_ext is None:
                                m.nota_final_oficial = None
                            elif m.nota_final_extraordinario >= 70:
                                m.nota_final_oficial = int(m.nota_final_extraordinario + 0.5)
                            else:
                                if ex_esp is None:
                                    m.nota_final_oficial = None
                                else:
                                    m.nota_final_oficial = int(m.nota_final_especial + 0.5)
            if hasattr(m.materia, 'categoria') and m.materia.categoria == 'modular':
                if m.materia.ra_configuracion:
                    valores = m.materia.ra_configuracion.get('valores', [])
                    porcentajes = []
                    for idx, peso in enumerate(valores):
                        ra_val = getattr(m, f'ra_{idx+1}', None)
                        if ra_val is not None:
                            # Calcular el porcentaje de completitud: (valor_obtenido / peso_mÃ¡ximo) * 100
                            porcentaje_completitud = (ra_val / peso) * 100
                            porcentajes.append(porcentaje_completitud)
                    # Promedio de los porcentajes de RAs completados
                    if porcentajes:
                        m.total_ra = round(sum(porcentajes) / len(porcentajes), 2)
                    else:
                        m.total_ra = None
                else:
                    # Sistema antiguo: cada RA vale 10% mÃ¡ximo
                    porcentajes = []
                    for i in range(1, 11):
                        ra_val = getattr(m, f'ra_{i}', None)
                        if ra_val is not None:
                            # Calcular porcentaje: (valor / 10) * 100
                            porcentaje_completitud = (ra_val / 10.0) * 100
                            porcentajes.append(porcentaje_completitud)
                    # Promedio de los RAs completados
                    if porcentajes:
                        m.total_ra = round(sum(porcentajes) / len(porcentajes), 2)
                    else:
                        m.total_ra = None
            else:
                m.total_ra = None
        except Exception as e:
            print(f"ERROR calculando notas en matrÃ­cula {m.id}: {e}")

    reporte_estudiantes = {}
    for m in matriculas:
        est = m.estudiante
        if est not in reporte_estudiantes:
            reporte_estudiantes[est] = {
                "matriculas": [],
                "total_materias": 0,
                "materias_aprobadas": 0,
                "materias_reprobadas": 0,
                "materias_en_progreso": 0,
                "promedio_general": None,
            }
        datos = reporte_estudiantes[est]
        datos["matriculas"].append(m)
        datos["total_materias"] += 1
        if m.nota_final_oficial is None:
            datos["materias_en_progreso"] += 1
        elif m.nota_final_oficial >= 70:
            datos["materias_aprobadas"] += 1
        else:
            datos["materias_reprobadas"] += 1
    for est, datos in reporte_estudiantes.items():
        finales = [
            m.nota_final_oficial
            for m in datos["matriculas"]
            if m.nota_final_oficial is not None
        ]
        if finales:
            datos["promedio_general"] = sum(finales) / len(finales)

    # Renderizar el template PDF
    template = get_template("est_forder/reporte_general_pdf.html")
    from .models import ConfiguracionEscuela
    config = ConfiguracionEscuela.get_configuracion()
    
    # Convertir logo a base64 si existe
    logo_base64 = None
    if config.mostrar_logo_reportes and config.logo:
        try:
            with open(config.logo.path, 'rb') as img_file:
                logo_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                # Detectar tipo de imagen
                ext = config.logo.name.split('.')[-1].lower()
                if ext in ['jpg', 'jpeg']:
                    logo_base64 = f"data:image/jpeg;base64,{logo_base64}"
                elif ext == 'png':
                    logo_base64 = f"data:image/png;base64,{logo_base64}"
                else:
                    logo_base64 = f"data:image/{ext};base64,{logo_base64}"
        except Exception as e:
            print(f"Error leyendo logo: {e}")
            logo_base64 = None
    
    html = template.render({
        "curso": curso,
        "reporte_estudiantes": reporte_estudiantes,
        "request": request,
        "config": config,
        "logo_base64": logo_base64,
    })
    
    # Generar PDF con xhtml2pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="reporte_general_{curso.id}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error al generar PDF', status=500)
    return response



def reporte_estudiante(request, curso_id, matricula_id):
    curso = get_object_or_404(Curso, id=curso_id)
    matricula = get_object_or_404(Matricula, id=matricula_id, curso=curso)

    # aquÃ­ calculas todos los promedios que ya tienes en tu modelo
    promedios = {
        "ComunicaciÃ³n": matricula.prom_comunicativa,
        "MatemÃ¡tica": matricula.prom_matematica,
        "Ciencias": matricula.prom_cientifica,
        "Sociales": matricula.prom_social,
        # aÃ±ade las demÃ¡s competencias
    }

    return render(request, "reporte_estudiante.html", {
        "curso": curso,
        "matricula": matricula,
        "promedios": promedios
    })


@admin_required
def agregar_materia1(request, curso_id):
    print("paso")
    # Verificar permisos
    if request.user.rol != 'Administrador':
        messages.error(request, "No tienes permisos para agregar materias.")
        return redirect('lista_materias')  # O al listado de materias

    # Obtener curso
    curso = get_object_or_404(Curso, id=curso_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        codigo = request.POST.get('codigo')
        profesor_id = request.POST.get('profesor')

        # Obtener profesor si se selecciona
        profesor = CustomUser.objects.filter(id=profesor_id, rol='Profesor').first() if profesor_id else None

        # Crear materia
        Materia.objects.create(
            nombre=nombre,
            codigo=codigo,
            curso=curso,
            profesor=profesor
        )

        messages.success(request, "Materia agregada exitosamente.")
        return redirect(f"{reverse('lista_materias')}?curso={curso_id}")

    # GET: mostrar formulario
    profesores = CustomUser.objects.filter(rol='Profesor')

    return render(request, 'est_forder/form_materia.html', {
        'curso': curso,
        'profesores': profesores,
        'titulo': f"Agregar Materia al curso {curso.nombre}",
        'curso_id': curso_id
    })

@admin_required
def agregar_materia(request, curso_id):

    curso = get_object_or_404(Curso, id=curso_id)

    if request.method == 'POST':
        form = MateriaForm(request.POST)
        if form.is_valid():
            materia = form.save(commit=False)
            materia.curso = curso
            materia.save()
            messages.success(request, "Materia agregada exitosamente.")
            return redirect(f"{reverse('lista_materias')}?curso={curso_id}")
    else:
        form = MateriaForm()

    return render(request, 'est_forder/form_materia.html', {
        'form': form,
        'titulo': f"Agregar Materia al curso {curso.nombre}",
        'curso_id': curso_id
    })


@admin_required
def editar_materia1(request, pk):
    materia = get_object_or_404(Materia, pk=pk)
    if request.method == 'POST':
        form = MateriaForm(request.POST, instance=materia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Materia actualizada exitosamente.')
            return redirect('lista_materias')
    else:
        form = MateriaForm(instance=materia)
    return render(request, 'est_forder/form_materia.html', {
        'form': form,
        'titulo': 'Editar Materia'
    })
@admin_required
def editar_materia(request, pk):
    materia = get_object_or_404(Materia, pk=pk)
    curso_id = materia.curso.id  # <-- agregamos esto

    if request.method == 'POST':
        form = MateriaForm(request.POST, instance=materia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Materia actualizada exitosamente.')
            return redirect(f"{reverse('lista_materias')}?curso={curso_id}")  # <-- incluimos curso_id
    else:
        form = MateriaForm(instance=materia)

    return render(request, 'est_forder/form_materia.html', {
        'form': form,
        'titulo': f"Editar Materia - {materia.nombre}",
        'curso_id': curso_id  # <-- para usarlo en el template
    })


@admin_required
def eliminar_materia(request, pk):
    """
    Solo redirige a la vista de confirmación (no borra).
    """
    return redirect('confirmar_eliminar_materia', pk=pk)


@login_required
def confirmar_eliminar_materia(request, pk):
    """
    Muestra el formulario de confirmación (password) y maneja el POST
    para borrar solo si la contraseña es correcta.
    """
    materia = get_object_or_404(Materia, pk=pk)
    curso_id = materia.curso.id if materia.curso else None

    # Solo admin/director/superuser
    if not (request.user.is_superuser or getattr(request.user, 'rol', None) in ['Administrador', 'Director']):
        messages.error(request, 'Solo administradores y directores pueden eliminar materias.')
        return redirect('lista_materias')

    from .models import CodigoAnulacion
    if request.method == 'POST':
        password = request.POST.get('password', '').strip()
        codigo_anulacion = request.POST.get('codigo_anulacion', '').strip()

        if not password or not codigo_anulacion:
            messages.error(request, 'Debe ingresar la contraseña y el código de anulación.')
            return redirect('confirmar_eliminar_materia', pk=pk)

        if not request.user.check_password(password):
            messages.error(request, 'Contraseña incorrecta.')
            return redirect('confirmar_eliminar_materia', pk=pk)

        if not CodigoAnulacion.validar_codigo(codigo_anulacion):
            messages.error(request, 'Código de anulación incorrecto.')
            return redirect('confirmar_eliminar_materia', pk=pk)

        try:
            materia.delete()
            messages.success(request, 'Materia eliminada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar la materia: {e}')

        if curso_id:
            return redirect(f"{reverse('lista_materias')}?curso={curso_id}")
        return redirect('lista_materias')

    # GET: mostrar confirmación
    return render(request, 'est_forder/confirmar_eliminar_materia.html', {
        'materia': materia,
        'curso_id': curso_id,
        'titulo': 'Confirmar Eliminación de Materia'
    })
# Vistas para MatrÃ­culas
@login_required
def lista_matriculas(request):
    matriculas = Matricula.objects.all().select_related('estudiante', 'materia')
    return render(request, 'est_forder/matriculas.html', {'matriculas': matriculas})

@admin_required
def agregar_matricula(request):
    if request.method == 'POST':
        form = MatriculaForm(request.POST)
        if form.is_valid():
            matricula = form.save()

            # Actualizar grado y sección del estudiante según el curso asociado a la materia
            try:
                curso = matricula.materia.curso
                nombre = curso.nombre or ''
                parts = nombre.rsplit(' ', 1)
                if len(parts) == 2 and parts[1].isalpha() and len(parts[1]) == 1:
                    grado_text = parts[0].strip()
                    seccion_text = parts[1].upper()
                else:
                    # Si no tiene sección al final, dejar sección en vacÃ­o
                    grado_text = nombre.strip()
                    seccion_text = ''

                estudiante = matricula.estudiante
                estudiante.grado = grado_text
                estudiante.seccion = seccion_text
                estudiante.save()
            except Exception:
                # No interrumpir el flujo si hay algÃºn problema al actualizar usuario
                pass

            messages.success(request, 'MatrÃ­cula agregada exitosamente.')
            return redirect('lista_matriculas')
    else:
        form = MatriculaForm()

    estudiantes = CustomUser.objects.filter(rol='Estudiante').order_by('first_name', 'last_name')
    materias = Materia.objects.all().select_related('curso').order_by('nombre')

    return render(request, 'est_forder/form_matricula.html', {
        'form': form,
        'titulo': 'Agregar MatrÃ­cula',
        'estudiantes': estudiantes,
        'materias': materias
    })

@admin_required
def editar_matricula(request, pk):
    matricula = get_object_or_404(Matricula, pk=pk)
    if request.method == 'POST':
        form = MatriculaForm(request.POST, instance=matricula)
        if form.is_valid():
            matricula = form.save()

            # Actualizar grado y sección del estudiante según el curso asociado
            try:
                curso = matricula.materia.curso
                nombre = curso.nombre or ''
                parts = nombre.rsplit(' ', 1)
                if len(parts) == 2 and parts[1].isalpha() and len(parts[1]) == 1:
                    grado_text = parts[0].strip()
                    seccion_text = parts[1].upper()
                else:
                    grado_text = nombre.strip()
                    seccion_text = ''

                estudiante = matricula.estudiante
                estudiante.grado = grado_text
                estudiante.seccion = seccion_text
                estudiante.save()
            except Exception:
                pass

            messages.success(request, 'MatrÃ­cula actualizada exitosamente.')
            return redirect('lista_matriculas')
    else:
        form = MatriculaForm(instance=matricula)

    estudiantes = CustomUser.objects.filter(rol='Estudiante').order_by('first_name', 'last_name')
    materias = Materia.objects.all().select_related('curso').order_by('nombre')

    return render(request, 'est_forder/form_matricula.html', {
        'form': form,
        'titulo': 'Editar MatrÃ­cula',
        'estudiantes': estudiantes,
        'materias': materias
    })

@admin_required
def eliminar_matricula(request, pk):
    matricula = get_object_or_404(Matricula, pk=pk)
    if request.method == 'POST':
        matricula.delete()
        messages.success(request, 'MatrÃ­cula eliminada exitosamente.')
        return redirect('lista_matriculas')
    return render(request, 'est_forder/confirmar_eliminar_matricula.html', {
        'matricula': matricula
    })

@login_required
def confirmar_eliminar_curso(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    from .models import CodigoAnulacion
    if request.method == 'POST':
        password = request.POST.get('password', '').strip()
        codigo_anulacion = request.POST.get('codigo_anulacion', '').strip()
        if not password or not codigo_anulacion:
            messages.error(request, 'Debe ingresar la contraseña y el código de anulación.')
            return render(request, 'est_forder/confirmar_eliminar_curso.html', {'curso': curso})

        if not request.user.check_password(password):
            messages.error(request, 'Contraseña incorrecta.')
            return render(request, 'est_forder/confirmar_eliminar_curso.html', {'curso': curso})

        if not CodigoAnulacion.validar_codigo(codigo_anulacion):
            messages.error(request, 'Código de anulación incorrecto.')
            return render(request, 'est_forder/confirmar_eliminar_curso.html', {'curso': curso})

        try:
            curso.delete()
            messages.success(request, 'Curso eliminado exitosamente.')
            return redirect('lista_cursos')
        except Exception as e:
            messages.error(request, f'Error al eliminar el curso: {str(e)}')
            return render(request, 'est_forder/confirmar_eliminar_curso.html', {'curso': curso})
    return render(request, 'est_forder/confirmar_eliminar_curso.html', {'curso': curso})

@login_required
def matriculas_materia(request, id):
    materia = get_object_or_404(Materia, id=id)

    # Matriculas ordenadas por nombre del estudiante
    matriculas = (
        Matricula.objects
        .filter(materia=materia)
        .select_related('estudiante')
        .order_by('estudiante__first_name', 'estudiante__last_name')
    )

    # Obtener estudiantes que no están matriculados en esta materia
    estudiantes_matriculados = matriculas.values_list('estudiante_id', flat=True)

    estudiantes_disponibles = (
        CustomUser.objects
        .filter(rol='Estudiante')
        .exclude(id__in=estudiantes_matriculados)
        .order_by('first_name', 'last_name')
    )

    return render(request, 'est_forder/matriculas_materia.html', {
        'materia': materia,
        'matriculas': matriculas,
        'estudiantes_disponibles': estudiantes_disponibles
    })
@login_required
def confirmar_eliminar_matricula(request, pk):
    matricula = get_object_or_404(Matricula, pk=pk)
    materia_id = matricula.materia.id   # <<--- obtenemos la materia

    if request.method == 'POST':
        password = request.POST.get('password')
        if not password:
            messages.error(request, 'Debe ingresar la contraseña de confirmación.')
            return redirect('confirmar_eliminar_matricula', pk=pk)

        if not check_password(password, request.user.password):
            messages.error(request, 'Contraseña incorrecta.')
            return redirect('confirmar_eliminar_matricula', pk=pk)

        try:
            matricula.delete()
            messages.success(request, 'MatrÃ­cula eliminada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar la matrÃ­cula: {str(e)}')

        #  redirigir a gestionar matriculas de esa materia
        return redirect('gestionar_matriculas', materia_id=materia_id)

    return render(request, 'est_forder/confirmar_eliminar_matricula.html', {'matricula': matricula})

@login_required
def confirmar_eliminar_matriculaNONE(request, pk):
    matricula = get_object_or_404(Matricula, pk=pk)
    if request.method == 'POST':
        password = request.POST.get('password')
        if not password:
            messages.error(request, 'Debe ingresar la contraseña de confirmación.')
            return redirect('confirmar_eliminar_matricula', pk=pk)

        if not check_password(password, request.user.password):
            messages.error(request, 'Contraseña incorrecta.')
            return redirect('confirmar_eliminar_matricula', pk=pk)

        try:
            matricula.delete()
            messages.success(request, 'MatrÃ­cula eliminada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar la matrÃ­cula: {str(e)}')
        return redirect('lista_matriculas')

    return render(request, 'est_forder/confirmar_eliminar_matricula.html', {'matricula': matricula})

@admin_required
def gestionar_matriculasNoenuso(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    matriculas = Matricula.objects.filter(materia=materia).select_related('estudiante')

    # Calcular estadísticas para el reporte
    total_aprobados = sum(1 for m in matriculas if m.promedio_final and m.promedio_final >= 60)
    total_reprobados = sum(1 for m in matriculas if m.promedio_final and m.promedio_final < 60)
    total_en_progreso = sum(1 for m in matriculas if not m.promedio_final)

    # Obtener estudiantes que no están matriculados en esta materia
    estudiantes_matriculados = matriculas.values_list('estudiante_id', flat=True)
    estudiantes_disponibles = CustomUser.objects.filter(
        rol='Estudiante'
    ).exclude(
        id__in=estudiantes_matriculados
    ).order_by('first_name', 'last_name')

    if request.method == 'POST':
        estudiante_id = request.POST.get('estudiante_id')
        if estudiante_id:
            estudiante = get_object_or_404(CustomUser, id=estudiante_id, rol='Estudiante')
            # Crear nueva matrÃ­cula
            Matricula.objects.create(
                estudiante=estudiante,
                materia=materia,
                anho_escolar=materia.curso.anho_escolar
            )
            messages.success(request, f'Estudiante {estudiante.get_full_name()} matriculado exitosamente.')
            return redirect('gestionar_matriculas', materia_id=materia_id)

    return render(request, 'est_forder/gestionar_matriculas.html', {
        'materia': materia,
        'matriculas': matriculas,
        'estudiantes_disponibles': estudiantes_disponibles,
        'total_aprobados': total_aprobados,
        'total_reprobados': total_reprobados,
        'total_en_progreso': total_en_progreso
    })

@admin_required
def gestionar_matriculasAntigua(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    curso_id = materia.curso.id  # <-- AquÃ­ tenemos el curso al que pertenece la materia

    matriculas = Matricula.objects.filter(materia=materia).select_related('estudiante')

    # Estadísticas
    total_aprobados = sum(1 for m in matriculas if m.promedio_final and m.promedio_final >= 70)
    total_reprobados = sum(1 for m in matriculas if m.promedio_final and m.promedio_final < 70)
    total_en_progreso = sum(1 for m in matriculas if not m.promedio_final)
    estudiantes_matriculados = matriculas.values_list('estudiante_id', flat=True)
    estudiantes_disponibles = CustomUser.objects.filter(
        rol='Estudiante'
    ).exclude(
        id__in=estudiantes_matriculados
    ).order_by('first_name', 'last_name')

    if request.method == 'POST':
        estudiante_id = request.POST.get('estudiante_id')
        if estudiante_id:
            estudiante = get_object_or_404(CustomUser, id=estudiante_id, rol='Estudiante')
            Matricula.objects.create(
                estudiante=estudiante,
                materia=materia,
                anho_escolar=materia.curso.anho_escolar
            )
            messages.success(request, f'Estudiante {estudiante.get_full_name()} matriculado exitosamente.')
            return redirect('gestionar_matriculas', materia_id=materia_id)

    return render(request, 'est_forder/gestionar_matriculas.html', {
        'materia': materia,
        'matriculas': matriculas,
        'estudiantes_disponibles': estudiantes_disponibles,
        'total_aprobados': total_aprobados,
        'total_reprobados': total_reprobados,
        'total_en_progreso': total_en_progreso,
        'curso_id': curso_id  # <-- Pasamos al template
    })

@login_required
def gestionar_matriculaAnt2s(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    curso_id = materia.curso.id  # Curso al que pertenece la materia

    matriculas = Matricula.objects.filter(materia=materia).select_related('estudiante')

    # Inicializar contadores
    total_aprobados = 0
    total_reprobados = 0
    total_en_progreso = 0

    resultados = {}
    for m in matriculas:
        # Obtenemos todas las notas de los 4 periodos y 4 competencias
        notas = [
            m.com_p1, m.com_p2, m.com_p3, m.com_p4,
            m.log_p1, m.log_p2, m.log_p3, m.log_p4,
            m.cie_p1, m.cie_p2, m.cie_p3, m.cie_p4,
            m.eti_p1, m.eti_p2, m.eti_p3, m.eti_p4
        ]

        notas_validas = [n for n in notas if n is not None]
        promedio_parcial = sum(notas_validas) / len(notas_validas) if notas_validas else None

        if len(notas_validas) < len(notas):
            estado = "En proceso"
            nota_final = None
        else:
            nota_final = promedio_parcial
            if nota_final >= 70:
                estado = "Aprobado"
            else:
                estado = "Reprobado"

        resultados[m.id] = {
            "nota_final": nota_final,
            "promedio_parcial": promedio_parcial,
            "estado": estado
        }

    # ...existing code...
        # Ajusta según los campos de notas que tengas en tu modelo
        notas = [m.nota1, m.nota2, m.nota3, m.nota4] if hasattr(m, "nota1") else []

        if not notas or any(n is None for n in notas):
            estado = "En proceso"
            nota_final = None
            total_en_progreso += 1
        else:
            nota_final = sum(notas) / len(notas)
            if nota_final >= 70:
                estado = "Aprobado"
                total_aprobados += 1
            else:
                estado = "Reprobado"
                total_reprobados += 1

        resultados.append({
            "matricula": m,
            "nota_final": nota_final,
            "estado": estado,
        })

    estudiantes_matriculados = matriculas.values_list('estudiante_id', flat=True)
    estudiantes_disponibles = CustomUser.objects.filter(
        rol='Estudiante'
    ).exclude(
        id__in=estudiantes_matriculados
    ).order_by('first_name', 'last_name')

    if request.method == 'POST':
        estudiante_id = request.POST.get('estudiante_id')
        if estudiante_id:
            estudiante = get_object_or_404(CustomUser, id=estudiante_id, rol='Estudiante')
            Matricula.objects.create(
                estudiante=estudiante,
                materia=materia,
                anho_escolar=materia.curso.anho_escolar
            )
            messages.success(request, f'Estudiante {estudiante.get_full_name()} matriculado exitosamente.')
            return redirect('gestionar_matriculas', materia_id=materia_id)

    return render(request, 'est_forder/gestionar_matriculas.html', {
        'materia': materia,
        'resultados': resultados,  # AquÃ­ mandamos los estados de cada matrÃ­cula
        'estudiantes_disponibles': estudiantes_disponibles,
        'total_aprobados': total_aprobados,
        'total_reprobados': total_reprobados,
        'total_en_progreso': total_en_progreso,
        'curso_id': curso_id
    })

@login_required
def gestionar_matriculas(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    curso_id = materia.curso.id  # Curso al que pertenece la materia

    # ¥ Ordenar estudiantes por first_name dentro de las matrículas
    matriculas = (
        Matricula.objects
        .filter(materia=materia)
        .select_related('estudiante')
        .order_by('estudiante__first_name', 'estudiante__last_name')
    )
    # Inicializar contadores
    total_aprobados = 0
    total_reprobados = 0
    total_en_progreso = 0

    resultados = {}
    for m in matriculas:
        # Detectar si es materia modular o por períodos
        if hasattr(materia, 'categoria') and materia.categoria == 'modular':
            # Para materias modulares, usar RA 1-10
            notas = [
                m.ra_1, m.ra_2, m.ra_3, m.ra_4, m.ra_5,
                m.ra_6, m.ra_7, m.ra_8, m.ra_9, m.ra_10
            ]
            
            # Obtener pesos de los RA desde la configuración
            if materia.ra_configuracion and 'valores' in materia.ra_configuracion:
                pesos = materia.ra_configuracion['valores']
            else:
                # Si no hay configuración, usar pesos iguales (10% cada uno para 10 RAs)
                pesos = [10.0] * 10
            
            # Calcular promedio ponderado
            suma_ponderada = 0
            suma_pesos_usados = 0
            todas_completas = True
            
            for i, nota in enumerate(notas):
                if nota is not None:
                    peso = pesos[i] if i < len(pesos) else 10.0
                    suma_ponderada += nota * (peso / 100.0)
                    suma_pesos_usados += peso
                else:
                    todas_completas = False
            
            # Calcular promedios
            if suma_pesos_usados > 0:
                # Promedio parcial: normalizar según pesos usados y multiplicar por 10 para escala 0-100
                promedio_parcial = (suma_ponderada * (100.0 / suma_pesos_usados)) * 10.0
            else:
                promedio_parcial = None
            
            # Si todas están completas, es nota final
            if todas_completas and suma_ponderada > 0:
                nota_final = suma_ponderada * 10.0  # Multiplicar por 10 para escala 0-100
                if nota_final >= 70:  # Nota mÃ­nima de aprobaciÃ³n en escala 0-100
                    estado = "Aprobado"
                    total_aprobados += 1
                else:
                    estado = "Reprobado"
                    total_reprobados += 1
            else:
                nota_final = None
                estado = "En proceso"
                total_en_progreso += 1
                
        else:
            # Para materias por períodos, usar competencias
            notas = [
                m.com_p1, m.com_p2, m.com_p3, m.com_p4,
                m.log_p1, m.log_p2, m.log_p3, m.log_p4,
                m.cie_p1, m.cie_p2, m.cie_p3, m.cie_p4,
                m.eti_p1, m.eti_p2, m.eti_p3, m.eti_p4
            ]

            # Calcular notas vÃ¡lidas (no None)
            notas_validas = [n for n in notas if n is not None]
            promedio_parcial = sum(notas_validas) / len(notas_validas) if notas_validas else None

            # Si faltan notas, estado "En proceso" y nota_final es None
            if len(notas_validas) < len(notas):
                estado = "En proceso"
                nota_final = None
                total_en_progreso += 1
            else:
                # Todas las notas están completas
                nota_final = promedio_parcial
                if nota_final >= 70:
                    estado = "Aprobado"
                    total_aprobados += 1
                else:
                    estado = "Reprobado"
                    total_reprobados += 1

        resultados[m.id] = {
            "nota_final": nota_final,
            "promedio_parcial": promedio_parcial,
            "estado": estado
        }

    estudiantes_matriculados = matriculas.values_list('estudiante_id', flat=True)
    estudiantes_disponibles = CustomUser.objects.filter(
        rol='Estudiante'
    ).exclude(
        id__in=estudiantes_matriculados
    ).order_by('first_name', 'last_name')

    if request.method == 'POST':
        estudiante_id = request.POST.get('estudiante_id')
        if estudiante_id:
            estudiante = get_object_or_404(CustomUser, id=estudiante_id, rol='Estudiante')
            Matricula.objects.create(
                estudiante=estudiante,
                materia=materia,
                anho_escolar=materia.curso.anho_escolar
            )
            messages.success(request, f'Estudiante {estudiante.get_full_name()} matriculado exitosamente.')
            return redirect('gestionar_matriculas', materia_id=materia_id)

    return render(request, 'est_forder/gestionar_matriculas.html', {
        'materia': materia,
        'matriculas': matriculas,           # Para iterar sobre los estudiantes
        'resultados': resultados,           # Para acceder a estado y nota_final
        'estudiantes_disponibles': estudiantes_disponibles,
        'total_aprobados': total_aprobados,
        'total_reprobados': total_reprobados,
        'total_en_progreso': total_en_progreso,
        'curso_id': curso_id
    })

@login_required
def gestionar_matriculasantigua(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    curso_id = materia.curso.id  # Curso al que pertenece la materia

    matriculas = Matricula.objects.filter(materia=materia).select_related('estudiante')

    # Inicializar contadores
    total_aprobados = 0
    total_reprobados = 0
    total_en_progreso = 0

    resultados = {}
    for m in matriculas:
        # Obtenemos todas las notas de los 4 periodos y 4 competencias
        notas = [
            m.com_p1, m.com_p2, m.com_p3, m.com_p4,
            m.log_p1, m.log_p2, m.log_p3, m.log_p4,
            m.cie_p1, m.cie_p2, m.cie_p3, m.cie_p4,
            m.eti_p1, m.eti_p2, m.eti_p3, m.eti_p4
        ]

        if any(n is None for n in notas):
            estado = "En proceso"
            nota_final = None
            total_en_progreso += 1
        else:
            nota_final = sum(notas) / len(notas)
            if nota_final >= 70:
                estado = "Aprobado"
                total_aprobados += 1
            else:
                estado = "Reprobado"
                total_reprobados += 1

        resultados[m.id] = {
            "nota_final": nota_final,
            "estado": estado
        }

    estudiantes_matriculados = matriculas.values_list('estudiante_id', flat=True)
    estudiantes_disponibles = CustomUser.objects.filter(
        rol='Estudiante'
    ).exclude(
        id__in=estudiantes_matriculados
    ).order_by('first_name', 'last_name')

    if request.method == 'POST':
        estudiante_id = request.POST.get('estudiante_id')
        if estudiante_id:
            estudiante = get_object_or_404(CustomUser, id=estudiante_id, rol='Estudiante')
            Matricula.objects.create(
                estudiante=estudiante,
                materia=materia,
                anho_escolar=materia.curso.anho_escolar
            )
            messages.success(request, f'Estudiante {estudiante.get_full_name()} matriculado exitosamente.')
            return redirect('gestionar_matriculas', materia_id=materia_id)

    return render(request, 'est_forder/gestionar_matriculas.html', {
        'materia': materia,
        'matriculas': matriculas,           # Para iterar sobre los estudiantes
        'resultados': resultados,           # Para acceder a estado y nota_final
        'estudiantes_disponibles': estudiantes_disponibles,
        'total_aprobados': total_aprobados,
        'total_reprobados': total_reprobados,
        'total_en_progreso': total_en_progreso,
        'curso_id': curso_id
    })


@admin_required
def eliminar_matricula(request, matricula_id):
    matricula = get_object_or_404(Matricula, id=matricula_id)
    materia_id = matricula.materia.id

    if request.method == 'POST':
        password = request.POST.get('password')
        if not password:
            messages.error(request, 'Debe ingresar la contraseña de confirmación.')
            return redirect('confirmar_eliminar_matricula', matricula_id=matricula_id)

        if not check_password(password, request.user.password):
            messages.error(request, 'Contraseña incorrecta.')
            return redirect('confirmar_eliminar_matricula', matricula_id=matricula_id)

        try:
            matricula.delete()
            messages.success(request, 'MatrÃ­cula eliminada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar la matrÃ­cula: {str(e)}')
        return redirect('gestionar_matriculas', materia_id=materia_id)

    return render(request, 'est_forder/confirmar_eliminar_matricula.html', {
        'matricula': matricula
    })

@admin_required
def actualizar_notasAntigua(request, matricula_id):
    matricula = get_object_or_404(Matricula, id=matricula_id)

    if request.method == 'POST':
        p1 = request.POST.get('p1')
        p2 = request.POST.get('p2')
        p3 = request.POST.get('p3')
        p4 = request.POST.get('p4')

        try:
            if p1: matricula.p1 = float(p1)
            if p2: matricula.p2 = float(p2)
            if p3: matricula.p3 = float(p3)
            if p4: matricula.p4 = float(p4)

            # Validar que las notas estÃ©n entre 0 y 100
            for nota in [matricula.p1, matricula.p2, matricula.p3, matricula.p4]:
                if nota is not None and (nota < 0 or nota > 100):
                    raise ValueError('Las notas deben estar entre 0 y 100')

            # Calcular nota final si hay al menos una nota
            if any([matricula.p1, matricula.p2, matricula.p3, matricula.p4]):
                notas = [n for n in [matricula.p1, matricula.p2, matricula.p3, matricula.p4] if n is not None]
                matricula.nota_final = sum(notas) / len(notas)

            matricula.save()
            messages.success(request, 'Notas actualizadas exitosamente.')
        except ValueError as e:
            messages.error(request, str(e) if str(e) != 'could not convert string to float: ' else 'Por favor ingrese valores numÃ©ricos válidos.')
        except Exception as e:
            messages.error(request, f'Error al actualizar las notas: {str(e)}')

        return redirect('gestionar_matriculas', materia_id=matricula.materia.id)

    return render(request, 'est_forder/actualizar_notas.html', {
        'matricula': matricula
    })

@admin_required
def actualizar_notas(request, matricula_id):
    matricula = get_object_or_404(Matricula, id=matricula_id)

    # Asegurar que los valores se muestren con punto decimal (no coma)
    for campo in [
        'com_p1','com_p2','com_p3','com_p4','com_rp1','com_rp2','com_rp3','com_rp4',
        'log_p1','log_p2','log_p3','log_p4','log_rp1','log_rp2','log_rp3','log_rp4',
        'cie_p1','cie_p2','cie_p3','cie_p4','cie_rp1','cie_rp2','cie_rp3','cie_rp4',
        'eti_p1','eti_p2','eti_p3','eti_p4','eti_rp1','eti_rp2','eti_rp3','eti_rp4',
    ]:
        valor = getattr(matricula, campo)
        if valor is not None:
            setattr(matricula, campo, str(valor).replace(',', '.'))

    if request.method == 'POST':
        try:
            # --- Comunicativa ---
            matricula.com_p1 = request.POST.get('com_p1') or None
            matricula.com_p2 = request.POST.get('com_p2') or None
            matricula.com_p3 = request.POST.get('com_p3') or None
            matricula.com_p4 = request.POST.get('com_p4') or None
            matricula.com_rp1 = request.POST.get('com_rp1') or None
            matricula.com_rp2 = request.POST.get('com_rp2') or None
            matricula.com_rp3 = request.POST.get('com_rp3') or None
            matricula.com_rp4 = request.POST.get('com_rp4') or None

            # --- Pensamiento LÃ³gico ---
            matricula.log_p1 = request.POST.get('log_p1') or None
            matricula.log_p2 = request.POST.get('log_p2') or None
            matricula.log_p3 = request.POST.get('log_p3') or None
            matricula.log_p4 = request.POST.get('log_p4') or None
            matricula.log_rp1 = request.POST.get('log_rp1') or None
            matricula.log_rp2 = request.POST.get('log_rp2') or None
            matricula.log_rp3 = request.POST.get('log_rp3') or None
            matricula.log_rp4 = request.POST.get('log_rp4') or None

            # --- CientÃ­fica ---
            matricula.cie_p1 = request.POST.get('cie_p1') or None
            matricula.cie_p2 = request.POST.get('cie_p2') or None
            matricula.cie_p3 = request.POST.get('cie_p3') or None
            matricula.cie_p4 = request.POST.get('cie_p4') or None
            matricula.cie_rp1 = request.POST.get('cie_rp1') or None
            matricula.cie_rp2 = request.POST.get('cie_rp2') or None
            matricula.cie_rp3 = request.POST.get('cie_rp3') or None
            matricula.cie_rp4 = request.POST.get('cie_rp4') or None

            # --- Ãtica ---
            matricula.eti_p1 = request.POST.get('eti_p1') or None
            matricula.eti_p2 = request.POST.get('eti_p2') or None
            matricula.eti_p3 = request.POST.get('eti_p3') or None
            matricula.eti_p4 = request.POST.get('eti_p4') or None
            matricula.eti_rp1 = request.POST.get('eti_rp1') or None
            matricula.eti_rp2 = request.POST.get('eti_rp2') or None
            matricula.eti_rp3 = request.POST.get('eti_rp3') or None
            matricula.eti_rp4 = request.POST.get('eti_rp4') or None

            # --- ExÃ¡menes Especiales ---
            matricula.ex_com = request.POST.get('ex_com') or None  # Completivo
            matricula.ex_ext = request.POST.get('ex_ext') or None  # Extraordinario
            matricula.ex_esp = request.POST.get('ex_esp') or None  # Especial

            # Validar y convertir valores
            for campo in [
                'com_p1','com_p2','com_p3','com_p4','com_rp1','com_rp2','com_rp3','com_rp4',
                'log_p1','log_p2','log_p3','log_p4','log_rp1','log_rp2','log_rp3','log_rp4',
                'cie_p1','cie_p2','cie_p3','cie_p4','cie_rp1','cie_rp2','cie_rp3','cie_rp4',
                'eti_p1','eti_p2','eti_p3','eti_p4','eti_rp1','eti_rp2','eti_rp3','eti_rp4',
                'ex_com','ex_ext','ex_esp',
            ]:
                valor = getattr(matricula, campo)
                if valor not in [None, '']:
                    # Aceptar coma o punto como decimal
                    valor = float(str(valor).replace(',', '.'))
                    if valor < 0 or valor > 100:
                        raise ValueError("Las notas deben estar entre 0 y 100")
                    setattr(matricula, campo, valor)
                else:
                    setattr(matricula, campo, None)

            matricula.save()
            messages.success(request, 'Notas actualizadas exitosamente.')

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error al actualizar las notas: {str(e)}')

        return redirect('actualizar_notas', matricula_id=matricula.id)

    return render(request, 'est_forder/actualizar_notas.html', {
        'matricula': matricula
    })

@admin_required
def actualizar_notas3(request, matricula_id):
    matricula = get_object_or_404(Matricula, id=matricula_id)

    if request.method == 'POST':
        try:
            # --- Comunicativa ---
            matricula.com_p1 = request.POST.get('com_p1') or None
            matricula.com_p2 = request.POST.get('com_p2') or None
            matricula.com_p3 = request.POST.get('com_p3') or None
            matricula.com_p4 = request.POST.get('com_p4') or None

            # --- Pensamiento LÃ³gico ---
            matricula.log_p1 = request.POST.get('log_p1') or None
            matricula.log_p2 = request.POST.get('log_p2') or None
            matricula.log_p3 = request.POST.get('log_p3') or None
            matricula.log_p4 = request.POST.get('log_p4') or None

            # --- CientÃ­fica ---
            matricula.cie_p1 = request.POST.get('cie_p1') or None
            matricula.cie_p2 = request.POST.get('cie_p2') or None
            matricula.cie_p3 = request.POST.get('cie_p3') or None
            matricula.cie_p4 = request.POST.get('cie_p4') or None

            # --- Ãtica ---
            matricula.eti_p1 = request.POST.get('eti_p1') or None
            matricula.eti_p2 = request.POST.get('eti_p2') or None
            matricula.eti_p3 = request.POST.get('eti_p3') or None
            matricula.eti_p4 = request.POST.get('eti_p4') or None

            # Validar y convertir decimales
            campos = [
                'com_p1','com_p2','com_p3','com_p4',
                'log_p1','log_p2','log_p3','log_p4',
                'cie_p1','cie_p2','cie_p3','cie_p4',
                'eti_p1','eti_p2','eti_p3','eti_p4',
            ]

            for campo in campos:
                valor = getattr(matricula, campo)
                if valor not in [None, '']:
                    # Convertir coma a punto para decimales europeos (ej. "95,5" -> "95.5")
                    valor = str(valor).replace(',', '.')
                    valor = float(valor)
                    if valor < 0 or valor > 100:
                        raise ValueError("Las notas deben estar entre 0 y 100")
                    setattr(matricula, campo, valor)
                else:
                    setattr(matricula, campo, None)

            matricula.save()
            messages.success(request, 'Notas actualizadas exitosamente.')

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error al actualizar las notas: {str(e)}')

        return redirect('actualizar_notas', matricula_id=matricula.id)

    return render(request, 'est_forder/actualizar_notas.html', {
        'matricula': matricula
    })


from django.shortcuts import render, get_object_or_404
from .models import Materia, Matricula
@login_required
def lista_estudiantes_materia(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    matriculas = Matricula.objects.filter(materia=materia).select_related('estudiante')

    context = {
        'materia': materia,
        'matriculas': matriculas,
    }
    return render(request, 'est_forder/reporte_estudiantes_materia.html', context)


@login_required
def hoja_calificaciones_materia(request, materia_id):
    """Vista para generar hoja de calificaciones imprimible para escribir notas a mano"""
    materia = get_object_or_404(Materia, id=materia_id)
    
    # Verificar permisos
    if request.user.rol not in ['Administrador', 'Director', 'Coordinador', 'Secretaria'] and materia.profesor != request.user:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Obtener estudiantes matriculados ordenados por apellido y nombre
    matriculas = Matricula.objects.filter(materia=materia).select_related('estudiante').order_by(
        'estudiante__last_name', 
        'estudiante__first_name'
    )
    
    # Obtener el tipo de evaluación
    tipo_evaluacion = request.GET.get('tipo', 'periodo1')  # periodo1, periodo2, periodo3, periodo4, modular
    
    context = {
        'materia': materia,
        'matriculas': matriculas,
        'tipo_evaluacion': tipo_evaluacion,
        'curso': materia.curso,
    }
    return render(request, 'est_forder/hoja_calificaciones_imprimible.html', context)


from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Materia, Matricula
from .utils_notas import redondear_nota
from .decorators import puede_editar_notas, puede_ver_notas

@login_required
def agregar_notas(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)

    #Verificar si el usuario puede ver esta materia
    if not puede_ver_notas(request.user, materia):
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Determinar si el usuario puede editar (Administrador, Secretaria, Director, Profesor de la materia)
    puede_editar = puede_editar_notas(request.user, materia)
    
    # Si es estudiante, filtrar solo sus propias notas
    if request.user.rol == 'Estudiante':
        # Solo puede ver su propia matrÃ­cula
        matriculas = Matricula.objects.filter(
            materia=materia,
            estudiante=request.user
        )
        if not matriculas.exists():
            messages.error(request, 'No estás matriculado en esta materia.')
            return redirect('plataform')
    else:
        # Otros roles ven todas las matrículas
        matriculas = Matricula.objects.filter(materia=materia).order_by('estudiante__first_name')
    
    # Si la materia es modular, redirigir a template especÃ­fico
    if materia.categoria == 'modular':
        return agregar_notas_modular(request, materia_id)

    # EnumeraciÃ³n
    for i, m in enumerate(matriculas, start=1):
        m.numero = i

    campos = [
        'com_p1', 'com_rp1', 'com_p2', 'com_rp2', 'com_p3', 'com_rp3', 'com_p4', 'com_rp4',
        'log_p1', 'log_rp1', 'log_p2', 'log_rp2', 'log_p3', 'log_rp3', 'log_p4', 'log_rp4',
        'cie_p1', 'cie_rp1', 'cie_p2', 'cie_rp2', 'cie_p3', 'cie_rp3', 'cie_p4', 'cie_rp4',
        'eti_p1', 'eti_rp1', 'eti_p2', 'eti_rp2', 'eti_p3', 'eti_rp3', 'eti_p4', 'eti_rp4',
        'ex_com', 'ex_ext', 'ex_esp'
    ]

    # Preparar valores formateados para el template (mantiene los valores originales para comparaciones)
    for m in matriculas:
        m.valores_display = {}
        for campo in campos:
            valor = getattr(m, campo)
            if valor is not None:
                # Convertir a string con punto decimal para inputs HTML
                m.valores_display[campo] = str(float(valor)).replace(',', '.')
            else:
                m.valores_display[campo] = ''

    # ------------ POST -------------
    if request.method == 'POST':
        # Verificar permisos de ediciÃ³n antes de procesar
        if not puede_editar:
            messages.error(request, 'No tienes permiso para modificar notas.')
            return redirect('agregar_notas', materia_id=materia.id)
        
        try:
            for m in matriculas:
                for campo in campos:
                    valor = request.POST.get(f"{campo}_{m.id}")
                    if valor == "" or valor is None:
                        setattr(m, campo, None)
                    else:
                        # Validar que el valor estÃ© entre 0 y 100
                        valor_float = float(valor)
                        if valor_float < 0 or valor_float > 100:
                            messages.error(request, f"Error: La nota '{campo}' del estudiante {m.estudiante.get_full_name()} debe estar entre 0 y 100. Valor ingresado: {valor_float}")
                            return redirect('agregar_notas', materia_id=materia.id)
                        setattr(m, campo, valor_float)

                m.save()

            messages.success(request, "Notas actualizadas exitosamente.")

        except ValueError as e:
            messages.error(request, f"Error: Valor inválido ingresado. Las notas deben ser números entre 0 y 100.")
        except Exception as e:
            messages.error(request, f"Error al actualizar las notas: {str(e)}")

        return redirect('agregar_notas', materia_id=materia.id)

    # ---------------------------------------
    #  CÃLCULO DE NOTA_FINAL (SIEMPRE AQUÃ)
    # ---------------------------------------
    
    for m in matriculas:
        try:
            # Convertir a float los promedios y recuperaciones
            prom_com = float(m.prom_comunicativa) if m.prom_comunicativa is not None else None
            prom_log = float(m.prom_logico) if m.prom_logico is not None else None
            prom_cie = float(m.prom_cientifica) if m.prom_cientifica is not None else None
            prom_eti = float(m.prom_etica) if m.prom_etica is not None else None

            ex_com = float(m.ex_com) if m.ex_com is not None else None
            ex_ext = float(m.ex_ext) if m.ex_ext is not None else None
            ex_esp = float(m.ex_esp) if m.ex_esp is not None else None

            # Inicializar todas las notas
            m.nota_final = m.nota_final_completivo = m.nota_final_extraordinario = m.nota_final_especial = m.nota_final_oficial = None

            if None not in (prom_com, prom_log, prom_cie, prom_eti):

                # 1ï¸✓£ Nota final promedio
                m.nota_final = redondear_nota((prom_com + prom_log + prom_cie + prom_eti) / 4, decimales=2)

                # 2ï¸✓£ Completivo
                if m.nota_final < 70 and ex_com is not None:
                    m.nota_final_completivo = redondear_nota((m.nota_final * 0.5) + (ex_com * 0.5), decimales=2)

                # 3ï¸✓£ Extraordinario
                if m.nota_final_completivo is not None and m.nota_final_completivo < 70 and ex_ext is not None:
                    m.nota_final_extraordinario = redondear_nota((m.nota_final * 0.3) + (ex_ext * 0.7), decimales=2)

                # 4ï¸✓£ Especial
                if m.nota_final_extraordinario is not None and m.nota_final_extraordinario < 70 and ex_esp is not None:
                    m.nota_final_especial = redondear_nota(ex_esp, decimales=2)

                # 5ï¸✓£ SelecciÃ³n de nota oficial antes del redondeo
                nota_sin_redondear = (
                    m.nota_final if m.nota_final >= 70 else
                    m.nota_final_completivo if m.nota_final_completivo is not None and m.nota_final_completivo >= 70 else
                    m.nota_final_extraordinario if m.nota_final_extraordinario is not None and m.nota_final_extraordinario >= 70 else
                    m.nota_final_especial if m.nota_final_especial is not None else
                    # Si ninguna pasa de 70, toma la última obtenida
                    m.nota_final_especial or m.nota_final_extraordinario or m.nota_final_completivo or m.nota_final
                )

                # 6ï¸✓£ Aplicar redondeo oficial (con 0 decimales para nota oficial)
                # redondea .50 hacia arriba usando ROUND_HALF_UP
                m.nota_final_oficial = redondear_nota(nota_sin_redondear, decimales=0)

            # Guardar sin validación porque puede haber datos antiguos fuera de rango
            m.save(skip_validation=True)

        except Exception as e:
            print(f"Error en matrÃ­cula {m.id}: {e}")
            m.nota_final = m.nota_final_completivo = m.nota_final_extraordinario = m.nota_final_especial = m.nota_final_oficial = None
            m.save(skip_validation=True)

    # Render
    return render(request, 'est_forder/agregar_notas.html', {
        'materia': materia,
        'matriculas': matriculas,
        'titulo': f'Agregar Notas - {materia.nombre}',
        'puede_editar': puede_editar,
        'es_estudiante': request.user.rol == 'Estudiante',
    })

@login_required
def agregar_notas_modular(request, materia_id):
    """Vista especÃ­fica para agregar notas a materias modulares con 10 Resultados de Aprendizaje (RA)"""
    materia = get_object_or_404(Materia, id=materia_id)

    # Verificar si el usuario puede ver esta materia
    if not puede_ver_notas(request.user, materia):
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Determinar si el usuario puede editar
    puede_editar = puede_editar_notas(request.user, materia)
    
    # Si es estudiante, filtrar solo sus propias notas
    if request.user.rol == 'Estudiante':
        matriculas = Matricula.objects.filter(
            materia=materia,
            estudiante=request.user
        )
        if not matriculas.exists():
            messages.error(request, 'No estás matriculado en esta materia.')
            return redirect('plataform')
    else:
        matriculas = Matricula.objects.filter(materia=materia).order_by('estudiante__first_name')

    # EnumeraciÃ³n
    for i, m in enumerate(matriculas, start=1):
        m.numero = i

    # Configuración de RA (cantidad y valores)
    ra_config = materia.ra_configuracion or {}
    cantidad_ra = int(ra_config.get('cantidad', 10))
    valores_ra = ra_config.get('valores', [10]*10)
    # Asegurar que valores_ra sea lista de números
    valores_ra = [float(v) for v in valores_ra]
    if len(valores_ra) != cantidad_ra:
        valores_ra = [10.0]*cantidad_ra

    # Permitir actualizar configuración de RA
    if request.method == 'POST' and 'guardar_config_ra' in request.POST:
        # Verificar permisos de ediciÃ³n
        if not puede_editar:
            messages.error(request, 'No tienes permiso para modificar la configuración de RA.')
            return redirect('agregar_notas_modular', materia_id=materia.id)
        
        try:
            cantidad = int(request.POST.get('cantidad_ra', 10))
            valores = []
            for i in range(1, cantidad+1):
                v = float(request.POST.get(f'valor_ra_{i}', 0))
                valores.append(v)
            if cantidad < 1 or cantidad > 10:
                raise ValueError('La cantidad de RA debe ser entre 1 y 10.')
            if round(sum(valores), 2) != 100.0:
                raise ValueError('La suma de los valores de RA debe ser 100%.')
            materia.ra_configuracion = {'cantidad': cantidad, 'valores': valores}
            materia.save(update_fields=['ra_configuracion'])

            # Borrar campos ra_n+1 a ra_10 en todas las matrículas si se reduce la cantidad
            if cantidad < 10:
                campos_extra = [f'ra_{i}' for i in range(cantidad+1, 11)]
                Matricula.objects.filter(materia=materia).update(**{campo: None for campo in campos_extra})

            messages.success(request, 'Configuración de RA actualizada.')
            return redirect('agregar_notas_modular', materia_id=materia.id)
        except Exception as e:
            messages.error(request, f'Error en la configuración de RA: {str(e)}')

    # Usar configuración actual
    campos_ra = [f'ra_{i}' for i in range(1, cantidad_ra+1)]

    # Formato para template
    for m in matriculas:
        for campo in campos_ra:
            valor = getattr(m, campo, None)
            if valor is not None:
                setattr(m, campo, str(valor).replace(',', '.'))

    # POST - Guardar notas
    if request.method == 'POST' and 'guardar_notas_modular' in request.POST:
        try:
            for m in matriculas:
                ra_valores = []
                for idx, campo in enumerate(campos_ra):
                    valor = request.POST.get(f"{campo}_{m.id}")
                    if valor == "" or valor is None:
                        setattr(m, campo, None)
                    else:
                        valor_float = float(valor)
                        # Obtener el peso mÃ¡ximo para este RA desde la configuración
                        peso_max = valores_ra[idx] if idx < len(valores_ra) else 10.0
                        # Validar que el RA estÃ© entre 0 y su peso mÃ¡ximo
                        if valor_float < 0 or valor_float > peso_max:
                            messages.error(request, f"Error: El RA {idx+1} del estudiante {m.estudiante.get_full_name()} debe estar entre 0 y {peso_max}. Valor ingresado: {valor_float}")
                            return redirect('agregar_notas_modular', materia_id=materia.id)
                        setattr(m, campo, valor_float)
                        ra_valores.append(valor_float)

                # Calcular nota final como suma de los RA (ya están en escala del peso)
                if len(ra_valores) == cantidad_ra:
                    total_ra = sum(ra_valores)
                    m.nota_final = round(total_ra, 2)
                    m.nota_final_oficial = m.nota_final
                else:
                    m.nota_final = None
                    m.nota_final_oficial = None
                m.save()
            messages.success(request, "Calificaciones modulares actualizadas exitosamente.")
        except ValueError as e:
            messages.error(request, f"Error: Valor inválido ingresado. Los RAs deben ser números entre 0 y 10.")
        except Exception as e:
            messages.error(request, f"Error al actualizar las calificaciones: {str(e)}")
        return redirect('agregar_notas_modular', materia_id=materia.id)

    # Calcular totales actuales para mostrar en template
    for m in matriculas:
        ra_vals = [getattr(m, campo, None) for campo in campos_ra]
        # Calcular promedio porcentual solo de los RAs completados
        porcentajes = []
        for idx, ra_val in enumerate(ra_vals):
            if ra_val is not None:
                peso = valores_ra[idx] if idx < len(valores_ra) else 10
                porcentaje_completitud = (float(ra_val) / peso) * 100
                porcentajes.append(porcentaje_completitud)
        # Promedio de los RAs completados
        m.total_ra = round(sum(porcentajes) / len(porcentajes), 2) if porcentajes else None

    return render(request, 'est_forder/agregar_notas_modular.html', {
        'materia': materia,
        'matriculas': matriculas,
        'titulo': f'Calificaciones MÃ³dulo Formativo - {materia.nombre}',
        'cantidad_ra': cantidad_ra,
        'valores_ra': valores_ra,
        'puede_editar': puede_editar,
        'es_estudiante': request.user.rol == 'Estudiante',
    })

@login_required
def agregar_notas2311(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)

    # Validar permisos
    if not (request.user.rol == 'Administrador' or
            (request.user.rol == 'Profesor' and materia.profesor == request.user)):
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('lista_cursos')

    matriculas = Matricula.objects.filter(materia=materia).order_by('estudiante__first_name')

    # EnumeraciÃ³n
    for i, m in enumerate(matriculas, start=1):
        m.numero = i

    campos = [
        'com_p1', 'com_p2', 'com_p3', 'com_p4', 'com_rp',
        'log_p1', 'log_p2', 'log_p3', 'log_p4', 'log_rp',
        'cie_p1', 'cie_p2', 'cie_p3', 'cie_p4', 'cie_rp',
        'eti_p1', 'eti_p2', 'eti_p3', 'eti_p4', 'eti_rp',
        'ex_com', 'ex_ext', 'ex_esp'
    ]

    # Formato para template
    for m in matriculas:
        for campo in campos:
            valor = getattr(m, campo)
            if valor is not None:
                setattr(m, campo, str(valor).replace(',', '.'))

    # ------------ POST -------------
    if request.method == 'POST':
        try:
            for m in matriculas:
                for campo in campos:
                    valor = request.POST.get(f"{campo}_{m.id}")
                    if valor == "" or valor is None:
                        setattr(m, campo, None)
                    else:
                        setattr(m, campo, float(valor))

                m.save()

            messages.success(request, "Notas actualizadas exitosamente.")

        except Exception as e:
            messages.error(request, f"Error al actualizar las notas: {str(e)}")

        return redirect('agregar_notas', materia_id=materia.id)

    # ---------------------------------------
    #  CÃLCULO DE NOTA_FINAL (SIEMPRE AQUÃ)
    # ---------------------------------------
    
    for m in matriculas:
        try:
            # Convertir a float los promedios y recuperaciones
            prom_com = float(m.prom_comunicativa) if m.prom_comunicativa is not None else None
            prom_log = float(m.prom_logico) if m.prom_logico is not None else None
            prom_cie = float(m.prom_cientifica) if m.prom_cientifica is not None else None
            prom_eti = float(m.prom_etica) if m.prom_etica is not None else None

            ex_com = float(m.ex_com) if m.ex_com is not None else None
            ex_ext = float(m.ex_ext) if m.ex_ext is not None else None
            ex_esp = float(m.ex_esp) if m.ex_esp is not None else None

            # Inicializar todas las notas
            m.nota_final = m.nota_final_completivo = m.nota_final_extraordinario = m.nota_final_especial = m.nota_final_oficial = None

            if None not in (prom_com, prom_log, prom_cie, prom_eti):

                # 1ï¸✓£ Nota final promedio
                m.nota_final = round((prom_com + prom_log + prom_cie + prom_eti) / 4, 2)

                # 2ï¸✓£ Completivo
                if m.nota_final < 70 and ex_com is not None:
                    m.nota_final_completivo = round((m.nota_final * 0.5) + (ex_com * 0.5), 2)

                # 3ï¸✓£ Extraordinario
                if m.nota_final_completivo is not None and m.nota_final_completivo < 70 and ex_ext is not None:
                    m.nota_final_extraordinario = round((m.nota_final * 0.3) + (ex_ext * 0.7), 2)

                # 4ï¸✓£ Especial
                if m.nota_final_extraordinario is not None and m.nota_final_extraordinario < 70 and ex_esp is not None:
                    m.nota_final_especial = round(ex_esp, 2)

                # 5ï¸✓£ SelecciÃ³n de nota oficial antes del redondeo
                nota_sin_redondear = (
                    m.nota_final if m.nota_final >= 70 else
                    m.nota_final_completivo if m.nota_final_completivo is not None and m.nota_final_completivo >= 70 else
                    m.nota_final_extraordinario if m.nota_final_extraordinario is not None and m.nota_final_extraordinario >= 70 else
                    m.nota_final_especial if m.nota_final_especial is not None else
                    # Si ninguna pasa de 70, toma la última obtenida
                    m.nota_final_especial or m.nota_final_extraordinario or m.nota_final_completivo or m.nota_final
                )

                # 6ï¸✓£ Aplicar redondeo oficial
                # redondea .50 hacia arriba
                m.nota_final_oficial = int(nota_sin_redondear + 0.5)

            m.save(skip_validation=True)

        except Exception as e:
            print(f"Error en matrÃ­cula {m.id}: {e}")
            m.nota_final = m.nota_final_completivo = m.nota_final_extraordinario = m.nota_final_especial = m.nota_final_oficial = None



            m.save(skip_validation=True)
        except Exception as e:
            print(f"Error en matrÃ­cula {m.id}: {e}")

        



    # Render
    return render(request, 'est_forder/agregar_notas.html', {
        'materia': materia,
        'matriculas': matriculas,
        'titulo': f'Agregar Notas - {materia.nombre}',
    })

@login_required
def agregar_notasXXX(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)

    # --- Validar permisos ---
    if not (request.user.rol == 'Administrador' or
            (request.user.rol == 'Profesor' and materia.profesor == request.user)):
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('lista_cursos')

    matriculas = Matricula.objects.filter(materia=materia)

    # --- Asegurar formato correcto para mostrar valores ---
    for m in matriculas:
        for campo in [
            'com_p1', 'com_p2', 'com_p3', 'com_p4', 'rp_com',
            'log_p1', 'log_p2', 'log_p3', 'log_p4', 'rp_log',
            'cie_p1', 'cie_p2', 'cie_p3', 'cie_p4', 'rp_cie',
            'eti_p1', 'eti_p2', 'eti_p3', 'eti_p4', 'rp_eti',
            'rp_p1', 'rp_p2', 'rp_p3', 'rp_p4'
        ]:
            valor = getattr(m, campo, None)
            if valor is not None:
                setattr(m, campo, str(valor).replace(',', '.'))

    # --- Si se envÃ­a el formulario ---
    if request.method == 'POST':
        try:
            for matricula in matriculas:
                # --- Comunicativa ---
                for i in range(1, 5):
                    setattr(matricula, f'com_p{i}', request.POST.get(f'com_p{i}_{matricula.id}') or None)
                matricula.rp_com = request.POST.get(f'rp_com_{matricula.id}') or None

                # --- LÃ³gico ---
                for i in range(1, 5):
                    setattr(matricula, f'log_p{i}', request.POST.get(f'log_p{i}_{matricula.id}') or None)
                matricula.rp_log = request.POST.get(f'rp_log_{matricula.id}') or None

                # --- CientÃ­fica ---
                for i in range(1, 5):
                    setattr(matricula, f'cie_p{i}', request.POST.get(f'cie_p{i}_{matricula.id}') or None)
                matricula.rp_cie = request.POST.get(f'rp_cie_{matricula.id}') or None

                # --- Ãtica ---
                for i in range(1, 5):
                    setattr(matricula, f'eti_p{i}', request.POST.get(f'eti_p{i}_{matricula.id}') or None)
                matricula.rp_eti = request.POST.get(f'rp_eti_{matricula.id}') or None

                # --- Recuperaciones por periodo ---
                for i in range(1, 5):
                    setattr(matricula, f'rp_p{i}', request.POST.get(f'rp_p{i}_{matricula.id}') or None)

                # -------------------------
                #   ¥ PROMEDIO PORCENTUAL MODULAR (RA)
                # -------------------------
                if hasattr(matricula.materia, 'categoria') and matricula.materia.categoria == 'modular':
                    if matricula.materia.ra_configuracion:
                        valores = matricula.materia.ra_configuracion.get('valores', [])
                        porcentajes = []
                        for idx, peso in enumerate(valores):
                            ra_val = getattr(matricula, f'ra_{idx+1}', None)
                            if ra_val is not None:
                                # Calcular el porcentaje de completitud: (valor_obtenido / peso_mÃ¡ximo) * 100
                                porcentaje_completitud = (ra_val / peso) * 100
                                porcentajes.append(porcentaje_completitud)
                        # Promedio de los porcentajes de RAs completados
                        if porcentajes:
                            matricula.total_ra = round(sum(porcentajes) / len(porcentajes), 2)
                        else:
                            matricula.total_ra = None
                    else:
                        # Sistema antiguo: cada RA vale 10% mÃ¡ximo
                        porcentajes = []
                        for i in range(1, 11):
                            ra_val = getattr(matricula, f'ra_{i}', None)
                            if ra_val is not None:
                                # Calcular porcentaje: (valor / 10) * 100
                                porcentaje_completitud = (ra_val / 10.0) * 100
                                porcentajes.append(porcentaje_completitud)
                        # Promedio de los RAs completados
                        if porcentajes:
                            matricula.total_ra = round(sum(porcentajes) / len(porcentajes), 2)
                        else:
                            matricula.total_ra = None
                else:
                    matricula.total_ra = None

                # --- Convertir valores a float válidos ---
                for campo in [
                    'com_p1', 'com_p2', 'com_p3', 'com_p4', 'rp_com',
                    'log_p1', 'log_p2', 'log_p3', 'log_p4', 'rp_log',
                    'cie_p1', 'cie_p2', 'cie_p3', 'cie_p4', 'rp_cie',
                    'eti_p1', 'eti_p2', 'eti_p3', 'eti_p4', 'rp_eti',
                    'rp_p1', 'rp_p2', 'rp_p3', 'rp_p4'
                ]:
                    valor = getattr(matricula, campo)
                    if valor not in [None, '']:
                        valor = float(str(valor).replace(',', '.'))
                        if not (0 <= valor <= 100):
                            raise ValueError("Las notas deben estar entre 0 y 100.")
                        setattr(matricula, campo, valor)
                    else:
                        setattr(matricula, campo, None)

                # --- Calcular promedios redondeados ---
                def promedio_redondeado(campos):
                    notas = [getattr(matricula, c) for c in campos if getattr(matricula, c) is not None]
                    return round(sum(notas) / len(notas), 2) if notas else None

                matricula.prom_comunicativa = promedio_redondeado(['com_p1', 'com_p2', 'com_p3', 'com_p4', 'rp_com'])
                matricula.prom_logico = promedio_redondeado(['log_p1', 'log_p2', 'log_p3', 'log_p4', 'rp_log'])
                matricula.prom_cientifica = promedio_redondeado(['cie_p1', 'cie_p2', 'cie_p3', 'cie_p4', 'rp_cie'])
                matricula.prom_etica = promedio_redondeado(['eti_p1', 'eti_p2', 'eti_p3', 'eti_p4', 'rp_eti'])

                # --- Promedio final ---
                promedios = [p for p in [
                    matricula.prom_comunicativa,
                    matricula.prom_logico,
                    matricula.prom_cientifica,
                    matricula.prom_etica
                ] if p is not None]
                matricula.promedio_final = round(sum(promedios) / len(promedios), 2) if promedios else None

                # --- Estado final ---
                if matricula.promedio_final is not None:
                    matricula.estado = "Aprobado" if matricula.promedio_final >= 70 else "Reprobado"
                else:
                    matricula.estado = "En proceso"

                matricula.save()

            messages.success(request, "Notas, recuperaciones y promedios actualizados correctamente.")

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Error al actualizar las notas: {str(e)}")

        return redirect('agregar_notas', materia_id=materia.id)

    # --- Contexto ---
    context = {
        'materia': materia,
        'matriculas': matriculas,
        'titulo': f'Agregar Notas - {materia.nombre}',
    }
    return render(request, 'est_forder/agregar_notas.html', context)





@login_required
def reporte_notas_estudiante2(request, estudiante_id):
    estudiante = get_object_or_404(CustomUser, id=estudiante_id, rol='Estudiante')

    # Obtener todas las matrículas del estudiante con sus materias y cursos
    matriculas = Matricula.objects.filter(
        estudiante=estudiante
    ).select_related(
        'materia',
        'materia__curso',
        'materia__curso__anho_escolar',
        'materia__profesor'
    ).order_by('materia__curso__anho_escolar', 'materia__curso', 'materia__nombre')

    # Agrupar matrículas por año escolar
    matriculas_por_anho = {}
    for matricula in matriculas:
        anho = matricula.materia.curso.anho_escolar
        if anho not in matriculas_por_anho:
            matriculas_por_anho[anho] = []
        matriculas_por_anho[anho].append(matricula)

    # Calcular estadísticas generales
    total_materias = matriculas.count()
    materias_aprobadas = sum(1 for m in matriculas if m.nota_final and m.nota_final >= 70)
    materias_reprobadas = sum(1 for m in matriculas if m.nota_final and m.nota_final < 70)
    materias_en_progreso = sum(1 for m in matriculas if not m.nota_final)

    # Calcular promedio general
    notas_finales = [m.nota_final for m in matriculas if m.nota_final is not None]
    promedio_general = sum(notas_finales) / len(notas_finales) if notas_finales else None

    context = {
        'estudiante': estudiante,
        'matriculas_por_anho': matriculas_por_anho,
        'total_materias': total_materias,
        'materias_aprobadas': materias_aprobadas,
        'materias_reprobadas': materias_reprobadas,
        'materias_en_progreso': materias_en_progreso,
        'promedio_general': promedio_general,
    }

    return render(request, 'est_forder/reporte_notas_estudiante.html', context)

@login_required
def reporte_notas_estudiante(request, estudiante_id):
    from .utils_notas import redondear_nota
    
    estudiante = get_object_or_404(CustomUser, id=estudiante_id, rol='Estudiante')
    
    matriculas = Matricula.objects.filter(
        estudiante=estudiante
    ).select_related(
        'materia',
        'materia__curso',
        'materia__curso__anho_escolar',
        'materia__profesor'
    ).order_by('materia__curso__anho_escolar', 'materia__curso', 'materia__nombre')

    # ===============================
    #   ¥ CALCULAR TODAS LAS NOTAS CON REDONDEO CORRECTO
    # ===============================
    for m in matriculas:
        try:
            # Obtener promedios por competencia (ya están redondeados por el modelo)
            prom_com = m.prom_comunicativa
            prom_log = m.prom_logico
            prom_cie = m.prom_cientifica
            prom_eti = m.prom_etica

            # Obtener exÃ¡menes
            ex_com = float(m.ex_com) if m.ex_com is not None else None
            ex_ext = float(m.ex_ext) if m.ex_ext is not None else None
            ex_esp = float(m.ex_esp) if m.ex_esp is not None else None

            # Reset
            m.nota_final = None
            m.nota_final_completivo = None
            m.nota_final_extraordinario = None
            m.nota_final_especial = None
            m.nota_final_oficial = None

            # Solo calcular si tiene los 4 promedios base
            if m.promedio_final is not None:

                # 1ï¸✓£ Final directo (ya viene redondeado del modelo)
                m.nota_final = m.promedio_final

                # 2ï¸✓£ Completivo (usa la función del modelo con redondeo correcto)
                if m.nota_final < 70 and m.calificacion_completiva_final is not None:
                    m.nota_final_completivo = m.calificacion_completiva_final

                # 3ï¸✓£ Extraordinario (usa la función del modelo con redondeo correcto)
                if m.nota_final_completivo is not None and m.nota_final_completivo < 70 and m.calificacion_extraordinario_final is not None:
                    m.nota_final_extraordinario = m.calificacion_extraordinario_final

                # 4ï¸✓£ Especial
                if m.nota_final_extraordinario is not None and m.nota_final_extraordinario < 70 and ex_esp is not None:
                    m.nota_final_especial = redondear_nota(ex_esp, decimales=2)

                # ================================
                #     Nota Final Oficial (redondeada a entero)
                # ================================

                # Aprobado directo
                if m.nota_final >= 70:
                    m.nota_final_oficial = redondear_nota(m.nota_final, decimales=0)

                # Requiere completivo
                elif m.nota_final < 70:

                    # Falta completivo ✓ en proceso
                    if ex_com is None:
                        m.nota_final_oficial = None

                    # Tiene completivo y aprobÃ³
                    elif m.nota_final_completivo >= 70:
                        m.nota_final_oficial = redondear_nota(m.nota_final_completivo, decimales=0)

                    else:
                        # Falta extraordinario ✓ en proceso
                        if ex_ext is None:
                            m.nota_final_oficial = None

                        # Tiene extraordinario y aprobÃ³
                        elif m.nota_final_extraordinario >= 70:
                            m.nota_final_oficial = redondear_nota(m.nota_final_extraordinario, decimales=0)

                        else:
                            # Falta especial ✓ en proceso
                            if ex_esp is None:
                                m.nota_final_oficial = None

                            else:
                                # Usa nota especial
                                m.nota_final_oficial = redondear_nota(m.nota_final_especial, decimales=0)

               
                
            m.save(skip_validation=True)

        except Exception as e:
            print(f"Error en matrÃ­cula {m.id}: {e}")


    # ===============================
    #   ¥ AGRUPACIÃN POR AÃO
    # ===============================
    matriculas_por_anho = {}
    for m in matriculas:
        anho = m.materia.curso.anho_escolar
        if anho not in matriculas_por_anho:
            matriculas_por_anho[anho] = []
        matriculas_por_anho[anho].append(m)

    # ===============================
    #   ¥ ESTADÃSTICAS DEL REPORTE
    # ===============================
    total_materias = matriculas.count()
    materias_aprobadas = sum(1 for m in matriculas if m.nota_final_oficial and m.nota_final_oficial >= 70)
    materias_reprobadas = sum(1 for m in matriculas if m.nota_final_oficial and m.nota_final_oficial < 70)
    materias_en_progreso = sum(1 for m in matriculas if m.nota_final_oficial is None)

    # PROMEDIO GENERAL usando nota_final_oficial con redondeo correcto
    notas_finales = [m.nota_final_oficial for m in matriculas if m.nota_final_oficial is not None]
    promedio_general = redondear_nota(sum(notas_finales) / len(notas_finales), decimales=2) if notas_finales else None

    # ===============================
    #   ¥ CONTEXTO FINAL
    # ===============================
    context = {
        'estudiante': estudiante,
        'matriculas_por_anho': matriculas_por_anho,
        'total_materias': total_materias,
        'materias_aprobadas': materias_aprobadas,
        'materias_reprobadas': materias_reprobadas,
        'materias_en_progreso': materias_en_progreso,
        'promedio_general': promedio_general,
    }
    return render(request, 'est_forder/reporte_notas_estudiante.html', context)


@login_required
def record_calificaciones_pdf(request, estudiante_id):
    """Generar rÃ©cord de calificaciones en PDF formato oficial"""
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    from django.conf import settings
    import os
    from datetime import date
    from .utils_notas import redondear_nota
    
    estudiante = get_object_or_404(CustomUser, id=estudiante_id, rol='Estudiante')
    
    # Obtener todas las matrículas del estudiante
    matriculas = Matricula.objects.filter(
        estudiante=estudiante
    ).select_related(
        'materia',
        'materia__curso',
        'materia__curso__anho_escolar',
        'materia__profesor'
    ).order_by('materia__curso__anho_escolar', 'materia__curso', 'materia__nombre')

    # Calcular notas finales con redondeo correcto
    for m in matriculas:
        try:
            # Obtener promedios por competencia (ya están redondeados por el modelo)
            prom_com = m.prom_comunicativa
            prom_log = m.prom_logico
            prom_cie = m.prom_cientifica
            prom_eti = m.prom_etica
            
            # Obtener exÃ¡menes
            ex_com = float(m.ex_com) if m.ex_com is not None else None
            ex_ext = float(m.ex_ext) if m.ex_ext is not None else None
            ex_esp = float(m.ex_esp) if m.ex_esp is not None else None

            m.nota_final_oficial = None

            # Calcular promedio final (ya usa redondeo correcto del modelo)
            if m.promedio_final is not None:
                m.nota_final = m.promedio_final
                
                # Si aprobÃ³ con el promedio regular
                if m.nota_final >= 70:
                    m.nota_final_oficial = redondear_nota(m.nota_final, decimales=0)
                # Si tiene completivo
                elif m.calificacion_completiva_final is not None:
                    m.nota_final_completivo = m.calificacion_completiva_final
                    if m.nota_final_completivo >= 70:
                        m.nota_final_oficial = redondear_nota(m.nota_final_completivo, decimales=0)
                    # Si tiene extraordinario
                    elif m.calificacion_extraordinario_final is not None:
                        m.nota_final_extraordinario = m.calificacion_extraordinario_final
                        if m.nota_final_extraordinario >= 70:
                            m.nota_final_oficial = redondear_nota(m.nota_final_extraordinario, decimales=0)
                        # Si tiene especial
                        elif ex_esp is not None:
                            m.nota_final_especial = redondear_nota(ex_esp, decimales=2)
                            m.nota_final_oficial = redondear_nota(m.nota_final_especial, decimales=0)
        except Exception as e:
            print(f"Error en matrÃ­cula {m.id}: {e}")

    # Agrupar materias por estudiante para crear tabla horizontal
    # Estructura: { 'materia_nombre': { 'grado1': {'nota': XX, 'fecha': 'XX', 'anho': 'XX'}, 'grado2': {...} } }
    
    # Primero obtener todos los grados Ãºnicos ordenados
    grados_ordenados = []
    grados_dict = {}
    for m in matriculas:
        grado = m.materia.curso.nombre
        anho = m.materia.curso.anho_escolar.nombre
        if grado not in grados_dict:
            grados_dict[grado] = anho
            grados_ordenados.append({'grado': grado, 'anho': anho})
    
    # Crear estructura de materias con calificaciones por grado
    materias_por_grado = {}
    for m in matriculas:
        materia_nombre = m.materia.nombre
        grado = m.materia.curso.nombre
        anho = m.materia.curso.anho_escolar.nombre
        
        if materia_nombre not in materias_por_grado:
            materias_por_grado[materia_nombre] = {}
        
        materias_por_grado[materia_nombre][grado] = {
            'nota': m.nota_final_oficial if hasattr(m, 'nota_final_oficial') else None,
            'fecha': 'Junio/' + anho.split('-')[-1] if hasattr(m, 'nota_final_oficial') and m.nota_final_oficial else None,
            'anho': anho,
            'aprobado': m.nota_final_oficial >= 70 if (hasattr(m, 'nota_final_oficial') and m.nota_final_oficial) else False
        }

    # Contexto para el template
    context = {
        'estudiante': estudiante,
        'grados_ordenados': grados_ordenados,
        'materias_por_grado': materias_por_grado,
        'total_columnas': (len(grados_ordenados) * 2) + 1,  # 2 columnas por grado (Cal, Fecha) + 1 (Asignaturas)
        'fecha_actual': date.today(),
        'STATIC_ROOT': settings.STATIC_ROOT,
    }

    # Renderizar template HTML
    template = get_template('est_forder/record_calificaciones_pdf.html')
    html = template.render(context)
    
    # Crear respuesta PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="record_calificaciones_{estudiante.cedula or estudiante.id}.pdf"'
    
    # Función para resolver rutas estáticas
    def link_callback(uri, rel):
        if os.path.isfile(uri):
            return uri
        
        if uri.startswith(settings.STATIC_ROOT):
            return uri
        
        clean_uri = uri.replace('/static/', '').replace('static/', '').lstrip('/')
        
        for static_dir in getattr(settings, 'STATICFILES_DIRS', []):
            path = os.path.join(static_dir, clean_uri)
            if os.path.isfile(path):
                return path
        
        path = os.path.join(settings.STATIC_ROOT, clean_uri)
        if os.path.isfile(path):
            return path
        
        return uri
    
    # Generar PDF
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisa_status.err:
        return HttpResponse('Error al generar PDF', status=500)
    return response


@login_required
def record_calificaciones_completo_pdf(request, estudiante_id):
    """Generar rÃ©cord de calificaciones completo (ambos ciclos) en PDF formato Legal (8.5 x 14)"""
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    from django.conf import settings
    import os
    from datetime import date
    from .utils_notas import redondear_nota
    
    estudiante = get_object_or_404(CustomUser, id=estudiante_id, rol='Estudiante')
    
    # Obtener todas las matrículas del estudiante
    matriculas = Matricula.objects.filter(
        estudiante=estudiante
    ).select_related(
        'materia',
        'materia__curso',
        'materia__curso__anho_escolar',
        'materia__profesor'
    ).order_by('materia__curso__anho_escolar', 'materia__curso', 'materia__nombre')

    # Debug: imprimir información de matrículas
    print(f"=== DEBUG RECORD COMPLETO ===")
    print(f"Estudiante: {estudiante.get_full_name()}")
    print(f"Total de matrículas encontradas: {matriculas.count()}")
    if matriculas.count() > 0:
        for m in matriculas[:5]:  # Solo las primeras 5 para no saturar
            print(f"  - {m.materia.nombre} | Curso: {m.materia.curso.nombre} | Año: {m.materia.curso.anho_escolar.nombre}")

    # Calcular notas finales con redondeo correcto
    for m in matriculas:
        try:
            # Obtener promedios por competencia (ya están redondeados por el modelo)
            prom_com = m.prom_comunicativa
            prom_log = m.prom_logico
            prom_cie = m.prom_cientifica
            prom_eti = m.prom_etica
            
            # Obtener exÃ¡menes
            ex_com = float(m.ex_com) if m.ex_com is not None else None
            ex_ext = float(m.ex_ext) if m.ex_ext is not None else None
            ex_esp = float(m.ex_esp) if m.ex_esp is not None else None

            m.nota_final_oficial = None

            # Calcular promedio final (ya usa redondeo correcto del modelo)
            if m.promedio_final is not None:
                m.nota_final = m.promedio_final
                
                # Si aprobÃ³ con el promedio regular
                if m.nota_final >= 70:
                    m.nota_final_oficial = redondear_nota(m.nota_final, decimales=0)
                # Si tiene completivo
                elif m.calificacion_completiva_final is not None:
                    m.nota_final_completivo = m.calificacion_completiva_final
                    if m.nota_final_completivo >= 70:
                        m.nota_final_oficial = redondear_nota(m.nota_final_completivo, decimales=0)
                    # Si tiene extraordinario
                    elif m.calificacion_extraordinario_final is not None:
                        m.nota_final_extraordinario = m.calificacion_extraordinario_final
                        if m.nota_final_extraordinario >= 70:
                            m.nota_final_oficial = redondear_nota(m.nota_final_extraordinario, decimales=0)
                        # Si tiene especial
                        elif ex_esp is not None:
                            m.nota_final_especial = redondear_nota(ex_esp, decimales=2)
                            m.nota_final_oficial = redondear_nota(m.nota_final_especial, decimales=0)
        except Exception as e:
            print(f"Error en matrÃ­cula {m.id}: {e}")

    # Separar grados por ciclo - detectar automáticamente usando patrones
    import re
    
    # PRIMERO: Agrupar TODAS las materias como en el reporte que funciona
    # Obtener todos los grados Ãºnicos ordenados
    grados_ordenados_todos = []
    grados_dict = {}
    for m in matriculas:
        grado = m.materia.curso.nombre
        anho = m.materia.curso.anho_escolar.nombre
        if grado not in grados_dict:
            grados_dict[grado] = anho
            grados_ordenados_todos.append({'grado': grado, 'anho': anho})
    
    # Crear estructura de materias con calificaciones por grado
    materias_por_grado_todas = {}
    for m in matriculas:
        materia_nombre = m.materia.nombre
        grado = m.materia.curso.nombre
        anho = m.materia.curso.anho_escolar.nombre
        
        if materia_nombre not in materias_por_grado_todas:
            materias_por_grado_todas[materia_nombre] = {}
        
        materias_por_grado_todas[materia_nombre][grado] = {
            'nota': m.nota_final_oficial if hasattr(m, 'nota_final_oficial') else None,
            'fecha': 'Junio/' + anho.split('-')[-1] if hasattr(m, 'nota_final_oficial') and m.nota_final_oficial else None,
            'anho': anho,
            'aprobado': m.nota_final_oficial >= 70 if (hasattr(m, 'nota_final_oficial') and m.nota_final_oficial) else False
        }
    
    # SEGUNDO: Separar los grados en dos ciclos
    primer_ciclo_grados_ord = []
    segundo_ciclo_grados_ord = []
    
    print(f"Total grados encontrados: {len(grados_ordenados_todos)}")
    for grado_info in grados_ordenados_todos:
        grado_nombre = grado_info['grado'].lower()
        print(f"Analizando grado: {grado_info['grado']}")
        # Buscar patrones para primer ciclo
        if re.search(r'(1Â°|1er|1ro|primero?|2Â°|2do|2da|segundo|3Â°|3er|3ro|tercero)', grado_nombre):
            primer_ciclo_grados_ord.append(grado_info)
            print(f"  -> Asignado a PRIMER CICLO")
        # Buscar patrones para segundo ciclo
        elif re.search(r'(4Â°|4to|4ta|cuarto|5Â°|5to|5ta|quinto|6Â°|6to|6ta|sexto)', grado_nombre):
            segundo_ciclo_grados_ord.append(grado_info)
            print(f"  -> Asignado a SEGUNDO CICLO")
        else:
            print(f"  -> NO RECONOCIDO")
    
    print(f"Primer ciclo: {len(primer_ciclo_grados_ord)} grados")
    print(f"Segundo ciclo: {len(segundo_ciclo_grados_ord)} grados")
    
    # Las materias son las mismas para ambos ciclos, solo filtramos qué grados mostrar en cada tabla
    primer_ciclo_materias = materias_por_grado_todas
    segundo_ciclo_materias = materias_por_grado_todas

    # Contexto para el template
    context = {
        'estudiante': estudiante,
        'primer_ciclo': {
            'grados_ordenados': primer_ciclo_grados_ord,
            'materias_por_grado': primer_ciclo_materias,
            'total_columnas': (len(primer_ciclo_grados_ord) * 2) + 1 if primer_ciclo_grados_ord else 1,  # 2 columnas por grado
        },
        'segundo_ciclo': {
            'grados_ordenados': segundo_ciclo_grados_ord,
            'materias_por_grado': segundo_ciclo_materias,
            'total_columnas': (len(segundo_ciclo_grados_ord) * 2) + 1 if segundo_ciclo_grados_ord else 1,  # 2 columnas por grado
        },
        'fecha_actual': date.today(),
        'STATIC_ROOT': settings.STATIC_ROOT,
    }

    # Renderizar template HTML
    template = get_template('est_forder/record_calificaciones_completo_pdf.html')
    html = template.render(context)
    
    # Crear respuesta PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="record_completo_{estudiante.cedula or estudiante.id}.pdf"'
    
    # Función para resolver rutas estáticas
    def link_callback(uri, rel):
        if os.path.isfile(uri):
            return uri
        
        if uri.startswith(settings.STATIC_ROOT):
            return uri
        
        clean_uri = uri.replace('/static/', '').replace('static/', '').lstrip('/')
        
        for static_dir in getattr(settings, 'STATICFILES_DIRS', []):
            path = os.path.join(static_dir, clean_uri)
            if os.path.isfile(path):
                return path
        
        path = os.path.join(settings.STATIC_ROOT, clean_uri)
        if os.path.isfile(path):
            return path
        
        return uri
    
    # Generar PDF
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisa_status.err:
        return HttpResponse('Error al generar PDF', status=500)
    return response


# ===============================
# ¥ ASISTENCIA (PASAR LISTA)
# ===============================

@login_required
def seleccionar_materia_asistencia(request):
    """Vista para que el profesor seleccione la materia a la que va a pasar lista"""
    if request.user.rol not in ['Profesor', 'Administrador', 'Director']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Obtener año escolar activo
    try:
        anho_escolar = AnhoEscolar.objects.get(activo=True)
    except AnhoEscolar.DoesNotExist:
        messages.error(request, 'No hay un año escolar activo. Por favor, active un año escolar.')
        return redirect('plataform')
    
    # Obtener materias del profesor o todas si es admin, filtradas por año activo
    if request.user.rol == 'Profesor':
        materias = Materia.objects.filter(
            profesor=request.user,
            curso__anho_escolar=anho_escolar
        ).select_related('curso', 'curso__anho_escolar', 'curso__profesor').order_by('nombre')
    else:  # Administrador
        materias = Materia.objects.filter(
            curso__anho_escolar=anho_escolar
        ).select_related('curso', 'profesor', 'curso__anho_escolar').order_by('nombre')
    
    # Agrupar materias por año escolar (aunque solo habrÃ¡ un año - el activo)
    materias_por_anho = {anho_escolar: list(materias)}
    
    context = {
        'materias': materias,
        'materias_por_anho': materias_por_anho,
        'anho_actual': anho_escolar,
        'anho_escolar': anho_escolar,
        'titulo': 'Seleccionar Materia para Pasar Lista',
        'total_materias': materias.count()
    }
    return render(request, 'est_forder/seleccionar_materia_asistencia.html', context)


@login_required
def pasar_lista(request, materia_id):
    """Vista para pasar lista a los estudiantes de una materia"""
    if request.user.rol not in ['Profesor', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    materia = get_object_or_404(Materia, id=materia_id)
    
    # Verificar que haya un año escolar activo
    try:
        anho_escolar = AnhoEscolar.objects.get(activo=True)
    except AnhoEscolar.DoesNotExist:
        messages.error(request, 'No hay un año escolar activo. Por favor, active un año escolar.')
        return redirect('plataform')
    
    # Verificar que la materia pertenezca al año escolar activo
    if materia.curso.anho_escolar != anho_escolar:
        messages.error(request, f'Esta materia pertenece al año escolar {materia.curso.anho_escolar.nombre}, no al año activo {anho_escolar.nombre}.')
        return redirect('seleccionar_materia_asistencia')
    
    # Verificar que el profesor tenga acceso a esta materia
    if request.user.rol == 'Profesor' and materia.profesor != request.user:
        messages.error(request, 'No tienes permiso para pasar lista en esta materia.')
        return redirect('seleccionar_materia_asistencia')
    
    # Obtener la fecha actual en la zona horaria local
    fecha_hoy = timezone.localtime(timezone.now()).date()
    
    # Obtener la fecha para la asistencia (hoy por defecto)
    if request.method == 'POST':
        fecha_str = request.POST.get('fecha', fecha_hoy.isoformat())
    else:
        fecha_str = request.GET.get('fecha', fecha_hoy.isoformat())
    
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        fecha = fecha_hoy
    
    # Obtener estudiantes matriculados en esta materia para el año escolar activo
    matriculas = Matricula.objects.filter(
        materia=materia,
        anho_escolar=anho_escolar
    ).select_related('estudiante').order_by('estudiante__first_name', 'estudiante__last_name')
    estudiantes = [m.estudiante for m in matriculas]
    
    if request.method == 'POST':
        # Procesar asistencia
        asistencias_guardadas = 0
        for estudiante in estudiantes:
            estado = request.POST.get(f'estado_{estudiante.id}')
            observaciones = request.POST.get(f'observaciones_{estudiante.id}', '').strip()
            
            if estado:  # Solo guardar si se marcÃ³ algÃºn estado
                asistencia, created = Asistencia.objects.update_or_create(
                    estudiante=estudiante,
                    materia=materia,
                    fecha=fecha,
                    defaults={
                        'estado': estado,
                        'observaciones': observaciones,
                        'registrado_por': request.user
                    }
                )
                asistencias_guardadas += 1
        
        messages.success(request, f'Asistencia guardada exitosamente para {asistencias_guardadas} estudiantes.')
        return redirect('historial_asistencia')
    
    # Obtener asistencia ya registrada para esta fecha
    asistencias_existentes = {}
    asistencias = Asistencia.objects.filter(materia=materia, fecha=fecha)
    for asistencia in asistencias:
        asistencias_existentes[asistencia.estudiante.id] = asistencia
    
    # Preparar lista de estudiantes con su asistencia
    estudiantes_con_asistencia = []
    for estudiante in estudiantes:
        estudiantes_con_asistencia.append({
            'estudiante': estudiante,
            'asistencia': asistencias_existentes.get(estudiante.id)
        })
    
    context = {
        'materia': materia,
        'fecha': fecha,
        'estudiantes_con_asistencia': estudiantes_con_asistencia,
        'titulo': f'Pasar Lista - {materia.nombre}',
        'anho_escolar': anho_escolar
    }
    return render(request, 'est_forder/pasar_lista.html', context)


@login_required
def historial_asistencia(request):
    """Vista para ver el historial de asistencia en formato mensual tipo planilla"""
    if request.user.rol not in ['Profesor', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Obtener año escolar activo
    try:
        anho_escolar = AnhoEscolar.objects.get(activo=True)
    except AnhoEscolar.DoesNotExist:
        messages.error(request, 'No hay un año escolar activo. Por favor, active un año escolar.')
        return redirect('plataform')
    
    # Filtros
    materia_id = request.GET.get('materia')
    mes = request.GET.get('mes')
    anho = request.GET.get('anho')
    
    # Obtener materias según el rol, filtradas por año activo
    if request.user.rol == 'Profesor':
        materias = Materia.objects.filter(
            profesor=request.user,
            curso__anho_escolar=anho_escolar
        ).select_related('curso', 'profesor').order_by('nombre')
    else:  # Administrador
        materias = Materia.objects.filter(
            curso__anho_escolar=anho_escolar
        ).select_related('curso', 'profesor').order_by('nombre')
    
    # Valores por defecto para mes y año (mes y año actual)
    if not mes or not anho:
        hoy = timezone.now().date()
        mes = mes or str(hoy.month)
        anho = anho or str(hoy.year)
    
    mes = int(mes)
    anho = int(anho)
    
    # Variables para el template
    materia = None
    estudiantes_asistencia = []
    dias_trabajados = []
    nombre_mes = ''
    
    if materia_id:
        materia = get_object_or_404(Materia, id=materia_id)
        
        # Verificar permisos del profesor
        if request.user.rol == 'Profesor' and materia.profesor != request.user:
            messages.error(request, 'No tienes permiso para ver esta materia.')
            return redirect('historial_asistencia')
        
        # Obtener el nombre del mes en español
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        nombre_mes = meses[mes]
        
        # Obtener primer y último día del mes
        import calendar
        primer_dia = datetime(anho, mes, 1).date()
        ultimo_dia = datetime(anho, mes, calendar.monthrange(anho, mes)[1]).date()
        
        # Obtener todas las asistencias del mes para esta materia
        asistencias = Asistencia.objects.filter(
            materia=materia,
            fecha__gte=primer_dia,
            fecha__lte=ultimo_dia
        ).select_related('estudiante').order_by('fecha', 'estudiante__first_name')
        
        # Obtener días Ãºnicos con asistencia (días trabajados)
        dias_trabajados = sorted(list(set([a.fecha.day for a in asistencias])))
        
        # Obtener estudiantes matriculados
        matriculas = Matricula.objects.filter(materia=materia).select_related('estudiante').order_by('estudiante__first_name', 'estudiante__last_name')
        
        # Crear diccionario de asistencias por estudiante y día
        asistencias_dict = {}
        for asistencia in asistencias:
            key = (asistencia.estudiante.id, asistencia.fecha.day)
            asistencias_dict[key] = asistencia.estado
        
        # Preparar datos para el template
        for idx, matricula in enumerate(matriculas, 1):
            estudiante = matricula.estudiante
            asistencias_por_dia = {}
            total_presente = 0
            total_tardanza = 0
            
            for dia in dias_trabajados:
                key = (estudiante.id, dia)
                estado = asistencias_dict.get(key, None)
                
                if estado == 'presente':
                    asistencias_por_dia[dia] = 'presente'
                    total_presente += 1
                elif estado == 'ausente':
                    asistencias_por_dia[dia] = 'ausente'
                elif estado == 'tardanza':
                    asistencias_por_dia[dia] = 'tardanza'
                    total_tardanza += 1
                else:
                    asistencias_por_dia[dia] = ''
            
            # Calcular totales y porcentajes
            total_asistencias = total_presente + total_tardanza
            total_dias_trabajados = len(dias_trabajados)
            porcentaje = (total_asistencias / total_dias_trabajados * 100) if total_dias_trabajados > 0 else 0
            
            estudiantes_asistencia.append({
                'numero': idx,
                'estudiante': estudiante,
                'asistencias': asistencias_por_dia,
                'total_asistencias': total_asistencias,
                'porcentaje': round(porcentaje, 1)
            })
    
    # Generar lista de años (últimos 5 años + prÃ³ximos 2)
    anho_actual = timezone.now().year
    anhos_disponibles = list(range(anho_actual - 5, anho_actual + 3))
    
    context = {
        'materias': materias,
        'materia': materia,
        'materia_id': materia_id,
        'mes': mes,
        'anho': anho,
        'anhos_disponibles': anhos_disponibles,
        'nombre_mes': nombre_mes,
        'dias_trabajados': dias_trabajados,
        'estudiantes_asistencia': estudiantes_asistencia,
        'total_dias_trabajados': len(dias_trabajados),
        'titulo': 'Registro de Asistencia Mensual'
    }
    return render(request, 'est_forder/historial_asistencia.html', context)


# ===============================
# ¥ ASISTENCIA PERSONAL (PROFESORES/STAFF)
# ===============================

@login_required
def ponchar_asistencia_view(request):
    """Vista para la interfaz de ponchado con código de barras"""
    # Verificar que haya un año escolar activo
    try:
        anho_escolar = AnhoEscolar.objects.get(activo=True)
    except AnhoEscolar.DoesNotExist:
        messages.error(request, 'No hay un año escolar activo. Por favor, active un año escolar.')
        return redirect('plataform')
    
    context = {
        'titulo': 'Ponchar Asistencia',
        'anho_escolar': anho_escolar
    }
    return render(request, 'est_forder/ponchar_asistencia.html', context)


@login_required
def generar_codigos_barras(request):
    """Genera códigos de barras Ãºnicos para usuarios que no los tienen"""
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta función.')
        return redirect('plataform')
    
    if request.method == 'POST':
        # Generar códigos para usuarios sin código de barras
        usuarios_sin_codigo = CustomUser.objects.filter(
            codigo_barras__isnull=True,
            rol__in=['Profesor', 'Secretaria', 'Administrador', 'Coordinador', 'Bibliotecario', 'Estudiante']
        )
        
        import random
        import string
        
        generados = 0
        for usuario in usuarios_sin_codigo:
            # Generar código Ãºnico basado en ID y números aleatorios
            # Prefijo según rol: EST=Estudiante, EMP=Personal
            prefijo = 'EST' if usuario.rol == 'Estudiante' else 'EMP'
            while True:
                codigo = f"{prefijo}{usuario.id:04d}{random.randint(1000, 9999)}"
                if not CustomUser.objects.filter(codigo_barras=codigo).exists():
                    usuario.codigo_barras = codigo
                    usuario.save()
                    generados += 1
                    break
        
        messages.success(request, f'Se generaron {generados} códigos de barras.')
        return redirect('generar_codigos_barras')
    
    # Obtener parámetros de búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    rol_filtro = request.GET.get('rol', 'todos')
    
    # Listar usuarios con y sin código
    usuarios = CustomUser.objects.filter(
        rol__in=['Vendedor', 'Gerente', 'Secretaria', 'Administrador', 'Cliente']
    )
    
    # Aplicar búsqueda
    if busqueda:
        from django.db.models import Q
        usuarios = usuarios.filter(
            Q(first_name__icontains=busqueda) |
            Q(last_name__icontains=busqueda) |
            Q(codigo_barras__icontains=busqueda) |
            Q(cedula__icontains=busqueda) |
            Q(email__icontains=busqueda)
        )
    
    # Aplicar filtro por rol
    if rol_filtro != 'todos':
        usuarios = usuarios.filter(rol=rol_filtro)
    
    usuarios = usuarios.order_by('rol', 'first_name', 'last_name')
    
    # Conteo por rol
    roles_disponibles = ['Vendedor', 'Gerente', 'Secretaria', 'Administrador', 'Cliente']
    conteo_roles = {}
    for rol in roles_disponibles:
        conteo_roles[rol] = CustomUser.objects.filter(rol=rol).count()
    
    context = {
        'titulo': 'Gestionar Códigos de Barras',
        'usuarios': usuarios,
        'busqueda': busqueda,
        'rol_filtro': rol_filtro,
        'conteo_roles': conteo_roles,
        'total_usuarios': usuarios.count()
    }
    return render(request, 'est_forder/generar_codigos_barras.html', context)


@login_required
def ponchar_asistencia_api(request):
    """API para registrar entrada/salida automática con código de barras"""
    if request.method == 'POST':
        # Obtener período fiscal (opcional)
        anho_escolar = obtener_periodo_fiscal_actual()
        
        # Verificar rango de fechas solo si hay año fiscal
        if anho_escolar:
            fecha_hoy = timezone.now().date()
            if not (anho_escolar.fecha_inicio <= fecha_hoy <= anho_escolar.fecha_fin):
                return JsonResponse({
                    'success': False,
                    'error': f'La fecha actual está fuera del período fiscal {anho_escolar.nombre}'
                }, status=400)
        
        codigo_barras = request.POST.get('codigo_barras', '').strip()
        
        if not codigo_barras:
            return JsonResponse({
                'success': False,
                'error': 'Código de barras no proporcionado'
            }, status=400)
        
        try:
            # Buscar usuario por código de barras
            usuario = CustomUser.objects.get(codigo_barras=codigo_barras)
            
            # Verificar que sea personal o estudiante
            if usuario.rol not in ['Profesor', 'Secretaria', 'Administrador', 'Coordinador', 'Bibliotecario', 'Estudiante']:
                return JsonResponse({
                    'success': False,
                    'error': 'Este código no está autorizado para ponchar'
                }, status=403)
            
            # Obtener fecha y hora local (zona horaria configurada en settings)
            ahora_local = timezone.localtime(timezone.now())
            fecha_hoy = ahora_local.date()
            hora_actual = ahora_local.time()
            
            # Verificar si ya existe un registro para hoy
            asistencia = AsistenciaPersonal.objects.filter(
                usuario=usuario,
                fecha=fecha_hoy
            ).first()
            
            if asistencia:
                # Ya ponchÃ³ entrada, registrar salida
                if asistencia.hora_salida:
                    return JsonResponse({
                        'success': False,
                        'error': f'{usuario.get_full_name()} ya registrÃ³ salida hoy',
                        'nombre': usuario.get_full_name(),
                        'hora_entrada': asistencia.hora_entrada.strftime('%H:%M') if asistencia.hora_entrada else None,
                        'hora_salida': asistencia.hora_salida.strftime('%H:%M')
                    })
                else:
                    asistencia.hora_salida = hora_actual
                    asistencia.save()
                    return JsonResponse({
                        'success': True,
                        'tipo': 'salida',
                        'nombre': usuario.get_full_name(),
                        'rol': usuario.rol,
                        'hora': hora_actual.strftime('%H:%M:%S'),
                        'hora_entrada': asistencia.hora_entrada.strftime('%H:%M') if asistencia.hora_entrada else None
                    })
            else:
                # Primera vez, registrar entrada
                asistencia = AsistenciaPersonal.objects.create(
                    usuario=usuario,
                    fecha=fecha_hoy,
                    estado='presente',
                    hora_entrada=hora_actual,
                    registrado_por=request.user
                )
                
                # Si es estudiante, marcar asistencia en las materias del día
                if usuario.rol == 'Estudiante':
                    # Obtener día de la semana actual (0=Lunes, 1=Martes, ..., 4=Viernes)
                    dia_semana = fecha_hoy.weekday()
                    
                    # Mapear día de semana a campo del modelo
                    dias_map = {
                        0: 'lunes',
                        1: 'martes',
                        2: 'miercoles',
                        3: 'jueves',
                        4: 'viernes'
                    }
                    
                    # Si es un día de semana laboral (lunes a viernes)
                    if dia_semana in dias_map:
                        campo_dia = dias_map[dia_semana]
                        
                        # Obtener las materias del estudiante que se imparten hoy
                        from django.db.models import Q
                        filter_kwargs = {campo_dia: True}
                        
                        materias_hoy = Materia.objects.filter(
                            matriculas__estudiante=usuario,
                            matriculas__anho_escolar=anho_escolar,
                            **filter_kwargs
                        ).distinct()
                        
                        # Registrar asistencia en cada materia del día
                        materias_registradas = []
                        for materia in materias_hoy:
                            from .models import Asistencia
                            asistencia_materia, created = Asistencia.objects.get_or_create(
                                estudiante=usuario,
                                materia=materia,
                                fecha=fecha_hoy,
                                defaults={
                                    'estado': 'presente',
                                    'registrado_por': request.user
                                }
                            )
                            materias_registradas.append(materia.nombre)
                        
                        return JsonResponse({
                            'success': True,
                            'tipo': 'entrada',
                            'nombre': usuario.get_full_name(),
                            'rol': usuario.rol,
                            'hora': hora_actual.strftime('%H:%M:%S'),
                            'materias_registradas': materias_registradas,
                            'total_materias': len(materias_registradas)
                        })
                
                return JsonResponse({
                    'success': True,
                    'tipo': 'entrada',
                    'nombre': usuario.get_full_name(),
                    'rol': usuario.rol,
                    'hora': hora_actual.strftime('%H:%M:%S')
                })
                
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Código de barras no reconocido'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al procesar: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)


@login_required
def pasar_lista_personal(request):
    """Vista para registrar asistencia diaria del personal (Profesores/Staff)"""
    if request.user.rol not in ['Secretaria', 'Administrador', 'Director']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Verificar que haya un año escolar activo
    try:
        anho_escolar = AnhoEscolar.objects.get(activo=True)
    except AnhoEscolar.DoesNotExist:
        messages.error(request, 'No hay un año escolar activo. Por favor, active un año escolar.')
        return redirect('plataform')
    
    fecha_hoy = timezone.now().date()
    fecha_seleccionada = request.GET.get('fecha', fecha_hoy)
    rol_filtro = request.GET.get('rol', 'todos')  # Filtro por rol
    busqueda = request.GET.get('busqueda', '').strip()  # Búsqueda por nombre/apellido/código
    pagina = request.GET.get('pagina', 1)  # Número de página
    
    # Convertir string a date si es necesario
    if isinstance(fecha_seleccionada, str):
        try:
            fecha_seleccionada = datetime.strptime(fecha_seleccionada, '%Y-%m-%d').date()
        except:
            fecha_seleccionada = fecha_hoy
    
    # Validar que la fecha estÃ© dentro del año escolar
    if not (anho_escolar.fecha_inicio <= fecha_seleccionada <= anho_escolar.fecha_fin):
        messages.warning(request, f'La fecha seleccionada está fuera del año escolar {anho_escolar.nombre}.')
        fecha_seleccionada = fecha_hoy
    
    # Obtener todos los usuarios según el filtro de rol
    roles_validos = ['Profesor', 'Secretaria', 'Administrador', 'Coordinador', 'Bibliotecario', 'Estudiante']
    
    if rol_filtro == 'todos':
        usuarios = CustomUser.objects.filter(rol__in=roles_validos)
    else:
        usuarios = CustomUser.objects.filter(rol=rol_filtro)
    
    # Aplicar búsqueda si hay tÃ©rmino
    if busqueda:
        from django.db.models import Q
        usuarios = usuarios.filter(
            Q(first_name__icontains=busqueda) |
            Q(last_name__icontains=busqueda) |
            Q(codigo_barras__icontains=busqueda) |
            Q(cedula__icontains=busqueda) |
            Q(email__icontains=busqueda)
        )
    
    usuarios = usuarios.order_by('rol', 'first_name', 'last_name')
    
    if request.method == 'POST':
        # Procesar el formulario de asistencia
        registros_guardados = 0
        for persona in usuarios:
            estado = request.POST.get(f'estado_{persona.id}')
            if estado:
                hora_entrada = request.POST.get(f'hora_entrada_{persona.id}') or None
                hora_salida = request.POST.get(f'hora_salida_{persona.id}') or None
                observaciones = request.POST.get(f'observaciones_{persona.id}', '').strip()
                
                # Crear o actualizar asistencia
                asistencia, created = AsistenciaPersonal.objects.update_or_create(
                    usuario=persona,
                    fecha=fecha_seleccionada,
                    defaults={
                        'estado': estado,
                        'hora_entrada': hora_entrada if hora_entrada else None,
                        'hora_salida': hora_salida if hora_salida else None,
                        'observaciones': observaciones,
                        'registrado_por': request.user
                    }
                )
                registros_guardados += 1
        
        messages.success(request, f'Asistencia guardada exitosamente para {registros_guardados} personas.')
        return redirect(f'{request.path}?fecha={fecha_seleccionada}&rol={rol_filtro}&busqueda={busqueda}&pagina={pagina}')
    
    # PaginaciÃ³n
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    paginator = Paginator(usuarios, 50)  # 50 usuarios por página
    
    try:
        usuarios_paginados = paginator.page(pagina)
    except PageNotAnInteger:
        usuarios_paginados = paginator.page(1)
    except EmptyPage:
        usuarios_paginados = paginator.page(paginator.num_pages)
    
    # Obtener asistencias ya registradas para la fecha
    asistencias_existentes = AsistenciaPersonal.objects.filter(
        fecha=fecha_seleccionada
    ).select_related('usuario')
    
    # Crear diccionario de asistencias por usuario
    asistencias_dict = {a.usuario.id: a for a in asistencias_existentes}
    
    # Preparar datos para el template agrupados por rol
    usuarios_por_rol = {}
    for persona in usuarios_paginados:
        rol = persona.rol
        if rol not in usuarios_por_rol:
            usuarios_por_rol[rol] = []
        
        asistencia = asistencias_dict.get(persona.id)
        usuarios_por_rol[rol].append({
            'persona': persona,
            'asistencia': asistencia
        })
    
    # Contar totales por rol
    conteo_roles = {}
    for rol in roles_validos:
        conteo_roles[rol] = CustomUser.objects.filter(rol=rol).count()
    
    context = {
        'titulo': 'Pasar Lista - Personal y Estudiantes',
        'fecha_seleccionada': fecha_seleccionada,
        'fecha_hoy': fecha_hoy,
        'usuarios_por_rol': usuarios_por_rol,
        'usuarios_paginados': usuarios_paginados,
        'total_usuarios': usuarios.count(),
        'anho_escolar': anho_escolar,
        'rol_filtro': rol_filtro,
        'busqueda': busqueda,
        'conteo_roles': conteo_roles,
        'roles_disponibles': roles_validos
    }
    return render(request, 'est_forder/pasar_lista_personal.html', context)


@login_required
def historial_asistencia_personal(request):
    """Vista para ver el historial de asistencia del personal en formato mensual"""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Verificar que haya un año escolar activo
    try:
        anho_escolar = AnhoEscolar.objects.get(activo=True)
    except AnhoEscolar.DoesNotExist:
        messages.error(request, 'No hay un año escolar activo.')
        return redirect('plataform')
    
    from calendar import monthrange
    import locale
    
    # Intentar establecer locale en español
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
        except:
            pass
    
    # Obtener mes y año de la URL o usar el actual
    hoy = timezone.now().date()
    mes = int(request.GET.get('mes', hoy.month))
    anho = int(request.GET.get('anho', hoy.year))
    
    # Validar mes
    if mes < 1 or mes > 12:
        mes = hoy.month
    
    # Obtener nombre del mes
    fecha_ejemplo = datetime(anho, mes, 1)
    nombre_mes = fecha_ejemplo.strftime('%B').capitalize()
    
    # Calcular días del mes
    num_dias = monthrange(anho, mes)[1]
    dias_trabajados = list(range(1, num_dias + 1))
    
    # Obtener personal
    personal = CustomUser.objects.filter(
        rol__in=['Profesor', 'Secretaria', 'Administrador']
    ).order_by('first_name', 'last_name')
    
    # Obtener todas las asistencias del mes
    asistencias = AsistenciaPersonal.objects.filter(
        fecha__year=anho,
        fecha__month=mes
    ).select_related('usuario')
    
    # Crear diccionario de asistencias por usuario y día
    asistencias_dict = {}
    for a in asistencias:
        if a.usuario.id not in asistencias_dict:
            asistencias_dict[a.usuario.id] = {}
        asistencias_dict[a.usuario.id][a.fecha.day] = a.estado
    
    # Preparar datos para el template
    personal_asistencia = []
    for idx, persona in enumerate(personal, 1):
        asistencias_mes = asistencias_dict.get(persona.id, {})
        
        # Contar asistencias
        total_presente = sum(1 for estado in asistencias_mes.values() if estado == 'presente')
        total_ausente = sum(1 for estado in asistencias_mes.values() if estado == 'ausente')
        total_tardanza = sum(1 for estado in asistencias_mes.values() if estado == 'tardanza')
        total_permiso = sum(1 for estado in asistencias_mes.values() if estado == 'permiso')
        
        personal_asistencia.append({
            'numero': idx,
            'persona': persona,
            'asistencias': asistencias_mes,
            'total_presente': total_presente,
            'total_ausente': total_ausente,
            'total_tardanza': total_tardanza,
            'total_permiso': total_permiso,
            'total_asistencias': len(asistencias_mes)
        })
    
    # Años disponibles
    anhos_disponibles = list(range(hoy.year - 2, hoy.year + 2))
    
    context = {
        'titulo': 'Historial de Asistencia Personal',
        'mes': mes,
        'anho': anho,
        'nombre_mes': nombre_mes,
        'dias_trabajados': dias_trabajados,
        'personal_asistencia': personal_asistencia,
        'total_dias_trabajados': len(dias_trabajados),
        'anhos_disponibles': anhos_disponibles,
        'anho_escolar': anho_escolar
    }
    return render(request, 'est_forder/historial_asistencia_personal.html', context)


@login_required
def historial_asistencia_general(request):
    """Vista para ver estadísticas generales de asistencia del personal de ventas"""
    if request.user.rol not in ['Secretaria', 'Administrador', 'Gerente']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Verificar que haya un año escolar activo (período fiscal)
    try:
        anho_escolar = AnhoEscolar.objects.get(activo=True)
    except AnhoEscolar.DoesNotExist:
        messages.error(request, 'No hay un período fiscal activo.')
        return redirect('plataform')
    
    from calendar import monthrange
    from django.db.models import Count, Q
    
    # Obtener mes y año de la URL o usar el actual
    hoy = timezone.now().date()
    mes = int(request.GET.get('mes', hoy.month))
    anho = int(request.GET.get('anho', hoy.year))
    fecha = request.GET.get('fecha', None)
    
    # Si se proporciona una fecha específica
    if fecha:
        try:
            fecha_seleccionada = datetime.strptime(fecha, '%Y-%m-%d').date()
        except:
            fecha_seleccionada = hoy
    else:
        fecha_seleccionada = None
    
    # Validar mes
    if mes < 1 or mes > 12:
        mes = hoy.month
    
    # Obtener nombre del mes
    fecha_ejemplo = datetime(anho, mes, 1)
    nombre_mes = fecha_ejemplo.strftime('%B').capitalize()
    
    # Estadísticas de personal (roles de ventas)
    personal_total = CustomUser.objects.filter(
        rol__in=['Vendedor', 'Gerente', 'Secretaria', 'Administrador']
    ).count()
    
    # Asistencias del mes para personal
    asistencias_personal_mes = AsistenciaPersonal.objects.filter(
        fecha__year=anho,
        fecha__month=mes,
        usuario__rol__in=['Vendedor', 'Gerente', 'Secretaria', 'Administrador']
    ).values('fecha').annotate(
        total=Count('id'),
        presentes=Count('id', filter=Q(estado='presente')),
        ausentes=Count('id', filter=Q(estado='ausente')),
        tardanzas=Count('id', filter=Q(estado='tardanza'))
    ).order_by('fecha')
    
    # Estadísticas por departamento/rol
    roles_stats = []
    roles_disponibles = ['Vendedor', 'Gerente', 'Secretaria', 'Administrador']
    
    for rol in roles_disponibles:
        personal_rol = CustomUser.objects.filter(rol=rol).count()
        
        if personal_rol > 0:
            # Asistencias del mes para este rol
            asistencias_rol = AsistenciaPersonal.objects.filter(
                fecha__year=anho,
                fecha__month=mes,
                usuario__rol=rol
            ).count()
            
            presentes_rol = AsistenciaPersonal.objects.filter(
                fecha__year=anho,
                fecha__month=mes,
                usuario__rol=rol,
                estado='presente'
            ).count()
            
            masculino_rol = CustomUser.objects.filter(rol=rol, genero='M').count()
            femenino_rol = CustomUser.objects.filter(rol=rol, genero='F').count()
            
            roles_stats.append({
                'rol': rol,
                'total': personal_rol,
                'masculino': masculino_rol,
                'femenino': femenino_rol,
                'asistencias': asistencias_rol,
                'presentes': presentes_rol,
                'porcentaje': round((presentes_rol / asistencias_rol * 100) if asistencias_rol > 0 else 0, 1)
            })
    
    # Si se solicita una fecha específica, mostrar detalles
    detalles_fecha = None
    if fecha_seleccionada:
        # Personal del día
        personal_dia = AsistenciaPersonal.objects.filter(
            fecha=fecha_seleccionada,
            usuario__rol__in=['Vendedor', 'Gerente', 'Secretaria', 'Administrador']
        ).select_related('usuario')
        
        # Estadísticas por rol del día
        roles_dia = []
        for rol in roles_disponibles:
            personal_rol_dia = AsistenciaPersonal.objects.filter(
                fecha=fecha_seleccionada,
                usuario__rol=rol
            )
            
            total_dia = personal_rol_dia.count()
            if total_dia > 0:
                presentes_dia = personal_rol_dia.filter(estado='presente').count()
                masculino_dia = personal_rol_dia.filter(usuario__genero='M').count()
                femenino_dia = personal_rol_dia.filter(usuario__genero='F').count()
                
                roles_dia.append({
                    'rol': rol,
                    'total': total_dia,
                    'presentes': presentes_dia,
                    'masculino': masculino_dia,
                    'femenino': femenino_dia
                })
        
        detalles_fecha = {
            'fecha': fecha_seleccionada,
            'personal': personal_dia,
            'roles': roles_dia
        }
    
    # Años disponibles
    anhos_disponibles = list(range(hoy.year - 2, hoy.year + 2))
    
    context = {
        'titulo': 'Estadísticas de Asistencia Personal',
        'mes': mes,
        'anho': anho,
        'nombre_mes': nombre_mes,
        'anhos_disponibles': anhos_disponibles,
        'personal_total': personal_total,
        'asistencias_personal_mes': asistencias_personal_mes,
        'roles_stats': roles_stats,
        'detalles_fecha': detalles_fecha,
        'fecha_seleccionada': fecha_seleccionada,
        'anho_escolar': anho_escolar
    }
    return render(request, 'est_forder/historial_asistencia_general.html', context)


# ===========================
# SISTEMA DE COBROS Y PAGOS
# ===========================

def obtener_o_crear_cliente_generico():
    """
    Obtiene o crea automáticamente el usuario genÃ©rico 'cliente' para ventas rÃ¡pidas.
    Este usuario se usa cuando no se tiene un estudiante especÃ­fico registrado.
    """
    try:
        cliente = CustomUser.objects.filter(
            rol='Cliente',
            first_name='Cliente',
            last_name='Generico'
        ).first()
        
        if cliente:
            print(f"✓ Cliente genérico encontrado (ID: {cliente.id})")
            return cliente
        
        # Si no existe, crear el usuario genérico automáticamente
        print("⚠ Cliente genérico no encontrado, creando uno nuevo...")
        
        # Usar email fijo para evitar duplicados
        email = "cliente.generico@ventas.local"
        
        # Verificar si ya existe un usuario con ese email
        usuario_existente = CustomUser.objects.filter(email=email).first()
        if usuario_existente:
            print(f"✓ Usuario con email {email} ya existe (ID: {usuario_existente.id}), usando ese...")
            usuario_existente.first_name = 'Cliente'
            usuario_existente.last_name = 'Generico'
            usuario_existente.rol = 'Cliente'
            usuario_existente.tipo_cliente = 'Minorista'
            usuario_existente.telefono = '000-000-0000'
            usuario_existente.save()
            return usuario_existente
        
        cliente = CustomUser.objects.create(
            email=email,
            first_name='Cliente',
            last_name='Generico',
            rol='Cliente',
            is_active=True,
            is_staff=False,
            is_superuser=False,
            tipo_cliente='Minorista',
            telefono='000-000-0000',
        )
        
        cliente.set_password("ClienteGenerico2026!")
        cliente.save()
        
        print(f"✓ Usuario genérico Cliente Generico creado con ID: {cliente.id}")
        
        
        return cliente
    except Exception as e:
        print(f"Error al obtener/crear cliente genÃ©rico: {str(e)}")
        return None

@login_required
def cobros_dashboard(request):
    """Dashboard principal del sistema de cobros"""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from .models import Pago, ConceptoPago, Factura
    from django.db.models import Sum, Q
    
    # Obtener período fiscal (opcional)
    anho_escolar = obtener_periodo_fiscal_actual()
    
    # Estadísticas basadas en Facturas
    # Si hay año fiscal, filtrar por él. Si no, mostrar todas las facturas
    if anho_escolar:
        facturas_anho = Factura.objects.filter(anho_escolar=anho_escolar).exclude(estado='anulada')
        periodo_nombre = anho_escolar.nombre
    else:
        # Sin año fiscal: mostrar facturas del año calendario actual
        anho_actual = timezone.now().year
        facturas_anho = Factura.objects.filter(
            fecha_emision__year=anho_actual
        ).exclude(estado='anulada')
        periodo_nombre = f"Año {anho_actual}"
    
    # Total de facturas
    total_facturas = facturas_anho.count()
    
    # Facturas por estado
    facturas_pagadas = facturas_anho.filter(estado='pagada').count()
    facturas_pendientes = facturas_anho.filter(Q(estado='pendiente') | Q(estado='parcial')).count()
    
    # Monto total recaudado (solo facturas pagadas completamente)
    total_recaudado = facturas_anho.filter(estado='pagada').aggregate(
        total=Sum('monto_pagado')
    )['total'] or 0
    
    # Monto total por cobrar (saldo pendiente de facturas no pagadas)
    facturas_no_pagadas = facturas_anho.exclude(estado='pagada')
    total_por_cobrar = sum(
        (factura.total - factura.monto_pagado) 
        for factura in facturas_no_pagadas
    )
    
    # Monto total de facturas (incluyendo todo)
    monto_total_facturas = facturas_anho.aggregate(total=Sum('total'))['total'] or 0
    
    # Facturas con mora
    facturas_vencidas = facturas_anho.filter(
        Q(estado='pendiente') | Q(estado='parcial')
    ).count()
    
    # Facturas parciales
    facturas_parcial = facturas_anho.filter(estado='parcial').count()
    
    # Facturas anuladas
    if anho_escolar:
        facturas_anuladas = Factura.objects.filter(anho_escolar=anho_escolar, estado='anulada').count()
    else:
        facturas_anuladas = Factura.objects.filter(
            fecha_emision__year=timezone.now().year,
            estado='anulada'
        ).count()
    
    # Promedio de factura
    promedio_factura = monto_total_facturas / total_facturas if total_facturas > 0 else 0
    
    # Porcentaje de cobro
    porcentaje_cobrado = (total_recaudado / monto_total_facturas * 100) if monto_total_facturas > 0 else 0
    
    # Ãltimas facturas
    ultimas_facturas = facturas_anho.select_related(
        'cliente', 'anho_escolar'
    ).order_by('-fecha_emision')[:10]
    
    # Estadísticas de Pagos (sistema antiguo, para compatibilidad)
    if anho_escolar:
        total_pagos = Pago.objects.filter(anho_escolar=anho_escolar).count()
    else:
        total_pagos = Pago.objects.filter(fecha__year=timezone.now().year).count()
    
    # Obtener o crear el estudiante genérico "cliente"
    cliente_generico = obtener_o_crear_cliente_generico()
    
    context = {
        'titulo': 'Sistema de Cobros',
        'anho_escolar': anho_escolar,
        'periodo_nombre': periodo_nombre,
        # Estadísticas de Facturas
        'total_facturas': total_facturas,
        'facturas_pagadas': facturas_pagadas,
        'facturas_pendientes': facturas_pendientes,
        'facturas_vencidas': facturas_vencidas,
        'facturas_parcial': facturas_parcial,
        'facturas_anuladas': facturas_anuladas,
        'total_recaudado': total_recaudado,
        'total_por_cobrar': total_por_cobrar,
        'monto_total_facturas': monto_total_facturas,
        'promedio_factura': promedio_factura,
        'porcentaje_cobrado': porcentaje_cobrado,
        'ultimas_facturas': ultimas_facturas,
        # Para compatibilidad con template existente
        'total_pagos': total_facturas,  # Usar facturas como "pagos"
        'pagos_completados': facturas_pagadas,
        'pagos_pendientes': facturas_pendientes,
        'ultimos_pagos': ultimas_facturas,  # Usar facturas en lugar de pagos
        'cliente_generico': cliente_generico,
    }
    return render(request, 'cobros/dashboard.html', context)


@login_required
def buscar_estudiante_cobro(request):
    """Buscar estudiante o familia para asignar pagos"""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Obtener año escolar activo
    try:
        anho_escolar = AnhoEscolar.objects.get(activo=True)
    except AnhoEscolar.DoesNotExist:
        messages.error(request, 'No hay un año escolar activo.')
        return redirect('plataform')
    
    # Búsqueda
    query = request.GET.get('q', '').strip()
    grado = request.GET.get('grado', '').strip()
    seccion = request.GET.get('seccion', '').strip()
    
    # REDIRECCIÃN AUTOMÃTICA: Si es un código de barras exacto de estudiante
    if query and not grado and not seccion:
        try:
            estudiante_exacto = CustomUser.objects.get(
                codigo_barras__iexact=query,
                rol='Estudiante',
                is_active=True
            )
            # Redirigir directamente a la vista rÃ¡pida de facturaciÃ³n
            return redirect(f'/facturas/nueva/?estudiante_id={estudiante_exacto.id}')
        except CustomUser.DoesNotExist:
            pass
        except CustomUser.MultipleObjectsReturned:
            pass
    
    # REDIRECCIÃN AUTOMÃTICA: Si es un código de familia exacto
    from .models import GrupoFamiliar
    if query and not grado and not seccion:
        try:
            familia_exacta = GrupoFamiliar.objects.get(
                codigo_familia__iexact=query,
                activo=True
            )
            # Redirigir directamente a facturar familia
            return redirect('grupo_familiar_facturar', grupo_id=familia_exacta.id)
        except GrupoFamiliar.DoesNotExist:
            pass
        except GrupoFamiliar.MultipleObjectsReturned:
            pass
    
    # Buscar familias por código o apellido (búsqueda parcial)
    familias = []
    if query:
        familias = GrupoFamiliar.objects.filter(
            Q(codigo_familia__icontains=query) |
            Q(apellido_familia__icontains=query),
            activo=True
        ).annotate(
            num_estudiantes=Count('estudiantes')
        ).order_by('apellido_familia')[:5]
    
    estudiantes = CustomUser.objects.filter(rol='Estudiante', is_active=True)
    
    if query:
        estudiantes = estudiantes.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(cedula__icontains=query) |
            Q(codigo_barras__icontains=query)
        )
    
    if grado:
        estudiantes = estudiantes.filter(grado=grado)
    
    if seccion:
        estudiantes = estudiantes.filter(seccion=seccion)
    
    estudiantes = estudiantes.order_by('first_name', 'last_name')
    
    # PaginaciÃ³n
    paginator = Paginator(estudiantes, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener grados y secciones Ãºnicas
    grados_disponibles = CustomUser.objects.filter(
        rol='Estudiante', 
        grado__isnull=False
    ).values_list('grado', flat=True).distinct().order_by('grado')
    
    secciones_disponibles = CustomUser.objects.filter(
        rol='Estudiante', 
        seccion__isnull=False
    ).values_list('seccion', flat=True).distinct().order_by('seccion')
    
    context = {
        'titulo': 'Buscar Estudiante o Familia para Cobro',
        'anho_escolar': anho_escolar,
        'estudiantes': page_obj,
        'familias': familias,
        'query': query,
        'grado': grado,
        'seccion': seccion,
        'grados_disponibles': grados_disponibles,
        'secciones_disponibles': secciones_disponibles,
    }
    return render(request, 'cobros/buscar_estudiante.html', context)


# SISTEMA DE PAGO SIMPLE OBSOLETO - REEMPLAZADO POR FACTURAS
# Las siguientes funciones ya no se usan, conservadas solo como referencia histÃ³rica
"""
@login_required
def asignar_pago_estudiante(request, estudiante_id):
    # Esta vista fue reemplazada por el sistema de facturaciÃ³n
    messages.warning(request, 'El sistema de pago simple ha sido reemplazado por el sistema de facturas.')
    return redirect('factura_crear', estudiante_id=estudiante_id)

@login_required
def ver_pagos_estudiante(request, estudiante_id):
    # Esta vista fue reemplazada por facturas_cliente
    messages.warning(request, 'El sistema de pago simple ha sido reemplazado por el sistema de facturas.')
    return redirect('facturas_cliente', cliente_id=estudiante_id)
    
    # Código original comentado:
    saldo_pendiente = total_adeudado - total_pagado
    
    pagos_pendientes = pagos.filter(estado='pendiente').count()
    pagos_completados = pagos.filter(estado='pagado').count()
    
    context = {
        'titulo': f'Pagos de {estudiante.get_full_name()}',
        'anho_escolar': anho_escolar,
        'estudiante': estudiante,
        'pagos': pagos,
        'total_adeudado': total_adeudado,
        'total_pagado': total_pagado,
        'saldo_pendiente': saldo_pendiente,
        'pagos_pendientes': pagos_pendientes,
        'pagos_completados': pagos_completados,
    }
    return render(request, 'cobros/ver_pagos_estudiante.html', context)
"""


# ===========================
# VISTAS DE FACTURACIÃN
# ===========================

@login_required
def facturas_list(request):
    """Lista todas las facturas"""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from .models import Factura
    from django.db.models import Q
    
    # Obtener período fiscal (opcional)
    anho_escolar = obtener_periodo_fiscal_actual()
    
    # Filtros
    estado = request.GET.get('estado', '')
    search = request.GET.get('search', '')
    
    # Si hay año fiscal, filtrar por él. Si no, mostrar del año actual
    if anho_escolar:
        facturas = Factura.objects.filter(anho_escolar=anho_escolar).select_related('cliente')
        periodo_nombre = anho_escolar.nombre
    else:
        anho_actual = timezone.now().year
        facturas = Factura.objects.filter(
            fecha_emision__year=anho_actual
        ).select_related('cliente')
        periodo_nombre = f"Año {anho_actual}"
    
    if estado:
        facturas = facturas.filter(estado=estado)
    
    if search:
        facturas = facturas.filter(
            Q(numero_factura__icontains=search) |
            Q(cliente__first_name__icontains=search) |
            Q(cliente__last_name__icontains=search) |
            Q(cliente__cedula__icontains=search)
        )
    
    facturas = facturas.order_by('-fecha_emision')
    
    # PaginaciÃ³n
    from django.core.paginator import Paginator
    paginator = Paginator(facturas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'titulo': 'Facturas',
        'anho_escolar': anho_escolar,
        'periodo_nombre': periodo_nombre,
        'page_obj': page_obj,
        'estado': estado,
        'search': search,
    }
    return render(request, 'cobros/facturas_list.html', context)


@login_required

def factura_crear_nueva(request):
    """Crear una nueva factura - Búsqueda de estudiante y creación integradas"""
    if request.user.rol not in ['Secretaria', 'Administrador', 'Vendedor', 'Gerente']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')

    from .models import Factura, DetalleFactura, ConceptoPago, CodigoAnulacion, PagoFactura
    from django.utils import timezone
    from django.db.models import Q
    from decimal import Decimal
    import json

    # Obtener período fiscal (opcional)
    anho_escolar = obtener_periodo_fiscal_actual()
    if not anho_escolar:
        # Si no hay año fiscal, crear uno automáticamente para el año actual
        anho_actual = timezone.now().year
        anho_escolar, created = AnhoEscolar.objects.get_or_create(
            nombre=f"Año {anho_actual}",
            defaults={
                'fecha_inicio': timezone.datetime(anho_actual, 1, 1).date(),
                'fecha_fin': timezone.datetime(anho_actual, 12, 31).date(),
                'activo': True
            }
        )
        if created:
            messages.info(request, f'Se creó automáticamente el período fiscal {anho_escolar.nombre}.')


    # --- Seguridad para copiar factura (editar) ---
    copiar_factura_id = request.GET.get('copiar_factura')
    detalles_json = None
    cliente_copiado = None
    monto_pagado_copiado = None
    if copiar_factura_id:
        # Si no se ha enviado el código, mostrar formulario de código
        if request.method == 'GET' and not request.GET.get('codigo_seguridad_validado'):
            if request.GET.get('codigo_intento'):
                codigo_intento = request.GET.get('codigo_intento').strip()
                if not CodigoAnulacion.validar_codigo(codigo_intento):
                    return render(request, 'cobros/seguridad_codigo.html', {
                        'error': 'Código incorrecto. Intente nuevamente.',
                        'copiar_factura_id': copiar_factura_id
                    })
                # Código correcto, continuar y marcar validado
                params = request.GET.copy()
                params['codigo_seguridad_validado'] = '1'
                return redirect(f"{request.path}?" + params.urlencode())
            # Mostrar formulario de código
            return render(request, 'cobros/seguridad_codigo.html', {
                'copiar_factura_id': copiar_factura_id
            })
        # Si el código fue validado, cargar detalles de la factura original
        try:
            factura_origen = Factura.objects.get(id=copiar_factura_id)
            detalles = []
            for det in factura_origen.detalles.all():
                if det.articulo:
                    detalles.append({
                        'articulo_id': det.articulo.id,
                        'nombre': det.articulo.nombre,
                        'codigo_barras': det.articulo.codigo_barras,
                        'precio': float(det.precio_unitario),
                        'cantidad': float(det.cantidad),
                        'descuento': float(det.descuento),
                        'stock_actual': getattr(det.articulo, 'stock_actual', 999),
                        'tipo_articulo': det.articulo.tipo,
                        'aplica_itbis': getattr(det.articulo, 'aplica_itbis', False),
                    })
                elif det.concepto:
                    # Incluir TODOS los conceptos, incluyendo mora
                    detalles.append({
                        'concepto_id': det.concepto.id,
                        'nombre': det.concepto.nombre,
                        'cantidad': float(det.cantidad),
                        'precio': float(det.precio_unitario),
                        'descuento': float( det.descuento),
                        'mes': det.mes,
                        'anio': det.anio,
                    })
            detalles_json = json.dumps(detalles)
            # Copiar el cliente/estudiante de la factura original
            cliente_copiado = factura_origen.cliente.id if factura_origen.cliente else None
            monto_pagado_copiado = float(factura_origen.monto_pagado) if factura_origen.monto_pagado is not None else None
            print(f"DEBUG monto_pagado_copiado: {monto_pagado_copiado}")  # DEBUG       
        except Factura.DoesNotExist:
            detalles_json = None
            cliente_copiado = None
    
    estudiante_seleccionado = None
    # Si se está copiando una factura, seleccionar el cliente automáticamente
    if not request.GET.get('estudiante_id') and cliente_copiado:
        request.GET = request.GET.copy()
        request.GET['estudiante_id'] = str(cliente_copiado)
    
    # Si viene cliente_id, usar ese en lugar de estudiante_id (para sistema de ventas)
    if request.GET.get('cliente_id') and not request.GET.get('estudiante_id'):
        request.GET = request.GET.copy()
        request.GET['estudiante_id'] = request.GET['cliente_id']
    
    # Búsqueda de estudiante/cliente
    buscar = request.GET.get('buscar', '')
    estudiantes_encontrados = []
    familias_encontradas = []
    
    # REDIRECCIÃN AUTOMÃTICA: Si es un código de barras exacto de estudiante
    if buscar and not request.GET.get('estudiante_id'):
        try:
            estudiante_exacto = CustomUser.objects.get(
                codigo_barras__iexact=buscar,
                rol__in=['Estudiante', 'Cliente'],
                is_active=True
            )
            # Redirigir con el estudiante seleccionado
            return redirect(f'/facturas/nueva/?estudiante_id={estudiante_exacto.id}')
        except CustomUser.DoesNotExist:
            pass
        except CustomUser.MultipleObjectsReturned:
            pass
    
    # REDIRECCIÃN AUTOMÃTICA: Si es un código de familia exacto
    from .models import GrupoFamiliar
    if buscar and not request.GET.get('estudiante_id'):
        try:
            familia_exacta = GrupoFamiliar.objects.get(
                codigo_familia__iexact=buscar,
                activo=True
            )
            # Redirigir directamente a facturar familia
            return redirect('grupo_familiar_facturar', grupo_id=familia_exacta.id)
        except GrupoFamiliar.DoesNotExist:
            pass
        except GrupoFamiliar.MultipleObjectsReturned:
            pass
    
    # Búsqueda de estudiantes y familias (si no hubo redirección)
    if buscar:
        # Buscar estudiantes y clientes
        estudiantes_encontrados = CustomUser.objects.filter(
            rol__in=['Estudiante', 'Cliente'],
            is_active=True
        ).filter(
            Q(first_name__icontains=buscar) |
            Q(last_name__icontains=buscar) |
            Q(codigo_barras__icontains=buscar) |
            Q(cedula__icontains=buscar) |
            Q(email__icontains=buscar)
        )[:10]
        
        # Buscar familias - DESHABILITADO: GrupoFamiliar está deprecated
        # TODO: Reemplazar con búsqueda de ClienteCorporativo cuando se migre
        # familias_encontradas = GrupoFamiliar.objects.filter(
        #     Q(codigo_familia__icontains=buscar) |
        #     Q(apellido_familia__icontains=buscar),
        #     activo=True
        # ).order_by('apellido_familia')[:5]
    
    # Estudiante seleccionado
    estudiante_id = request.GET.get('estudiante_id', '')
    meses_pagados = []  # Lista de meses ya pagados por el estudiante (formato: "mes-anio")
    
    # Obtener cliente genÃ©rico para comparación
    cliente_generico = obtener_o_crear_cliente_generico()
    es_cliente_generico = False
    
    if estudiante_id:
        try:
            estudiante_seleccionado = CustomUser.objects.get(id=estudiante_id, rol__in=['Estudiante', 'Cliente'])
            
            # Verificar si es el cliente genÃ©rico
            if cliente_generico and estudiante_seleccionado.id == cliente_generico.id:
                es_cliente_generico = True
            
            # Obtener SOLO mensualidades pagadas (mismo criterio que usa JavaScript para validar)
            # Solo conceptos con tipo='mensualidad' y que tengan mes/año asignado
            detalles_pagados = DetalleFactura.objects.filter(
                factura__cliente=estudiante_seleccionado,
                factura__anho_escolar=anho_escolar,
                concepto__tipo='mensualidad',
                mes__isnull=False,
                anio__isnull=False
            ).values_list('mes', 'anio')
            
            # Convertir a set para eliminar duplicados, luego a lista
            # Esto asegura que contamos cada mes solo una vez
            meses_unicos = set(detalles_pagados)
            meses_pagados = [f"{mes}-{anio}" for mes, anio in meses_unicos]
            
            print(f"DEBUG - Meses encontrados en BD: {len(detalles_pagados)}, Ãnicos: {len(meses_unicos)}, Lista: {sorted(meses_pagados)}")

            # Cargar tarifas activas del estudiante (mensualidad, inscripcion y transporte)
            from .models import TarifaEstudiante
            tarifas = TarifaEstudiante.objects.filter(
                estudiante=estudiante_seleccionado, 
                activo=True
            ).select_related('concepto')
            
            tarifa_mens = tarifas.filter(concepto__tipo='mensualidad').first()
            tarifa_insc = tarifas.filter(concepto__tipo='inscripcion').first()
            tarifa_trans = tarifas.filter(concepto__tipo='transporte').first()
            
            import json
            tarifa_data = {
                'mensualidad': None,
                'inscripcion': None,
                'transporte': None,
            }
            
            if tarifa_mens:
                tarifa_data['mensualidad'] = {
                    'id': tarifa_mens.id,
                    'concepto_id': tarifa_mens.concepto.id if tarifa_mens.concepto else None,
                    'monto': float(tarifa_mens.monto),
                    'concepto_nombre': tarifa_mens.concepto.nombre if tarifa_mens.concepto else None,
                }
            if tarifa_insc:
                tarifa_data['inscripcion'] = {
                    'id': tarifa_insc.id,
                    'concepto_id': tarifa_insc.concepto.id if tarifa_insc.concepto else None,
                    'monto': float(tarifa_insc.monto),
                    'concepto_nombre': tarifa_insc.concepto.nombre if tarifa_insc.concepto else None,
                }
            if tarifa_trans:
                tarifa_data['transporte'] = {
                    'id': tarifa_trans.id,
                    'concepto_id': tarifa_trans.concepto.id if tarifa_trans.concepto else None,
                    'monto': float(tarifa_trans.monto),
                    'concepto_nombre': tarifa_trans.concepto.nombre if tarifa_trans.concepto else None,
                    'observaciones': tarifa_trans.observaciones or '',
                }
            tarifa_json = json.dumps(tarifa_data)

            
        except CustomUser.DoesNotExist:
            pass
    
    # Crear factura
    if request.method == 'POST':
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("=" * 80)
            logger.warning("DEBUG POST DATA RECIBIDO:")
            logger.warning(f"POST keys: {list(request.POST.keys())}")
            logger.warning(f"POST data completo: {dict(request.POST)}")
            logger.warning("=" * 80)

            estudiante_id_post = request.POST.get('estudiante_id_hidden', '')
            if not estudiante_id_post:
                messages.error(request, 'Debes seleccionar un cliente.')
                return redirect('factura_crear_nueva')

            estudiante_post = CustomUser.objects.get(id=estudiante_id_post, rol__in=['Estudiante', 'Cliente'])
            fecha_vencimiento = request.POST.get('fecha_vencimiento')
            
            # Si no se especifica fecha de vencimiento, calcularla automáticamente
            # basada en el día de vencimiento del grupo familiar
            if not fecha_vencimiento and hasattr(estudiante_post, 'grupo_familiar') and estudiante_post.grupo_familiar:
                from datetime import date
                from calendar import monthrange
                
                dia_vencimiento = estudiante_post.grupo_familiar.dia_vencimiento
                hoy = date.today()
                
                # Si ya pasÃ³ el día de vencimiento este mes, usar el prÃ³ximo mes
                if hoy.day > dia_vencimiento:
                    # PrÃ³ximo mes
                    if hoy.month == 12:
                        fecha_base = date(hoy.year + 1, 1, 1)
                    else:
                        fecha_base = date(hoy.year, hoy.month + 1, 1)
                else:
                    # Este mes
                    fecha_base = hoy
                
                # Ajustar el día, manejando meses con menos días
                try:
                    fecha_vencimiento = fecha_base.replace(day=dia_vencimiento).strftime('%Y-%m-%d')
                except ValueError:
                    # Si el mes no tiene ese día (ej: 31 en febrero), usar el último día del mes
                    ultimo_dia = monthrange(fecha_base.year, fecha_base.month)[1]
                    fecha_vencimiento = fecha_base.replace(day=ultimo_dia).strftime('%Y-%m-%d')
            
            observaciones = request.POST.get('observaciones', '')
            descuento_factura = Decimal(request.POST.get('descuento_factura', 0))
            impuesto_factura = Decimal(request.POST.get('impuesto', 0))
            monto_pagado = Decimal(request.POST.get('monto_pagado', 0))
            metodo_pago = request.POST.get('metodo_pago', 'efectivo')
            referencia_pago = request.POST.get('referencia_pago', '')

            observaciones_completas = observaciones
            if referencia_pago:
                if observaciones_completas:
                    observaciones_completas += f" | Ref: {referencia_pago}"
                else:
                    observaciones_completas = f"Ref: {referencia_pago}"

            # Si se está editando una factura (copiar_factura), actualizar la original
            factura_id_editar = request.GET.get('copiar_factura')
            factura = None
            if factura_id_editar:
                try:
                    factura = Factura.objects.get(id=factura_id_editar)
                    # Actualizar campos principales
                    factura.cliente = estudiante_post
                    factura.anho_escolar = anho_escolar
                    factura.fecha_vencimiento = fecha_vencimiento if fecha_vencimiento else None
                    factura.descuento = descuento_factura
                    factura.impuesto = impuesto_factura
                    factura.monto_pagado = monto_pagado
                    factura.metodo_pago = metodo_pago
                    factura.observaciones = observaciones_completas
                    factura.save()
                    # Eliminar detalles anteriores
                    factura.detalles.all().delete()
                except Factura.DoesNotExist:
                    factura = None
            if not factura:
                factura = Factura.objects.create(
                    cliente=estudiante_post,
                    anho_escolar=anho_escolar,
                    fecha_vencimiento=fecha_vencimiento if fecha_vencimiento else None,
                    descuento=descuento_factura,
                    impuesto=impuesto_factura,
                    monto_pagado=monto_pagado,
                    metodo_pago=metodo_pago,
                    observaciones=observaciones_completas,
                    creado_por=request.user
                )
            
            # Agregar detalles
            conceptos_ids = request.POST.getlist('concepto_id[]')
            articulos_ids = request.POST.getlist('articulo_id[]')  # Nuevo: para artículos
            cantidades = request.POST.getlist('cantidad[]')
            precios = request.POST.getlist('precio[]')
            descuentos = request.POST.getlist('descuento[]')
            meses = request.POST.getlist('mes[]')
            anios = request.POST.getlist('anio[]')
            
            print(f"DEBUG - Conceptos recibidos: {len(conceptos_ids)}")
            print(f"DEBUG - Artículos recibidos: {len(articulos_ids)}")
            print(f"DEBUG - IDs Conceptos: {conceptos_ids}")
            print(f"DEBUG - IDs Artículos: {articulos_ids}")
            
            # Variable para acumular mora de mensualidades vencidas
            mora_acumulada = Decimal('0')
            mensualidades_vencidas_info = []
            
            # VALIDAR QUE HAYA AL MENOS UN DETALLE
            max_items = max(len(conceptos_ids), len(articulos_ids))
            if max_items == 0:
                factura.delete()
                messages.error(request, 'Debes agregar al menos un concepto o artÃ­culo a la factura.')
                return redirect('factura_crear_nueva')
            print(f"DEBUG - IDs Conceptos: {conceptos_ids}")
            print(f"DEBUG - IDs Artículos: {articulos_ids}")
            print(f"DEBUG - Cantidades: {cantidades}")
            print(f"DEBUG - Precios: {precios}")
            print(f"DEBUG - Meses: {meses}")
            print(f"DEBUG - Años: {anios}")
            
            from .models import Articulo, MovimientoInventario
            
            detalles_creados = 0
            max_items = max(len(conceptos_ids), len(articulos_ids))
            
            for i in range(max_items):
                # Obtener concepto o artÃ­culo
                concepto = None
                articulo = None
                descripcion = ''
                
                # Verificar si es un concepto tradicional
                if i < len(conceptos_ids) and conceptos_ids[i]:
                    concepto = ConceptoPago.objects.get(id=conceptos_ids[i])
                    descripcion = concepto.nombre
                    
                    # VALIDAR: Mensualidad/InscripciÃ³n/Transporte solo para estudiantes reales
                    if concepto.tipo in ['mensualidad', 'inscripcion', 'transporte']:
                        # Obtener cliente genÃ©rico
                        cliente_generico = obtener_o_crear_cliente_generico()
                        
                        # Validar que no sea cliente genÃ©rico
                        if cliente_generico and estudiante_post.id == cliente_generico.id:
                            factura.delete()
                            messages.error(request, f'El cliente genÃ©rico no puede tener {concepto.tipo}. Selecciona un estudiante real.')
                            return redirect('factura_crear_nueva')
                        
                        # Validar que el cliente tenga rol Estudiante
                        if estudiante_post.rol != 'Estudiante':
                            factura.delete()
                            messages.error(request, f'Solo los estudiantes pueden tener {concepto.tipo}.')
                            return redirect('factura_crear_nueva')
                    
                # O si es un artÃ­culo del inventario
                elif i < len(articulos_ids) and articulos_ids[i]:
                    articulo = Articulo.objects.get(id=articulos_ids[i])
                    descripcion = f"{articulo.nombre} (CB: {articulo.codigo_barras})"
                else:
                    continue  # Saltar si no hay ni concepto ni artÃ­culo
                
                # Procesar mes y año con validación
                mes_valor = None
                if i < len(meses) and meses[i] and meses[i].strip():
                    try:
                        mtemp = int(meses[i])
                        # Validar rango 1-12
                        if 1 <= mtemp <= 12:
                            mes_valor = mtemp
                        else:
                            mes_valor = None
                    except (ValueError, TypeError):
                        mes_valor = None
                
                anio_valor = None
                if i < len(anios) and anios[i] and anios[i].strip():
                    try:
                        anio_valor = int(anios[i])
                    except (ValueError, TypeError):
                        anio_valor = None
                
                cantidad_valor = Decimal(cantidades[i]) if i < len(cantidades) and cantidades[i] else Decimal('1')
                precio_valor = Decimal(precios[i]) if i < len(precios) else Decimal('0')

                # Si corresponde, buscar o crear Mensualidad y enlazarla
                mensualidad_obj = None
                try:
                    from .models import Mensualidad
                except Exception:
                    Mensualidad = None

                if mes_valor and anio_valor and Mensualidad:
                    # Crear/enlazar mensualidad para conceptos tipo 'mensualidad' o 'inscripcion'
                    try:
                        if concepto and getattr(concepto, 'tipo', '') in ('mensualidad', 'inscripcion'):
                            mensualidad_obj, created = Mensualidad.objects.get_or_create(
                                estudiante=estudiante_post,
                                anho_escolar=anho_escolar,
                                mes=mes_valor,
                                anio=anio_valor,
                                defaults={
                                    'concepto': concepto,
                                    'descripcion': descripcion,
                                    'monto': precio_valor,
                                    'creado_por': request.user
                                }
                            )
                            
                            # Calcular mora para esta mensualidad si está vencida
                            if concepto.tipo == 'mensualidad' and hasattr(estudiante_post, 'grupo_familiar') and estudiante_post.grupo_familiar:
                                from datetime import date
                                from calendar import monthrange
                                
                                # Obtener día de vencimiento del grupo familiar
                                dia_vencimiento = estudiante_post.grupo_familiar.dia_vencimiento
                                
                                # Crear fecha de vencimiento de esta mensualidad
                                try:
                                    # Obtener el último día del mes si el día de vencimiento no existe
                                    ultimo_dia_mes = monthrange(anio_valor, mes_valor)[1]
                                    dia_venc_ajustado = min(dia_vencimiento, ultimo_dia_mes)
                                    fecha_venc_mensualidad = date(anio_valor, mes_valor, dia_venc_ajustado)
                                    
                                    hoy = date.today()
                                    
                                    # Si la mensualidad está vencida, calcular mora
                                    if hoy > fecha_venc_mensualidad:
                                        porcentaje_mora = estudiante_post.get_porcentaje_mora()
                                        if porcentaje_mora > 0:
                                            monto_mora_mensualidad = (precio_valor * porcentaje_mora) / Decimal('100')
                                            mora_acumulada += monto_mora_mensualidad
                                            mensualidades_vencidas_info.append({
                                                'mes': mes_valor,
                                                'anio': anio_valor,
                                                'monto_base': precio_valor,
                                                'mora': monto_mora_mensualidad,
                                                'fecha_vencimiento': fecha_venc_mensualidad
                                            })
                                            print(f"DEBUG MORA MENSUALIDAD - {mes_valor}/{anio_valor} vencida el {fecha_venc_mensualidad}: Mora RD${monto_mora_mensualidad} ({porcentaje_mora}% de RD${precio_valor})")
                                except Exception as e:
                                    print(f"DEBUG MORA - Error al calcular fecha vencimiento para {mes_valor}/{anio_valor}: {e}")
                    except Exception as e:
                        print(f"DEBUG: error al get_or_create Mensualidad: {e}")

                # Crear detalle de factura (vinculando mensualidad si existe)
                detalle = DetalleFactura.objects.create(
                    factura=factura,
                    concepto=concepto,
                    articulo=articulo,  # Agregar el artÃ­culo aquÃ­
                    mensualidad=mensualidad_obj,
                    descripcion=descripcion,
                    cantidad=cantidad_valor,
                    precio_unitario=precio_valor,
                    descuento=Decimal(descuentos[i]) if i < len(descuentos) and descuentos[i] else Decimal('0'),
                    mes=mes_valor,
                    anio=anio_valor
                )
                
                # Si es un artÃ­culo, descontar del inventario y registrar movimiento
                if articulo and articulo.tipo == 'producto':
                    try:
                        stock_anterior = articulo.stock_actual
                        articulo.ajustar_stock(int(cantidad_valor), tipo='salida')
                        
                        # Registrar movimiento
                        MovimientoInventario.objects.create(
                            articulo=articulo,
                            tipo='salida',
                            cantidad=int(cantidad_valor),
                            stock_anterior=stock_anterior,
                            stock_nuevo=articulo.stock_actual,
                            motivo=f"Venta - Factura {factura.numero_factura}",
                            factura=factura,
                            usuario=request.user
                        )
                        print(f"DEBUG - Stock actualizado para {articulo.nombre}: {stock_anterior} ✓ {articulo.stock_actual}")
                    except ValueError as e:
                        # Si no hay stock suficiente, eliminar la factura y mostrar error
                        factura.delete()
                        messages.error(request, f'Error: {str(e)}')
                        return redirect('factura_crear_nueva')
                
                detalles_creados += 1
                tipo_detalle = 'ArtÃ­culo' if articulo else 'Concepto'
                nombre_detalle = articulo.nombre if articulo else concepto.nombre
                print(f"DEBUG - Detalle #{i+1} creado: {tipo_detalle} - {nombre_detalle} - Mes: {mes_valor}/{anio_valor}")
            
            # Agregar concepto de mora acumulada si hay mensualidades vencidas
            if mora_acumulada > 0:
                print(f"DEBUG MORA ACUMULADA - Total: RD${mora_acumulada} de {len(mensualidades_vencidas_info)} mensualidades vencidas")
                
                # Crear o buscar concepto de mora
                concepto_mora, created = ConceptoPago.objects.get_or_create(
                    tipo='otro',
                    nombre='Mora por Pago Atrasado',
                    defaults={
                        'monto': 0,
                        'descripcion': 'Recargo por pago fuera de fecha',
                        'activo': True
                    }
                )
                
                # Crear descripción detallada
                porcentaje_mora = estudiante_post.get_porcentaje_mora()
                descripcion_mora = f'Mora por Mensualidades Vencidas ({porcentaje_mora}%)'
                if len(mensualidades_vencidas_info) > 0:
                    meses_texto = ', '.join([f"{info['mes']}/{info['anio']}" for info in mensualidades_vencidas_info[:3]])
                    if len(mensualidades_vencidas_info) > 3:
                        meses_texto += f" y {len(mensualidades_vencidas_info) - 3} mÃ¡s"
                    descripcion_mora += f' - Meses: {meses_texto}'
                
                # Agregar detalle de mora
                detalle_mora = DetalleFactura.objects.create(
                    factura=factura,
                    concepto=concepto_mora,
                    descripcion=descripcion_mora,
                    cantidad=1,
                    precio_unitario=mora_acumulada,
                    descuento=0
                )
                print(f"DEBUG MORA - ✓ Mora agregada a factura: RD${mora_acumulada} (Detalle ID: {detalle_mora.id})")
                detalles_creados += 1
            elif hasattr(estudiante_post, 'grupo_familiar') and estudiante_post.grupo_familiar:
                # Si no hay mora pero el estudiante está en un grupo familiar, agregar mora en 0 para que se vea
                concepto_mora, created = ConceptoPago.objects.get_or_create(
                    tipo='otro',
                    nombre='Mora por Pago Atrasado',
                    defaults={
                        'monto': 0,
                        'descripcion': 'Recargo por pago fuera de fecha',
                        'activo': True
                    }
                )
                
                # Agregar detalle de mora en 0
                detalle_mora = DetalleFactura.objects.create(
                    factura=factura,
                    concepto=concepto_mora,
                    descripcion='Mora - Sin cargo (pagos al día)',
                    cantidad=1,
                    precio_unitario=Decimal('0'),
                    descuento=0
                )
                print(f"DEBUG MORA - Mora en $0 agregada (estudiante al día)")
                detalles_creados += 1
            
            # Aplicar mora si la fecha de vencimiento ya pasÃ³
            print(f"DEBUG MORA - fecha_vencimiento recibida: {fecha_vencimiento} (tipo: {type(fecha_vencimiento)})")
            if fecha_vencimiento:
                from datetime import datetime, date
                try:
                    # Convertir fecha_vencimiento a date si es string
                    if isinstance(fecha_vencimiento, str):
                        fecha_venc_date = datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date()
                    else:
                        fecha_venc_date = fecha_vencimiento
                    
                    hoy = date.today()
                    print(f"DEBUG MORA - Hoy: {hoy} | Vencimiento: {fecha_venc_date} | EstÃ¡ vencida: {hoy > fecha_venc_date}")
                    
                    # Verificar si está vencida
                    if hoy > fecha_venc_date:
                        # Calcular el subtotal actual (antes de mora)
                        subtotal_actual = sum(detalle.get_total() for detalle in factura.detalles.all())
                        print(f"DEBUG MORA - Subtotal para calcular mora: RD${subtotal_actual}")
                        
                        # Obtener porcentaje de mora del estudiante
                        porcentaje_mora = estudiante_post.get_porcentaje_mora()
                        print(f"DEBUG MORA - Porcentaje de mora del estudiante {estudiante_post.get_full_name()}: {porcentaje_mora}%")
                        print(f"DEBUG MORA - Grupo familiar: {getattr(estudiante_post, 'grupo_familiar', None)}")
                        if hasattr(estudiante_post, 'grupo_familiar') and estudiante_post.grupo_familiar:
                            print(f"DEBUG MORA - Mora del grupo: {estudiante_post.grupo_familiar.porcentaje_mora}%")
                        print(f"DEBUG MORA - Mora individual: {estudiante_post.porcentaje_mora_individual}%")
                        
                        if porcentaje_mora > 0:
                            monto_mora = (subtotal_actual * porcentaje_mora) / Decimal('100')
                            print(f"DEBUG MORA - Monto mora a aplicar: RD${monto_mora}")
                            
                            # Crear o buscar concepto de mora
                            concepto_mora, created = ConceptoPago.objects.get_or_create(
                                tipo='otro',
                                nombre='Mora por Pago Atrasado',
                                defaults={
                                    'monto': 0,  # El monto varÃ­a según cada caso
                                    'descripcion': 'Recargo por pago fuera de fecha',
                                    'activo': True
                                }
                            )
                            
                            # Agregar detalle de mora
                            detalle_mora = DetalleFactura.objects.create(
                                factura=factura,
                                concepto=concepto_mora,
                                descripcion=f'Mora ({porcentaje_mora}% sobre facturas vencidas)',
                                cantidad=1,
                                precio_unitario=monto_mora,
                                descuento=0
                            )
                            print(f"DEBUG MORA - ✓ Mora aplicada exitosamente: {porcentaje_mora}% = RD${monto_mora} (Detalle ID: {detalle_mora.id})")
                            detalles_creados += 1
                        else:
                            print(f"DEBUG MORA - ✓ NO se aplica mora: porcentaje es 0%")
                    else:
                        print(f"DEBUG MORA - ✓ NO se aplica mora: la factura no está vencida")
                except Exception as e:
                    print(f"DEBUG MORA - ✓✓✓ ERROR al aplicar mora: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"DEBUG MORA - ✓ NO se aplica mora: no hay fecha_vencimiento")
            
            # Recalcular totales de la factura
            factura.calcular_totales()
            factura.actualizar_estado()
            factura.save()

            # ============================================
            # REGISTRAR PAGO AUTOMÃTICAMENTE si monto_pagado > 0
            # ============================================
            pago_creado_exitosamente = False
            if monto_pagado > 0:
                try:
                    # Verificar si ya existe un pago para esta factura (por si se está editando)
                    pago_existente = PagoFactura.objects.filter(factura=factura).first()
                    
                    if not pago_existente:
                        # Crear registro de pago automáticamente
                        from datetime import datetime
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                        contador_pago = PagoFactura.objects.count() + 1
                        numero_recibo_auto = f"REC-{timestamp}-{contador_pago:05d}"
                        
                        pago = PagoFactura.objects.create(
                            factura=factura,
                            monto=monto_pagado,
                            metodo_pago=metodo_pago,
                            fecha_pago=timezone.now(),  # Usar fecha actual
                            registrado_por=request.user,
                            numero_recibo=numero_recibo_auto,
                            referencia=referencia_pago if referencia_pago else None,
                            observaciones=f'Pago registrado automáticamente al crear la factura'
                        )
                        pago_creado_exitosamente = True
                        print(f"DEBUG PAGO - ✓ Pago automático creado: {pago.numero_recibo} por RD${monto_pagado}")
                        messages.success(request, f'✓ Pago registrado: {pago.numero_recibo} por RD${monto_pagado:,.2f}')
                    else:
                        pago_creado_exitosamente = True
                        print(f"DEBUG PAGO - ✓ Ya existe un pago para esta factura: {pago_existente.numero_recibo}")
                except Exception as e:
                    # Si falla la creación del pago, resetear monto_pagado para mantener consistencia
                    print(f"DEBUG PAGO - ✗ ERROR al crear pago automático: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # IMPORTANTE: Si no se pudo crear el pago, ajustar monto_pagado a 0
                    factura.monto_pagado = Decimal('0')
                    factura.actualizar_estado()
                    factura.save()
                    
                    messages.warning(
                        request, 
                        f'⚠️ La factura #{factura.numero_factura} se creó pero hubo un error al registrar el pago. '
                        f'Por favor, registre el pago manualmente desde la vista de facturas. Error: {str(e)}'
                    )
            
            # Verificar que el estado sea consistente con los pagos reales
            if not pago_creado_exitosamente and factura.estado in ['pagada', 'parcial']:
                # Si la factura está marcada como pagada/parcial pero no se creó el pago, corregir
                factura.monto_pagado = Decimal('0')
                factura.actualizar_estado()
                factura.save()
                print(f"DEBUG PAGO - ⚠️ Estado de factura corregido a {factura.estado} (no hay pagos registrados)")

            # ============================================
            # VALIDACIÓN: Clientes con nombre "Cliente" NO pueden comprar a crédito
            # ============================================
            if estudiante_post.first_name == 'Cliente' and monto_pagado < factura.total:
                # Capturar el total antes de eliminar la factura
                total_factura = factura.total
                # Eliminar la factura antes de redirigir
                factura.delete()
                messages.error(
                    request, 
                    '❌ Los clientes con nombre "Cliente" no pueden realizar compras a crédito. '
                    f'Total de la factura: RD${total_factura:,.2f} | Monto pagado: RD${monto_pagado:,.2f}. '
                    'Solo se permiten ventas pagadas en su totalidad (efectivo, tarjeta, transferencia, mixto). '
                    'Para ventas a crédito, debe registrar un cliente real con nombre y apellidos completos.'
                )
                return redirect('factura_crear_nueva')

            # Vincular y actualizar mensualidades asociadas a los detalles
            try:
                from .models import Mensualidad
                for det in factura.detalles.filter(mensualidad__isnull=False).select_related('mensualidad'):
                    m = det.mensualidad
                    if not m:
                        continue
                    m.factura = factura
                    # Si la factura quedÃ³ pagada, marcar la mensualidad como pagada
                    if factura.estado == 'pagada':
                        try:
                            m.marcar_pagada(factura)
                        except Exception:
                            m.estado = 'pagada'
                            m.fecha_pagado = timezone.now()
                            m.factura = factura
                            m.save()
                    else:
                        # Si hay algÃºn abono, marcar parcial; si no, pendiente
                        try:
                            if factura.monto_pagado and factura.monto_pagado > 0:
                                m.estado = 'parcial'
                            else:
                                m.estado = 'pendiente'
                            m.save()
                        except Exception:
                            m.save()
            except Exception as e:
                print(f"DEBUG: error al actualizar mensualidades post-factura: {e}")
            
            print(f"DEBUG - Total detalles creados: {detalles_creados}")
            print(f"DEBUG - Factura totales - Subtotal: {factura.subtotal}, Total: {factura.total}, Estado: {factura.estado}")
            
            # Obtener o crear el estudiante "cliente" para cargar automáticamente
            cliente_generico = obtener_o_crear_cliente_generico()
            
            if cliente_generico:
                url_nueva_factura = f'/facturas/nueva/?estudiante_id={cliente_generico.id}'
            else:
                url_nueva_factura = '/facturas/nueva/'
            
            # Construir respuesta HTML que abre el recibo e imprime automáticamente
            from django.http import HttpResponse
            recibo_url = f"/facturas/{factura.id}/recibo/"
            
            html_response = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Factura Guardada</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: #f5f5f5;
                    }}
                    .mensaje {{
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        text-align: center;
                    }}
                    .icono {{
                        font-size: 48px;
                        color: #28a745;
                        margin-bottom: 20px;
                    }}
                    h2 {{
                        color: #333;
                        margin-bottom: 10px;
                    }}
                    p {{
                        color: #666;
                        margin-bottom: 20px;
                    }}
                    .spinner {{
                        border: 4px solid #f3f3f3;
                        border-top: 4px solid #28a745;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        animation: spin 1s linear infinite;
                        margin: 20px auto;
                    }}
                    @keyframes spin {{
                        0% {{ transform: rotate(0deg); }}
                        100% {{ transform: rotate(360deg); }}
                    }}
                </style>
            </head>
            <body>
                <div class="mensaje">
                    <div class="icono">✓</div>
                    <h2>¡Factura Creada Exitosamente!</h2>
                    <p>Factura: <strong>{factura.numero_factura}</strong></p>
                    <p>Total: <strong>RD${factura.total}</strong></p>
                    <div class="spinner"></div>
                    <p>Abriendo recibo para imprimir...</p>
                </div>
                <script>
                    // Abrir recibo en nueva ventana
                    var ventanaRecibo = window.open('{recibo_url}', '_blank', 'width=400,height=700,location=no,menubar=no,toolbar=no,status=no');
                    
                    // Esperar un momento y redirigir a nueva factura con cliente cargado
                    setTimeout(function() {{
                        window.location.href = '{url_nueva_factura}';
                    }}, 2000);
                </script>
            </body>
            </html>
            """
            return HttpResponse(html_response)
            
        except Exception as e:
            import traceback
            print(f"\n{'='*80}")
            print(f"ERROR AL CREAR FACTURA:")
            print(f"Mensaje: {str(e)}")
            print(f"Traceback completo:")
            traceback.print_exc()
            print(f"{'='*80}\n")
            messages.error(request, f'Error al crear la factura: {str(e)}')
    
    # Obtener conceptos de pago activos, excluyendo conceptos no deseados
    conceptos = ConceptoPago.objects.filter(activo=True).exclude(
        Q(nombre__icontains='mensualidad tes') | 
        Q(nombre__icontains='cuaderno') |
        Q(nombre__icontains='transporte red') |
        Q(nombre__icontains='transporte rd')
    ).order_by('tipo', 'nombre')
    
    # Convertir conceptos a lista de diccionarios para JSON
    import json
    conceptos_list = [
        {
            'id': c.id,
            'nombre': c.nombre,  # Sin monto en el nombre
            'tipo': c.tipo,
            'monto': float(c.monto) if c.tipo not in ['mensualidad', 'inscripcion'] else 0  # Para mensualidad/inscripciÃ³n, monto viene de tarifa
        }
        for c in conceptos
    ]
    
    # Año actual
    import datetime
    anio_actual = datetime.datetime.now().year
    
    context = {
        'titulo': 'Nueva Factura',
        'anho_escolar': anho_escolar,
        'estudiante': estudiante_seleccionado,
        'estudiantes_encontrados': estudiantes_encontrados,
        'familias_encontradas': familias_encontradas,
        'buscar': buscar,
        'conceptos': conceptos,
        'conceptos_json': json.dumps(conceptos_list),
        'anio_actual': anio_actual,
        'meses_pagados': json.dumps(meses_pagados),  # Pasar meses pagados como JSON
        'tarifa_json': tarifa_json if 'tarifa_json' in locals() else None,
        'es_cliente_generico': es_cliente_generico,
        'detalles_json': detalles_json,
        'monto_pagado_copiado': monto_pagado_copiado,
    }
    return render(request, 'cobros/factura_crear_nueva.html', context)
    


@login_required
def buscar_articulo_barras(request):
    """Buscar artÃ­culo por código de barras - API AJAX"""
    if request.user.rol not in ['Secretaria', 'Administrador', 'Vendedor', 'Gerente']:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    from .models import Articulo
    import json
    
    codigo_barras = request.GET.get('codigo', '').strip()
    
    if not codigo_barras:
        return JsonResponse({'error': 'Código vacÃ­o'}, status=400)
    
    try:
        articulo = Articulo.objects.get(codigo_barras=codigo_barras, activo=True)
        
        data = {
            'success': True,
            'articulo': {
                'id': articulo.id,
                'codigo_barras': articulo.codigo_barras,
                'nombre': articulo.nombre,
                'descripcion': articulo.descripcion or '',
                'precio_venta': float(articulo.precio_venta),
                'stock_actual': articulo.stock_actual,
                'tipo': articulo.tipo,
                'permite_descuento': articulo.permite_descuento,
                'aplica_itbis': articulo.aplica_itbis,
            }
        }
        return JsonResponse(data)
        
    except Articulo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'ArtÃ­culo con código "{codigo_barras}" no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def buscar_articulo_nombre(request):
    """Buscar artículos por nombre (AJAX)"""
    if request.user.rol not in ['Secretaria', 'Administrador', 'Vendedor', 'Gerente']:
        return JsonResponse({'error': 'No autorizado'}, status=403)

    from .models import Articulo

    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'success': True, 'results': []})

    try:
        articulos = Articulo.objects.filter(nombre__icontains=q, activo=True)[:20]
        results = []
        for a in articulos:
            results.append({
                'id': a.id,
                'codigo_barras': a.codigo_barras,
                'nombre': a.nombre,
                'descripcion': a.descripcion or '',
                'precio_venta': float(a.precio_venta),
                'stock_actual': a.stock_actual,
                'tipo': a.tipo,
                'permite_descuento': a.permite_descuento,
                'aplica_itbis': a.aplica_itbis,
            })
        return JsonResponse({'success': True, 'results': results})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def tarifa_estudiante_api(request):
    """Devuelve la tarifa activa (mensualidad/inscripcion) para un estudiante dado (AJAX)."""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        return JsonResponse({'error': 'No autorizado'}, status=403)

    estudiante_id = request.GET.get('estudiante_id')
    if not estudiante_id:
        return JsonResponse({'success': True, 'tarifa': None})

    try:
        from .models import TarifaEstudiante
        tarifas = TarifaEstudiante.objects.filter(estudiante_id=estudiante_id, activo=True).select_related('concepto')
        data = {'mensualidad': None, 'inscripcion': None}
        mens = tarifas.filter(tipo='mensualidad').first()
        insc = tarifas.filter(tipo='inscripcion').first()
        if mens:
            data['mensualidad'] = {
                'id': mens.id,
                'concepto_id': mens.concepto.id if mens.concepto else None,
                'monto': float(mens.monto),
                'concepto_nombre': mens.concepto.nombre if mens.concepto else None,
            }
        if insc:
            data['inscripcion'] = {
                'id': insc.id,
                'concepto_id': insc.concepto.id if insc.concepto else None,
                'monto': float(insc.monto),
                'concepto_nombre': insc.concepto.nombre if insc.concepto else None,
            }
        return JsonResponse({'success': True, 'tarifa': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def tarifas_list(request):
    """Lista las tarifas por estudiante (CRUD admin) con búsqueda."""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')

    # Agrupar tarifas por estudiante
    from collections import defaultdict
    from django.db.models import Q
    
    # Obtener parámetros de búsqueda
    search_query = request.GET.get('search', '').strip()
    tipo_tarifa = request.GET.get('tipo', '').strip()
    mostrar_sin_tarifas = request.GET.get('sin_tarifas', '').strip() == '1'
    
    # Filtrar tarifas activas
    tarifas_qs = TarifaEstudiante.objects.select_related('estudiante', 'concepto').filter(activo=True)
    
    # Aplicar búsqueda por nombre de estudiante
    if search_query:
        tarifas_qs = tarifas_qs.filter(
            Q(estudiante__first_name__icontains=search_query) |
            Q(estudiante__last_name__icontains=search_query) |
            Q(estudiante__cedula__icontains=search_query)
        )
    
    # Aplicar filtro por tipo de tarifa
    if tipo_tarifa:
        tarifas_qs = tarifas_qs.filter(concepto__tipo=tipo_tarifa)
    
    tarifas_qs = tarifas_qs.order_by('estudiante__first_name', 'estudiante__last_name')
    
    # Crear diccionario agrupado por estudiante
    tarifas_por_estudiante = defaultdict(lambda: {'mensualidad': None, 'inscripcion': None, 'transporte': None, 'estudiante': None})
    
    for tarifa in tarifas_qs:
        estudiante_id = tarifa.estudiante.id
        tarifas_por_estudiante[estudiante_id]['estudiante'] = tarifa.estudiante
        
        if tarifa.concepto.tipo == 'mensualidad':
            tarifas_por_estudiante[estudiante_id]['mensualidad'] = tarifa
        elif tarifa.concepto.tipo == 'inscripcion':
            tarifas_por_estudiante[estudiante_id]['inscripcion'] = tarifa
        elif tarifa.concepto.tipo == 'transporte':
            tarifas_por_estudiante[estudiante_id]['transporte'] = tarifa
    
    # Convertir a lista para paginar
    tarifas_agrupadas = list(tarifas_por_estudiante.values())
    
    # Buscar estudiantes sin tarifas
    estudiantes_con_tarifas_ids = [grupo['estudiante'].id for grupo in tarifas_agrupadas if grupo['estudiante']]
    estudiantes_sin_tarifas = CustomUser.objects.filter(
        rol='Estudiante',
        is_active=True
    ).exclude(
        id__in=estudiantes_con_tarifas_ids
    ).order_by('first_name', 'last_name')
    
    # Si se solicita búsqueda de estudiantes sin tarifas
    if search_query and mostrar_sin_tarifas:
        estudiantes_sin_tarifas = estudiantes_sin_tarifas.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(cedula__icontains=search_query)
        )
    
    paginator = Paginator(tarifas_agrupadas, 25)
    page = request.GET.get('page')
    tarifas = paginator.get_page(page)
    
    context = {
        'tarifas': tarifas,
        'search_query': search_query,
        'tipo_tarifa': tipo_tarifa,
        'total_estudiantes': len(tarifas_agrupadas),
        'estudiantes_sin_tarifas': list(estudiantes_sin_tarifas[:20]),  # Limitar a 20
        'total_sin_tarifas': estudiantes_sin_tarifas.count(),
        'mostrar_sin_tarifas': mostrar_sin_tarifas,
    }
    
    return render(request, 'cobros/tarifas_list.html', context)


@login_required
def tarifa_create(request):
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')

    # Obtener return_to desde GET o POST
    return_to = request.GET.get('return_to') or request.POST.get('return_to')
    
    if request.method == 'POST':
        # Si es Secretaria, validar código de seguridad
        if request.user.rol == 'Secretaria':
            from .models import CodigoAnulacion
            codigo_ingresado = request.POST.get('codigo_seguridad', '').strip()
            
            if not CodigoAnulacion.validar_codigo(codigo_ingresado):
                messages.error(request, 'Código de seguridad incorrecto.')
                form = TarifaEstudianteForm(request.POST)
                return render(request, 'cobros/tarifa_form.html', {
                    'form': form,
                    'titulo': 'Crear Tarifa',
                    'return_to': return_to,
                    'requiere_codigo': True,
                    'error_codigo': True,
                })
        
        form = TarifaEstudianteForm(request.POST)
        if form.is_valid():
            tarifa = form.save()
            messages.success(request, 'Tarifa creada correctamente.')
            # Si viene desde factura, redirigir de vuelta con el estudiante
            if return_to == 'factura':
                return redirect('factura_crear', estudiante_id=tarifa.estudiante.id)
            return redirect('tarifas_list')
    else:
        # Preseleccionar estudiante si viene en la URL
        estudiante_id = request.GET.get('estudiante')
        if estudiante_id:
            form = TarifaEstudianteForm(initial={'estudiante': estudiante_id})
        else:
            form = TarifaEstudianteForm()
    
    # Secretaria requiere código de seguridad
    requiere_codigo = (request.user.rol == 'Secretaria')
    
    return render(request, 'cobros/tarifa_form.html', {
        'form': form, 
        'titulo': 'Crear Tarifa',
        'return_to': return_to,
        'requiere_codigo': requiere_codigo,
    })


@login_required
def obtener_concepto_monto(request, concepto_id):
    """API para obtener el monto de un concepto seleccionado."""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        concepto = ConceptoPago.objects.get(id=concepto_id, activo=True)
        return JsonResponse({
            'id': concepto.id,
            'nombre': concepto.nombre,
            'tipo': concepto.tipo,
            'monto': float(concepto.monto),
            'descripcion': concepto.descripcion or ''
        })
    except ConceptoPago.DoesNotExist:
        return JsonResponse({'error': 'Concepto no encontrado'}, status=404)


@login_required
def tarifa_edit(request, pk):
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')

    tarifa = get_object_or_404(TarifaEstudiante, pk=pk)
    
    if request.method == 'POST':
        # Si es Secretaria, validar código de seguridad
        if request.user.rol == 'Secretaria':
            from .models import CodigoAnulacion
            codigo_ingresado = request.POST.get('codigo_seguridad', '').strip()
            
            if not CodigoAnulacion.validar_codigo(codigo_ingresado):
                messages.error(request, 'Código de seguridad incorrecto.')
                form = TarifaEstudianteForm(request.POST, instance=tarifa)
                return render(request, 'cobros/tarifa_form.html', {
                    'form': form,
                    'titulo': 'Editar Tarifa',
                    'tarifa': tarifa,
                    'requiere_codigo': True,
                    'error_codigo': True,
                })
        
        form = TarifaEstudianteForm(request.POST, instance=tarifa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tarifa actualizada correctamente.')
            return redirect('tarifas_list')
    else:
        form = TarifaEstudianteForm(instance=tarifa)
    
    # Secretaria requiere código de seguridad
    requiere_codigo = (request.user.rol == 'Secretaria')
    
    return render(request, 'cobros/tarifa_form.html', {
        'form': form,
        'titulo': 'Editar Tarifa',
        'tarifa': tarifa,
        'requiere_codigo': requiere_codigo,
    })


@login_required
def tarifa_delete(request, pk):
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')

    tarifa = get_object_or_404(TarifaEstudiante, pk=pk)
    if request.method == 'POST':
        tarifa.delete()
        messages.success(request, 'Tarifa eliminada.')
        return redirect('tarifas_list')
    return render(request, 'cobros/tarifa_confirm_delete.html', {'tarifa': tarifa})


@login_required
def factura_crear(request, estudiante_id):
    """Redirige a la vista unificada de creaciÃ³n de factura con estudiante pre-seleccionado"""
    return redirect(f'/facturas/nueva/?estudiante_id={estudiante_id}')
    
    # Obtener conceptos de pago activos
    conceptos = ConceptoPago.objects.filter(activo=True).order_by('tipo', 'nombre')
    
    # Año actual
    import datetime
    anio_actual = datetime.datetime.now().year
    
    context = {
        'titulo': f'Crear Factura - {estudiante.get_full_name()}',
        'anho_escolar': anho_escolar,
        'estudiante': estudiante,
        'conceptos': conceptos,
        'anio_actual': anio_actual,
    }
    return render(request, 'cobros/factura_crear.html', context)


@login_required
def factura_detalle(request, factura_id):
    """Ver detalle de una factura"""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from .models import Factura
    import logging
    logger = logging.getLogger(__name__)
    
    factura = get_object_or_404(
        Factura.objects.select_related('cliente', 'anho_escolar', 'creado_por')
        .prefetch_related('detalles__concepto', 'detalles__articulo', 'pagos__registrado_por'),
        id=factura_id
    )
    
    # Debug: verificar detalles
    detalles_count = factura.detalles.count()
    logger.warning(f"DEBUG - Factura {factura.numero_factura} tiene {detalles_count} detalles")
    print(f"DEBUG - Factura {factura.numero_factura} tiene {detalles_count} detalles")
    
    # Calcular información de mora
    mora_info = factura.calcular_mora()
    tiene_mora_aplicada = False
    monto_mora_aplicado = 0
    
    for detalle in factura.detalles.all():
        item_nombre = detalle.concepto.nombre if detalle.concepto else (detalle.articulo.nombre if detalle.articulo else 'Sin item')
        logger.warning(f"  - Detalle: {detalle.descripcion} | Item: {item_nombre} | Mes: {detalle.mes} | Total: {detalle.get_total()}")
        print(f"  - Detalle: {detalle.descripcion} | Item: {item_nombre} | Mes: {detalle.mes} | Total: {detalle.get_total()}")
        
        # Verificar si hay un detalle de mora
        if detalle.concepto and 'mora' in detalle.concepto.nombre.lower():
            tiene_mora_aplicada = True
            monto_mora_aplicado += detalle.get_total()
    
    context = {
        'titulo': f'Factura {factura.numero_factura}',
        'factura': factura,
        'mora_info': mora_info,
        'tiene_mora_aplicada': tiene_mora_aplicada,
        'monto_mora_aplicado': monto_mora_aplicado,
    }
    return render(request, 'cobros/factura_detalle.html', context)


@login_required
def factura_recibo_pos(request, factura_id):
    """Generar recibo para impresora punto de venta"""
    from .models import Factura, AnhoEscolar
    from django.conf import settings
    
    factura = get_object_or_404(
        Factura.objects.select_related('cliente', 'anho_escolar', 'creado_por')
        .prefetch_related('detalles__concepto', 'detalles__articulo'),
        id=factura_id
    )
    
    # Obtener información de la escuela desde settings o base de datos
    # Puedes personalizar estos valores en tu archivo settings.py o crear un modelo de configuración
    escuela_info = {
        'nombre': getattr(settings, 'ESCUELA_NOMBRE', 'Centro Educativo San JosÃ©'),
        'rnc': getattr(settings, 'ESCUELA_RNC', '123-45678-9'),
        'telefono': getattr(settings, 'ESCUELA_TELEFONO', '(809) 555-1234'),
        'direccion': getattr(settings, 'ESCUELA_DIRECCION', 'Calle Principal #123, Santo Domingo'),
        'email': getattr(settings, 'ESCUELA_EMAIL', 'info@escuela.edu.do'),
    }
    
    # Calcular cambio si pagÃ³ de mÃ¡s
    cambio = max(0, float(factura.monto_pagado) - float(factura.total))
    
    context = {
        'factura': factura,
        'escuela': escuela_info,
        'cambio': cambio,
    }
    return render(request, 'cobros/recibo_pos.html', context)


@login_required
def factura_registrar_pago(request, factura_id):
    """Registrar un pago/abono para una factura"""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from .models import Factura, PagoFactura
    
    factura = get_object_or_404(Factura, id=factura_id)
    
    if request.method == 'POST':
        try:
            monto = float(request.POST.get('monto'))
            metodo_pago = request.POST.get('metodo_pago')
            referencia = request.POST.get('referencia', '')
            banco = request.POST.get('banco', '')
            observaciones = request.POST.get('observaciones', '')
            
            # Validar que no se pague mÃ¡s del saldo pendiente
            saldo_pendiente = factura.saldo_pendiente
            if monto > saldo_pendiente:
                messages.error(request, f'El monto no puede ser mayor al saldo pendiente (RD${saldo_pendiente})')
                return redirect('factura_detalle', factura_id=factura.id)
            
            PagoFactura.objects.create(
                factura=factura,
                monto=monto,
                metodo_pago=metodo_pago,
                referencia=referencia,
                banco=banco,
                observaciones=observaciones,
                registrado_por=request.user
            )
            
            messages.success(request, f'Pago de RD${monto} registrado exitosamente')
            return redirect('factura_detalle', factura_id=factura.id)
            
        except Exception as e:
            messages.error(request, f'Error al registrar el pago: {str(e)}')
    
    return redirect('factura_detalle', factura_id=factura.id)


@login_required
def facturas_estudiante(request, estudiante_id):
    """Ver todas las facturas de un estudiante"""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from .models import Factura
    from django.db.models import Sum
    
    estudiante = get_object_or_404(CustomUser, id=estudiante_id, rol='Estudiante')
    
    # Obtener año escolar activo
    try:
        anho_escolar = AnhoEscolar.objects.get(activo=True)
    except AnhoEscolar.DoesNotExist:
        messages.error(request, 'No hay un año escolar activo.')
        return redirect('plataform')
    
    # Obtener facturas del estudiante
    facturas = Factura.objects.filter(
        cliente=estudiante,
        anho_escolar=anho_escolar
    ).prefetch_related('detalles', 'pagos').order_by('-fecha_emision')
    
    # Estadísticas (excluyendo facturas anuladas)
    facturas_validas = facturas.exclude(estado='anulada')
    total_facturas = facturas_validas.count()
    total_adeudado = sum(f.total for f in facturas_validas)
    total_pagado = sum(f.monto_pagado for f in facturas_validas)
    saldo_pendiente = total_adeudado - total_pagado
    
    facturas_pendientes = facturas_validas.filter(estado__in=['pendiente', 'parcial']).count()
    facturas_pagadas = facturas_validas.filter(estado='pagada').count()
    
    # Obtener mensualidades pagadas por mes
    from .models import DetalleFactura
    import datetime
    anio_actual = datetime.datetime.now().year
    
    # Obtener todas las mensualidades pagadas (facturas pagadas) del año actual
    detalles_pagados = DetalleFactura.objects.filter(
        factura__cliente=estudiante,
        factura__anho_escolar=anho_escolar,
        factura__estado='pagada',
        concepto__tipo='mensualidad',
        mes__isnull=False,
        anio=anio_actual
    ).values_list('mes', flat=True).distinct()
    
    meses_pagados = list(detalles_pagados)
    
    # Crear lista de meses del año con estado de pago
    meses_nombres = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]
    
    mensualidades_estado = []
    for i in range(1, 13):
        mensualidades_estado.append({
            'numero': i,
            'nombre': meses_nombres[i-1],
            'pagado': i in meses_pagados
        })
    
    context = {
        'titulo': f'Facturas de {estudiante.get_full_name()}',
        'anho_escolar': anho_escolar,
        'estudiante': estudiante,
        'facturas': facturas,
        'total_facturas': total_facturas,
        'total_adeudado': total_adeudado,
        'total_pagado': total_pagado,
        'saldo_pendiente': saldo_pendiente,
        'facturas_pendientes': facturas_pendientes,
        'facturas_pagadas': facturas_pagadas,
        'mensualidades_estado': mensualidades_estado,
        'anio_actual': anio_actual,
    }
    return render(request, 'cobros/facturas_estudiante.html', context)


@login_required
def facturas_cliente(request, cliente_id):
    """Ver todas las facturas de un cliente (sistema de ventas)"""
    if request.user.rol not in ['Secretaria', 'Administrador', 'Vendedor', 'Gerente']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from .models import Factura
    from django.db.models import Sum
    
    # Buscar cliente (puede ser rol 'Estudiante' o 'Cliente')
    cliente = get_object_or_404(CustomUser, id=cliente_id, rol__in=['Estudiante', 'Cliente'])
    
    # Obtener todas las facturas del cliente
    facturas = Factura.objects.filter(
        cliente=cliente
    ).prefetch_related('detalles', 'pagos').order_by('-fecha_emision')
    
    # Estadísticas (excluyendo facturas anuladas)
    facturas_validas = facturas.exclude(estado='anulada')
    total_facturas = facturas_validas.count()
    total_adeudado = sum(f.total for f in facturas_validas)
    total_pagado = sum(f.monto_pagado for f in facturas_validas)
    saldo_pendiente = total_adeudado - total_pagado
    
    facturas_pendientes = facturas_validas.filter(estado__in=['pendiente', 'parcial']).count()
    facturas_pagadas = facturas_validas.filter(estado='pagada').count()
    
    context = {
        'titulo': f'Facturas de {cliente.get_full_name()}',
        'cliente': cliente,
        'facturas': facturas,
        'total_facturas': total_facturas,
        'total_adeudado': total_adeudado,
        'total_pagado': total_pagado,
        'saldo_pendiente': saldo_pendiente,
        'facturas_pendientes': facturas_pendientes,
        'facturas_pagadas': facturas_pagadas,
    }
    return render(request, 'cobros/facturas_cliente.html', context)


@login_required
@user_passes_test(lambda u: u.rol == 'Administrador')
def anular_facturas_confirmar(request):
    """Vista para confirmar anulación de facturas con código de seguridad"""
    from .models import Factura, CodigoAnulacion
    from django.utils import timezone
    
    # Obtener IDs de facturas a anular desde la sesión
    facturas_ids = request.session.get('facturas_a_anular', [])
    
    if not facturas_ids:
        messages.error(request, 'No hay facturas seleccionadas para anular.')
        return redirect('facturas_list')
    
    # Obtener las facturas
    facturas = Factura.objects.filter(id__in=facturas_ids).exclude(estado='anulada')
    
    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo_anulacion', '').strip().upper()
        motivo = request.POST.get('motivo_anulacion', '').strip()
        
        # Validar código
        if not CodigoAnulacion.validar_codigo(codigo_ingresado):
            messages.error(request, 'Código de anulación incorrecto.')
            context = {
                'titulo': 'Anular Facturas',
                'facturas': facturas,
                'error_codigo': True,
            }
            return render(request, 'cobros/anular_facturas_confirmar.html', context)
        
        # Validar motivo
        if not motivo or len(motivo) < 10:
            messages.error(request, 'Debe proporcionar un motivo de anulación (mÃ­nimo 10 caracteres).')
            context = {
                'titulo': 'Anular Facturas',
                'facturas': facturas,
                'codigo_valido': True,
            }
            return render(request, 'cobros/anular_facturas_confirmar.html', context)
        
        # Anular las facturas
        facturas_anuladas = 0
        for factura in facturas:
            factura.estado = 'anulada'
            factura.anulado_por = request.user
            factura.fecha_anulacion = timezone.now()
            factura.motivo_anulacion = motivo
            factura.save()
            facturas_anuladas += 1
        
        # Limpiar sesión
        del request.session['facturas_a_anular']
        
        messages.success(request, f'Se anularon {facturas_anuladas} factura(s) correctamente.')
        return redirect('facturas_list')
    
    # Obtener código activo para mostrar (solo para administrador y director)
    codigo_activo = None
    if request.user.rol in ['Administrador', 'Director']:
        codigo_activo = CodigoAnulacion.obtener_codigo_actual()
    
    context = {
        'titulo': 'Anular Facturas',
        'facturas': facturas,
        'codigo_activo': codigo_activo,
    }
    return render(request, 'cobros/anular_facturas_confirmar.html', context)


@login_required
def factura_anular(request, factura_id):
    """Vista para anular una factura individual con código de seguridad"""
    from .models import Factura, CodigoAnulacion
    from django.utils import timezone
    
    # Verificar permisos (solo Administrador, Director y Secretaria pueden anular)
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tiene permisos para anular facturas.')
        return redirect('facturas_list')
    
    # Obtener la factura
    factura = get_object_or_404(Factura, id=factura_id)
    
    # Verificar que no estÃ© ya anulada
    if factura.estado == 'anulada':
        messages.warning(request, 'Esta factura ya está anulada.')
        return redirect('factura_detalle', factura_id=factura_id)
    
    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo_anulacion', '').strip()
        motivo = request.POST.get('motivo_anulacion', '').strip()
        
        # Validar código
        if not CodigoAnulacion.validar_codigo(codigo_ingresado):
            messages.error(request, 'Código de anulación incorrecto.')
            return redirect('factura_detalle', factura_id=factura_id)
        
        # Validar motivo
        if not motivo or len(motivo) < 10:
            messages.error(request, 'Debe proporcionar un motivo de anulación (mÃ­nimo 10 caracteres).')
            return redirect('factura_detalle', factura_id=factura_id)
        
        # Anular la factura
        factura.estado = 'anulada'
        factura.anulado_por = request.user
        factura.fecha_anulacion = timezone.now()
        factura.motivo_anulacion = motivo
        factura.save()
        
        messages.success(request, f'Factura {factura.numero_factura} anulada correctamente.')
        return redirect('factura_detalle', factura_id=factura_id)
    
    # Si es GET, redirigir al detalle de la factura (el modal se mostrarÃ¡ allÃ­)
    return redirect('factura_detalle', factura_id=factura_id)


@login_required
@user_passes_test(lambda u: u.rol == 'Administrador')
def codigo_anulacion_ver(request):
    """Vista para ver el código de anulación actual"""
    from .models import CodigoAnulacion
    
    codigo_activo = CodigoAnulacion.obtener_codigo_actual()
    
    # Obtener historial de códigos (últimos 10)
    historial = CodigoAnulacion.objects.all().order_by('-creado')[:10]
    
    context = {
        'titulo': 'Código de AnulaciÃ³n de Facturas',
        'codigo_activo': codigo_activo,
        'historial': historial,
    }
    return render(request, 'cobros/codigo_anulacion_ver.html', context)


@login_required
def log_usuarios_eliminados(request):
    """Vista para ver el log de usuarios eliminados - Solo Administrador y Secretaria"""
    from .models import SecurityLog
    
    # Solo Administradores y Secretaria pueden ver este log
    if request.user.rol not in ['Administrador', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Filtrar logs de tipo ADMIN_ACTION relacionados con eliminación de usuarios
    logs_eliminacion = SecurityLog.objects.filter(
        tipo_evento='ADMIN_ACTION',
        descripcion__icontains='ELIMINACIÃN DE USUARIO'
    ).select_related('usuario').order_by('-fecha')[:100]
    
    context = {
        'titulo': 'Log de Usuarios Eliminados',
        'logs': logs_eliminacion,
    }
    return render(request, 'users/log_usuarios_eliminados.html', context)


# ===========================
# VISTAS DE CONCEPTOS DE PAGO (TARIFAS ESTÃNDAR)
# ===========================

@login_required
def conceptos_list(request):
    """Vista para listar conceptos de pago (tarifas estándar) - Solo Administrador"""
    from .models import ConceptoPago
    
    if request.user.rol != 'Administrador':
        messages.error(request, 'Solo el Administrador puede gestionar conceptos estándar.')
        return redirect('tarifas_list')
    
    conceptos = ConceptoPago.objects.all().order_by('tipo', 'nombre')
    
    # Verificar si hay conceptos estándar configurados
    conceptos_estandar = conceptos.filter(es_estandar=True, activo=True)
    tiene_mensualidad_estandar = conceptos_estandar.filter(tipo='mensualidad').exists()
    tiene_inscripcion_estandar = conceptos_estandar.filter(tipo='inscripcion').exists()
    
    context = {
        'titulo': 'Conceptos de Pago (Tarifas EstÃ¡ndar)',
        'conceptos': conceptos,
        'tiene_mensualidad_estandar': tiene_mensualidad_estandar,
        'tiene_inscripcion_estandar': tiene_inscripcion_estandar,
    }
    return render(request, 'cobros/conceptos_list.html', context)


@login_required
def concepto_create(request):
    """Vista para crear un concepto de pago - Solo Administrador"""
    if request.user.rol != 'Administrador':
        messages.error(request, 'Solo el Administrador puede crear conceptos.')
        return redirect('tarifas_list')
    
    if request.method == 'POST':
        from .forms import ConceptoPagoForm
        form = ConceptoPagoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Concepto de pago creado correctamente.')
            return redirect('conceptos_list')
    else:
        from .forms import ConceptoPagoForm
        form = ConceptoPagoForm()
    
    context = {
        'titulo': 'Crear Concepto de Pago',
        'form': form,
    }
    return render(request, 'cobros/concepto_form.html', context)


@login_required
def concepto_edit(request, pk):
    """Vista para editar un concepto de pago - Solo Administrador"""
    from .models import ConceptoPago
    
    if request.user.rol != 'Administrador':
        messages.error(request, 'Solo el Administrador puede editar conceptos.')
        return redirect('tarifas_list')
    
    concepto = get_object_or_404(ConceptoPago, pk=pk)
    
    if request.method == 'POST':
        from .forms import ConceptoPagoForm
        form = ConceptoPagoForm(request.POST, instance=concepto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Concepto actualizado correctamente.')
            return redirect('conceptos_list')
    else:
        from .forms import ConceptoPagoForm
        form = ConceptoPagoForm(instance=concepto)
    
    context = {
        'titulo': 'Editar Concepto de Pago',
        'form': form,
        'concepto': concepto,
    }
    return render(request, 'cobros/concepto_form.html', context)


@login_required
def concepto_delete(request, pk):
    """Vista para eliminar un concepto de pago - Solo Administrador"""
    from .models import ConceptoPago, TarifaEstudiante, DetalleFactura
    from django.db.models import ProtectedError
    
    if request.user.rol != 'Administrador':
        messages.error(request, 'Solo el Administrador puede eliminar conceptos.')
        return redirect('tarifas_list')
    
    concepto = get_object_or_404(ConceptoPago, pk=pk)
    
    if request.method == 'POST':
        nombre = concepto.nombre
        try:
            concepto.delete()
            messages.success(request, f'Concepto "{nombre}" eliminado correctamente.')
            return redirect('conceptos_list')
        except ProtectedError as e:
            # Contar referencias
            tarifas_count = TarifaEstudiante.objects.filter(concepto=concepto).count()
            facturas_count = DetalleFactura.objects.filter(concepto=concepto).count()
            
            error_msg = f'No se puede eliminar el concepto "{nombre}" porque está siendo utilizado en '
            partes = []
            if tarifas_count > 0:
                partes.append(f'{tarifas_count} tarifa(s) de estudiante(s)')
            if facturas_count > 0:
                partes.append(f'{facturas_count} factura(s)')
            
            error_msg += ' y '.join(partes) + '. Debe eliminar o modificar estas referencias primero, o marcar el concepto como inactivo en lugar de eliminarlo.'
            messages.error(request, error_msg)
            return redirect('conceptos_list')
    
    # Verificar si hay tarifas o facturas usando este concepto
    tarifas_count = TarifaEstudiante.objects.filter(concepto=concepto).count()
    facturas_count = DetalleFactura.objects.filter(concepto=concepto).count()
    total_count = tarifas_count + facturas_count
    
    context = {
        'titulo': 'Eliminar Concepto',
        'concepto': concepto,
        'tarifas_count': tarifas_count,
        'facturas_count': facturas_count,
        'total_count': total_count,
        'puede_eliminar': total_count == 0,
    }
    return render(request, 'cobros/concepto_confirm_delete.html', context)

#============================
@login_required
def inventario_lista_completa(request):
    """Lista completa de productos y servicios disponibles"""
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from .models import Articulo, ConceptoPago
    from django.db.models import Q
    
    # Filtros
    search = request.GET.get('search', '')
    tipo_filtro = request.GET.get('tipo', '')  # 'producto', 'servicio', 'todos'
    solo_activos = request.GET.get('activos', '1') == '1'
    
    # Lista consolidada de items
    items = []
    
    # Obtener artículos (productos)
    articulos = Articulo.objects.select_related('categoria')
    if solo_activos:
        articulos = articulos.filter(activo=True)
    
    if search:
        articulos = articulos.filter(
            Q(codigo_barras__icontains=search) |
            Q(nombre__icontains=search) |
            Q(descripcion__icontains=search)
        )
    
    if not tipo_filtro or tipo_filtro == 'producto':
        for articulo in articulos:
            items.append({
                'id': articulo.id,
                'tipo': 'producto',
                'tipo_display': 'Producto',
                'codigo': articulo.codigo_barras or 'N/A',
                'nombre': articulo.nombre,
                'descripcion': articulo.descripcion or '',
                'categoria': articulo.categoria.nombre if articulo.categoria else 'Sin categoría',
                'precio': articulo.precio_venta,
                'stock_actual': articulo.stock_actual,
                'stock_minimo': articulo.stock_minimo,
                'aplica_itbis': articulo.aplica_itbis,
                'activo': articulo.activo,
                'permite_descuento': articulo.permite_descuento,
                'link_editar': f'/inventario/articulos/{articulo.id}/editar/',
                'link_detalle': f'/inventario/articulos/{articulo.id}/',
            })
    
    # Obtener servicios (conceptos de pago)
    conceptos = ConceptoPago.objects.all()
    if solo_activos:
        conceptos = conceptos.filter(activo=True)
    
    if search:
        conceptos = conceptos.filter(
            Q(nombre__icontains=search) |
            Q(descripcion__icontains=search)
        )
    
    if not tipo_filtro or tipo_filtro == 'servicio':
        for concepto in conceptos:
            # Determinar si tiene precio fijo
            tiene_precio_fijo = concepto.tipo not in ['mensualidad', 'inscripcion', 'transporte']
            
            items.append({
                'id': concepto.id,
                'tipo': 'servicio',
                'tipo_display': concepto.get_tipo_display(),
                'codigo': 'SERV',
                'nombre': concepto.nombre,
                'descripcion': concepto.descripcion or '',
                'categoria': concepto.get_tipo_display(),
                'precio': concepto.monto if tiene_precio_fijo else None,
                'stock_actual': None,  # Los servicios no tienen stock
                'stock_minimo': None,
                'aplica_itbis': False,
                'activo': concepto.activo,
                'permite_descuento': True,
                'es_estandar': concepto.es_estandar,
                'link_editar': f'/conceptos/editar/{concepto.id}/',
                'link_detalle': None,
            })
    
    # Ordenar items por nombre
    items.sort(key=lambda x: x['nombre'])
    
    # PaginaciÃ³n
    from django.core.paginator import Paginator
    paginator = Paginator(items, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_productos = Articulo.objects.filter(activo=True).count()
    total_servicios = ConceptoPago.objects.filter(activo=True).count()
    
    context = {
        'titulo': 'Inventario Completo - Productos y Servicios',
        'page_obj': page_obj,
        'search': search,
        'tipo_filtro': tipo_filtro,
        'solo_activos': solo_activos,
        'total_productos': total_productos,
        'total_servicios': total_servicios,
        'total_items': total_productos + total_servicios,
    }
    return render(request, 'inventario/lista_completa.html', context)


# ===========================
# VISTAS DE INVENTARIO
# ===========================

@login_required
def inventario_dashboard(request):
    """Dashboard del inventario"""
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from .models import Articulo, CategoriaArticulo, MovimientoInventario
    
    # Estadísticas
    total_articulos = Articulo.objects.filter(activo=True).count()
    articulos_bajo_stock = Articulo.objects.filter(activo=True, stock_actual__lte=F('stock_minimo')).count()
    categorias_count = CategoriaArticulo.objects.filter(activa=True).count()
    
    # Valor del inventario
    valor_inventario = Articulo.objects.filter(activo=True).aggregate(
        total=Sum(F('stock_actual') * F('precio_compra'))
    )['total'] or 0
    
    # Ãltimos movimientos
    ultimos_movimientos = MovimientoInventario.objects.select_related(
        'articulo', 'usuario'
    ).order_by('-fecha')[:10]
    
    # Artículos con bajo stock
    articulos_criticos = Articulo.objects.filter(
        activo=True,
        stock_actual__lte=F('stock_minimo')
    ).order_by('stock_actual')[:10]
    
    context = {
        'titulo': 'Gestion de Inventario',
        'total_articulos': total_articulos,
        'articulos_bajo_stock': articulos_bajo_stock,
        'categorias_count': categorias_count,
        'valor_inventario': valor_inventario,
        'ultimos_movimientos': ultimos_movimientos,
        'articulos_criticos': articulos_criticos,
    }
    return render(request, 'inventario/dashboard.html', context)


@login_required
def articulos_list(request):
    """Lista de artículos"""
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from .models import Articulo, CategoriaArticulo
    from django.db.models import Q
    
    # Filtros
    search = request.GET.get('search', '')
    categoria_id = request.GET.get('categoria', '')
    tipo = request.GET.get('tipo', '')
    solo_activos = request.GET.get('activos', '1') == '1'
    
    articulos = Articulo.objects.select_related('categoria', 'creado_por')
    
    if solo_activos:
        articulos = articulos.filter(activo=True)
    
    if search:
        articulos = articulos.filter(
            Q(codigo_barras__icontains=search) |
            Q(nombre__icontains=search) |
            Q(descripcion__icontains=search)
        )
    
    if categoria_id:
        articulos = articulos.filter(categoria_id=categoria_id)
    
    if tipo:
        articulos = articulos.filter(tipo=tipo)
    
    articulos = articulos.order_by('nombre')
    
    # PaginaciÃ³n
    from django.core.paginator import Paginator
    paginator = Paginator(articulos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Categorías para filtro
    categorias = CategoriaArticulo.objects.filter(activa=True).order_by('nombre')
    
    context = {
        'titulo': 'Artículos',
        'page_obj': page_obj,
        'search': search,
        'categoria_id': categoria_id,
        'tipo': tipo,
        'solo_activos': solo_activos,
        'categorias': categorias,
    }
    return render(request, 'inventario/articulos_list.html', context)
@login_required
def inventario_articulos_pdf(request):
    """Genera PDF con la lista de todos los artículos/productos"""
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from .models import Articulo, CategoriaArticulo
    from django.template.loader import render_to_string
    from xhtml2pdf import pisa
    from django.http import HttpResponse
    from django.utils import timezone
    import io
    
    # Obtener todos los artículos activos
    articulos = Articulo.objects.select_related('categoria').filter(activo=True).order_by('categoria__nombre', 'nombre')
    # Agrupar por categoría
    categorias = {}
    for articulo in articulos:
        cat_nombre = articulo.categoria.nombre if articulo.categoria else 'Sin categoría'
        if cat_nombre not in categorias:
            categorias[cat_nombre] = []
        categorias[cat_nombre].append(articulo)
    
    # Estadísticas
    total_articulos = articulos.count()
    total_categorias = CategoriaArticulo.objects.filter(activa=True).count()
    valor_total = sum(art.precio_venta * art.stock_actual for art in articulos)
    articulos_bajo_stock = articulos.filter(stock_actual__lte=F('stock_minimo')).count()

    # Calcular el valor total de compra (opcional, para mostrar en el PDF)
    valor_total_compra = sum(art.precio_compra * art.stock_actual for art in articulos)

    context = {
        'titulo': 'Lista de Productos',
        'fecha_generacion': timezone.now(),
        'generado_por': request.user.get_full_name(),
        'articulos': articulos,
        'categorias': categorias,
        'total_articulos': total_articulos,
        'total_categorias': total_categorias,
        'valor_total': valor_total,
        'valor_total_compra': valor_total_compra,
        'articulos_bajo_stock': articulos_bajo_stock,
        'escuela_nombre': getattr(settings, 'ESCUELA_NOMBRE', 'Escuela'),
        'escuela_rnc': getattr(settings, 'ESCUELA_RNC', ''),
        'escuela_telefono': getattr(settings, 'ESCUELA_TELEFONO', ''),
        'escuela_direccion': getattr(settings, 'ESCUELA_DIRECCION', ''),
    }
    
    # Renderizar template para PDF
    html_string = render_to_string('inventario/articulos_pdf.html', context)
    
    # Crear el PDF
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html_string.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        filename = f"lista_productos_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    else:
        messages.error(request, 'Error al generar el PDF.')
        return redirect('inventario_lista_completa')


@login_required
def inventario_servicios_pdf(request):
    """Genera PDF con la lista de todos los servicios/conceptos"""
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from .models import ConceptoPago
    from django.template.loader import render_to_string
    from xhtml2pdf import pisa
    from django.http import HttpResponse
    from django.utils import timezone
    import io
    
    # Obtener todos los conceptos activos
    conceptos = ConceptoPago.objects.filter(activo=True).order_by('tipo', 'nombre')
    
    # Agrupar por tipo
    tipos = {}
    for concepto in conceptos:
        tipo_display = concepto.get_tipo_display()
        if tipo_display not in tipos:
            tipos[tipo_display] = []
        tipos[tipo_display].append(concepto)
    
    # Estadísticas
    total_conceptos = conceptos.count()
    conceptos_estandar = conceptos.filter(es_estandar=True).count()
    
    context = {
        'titulo': 'Lista de Servicios',
        'fecha_generacion': timezone.now(),
        'generado_por': request.user.get_full_name(),
        'conceptos': conceptos,
        'tipos': tipos,
        'total_conceptos': total_conceptos,
        'conceptos_estandar': conceptos_estandar,
        'escuela_nombre': getattr(settings, 'ESCUELA_NOMBRE', 'Escuela'),
        'escuela_rnc': getattr(settings, 'ESCUELA_RNC', ''),
        'escuela_telefono': getattr(settings, 'ESCUELA_TELEFONO', ''),
        'escuela_direccion': getattr(settings, 'ESCUELA_DIRECCION', ''),
    }
    
    # Renderizar template para PDF
    html_string = render_to_string('inventario/servicios_pdf.html', context)
    
    # Crear el PDF
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html_string.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        filename = f"lista_servicios_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    else:
        messages.error(request, 'Error al generar el PDF.')
        return redirect('inventario_lista_completa')

@login_required
def articulo_eliminar(request, articulo_id):
    """Eliminar artÃ­culo con código de seguridad"""
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para eliminar artículos.')
        return redirect('articulos_list')
    
    from .models import Articulo, DetalleFactura, CodigoAnulacion
    from django.utils import timezone
    
    articulo = get_object_or_404(Articulo, id=articulo_id)
    
    # Verificar si ya está inactivo
    if not articulo.activo:
        messages.warning(request, 'Este artÃ­culo ya está inactivo.')
        return redirect('articulo_detalle', articulo_id=articulo_id)
    
    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo_anulacion', '').strip()
        motivo = request.POST.get('motivo_eliminacion', '').strip()
        
        # Validar código de anulación
        if not CodigoAnulacion.validar_codigo(codigo_ingresado):
            messages.error(request, 'Código de seguridad incorrecto.')
            return redirect('articulo_detalle', articulo_id=articulo_id)
        
        # Validar motivo
        if not motivo or len(motivo) < 10:
            messages.error(request, 'Debe proporcionar un motivo de eliminación (mÃ­nimo 10 caracteres).')
            return redirect('articulo_detalle', articulo_id=articulo_id)
        
        nombre = articulo.nombre
        codigo = articulo.codigo_barras
        
        # Verificar si el artÃ­culo ha sido usado en facturas
        detalles_con_articulo = DetalleFactura.objects.filter(articulo=articulo).count()
        
        if detalles_con_articulo > 0:
            # Marcar como inactivo con registro de motivo
            articulo.activo = False
            articulo.save()
            
            messages.warning(
                request, 
                f'El artÃ­culo "{nombre}" ha sido usado en {detalles_con_articulo} factura(s), '
                f'se marcÃ³ como inactivo. Motivo: {motivo}'
            )
        else:
            # Si no ha sido usado, se puede eliminar completamente
            articulo.delete()
            messages.success(request, f'ArtÃ­culo "{codigo} - {nombre}" eliminado exitosamente. Motivo: {motivo}')
        
        return redirect('articulos_list')
    
    # Si es GET, redirigir al detalle del artÃ­culo (el modal se mostrarÃ¡ allÃ­)
    return redirect('articulo_detalle', articulo_id=articulo_id)



@login_required
def articulo_crear(request):
    """Crear nuevo artÃ­culo"""
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from .models import Articulo, CategoriaArticulo
    
    if request.method == 'POST':
        try:
            articulo = Articulo(
                codigo_barras=request.POST.get('codigo_barras', '').strip(),
                nombre=request.POST['nombre'],
                descripcion=request.POST.get('descripcion', ''),
                tipo=request.POST.get('tipo', 'producto'),
                precio_compra=request.POST.get('precio_compra', 0) or 0,
                precio_venta=request.POST['precio_venta'],
                precio_minimo=request.POST.get('precio_minimo') or None,
                stock_actual=request.POST.get('stock_actual', 0) or 0,
                stock_minimo=request.POST.get('stock_minimo', 0) or 0,
                stock_maximo=request.POST.get('stock_maximo') or None,
                unidad_medida=request.POST.get('unidad_medida', 'unidad'),
                aplica_itbis=request.POST.get('aplica_itbis') == 'on',
                permite_descuento=request.POST.get('permite_descuento') == 'on',
                creado_por=request.user
            )
            
            categoria_id = request.POST.get('categoria')
            if categoria_id:
                articulo.categoria_id = categoria_id
            
            articulo.save()
            messages.success(request, f'ArtÃ­culo {articulo.codigo_barras} creado exitosamente.')
            return redirect('articulos_list')
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"ERROR al crear artÃ­culo: {error_detail}")
            messages.error(request, f'Error al crear artÃ­culo: {str(e)}')
    
    categorias = CategoriaArticulo.objects.filter(activa=True).order_by('nombre')
    
    context = {
        'titulo': 'Nuevo ArtÃ­culo',
        'categorias': categorias,
    }
    return render(request, 'inventario/articulo_form.html', context)


@login_required
def articulo_editar(request, articulo_id):
    """Editar artÃ­culo"""
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from .models import Articulo, CategoriaArticulo
    
    articulo = get_object_or_404(Articulo, id=articulo_id)
    
    if request.method == 'POST':
        try:
            articulo.codigo_barras = request.POST.get('codigo_barras', '').strip() or None
            articulo.nombre = request.POST['nombre']
            articulo.descripcion = request.POST.get('descripcion', '')
            articulo.tipo = request.POST.get('tipo', 'producto')
            articulo.precio_compra = request.POST.get('precio_compra', 0)
            articulo.precio_venta = request.POST['precio_venta']
            articulo.precio_minimo = request.POST.get('precio_minimo') or None
            articulo.stock_actual = request.POST.get('stock_actual', 0)
            articulo.stock_minimo = request.POST.get('stock_minimo', 0)
            articulo.stock_maximo = request.POST.get('stock_maximo') or None
            articulo.unidad_medida = request.POST.get('unidad_medida', 'unidad')
            articulo.aplica_itbis = request.POST.get('aplica_itbis') == 'on'
            articulo.permite_descuento = request.POST.get('permite_descuento') == 'on'
            articulo.activo = request.POST.get('activo') == 'on'
            
            categoria_id = request.POST.get('categoria')
            if categoria_id:
                articulo.categoria_id = categoria_id
            else:
                articulo.categoria = None
            
            articulo.save()
            messages.success(request, f'ArtÃ­culo {articulo.codigo_barras} actualizado exitosamente.')
            return redirect('articulos_list')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar artÃ­culo: {str(e)}')
    
    categorias = CategoriaArticulo.objects.filter(activa=True).order_by('nombre')
    
    context = {
        'titulo': 'Editar ArtÃ­culo',
        'articulo': articulo,
        'categorias': categorias,
    }
    return render(request, 'inventario/articulo_form.html', context)


@login_required
def articulo_detalle(request, articulo_id):
    """Ver detalle del artÃ­culo"""
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from .models import Articulo, MovimientoInventario
    
    articulo = get_object_or_404(Articulo.objects.select_related('categoria', 'creado_por'), id=articulo_id)
    
    # Ãltimos movimientos
    movimientos = MovimientoInventario.objects.filter(
        articulo=articulo
    ).select_related('usuario', 'factura').order_by('-fecha')[:20]
    
    context = {
        'titulo': f'ArtÃ­culo: {articulo.nombre}',
        'articulo': articulo,
        'movimientos': movimientos,
    }
    return render(request, 'inventario/articulo_detalle.html', context)


@login_required
def categorias_list(request):
    """Lista de categorías"""
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from .models import CategoriaArticulo
    
    categorias = CategoriaArticulo.objects.annotate(
        total_articulos=Count('articulos')
    ).order_by('nombre')
    
    context = {
        'titulo': 'Categorías de Artículos',
        'categorias': categorias,
    }
    return render(request, 'inventario/categorias_list.html', context)


@login_required
def categoria_crear(request):
    """Crear nueva categoría"""
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('categorias_list')
    
    from .models import CategoriaArticulo
    
    if request.method == 'POST':
        try:
            # Si el checkbox no está marcado, request.POST.get('activa') será None
            # Por defecto, una nueva categoría debe estar activa
            activa = request.POST.get('activa') == 'on' if 'activa' in request.POST else True
            
            categoria = CategoriaArticulo(
                nombre=request.POST['nombre'],
                descripcion=request.POST.get('descripcion', ''),
                activa=activa
            )
            categoria.save()
            messages.success(request, f'Categoría "{categoria.nombre}" creada exitosamente.')
            return redirect('categorias_list')
            
        except Exception as e:
            messages.error(request, f'Error al crear categoría: {str(e)}')
    
    context = {
        'titulo': 'Nueva Categoría',
    }
    return render(request, 'inventario/categoria_form.html', context)


@login_required
def categoria_editar(request, categoria_id):
    """Editar categoría"""
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('categorias_list')
    
    from .models import CategoriaArticulo
    
    categoria = get_object_or_404(CategoriaArticulo, id=categoria_id)
    
    if request.method == 'POST':
        try:
            categoria.nombre = request.POST['nombre']
            categoria.descripcion = request.POST.get('descripcion', '')
            categoria.activa = request.POST.get('activa') == 'on'
            categoria.save()
            messages.success(request, f'Categoría "{categoria.nombre}" actualizada exitosamente.')
            return redirect('categorias_list')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar categoría: {str(e)}')
    
    context = {
        'titulo': 'Editar Categoría',
        'categoria': categoria,
    }
    return render(request, 'inventario/categoria_form.html', context)


@login_required
def categoria_eliminar(request, categoria_id):
    """Eliminar categoría"""
    if request.user.rol not in ['Administrador']:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('categorias_list')
    
    from .models import CategoriaArticulo
    
    categoria = get_object_or_404(CategoriaArticulo, id=categoria_id)
    
    if request.method == 'POST':
        nombre = categoria.nombre
        # Los artículos quedarÃ¡n sin categoría (FK permite null=True)
        categoria.delete()
        messages.success(request, f'Categoría "{nombre}" eliminada exitosamente.')
        return redirect('categorias_list')
    
    return redirect('categorias_list')


# ==================== REPORTES DE VENTAS ====================

@login_required
def reportes_ventas(request):
    """Dashboard principal de reportes de ventas"""
    if request.user.rol not in ['Administrador', 'Secretaria', 'Director']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from .models import Factura, DetalleFactura, ConfiguracionEscuela, PagoFactura
    from django.db.models import Sum, Count, Avg, Q, F, DecimalField, ExpressionWrapper
    from datetime import datetime, timedelta
    from django.utils import timezone

    config_escuela = ConfiguracionEscuela.get_configuracion()
    
    # Obtener parámetros de filtro
    periodo = request.GET.get('periodo', 'dia')  # dia, semana, mes, anio, personalizado (por defecto: hoy)
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    usuario_id = request.GET.get('usuario', '')  # Filtro por usuario
    export_pdf = request.GET.get('export', '')  # ParÃ¡metro para exportar PDF
    
    # Calcular rango de fechas según el período
    hoy = timezone.localtime(timezone.now())
    
    if periodo == 'dia':
        fecha_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)
        titulo_periodo = f"Hoy - {fecha_inicio.strftime('%d/%m/%Y')}"
    elif periodo == 'semana':
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        fecha_inicio = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)
        titulo_periodo = f"Esta Semana - {fecha_inicio.strftime('%d/%m')} al {fecha_fin.strftime('%d/%m/%Y')}"
    elif periodo == 'mes':
        fecha_inicio = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)
        titulo_periodo = f"Este Mes - {fecha_inicio.strftime('%B %Y')}"
    elif periodo == 'anio':
        fecha_inicio = hoy.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)
        titulo_periodo = f"Este Año - {fecha_inicio.year}"
    elif periodo == 'personalizado' and fecha_inicio and fecha_fin:
        fecha_inicio = timezone.make_aware(datetime.strptime(fecha_inicio, '%Y-%m-%d'))
        fecha_fin = timezone.make_aware(datetime.strptime(fecha_fin + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        titulo_periodo = f"{fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}"
    else:
        # Por defecto, el mes actual
        fecha_inicio = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)
        titulo_periodo = f"Este Mes - {fecha_inicio.strftime('%B %Y')}"
        periodo = 'mes'
    
    # Filtrar facturas por período
    facturas = Factura.objects.filter(
        fecha_emision__gte=fecha_inicio,
        fecha_emision__lte=fecha_fin
    ).exclude(estado='anulada')
    
    # Filtro por usuario: Administrador puede ver todos, Secretaria solo sus ventas
    if request.user.rol == 'Secretaria':
        # Secretarias solo ven sus propias ventas
        facturas = facturas.filter(creado_por=request.user)
        usuario_filtrado = request.user
    elif request.user.rol == 'Administrador' and usuario_id:
        # Administrador puede filtrar por usuario especÃ­fico
        from .models import CustomUser
        try:
            usuario_filtrado = CustomUser.objects.get(id=usuario_id)
            facturas = facturas.filter(creado_por=usuario_filtrado)
        except CustomUser.DoesNotExist:
            usuario_filtrado = None
    else:
        # Administrador sin filtro ve todo
        usuario_filtrado = None
    
    # ================================================================
    # PAGOS REALES: Filtrar pagos por fecha_pago (NO por fecha_emision)
    # Esto permite que pagos parciales de hoy se contabilicen hoy,
    # independientemente de cuándo se emitió la factura
    # ================================================================
    pagos_periodo = PagoFactura.objects.filter(
        fecha_pago__gte=fecha_inicio,
        fecha_pago__lte=fecha_fin
    ).exclude(factura__estado='anulada')
    
    # Aplicar filtro de usuario a los pagos
    if request.user.rol == 'Secretaria':
        pagos_periodo = pagos_periodo.filter(registrado_por=request.user)
    elif request.user.rol == 'Administrador' and usuario_id and usuario_filtrado:
        pagos_periodo = pagos_periodo.filter(registrado_por=usuario_filtrado)
    
    # Estadísticas generales
    # IMPORTANTE: total_cobrado viene de los PAGOS del período (fecha_pago)
    # total_facturado viene de las FACTURAS emitidas en el período (fecha_emision)
    total_facturado = facturas.aggregate(total=Sum('total'))['total'] or 0
    total_cobrado = pagos_periodo.aggregate(total=Sum('monto'))['total'] or 0  # PAGOS REALES
    total_ventas = total_cobrado  # Para reportes, lo importante es lo que se ha cobrado HOY
    
    total_facturas = facturas.count()
    promedio_venta = facturas.aggregate(promedio=Avg('total'))['promedio'] or 0
    total_descuentos = facturas.aggregate(total_desc=Sum('descuento'))['total_desc'] or 0
    total_impuestos = facturas.aggregate(total_imp=Sum('impuesto'))['total_imp'] or 0
    
    # Facturas por estado (métricas operativas)
    facturas_pendientes = facturas.filter(estado='pendiente').count()
    facturas_pagadas = facturas.filter(estado='pagada').count()
    facturas_parciales = facturas.filter(estado='parcial').count()
    
    # Ventas por día (para gráfico) - Agrupar PAGOS por fecha_pago
    ventas_por_dia = pagos_periodo.extra(
        select={'dia': 'DATE(fecha_pago)'}
    ).values('dia').annotate(
        monto_cobrado=Sum('monto'),  # Total realmente cobrado ese día
        cantidad=Count('id')  # Cantidad de pagos
    ).order_by('dia')
    
    # También calcular facturas emitidas por día (para comparación)
    facturas_por_dia = facturas.extra(
        select={'dia': 'DATE(fecha_emision)'}
    ).values('dia').annotate(
        monto_facturado=Sum('total'),
        cantidad_facturas=Count('id')
    ).order_by('dia')
    
    # Top artículos mÃ¡s vendidos
    from .models import Articulo
    from django.db.models import Case, When, Value
    
    detalles_query = DetalleFactura.objects.filter(
        factura__fecha_emision__gte=fecha_inicio,
        factura__fecha_emision__lte=fecha_fin,
        factura__estado__in=['pagada', 'parcial']
    )
    
    # Aplicar filtro de usuario a los detalles
    if request.user.rol == 'Secretaria':
        detalles_query = detalles_query.filter(factura__creado_por=request.user)
    elif request.user.rol == 'Administrador' and usuario_id and usuario_filtrado:
        detalles_query = detalles_query.filter(factura__creado_por=usuario_filtrado)
    
    # ExpresiÃ³n para calcular ingresos con ITBIS (protegido contra divisiÃ³n por cero)
    ingresos_con_itbis = ExpressionWrapper(
        Case(
            When(
                factura__subtotal__gt=0,
                then=(F('cantidad') * F('precio_unitario') - F('descuento')) * 
                     (F('factura__total') / F('factura__subtotal'))
            ),
            default=F('cantidad') * F('precio_unitario') - F('descuento'),
            output_field=DecimalField(max_digits=15, decimal_places=2)
        ),
        output_field=DecimalField(max_digits=15, decimal_places=2)
    )
    
    top_articulos = detalles_query.filter(
    ).exclude(
        articulo=None
    ).values(
        'articulo__nombre', 'articulo__codigo_barras'
    ).annotate(
        total_vendido=Sum('cantidad'),
        ingresos=Sum(ingresos_con_itbis)
    ).order_by('-total_vendido')[:10]
    
    # TODOS los artículos vendidos (para detalle completo)
    todos_articulos = detalles_query.filter(
    ).exclude(
        articulo=None
    ).values(
        'articulo__nombre', 'articulo__codigo_barras'
    ).annotate(
        total_vendido=Sum('cantidad'),
        ingresos=Sum(ingresos_con_itbis)
    ).order_by('-ingresos')
    
    # TODOS los conceptos/servicios vendidos (para detalle completo)
    todos_conceptos = detalles_query.filter(
    ).exclude(
        concepto=None
    ).values(
        'concepto__nombre', 'concepto__tipo'
    ).annotate(
        total_vendido=Sum('cantidad'),
        ingresos=Sum(ingresos_con_itbis)
    ).order_by('-ingresos')
    
    # Combinar artículos y conceptos en una lista unificada
    todos_items_vendidos = []
    
    # Agregar artículos
    for articulo in todos_articulos:
        todos_items_vendidos.append({
            'tipo': 'Producto',
            'codigo': articulo.get('articulo__codigo_barras', 'N/A'),
            'nombre': articulo.get('articulo__nombre', ''),
            'cantidad': articulo.get('total_vendido', 0),
            'ingresos': articulo.get('ingresos', 0)
        })
    
    # Agregar conceptos/servicios
    for concepto in todos_conceptos:
        tipo_concepto = concepto.get('concepto__tipo', 'servicio')
        if tipo_concepto == 'mensualidad':
            tipo_label = 'Mensualidad'
        elif tipo_concepto == 'inscripcion':
            tipo_label = 'InscripciÃ³n'
        else:
            tipo_label = 'Servicio'
            
        todos_items_vendidos.append({
            'tipo': tipo_label,
            'codigo': 'SERV',
            'nombre': concepto.get('concepto__nombre', ''),
            'cantidad': concepto.get('total_vendido', 0),
            'ingresos': concepto.get('ingresos', 0)
        })
    
    # Ordenar por ingresos descendente
    todos_items_vendidos.sort(key=lambda x: x['ingresos'], reverse=True)
    
    # Top conceptos mÃ¡s facturados
    from .models import ConceptoPago
    top_conceptos = detalles_query.filter(
    ).exclude(
        concepto=None
    ).values(
        'concepto__nombre', 'concepto__tipo'
    ).annotate(
        cantidad_ventas=Count('id'),
        ingresos=Sum(ingresos_con_itbis)
    ).order_by('-ingresos')[:10]
    
    # Ventas por estudiante/cliente (top 10) - basado en PAGOS del período
    top_estudiantes = pagos_periodo.values(
        'factura__cliente__first_name', 
        'factura__cliente__last_name',
        'factura__cliente__codigo_barras'
    ).annotate(
        monto_pagado_total=Sum('monto'),  # Total realmente pagado en este período
        num_facturas=Count('factura__id', distinct=True)  # Número de facturas distintas
    ).order_by('-monto_pagado_total')[:10]
    
    # Comparación con período anterior
    if periodo == 'dia':
        fecha_inicio_anterior = fecha_inicio - timedelta(days=1)
        fecha_fin_anterior = fecha_inicio - timedelta(seconds=1)
    elif periodo == 'semana':
        fecha_inicio_anterior = fecha_inicio - timedelta(days=7)
        fecha_fin_anterior = fecha_inicio - timedelta(seconds=1)
    elif periodo == 'mes':
        if fecha_inicio.month == 1:
            fecha_inicio_anterior = fecha_inicio.replace(year=fecha_inicio.year-1, month=12)
        else:
            fecha_inicio_anterior = fecha_inicio.replace(month=fecha_inicio.month-1)
        fecha_fin_anterior = fecha_inicio - timedelta(seconds=1)
    else:
        fecha_inicio_anterior = fecha_inicio.replace(year=fecha_inicio.year-1)
        fecha_fin_anterior = fecha_inicio - timedelta(seconds=1)
    
    # Comparar con PAGOS del período anterior (no facturas)
    pagos_anterior = PagoFactura.objects.filter(
        fecha_pago__gte=fecha_inicio_anterior,
        fecha_pago__lte=fecha_fin_anterior
    ).exclude(factura__estado='anulada')
    
    # Aplicar el mismo filtro de usuario al período anterior
    if request.user.rol == 'Secretaria':
        pagos_anterior = pagos_anterior.filter(registrado_por=request.user)
    elif request.user.rol == 'Administrador' and usuario_id and usuario_filtrado:
        pagos_anterior = pagos_anterior.filter(registrado_por=usuario_filtrado)
    
    total_ventas_anterior = pagos_anterior.aggregate(total=Sum('monto'))['total'] or 0
    
    # Calcular variaciÃ³n porcentual
    if total_ventas_anterior > 0:
        variacion_porcentual = ((total_ventas - total_ventas_anterior) / total_ventas_anterior) * 100
    else:
        variacion_porcentual = 100 if total_ventas > 0 else 0
    
    # NUEVAS MÃTRICAS AVANZADAS
    
    # Análisis de efectivo (ya calculado arriba como total_cobrado)
    # total_cobrado ya está definido arriba con todas las facturas
    total_pendiente_cobro = facturas.filter(estado__in=['pendiente', 'parcial']).aggregate(
        pendiente=Sum(ExpressionWrapper(F('total') - F('monto_pagado'), output_field=DecimalField()))
    )['pendiente'] or 0
    
    # Ventas por método de pago - usar PAGOS reales del período
    ventas_por_metodo = pagos_periodo.values('metodo_pago').annotate(
        monto_cobrado=Sum('monto'),  # Total realmente cobrado por este método
        cantidad=Count('id')  # Cantidad de pagos
    ).order_by('-monto_cobrado')
    
    # Análisis de productos vs servicios
    ingresos_productos_query = DetalleFactura.objects.filter(
        factura__fecha_emision__gte=fecha_inicio,
        factura__fecha_emision__lte=fecha_fin,
        articulo__isnull=False
    )
    
    # Aplicar filtro de usuario
    if request.user.rol == 'Secretaria':
        ingresos_productos_query = ingresos_productos_query.filter(factura__creado_por=request.user)
    elif request.user.rol == 'Administrador' and usuario_id and usuario_filtrado:
        ingresos_productos_query = ingresos_productos_query.filter(factura__creado_por=usuario_filtrado)
    
    ingresos_productos = ingresos_productos_query.annotate(
        ingreso_con_itbis=Case(
            When(
                factura__subtotal__gt=0,
                then=(F('cantidad') * F('precio_unitario') - F('descuento')) * 
                     (F('factura__total') / F('factura__subtotal'))
            ),
            default=F('cantidad') * F('precio_unitario') - F('descuento'),
            output_field=DecimalField(max_digits=15, decimal_places=2)
        )
    ).aggregate(total=Sum('ingreso_con_itbis'))['total'] or 0
    
    ingresos_servicios_query = DetalleFactura.objects.filter(
        factura__fecha_emision__gte=fecha_inicio,
        factura__fecha_emision__lte=fecha_fin,
        concepto__isnull=False
    )
    
    # Aplicar filtro de usuario
    if request.user.rol == 'Secretaria':
        ingresos_servicios_query = ingresos_servicios_query.filter(factura__creado_por=request.user)
    elif request.user.rol == 'Administrador' and usuario_id and usuario_filtrado:
        ingresos_servicios_query = ingresos_servicios_query.filter(factura__creado_por=usuario_filtrado)
    
    ingresos_servicios = ingresos_servicios_query.annotate(
        ingreso_con_itbis=Case(
            When(
                factura__subtotal__gt=0,
                then=(F('cantidad') * F('precio_unitario') - F('descuento')) * 
                     (F('factura__total') / F('factura__subtotal'))
            ),
            default=F('cantidad') * F('precio_unitario') - F('descuento'),
            output_field=DecimalField(max_digits=15, decimal_places=2)
        )
    ).aggregate(total=Sum('ingreso_con_itbis'))['total'] or 0
    
    # Ventas por hora del día (solo para día y semana) - usar fecha_pago
    ventas_por_hora = None
    if periodo in ['dia', 'semana']:
        ventas_por_hora = pagos_periodo.extra(
            select={'hora': "EXTRACT(HOUR FROM fecha_pago)"}
        ).values('hora').annotate(
            monto_cobrado=Sum('monto'),  # Total realmente cobrado en esa hora
            cantidad=Count('id')  # Cantidad de pagos
        ).order_by('hora')
    
    # Ticket promedio por cliente
    ticket_promedio_cliente = facturas.values('cliente').annotate(
        total_gastado=Sum('monto_pagado')  # Usar monto_pagado para reflejar lo realmente pagado
    ).aggregate(promedio=Avg('total_gastado'))['promedio'] or 0
    
    # Tasa de conversión (facturas pagadas vs total)
    tasa_pago = (facturas_pagadas / total_facturas * 100) if total_facturas > 0 else 0
    
    # Porcentaje de pendiente
    pendiente_porcentaje = (total_pendiente_cobro / total_ventas * 100) if total_ventas > 0 else 0
    
    # Análisis de descuentos
    facturas_con_descuento = facturas.filter(descuento__gt=0).count()
    porcentaje_descuento_promedio = (total_descuentos / total_ventas * 100) if total_ventas > 0 else 0
    
    # Top clientes por cantidad de pagos realizados en el período
    clientes_frecuentes = pagos_periodo.values(
        'factura__cliente__first_name', 
        'factura__cliente__last_name',
        'factura__cliente__id'
    ).annotate(
        num_compras=Count('id'),  # Número de pagos realizados
        monto_pagado_total=Sum('monto'),  # Total realmente pagado
        ticket_promedio=Avg('monto')  # Promedio por pago
    ).order_by('-num_compras')[:10]
    
    # Detalles de mensualidades vs otros conceptos
    mensualidades_query = DetalleFactura.objects.filter(
        factura__fecha_emision__gte=fecha_inicio,
        factura__fecha_emision__lte=fecha_fin,
        concepto__tipo='mensualidad'
    )
    
    # Aplicar filtro de usuario
    if request.user.rol == 'Secretaria':
        mensualidades_query = mensualidades_query.filter(factura__creado_por=request.user)
    elif request.user.rol == 'Administrador' and usuario_id and usuario_filtrado:
        mensualidades_query = mensualidades_query.filter(factura__creado_por=usuario_filtrado)
    
    mensualidades = mensualidades_query.annotate(
        ingreso_con_itbis=Case(
            When(
                factura__subtotal__gt=0,
                then=(F('cantidad') * F('precio_unitario') - F('descuento')) * 
                     (F('factura__total') / F('factura__subtotal'))
            ),
            default=F('cantidad') * F('precio_unitario') - F('descuento'),
            output_field=DecimalField(max_digits=15, decimal_places=2)
        )
    ).aggregate(
        total=Sum('ingreso_con_itbis'),
        cantidad=Count('id')
    )
    
    ingresos_mensualidades = mensualidades['total'] or 0
    cantidad_mensualidades = mensualidades['cantidad'] or 0
    
    # Ventas por día de la semana - usar fecha_pago de los pagos
    ventas_por_dia_semana = pagos_periodo.extra(
        select={'dia_semana': "EXTRACT(DOW FROM fecha_pago)"}
    ).values('dia_semana').annotate(
        monto_cobrado=Sum('monto'),  # Total realmente cobrado ese día de la semana
        cantidad=Count('id')  # Cantidad de pagos
    ).order_by('dia_semana')
    
    # Mapear días de la semana
    dias_semana = {0: 'Domingo', 1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado'}
    for venta in ventas_por_dia_semana:
        venta['nombre_dia'] = dias_semana.get(venta['dia_semana'], 'Desconocido')
    
    # Lista de usuarios para filtro (solo para administradores y directores)
    usuarios_vendedores = None
    if request.user.rol in ['Administrador', 'Director']:
        from .models import CustomUser
        usuarios_vendedores = CustomUser.objects.filter(
            rol__in=['Administrador', 'Secretaria'],
            is_active=True
        ).order_by('first_name', 'last_name')
    
    # Calcular total general de items (suma de todos los ingresos)
    from decimal import Decimal
    total_general_items = sum([Decimal(str(item['ingresos'])) for item in todos_items_vendidos], Decimal('0'))
    
    context = {
        'titulo': 'Reportes de Ventas',
        'periodo': periodo,
        'titulo_periodo': titulo_periodo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'fecha_actual': timezone.now(),
        'usuario': request.user.get_full_name(),
        
        # Filtro de usuario
        'usuario_id': usuario_id,
        'usuario_filtrado': usuario_filtrado,
        'usuarios_vendedores': usuarios_vendedores,
        
        # Información de la escuela desde configuración
        'escuela_nombre': config_escuela.nombre_escuela or getattr(settings, 'ESCUELA_NOMBRE', 'Escuela'),
        'escuela_rnc': config_escuela.rnc or getattr(settings, 'ESCUELA_RNC', ''),
        'escuela_telefono': config_escuela.telefono or getattr(settings, 'ESCUELA_TELEFONO', ''),
        'escuela_direccion': config_escuela.direccion or getattr(settings, 'ESCUELA_DIRECCION', ''),
        'escuela_email': config_escuela.email or getattr(settings, 'ESCUELA_EMAIL', ''),
        'escuela_lema': config_escuela.lema or 'Excelencia Educativa y FormaciÃ³n Integral',
        
        # Estadísticas bÃ¡sicas
        'total_ventas': total_ventas,  # Total cobrado (lo importante para reportes)
        'total_facturado': total_facturado,  # Total de todas las facturas
        'total_cobrado': total_cobrado,  # Total realmente cobrado (incluye parciales)
        'total_facturas': total_facturas,
        'promedio_venta': promedio_venta,
        'total_descuentos': total_descuentos,
        'total_impuestos': total_impuestos,
        
        # Estados
        'facturas_pendientes': facturas_pendientes,
        'facturas_pagadas': facturas_pagadas,
        'facturas_parciales': facturas_parciales,
        
        # Gráficos básicos
        'ventas_por_dia': list(ventas_por_dia),
        'top_articulos': list(top_articulos),
        'todos_articulos': list(todos_articulos),
        'todos_items_vendidos': todos_items_vendidos,
        'top_conceptos': list(top_conceptos),
        'top_estudiantes': list(top_estudiantes),
        
        # Comparación
        'total_ventas_anterior': total_ventas_anterior,
        'variacion_porcentual': variacion_porcentual,
        
        # NUEVAS MÃTRICAS
        'total_cobrado': total_cobrado,
        'total_pendiente_cobro': total_pendiente_cobro,
        'pendiente_porcentaje': pendiente_porcentaje,
        'ventas_por_metodo': list(ventas_por_metodo),
        'ingresos_productos': ingresos_productos,
        'ingresos_servicios': ingresos_servicios,
        'ventas_por_hora': list(ventas_por_hora) if ventas_por_hora else [],
        'ticket_promedio_cliente': ticket_promedio_cliente,
        'tasa_pago': tasa_pago,
        'facturas_con_descuento': facturas_con_descuento,
        'porcentaje_descuento_promedio': porcentaje_descuento_promedio,
        'clientes_frecuentes': list(clientes_frecuentes),
        'ingresos_mensualidades': ingresos_mensualidades,
        'cantidad_mensualidades': cantidad_mensualidades,
        'ventas_por_dia_semana': list(ventas_por_dia_semana),
        'total_general_items': total_general_items,
    }
    
    # Si se solicita exportar a PDF
    if export_pdf == 'pdf':
        from django.template.loader import render_to_string
        from xhtml2pdf import pisa
        from django.http import HttpResponse
        import io
        import base64

        pdf_context = context.copy()
        pdf_context['logo_base64'] = None

        if config_escuela.mostrar_logo_reportes and config_escuela.logo:
            try:
                with open(config_escuela.logo.path, 'rb') as img_file:
                    img_b64 = base64.b64encode(img_file.read()).decode('utf-8')
                    ext = config_escuela.logo.name.split('.')[-1].lower()
                    mime = 'jpeg' if ext in ['jpg', 'jpeg'] else ext
                    pdf_context['logo_base64'] = f"data:image/{mime};base64,{img_b64}"
            except Exception as e:
                print(f"Error cargando logo para PDF de ventas: {e}")

        # Renderizar template para PDF
        html_string = render_to_string('cobros/reportes_ventas_pdf.html', pdf_context)
        
        # Crear el PDF
        result = io.BytesIO()
        pdf = pisa.pisaDocument(io.BytesIO(html_string.encode("UTF-8")), result)
        
        if not pdf.err:
            # Crear respuesta HTTP con el PDF
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            filename = f"reporte_ventas_{periodo}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
        else:
            messages.error(request, 'Error al generar el PDF.')
            return redirect('reportes_ventas')
    
    return render(request, 'cobros/reportes_ventas.html', context)


# ==========================================
# LISTAS DE ESTUDIANTES POR CURSO
# ==========================================

@login_required
def lista_estudiantes_curso_info(request):
    """Lista de estudiantes con solo información personal"""
    curso_id = request.GET.get('curso')
    if not curso_id:
        messages.error(request, 'Debe especificar un curso.')
        return redirect('lista_cursos')
    
    curso = get_object_or_404(Curso, id=curso_id)
    
    # Obtener estudiantes Ãºnicos matriculados en el curso
    estudiantes = CustomUser.objects.filter(
        matriculas__materia__curso=curso,
        rol='Estudiante'
    ).distinct().order_by('first_name', 'last_name')
    
    context = {
        'curso': curso,
        'estudiantes': estudiantes,
        'titulo': f'Lista de Estudiantes - {curso.nombre}',
    }
    
    return render(request, 'est_forder/lista_estudiantes_info.html', context)


@login_required
def lista_estudiantes_curso_promedios(request):
    """Lista de estudiantes con promedios por materia"""
    curso_id = request.GET.get('curso')
    if not curso_id:
        messages.error(request, 'Debe especificar un curso.')
        return redirect('lista_cursos')
    
    curso = get_object_or_404(Curso, id=curso_id)
    
    # Obtener materias del curso
    materias = Materia.objects.filter(curso=curso).order_by('nombre')
    
    # Obtener estudiantes con sus matrículas
    estudiantes_data = []
    estudiantes = CustomUser.objects.filter(
        matriculas__materia__curso=curso,
        rol='Estudiante'
    ).distinct().order_by('first_name', 'last_name')
    
    for estudiante in estudiantes:
        # Obtener matrículas del estudiante para las materias de este curso
        matriculas_dict = {}
        matriculas = Matricula.objects.filter(
            estudiante=estudiante,
            materia__curso=curso
        ).select_related('materia')
        
        for matricula in matriculas:
            matriculas_dict[matricula.materia.id] = {
                'promedio': matricula.promedio_final,
                'estado': matricula.estado
            }
        
        estudiantes_data.append({
            'estudiante': estudiante,
            'matriculas': matriculas_dict
        })
    
    context = {
        'curso': curso,
        'materias': materias,
        'estudiantes_data': estudiantes_data,
        'titulo': f'Promedios de Estudiantes - {curso.nombre}',
    }
    
    return render(request, 'est_forder/lista_estudiantes_promedios.html', context)


@login_required
def lista_estudiantes_curso_info_pdf(request):
    """Genera PDF de la lista de estudiantes con información personal"""
    curso_id = request.GET.get('curso')
    if not curso_id:
        messages.error(request, 'Debe especificar un curso.')
        return redirect('lista_cursos')
    
    curso = get_object_or_404(Curso, id=curso_id)
    
    # Obtener estudiantes Ãºnicos matriculados en el curso
    estudiantes = CustomUser.objects.filter(
        matriculas__materia__curso=curso,
        rol='Estudiante'
    ).distinct().order_by('first_name', 'last_name')
    
    # Renderizar el template PDF
    template = get_template("est_forder/lista_estudiantes_info_pdf.html")
    html = template.render({
        "curso": curso,
        "estudiantes": estudiantes,
        "request": request,
        "STATIC_ROOT": settings.STATIC_ROOT,
    })
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="lista_estudiantes_info_{curso.id}.pdf"'
    
    # Función para resolver rutas de archivos estáticos
    def link_callback(uri, rel):
        import os
        if os.path.isfile(uri):
            return uri
        if uri.startswith(settings.STATIC_ROOT):
            return uri
        clean_uri = uri.replace('/static/', '').replace('static/', '').lstrip('/')
        for static_dir in getattr(settings, 'STATICFILES_DIRS', []):
            path = os.path.join(static_dir, clean_uri)
            if os.path.isfile(path):
                return path
        path = os.path.join(settings.STATIC_ROOT, clean_uri)
        if os.path.isfile(path):
            return path
        return uri
    
    from xhtml2pdf import pisa
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    
    if pisa_status.err:
        return HttpResponse('Error al generar PDF', status=500)
    return response


@login_required
def lista_estudiantes_curso_promedios_pdf(request):
    """Genera PDF de la lista de estudiantes con promedios por materia"""
    curso_id = request.GET.get('curso')
    if not curso_id:
        messages.error(request, 'Debe especificar un curso.')
        return redirect('lista_cursos')
    
    curso = get_object_or_404(Curso, id=curso_id)
    
    # Obtener materias del curso
    materias = Materia.objects.filter(curso=curso).order_by('nombre')
    
    # Obtener estudiantes con sus matrículas
    estudiantes_data = []
    estudiantes = CustomUser.objects.filter(
        matriculas__materia__curso=curso,
        rol='Estudiante'
    ).distinct().order_by('first_name', 'last_name')
    
    for estudiante in estudiantes:
        matriculas_dict = {}
        matriculas = Matricula.objects.filter(
            estudiante=estudiante,
            materia__curso=curso
        ).select_related('materia')
        
        for matricula in matriculas:
            matriculas_dict[matricula.materia.id] = {
                'promedio': matricula.promedio_final,
                'estado': matricula.estado
            }
        
        estudiantes_data.append({
            'estudiante': estudiante,
            'matriculas': matriculas_dict
        })
    
    # Renderizar el template PDF
    template = get_template("est_forder/lista_estudiantes_promedios_pdf.html")
    html = template.render({
        "curso": curso,
        "materias": materias,
        "estudiantes_data": estudiantes_data,
        "request": request,
        "STATIC_ROOT": settings.STATIC_ROOT,
    })
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="lista_promedios_{curso.id}.pdf"'
    
    # Función para resolver rutas de archivos estáticos
    def link_callback(uri, rel):
        import os
        if os.path.isfile(uri):
            return uri
        if uri.startswith(settings.STATIC_ROOT):
            return uri
        clean_uri = uri.replace('/static/', '').replace('static/', '').lstrip('/')
        for static_dir in getattr(settings, 'STATICFILES_DIRS', []):
            path = os.path.join(static_dir, clean_uri)
            if os.path.isfile(path):
                return path
        path = os.path.join(settings.STATIC_ROOT, clean_uri)
        if os.path.isfile(path):
            return path
        return uri
    
    from xhtml2pdf import pisa
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    
    if pisa_status.err:
        return HttpResponse('Error al generar PDF', status=500)
    return response


# ============================================
# VISTAS DE CONTABILIDAD - PLAN DE CUENTAS
# ============================================

from .models import PlanCuentas
from .forms import PlanCuentasForm, PlanCuentasBusquedaForm
from django.db.models import Q, Count

@login_required
def plan_cuentas_list(request):
    """
    Vista para listar todas las cuentas contables con búsqueda y filtros
    """
    # Verificar permisos
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Obtener todas las cuentas
    cuentas = PlanCuentas.objects.all()
    
    # Aplicar filtros desde el formulario
    form = PlanCuentasBusquedaForm(request.GET)
    
    if form.is_valid():
        busqueda = form.cleaned_data.get('busqueda')
        tipo_cuenta = form.cleaned_data.get('tipo_cuenta')
        activo = form.cleaned_data.get('activo')
        es_detalle = form.cleaned_data.get('es_detalle')
        
        # Filtro de búsqueda
        if busqueda:
            cuentas = cuentas.filter(
                Q(codigo__icontains=busqueda) |
                Q(nombre__icontains=busqueda) |
                Q(descripcion__icontains=busqueda)
            )
        
        # Filtro por tipo de cuenta
        if tipo_cuenta:
            cuentas = cuentas.filter(tipo_cuenta=tipo_cuenta)
        
        # Filtro por estado activo
        if activo == 'true':
            cuentas = cuentas.filter(activo=True)
        elif activo == 'false':
            cuentas = cuentas.filter(activo=False)
        
        # Filtro por cuenta de detalle
        if es_detalle == 'true':
            cuentas = cuentas.filter(es_detalle=True)
        elif es_detalle == 'false':
            cuentas = cuentas.filter(es_detalle=False)
    
    # Ordenar por código
    cuentas = cuentas.order_by('codigo')
    
    # Calcular estadísticas
    stats = {
        'total': PlanCuentas.objects.count(),
        'activas': PlanCuentas.objects.filter(activo=True).count(),
        'inactivas': PlanCuentas.objects.filter(activo=False).count(),
        'detalle': PlanCuentas.objects.filter(es_detalle=True).count(),
        'agrupacion': PlanCuentas.objects.filter(es_detalle=False).count(),
        'activos': PlanCuentas.objects.filter(tipo_cuenta='ACTIVO').count(),
        'pasivos': PlanCuentas.objects.filter(tipo_cuenta='PASIVO').count(),
        'capital': PlanCuentas.objects.filter(tipo_cuenta='CAPITAL').count(),
        'ingresos': PlanCuentas.objects.filter(tipo_cuenta='INGRESO').count(),
        'gastos': PlanCuentas.objects.filter(tipo_cuenta='GASTO').count(),
        'costos': PlanCuentas.objects.filter(tipo_cuenta='COSTO').count(),
    }
    
    context = {
        'cuentas': cuentas,
        'form': form,
        'stats': stats,
    }
    
    return render(request, 'contabilidad/plan_cuentas_list.html', context)


@login_required
def plan_cuentas_crear(request):
    """
    Vista para crear una nueva cuenta contable
    """
    # Verificar permisos
    if request.user.rol not in ['Administrador', 'Director']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plan_cuentas_list')
    
    if request.method == 'POST':
        form = PlanCuentasForm(request.POST)
        if form.is_valid():
            cuenta = form.save(commit=False)
            cuenta.creado_por = request.user
            cuenta.save()
            messages.success(request, f'Cuenta contable "{cuenta.codigo} - {cuenta.nombre}" creada exitosamente.')
            return redirect('plan_cuentas_list')
    else:
        form = PlanCuentasForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Nueva Cuenta Contable',
        'accion': 'Crear',
    }
    
    return render(request, 'contabilidad/plan_cuentas_form.html', context)


@login_required
def plan_cuentas_editar(request, pk):
    """
    Vista para editar una cuenta contable existente
    """
    # Verificar permisos
    if request.user.rol not in ['Administrador', 'Director']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plan_cuentas_list')
    
    cuenta = get_object_or_404(PlanCuentas, pk=pk)
    
    # Verificar si la cuenta tiene movimientos
    if cuenta.tiene_movimientos():
        messages.warning(
            request, 
            'Esta cuenta tiene movimientos asociados. Solo puedes editar algunos campos.'
        )
    
    if request.method == 'POST':
        form = PlanCuentasForm(request.POST, instance=cuenta)
        if form.is_valid():
            cuenta_editada = form.save(commit=False)
            cuenta_editada.modificado_por = request.user
            cuenta_editada.save()
            messages.success(request, f'Cuenta "{cuenta_editada.codigo} - {cuenta_editada.nombre}" actualizada exitosamente.')
            return redirect('plan_cuentas_list')
    else:
        form = PlanCuentasForm(instance=cuenta)
        
        # Si tiene movimientos, deshabilitar algunos campos
        if cuenta.tiene_movimientos():
            form.fields['codigo'].disabled = True
            form.fields['tipo_cuenta'].disabled = True
            form.fields['naturaleza'].disabled = True
    
    context = {
        'form': form,
        'titulo': f'Editar Cuenta: {cuenta.codigo}',
        'accion': 'Actualizar',
        'cuenta': cuenta,
    }
    
    return render(request, 'contabilidad/plan_cuentas_form.html', context)


@login_required
def plan_cuentas_detalle(request, pk):
    """
    Vista para ver los detalles de una cuenta contable
    """
    # Verificar permisos
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    cuenta = get_object_or_404(PlanCuentas, pk=pk)
    
    # Obtener subcuentas
    subcuentas = cuenta.get_subcuentas_activas()
    
    # Calcular saldo actualizado
    saldo_calculado = cuenta.calcular_saldo()
    
    # Verificar si puede eliminarse
    puede_eliminar = cuenta.puede_eliminarse()
    
    context = {
        'cuenta': cuenta,
        'subcuentas': subcuentas,
        'saldo_calculado': saldo_calculado,
        'puede_eliminar': puede_eliminar,
        'ruta_completa': cuenta.get_ruta_completa(),
    }
    
    return render(request, 'contabilidad/plan_cuentas_detalle.html', context)


@login_required
def plan_cuentas_eliminar(request, pk):
    """
    Vista para eliminar una cuenta contable
    """
    # Verificar permisos
    if request.user.rol not in ['Administrador']:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('plan_cuentas_list')
    
    cuenta = get_object_or_404(PlanCuentas, pk=pk)
    
    # Verificar si puede eliminarse
    if not cuenta.puede_eliminarse():
        messages.error(
            request, 
            'No se puede eliminar esta cuenta porque tiene movimientos asociados o subcuentas.'
        )
        return redirect('plan_cuentas_detalle', pk=pk)
    
    if request.method == 'POST':
        codigo = cuenta.codigo
        nombre = cuenta.nombre
        cuenta.delete()
        messages.success(request, f'Cuenta "{codigo} - {nombre}" eliminada exitosamente.')
        return redirect('plan_cuentas_list')
    
    context = {
        'cuenta': cuenta,
    }
    
    return render(request, 'contabilidad/plan_cuentas_confirm_delete.html', context)


@login_required
def plan_cuentas_toggle_activo(request, pk):
    """
    Vista para activar/desactivar una cuenta contable (AJAX)
    """
    # Verificar permisos
    if request.user.rol not in ['Administrador', 'Director']:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    if request.method == 'POST':
        cuenta = get_object_or_404(PlanCuentas, pk=pk)
        cuenta.activo = not cuenta.activo
        cuenta.modificado_por = request.user
        cuenta.save()
        
        return JsonResponse({
            'success': True,
            'activo': cuenta.activo,
            'mensaje': f'Cuenta {"activada" if cuenta.activo else "desactivada"} exitosamente.'
        })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def plan_cuentas_obtener_subcuentas(request, pk):
    """
    API para obtener las subcuentas de una cuenta padre (AJAX)
    Ãtil para actualizar dinámicamente formularios
    """
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        cuenta = PlanCuentas.objects.get(pk=pk, activo=True)
        subcuentas = cuenta.get_subcuentas_activas().values(
            'id', 'codigo', 'nombre', 'tipo_cuenta', 'es_detalle'
        )
        
        return JsonResponse({
            'cuenta_padre': {
                'id': cuenta.id,
                'codigo': cuenta.codigo,
                'nombre': cuenta.nombre,
            },
            'subcuentas': list(subcuentas)
        })
    except PlanCuentas.DoesNotExist:
        return JsonResponse({'error': 'Cuenta no encontrada'}, status=404)


@login_required
def plan_cuentas_estructura_json(request):
    """
    API para obtener la estructura completa del plan de cuentas en formato JSON jerÃ¡rquico
    Ãtil para visualizaciones tipo Ã¡rbol
    """
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    def construir_arbol(cuenta_padre=None):
        """Función recursiva para construir el Ã¡rbol de cuentas"""
        if cuenta_padre:
            cuentas = PlanCuentas.objects.filter(
                cuenta_padre=cuenta_padre,
                activo=True
            ).order_by('codigo')
        else:
            cuentas = PlanCuentas.objects.filter(
                cuenta_padre__isnull=True,
                activo=True
            ).order_by('codigo')
        
        resultado = []
        for cuenta in cuentas:
            nodo = {
                'id': cuenta.id,
                'codigo': cuenta.codigo,
                'nombre': cuenta.nombre,
                'tipo_cuenta': cuenta.get_tipo_cuenta_display(),
                'saldo_actual': float(cuenta.saldo_actual),
                'es_detalle': cuenta.es_detalle,
                'nivel': cuenta.nivel,
                'hijos': construir_arbol(cuenta)
            }
            resultado.append(nodo)
        
        return resultado
    
    estructura = construir_arbol()
    
    return JsonResponse({
        'estructura': estructura,
        'total_cuentas': PlanCuentas.objects.filter(activo=True).count()
    })

# ============================================
# VISTAS DE ASIENTOS CONTABLES
# ============================================

from .models import AsientoContable, DetalleAsiento
from .forms import AsientoContableForm, DetalleAsientoForm, AsientoBusquedaForm, AnularAsientoForm
from decimal import Decimal
import json

@login_required
def asientos_list(request):
    """
    Vista para listar todos los asientos contables con búsqueda y filtros
    """
    # Verificar permisos
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Obtener todos los asientos
    asientos = AsientoContable.objects.all().prefetch_related('detalles')
    
    # Aplicar filtros
    form = AsientoBusquedaForm(request.GET)
    
    if form.is_valid():
        busqueda = form.cleaned_data.get('busqueda')
        tipo_asiento = form.cleaned_data.get('tipo_asiento')
        estado = form.cleaned_data.get('estado')
        fecha_desde = form.cleaned_data.get('fecha_desde')
        fecha_hasta = form.cleaned_data.get('fecha_hasta')
        
        if busqueda:
            asientos = asientos.filter(
                Q(numero_asiento__icontains=busqueda) |
                Q(concepto__icontains=busqueda) |
                Q(referencia__icontains=busqueda)
            )
        
        if tipo_asiento:
            asientos = asientos.filter(tipo_asiento=tipo_asiento)
        
        if estado:
            asientos = asientos.filter(estado=estado)
        
        if fecha_desde:
            asientos = asientos.filter(fecha_asiento__gte=fecha_desde)
        
        if fecha_hasta:
            asientos = asientos.filter(fecha_asiento__lte=fecha_hasta)
    
    # Calcular estadísticas
    stats = {
        'total': AsientoContable.objects.count(),
        'borradores': AsientoContable.objects.filter(estado='BORRADOR').count(),
        'contabilizados': AsientoContable.objects.filter(estado='CONTABILIZADO').count(),
        'anulados': AsientoContable.objects.filter(estado='ANULADO').count(),
        'total_debito': AsientoContable.objects.filter(
            estado='CONTABILIZADO'
        ).aggregate(total=Sum('total_debito'))['total'] or Decimal('0.00'),
        'total_credito': AsientoContable.objects.filter(
            estado='CONTABILIZADO'
        ).aggregate(total=Sum('total_credito'))['total'] or Decimal('0.00'),
    }
    
    context = {
        'asientos': asientos,
        'form': form,
        'stats': stats,
    }
    
    return render(request, 'contabilidad/asientos_list.html', context)


@login_required
def asiento_crear(request):
    """
    Vista para crear un nuevo asiento contable
    """
    # Verificar permisos
    if request.user.rol not in ['Administrador', 'Director']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('asientos_list')
    
    if request.method == 'POST':
        # Procesar formulario del asiento
        form = AsientoContableForm(request.POST)
        
        # Obtener datos de las lÃ­neas (JSON)
        lineas_json = request.POST.get('lineas_data', '[]')
        
        try:
            lineas_data = json.loads(lineas_json)
        except:
            lineas_data = []
        
        if form.is_valid() and lineas_data:
            # Crear el asiento
            asiento = form.save(commit=False)
            asiento.creado_por = request.user
            asiento.save()
            
            # Crear las lÃ­neas
            total_debito = Decimal('0.00')
            total_credito = Decimal('0.00')
            
            for idx, linea_data in enumerate(lineas_data, start=1):
                try:
                    cuenta = PlanCuentas.objects.get(id=linea_data['cuenta_id'])
                    
                    detalle = DetalleAsiento(
                        asiento=asiento,
                        linea=idx,
                        cuenta=cuenta,
                        descripcion=linea_data['descripcion'],
                        debito=Decimal(linea_data.get('debito', 0)),
                        credito=Decimal(linea_data.get('credito', 0)),
                        centro_costo=linea_data.get('centro_costo', ''),
                        referencia_interna=linea_data.get('referencia', '')
                    )
                    detalle.save()
                    
                    total_debito += detalle.debito
                    total_credito += detalle.credito
                    
                except Exception as e:
                    messages.error(request, f'Error en lÃ­nea {idx}: {str(e)}')
                    asiento.delete()
                    return redirect('asiento_crear')
            
            # Actualizar totales del asiento
            asiento.total_debito = total_debito
            asiento.total_credito = total_credito
            asiento.save()
            
            messages.success(
                request,
                f'Asiento {asiento.numero_asiento} creado exitosamente.'
            )
            return redirect('asiento_detalle', pk=asiento.pk)
        else:
            if not lineas_data:
                messages.error(request, 'Debe agregar al menos una lÃ­nea al asiento.')
    else:
        form = AsientoContableForm()
    
    # Obtener cuentas activas de detalle para el selector
    cuentas = PlanCuentas.objects.filter(
        es_detalle=True,
        activo=True
    ).order_by('codigo')
    
    context = {
        'form': form,
        'cuentas': cuentas,
        'titulo': 'Crear Nuevo Asiento Contable',
    }
    
    return render(request, 'contabilidad/asiento_form.html', context)


@login_required
def asiento_detalle(request, pk):
    """
    Vista para ver los detalles de un asiento contable
    """
    # Verificar permisos
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    asiento = get_object_or_404(AsientoContable, pk=pk)
    detalles = asiento.detalles.all().select_related('cuenta')
    
    context = {
        'asiento': asiento,
        'detalles': detalles,
    }
    
    return render(request, 'contabilidad/asiento_detalle.html', context)


@login_required
def asiento_contabilizar(request, pk):
    """
    Vista para contabilizar un asiento (cambiar de borrador a contabilizado)
    """
    # Verificar permisos
    if request.user.rol not in ['Administrador', 'Director']:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('asiento_detalle', pk=pk)
    
    asiento = get_object_or_404(AsientoContable, pk=pk)
    
    if request.method == 'POST':
        if asiento.puede_contabilizarse():
            try:
                asiento.contabilizar(request.user)
                messages.success(
                    request,
                    f'Asiento {asiento.numero_asiento} contabilizado exitosamente.'
                )
            except Exception as e:
                messages.error(request, f'Error al contabilizar: {str(e)}')
        else:
            messages.error(
                request,
                'El asiento no puede ser contabilizado. Verifique que estÃ© cuadrado y tenga lÃ­neas.'
            )
        
        return redirect('asiento_detalle', pk=pk)
    
    context = {
        'asiento': asiento,
    }
    
    return render(request, 'contabilidad/asiento_confirm_contabilizar.html', context)


@login_required
def asiento_anular(request, pk):
    """
    Vista para anular un asiento contable
    """
    # Verificar permisos
    if request.user.rol not in ['Administrador']:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('asiento_detalle', pk=pk)
    
    asiento = get_object_or_404(AsientoContable, pk=pk)
    
    if not asiento.puede_anularse():
        messages.error(request, 'Este asiento no puede ser anulado.')
        return redirect('asiento_detalle', pk=pk)
    
    if request.method == 'POST':
        form = AnularAsientoForm(request.POST)
        if form.is_valid():
            motivo = form.cleaned_data['motivo_anulacion']
            try:
                asiento.anular(request.user, motivo)
                messages.success(
                    request,
                    f'Asiento {asiento.numero_asiento} anulado exitosamente.'
                )
                return redirect('asiento_detalle', pk=pk)
            except Exception as e:
                messages.error(request, f'Error al anular: {str(e)}')
    else:
        form = AnularAsientoForm()
    
    context = {
        'asiento': asiento,
        'form': form,
    }
    
    return render(request, 'contabilidad/asiento_anular.html', context)


@login_required
def asiento_eliminar(request, pk):
    """
    Vista para eliminar un asiento (solo borradores)
    """
    # Verificar permisos
    if request.user.rol not in ['Administrador']:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('asiento_detalle', pk=pk)
    
    asiento = get_object_or_404(AsientoContable, pk=pk)
    
    if asiento.estado != 'BORRADOR':
        messages.error(request, 'Solo se pueden eliminar asientos en borrador.')
        return redirect('asiento_detalle', pk=pk)
    
    if request.method == 'POST':
        numero = asiento.numero_asiento
        asiento.delete()
        messages.success(request, f'Asiento {numero} eliminado exitosamente.')
        return redirect('asientos_list')
    
    context = {
        'asiento': asiento,
    }
    
    return render(request, 'contabilidad/asiento_confirm_delete.html', context)


@login_required
def asiento_imprimir(request, pk):
    """
    Vista para imprimir/generar PDF del asiento contable
    """
    # Verificar permisos
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    asiento = get_object_or_404(AsientoContable, pk=pk)
    detalles = asiento.detalles.all().select_related('cuenta')
    
    context = {
        'asiento': asiento,
        'detalles': detalles,
    }
    
    return render(request, 'contabilidad/asiento_imprimir.html', context)


# ============================================
# DASHBOARD Y REPORTES CONTABLES
# ============================================

from django.db.models.functions import Coalesce

@login_required
def contabilidad_dashboard(request):
    """
    Dashboard principal de contabilidad con KPIs y resumen
    """
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Estadísticas generales
    stats = {
        'total_cuentas': PlanCuentas.objects.filter(activo=True).count(),
        'cuentas_detalle': PlanCuentas.objects.filter(es_detalle=True, activo=True).count(),
        'total_asientos': AsientoContable.objects.count(),
        'asientos_borrador': AsientoContable.objects.filter(estado='BORRADOR').count(),
        'asientos_contabilizados': AsientoContable.objects.filter(estado='CONTABILIZADO').count(),
    }
    
    # Totales por tipo de cuenta
    totales_tipo = {}
    for tipo in ['ACTIVO', 'PASIVO', 'CAPITAL', 'INGRESO', 'GASTO', 'COSTO']:
        total = PlanCuentas.objects.filter(
            tipo_cuenta=tipo,
            activo=True
        ).aggregate(total=Sum('saldo_actual'))['total'] or Decimal('0.00')
        totales_tipo[tipo] = total
    
    # Ãltimos asientos
    ultimos_asientos = AsientoContable.objects.all()[:10]
    
    # Cuentas con mayor movimiento
    cuentas_activas = PlanCuentas.objects.filter(
        es_detalle=True,
        activo=True
    ).annotate(
        num_movimientos=Count('movimientos_asiento')
    ).order_by('-num_movimientos')[:10]
    
    context = {
        'stats': stats,
        'totales_tipo': totales_tipo,
        'ultimos_asientos': ultimos_asientos,
        'cuentas_activas': cuentas_activas,
    }
    
    return render(request, 'contabilidad/dashboard.html', context)


@login_required
def libro_diario(request):
    """
    Libro Diario - Registro cronolÃ³gico de todos los asientos contables
    """
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    estado = request.GET.get('estado', 'CONTABILIZADO')
    
    # Query base
    asientos = AsientoContable.objects.all().prefetch_related('detalles__cuenta')
    
    # Aplicar filtros
    if estado:
        asientos = asientos.filter(estado=estado)
    
    if fecha_desde:
        asientos = asientos.filter(fecha_asiento__gte=fecha_desde)
    
    if fecha_hasta:
        asientos = asientos.filter(fecha_asiento__lte=fecha_hasta)
    
    asientos = asientos.order_by('fecha_asiento', 'numero_asiento')
    
    # Calcular totales
    totales = asientos.aggregate(
        total_debito=Sum('total_debito'),
        total_credito=Sum('total_credito')
    )
    
    context = {
        'asientos': asientos,
        'totales': totales,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'estado': estado,
    }
    
    return render(request, 'contabilidad/libro_diario.html', context)


@login_required
def libro_mayor(request):
    """
    Libro Mayor - Movimientos agrupados por cuenta
    """
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    cuenta_id = request.GET.get('cuenta_id')
    tipo_cuenta = request.GET.get('tipo_cuenta')
    
    # Obtener cuentas para el filtro
    cuentas_list = PlanCuentas.objects.filter(
        es_detalle=True,
        activo=True
    ).order_by('codigo')
    
    # Query de movimientos
    movimientos = DetalleAsiento.objects.filter(
        asiento__estado='CONTABILIZADO'
    ).select_related('asiento', 'cuenta')
    
    # Aplicar filtros
    if fecha_desde:
        movimientos = movimientos.filter(asiento__fecha_asiento__gte=fecha_desde)
    
    if fecha_hasta:
        movimientos = movimientos.filter(asiento__fecha_asiento__lte=fecha_hasta)
    
    if cuenta_id:
        movimientos = movimientos.filter(cuenta_id=cuenta_id)
    
    if tipo_cuenta:
        movimientos = movimientos.filter(cuenta__tipo_cuenta=tipo_cuenta)
    
    movimientos = movimientos.order_by('cuenta__codigo', 'asiento__fecha_asiento', 'asiento__numero_asiento')
    
    # Agrupar por cuenta
    cuentas_con_movimientos = {}
    for movimiento in movimientos:
        cuenta_codigo = movimiento.cuenta.codigo
        if cuenta_codigo not in cuentas_con_movimientos:
            cuentas_con_movimientos[cuenta_codigo] = {
                'cuenta': movimiento.cuenta,
                'movimientos': [],
                'total_debito': Decimal('0.00'),
                'total_credito': Decimal('0.00'),
                'saldo': Decimal('0.00'),
            }
        
        cuentas_con_movimientos[cuenta_codigo]['movimientos'].append(movimiento)
        cuentas_con_movimientos[cuenta_codigo]['total_debito'] += movimiento.debito
        cuentas_con_movimientos[cuenta_codigo]['total_credito'] += movimiento.credito
        
        # Calcular saldo según naturaleza
        if movimiento.cuenta.naturaleza == 'DEUDORA':
            cuentas_con_movimientos[cuenta_codigo]['saldo'] += movimiento.debito - movimiento.credito
        else:
            cuentas_con_movimientos[cuenta_codigo]['saldo'] += movimiento.credito - movimiento.debito
    
    context = {
        'cuentas_con_movimientos': cuentas_con_movimientos,
        'cuentas_list': cuentas_list,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'cuenta_id': cuenta_id,
        'tipo_cuenta': tipo_cuenta,
    }
    
    return render(request, 'contabilidad/libro_mayor.html', context)


@login_required
def balance_comprobacion(request):
    """
    Balance de ComprobaciÃ³n - Sumas y Saldos de todas las cuentas
    """
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Filtros
    fecha_hasta = request.GET.get('fecha_hasta')
    tipo_cuenta = request.GET.get('tipo_cuenta')
    
    # Obtener todas las cuentas de detalle
    cuentas = PlanCuentas.objects.filter(
        es_detalle=True,
        activo=True
    ).order_by('codigo')
    
    if tipo_cuenta:
        cuentas = cuentas.filter(tipo_cuenta=tipo_cuenta)
    
    # Calcular movimientos para cada cuenta
    balance_data = []
    totales = {
        'debito': Decimal('0.00'),
        'credito': Decimal('0.00'),
        'saldo_deudor': Decimal('0.00'),
        'saldo_acreedor': Decimal('0.00'),
    }
    
    for cuenta in cuentas:
        # Obtener movimientos contabilizados
        movimientos = cuenta.movimientos_asiento.filter(
            asiento__estado='CONTABILIZADO'
        )
        
        if fecha_hasta:
            movimientos = movimientos.filter(asiento__fecha_asiento__lte=fecha_hasta)
        
        # Calcular sumas
        sumas = movimientos.aggregate(
            debito=Sum('debito'),
            credito=Sum('credito')
        )
        
        debito = sumas['debito'] or Decimal('0.00')
        credito = sumas['credito'] or Decimal('0.00')
        
        # Calcular saldo según naturaleza
        if cuenta.naturaleza == 'DEUDORA':
            saldo = debito - credito
        else:
            saldo = credito - debito
        
        # Solo mostrar cuentas con movimiento
        if debito > 0 or credito > 0:
            balance_data.append({
                'cuenta': cuenta,
                'debito': debito,
                'credito': credito,
                'saldo': saldo,
                'saldo_deudor': saldo if saldo > 0 else Decimal('0.00'),
                'saldo_acreedor': abs(saldo) if saldo < 0 else Decimal('0.00'),
            })
            
            # Actualizar totales
            totales['debito'] += debito
            totales['credito'] += credito
            if saldo > 0:
                totales['saldo_deudor'] += saldo
            else:
                totales['saldo_acreedor'] += abs(saldo)
    
    context = {
        'balance_data': balance_data,
        'totales': totales,
        'fecha_hasta': fecha_hasta,
        'tipo_cuenta': tipo_cuenta,
    }
    
    return render(request, 'contabilidad/balance_comprobacion.html', context)


@login_required
def estado_resultados(request):
    """
    Estado de Resultados (P&L) - Ingresos vs Gastos
    """
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    # Obtener cuentas de ingresos y gastos
    ingresos = PlanCuentas.objects.filter(
        tipo_cuenta='INGRESO',
        es_detalle=True,
        activo=True
    ).order_by('codigo')
    
    gastos = PlanCuentas.objects.filter(
        tipo_cuenta__in=['GASTO', 'COSTO'],
        es_detalle=True,
        activo=True
    ).order_by('codigo')
    
    # Calcular montos
    ingresos_data = []
    total_ingresos = Decimal('0.00')
    
    for cuenta in ingresos:
        movimientos = cuenta.movimientos_asiento.filter(
            asiento__estado='CONTABILIZADO'
        )
        
        if fecha_desde:
            movimientos = movimientos.filter(asiento__fecha_asiento__gte=fecha_desde)
        if fecha_hasta:
            movimientos = movimientos.filter(asiento__fecha_asiento__lte=fecha_hasta)
        
        monto = movimientos.aggregate(
            total=Coalesce(Sum('credito'), Decimal('0.00')) - Coalesce(Sum('debito'), Decimal('0.00'))
        )['total'] or Decimal('0.00')
        
        if monto != 0:
            ingresos_data.append({
                'cuenta': cuenta,
                'monto': monto
            })
            total_ingresos += monto
    
    gastos_data = []
    total_gastos = Decimal('0.00')
    
    for cuenta in gastos:
        movimientos = cuenta.movimientos_asiento.filter(
            asiento__estado='CONTABILIZADO'
        )
        
        if fecha_desde:
            movimientos = movimientos.filter(asiento__fecha_asiento__gte=fecha_desde)
        if fecha_hasta:
            movimientos = movimientos.filter(asiento__fecha_asiento__lte=fecha_hasta)
        
        monto = movimientos.aggregate(
            total=Coalesce(Sum('debito'), Decimal('0.00')) - Coalesce(Sum('credito'), Decimal('0.00'))
        )['total'] or Decimal('0.00')
        
        if monto != 0:
            gastos_data.append({
                'cuenta': cuenta,
                'monto': monto
            })
            total_gastos += monto
    
    utilidad_neta = total_ingresos - total_gastos
    
    context = {
        'ingresos_data': ingresos_data,
        'gastos_data': gastos_data,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'utilidad_neta': utilidad_neta,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'contabilidad/estado_resultados.html', context)


@login_required
def balance_general(request):
    """
    Balance General - Estado de SituaciÃ³n Financiera (Activos, Pasivos, Patrimonio)
    """
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Fecha de corte
    fecha_corte = request.GET.get('fecha_corte')
    
    # Obtener cuentas por tipo
    activos = PlanCuentas.objects.filter(
        tipo_cuenta='ACTIVO',
        es_detalle=True,
        activo=True
    ).order_by('codigo')
    
    pasivos = PlanCuentas.objects.filter(
        tipo_cuenta='PASIVO',
        es_detalle=True,
        activo=True
    ).order_by('codigo')
    
    patrimonio = PlanCuentas.objects.filter(
        tipo_cuenta='CAPITAL',
        es_detalle=True,
        activo=True
    ).order_by('codigo')
    
    # Calcular saldos
    def calcular_saldos(cuentas, fecha_corte=None):
        data = []
        total = Decimal('0.00')
        
        for cuenta in cuentas:
            movimientos = cuenta.movimientos_asiento.filter(
                asiento__estado='CONTABILIZADO'
            )
            
            if fecha_corte:
                movimientos = movimientos.filter(asiento__fecha_asiento__lte=fecha_corte)
            
            if cuenta.naturaleza == 'DEUDORA':
                saldo = movimientos.aggregate(
                    total=Coalesce(Sum('debito'), Decimal('0.00')) - Coalesce(Sum('credito'), Decimal('0.00'))
                )['total'] or Decimal('0.00')
            else:
                saldo = movimientos.aggregate(
                    total=Coalesce(Sum('credito'), Decimal('0.00')) - Coalesce(Sum('debito'), Decimal('0.00'))
                )['total'] or Decimal('0.00')
            
            if saldo != 0:
                data.append({
                    'cuenta': cuenta,
                    'saldo': saldo
                })
                total += saldo
        
        return data, total
    
    activos_data, total_activos = calcular_saldos(activos, fecha_corte)
    pasivos_data, total_pasivos = calcular_saldos(pasivos, fecha_corte)
    patrimonio_data, total_patrimonio = calcular_saldos(patrimonio, fecha_corte)
    
    # El patrimonio debe equilibrar la ecuaciÃ³n contable
    total_pasivo_patrimonio = total_pasivos + total_patrimonio
    
    context = {
        'activos_data': activos_data,
        'pasivos_data': pasivos_data,
        'patrimonio_data': patrimonio_data,
        'total_activos': total_activos,
        'total_pasivos': total_pasivos,
        'total_patrimonio': total_patrimonio,
        'total_pasivo_patrimonio': total_pasivo_patrimonio,
        'fecha_corte': fecha_corte,
    }
    
    return render(request, 'contabilidad/balance_general.html', context)


@login_required
def consulta_cuenta(request, pk):
    """
    Consulta detallada de movimientos de una cuenta especÃ­fica
    """
    if request.user.rol not in ['Administrador', 'Director', 'Secretaria']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    cuenta = get_object_or_404(PlanCuentas, pk=pk)
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    # Obtener movimientos
    movimientos = cuenta.movimientos_asiento.filter(
        asiento__estado='CONTABILIZADO'
    ).select_related('asiento').order_by('asiento__fecha_asiento')
    
    if fecha_desde:
        movimientos = movimientos.filter(asiento__fecha_asiento__gte=fecha_desde)
    
    if fecha_hasta:
        movimientos = movimientos.filter(asiento__fecha_asiento__lte=fecha_hasta)
    
    # Calcular saldo corriente
    saldo_actual = Decimal('0.00')
    movimientos_con_saldo = []
    
    for mov in movimientos:
        if cuenta.naturaleza == 'DEUDORA':
            saldo_actual += mov.debito - mov.credito
        else:
            saldo_actual += mov.credito - mov.debito
        
        movimientos_con_saldo.append({
            'movimiento': mov,
            'saldo': saldo_actual
        })
    
    # Totales
    totales = movimientos.aggregate(
        total_debito=Sum('debito'),
        total_credito=Sum('credito')
    )
    
    context = {
        'cuenta': cuenta,
        'movimientos_con_saldo': movimientos_con_saldo,
        'totales': totales,
        'saldo_final': saldo_actual,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'contabilidad/consulta_cuenta.html', context)


# ============================================
# REGISTRO PÚBLICO DE ESCUELAS (MULTI-TENANT)
# ============================================

def registrar_empresa(request):
    """
    Vista pública para que nuevas empresas se registren en el sistema  
    Crea un nuevo TENANT (schema PostgreSQL separado) con django-tenants
    No requiere autenticación
    ✅ SEGURIDAD: Rate limiting, CAPTCHA, email confirmation
    """
    # Si ya está autenticado, redirigir al dashboard
    if request.user.is_authenticated:
        return redirect('lista_anhos_escolares')
    
    # 🔒 SEGURIDAD: Obtener IP y user agent
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # 🔒 SEGURIDAD: Verificar rate limiting (máximo 3 intentos por hora desde una IP)
    from .models import RegistroEscuelaAttempt
    if RegistroEscuelaAttempt.is_ip_blocked(ip_address, max_attempts=10, block_hours=1):
        messages.error(
            request,
            '⚠️ Demasiados intentos de registro desde tu IP. '
            'Por favor, intenta nuevamente en una hora. '
            'Esto es para prevenir el uso automatizado del sistema.'
        )
        return render(request, 'public/registro_escuela.html', {'ip_blocked': True})
    
    if request.method == 'POST':
        try:
            from django.db import connection
            from .tenant_models import Client, Domain
            
            # 🔒 SEGURIDAD: Verificar CAPTCHA
            recaptcha_response = request.POST.get('g-recaptcha-response')
            if not recaptcha_response:
                messages.error(request, '❌ Por favor, completa el CAPTCHA para verificar que eres humano.')
                RegistroEscuelaAttempt.record_attempt(
                    ip_address=ip_address,
                    nombre_corto='',
                    exitoso=False,
                    razon_fallo='Captcha no completado',
                    user_agent=user_agent
                )
                return render(request, 'public/registro_escuela.html')
            
            # Validar CAPTCHA con Google
            import urllib.request
            import urllib.parse
            import json
            
            data = urllib.parse.urlencode({
                'secret': settings.RECAPTCHA_PRIVATE_KEY,
                'response': recaptcha_response,
                'remoteip': ip_address
            }).encode()
            
            req = urllib.request.Request('https://www.google.com/recaptcha/api/siteverify', data=data)
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode())
            
            if not result.get('success'):
                messages.error(request, '❌ Verificación CAPTCHA fallida. Por favor, intenta nuevamente.')
                RegistroEscuelaAttempt.record_attempt(
                    ip_address=ip_address,
                    nombre_corto='',
                    exitoso=False,
                    razon_fallo='Verificación CAPTCHA fallida',
                    user_agent=user_agent
                )
                return render(request, 'public/registro_escuela.html')
            
            # Datos de la empresa
            nombre_empresa = request.POST.get('nombre_empresa')
            nombre_corto = request.POST.get('nombre_corto').lower().strip()
            email_empresa = request.POST.get('email_empresa')
            telefono_empresa = request.POST.get('telefono_empresa', '')
            direccion_empresa = request.POST.get('direccion_empresa', '')
            plan = request.POST.get('plan', 'prueba')
            max_usuarios = int(request.POST.get('max_usuarios', 50))
            
            # Datos del administrador
            admin_nombre = request.POST.get('admin_nombre')
            admin_email = request.POST.get('admin_email')
            admin_password = request.POST.get('admin_password')
            admin_password_confirm = request.POST.get('admin_password_confirm')
            
            # Validaciones
            if admin_password != admin_password_confirm:
                messages.error(request, 'Las contraseñas no coinciden.')
                RegistroEscuelaAttempt.record_attempt(
                    ip_address=ip_address,
                    nombre_corto=nombre_corto,
                    exitoso=False,
                    razon_fallo='Contraseñas no coinciden',
                    user_agent=user_agent
                )
                return render(request, 'public/registro_escuela.html')
            
            # Validar nombre corto (solo letras, números y guiones)
            import re
            if not re.match(r'^[a-z0-9-]+$', nombre_corto):
                messages.error(
                    request, 
                    'El nombre corto solo puede contener letras minúsculas, números y guiones.'
                )
                RegistroEscuelaAttempt.record_attempt(
                    ip_address=ip_address,
                    nombre_corto=nombre_corto,
                    exitoso=False,
                    razon_fallo='Formato de nombre_corto inválido',
                    user_agent=user_agent
                )
                return render(request, 'public/registro_escuela.html')
            
            # Verificar que el nombre corto no esté tomado (verifica Client con schema_name)
            if Client.objects.filter(schema_name=nombre_corto).exists():
                messages.error(
                    request, 
                    f'El subdominio "{nombre_corto}" ya está en uso. Por favor, elige otro.'
                )
                RegistroEscuelaAttempt.record_attempt(
                    ip_address=ip_address,
                    nombre_corto=nombre_corto,
                    exitoso=False,
                    razon_fallo='Nombre corto ya existe',
                    user_agent=user_agent
                )
                return render(request, 'public/registro_escuela.html')
            
            # Verificar que no exista dominio con ese nombre
            if Domain.objects.filter(domain=f'{nombre_corto}.localhost').exists():
                messages.error(
                    request, 
                    f'El dominio "{nombre_corto}.localhost" ya está en uso.'
                )
                RegistroEscuelaAttempt.record_attempt(
                    ip_address=ip_address,
                    nombre_corto=nombre_corto,
                    exitoso=False,
                    razon_fallo='Dominio ya existe',
                    user_agent=user_agent
                )
                return render(request, 'public/registro_escuela.html')
            
            # Verificar que el email de contacto no esté ya registrado
            if Client.objects.filter(email_contacto=email_empresa).exists():
                messages.error(
                    request, 
                    f'El correo electrónico "{email_empresa}" ya está registrado para otra empresa. '
                    'Por favor, usa un correo diferente.'
                )
                RegistroEscuelaAttempt.record_attempt(
                    ip_address=ip_address,
                    nombre_corto=nombre_corto,
                    exitoso=False,
                    razon_fallo='Email de contacto duplicado',
                    user_agent=user_agent
                )
                return render(request, 'public/registro_escuela.html')
            
            # Calcular fecha de vencimiento (30 días para prueba)
            fecha_venc = None
            if plan in ['gratis', 'prueba']:
                fecha_venc = timezone.now() + timedelta(days=30)
            
            # 🔒 1. Crear el TENANT (Client) - INACTIVO hasta confirmar email
            tenant = Client(
                schema_name=nombre_corto,  # Nombre del schema de PostgreSQL
                nombre=nombre_empresa,
                nombre_corto=nombre_corto,
                email_contacto=email_empresa,
                telefono=telefono_empresa,
                direccion=direccion_empresa,
                plan=plan if plan != 'gratis' else 'prueba',
                max_usuarios=max_usuarios,
                activo=False,  # 🔒 INACTIVO hasta activación por email
                fecha_vencimiento=fecha_venc
            )
            
            # 🔒 Generar token de activación
            tenant.activation_token = uuid.uuid4()
            tenant.save()  # Crea automáticamente el schema y ejecuta migraciones
            
            logger.info(f'Tenant creado (INACTIVO): {tenant.schema_name} - Esperando activación por email')
            
            # 2. Crear DOMINIOS para el tenant
            # Dominio para desarrollo (localhost)
            domain_local = Domain()
            domain_local.domain = f'{nombre_corto}.localhost'
            domain_local.tenant = tenant
            domain_local.is_primary = True
            domain_local.save()
            
            # Dominio para producción (si corresponde)
            if not settings.DEBUG:
                domain_prod = Domain()
                domain_prod.domain = f'{nombre_corto}.ventasenlinea.com'
                domain_prod.tenant = tenant
                domain_prod.is_primary = False
                domain_prod.save()
            
            logger.info(f'Dominios creados: {domain_local.domain}')
            
            # 3. Crear usuario administrador DENTRO del schema del tenant
            # IMPORTANTE: Cambiamos al schema del tenant para crear el usuario allí
            connection.set_tenant(tenant)
            
            # Separar nombre y apellido del admin
            nombre_partes = admin_nombre.split(' ', 1)
            first_name = nombre_partes[0]
            last_name = nombre_partes[1] if len(nombre_partes) > 1 else ''
            
            # Crear usuario administrador EN EL SCHEMA DEL TENANT
            admin_user = CustomUser.objects.create_user(
                email=admin_email,
                password=admin_password,
                first_name=first_name,
                last_name=last_name,
                rol='Administrador',
                is_active=True,
                is_staff=True
            )
            
            logger.info(
                f'Usuario admin creado en schema {tenant.schema_name}: {admin_user.email}'
            )
            
            # 4. Crear período fiscal automáticamente para el año actual
            from datetime import date
            from .models import AnhoEscolar
            
            ano_actual = date.today().year
            periodo_fiscal = AnhoEscolar.objects.create(
                nombre=f'Año Fiscal {ano_actual}',
                fecha_inicio=date(ano_actual, 1, 1),
                fecha_fin=date(ano_actual, 12, 31),
                activo=True
            )
            
            logger.info(
                f'Período fiscal creado automáticamente: {periodo_fiscal.nombre} (ID: {periodo_fiscal.id})'
            )
            
            # 5. Crear cliente genérico automáticamente
            import random
            import string
            random_suffix = ''.join(random.choices(string.digits, k=6))
            email_generico = f"cliente.generico.{random_suffix}@{nombre_corto}.local"
            
            cliente_generico = CustomUser.objects.create(
                email=email_generico,
                first_name='Cliente',
                last_name='Genérico',
                rol='Cliente',
                is_active=True,
                is_staff=False,
                is_superuser=False,
                estado='Activo',
            )
            cliente_generico.set_password('ClienteGenerico2026!')
            cliente_generico.save()
            
            logger.info(
                f'Cliente genérico creado automáticamente: {cliente_generico.email} (ID: {cliente_generico.id})'
            )
            
            # Volver al schema público
            from django_tenants.utils import get_public_schema_name
            connection.set_schema_to_public()
            
            # 🔒 4. Enviar email de ACTIVACIÓN (no bienvenida)
            try:
                from django.core.mail import EmailMessage
                
                # Generar UID codificado para la URL
                uid = urlsafe_base64_encode(force_bytes(tenant.pk))
                
                # Construir URL de activación
                current_site = get_current_site(request)
                activation_url = f"{request.scheme}://{current_site.domain}/activate-school/{uid}/{tenant.activation_token}/"
                
                url_acceso = f'http://{nombre_corto}.localhost:8000' if settings.DEBUG else f'https://{nombre_corto}.ventasenlinea.com'
                
                subject = f'💼 Activa tu empresa: {nombre_empresa}'
                
                html_message = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #4e73df; border-bottom: 3px solid #1cc88a; padding-bottom: 10px;">
                            ✅ Confirma tu Registro
                        </h2>
                        <p>Hola <strong>{admin_nombre}</strong>,</p>
                        <p>Tu empresa <strong>{nombre_empresa}</strong> ha sido registrada exitosamente, 
                        pero necesitamos que confirmes tu dirección de correo electrónico.</p>
                        
                        <div style="background: #f8f9fc; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 5px solid #1cc88a;">
                            <h3 style="color: #1cc88a; margin-top: 0;">📋 Datos de tu Empresa</h3>
                            <p style="margin: 5px 0;"><strong>Nombre:</strong> {nombre_empresa}</p>
                            <p style="margin: 5px 0;"><strong>Subdominio:</strong> {nombre_corto}</p>
                            <p style="margin: 5px 0;"><strong>Plan:</strong> {plan.title()}</p>
                            <p style="margin: 5px 0;"><strong>Usuarios:</strong> {max_usuarios}</p>
                        </div>
                        
                        <div style="background: #fff3cd; padding: 15px; border-radius: 10px; margin: 20px 0; border-left: 5px solid #f6c23e;">
                            <p style="margin: 0; color: #856404;">
                                ⚠️ <strong>¡Acción Requerida!</strong><br>
                                Haz clic en el botón de abajo para activar tu empresa. 
                                Este enlace es válido por 24 horas.
                            </p>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{activation_url}" 
                               style="background: linear-gradient(180deg, #1cc88a 10%, #17a673 100%); 
                                      color: white; 
                                      padding: 15px 40px; 
                                      text-decoration: none; 
                                      border-radius: 5px; 
                                      display: inline-block;
                                      font-weight: bold;
                                      font-size: 16px;
                                      box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                                🚀 Activar Mi Empresa
                            </a>
                        </div>
                        
                        <p style="color: #858796; font-size: 13px; margin-top: 30px;">
                            <strong>¿Por qué este paso?</strong><br>
                            La confirmación por email nos ayuda a prevenir registros fraudulentos y 
                            asegura que puedas recibir notificaciones importantes sobre tu empresa.
                        </p>
                        
                        <p style="color: #858796; font-size: 13px;">
                            Si no creaste esta cuenta, puedes ignorar este mensaje.<br>
                            El registro será eliminado automáticamente después de 24 horas sin activar.
                        </p>
                        
                        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e3e6f0; color: #858796; font-size: 12px;">
                            <p>Sistema de Ventas Online - Gestión Comercial</p>
                            <p>Si el botón no funciona, copia este enlace:<br>
                            <a href="{activation_url}" style="color: #4e73df; word-break: break-all;">{activation_url}</a></p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                email = EmailMessage(
                    subject,
                    html_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email_empresa],
                )
                email.content_subtype = 'html'
                email.send(fail_silently=True)
                
                logger.info(f'Email de activación enviado a {email_empresa}')
                
            except Exception as e:
                logger.error(f'Error enviando email de activación: {e}')
            
            # 🔒 5. Registrar intento EXITOSO
            RegistroEscuelaAttempt.record_attempt(
                ip_address=ip_address,
                nombre_corto=nombre_corto,
                exitoso=True,
                razon_fallo='',
                user_agent=user_agent
            )
            
            # 🔒 6. Log de seguridad
            try:
                from .models import SecurityLog
                SecurityLog.objects.create(
                    tipo_evento='SCHOOL_REGISTERED',
                    nivel_severidad='INFO',
                    email=admin_email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    descripcion=f'Nueva empresa registrada: {nombre_empresa} ({nombre_corto}). Esperando activación por email.',
                    metadata={
                        'nombre_empresa': nombre_empresa,
                        'nombre_corto': nombre_corto,
                        'email_contacto': email_empresa,
                        'plan': plan,
                        'tenant_id': tenant.id
                    }
                )
            except Exception as e:
                logger.error(f'Error registrando SecurityLog: {e}')
            
            # Mensaje de éxito
            messages.success(
                request,
                f'✅ ¡Registro exitoso! Hemos enviado un correo de confirmación a <strong>{email_empresa}</strong>. '
                f'<br><br>📧 Por favor, revisa tu bandeja de entrada (y spam) y haz clic en el enlace de activación '
                f'para completar el registro de tu empresa <strong>{nombre_empresa}</strong>. '
                f'<br><br>⚠️ <strong>Importante:</strong> Tu empresa estará disponible después de verificar el email.'
            )
            
            # Construir URL del subdominio de la empresa
            url_empresa = f'http://{nombre_corto}.localhost:8000' if settings.DEBUG else f'https://{nombre_corto}.ventasenlinea.com'
            
            # Redirigir al login del subdominio de la escuela recién creada
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(f'{url_escuela}/login/')
            
        except Exception as e:
            logger.error(f'Error registrando escuela: {e}', exc_info=True)
            
            # 🔒 Registrar intento FALLIDO
            RegistroEscuelaAttempt.record_attempt(
                ip_address=ip_address,
                nombre_corto=nombre_corto if 'nombre_corto' in locals() else '',
                exitoso=False,
                razon_fallo=f'Error del sistema: {str(e)[:200]}',
                user_agent=user_agent
            )
            
            messages.error(
                request, 
                f'Ocurrió un error al registrar la escuela. Por favor, intenta nuevamente. Error: {str(e)}'
            )
            return render(request, 'public/registro_escuela.html')
    
    # GET request - mostrar formulario
    return render(request, 'public/registro_escuela.html')


def home_public(request):
    """
    Página de inicio del dominio público (sin tenant)
    Redirige al login
    """
    return redirect('login')




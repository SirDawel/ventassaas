#!/usr/bin/env python
"""Script para agregar vista de registro de escuelas"""

vista_codigo = '''

# ============================================
# REGISTRO PÚBLICO DE ESCUELAS (MULTI-TENANT)
# ============================================

def registrar_escuela(request):
    """
    Vista pública para que nuevas escuelas se registren en el sistema
    No requiere autenticación
    """
    # Si ya está autenticado, redirigir al dashboard
    if request.user.is_authenticated:
        return redirect('anhos-escolares')
    
    if request.method == 'POST':
        try:
            # Datos de la escuela
            nombre_escuela = request.POST.get('nombre_escuela')
            nombre_corto = request.POST.get('nombre_corto').lower().strip()
            email_escuela = request.POST.get('email_escuela')
            telefono_escuela = request.POST.get('telefono_escuela')
            rnc = request.POST.get('rnc', '')
            direccion_escuela = request.POST.get('direccion_escuela')
            plan = request.POST.get('plan')
            max_usuarios = int(request.POST.get('max_usuarios', 50))
            
            # Datos del administrador
            admin_nombre = request.POST.get('admin_nombre')
            admin_email = request.POST.get('admin_email')
            admin_password = request.POST.get('admin_password')
            admin_password_confirm = request.POST.get('admin_password_confirm')
            
            # Validaciones
            if admin_password != admin_password_confirm:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, 'public/registro_escuela.html')
            
            # Validar nombre corto (solo letras, números y guiones)
            import re
            if not re.match(r'^[a-z0-9-]+$', nombre_corto):
                messages.error(
                    request, 
                    'El nombre corto solo puede contener letras minúsculas, números y guiones.'
                )
                return render(request, 'public/registro_escuela.html')
            
            # Verificar que el nombre corto no esté tomado
            from .models_escuela import Escuela
            if Escuela.objects.filter(nombre_corto=nombre_corto).exists():
                messages.error(
                    request, 
                    f'El subdominio "{nombre_corto}" ya está en uso. Por favor, elige otro.'
                )
                return render(request, 'public/registro_escuela.html')
            
            # Verificar que el email del admin no esté en uso
            if CustomUser.objects.filter(email=admin_email).exists():
                messages.error(
                    request, 
                    'Ya existe una cuenta con este email. Por favor, usa otro.'
                )
                return render(request, 'public/registro_escuela.html')
            
            # Crear la escuela
            escuela = Escuela.objects.create(
                nombre=nombre_escuela,
                nombre_corto=nombre_corto,
                email_contacto=email_escuela,
                telefono=telefono_escuela,
                rnc=rnc,
                direccion=direccion_escuela,
                plan=plan,
                max_usuarios=max_usuarios,
                activo=True,  # Activar inmediatamente
                fecha_suscripcion=timezone.now()
            )
            
            # Separar nombre y apellido del admin
            nombre_partes = admin_nombre.split(' ', 1)
            first_name = nombre_partes[0]
            last_name = nombre_partes[1] if len(nombre_partes) > 1 else ''
            
            # Crear usuario administrador
            admin_user = CustomUser.objects.create_user(
                email=admin_email,
                password=admin_password,
                first_name=first_name,
                last_name=last_name,
                rol='Administrador',
                is_active=True,
                is_staff=True,  # Dar permisos de staff
                # escuela=escuela  # TODO: Agregar cuando se implemente FK escuela
            )
            
            logger.info(
                f'Nueva escuela registrada: {escuela.nombre} ({escuela.nombre_corto}) '
                f'por {admin_user.email}'
            )
            
            # Enviar email de bienvenida
            try:
                from django.core.mail import EmailMessage
                subject = f'¡Bienvenido a Sistema Escolar, {nombre_escuela}!'
                
                html_message = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #4e73df;">¡Felicidades! Tu escuela ha sido registrada</h2>
                    <p>Hola <strong>{admin_nombre}</strong>,</p>
                    <p>Tu institución <strong>{nombre_escuela}</strong> ha sido registrada exitosamente en nuestro sistema.</p>
                    
                    <div style="background: #f8f9fc; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <h3 style="color: #1cc88a;">Datos de Acceso</h3>
                        <p><strong>URL de tu escuela:</strong> <a href="{escuela.get_url_acceso()}">{escuela.get_url_acceso()}</a></p>
                        <p><strong>Email:</strong> {admin_email}</p>
                        <p><strong>Plan:</strong> {plan.title()}</p>
                        <p><strong>Usuarios permitidos:</strong> {max_usuarios}</p>
                    </div>
                    
                    <h3>Próximos Pasos:</h3>
                    <ol>
                        <li>Inicia sesión en tu panel de administración</li>
                        <li>Configura los datos de tu escuela</li>
                        <li>Agrega profesores y estudiantes</li>
                        <li>Comienza a usar el sistema</li>
                    </ol>
                    
                    <p style="margin-top: 30px;">
                        <a href="{escuela.get_url_acceso()}/login/" 
                           style="background: #1cc88a; color: white; padding: 15px 30px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Iniciar Sesión Ahora
                        </a>
                    </p>
                    
                    <p style="margin-top: 30px; color: #858796;">
                        Si tienes alguna pregunta, no dudes en contactarnos.<br>
                        <strong>Soporte Técnico:</strong> soporte@sistemaescolar.com
                    </p>
                </body>
                </html>
                """
                
                email = EmailMessage(
                    subject,
                    html_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [admin_email],
                )
                email.content_subtype = 'html'
                email.send(fail_silently=True)
            except Exception as e:
                logger.error(f'Error enviando email de bienvenida: {e}')
            
            # Mensaje de éxito
            messages.success(
                request,
                f'¡Felicidades! Tu escuela "{nombre_escuela}" ha sido creada exitosamente. '
                f'Ya puedes iniciar sesión en: {escuela.get_url_acceso()}'
            )
            
            # Redirigir al login de la escuela
            return redirect(f'{escuela.get_url_acceso()}/login/')
            
        except Exception as e:
            logger.error(f'Error registrando escuela: {e}')
            messages.error(
                request, 
                f'Ocurrió un error al registrar la escuela. Por favor, intenta nuevamente. Error: {str(e)}'
            )
            return render(request, 'public/registro_escuela.html')
    
    # GET request - mostrar formulario
    return render(request, 'public/registro_escuela.html')
'''

# Leer contenido actual
with open('escuelaweb/views.py', 'r', encoding='latin-1') as f:
    contenido_actual = f.read()

# Agregar vista si no existe
if 'def registrar_escuela' not in contenido_actual:
    with open('escuelaweb/views.py', 'a', encoding='utf-8') as f:
        f.write(vista_codigo)
    print("✅ Vista 'registrar_escuela' agregada correctamente")
else:
    print("ℹ️  Vista 'registrar_escuela' ya existe")

"""
Script para probar el envío del email de activación tal como se envía en el registro
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import uuid

print("\n" + "="*70)
print("📧 PRUEBA DE EMAIL DE ACTIVACIÓN DE EMPRESA")
print("="*70 + "\n")

# Datos de prueba
nombre_empresa = "Empresa de Prueba XYZ"
nombre_corto = "prueba-xyz"
admin_nombre = "Juan Pérez"
email_empresa = settings.EMAIL_HOST_USER  # Enviar al mismo email configurado
plan = "gratis"

# Simular el tenant
class TenantMock:
    pk = 999
    activation_token = uuid.uuid4()

tenant = TenantMock()

# Generar UID codificado
uid = urlsafe_base64_encode(force_bytes(tenant.pk))

# Construir URL de activación
activation_url = f"http://127.0.0.1:8000/activate-school/{uid}/{tenant.activation_token}/"
url_acceso = f'http://{nombre_corto}.localhost:8000'

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

print(f"📤 Enviando email de prueba a: {email_empresa}")
print(f"📝 Asunto: {subject}")
print(f"🔗 URL de activación: {activation_url}\n")

try:
    email = EmailMessage(
        subject,
        html_message,
        settings.DEFAULT_FROM_EMAIL,
        [email_empresa],
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)
    
    print("✅ EMAIL ENVIADO EXITOSAMENTE!")
    print(f"\n📬 Instrucciones:")
    print(f"   1. Revisa la bandeja de entrada de: {email_empresa}")
    print(f"   2. Si no aparece, revisa la carpeta de SPAM/CORREO NO DESEADO")
    print(f"   3. El email tiene formato HTML con un botón verde para activar")
    print(f"   4. También incluye el link de activación al final\n")
    
except Exception as e:
    print(f"❌ ERROR AL ENVIAR EMAIL:")
    print(f"   {type(e).__name__}: {str(e)}\n")
    import traceback
    traceback.print_exc()

print("="*70 + "\n")

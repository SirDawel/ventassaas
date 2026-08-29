"""
Script para actualizar el nombre de la empresa en la configuración
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django_tenants.utils import schema_context
from ventasweb.models import ConfiguracionEscuela, Client

def actualizar_nombre_empresa():
    """Actualiza el nombre de la empresa en todos los tenants"""
    
    # Actualizar tenant público
    print("\n📝 Actualizando tenant público...")
    with schema_context('public'):
        try:
            config, created = ConfiguracionEscuela.objects.get_or_create(
                id=1,
                defaults={
                    'nombre_escuela': 'Mis Ventas Flash',
                    'direccion': 'República Dominicana',
                    'telefono': '809-000-0000',
                    'email': 'contacto@misventasflash.com'
                }
            )
            if not created:
                config.nombre_escuela = 'Mis Ventas Flash'
                config.save()
                print("✅ Nombre actualizado en tenant público")
            else:
                print("✅ Configuración creada en tenant público")
        except Exception as e:
            print(f"❌ Error en tenant público: {e}")
    
    # Actualizar todos los tenants activos
    tenants = Client.objects.filter(activo=True).exclude(schema_name='public')
    print(f"\n📊 Actualizando {tenants.count()} tenants activos...")
    
    for tenant in tenants:
        try:
            with schema_context(tenant.schema_name):
                config, created = ConfiguracionEscuela.objects.get_or_create(
                    id=1,
                    defaults={
                        'nombre_escuela': 'Mis Ventas Flash',
                        'direccion': 'República Dominicana',
                        'telefono': tenant.telefono or '809-000-0000',
                        'email': 'contacto@misventasflash.com'
                    }
                )
                if not created:
                    config.nombre_escuela = 'Mis Ventas Flash'
                    config.save()
                    print(f"✅ {tenant.nombre}: Nombre actualizado")
                else:
                    print(f"✅ {tenant.nombre}: Configuración creada")
        except Exception as e:
            print(f"❌ Error en {tenant.nombre}: {e}")
    
    print("\n✅ Proceso completado!")
    print("🔄 El cambio se verá reflejado al recargar el navegador")

if __name__ == '__main__':
    actualizar_nombre_empresa()

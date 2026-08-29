#!/usr/bin/env python
"""
Script para crear el tenant 'boutique' con su dominio configurado
"""
import os
import sys
import django
from datetime import timedelta

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from ventasweb.tenant_models import Client, Domain
from django.utils import timezone
from django.db import transaction

def crear_tenant_boutique():
    print("\n" + "=" * 80)
    print("🏪 CREANDO TENANT 'BOUTIQUE'")
    print("=" * 80)
    
    schema_name = 'boutique'
    nombre_corto = 'boutique'
    
    # Verificar si ya existe
    if Client.objects.filter(schema_name=schema_name).exists():
        print(f"\n⚠️  El tenant '{schema_name}' ya existe")
        tenant = Client.objects.get(schema_name=schema_name)
        print(f"   Nombre: {tenant.nombre}")
        print(f"   Activo: {tenant.activo}")
        
        respuesta = input("\n¿Quieres actualizar su configuración? (s/n): ").strip().lower()
        if respuesta != 's':
            print("\n✋ Operación cancelada")
            return
        
        crear_nuevo = False
    else:
        crear_nuevo = True
    
    # Recopilar información
    print("\n📝 Configuración del tenant:")
    print("-" * 80)
    
    if crear_nuevo:
        nombre = input("Nombre completo del negocio (ej: Boutique Fashion): ").strip()
        if not nombre:
            nombre = "Boutique Fashion"
    else:
        nombre = tenant.nombre
        print(f"Nombre actual: {nombre}")
        nuevo_nombre = input("Nuevo nombre (Enter para mantener): ").strip()
        if nuevo_nombre:
            nombre = nuevo_nombre
    
    email = input("Email de contacto: ").strip()
    if not email:
        email = "boutique@misventasflash.com"
    
    telefono = input("Teléfono (opcional): ").strip()
    
    plan = input("Plan (prueba/basico/profesional/premium) [prueba]: ").strip().lower()
    if plan not in ['prueba', 'basico', 'profesional', 'premium']:
        plan = 'prueba'
    
    # Dominios
    print("\n🌐 Dominios a configurar:")
    dominios_crear = []
    
    print("1. localhost (para desarrollo local)")
    usar_localhost = input("   ¿Incluir? (s/n) [s]: ").strip().lower()
    if usar_localhost != 'n':
        dominios_crear.append(('boutique.localhost', False))
    
    print("2. boutique.misventasflash.com (producción)")
    usar_prod = input("   ¿Incluir? (s/n) [s]: ").strip().lower()
    if usar_prod != 'n':
        dominios_crear.append(('boutique.misventasflash.com', True))  # Primario
    
    # Dominio personalizado
    print("3. Dominio personalizado (opcional)")
    dominio_custom = input("   Dominio (Enter para omitir): ").strip()
    if dominio_custom:
        dominios_crear.append((dominio_custom, False))
    
    # Confirmar
    print("\n" + "=" * 80)
    print("📋 RESUMEN DE CONFIGURACIÓN")
    print("=" * 80)
    print(f"Schema: {schema_name}")
    print(f"Nombre: {nombre}")
    print(f"Nombre corto: {nombre_corto}")
    print(f"Email: {email}")
    print(f"Teléfono: {telefono or 'N/A'}")
    print(f"Plan: {plan}")
    print(f"Dominios:")
    for dom, primario in dominios_crear:
        primario_txt = "⭐ (primario)" if primario else ""
        print(f"  - {dom} {primario_txt}")
    
    confirmar = input("\n¿Crear/Actualizar tenant? (s/n): ").strip().lower()
    if confirmar != 's':
        print("\n✋ Operación cancelada")
        return
    
    # Crear o actualizar tenant
    print("\n🔧 Procesando...")
    
    try:
        with transaction.atomic():
            if crear_nuevo:
                print(f"📦 Creando tenant '{schema_name}'...")
                tenant = Client.objects.create(
                    schema_name=schema_name,
                    nombre=nombre,
                    nombre_corto=nombre_corto,
                    email_contacto=email,
                    telefono=telefono,
                    plan=plan,
                    activo=True,
                    max_usuarios=100,
                    fecha_vencimiento=timezone.now() + timedelta(days=365)
                )
                print(f"✅ Tenant creado")
                print(f"   ⏳ Esperando a que django-tenants cree el schema...")
                # django-tenants crea el schema automáticamente debido a auto_create_schema=True
            else:
                print(f"📝 Actualizando tenant '{schema_name}'...")
                tenant.nombre = nombre
                tenant.email_contacto = email
                tenant.telefono = telefono
                tenant.plan = plan
                tenant.activo = True
                tenant.save()
                print(f"✅ Tenant actualizado")
            
            # Crear dominios
            print(f"\n🌐 Configurando dominios...")
            for dominio, es_primario in dominios_crear:
                domain_obj, created = Domain.objects.get_or_create(
                    domain=dominio,
                    defaults={
                        'tenant': tenant,
                        'is_primary': es_primario
                    }
                )
                if created:
                    print(f"   ✅ Dominio '{dominio}' creado")
                else:
                    # Actualizar si cambió
                    if domain_obj.tenant != tenant:
                        domain_obj.tenant = tenant
                        domain_obj.save()
                        print(f"   📝 Dominio '{dominio}' actualizado")
                    else:
                        print(f"   ℹ️  Dominio '{dominio}' ya existe")
        
        print("\n" + "=" * 80)
        print("✅ TENANT CONFIGURADO EXITOSAMENTE")
        print("=" * 80)
        
        print(f"\n🎉 El tenant 'boutique' está listo!")
        print(f"\n📍 Puedes acceder en:")
        for dominio, _ in dominios_crear:
            if 'localhost' in dominio:
                print(f"   - http://{dominio}:8000 (desarrollo)")
            else:
                print(f"   - https://{dominio} (producción)")
        
        print(f"\n⚠️  IMPORTANTE para producción:")
        print(f"   1. Verifica que ALLOWED_HOSTS incluya: .misventasflash.com")
        print(f"   2. Configura DNS: boutique.misventasflash.com → IP de EC2")
        print(f"   3. Certificado SSL debe ser wildcard: *.misventasflash.com")
        print(f"   4. Reinicia gunicorn: sudo systemctl restart gunicorn")
        
        print("\n" + "=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error al crear tenant: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    try:
        crear_tenant_boutique()
    except KeyboardInterrupt:
        print("\n\n✋ Operación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

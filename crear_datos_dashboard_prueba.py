"""
Script para crear datos de prueba para el Dashboard Analytics
Crea facturas, productos, clientes y un usuario admin en un tenant existente
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from django_tenants.utils import schema_context
from ventasweb.models import (
    Client, Articulo, CategoriaArticulo, CustomUser, 
    Factura, DetalleFactura, AnhoEscolar
)

User = get_user_model()

# ============= CONFIGURACIÓN =============
TENANT_SCHEMA = 'alexandercolmado'  # Cambiar si quieres usar otro tenant
USUARIO_ADMIN = 'admin@alexandercolmado.com'
PASSWORD_ADMIN = 'admin123'

print(f"\n{'='*60}")
print("🚀 GENERANDO DATOS DE PRUEBA PARA DASHBOARD ANALYTICS")
print(f"{'='*60}\n")

try:
    # Obtener el tenant
    tenant = Client.objects.get(schema_name=TENANT_SCHEMA)
    print(f"✅ Tenant encontrado: {tenant.nombre} ({tenant.schema_name})")
    
    with schema_context(tenant.schema_name):
        
        # ============= 1. CREAR USUARIO ADMIN =============
        print(f"\n📋 1. Verificando usuario administrador...")
        
        admin_user, created = CustomUser.objects.get_or_create(
            email=USUARIO_ADMIN,
            defaults={
                'first_name': 'Admin',
                'last_name': 'Sistema',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'rol': 'Administrador'
            }
        )
        
        if created:
            admin_user.set_password(PASSWORD_ADMIN)
            admin_user.save()
            print(f"   ✅ Usuario admin creado: {USUARIO_ADMIN}")
        else:
            admin_user.set_password(PASSWORD_ADMIN)  # Actualizar password por si acaso
            admin_user.save()
            print(f"   ℹ️  Usuario admin ya existe: {USUARIO_ADMIN}")
        
        print(f"   🔑 Password: {PASSWORD_ADMIN}")
        
        # ============= 2. OBTENER O CREAR AÑO ESCOLAR =============
        print(f"\n📅 2. Verificando año escolar...")
        
        anho_actual = datetime.now().year
        anho_escolar, created = AnhoEscolar.objects.get_or_create(
            nombre=f"Año {anho_actual}",
            defaults={
                'activo': True,
                'fecha_inicio': datetime(anho_actual, 1, 1),
                'fecha_fin': datetime(anho_actual, 12, 31)
            }
        )
        
        if created:
            print(f"   ✅ Año escolar {anho_actual} creado")
        else:
            print(f"   ℹ️  Año escolar {anho_actual} ya existe")
        
        # ============= 3. CREAR CATEGORÍAS =============
        print(f"\n🏷️  3. Creando categorías de productos...")
        
        categorias_data = [
            {'nombre': 'Electrónica', 'descripcion': 'Productos electrónicos'},
            {'nombre': 'Ropa', 'descripcion': 'Prendas de vestir'},
            {'nombre': 'Alimentos', 'descripcion': 'Productos alimenticios'},
            {'nombre': 'Papelería', 'descripcion': 'Útiles escolares y oficina'},
        ]
        
        categorias = []
        for cat_data in categorias_data:
            cat, created = CategoriaArticulo.objects.get_or_create(
                nombre=cat_data['nombre'],
                defaults={'descripcion': cat_data['descripcion']}
            )
            categorias.append(cat)
            if created:
                print(f"   ✅ Categoría creada: {cat.nombre}")
        
        # ============= 4. CREAR PRODUCTOS =============
        print(f"\n📦 4. Creando productos...")
        
        productos_data = [
            {'nombre': 'Laptop HP 15', 'precio': Decimal('450.00'), 'categoria': categorias[0], 'stock': 25},
            {'nombre': 'Mouse Inalámbrico', 'precio': Decimal('15.00'), 'categoria': categorias[0], 'stock': 100},
            {'nombre': 'Teclado Mecánico', 'precio': Decimal('35.00'), 'categoria': categorias[0], 'stock': 50},
            {'nombre': 'Camisa Polo', 'precio': Decimal('25.00'), 'categoria': categorias[1], 'stock': 80},
            {'nombre': 'Pantalón Jean', 'precio': Decimal('40.00'), 'categoria': categorias[1], 'stock': 60},
            {'nombre': 'Zapatos Deportivos', 'precio': Decimal('55.00'), 'categoria': categorias[1], 'stock': 45},
            {'nombre': 'Café Premium 500g', 'precio': Decimal('8.00'), 'categoria': categorias[2], 'stock': 200},
            {'nombre': 'Galletas Surtidas', 'precio': Decimal('3.50'), 'categoria': categorias[2], 'stock': 150},
            {'nombre': 'Cuaderno Universitario', 'precio': Decimal('2.50'), 'categoria': categorias[3], 'stock': 300},
            {'nombre': 'Bolígrafo Pack x12', 'precio': Decimal('5.00'), 'categoria': categorias[3], 'stock': 180},
        ]
        
        productos = []
        for prod_data in productos_data:
            prod, created = Articulo.objects.get_or_create(
                nombre=prod_data['nombre'],
                defaults={
                    'precio_venta': prod_data['precio'],
                    'precio_compra': prod_data['precio'] * Decimal('0.6'),  # 60% del precio de venta
                    'categoria': prod_data['categoria'],
                    'stock_actual': prod_data['stock'],
                    'descripcion': f'Producto de prueba: {prod_data["nombre"]}'
                }
            )
            productos.append(prod)
            if created:
                print(f"   ✅ Producto creado: {prod.nombre} - ${prod.precio_venta}")
        
        # ============= 5. CREAR CLIENTES =============
        print(f"\n👥 5. Creando clientes...")
        
        clientes_data = [
            {'nombre': 'Juan', 'apellido': 'Pérez', 'email': 'juan.perez@email.com'},
            {'nombre': 'María', 'apellido': 'González', 'email': 'maria.gonzalez@email.com'},
            {'nombre': 'Carlos', 'apellido': 'Rodríguez', 'email': 'carlos.rodriguez@email.com'},
            {'nombre': 'Ana', 'apellido': 'Martínez', 'email': 'ana.martinez@email.com'},
            {'nombre': 'Luis', 'apellido': 'López', 'email': 'luis.lopez@email.com'},
        ]
        
        clientes = []
        for cliente_data in clientes_data:
            cliente, created = CustomUser.objects.get_or_create(
                email=cliente_data['email'],
                defaults={
                    'first_name': cliente_data['nombre'],
                    'last_name': cliente_data['apellido'],
                    'rol': 'Cliente',
                    'tipo_cliente': 'Minorista',
                    'is_active': True
                }
            )
            if created:
                cliente.set_password('cliente123')
                cliente.save()
            clientes.append(cliente)
            if created:
                print(f"   ✅ Cliente creado: {cliente.first_name} {cliente.last_name}")
        
        # ============= 6. CREAR FACTURAS (Últimos 6 meses) =============
        print(f"\n💰 6. Generando facturas de los últimos 6 meses...")
        
        hoy = datetime.now()
        facturas_creadas = 0
        total_ventas = Decimal('0.00')
        
        # Generar facturas para cada mes (últimos 6 meses)
        for mes_atras in range(6):
            fecha_mes = hoy - timedelta(days=30 * mes_atras)
            
            # Crear entre 10-20 facturas por mes
            num_facturas = random.randint(10, 20)
            
            for i in range(num_facturas):
                # Seleccionar cliente y vendedor aleatorios
                cliente = random.choice(clientes)
                vendedor = admin_user
                
                # Fecha aleatoria dentro del mes
                dia_aleatorio = random.randint(1, 28)
                fecha_factura = fecha_mes.replace(day=dia_aleatorio)
                
                # Crear factura con número único
                import uuid
                numero_factura = f"FAC-{fecha_mes.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
                
                factura = Factura.objects.create(
                    numero_factura=numero_factura,
                    cliente=cliente,
                    vendedor=vendedor,
                    fecha_emision=fecha_factura,
                    estado='pagada',
                    anho_escolar=anho_escolar,
                    total=Decimal('0.00'),  # Se calculará después
                    metodo_pago=random.choice(['efectivo', 'tarjeta', 'transferencia'])
                )
                
                # Agregar entre 1-4 productos a la factura
                num_productos = random.randint(1, 4)
                subtotal = Decimal('0.00')
                
                productos_seleccionados = random.sample(productos, num_productos)
                
                for producto in productos_seleccionados:
                    cantidad = random.randint(1, 5)
                    precio_unitario = producto.precio_venta
                    total_linea = precio_unitario * cantidad
                    
                    DetalleFactura.objects.create(
                        factura=factura,
                        articulo=producto,
                        descripcion=producto.nombre,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario
                    )
                    
                    subtotal += total_linea
                
                # Actualizar monto total de la factura
                factura.total = subtotal
                factura.save()
                
                facturas_creadas += 1
                total_ventas += subtotal
        
        print(f"   ✅ {facturas_creadas} facturas creadas")
        print(f"   💵 Total en ventas: ${total_ventas:,.2f}")
        
        # ============= 7. CREAR ALGUNAS FACTURAS PENDIENTES =============
        print(f"\n⏳ 7. Creando facturas pendientes...")
        
        for i in range(5):
            cliente = random.choice(clientes)
            fecha_factura = hoy - timedelta(days=random.randint(1, 10))
            
            import uuid
            numero_factura = f"FAC-PEND-{uuid.uuid4().hex[:12].upper()}"
            
            factura = Factura.objects.create(
                numero_factura=numero_factura,
                cliente=cliente,
                vendedor=admin_user,
                fecha_emision=fecha_factura,
                estado='pendiente',
                anho_escolar=anho_escolar,
                total=Decimal('0.00'),
                metodo_pago='efectivo'
            )
            
            # Agregar productos
            num_productos = random.randint(1, 3)
            subtotal = Decimal('0.00')
            productos_seleccionados = random.sample(productos, num_productos)
            
            for producto in productos_seleccionados:
                cantidad = random.randint(1, 3)
                precio_unitario = producto.precio_venta
                total_linea = precio_unitario * cantidad
                
                DetalleFactura.objects.create(
                    factura=factura,
                    articulo=producto,
                    descripcion=producto.nombre,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario
                )
                
                subtotal += total_linea
            
            factura.total = subtotal
            factura.save()
        
        print(f"   ✅ 5 facturas pendientes creadas")
        
        # ============= RESUMEN FINAL =============
        print(f"\n{'='*60}")
        print("✅ DATOS DE PRUEBA CREADOS EXITOSAMENTE")
        print(f"{'='*60}\n")
        
        print("📊 RESUMEN:")
        print(f"   • Categorías: {CategoriaArticulo.objects.count()}")
        print(f"   • Productos: {Articulo.objects.count()}")
        print(f"   • Clientes: {CustomUser.objects.filter(rol='Cliente').count()}")
        print(f"   • Facturas pagadas: {Factura.objects.filter(estado='pagada').count()}")
        print(f"   • Facturas pendientes: {Factura.objects.filter(estado='pendiente').count()}")
        print(f"   • Total en ventas: ${total_ventas:,.2f}")
        
        print(f"\n🔐 CREDENCIALES DE ACCESO:")
        print(f"   URL: http://127.0.0.1:8000/login/")
        print(f"   Usuario: {USUARIO_ADMIN}")
        print(f"   Password: {PASSWORD_ADMIN}")
        
        print(f"\n📈 DASHBOARD:")
        print(f"   URL: http://127.0.0.1:8000/plataform")
        print(f"\n{'='*60}\n")

except Client.DoesNotExist:
    print(f"❌ ERROR: Tenant '{TENANT_SCHEMA}' no encontrado")
    print("\nTenants disponibles:")
    for tenant in Client.objects.exclude(schema_name='public'):
        print(f"   • {tenant.schema_name} - {tenant.nombre}")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

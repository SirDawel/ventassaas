"""
Script para crear el artículo de Mensualidad necesario para el sistema de pagos estudiantiles.
Ejecutar: python manage.py shell < scripts/crear_articulo_mensualidad.py
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from escuelaweb.models import Articulo
from decimal import Decimal

# Verificar si ya existe
articulo_existente = Articulo.objects.filter(nombre__icontains='mensualidad').first()

if articulo_existente:
    print(f"✅ Ya existe el artículo: {articulo_existente.nombre}")
    print(f"   - ID: {articulo_existente.id}")
    print(f"   - Precio: RD$ {articulo_existente.precio_venta}")
    print(f"   - Activo: {articulo_existente.activo}")
else:
    # Crear el artículo de mensualidad
    articulo = Articulo.objects.create(
        codigo_barras='MENS-001',
        nombre='Mensualidad Escolar',
        descripcion='Pago mensual de colegiatura para estudiantes',
        tipo='servicio',
        precio_venta=Decimal('5000.00'),  # Precio por defecto, se puede ajustar
        precio_compra=Decimal('0.00'),
        stock_actual=0,  # Los servicios no tienen stock
        stock_minimo=0,
        activo=True,
        permite_descuento=True,
        aplica_itbis=False  # No aplica ITBIS a servicios educativos
    )
    
    print(f"✅ Artículo creado exitosamente!")
    print(f"   - ID: {articulo.id}")
    print(f"   - Nombre: {articulo.nombre}")
    print(f"   - Tipo: {articulo.tipo}")
    print(f"   - Precio: RD$ {articulo.precio_venta}")
    print(f"\n⚠️  IMPORTANTE: Ajusta el precio según las tarifas de tu institución.")
    print(f"   Puedes editarlo desde el admin de Django o directamente en la base de datos.")

print("\n✅ Proceso completado. Ahora puedes usar el sistema de pagos estudiantiles.")

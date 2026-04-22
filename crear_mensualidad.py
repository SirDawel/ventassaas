from escuelaweb.models import Articulo
from decimal import Decimal

# Verificar si existe
art_existente = Articulo.objects.filter(nombre__icontains='mensualidad').first()

if art_existente:
    print(f"✅ Ya existe el artículo: {art_existente.nombre} (ID: {art_existente.id})")
    print(f"   Precio: RD$ {art_existente.precio_venta}")
else:
    # Crear nuevo artículo
    art = Articulo.objects.create(
        codigo_barras='MENS-001',
        nombre='Mensualidad Escolar',
        descripcion='Pago mensual de colegiatura para estudiantes',
        tipo='servicio',
        precio_venta=Decimal('5000.00'),
        precio_compra=Decimal('0.00'),
        stock_actual=0,
        stock_minimo=0,
        activo=True,
        permite_descuento=True,
        aplica_itbis=False
    )
    print(f"✅ Artículo creado exitosamente!")
    print(f"   ID: {art.id}")
    print(f"   Nombre: {art.nombre}")
    print(f"   Precio: RD$ {art.precio_venta}")

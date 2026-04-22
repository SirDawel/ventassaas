@echo off
echo Creando articulo de Mensualidad...
call .venv\Scripts\activate.bat
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings'); django.setup(); from escuelaweb.models import Articulo; from decimal import Decimal; art = Articulo.objects.filter(nombre__icontains='mensualidad').first(); print('Ya existe') if art else Articulo.objects.create(codigo_barras='MENS-001', nombre='Mensualidad Escolar', descripcion='Pago mensual de colegiatura', tipo='servicio', precio_venta=Decimal('5000.00'), precio_compra=Decimal('0.00'), stock_actual=0, stock_minimo=0, activo=True, permite_descuento=True, aplica_itbis=False) and print('Articulo creado exitosamente')"
pause

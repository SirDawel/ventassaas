"""
Script para limpiar facturas duplicadas del sistema de pagos estudiantiles.
Ejecutar: python limpiar_facturas_duplicadas.py
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.models import Factura, DetalleFactura, CustomUser, AnhoEscolar
from django.db.models import Count

# Obtener año escolar activo
try:
    anho_escolar = AnhoEscolar.objects.get(activo=True)
    print(f"📅 Año escolar activo: {anho_escolar.nombre}")
except AnhoEscolar.DoesNotExist:
    print("❌ No hay año escolar activo")
    sys.exit(1)

# Buscar estudiantes con facturas duplicadas
estudiantes = CustomUser.objects.filter(rol='Estudiante')

total_eliminadas = 0

for estudiante in estudiantes:
    print(f"\n👤 Procesando: {estudiante.get_full_name()}")
    
    # Obtener todas las facturas del estudiante para este año escolar
    facturas = Factura.objects.filter(
        cliente=estudiante,
        anho_escolar=anho_escolar
    ).order_by('fecha_emision')
    
    # Agrupar por mes/año
    facturas_por_mes = {}
    
    for factura in facturas:
        # Obtener mes y año de la fecha de emisión
        mes_key = f"{factura.fecha_emision.year}-{factura.fecha_emision.month:02d}"
        
        if mes_key not in facturas_por_mes:
            facturas_por_mes[mes_key] = []
        
        facturas_por_mes[mes_key].append(factura)
    
    # Eliminar duplicados (mantener solo la primera factura de cada mes)
    for mes_key, facturas_mes in facturas_por_mes.items():
        if len(facturas_mes) > 1:
            print(f"   ⚠️  {mes_key}: {len(facturas_mes)} facturas duplicadas")
            
            # Mantener la primera (o la que tenga DetalleFactura con mes/anio)
            factura_a_mantener = None
            
            for f in facturas_mes:
                detalle = DetalleFactura.objects.filter(factura=f).first()
                if detalle and detalle.mes and detalle.anio:
                    factura_a_mantener = f
                    break
            
            # Si no encontramos una con mes/anio, mantener la primera
            if not factura_a_mantener:
                factura_a_mantener = facturas_mes[0]
            
            print(f"   ✅ Manteniendo: {factura_a_mantener.numero_factura}")
            
            # Eliminar las demás
            for f in facturas_mes:
                if f.id != factura_a_mantener.id:
                    print(f"   🗑️  Eliminando: {f.numero_factura}")
                    f.delete()
                    total_eliminadas += 1

print(f"\n✅ Proceso completado")
print(f"📊 Total facturas eliminadas: {total_eliminadas}")
print(f"\n💡 Ahora recarga la página de pagos estudiantiles para ver solo una factura por mes.")

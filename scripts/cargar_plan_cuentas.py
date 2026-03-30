"""
Script para cargar el Plan de Cuentas básico de una institución educativa
Ejecutar con: python manage.py shell < scripts/cargar_plan_cuentas.py
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.models import PlanCuentas, CustomUser
from decimal import Decimal

# Obtener un usuario administrador para auditoría
try:
    admin_user = CustomUser.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = CustomUser.objects.filter(rol='Administrador').first()
except:
    admin_user = None

print("=" * 60)
print("CARGANDO PLAN DE CUENTAS BÁSICO")
print("=" * 60)

# Definir estructura del Plan de Cuentas
cuentas_data = [
    # ===== ACTIVOS =====
    {'codigo': '1', 'nombre': 'ACTIVO', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': False},
    {'codigo': '1.1', 'nombre': 'ACTIVO CORRIENTE', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': False, 'padre': '1'},
    {'codigo': '1.1.01', 'nombre': 'EFECTIVO Y EQUIVALENTES', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': False, 'padre': '1.1'},
    {'codigo': '1.1.01.001', 'nombre': 'Caja General', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '1.1.01', 'saldo': 0},
    {'codigo': '1.1.01.002', 'nombre': 'Caja Chica', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '1.1.01', 'saldo': 0},
    {'codigo': '1.1.02', 'nombre': 'BANCOS', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': False, 'padre': '1.1'},
    {'codigo': '1.1.02.001', 'nombre': 'Banco - Cuenta Corriente', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '1.1.02', 'saldo': 0},
    {'codigo': '1.1.02.002', 'nombre': 'Banco - Cuenta Ahorros', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '1.1.02', 'saldo': 0},
    {'codigo': '1.1.03', 'nombre': 'CUENTAS POR COBRAR', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': False, 'padre': '1.1'},
    {'codigo': '1.1.03.001', 'nombre': 'Cuentas por Cobrar - Matrículas', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '1.1.03', 'saldo': 0, 'requiere_tercero': True},
    {'codigo': '1.1.03.002', 'nombre': 'Cuentas por Cobrar - Mensualidades', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '1.1.03', 'saldo': 0, 'requiere_tercero': True},
    {'codigo': '1.1.03.003', 'nombre': 'Cuentas por Cobrar - Otros', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '1.1.03', 'saldo': 0, 'requiere_tercero': True},
    {'codigo': '1.1.04', 'nombre': 'INVENTARIOS', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': False, 'padre': '1.1'},
    {'codigo': '1.1.04.001', 'nombre': 'Inventario de Útiles Escolares', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '1.1.04', 'saldo': 0},
    {'codigo': '1.1.04.002', 'nombre': 'Inventario de Libros', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '1.1.04', 'saldo': 0},
    
    {'codigo': '1.2', 'nombre': 'ACTIVO NO CORRIENTE', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': False, 'padre': '1'},
    {'codigo': '1.2.01', 'nombre': 'PROPIEDAD, PLANTA Y EQUIPO', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': False, 'padre': '1.2'},
    {'codigo': '1.2.01.001', 'nombre': 'Edificios', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '1.2.01', 'saldo': 0},
    {'codigo': '1.2.01.002', 'nombre': 'Mobiliario y Equipo', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '1.2.01', 'saldo': 0},
    {'codigo': '1.2.01.003', 'nombre': 'Equipo de Cómputo', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '1.2.01', 'saldo': 0},
    {'codigo': '1.2.01.004', 'nombre': 'Vehículos', 'tipo': 'ACTIVO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '1.2.01', 'saldo': 0},
    
    # ===== PASIVOS =====
    {'codigo': '2', 'nombre': 'PASIVO', 'tipo': 'PASIVO', 'naturaleza': 'ACREEDORA', 'es_detalle': False},
    {'codigo': '2.1', 'nombre': 'PASIVO CORRIENTE', 'tipo': 'PASIVO', 'naturaleza': 'ACREEDORA', 'es_detalle': False, 'padre': '2'},
    {'codigo': '2.1.01', 'nombre': 'CUENTAS POR PAGAR', 'tipo': 'PASIVO', 'naturaleza': 'ACREEDORA', 'es_detalle': False, 'padre': '2.1'},
    {'codigo': '2.1.01.001', 'nombre': 'Cuentas por Pagar - Proveedores', 'tipo': 'PASIVO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '2.1.01', 'saldo': 0, 'requiere_tercero': True},
    {'codigo': '2.1.01.002', 'nombre': 'Cuentas por Pagar - Servicios', 'tipo': 'PASIVO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '2.1.01', 'saldo': 0, 'requiere_tercero': True},
    {'codigo': '2.1.02', 'nombre': 'OBLIGACIONES LABORALES', 'tipo': 'PASIVO', 'naturaleza': 'ACREEDORA', 'es_detalle': False, 'padre': '2.1'},
    {'codigo': '2.1.02.001', 'nombre': 'Sueldos por Pagar', 'tipo': 'PASIVO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '2.1.02', 'saldo': 0},
    {'codigo': '2.1.02.002', 'nombre': 'Prestaciones Sociales por Pagar', 'tipo': 'PASIVO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '2.1.02', 'saldo': 0},
    {'codigo': '2.1.03', 'nombre': 'RETENCIONES Y APORTES', 'tipo': 'PASIVO', 'naturaleza': 'ACREEDORA', 'es_detalle': False, 'padre': '2.1'},
    {'codigo': '2.1.03.001', 'nombre': 'Retenciones Fiscales', 'tipo': 'PASIVO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '2.1.03', 'saldo': 0},
    {'codigo': '2.1.03.002', 'nombre': 'Aportes de Seguridad Social', 'tipo': 'PASIVO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '2.1.03', 'saldo': 0},
    
    {'codigo': '2.2', 'nombre': 'PASIVO NO CORRIENTE', 'tipo': 'PASIVO', 'naturaleza': 'ACREEDORA', 'es_detalle': False, 'padre': '2'},
    {'codigo': '2.2.01', 'nombre': 'PRÉSTAMOS A LARGO PLAZO', 'tipo': 'PASIVO', 'naturaleza': 'ACREEDORA', 'es_detalle': False, 'padre': '2.2'},
    {'codigo': '2.2.01.001', 'nombre': 'Préstamos Bancarios LP', 'tipo': 'PASIVO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '2.2.01', 'saldo': 0},
    
    # ===== CAPITAL/PATRIMONIO =====
    {'codigo': '3', 'nombre': 'PATRIMONIO', 'tipo': 'CAPITAL', 'naturaleza': 'ACREEDORA', 'es_detalle': False},
    {'codigo': '3.1', 'nombre': 'CAPITAL INSTITUCIONAL', 'tipo': 'CAPITAL', 'naturaleza': 'ACREEDORA', 'es_detalle': False, 'padre': '3'},
    {'codigo': '3.1.01', 'nombre': 'Capital Social', 'tipo': 'CAPITAL', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '3.1', 'saldo': 0},
    {'codigo': '3.2', 'nombre': 'RESULTADOS', 'tipo': 'CAPITAL', 'naturaleza': 'ACREEDORA', 'es_detalle': False, 'padre': '3'},
    {'codigo': '3.2.01', 'nombre': 'Resultado del Ejercicio', 'tipo': 'CAPITAL', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '3.2', 'saldo': 0},
    {'codigo': '3.2.02', 'nombre': 'Resultados Acumulados', 'tipo': 'CAPITAL', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '3.2', 'saldo': 0},
    
    # ===== INGRESOS =====
    {'codigo': '4', 'nombre': 'INGRESOS', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': False},
    {'codigo': '4.1', 'nombre': 'INGRESOS OPERACIONALES', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': False, 'padre': '4'},
    {'codigo': '4.1.01', 'nombre': 'INGRESOS POR MATRÍCULAS', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': False, 'padre': '4.1'},
    {'codigo': '4.1.01.001', 'nombre': 'Matrículas - Educación Inicial', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '4.1.01', 'saldo': 0},
    {'codigo': '4.1.01.002', 'nombre': 'Matrículas - Educación Básica', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '4.1.01', 'saldo': 0},
    {'codigo': '4.1.01.003', 'nombre': 'Matrículas - Educación Media', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '4.1.01', 'saldo': 0},
    {'codigo': '4.1.02', 'nombre': 'INGRESOS POR MENSUALIDADES', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': False, 'padre': '4.1'},
    {'codigo': '4.1.02.001', 'nombre': 'Mensualidades - Educación Inicial', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '4.1.02', 'saldo': 0},
    {'codigo': '4.1.02.002', 'nombre': 'Mensualidades - Educación Básica', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '4.1.02', 'saldo': 0},
    {'codigo': '4.1.02.003', 'nombre': 'Mensualidades - Educación Media', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '4.1.02', 'saldo': 0},
    {'codigo': '4.1.03', 'nombre': 'OTROS INGRESOS EDUCATIVOS', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': False, 'padre': '4.1'},
    {'codigo': '4.1.03.001', 'nombre': 'Ingresos por Transporte', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '4.1.03', 'saldo': 0},
    {'codigo': '4.1.03.002', 'nombre': 'Ingresos por Cafetería', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '4.1.03', 'saldo': 0},
    {'codigo': '4.1.03.003', 'nombre': 'Ingresos por Venta de Uniformes', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '4.1.03', 'saldo': 0},
    {'codigo': '4.1.03.004', 'nombre': 'Ingresos por Venta de Útiles', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '4.1.03', 'saldo': 0},
    
    {'codigo': '4.2', 'nombre': 'INGRESOS NO OPERACIONALES', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': False, 'padre': '4'},
    {'codigo': '4.2.01', 'nombre': 'Intereses Ganados', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '4.2', 'saldo': 0},
    {'codigo': '4.2.02', 'nombre': 'Donaciones Recibidas', 'tipo': 'INGRESO', 'naturaleza': 'ACREEDORA', 'es_detalle': True, 'padre': '4.2', 'saldo': 0},
    
    # ===== GASTOS =====
    {'codigo': '5', 'nombre': 'GASTOS', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': False},
    {'codigo': '5.1', 'nombre': 'GASTOS OPERACIONALES', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': False, 'padre': '5'},
    {'codigo': '5.1.01', 'nombre': 'GASTOS DE PERSONAL', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': False, 'padre': '5.1'},
    {'codigo': '5.1.01.001', 'nombre': 'Sueldos y Salarios - Docentes', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '5.1.01', 'saldo': 0, 'requiere_centro_costo': True},
    {'codigo': '5.1.01.002', 'nombre': 'Sueldos y Salarios - Administrativos', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '5.1.01', 'saldo': 0, 'requiere_centro_costo': True},
    {'codigo': '5.1.01.003', 'nombre': 'Prestaciones Sociales', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '5.1.01', 'saldo': 0},
    {'codigo': '5.1.01.004', 'nombre': 'Aportes de Seguridad Social', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '5.1.01', 'saldo': 0},
    {'codigo': '5.1.02', 'nombre': 'SERVICIOS PÚBLICOS', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': False, 'padre': '5.1'},
    {'codigo': '5.1.02.001', 'nombre': 'Energía Eléctrica', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '5.1.02', 'saldo': 0},
    {'codigo': '5.1.02.002', 'nombre': 'Agua', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '5.1.02', 'saldo': 0},
    {'codigo': '5.1.02.003', 'nombre': 'Teléfono e Internet', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '5.1.02', 'saldo': 0},
    {'codigo': '5.1.03', 'nombre': 'ARRENDAMIENTOS', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': False, 'padre': '5.1'},
    {'codigo': '5.1.03.001', 'nombre': 'Arrendamiento de Edificio', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '5.1.03', 'saldo': 0},
    {'codigo': '5.1.04', 'nombre': 'MANTENIMIENTO Y REPARACIONES', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': False, 'padre': '5.1'},
    {'codigo': '5.1.04.001', 'nombre': 'Mantenimiento de Edificio', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '5.1.04', 'saldo': 0},
    {'codigo': '5.1.04.002', 'nombre': 'Mantenimiento de Equipo', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '5.1.04', 'saldo': 0},
    {'codigo': '5.1.05', 'nombre': 'ÚTILES Y SUMINISTROS', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': False, 'padre': '5.1'},
    {'codigo': '5.1.05.001', 'nombre': 'Útiles de Oficina', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '5.1.05', 'saldo': 0},
    {'codigo': '5.1.05.002', 'nombre': 'Material Didáctico', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '5.1.05', 'saldo': 0},
    {'codigo': '5.1.05.003', 'nombre': 'Productos de Limpieza', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '5.1.05', 'saldo': 0},
    
    {'codigo': '5.2', 'nombre': 'GASTOS NO OPERACIONALES', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': False, 'padre': '5'},
    {'codigo': '5.2.01', 'nombre': 'Gastos Financieros', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '5.2', 'saldo': 0},
    {'codigo': '5.2.02', 'nombre': 'Gastos Bancarios', 'tipo': 'GASTO', 'naturaleza': 'DEUDORA', 'es_detalle': True, 'padre': '5.2', 'saldo': 0},
]

# Crear las cuentas
cuentas_creadas = {}
contador = 0

for cuenta_data in cuentas_data:
    try:
        # Buscar cuenta padre si existe
        cuenta_padre = None
        if 'padre' in cuenta_data:
            codigo_padre = cuenta_data['padre']
            cuenta_padre = cuentas_creadas.get(codigo_padre)
        
        # Crear o actualizar la cuenta
        cuenta, created = PlanCuentas.objects.update_or_create(
            codigo=cuenta_data['codigo'],
            defaults={
                'nombre': cuenta_data['nombre'],
                'tipo_cuenta': cuenta_data['tipo'],
                'naturaleza': cuenta_data['naturaleza'],
                'es_detalle': cuenta_data.get('es_detalle', True),
                'cuenta_padre': cuenta_padre,
                'saldo_inicial': Decimal(cuenta_data.get('saldo', 0)),
                'saldo_actual': Decimal(cuenta_data.get('saldo', 0)),
                'activo': True,
                'requiere_centro_costo': cuenta_data.get('requiere_centro_costo', False),
                'requiere_tercero': cuenta_data.get('requiere_tercero', False),
                'creado_por': admin_user,
            }
        )
        
        cuentas_creadas[cuenta.codigo] = cuenta
        contador += 1
        
        if created:
            print(f"✓ Creada: {cuenta.codigo} - {cuenta.nombre}")
        else:
            print(f"↻ Actualizada: {cuenta.codigo} - {cuenta.nombre}")
            
    except Exception as e:
        print(f"✗ Error en {cuenta_data['codigo']}: {str(e)}")

print("\n" + "=" * 60)
print(f"PROCESO COMPLETADO: {contador} cuentas procesadas")
print("=" * 60)
print(f"\nTotal de cuentas en el sistema: {PlanCuentas.objects.count()}")
print(f"Cuentas activas: {PlanCuentas.objects.filter(activo=True).count()}")
print(f"Cuentas de detalle: {PlanCuentas.objects.filter(es_detalle=True).count()}")
print(f"Cuentas agrupadores: {PlanCuentas.objects.filter(es_detalle=False).count()}")
print("\n" + "=" * 60)
print("Puede acceder al Plan de Cuentas en:")
print("http://127.0.0.1:8000/contabilidad/plan-cuentas/")
print("=" * 60)

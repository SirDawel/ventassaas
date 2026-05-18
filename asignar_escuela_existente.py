#!/usr/bin/env python
"""
Script para asignar todos los registros existentes a la escuela de prueba
Ejecutar: python asignar_escuela_existente.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.models_escuela import Escuela
from escuelaweb.models import (
    CustomUser, AnhoEscolar, Estudiante, Profesor, Curso, Materia,
    GrupoFamiliar, ConceptoPago, Pago, Factura,
    # Nuevos modelos agregados
    Matricula, StudentGroup, Asistencia, AsistenciaPersonal,
    TarifaEstudiante, DetalleFactura, PagoFactura, CodigoAnulacion,
    Articulo, CategoriaArticulo, MovimientoInventario,
    PlanCuentas, AsientoContable, DetalleAsiento,
    ListaCotejo, EvaluacionDiagnostica, Rubrica,
    ConfiguracionEscuela, TransaccionPOS, TerminalEstudiante,
    Mensualidad, Tutor, Persona
)

def main():
    print("=" * 60)
    print("ASIGNACIÓN DE ESCUELA A DATOS EXISTENTES")
    print("=" * 60)
    
    # Obtener o crear escuela de prueba
    escuela, created = Escuela.objects.get_or_create(
        nombre_corto='prueba',
        defaults={
            'nombre': 'Escuela de Prueba',
            'direccion': 'Dirección de Prueba',
            'telefono': '555-0000',
            'email': 'prueba@escuela.com',
            'activa': True,
            'plan': 'basico',
            'fecha_inicio_suscripcion': '2025-01-01',
            'fecha_fin_suscripcion': '2026-01-01',
        }
    )
    
    if created:
        print(f"✅ Escuela creada: {escuela.nombre}")
    else:
        print(f"✅ Escuela encontrada: {escuela.nombre}")
    
    print(f"   ID: {escuela.id}")
    print(f"   Nombre corto: {escuela.nombre_corto}")
    print()
    
    # Modelos a actualizar
    modelos = [
        ('CustomUser', CustomUser),
        ('AnhoEscolar', AnhoEscolar),
        ('Estudiante', Estudiante),
        ('Profesor', Profesor),
        ('Curso', Curso),
        ('Materia', Materia),
        ('GrupoFamiliar', GrupoFamiliar),
        ('ConceptoPago', ConceptoPago),
        ('Pago', Pago),
        ('Factura', Factura),
        # Académicos
        ('Matricula', Matricula),
        ('StudentGroup', StudentGroup),
        ('Asistencia', Asistencia),
        ('AsistenciaPersonal', AsistenciaPersonal),
        # Financieros
        ('TarifaEstudiante', TarifaEstudiante),
        ('DetalleFactura', DetalleFactura),
        ('PagoFactura', PagoFactura),
        ('CodigoAnulacion', CodigoAnulacion),
        ('TransaccionPOS', TransaccionPOS),
        ('TerminalEstudiante', TerminalEstudiante),
        # Inventario
        ('Articulo', Articulo),
        ('CategoriaArticulo', CategoriaArticulo),
        ('MovimientoInventario', MovimientoInventario),
        # Contabilidad
        ('PlanCuentas', PlanCuentas),
        ('AsientoContable', AsientoContable),
        ('DetalleAsiento', DetalleAsiento),
        # Evaluaciones
        ('ListaCotejo', ListaCotejo),
        ('EvaluacionDiagnostica', EvaluacionDiagnostica),
        ('Rubrica', Rubrica),
        # Configuración
        ('ConfiguracionEscuela', ConfiguracionEscuela),
        # Legacy
        ('Mensualidad', Mensualidad),
        ('Tutor', Tutor),
        ('Persona', Persona),
    ]
    
    print("Asignando registros...")
    print("-" * 60)
    
    total_actualizados = 0
    
    for nombre_modelo, modelo in modelos:
        # Contar registros sin escuela
        sin_escuela = modelo.objects.filter(escuela__isnull=True).count()
        
        if sin_escuela > 0:
            # Actualizar registros
            actualizados = modelo.objects.filter(escuela__isnull=True).update(escuela=escuela)
            total_actualizados += actualizados
            print(f"✅ {nombre_modelo:20} - {actualizados:5} registros actualizados")
        else:
            total = modelo.objects.count()
            print(f"   {nombre_modelo:20} - {total:5} registros (ya asignados)")
    
    print("-" * 60)
    print(f"✅ Total de registros actualizados: {total_actualizados}")
    print()
    print("=" * 60)
    print("PROCESO COMPLETADO")
    print("=" * 60)
    print()
    print("Siguiente paso:")
    print("  1. Verificar que todos los registros tengan escuela asignada")
    print("  2. Modificar models.py para quitar null=True y blank=True")
    print("  3. Ejecutar: python manage.py makemigrations")
    print("  4. Ejecutar: python manage.py migrate")
    print()

if __name__ == '__main__':
    main()

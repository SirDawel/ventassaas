"""
Script para migrar las 4 escuelas existentes a schemas separados de django-tenants
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from django.db import connection
from escuelaweb.tenant_models import Client, Domain
from escuelaweb.models import (
    CustomUser, AnhoEscolar, Estudiante, Profesor, Curso, Materia,
    GrupoFamiliar, ConceptoPago, Pago, Factura, Matricula, StudentGroup,
    Asistencia, AsistenciaPersonal, TarifaEstudiante, DetalleFactura,
    PagoFactura, CodigoAnulacion, Articulo, CategoriaArticulo,
    MovimientoInventario, PlanCuentas, AsientoContable, DetalleAsiento,
    ListaCotejo, EvaluacionDiagnostica, Rubrica, ConfiguracionEscuela,
    TransaccionPOS, TerminalEstudiante, Mensualidad, Tutor, Persona
)

def obtener_escuelas_existentes():
    """Obtiene escuelas de la tabla antigua antes de eliminarla"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, nombre, nombre_corto, email_contacto, telefono, direccion,
                   logo, color_primario, color_secundario, fecha_creacion, activo
            FROM escuelaweb_escuela
        """)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def crear_tenant_desde_escuela(escuela_data):
    """Crea tenant (Client) y domain para una escuela existente"""
    
    nombre_corto = escuela_data['nombre_corto']
    
    # Verificar si el tenant ya existe
    if Client.objects.filter(schema_name=nombre_corto).exists():
        print(f"⏭️  Tenant '{nombre_corto}' ya existe, saltando...")
        return Client.objects.get(schema_name=nombre_corto)
    
    # Crear tenant (esto crea el schema automáticamente)
    print(f"📁 Creando schema para '{escuela_data['nombre']}'...")
    tenant = Client.objects.create(
        schema_name=nombre_corto,
        nombre=escuela_data['nombre'],
        nombre_corto=nombre_corto,
        email_contacto=escuela_data['email_contacto'] or f'{nombre_corto}@escuela.com',
        telefono=escuela_data['telefono'] or '',
        direccion=escuela_data['direccion'] or '',
        plan='prueba',
        max_usuarios=500,
        activo=escuela_data['activo'],
        logo=escuela_data['logo'] or '',
        color_primario=escuela_data['color_primario'] or '#007bff',
        color_secundario=escuela_data['color_secundario'] or '#6c757d'
    )
    
    # Crear dominio
    print(f"🌐 Creando dominio {nombre_corto}.localhost...")
    Domain.objects.create(
        domain=f'{nombre_corto}.localhost',
        tenant=tenant,
        is_primary=True
    )
    
    return tenant

def copiar_registros_modelo(modelo, escuela_id, tenant):
    """Copia registros de un modelo al schema del tenant"""
    # Obtener registros de la escuela desde public schema
    connection.set_schema_to_public()
    registros = list(modelo.objects.filter(escuela_id=escuela_id).values())
    
    if not registros:
        return 0
    
    # Cambiar al schema del tenant
    connection.set_tenant(tenant)
    
    # Eliminar campo escuela_id de los registros
    for registro in registros:
        if 'escuela_id' in registro:
            del registro['escuela_id']
    
    # Bulk create en el schema del tenant
    objetos = [modelo(**registro) for registro in registros]
    modelo.objects.bulk_create(objetos, ignore_conflicts=True)
    
    count = len(objetos)
    return count

def migrar_escuela(escuela_data):
    """Migra una escuela completa a su propio schema"""
    escuela_id = escuela_data['id']
    nombre = escuela_data['nombre']
    nombre_corto = escuela_data['nombre_corto']
    
    print(f"\n{'='*60}")
    print(f"🏫 MIGRANDO: {nombre} ({nombre_corto})")
    print(f"{'='*60}")
    
    # 1. Crear tenant
    tenant = crear_tenant_desde_escuela(escuela_data)
    
    # 2. Migrar todos los modelos
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
        ('Matricula', Matricula),
        ('StudentGroup', StudentGroup),
        ('Asistencia', Asistencia),
        ('AsistenciaPersonal', AsistenciaPersonal),
        ('TarifaEstudiante', TarifaEstudiante),
        ('DetalleFactura', DetalleFactura),
        ('PagoFactura', PagoFactura),
        ('CodigoAnulacion', CodigoAnulacion),
        ('Articulo', Articulo),
        ('CategoriaArticulo', CategoriaArticulo),
        ('MovimientoInventario', MovimientoInventario),
        ('PlanCuentas', PlanCuentas),
        ('AsientoContable', AsientoContable),
        ('DetalleAsiento', DetalleAsiento),
        ('ListaCotejo', ListaCotejo),
        ('EvaluacionDiagnostica', EvaluacionDiagnostica),
        ('Rubrica', Rubrica),
        ('ConfiguracionEscuela', ConfiguracionEscuela),
        ('TransaccionPOS', TransaccionPOS),
        ('TerminalEstudiante', TerminalEstudiante),
        ('Mensualidad', Mensualidad),
        ('Tutor', Tutor),
        ('Persona', Persona),
    ]
    
    total_registros = 0
    
    for nombre_modelo, modelo in modelos:
        try:
            count = copiar_registros_modelo(modelo, escuela_id, tenant)
            if count > 0:
                print(f"  ✅ {nombre_modelo}: {count} registros migrados")
                total_registros += count
        except Exception as e:
            print(f"  ⚠️  {nombre_modelo}: Error - {str(e)}")
    
    # Volver a public schema
    connection.set_schema_to_public()
    
    print(f"\n✅ Total migrado: {total_registros} registros")
    print(f"🔗 Acceso: http://{nombre_corto}.localhost:8000/")
    
    return total_registros

def main():
    print("🚀 INICIANDO MIGRACIÓN DE ESCUELAS A SCHEMAS SEPARADOS")
    print("="*60)
    
    # 1. Obtener escuelas existentes
    print("\n📋 Obteniendo escuelas existentes...")
    try:
        escuelas = obtener_escuelas_existentes()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("⚠️  La tabla escuelaweb_escuela no existe o ya fue eliminada")
        return
    
    print(f"✅ Encontradas {len(escuelas)} escuelas")
    
    # 2. Migrar cada escuela
    total_general = 0
    for escuela in escuelas:
        try:
            total = migrar_escuela(escuela)
            total_general += total
        except Exception as e:
            print(f"❌ Error migrando {escuela['nombre']}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 3. Resumen final
    print(f"\n{'='*60}")
    print(f"✅ MIGRACIÓN COMPLETA")
    print(f"📊 Total de registros migrados: {total_general}")
    print(f"🏫 Escuelas migradas: {len(escuelas)}")
    print(f"\nAhora puedes aplicar la migración 0058 para eliminar los campos escuela_id:")
    print(f"  python manage.py migrate_schemas")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

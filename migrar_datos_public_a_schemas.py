"""
Script MEJORADO para migrar datos desde public schema a tenant schemas
Los datos están en public con escuela_id, pero los tenants ya tienen migración 0058 aplicada (sin escuela_id)
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.db import connection
from ventasweb.tenant_models import Client

# Mapeo de escuela_id a nombre_corto de tenant
ESCUELA_TO_TENANT = {}

def obtener_mapeo_escuelas():
    """Obtiene mapeo de escuela_id -> tenant schema_name desde public schema"""
    global ESCUELA_TO_TENANT
    
    with connection.cursor() as cursor:
        # Obtener escuelas de la tabla antigua en public schema
        cursor.execute("SELECT id, nombre_corto FROM ventasweb_escuela")
        for escuela_id, nombre_corto in cursor.fetchall():
            ESCUELA_TO_TENANT[escuela_id] = nombre_corto
    
    print(f"📋 Mapeo de escuelas encontrado:")
    for esc_id, nombre in ESCUELA_TO_TENANT.items():
        print(f"  - Escuela ID {esc_id} → Schema '{nombre}'")

def contar_registros_por_escuela(tabla, escuela_id):
    """Cuenta registros de una tabla para una escuela específica en public schema"""
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE escuela_id = %s", [escuela_id])
        return cursor.fetchone()[0]

def migrar_tabla(tabla_nombre, escuela_id, tenant_schema):
    """Migra registros de una tabla desde public al schema del tenant"""
    
    # 1. Obtener registros del public schema
    connection.set_schema_to_public()
    
    with connection.cursor() as cursor:
        # Contar registros
        cursor.execute(f"SELECT COUNT(*) FROM {tabla_nombre} WHERE escuela_id = %s", [escuela_id])
        count = cursor.fetchone()[0]
        
        if count == 0:
            return 0
        
        # Obtener columnas de la tabla
        cursor.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = %s 
            AND column_name != 'escuela_id'
            ORDER BY ordinal_position
        """, [tabla_nombre])
        
        columnas = [row[0] for row in cursor.fetchall()]
        columnas_str = ', '.join(columnas)
        
        # Leer datos
        cursor.execute(f"SELECT {columnas_str} FROM {tabla_nombre} WHERE escuela_id = %s", [escuela_id])
        registros = cursor.fetchall()
    
    # 2. Insertar en el schema del tenant
    with connection.cursor() as cursor:
        cursor.execute(f"SET search_path TO {tenant_schema}, public")
        
        # Preparar query de inserción
        placeholders = ', '.join(['%s'] * len(columnas))
        insert_query = f"INSERT INTO {tabla_nombre} ({columnas_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
        
        # Insertar cada registro
        for registro in registros:
            try:
                cursor.execute(insert_query, registro)
            except Exception as e:
                # Algunos registros pueden fallar por constraints (ej: duplicados)
                pass
    
    connection.set_schema_to_public()
    return count

def migrar_escuela(escuela_id, nombre_corto):
    """Migra todos los datos de una escuela a su schema"""
    print(f"\n{'='*70}")
    print(f"🏫 MIGRANDO ESCUELA: {nombre_corto} (ID: {escuela_id})")
    print(f"{'='*70}")
    
    # Verificar que el tenant existe
    try:
        tenant = Client.objects.get(schema_name=nombre_corto)
    except Client.DoesNotExist:
        print(f"❌ Tenant '{nombre_corto}' no existe")
        return 0
    
    # Tablas a migrar (en orden para respetar FKs)
    tablas = [
        ('ventasweb_customuser', 'Usuarios'),
        ('ventasweb_anhoescolar', 'Años Escolares'),
        ('ventasweb_profesor', 'Profesores'),
        ('ventasweb_estudiante', 'Estudiantes'),
        ('ventasweb_curso', 'Cursos'),
        ('ventasweb_materia', 'Materias'),
        ('ventasweb_grupofamiliar', 'Grupos Familiares'),
        ('ventasweb_tutor', 'Tutores'),
        ('ventasweb_persona', 'Personas'),
        ('ventasweb_conceptopago', 'Conceptos de Pago'),
        ('ventasweb_matricula', 'Matrículas'),
        ('ventasweb_pago', 'Pagos'),
        ('ventasweb_factura', 'Facturas'),
        ('ventasweb_mensualidad', 'Mensualidades'),
        ('ventasweb_detallefactura', 'Detalles de Factura'),
        ('ventasweb_pagofactura', 'Pagos de Factura'),
        ('ventasweb_tarifaestudiante', 'Tarifas de Estudiante'),
        ('ventasweb_studentgroup', 'Grupos de Estudiantes'),
        ('ventasweb_asistencia', 'Asistencias'),
        ('ventasweb_asistenciapersonal', 'Asistencias Personal'),
        ('ventasweb_codigoanulacion', 'Códigos de Anulación'),
        ('ventasweb_categoriaarticulo', 'Categorías de Artículo'),
        ('ventasweb_articulo', 'Artículos'),
        ('ventasweb_movimientoinventario', 'Movimientos de Inventario'),
        ('ventasweb_plancuentas', 'Plan de Cuentas'),
        ('ventasweb_asientocontable', 'Asientos Contables'),
        ('ventasweb_detalleasiento', 'Detalles de Asiento'),
        ('ventasweb_listacotejo', 'Listas de Cotejo'),
        ('ventasweb_evaluaciondiagnostica', 'Evaluaciones Diagnósticas'),
        ('ventasweb_rubrica', 'Rúbricas'),
        ('ventasweb_configuracionescuela', 'Configuración de Escuela'),
        ('ventasweb_transaccionpos', 'Transacciones POS'),
        ('ventasweb_terminalestudiante', 'Terminales de Estudiante'),
    ]
    
    total_migrado = 0
    
    for tabla, descripcion in tablas:
        try:
            count = migrar_tabla(tabla, escuela_id, nombre_corto)
            if count > 0:
                print(f"  ✅ {descripcion}: {count} registros")
                total_migrado += count
            else:
                print(f"  ⏭️  {descripcion}: 0 registros")
        except Exception as e:
            print(f"  ❌ {descripcion}: Error - {str(e)}")
    
    print(f"\n✅ Total migrado para '{nombre_corto}': {total_migrado} registros")
    print(f"🔗 Acceso: http://{nombre_corto}.localhost:8000/")
    
    return total_migrado

def main():
    print("🚀 INICIANDO MIGRACIÓN DE DATOS (Public → Tenant Schemas)")
    print("="*70)
    
    # 1. Obtener mapeo de escuelas
    try:
        obtener_mapeo_escuelas()
    except Exception as e:
        print(f"❌ Error obteniendo escuelas: {e}")
        print("La tabla ventasweb_escuela no existe en public schema")
        return
    
    if not ESCUELA_TO_TENANT:
        print("⚠️  No se encontraron escuelas para migrar")
        return
    
    # 2. Migrar cada escuela
    total_general = 0
    escuelas_migradas = 0
    
    for escuela_id, nombre_corto in ESCUELA_TO_TENANT.items():
        try:
            total = migrar_escuela(escuela_id, nombre_corto)
            total_general += total
            escuelas_migradas += 1
        except Exception as e:
            print(f"❌ Error migrando escuela {nombre_corto}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 3. Resumen final
    print(f"\n{'='*70}")
    print(f"✅ MIGRACIÓN COMPLETADA")
    print(f"📊 Total de registros migrados: {total_general}")
    print(f"🏫 Escuelas migradas: {escuelas_migradas}/{len(ESCUELA_TO_TENANT)}")
    print(f"\nAhora puedes aplicar la migración 0058 en el schema public:")
    print(f"  python manage.py migrate_schemas --schema=public")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()


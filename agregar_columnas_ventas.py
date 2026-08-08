"""
Script para agregar las columnas de ventas a ventasweb_customuser en todos los schemas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.db import connection

def agregar_columnas_ventas():
    """Agrega las columnas de ventas a la tabla customuser en todos los schemas"""
    
    print("🔧 AGREGANDO COLUMNAS DE VENTAS A CUSTOMUSER")
    print("=" * 70)
    
    # Obtener todos los schemas
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY CASE WHEN schema_name = 'public' THEN 0 ELSE 1 END, schema_name
        """)
        
        schemas = [row[0] for row in cursor.fetchall()]
    
    print(f"\n📁 Schemas encontrados: {len(schemas)}")
    
    # Definir las columnas a agregar
    columnas = [
        ('tipo_cliente', 'VARCHAR(20)'),
        ('limite_credito', 'NUMERIC(12, 2) DEFAULT 0 NOT NULL'),
        ('dias_credito', 'INTEGER DEFAULT 30 NOT NULL'),
        ('descuento_cliente', 'NUMERIC(5, 2) DEFAULT 0 NOT NULL'),
        ('comision_vendedor', 'NUMERIC(5, 2) DEFAULT 0 NOT NULL'),
        ('meta_mensual', 'NUMERIC(12, 2) DEFAULT 0 NOT NULL'),
        ('zona_venta', 'VARCHAR(100)'),
        ('cliente_corporativo_id', 'BIGINT'),
    ]
    
    print(f"\n🔨 Agregando columnas en cada schema...")
    print("=" * 70)
    
    exitosos = 0
    ya_existentes = 0
    errores = 0
    
    for schema in schemas:
        print(f"\n📂 Schema: {schema}")
        
        with connection.cursor() as cursor:
            # Cambiar al schema
            cursor.execute(f'SET search_path TO "{schema}"')
            
            for nombre_col, tipo_col in columnas:
                try:
                    # Verificar si la columna ya existe
                    cursor.execute(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = %s 
                        AND table_name = 'ventasweb_customuser' 
                        AND column_name = %s
                    """, [schema, nombre_col])
                    
                    if cursor.fetchone():
                        print(f"   ⏭ {nombre_col}: Ya existe")
                        ya_existentes += 1
                    else:
                        # Agregar la columna
                        cursor.execute(f"""
                            ALTER TABLE "{schema}".ventasweb_customuser 
                            ADD COLUMN {nombre_col} {tipo_col}
                        """)
                        connection.connection.commit()
                        print(f"   ✓ {nombre_col}: Agregada")
                        exitosos += 1
                        
                except Exception as e:
                    print(f"   ✗ {nombre_col}: Error - {e}")
                    errores += 1
    
    print("\n" + "=" * 70)
    print(f"✅ PROCESO COMPLETADO:")
    print(f"   - Columnas agregadas: {exitosos}")
    print(f"   - Columnas ya existentes: {ya_existentes}")
    if errores > 0:
        print(f"   - Errores: {errores}")
    
    # Agregar tabla vendedor a factura
    print(f"\n🔨 Agregando columna 'vendedor_id' a ventasweb_factura...")
    print("=" * 70)
    
    exitosos_factura = 0
    ya_existe_factura = 0
    
    for schema in schemas:
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema}"')
            
            try:
                # Verificar si la columna ya existe
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = %s 
                    AND table_name = 'ventasweb_factura' 
                    AND column_name = 'vendedor_id'
                """, [schema])
                
                if cursor.fetchone():
                    ya_existe_factura += 1
                else:
                    cursor.execute(f"""
                        ALTER TABLE "{schema}".ventasweb_factura 
                        ADD COLUMN vendedor_id BIGINT
                    """)
                    
                    # Agregar foreign key
                    cursor.execute(f"""
                        ALTER TABLE "{schema}".ventasweb_factura 
                        ADD CONSTRAINT ventasweb_f_vendedo_bd7a9a_fk 
                        FOREIGN KEY (vendedor_id) 
                        REFERENCES "{schema}".ventasweb_customuser(id)
                        DEFERRABLE INITIALLY DEFERRED
                    """)
                    
                    connection.connection.commit()
                    print(f"   ✓ {schema}: Columna vendedor_id agregada")
                    exitosos_factura += 1
                    
            except Exception as e:
                if 'already exists' in str(e):
                    ya_existe_factura += 1
                else:
                    print(f"   ✗ {schema}: Error - {e}")
    
    print(f"\n✅ Factura: {exitosos_factura} agregadas, {ya_existe_factura} ya existían")
    print("\n✅ ¡Proceso completado! Ahora reinicia el servidor.")

if __name__ == '__main__':
    try:
        agregar_columnas_ventas()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)

"""
Script para agregar TenantManager a todos los modelos con campo escuela
"""
import re

# Leer archivo
with open('escuelaweb/models.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Modelos que necesitan TenantManager (tienen campo escuela)
modelos_con_escuela = [
    'CustomUser', 'AnhoEscolar', 'Estudiante', 'Profesor', 'Curso', 'Materia',
    'GrupoFamiliar', 'ConceptoPago', 'Pago', 'Factura', 'Matricula',
    'StudentGroup', 'Asistencia', 'AsistenciaPersonal', 'TarifaEstudiante',
    'DetalleFactura', 'PagoFactura', 'CodigoAnulacion', 'Articulo',
    'CategoriaArticulo', 'MovimientoInventario', 'PlanCuentas',
    'AsientoContable', 'DetalleAsiento', 'ListaCotejo', 'EvaluacionDiagnostica',
    'Rubrica', 'ConfiguracionEscuela', 'TransaccionPOS', 'TerminalEstudiante',
    'Mensualidad', 'Tutor', 'Persona'
]

# Agregar import de TenantManager al inicio del archivo
if 'from .tenant_managers import TenantManager' not in contenido:
    # Buscar donde están los imports
    import_pattern = r'(from django\.db import models)'
    contenido = re.sub(
        import_pattern,
        r'\1\nfrom .tenant_managers import TenantManager',
        contenido,
        count=1
    )
    print("✅ Agregado import de TenantManager")

# Para cada modelo, agregar objects = TenantManager()
contador = 0
for modelo in modelos_con_escuela:
    # Patrón para encontrar la definición de clase y agregar el manager justo después
    # Buscar: class ModeloName(models.Model): seguido de campos/Meta
    # Insertar: objects = TenantManager() antes del primer campo que no sea escuela
    
    # Patrón: class Modelo( ... después de escuela FK, antes del siguiente campo
    pattern = rf'(class {modelo}\([^)]+\):.*?escuela = models\.ForeignKey\([^)]+\)[^\n]*\n(?:\s+[^\n]+\n)*?)'
    
    # Verificar si ya tiene objects definido
    if re.search(rf'class {modelo}\([^)]+\):.*?objects\s*=', contenido, re.DOTALL):
        print(f"⏭️  {modelo}: Ya tiene manager definido")
        continue
    
    # Buscar donde insertar (después del campo escuela y sus parámetros)
    match = re.search(
        rf'(class {modelo}\([^)]+\):.*?escuela = models\.ForeignKey\(\s*\'Escuela\'[^)]+\)\s*\n)',
        contenido,
        re.DOTALL
    )
    
    if match:
        # Insertar el manager después del campo escuela
        insert_pos = match.end()
        contenido = (
            contenido[:insert_pos] +
            '\n    # Multi-Tenant Manager\n    objects = TenantManager()\n' +
            contenido[insert_pos:]
        )
        contador += 1
        print(f"✅ {modelo}: TenantManager agregado")
    else:
        print(f"❌ {modelo}: No se encontró el patrón correcto")

print(f"\n{'='*60}")
print(f"✅ Total de managers agregados: {contador}/{len(modelos_con_escuela)}")
print(f"{'='*60}")

# Guardar archivo modificado
with open('escuelaweb/models.py', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("\n✅ Archivo models.py actualizado correctamente")
print("\nPróximos pasos:")
print("1. Reinicia el servidor: python manage.py runserver")
print("2. Prueba accediendo desde subdominios diferentes")
print("3. Verifica que cada escuela solo vea sus datos")

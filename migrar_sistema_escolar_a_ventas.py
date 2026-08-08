"""
Script de Migración: Sistema Escolar → Sistema de Ventas
=========================================================

Este script migra los datos existentes de un sistema escolar
a un sistema de ventas.

IMPORTANTE: 
- Hacer backup de la base de datos antes de ejecutar
- Ejecutar en ambiente de desarrollo primero
- Revisar los cambios antes de aplicar en producción

Uso:
    python migrar_sistema_escolar_a_ventas.py

"""

import os
import sys
import django
from datetime import datetime
from decimal import Decimal

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.db import transaction
from ventasweb.models import (
    CustomUser, GrupoFamiliar, ClienteCorporativo, 
    Factura, Mensualidad
)


class MigradorSistemaVentas:
    """Clase para migrar sistema escolar a sistema de ventas"""
    
    def __init__(self):
        self.log = []
        self.errores = []
        
    def log_info(self, mensaje):
        """Registra un mensaje informativo"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg = f"[{timestamp}] INFO: {mensaje}"
        print(msg)
        self.log.append(msg)
    
    def log_error(self, mensaje):
        """Registra un error"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg = f"[{timestamp}] ERROR: {mensaje}"
        print(msg)
        self.errores.append(msg)
    
    def confirmar_accion(self, mensaje):
        """Solicita confirmación al usuario"""
        respuesta = input(f"\n{mensaje} (s/n): ").strip().lower()
        return respuesta == 's'
    
    def crear_backup_mensaje(self):
        """Muestra mensaje de backup"""
        print("\n" + "="*70)
        print("IMPORTANTE: CREAR BACKUP DE LA BASE DE DATOS")
        print("="*70)
        print("\nAntes de continuar, asegúrese de:")
        print("1. Hacer backup completo de la base de datos")
        print("2. Probar la migración en ambiente de desarrollo")
        print("3. Tener un plan de rollback")
        print("\n")
        
        if not self.confirmar_accion("¿Ha creado el backup y desea continuar?"):
            print("\nMigración cancelada. Por favor, cree un backup primero.")
            sys.exit(0)
    
    def migrar_roles_usuarios(self):
        """Migra los roles de usuarios de sistema escolar a sistema de ventas"""
        self.log_info("Iniciando migración de roles de usuarios...")
        
        mapeo_roles = {
            'Estudiante': 'Cliente',
            'Profesor': 'Vendedor',
            'Director': 'Gerente',
            'Secretaria': 'Secretaria',
            'Administrador': 'Administrador',
            'Coordinador': 'Supervisor',
            'Bibliotecario': 'Almacenista',
            'Psicologo': 'Asistente',
        }
        
        try:
            usuarios_actualizados = 0
            for rol_antiguo, rol_nuevo in mapeo_roles.items():
                count = CustomUser.objects.filter(rol=rol_antiguo).update(rol=rol_nuevo)
                usuarios_actualizados += count
                if count > 0:
                    self.log_info(f"  - Convertidos {count} usuarios de '{rol_antiguo}' a '{rol_nuevo}'")
            
            self.log_info(f"✓ Total de usuarios actualizados: {usuarios_actualizados}")
            return True
            
        except Exception as e:
            self.log_error(f"Error al migrar roles: {str(e)}")
            return False
    
    def migrar_grupos_familiares_a_corporativos(self):
        """Migra grupos familiares a clientes corporativos"""
        self.log_info("Iniciando migración de grupos familiares a clientes corporativos...")
        
        try:
            grupos = GrupoFamiliar.objects.all()
            total_grupos = grupos.count()
            
            if total_grupos == 0:
                self.log_info("  No hay grupos familiares para migrar")
                return True
            
            migrados = 0
            for grupo in grupos:
                # Crear cliente corporativo equivalente
                cliente_corp = ClienteCorporativo.objects.create(
                    codigo_cliente=grupo.codigo_familia,
                    nombre_empresa=f"Familia {grupo.apellido_familia}",
                    contacto_principal=grupo.responsable_pago,
                    telefono_contacto=grupo.telefono_contacto,
                    email_contacto=grupo.email_contacto,
                    direccion=grupo.direccion,
                    descuento_general=grupo.descuento_general,
                    limite_credito=Decimal('50000.00'),  # Límite por defecto
                    dias_credito=30,
                    activo=grupo.activo,
                    notas=f"Migrado desde grupo familiar. {grupo.notas or ''}",
                    creado_por=grupo.creado_por
                )
                
                # Actualizar referencias de estudiantes a clientes
                # Cambiar grupo_familiar por cliente_corporativo
                estudiantes = CustomUser.objects.filter(
                    rol='Cliente',  # Ya migrado de 'Estudiante'
                    grupo_familiar=grupo
                )
                
                for estudiante in estudiantes:
                    estudiante.cliente_corporativo = cliente_corp
                    estudiante.tipo_cliente = 'corporativo'
                    estudiante.grupo_familiar = None  # Limpiar referencia antigua
                    estudiante.save()
                
                migrados += 1
                self.log_info(f"  - Migrado grupo '{grupo.apellido_familia}' con {estudiantes.count()} clientes")
            
            self.log_info(f"✓ Total de grupos migrados: {migrados}/{total_grupos}")
            return True
            
        except Exception as e:
            self.log_error(f"Error al migrar grupos familiares: {str(e)}")
            return False
    
    def configurar_clientes_individuales(self):
        """Configura clientes individuales (sin grupo/corporativo)"""
        self.log_info("Configurando clientes individuales...")
        
        try:
            clientes_sin_grupo = CustomUser.objects.filter(
                rol='Cliente',
                cliente_corporativo__isnull=True,
                tipo_cliente__isnull=True
            )
            
            count = clientes_sin_grupo.count()
            if count > 0:
                clientes_sin_grupo.update(
                    tipo_cliente='individual',
                    limite_credito=Decimal('10000.00'),  # Límite por defecto
                    dias_credito=30
                )
                self.log_info(f"  - Configurados {count} clientes individuales")
            else:
                self.log_info("  No hay clientes individuales para configurar")
            
            return True
            
        except Exception as e:
            self.log_error(f"Error al configurar clientes individuales: {str(e)}")
            return False
    
    def configurar_vendedores(self):
        """Configura vendedores con comisión por defecto"""
        self.log_info("Configurando vendedores...")
        
        try:
            vendedores = CustomUser.objects.filter(rol='Vendedor')
            count = vendedores.count()
            
            if count > 0:
                # Asignar comisión del 5% por defecto
                vendedores.update(
                    comision_vendedor=Decimal('5.00'),
                    meta_mensual=Decimal('50000.00')
                )
                self.log_info(f"  - Configurados {count} vendedores (comisión 5%, meta $50,000)")
            else:
                self.log_info("  No hay vendedores para configurar")
            
            return True
            
        except Exception as e:
            self.log_error(f"Error al configurar vendedores: {str(e)}")
            return False
    
    def actualizar_facturas(self):
        """Actualiza facturas existentes para sistema de ventas"""
        self.log_info("Actualizando facturas existentes...")
        
        try:
            # Hacer anho_escolar opcional en facturas existentes
            facturas = Factura.objects.all()
            count = facturas.count()
            
            if count > 0:
                self.log_info(f"  - Se mantendrán {count} facturas existentes")
                self.log_info("  - Las facturas antiguas mantienen referencia a año escolar")
                self.log_info("  - Las nuevas facturas no requerirán año escolar")
            else:
                self.log_info("  No hay facturas existentes")
            
            return True
            
        except Exception as e:
            self.log_error(f"Error al actualizar facturas: {str(e)}")
            return False
    
    def limpiar_datos_obsoletos_menu(self):
        """Menú para eliminar datos escolares obsoletos"""
        print("\n" + "="*70)
        print("ELIMINACIÓN DE DATOS ESCOLARES OBSOLETOS")
        print("="*70)
        print("\nLos siguientes modelos ya no son necesarios en el sistema de ventas:")
        print("- Años Escolares")
        print("- Materias")
        print("- Cursos")
        print("- Matrículas")
        print("- Calificaciones y evaluaciones")
        print("- Asistencias")
        print("\nEsta acción NO se puede deshacer.")
        print("Los datos de facturación y pagos se mantienen intactos.")
        
        if self.confirmar_accion("\n¿Desea eliminar los datos escolares obsoletos?"):
            return self.limpiar_datos_obsoletos()
        else:
            self.log_info("Se omitió la eliminación de datos obsoletos")
            return True
    
    def limpiar_datos_obsoletos(self):
        """Elimina modelos escolares obsoletos (OPCIONAL)"""
        self.log_info("Limpiando datos escolares obsoletos...")
        
        try:
            from ventasweb.models import (
                AnhoEscolar, Materia, Curso, Matricula,
                Estudiante, Profesor, Persona, Tutor,
                StudentGroup, Asistencia, AsistenciaPersonal
            )
            
            # Contar registros antes de eliminar
            counts = {
                'AnhoEscolar': AnhoEscolar.objects.count(),
                'Materia': Materia.objects.count(),
                'Curso': Curso.objects.count(),
                'Matricula': Matricula.objects.count(),
                'Estudiante': Estudiante.objects.count(),
                'Profesor': Profesor.objects.count(),
                'Persona': Persona.objects.count(),
                'Tutor': Tutor.objects.count(),
            }
            
            # Eliminar en orden correcto para evitar problemas de FK
            Matricula.objects.all().delete()
            Materia.objects.all().delete()
            Curso.objects.all().delete()
            AnhoEscolar.objects.all().delete()
            Estudiante.objects.all().delete()
            Profesor.objects.all().delete()
            Persona.objects.all().delete()
            Tutor.objects.all().delete()
            
            for modelo, count in counts.items():
                if count > 0:
                    self.log_info(f"  - Eliminados {count} registros de {modelo}")
            
            self.log_info("✓ Datos escolares obsoletos eliminados")
            return True
            
        except Exception as e:
            self.log_error(f"Error al limpiar datos obsoletos: {str(e)}")
            self.log_error("Puede ser necesario eliminar estos modelos manualmente")
            return False
    
    def generar_reporte(self):
        """Genera reporte final de la migración"""
        print("\n" + "="*70)
        print("REPORTE DE MIGRACIÓN")
        print("="*70)
        
        # Estadísticas
        try:
            stats = {
                'Clientes': CustomUser.objects.filter(rol='Cliente').count(),
                'Vendedores': CustomUser.objects.filter(rol='Vendedor').count(),
                'Gerentes': CustomUser.objects.filter(rol='Gerente').count(),
                'Clientes Corporativos': ClienteCorporativo.objects.count(),
                'Facturas': Factura.objects.count(),
            }
            
            print("\nEstadísticas del Sistema:")
            for nombre, valor in stats.items():
                print(f"  - {nombre}: {valor}")
            
        except Exception as e:
            print(f"  Error al generar estadísticas: {str(e)}")
        
        # Logs
        print(f"\nTotal de operaciones exitosas: {len(self.log)}")
        if self.errores:
            print(f"Total de errores: {len(self.errores)}")
            print("\nErrores encontrados:")
            for error in self.errores:
                print(f"  {error}")
        else:
            print("\n✓ Migración completada sin errores")
        
        # Guardar log en archivo
        try:
            with open('migracion_ventas.log', 'w', encoding='utf-8') as f:
                f.write("LOG DE MIGRACIÓN - SISTEMA ESCOLAR A VENTAS\n")
                f.write("=" * 70 + "\n\n")
                for linea in self.log:
                    f.write(linea + "\n")
                if self.errores:
                    f.write("\n\nERRORES:\n")
                    for error in self.errores:
                        f.write(error + "\n")
            
            print("\n✓ Log guardado en: migracion_ventas.log")
        except Exception as e:
            print(f"\nError al guardar log: {str(e)}")
    
    def ejecutar_migracion(self):
        """Ejecuta el proceso completo de migración"""
        print("\n" + "="*70)
        print("MIGRACIÓN: SISTEMA ESCOLAR → SISTEMA DE VENTAS")
        print("="*70)
        
        # Paso 1: Verificar backup
        self.crear_backup_mensaje()
        
        # Confirmación final
        if not self.confirmar_accion("\n¿Desea iniciar la migración ahora?"):
            print("\nMigración cancelada por el usuario.")
            sys.exit(0)
        
        print("\nIniciando migración...")
        
        # Ejecutar migración en transacción
        try:
            with transaction.atomic():
                # Paso 2: Migrar roles
                if not self.migrar_roles_usuarios():
                    raise Exception("Error al migrar roles")
                
                # Paso 3: Migrar grupos familiares
                if not self.migrar_grupos_familiares_a_corporativos():
                    raise Exception("Error al migrar grupos familiares")
                
                # Paso 4: Configurar clientes individuales
                if not self.configurar_clientes_individuales():
                    raise Exception("Error al configurar clientes individuales")
                
                # Paso 5: Configurar vendedores
                if not self.configurar_vendedores():
                    raise Exception("Error al configurar vendedores")
                
                # Paso 6: Actualizar facturas
                if not self.actualizar_facturas():
                    raise Exception("Error al actualizar facturas")
                
                self.log_info("\n✓ Migración principal completada exitosamente")
            
            # Paso 7: Limpiar datos obsoletos (fuera de transacción, opcional)
            self.limpiar_datos_obsoletos_menu()
            
        except Exception as e:
            self.log_error(f"Error durante la migración: {str(e)}")
            print("\n❌ La migración falló y se revirtieron los cambios.")
            self.generar_reporte()
            sys.exit(1)
        
        # Generar reporte
        self.generar_reporte()
        
        print("\n" + "="*70)
        print("PRÓXIMOS PASOS")
        print("="*70)
        print("\n1. Ejecutar migraciones de Django:")
        print("   python manage.py makemigrations")
        print("   python manage.py migrate")
        print("\n2. Actualizar el admin de Django")
        print("\n3. Actualizar vistas y templates")
        print("\n4. Probar el sistema completo")
        print("\n5. Actualizar documentación")


def main():
    """Función principal"""
    migrador = MigradorSistemaVentas()
    migrador.ejecutar_migracion()


if __name__ == '__main__':
    main()

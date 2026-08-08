# Plan de Transformación: Sistema Escolar → Sistema de Ventas

## Resumen
Transformar el sistema educativo multi-tenant en un sistema completo de ventas manteniendo:
- ✅ Sistema de facturación (Factura, DetalleFactura, PagoFactura)
- ✅ Reportes de ventas y pagos
- ✅ Multi-tenancy con django-tenants
- ✅ Sistema de inventario (Artículos, Categorías, Movimientos)
- ✅ Sistema de usuarios y autenticación

## Cambios en Modelos

### 1. CustomUser - Actualización de Roles
**Roles Actuales (Escolar):**
- Estudiante → **Cliente**
- Profesor → **Vendedor**
- Director → **Gerente**
- Secretaria → **Secretaria** (mantener)
- Administrador → **Administrador** (mantener)
- Coordinador → **Supervisor**
- Bibliotecario → **Almacenista**
- Psicólogo → **Asistente**

**Campos a Eliminar:**
- grupo_familiar → se transforma en "cliente_corporativo"
- grado, seccion (estudiantes)
- especialidad (profesores)
- porcentaje_mora_individual, dia_vencimiento_individual, descuento_individual → mover a configuración de cliente

**Campos a Agregar:**
- tipo_cliente: choices=['individual', 'corporativo']
- comision_vendedor: DecimalField (para vendedores)
- meta_mensual: DecimalField (para vendedores)
- zona_venta: CharField (para vendedores)
- limite_credito: DecimalField (para clientes)
- dias_credito: IntegerField (para clientes)

### 2. Modelos a ELIMINAR (Escolares)
- ❌ AnhoEscolar
- ❌ Materia
- ❌ Curso
- ❌ Matricula
- ❌ Estudiante (modelo redundante)
- ❌ Profesor (modelo redundante)
- ❌ Persona (modelo redundante con CustomUser)
- ❌ Tutor
- ❌ StudentGroup
- ❌ Asistencia
- ❌ AsistenciaPersonal
- ❌ Todos los modelos relacionados con calificaciones/notas

### 3. Modelos a MANTENER y ADAPTAR

#### GrupoFamiliar → ClienteCorporativo
- Renombrar modelo
- codigo_familia → codigo_cliente
- apellido_familia → nombre_empresa
- responsable_pago → contacto_principal
- Mantener: descuento_general, limite_credito, dias_credito

#### Mensualidad → CuentaPorCobrar
- Transformar para pagos recurrentes o créditos
- estudiante → cliente
- anho_escolar → eliminar (usar fecha)
- mes/anio → fecha_vencimiento
- Agregar: tipo_cuenta ['credito', 'recurrente', 'servicio']

#### Mantener sin cambios:
- ✅ Factura
- ✅ DetalleFactura
- ✅ PagoFactura
- ✅ Articulo
- ✅ CategoriaArticulo
- ✅ MovimientoInventario
- ✅ ConceptoPago
- ✅ CodigoAnulacion
- ✅ TarifaEstudiante → TarifaCliente (renombrar)

### 4. Nuevos Modelos a CREAR

#### Cotizacion
- cliente: FK CustomUser
- vendedor: FK CustomUser
- fecha_cotizacion: DateField
- fecha_vencimiento: DateField
- estado: choices=['pendiente', 'aprobada', 'rechazada', 'convertida']
- subtotal, itbis, total
- notas
- valida_hasta

#### DetalleCotizacion
- cotizacion: FK Cotizacion
- articulo: FK Articulo
- cantidad, precio_unitario, descuento, subtotal

#### ComisionVendedor
- vendedor: FK CustomUser
- factura: FK Factura
- monto_venta: DecimalField
- porcentaje_comision: DecimalField
- monto_comision: DecimalField
- estado: choices=['pendiente', 'pagada']
- fecha_calculo, fecha_pago

#### MetaVendedor
- vendedor: FK CustomUser
- mes, anio
- meta_monto: DecimalField
- monto_alcanzado: DecimalField
- porcentaje_cumplimiento: calculated

## Cambios en Settings

### Actualizar TENANT_MODEL
```python
TENANT_MODEL = "escuelaweb.Empresa"  # Cambiar nombre
TENANT_DOMAIN_MODEL = "escuelaweb.Domain"  # mantener
```

### Actualizar Roles en Middleware
Actualizar role-based session en middleware para nuevos roles

## Cambios en Vistas y Forms

### Vistas a Eliminar
- views_evaluaciones.py
- views_listas_cotejo.py
- utils_notas.py
- Todas las vistas relacionadas con calificaciones

### Vistas a Crear
- views_cotizaciones.py
- views_comisiones.py
- views_clientes.py (reemplazar views de estudiantes)
- views_vendedores.py (reemplazar views de profesores)
- views_dashboard_ventas.py

### Vistas a Adaptar
- views_pagos_estudiante.py → views_pagos_cliente.py
- views_familias.py → views_clientes_corporativos.py
- views.py (actualizar contexto y permisos)

## Cambios en Templates

### Templates a Eliminar
- Todos los relacionados con calificaciones
- Asistencia escolar
- Año escolar
- Materias y cursos

### Templates a Crear
- cotizaciones/
- comisiones/
- dashboard_ventas/
- clientes/ (reemplazar estudiantes/)
- vendedores/ (reemplazar profesores/)

### Templates a Adaptar
- base.html (actualizar menú)
- home.html (dashboard de ventas)
- facturas/ (actualizar referencias)

## Migraciones

### Estrategia de Migración
1. Crear script de backup de datos importantes
2. Crear nuevos modelos (Cotizacion, ComisionVendedor, etc.)
3. Migrar datos de CustomUser (actualizar roles)
4. Transformar GrupoFamiliar → ClienteCorporativo
5. Transformar Mensualidad → CuentaPorCobrar (opcional)
6. Eliminar modelos obsoletos
7. Actualizar referencias en código

### Script de Migración de Datos
```python
# migrar_a_sistema_ventas.py
# - Backup de BD
# - Actualizar roles de usuarios
# - Migrar grupos familiares
# - Eliminar datos escolares obsoletos
```

## Orden de Implementación

1. ✅ Crear plan detallado (este documento)
2. 🔄 Actualizar models.py
3. 🔄 Crear nuevos modelos (Cotizacion, ComisionVendedor, etc.)
4. 🔄 Actualizar admin.py
5. 🔄 Crear migraciones
6. 🔄 Actualizar forms.py
7. 🔄 Actualizar/crear vistas
8. 🔄 Actualizar/crear templates
9. 🔄 Actualizar urls.py
10. 🔄 Actualizar documentación
11. 🔄 Crear script de migración de datos
12. 🔄 Testing

## Funcionalidades del Sistema de Ventas

### Módulos Principales
1. **Gestión de Clientes**
   - Registro de clientes individuales y corporativos
   - Límites de crédito
   - Historial de compras
   - Cuentas por cobrar

2. **Gestión de Vendedores**
   - Registro de vendedores
   - Asignación de zonas
   - Metas mensuales
   - Comisiones

3. **Cotizaciones**
   - Crear cotizaciones
   - Aprobar/rechazar
   - Convertir a factura
   - Seguimiento

4. **Facturación** (YA EXISTE)
   - Mantener sistema actual
   - Agregar referencias a vendedor
   - Calcular comisiones automáticamente

5. **Inventario** (YA EXISTE)
   - Mantener sistema actual
   - Mejorar reportes

6. **Reportes**
   - Ventas por período
   - Comisiones de vendedores
   - Cumplimiento de metas
   - Cuentas por cobrar
   - Inventario y rotación
   - Top clientes

7. **POS** (YA EXISTE)
   - Mantener sistema actual
   - Integrar con comisiones

## Configuración Multi-Tenant

El sistema mantendrá la arquitectura multi-tenant donde cada empresa tendrá:
- Su propia BD schema
- Sus propios clientes
- Sus propios vendedores
- Su propio inventario
- Sus propias facturas

## Notas Importantes

- ⚠️ Hacer backup completo antes de empezar
- ⚠️ Probar en ambiente de desarrollo primero
- ⚠️ Documentar todos los cambios
- ⚠️ Crear migraciones reversibles cuando sea posible
- ⚠️ Mantener compatibilidad con sistema de suscripciones (Stripe)
- ⚠️ Mantener sistema de seguridad y autenticación actual

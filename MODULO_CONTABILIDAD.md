# Módulo de Contabilidad - Plan de Cuentas

## 📊 Descripción

El módulo de contabilidad proporciona un sistema completo de gestión del Plan de Cuentas Contable para instituciones educativas. Este es el primer módulo de una serie que implementará un sistema contable completo.

## ✨ Características Implementadas

### Plan de Cuentas (Catálogo de Cuentas)
- ✅ **Gestión completa de cuentas contables**
  - Crear, editar, ver y eliminar cuentas
  - Estructura jerárquica con cuenta padre/subcuentas
  - Códigos de cuenta personalizables
  - 6 tipos de cuentas: Activo, Pasivo, Capital, Ingreso, Gasto, Costo

- ✅ **Clasificación contable**
  - Naturaleza: Deudora o Acreedora (se asigna automáticamente)
  - Niveles jerárquicos automáticos basados en el código
  - Cuentas de detalle (aceptan movimientos) vs. Agrupadores (solo organizan)

- ✅ **Control y seguridad**
  - Auditoría completa: usuario creador y modificador
  - Validación de eliminación (no se permite si tiene movimientos o subcuentas)
  - Control de edición (campos limitados si tiene movimientos)
  - Activación/desactivación de cuentas

- ✅ **Configuraciones especiales**
  - Requiere centro de costo
  - Requiere tercero (cliente/proveedor)
  - Saldo inicial personalizable

- ✅ **Interfaz moderna**
  - Diseño responsivo con gradientes y animaciones
  - Búsqueda y filtros avanzados
  - Estadísticas en tiempo real
  - Cards visuales por tipo de cuenta
  - Estructura de árbol para visualizar jerarquías

## 🗂️ Estructura del Plan de Cuentas Cargado

Se incluye un plan de cuentas básico de **82 cuentas** organizadas así:

### 1. ACTIVOS
- **1.1 Activo Corriente**
  - Efectivo y equivalentes (Caja General, Caja Chica)
  - Bancos (Cuenta Corriente, Cuenta Ahorros)
  - Cuentas por Cobrar (Matrículas, Mensualidades, Otros)
  - Inventarios (Útiles Escolares, Libros)

- **1.2 Activo No Corriente**
  - Propiedad, Planta y Equipo (Edificios, Mobiliario, Equipos, Vehículos)

### 2. PASIVOS
- **2.1 Pasivo Corriente**
  - Cuentas por Pagar (Proveedores, Servicios)
  - Obligaciones Laborales (Sueldos, Prestaciones)
  - Retenciones y Aportes

- **2.2 Pasivo No Corriente**
  - Préstamos a Largo Plazo

### 3. PATRIMONIO
- Capital Institucional
- Resultados (Ejercicio Actual, Acumulados)

### 4. INGRESOS
- **4.1 Ingresos Operacionales**
  - Matrículas (Inicial, Básica, Media)
  - Mensualidades (Inicial, Básica, Media)
  - Otros (Transporte, Cafetería, Uniformes, Útiles)

- **4.2 Ingresos No Operacionales**
  - Intereses Ganados
  - Donaciones

### 5. GASTOS
- **5.1 Gastos Operacionales**
  - Personal (Sueldos Docentes, Administrativos, Prestaciones)
  - Servicios Públicos (Electricidad, Agua, Teléfono)
  - Arrendamientos
  - Mantenimiento y Reparaciones
  - Útiles y Suministros

- **5.2 Gastos No Operacionales**
  - Gastos Financieros
  - Gastos Bancarios

## 🚀 Acceso y Uso

### URLs Disponibles

```
/contabilidad/plan-cuentas/              - Listar todas las cuentas
/contabilidad/plan-cuentas/crear/        - Crear nueva cuenta
/contabilidad/plan-cuentas/<id>/         - Ver detalles de cuenta
/contabilidad/plan-cuentas/<id>/editar/  - Editar cuenta
/contabilidad/plan-cuentas/<id>/eliminar/ - Eliminar cuenta
```

### APIs (JSON)

```
/contabilidad/api/plan-cuentas/<id>/subcuentas/  - Obtener subcuentas (AJAX)
/contabilidad/api/plan-cuentas/estructura/       - Estructura completa en árbol
```

### Permisos

- **Ver cuentas**: Administrador, Director, Secretaria
- **Crear/Editar**: Administrador, Director
- **Eliminar**: Solo Administrador

## 📝 Cómo Crear una Cuenta

1. Acceder a `/contabilidad/plan-cuentas/`
2. Click en "Nueva Cuenta"
3. Completar:
   - **Código**: Formato jerárquico (ej: 1.1.01.001)
   - **Nombre**: Descriptivo
   - **Tipo**: Activo, Pasivo, Capital, Ingreso, Gasto o Costo
   - **Naturaleza**: Se asigna automáticamente
   - **Cuenta Padre** (opcional): Para crear subcuentas
   - **Es detalle**: Marcar si acepta movimientos directos
   - **Saldo Inicial**: Solo para cuentas de detalle

4. Guardar

## 🔧 Comandos Útiles

### Cargar Plan de Cuentas Básico
```powershell
Get-Content scripts/cargar_plan_cuentas.py | python manage.py shell
```

### Verificar Migración
```powershell
python manage.py showmigrations escuelaweb
```

### Crear Superusuario (si no existe)
```powershell
python manage.py createsuperuser
```

## 📊 Modelo de Datos

### Campos Principales del Modelo PlanCuentas

```python
- codigo: CharField(20) - Código único jerárquico
- nombre: CharField(200) - Nombre de la cuenta
- descripcion: TextField - Descripción detallada (opcional)
- tipo_cuenta: CharField - ACTIVO, PASIVO, CAPITAL, INGRESO, GASTO, COSTO
- naturaleza: CharField - DEUDORA, ACREEDORA
- nivel: IntegerField - Nivel jerárquico (calculado automáticamente)
- cuenta_padre: ForeignKey(self) - Relación jerárquica
- es_detalle: BooleanField - Si acepta movimientos
- activo: BooleanField - Estado activo/inactivo
- saldo_inicial: DecimalField - Saldo al inicio del período
- saldo_actual: DecimalField - Saldo actual
- requiere_centro_costo: BooleanField
- requiere_tercero: BooleanField
- fecha_creacion: DateTimeField
- fecha_modificacion: DateTimeField
- creado_por: ForeignKey(CustomUser)
- modificado_por: ForeignKey(CustomUser)
```

## 🎨 Características de la Interfaz

### Lista de Cuentas
- **Búsqueda** por código, nombre o descripción
- **Filtros** por tipo, estado y clasificación
- **Estadísticas** visuales con cards animados
- **Distribución** por tipo de cuenta
- **Vista de tabla** moderna con hover effects

### Formulario de Cuenta
- Validación en tiempo real
- Asignación automática de naturaleza según tipo
- Ayuda contextual con tooltips
- Validación de código jerárquico
- Inhabilitación de saldo si es cuenta agrupadora

### Vista de Detalle
- Información completa y organizada
- Visualización de la ruta jerárquica
- Lista de subcuentas con enlaces directos
- Saldo actual vs. saldo calculado
- Alertas sobre restricciones de eliminación

## 📋 Próximos Módulos Contables

Este es el primer módulo de contabilidad. Los próximos módulos a implementar son:

1. **Asientos Contables** (Journal Entries) - PRÓXIMO
2. **Libro Mayor** (General Ledger)
3. **Balance de Comprobación** (Trial Balance)
4. **Estados Financieros** (Financial Statements)
5. **Centros de Costo** (Cost Centers)
6. **Conciliación Bancaria** (Bank Reconciliation)
7. **Presupuestos** (Budgets)
8. **Reportes Contables** (Accounting Reports)

## 🐛 Solución de Problemas

### Error al crear cuenta
- Verificar que el código no esté duplicado
- Confirmar formato correcto del código (solo números y puntos)
- Si tiene cuenta padre, el código debe comenzar con el código del padre

### No puedo eliminar una cuenta
- Verificar que no tenga subcuentas
- Confirmar que no tenga movimientos contables
- Considerar desactivarla en lugar de eliminarla

### La naturaleza no se asigna correctamente
- La naturaleza se asigna automáticamente al guardar
- Activo, Gasto, Costo = Deudora
- Pasivo, Capital, Ingreso = Acreedora

## 📞 Soporte

Para soporte o preguntas sobre el módulo de contabilidad:
- Revisar la documentación en `/contabilidad/plan-cuentas/`
- Consultar los comentarios en el código
- Verificar la consola del navegador para errores JavaScript
- Revisar los logs de Django para errores del servidor

---

**Versión**: 1.0.0  
**Fecha**: $(Get-Date -Format "dd/MM/yyyy")  
**Autor**: Sistema de Gestión Escolar  
**Módulo**: Contabilidad - Plan de Cuentas

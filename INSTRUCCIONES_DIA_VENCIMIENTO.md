# Sistema de Día de Vencimiento y Mora

## Descripción General

El sistema ahora incluye la funcionalidad de configurar un **día de vencimiento** para cada grupo familiar. Este día determina cuándo vencen las mensualidades y cuándo se debe aplicar la mora automáticamente.

## Características Implementadas

### 1. Campo Día de Vencimiento en Grupo Familiar

- **Campo**: `dia_vencimiento` (valor por defecto: 10)
- **Rango**: 1-31 (día del mes)
- **Ubicación**: GrupoFamiliar model

### 2. Configuración Manual

Puedes configurar el día de vencimiento al:
- **Crear un nuevo grupo familiar**: En el formulario de creación, especifica el día del mes (1-31)
- **Editar un grupo existente**: Modifica el día de vencimiento en cualquier momento

### 3. Cálculo Automático de Fecha de Vencimiento

Cuando creas una factura:

1. **Si NO especificas fecha de vencimiento manualmente**:
   - El sistema automáticamente calcula la fecha basada en el `dia_vencimiento` del grupo familiar
   - **Regla**: 
     - Si hoy es ANTES del día de vencimiento → usa el mes actual
     - Si hoy es DESPUÉS del día de vencimiento → usa el próximo mes
   
2. **Si especificas una fecha de vencimiento**:
   - El sistema respeta la fecha que ingresas manualmente

### 4. Aplicación Automática de Mora

El sistema aplica mora automáticamente si:
- La factura tiene una fecha de vencimiento configurada
- La fecha actual es posterior a la fecha de vencimiento
- El grupo familiar o estudiante tiene un porcentaje de mora configurado (mayor a 0%)

## Ejemplos de Uso

### Ejemplo 1: Vencimiento Día 10

**Configuración:**
- Grupo Familiar: "Pérez"
- Día de Vencimiento: 10
- Porcentaje Mora: 7%

**Escenario A - Factura creada el 5 de marzo:**
- Fecha de vencimiento automática: **10 de marzo** (mismo mes)
- Si se paga el 12 de marzo → Mora del 7% aplicada automáticamente

**Escenario B - Factura creada el 15 de marzo:**
- Fecha de vencimiento automática: **10 de abril** (próximo mes)
- Si se paga en abril después del día 10 → Mora del 7% aplicada

### Ejemplo 2: Vencimiento Día 31

**Configuración:**
- Grupo Familiar: "González"
- Día de Vencimiento: 31
- Porcentaje Mora: 5%

**Escenario - Factura creada en febrero:**
- Fecha de vencimiento: **28/29 de febrero** (último día del mes, ya que febrero no tiene 31 días)
- Sistema ajusta automáticamente para meses con menos de 31 días

## Visualización en el Sistema

### En Detalle de Grupo Familiar
Verás una nueva sección que muestra:
```
Día de Vencimiento: Día 10
Las mensualidades vencen el día 10 de cada mes
```

### En Factura
Si una factura está vencida, aparecerá:
- ⚠️ Alerta amarilla indicando "Factura Vencida"
- Detalle de mora aplicada con porcentaje y monto
- Fila de mora destacada en amarillo en la tabla de detalles

### En Recibo POS
- Marca ⚠️ MORA en los conceptos de mora

## Recomendaciones

1. **Día de Vencimiento Común**: La mayoría de escuelas usan día 5, 10 o 15
2. **Porcentaje de Mora Estándar**: Típicamente entre 5% y 10%
3. **Actualización por Lotes**: Puedes actualizar el día de vencimiento de grupos familiares en cualquier momento

## Base de Datos

### Migración
- **Archivo**: `0033_grupofamiliar_dia_vencimiento.py`
- **Estado**: ✅ Aplicada exitosamente
- **Cambios**: Agrega campo `dia_vencimiento` con valor por defecto 10

### Actualización de Grupos Existentes
Todos los grupos familiares existentes tienen ahora:
- `dia_vencimiento = 10` (valor por defecto)
- Puedes modificarlos individualmente según necesites

## Notas Técnicas

### Lógica de Cálculo
```python
if hoy.day > dia_vencimiento:
    # Próximo mes
    fecha_base = hoy + relativedelta(months=1)
else:
    # Este mes
    fecha_base = hoy

# Ajustar día, manejando meses con menos días
fecha_vencimiento = fecha_base.replace(day=dia_vencimiento)
```

### Manejo de Casos Especiales
- **Día 31 en febrero**: Sistema usa el último día del mes (28 o 29)
- **Sin grupo familiar**: Si el estudiante no tiene grupo familiar, debes especificar la fecha manualmente
- **Mora individual**: Los estudiantes pueden tener mora individual que sobrescribe la del grupo

## Próximos Pasos

Para usar esta funcionalidad:

1. **Edita los grupos familiares** existentes y configura el día de vencimiento apropiado
2. **Crea nuevas facturas** sin especificar fecha de vencimiento
3. **Verifica** que la fecha se calcula automáticamente
4. **Revisa** que la mora se aplica correctamente cuando la fecha vence

---

**Última actualización**: 3 de marzo de 2026

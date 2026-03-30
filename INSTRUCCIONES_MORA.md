# Sistema de Mora por Pagos Atrasados

## ¿Qué es la Mora?

La mora es un recargo automático que se aplica a las facturas cuando el pago se realiza después de la fecha de vencimiento. Este recargo se calcula como un porcentaje del subtotal de la factura.

## Configuración de Mora

### Para Grupos Familiares
1. Accede a **Familias** → **Grupos Familiares**
2. Selecciona o crea un grupo familiar
3. En el formulario, configura el campo **"Porcentaje de Mora (%)"**
   - Ejemplo: 5 para aplicar 5% de recargo
4. Guarda los cambios

### Para Estudiantes Individuales
1. Accede a **Usuarios** → Editar estudiante
2. Configura el campo **"Porcentaje de Mora Individual (%)"**
   - Solo se aplica si el estudiante NO está en un grupo familiar
   - Si está en un grupo, se usa el porcentaje del grupo

## ¿Cómo se Aplica la Mora?

### Aplicación Automática
La mora se aplica automáticamente cuando:
1. Se crea una factura con una **fecha de vencimiento**
2. La fecha de vencimiento ya ha pasado (está vencida)
3. El estudiante o familia tiene un porcentaje de mora configurado (> 0%)

### Cálculo
```
Monto de Mora = Subtotal de Factura × Porcentaje de Mora / 100
```

**Ejemplo:**
- Subtotal de factura: RD$ 5,000
- Porcentaje de mora configurado: 10%
- **Mora aplicada: RD$ 500**
- **Total con mora: RD$ 5,500**

## Visualización de la Mora

### En el Detalle de Factura
- **Alerta amarilla** si la factura está vencida
- **Badge de advertencia** mostrando el porcentaje de mora configurado
- **Fila resaltada** en amarillo para el detalle de mora
- **Icono de advertencia** (⚠️) junto al concepto de mora

### En el Recibo POS
- El detalle de mora aparece con el indicador **"⚠️ MORA"**
- Se incluye en el subtotal y total de la factura

### En la Edición de Factura
- Cuando se edita una facturaexistente, todos los detalles se cargan
- Si había mora aplicada, aparecerá en la lista de conceptos
- La mora se recalcula si se cambia la fecha de vencimiento

## Flujo Completo

### Escenario 1: Pago a Tiempo
```
1. Factura creada: 01/03/2026
2. Fecha vencimiento: 15/03/2026
3. Usuario crea factura el 10/03/2026
   → No hay mora (no está vencida)
```

### Escenario 2: Pago Atrasado
```
1. Factura creada: 01/03/2026  
2. Fecha vencimiento: 15/03/2026
3. Usuario crea factura el 20/03/2026
   → Mora aplicada automáticamente
   → Se agrega como línea extra en la factura
```

### Escenario 3: Edición de Factura
```
1. Factura original con mora aplicada
2. Usuario edita la factura (requiere código de seguridad)
3. Se eliminan todos los detalles anteriores
4. Se recargan los conceptos originales
5. La mora se recalcula según la nueva fecha de vencimiento
```

## Verificación

### ¿Cómo verificar que la mora funciona?

1. **Configurar mora en una familia:**
   - Ve a Familias → Editar grupo
   - Pon 10% en "Porcentaje de Mora"
   - Guarda

2. **Crear factura vencida:**
   - Ve a Punto de Venta
   - Selecciona un estudiante de esa familia
   - Agrega conceptos (ej: mensualidad)
   - Pon una fecha de vencimiento en el **pasado** (ej: 01/03/2026)
   - Guarda la factura

3. **Verificar:**
   - La factura debe tener un detalle extra: **"Mora por Pago Atrasado"**
   - El monto debe ser el 10% del subtotal
   - En la vista de detalle, debe aparecer una alerta amarilla

## Conceptos Técnicos

### Modelos Actualizados
- `GrupoFamiliar.porcentaje_mora` - Mora para familias
- `CustomUser.porcentaje_mora_individual` - Mora para estudiantes individuales
- `Factura.esta_vencida()` - Método para verificar si está vencida  
- `Factura.calcular_mora()` - Método para calcular el monto de mora
- `CustomUser.get_porcentaje_mora()` - Obtiene el porcentaje aplicable

### Concepto de Mora
La mora se guarda como un `ConceptoPago` con:
- **Tipo:** otro
- **Nombre:** "Mora por Pago Atrasado"
- Se crea automáticamente si no existe

### Detalle de Mora
Se guarda como un `DetalleFactura` con:
- **Concepto:** Mora por Pago Atrasado
- **Descripción:** "Mora (X% sobre facturas vencidas)"
- **Cantidad:** 1
- **Precio unitario:** Monto calculado de la mora

## Preguntas Frecuentes

**P: ¿La mora se aplica sobre el total o el subtotal?**
R: La mora se calcula sobre el **subtotal** (antes de descuentos e impuestos).

**P: ¿Puedo cambiar el porcentaje de mora después?**
R: Sí, pero solo afectará a nuevas facturas. Las facturas existentes mantienen la mora que tenían.

**P: ¿Qué pasa si elimino la mora manualmente de una factura?**
R: Puedes hacerlo editando la factura y eliminando el concepto de mora. No se volverá a aplicar automáticamente a menos que cambies la fecha de vencimiento.

**P: ¿Se puede tener diferentes porcentajes de mora para diferentes estudiantes de la misma familia?**
R: No. Si un estudiante está en un grupo familiar, se usa el porcentaje del grupo. Para tener porcentajes individuales, el estudiante no debe estar en ningún grupo familiar.

## Soporte Técnico

Si tienes problemas con el sistema de mora:
1. Verifica que el porcentaje esté configurado (> 0%)
2. Verifica que la fecha de vencimiento esté en el pasado
3. Revisa los logs del sistema para mensajes de debug sobre mora
4. Verifica que exista el concepto "Mora por Pago Atrasado" en el sistema

---
**Última actualización:** Marzo 2026

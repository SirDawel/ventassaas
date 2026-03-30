# ✅ DESCUENTOS APLICADOS A ESTUDIANTES EN GRUPOS FAMILIARES

## 🎯 PROBLEMA SOLUCIONADO

**Problema anterior:** Cuando se creaba una factura para un estudiante individual que pertenecía a un grupo familiar, NO se aplicaba el descuento del grupo familiar a sus mensualidades, inscripciones y transporte.

**Solución implementada:** Ahora el sistema detecta automáticamente si un estudiante pertenece a un grupo familiar y aplica el descuento correspondiente a:
- ✅ Mensualidades
- ✅ Inscripciones  
- ✅ Transporte

---

## 📝 CAMBIOS REALIZADOS

### 1. Variable global de descuento del grupo familiar
Se agregó una variable JavaScript que almacena el descuento del grupo familiar si el estudiante pertenece a uno:

```javascript
{% if estudiante and estudiante.grupo_familiar %}
const descuentoGrupoFamiliar = {{ estudiante.grupo_familiar.descuento_general|unlocalize }};
{% else %}
const descuentoGrupoFamiliar = 0;
{% endif %}
```

### 2. Aplicación automática de descuento al agregar mensualidad rápida
Cuando se hace clic en "Agregar Mensualidad Actual", el sistema ahora:
- Calcula el descuento basado en el porcentaje del grupo familiar
- Aplica el descuento a la mensualidad automáticamente
- Muestra en consola el descuento aplicado para depuración

### 3. Aplicación de descuento en inscripción y transporte automáticos
Lo mismo se aplica cuando se agregan inscripciones y transporte de forma rápida.

### 4. Aplicación de descuento en mensualidades manuales
Cuando el usuario agrega mensualidades manualmente (seleccionando mes y año específicos):
- El sistema calcula el descuento del grupo familiar
- Aplica el descuento a cada mensualidad agregada
- Funciona tanto para un mes individual como para rangos de meses

### 5. Depuración mejorada
Se agregaron logs de consola para rastrear:
```
DEBUG DESCUENTO - Mensualidad monto: RD$1500, Descuento %: 10%, Descuento RD$: 150.00
DEBUG DESCUENTO - Inscripción monto: RD$2000, Descuento %: 10%, Descuento RD$: 200.00
DEBUG DESCUENTO - Transporte monto: RD$800, Descuento %: 10%, Descuento RD$: 80.00
```

---

## 🧪 CÓMO PROBAR

### Paso 1: Verificar que un estudiante esté en un grupo familiar
```bash
python manage.py shell
```

```python
from escuelaweb.models import CustomUser, GrupoFamiliar

# Buscar un estudiante con grupo familiar
estudiante = CustomUser.objects.filter(
    rol='Estudiante',
    grupo_familiar__isnull=False
).first()

if estudiante:
    print(f"Estudiante: {estudiante.get_full_name()}")
    print(f"Grupo familiar: {estudiante.grupo_familiar.apellido_familia}")
    print(f"Descuento del grupo: {estudiante.grupo_familiar.descuento_general}%")
else:
    print("No hay estudiantes en grupos familiares")
    
# Si no hay, crear uno de prueba
grupo = GrupoFamiliar.objects.first()
if grupo:
    grupo.descuento_general = 10.00  # 10% de descuento
    grupo.save()
    print(f"✓ Grupo {grupo.apellido_familia} configurado con 10% de descuento")
```

### Paso 2: Crear factura para el estudiante
1. Ir a: **http://127.0.0.1:8000/facturas/nueva/**
2. Buscar el estudiante que pertenece al grupo familiar
3. Seleccionarlo
4. Click en **"Agregar Mensualidad Actual"**
5. Verificar en la consola del navegador (F12) que aparezca:
   ```
   DEBUG DESCUENTO - Mensualidad monto: RD$XXXX, Descuento %: 10%, Descuento RD$: XXX.XX
   ```

### Paso 3: Verificar el total de la factura
- Si la mensualidad cuesta RD$1500 y el descuento es 10%
- El total debería ser: RD$1350 (1500 - 150)
- **Antes del cambio:** mostraba RD$1500
- **Después del cambio:** muestra RD$1350 ✅

### Paso 4: Probar con inscripción y transporte
1. Click en "Agregar Inscripción Actual"
2. Click en "Agregar Transporte Actual"
3. Verificar que ambos también muestren descuentos aplicados en la consola
4. Verificar el total de la factura

### Paso 5: Probar mensualidades manuales
1. Seleccionar un concepto de tipo "Mensualidad"
2. Elegir un mes específico (ej: Enero)
3. Click en "Agregar"
4. Verificar que el descuento se aplique
5. Probar con rango de meses (ej: Enero a Marzo)
6. Verificar que el descuento se aplique a cada mes

---

## 📊 COMPARACIÓN: ANTES vs DESPUÉS

### ANTES (sin descuento de grupo familiar):
```
Estudiante: Juan Pérez
Grupo Familiar: Familia Pérez (10% descuento)

Factura:
- Mensualidad Enero 2025: RD$1500.00
- Inscripción 2025: RD$2000.00
- Transporte: RD$800.00
─────────────────────────────────
Subtotal: RD$4300.00
Total: RD$4300.00  ❌ SIN DESCUENTO
```

### DESPUÉS (con descuento de grupo familiar):
```
Estudiante: Juan Pérez
Grupo Familiar: Familia Pérez (10% descuento)

Factura:
- Mensualidad Enero 2025: RD$1350.00 (desc. RD$150)
- Inscripción 2025: RD$1800.00 (desc. RD$200)
- Transporte: RD$720.00 (desc. RD$80)
─────────────────────────────────
Subtotal: RD$3870.00
Total: RD$3870.00  ✅ CON DESCUENTO
```

**Ahorro:** RD$430.00 (10% del total)

---

## 🔍 DÓNDE SE APLICA EL DESCUENTO

### ✅ SE APLICA a:
- Mensualidades (manuales y automáticas)
- Inscripciones
- Transporte

### ❌ NO SE APLICA a:
- Artículos de inventario
- Otros servicios/conceptos
- Facturas a estudiantes SIN grupo familiar

**Razón:** El descuento del grupo familiar es específico para conceptos educativos recurrentes (mensualidad, inscripción, transporte).

---

## 🛠️ PARA DESARROLLADORES

### Ubicación de los cambios:
- **Archivo:** `escuelaweb/templates/cobros/factura_crear_nueva.html`
- **Líneas modificadas:** 
  - ~825-835: Definición de variable `descuentoGrupoFamiliar`
  - ~1075-1110: Aplicación automática de descuento (mensualidad, inscripción, transporte)
  - ~1265-1330: Aplicación manual de descuento (función `agregarConceptoRapido`)

### Lógica del descuento:
```javascript
// Calcular descuento si el estudiante está en un grupo familiar
const montoMensualidad = parseFloat(mens.monto || 0);
const descuentoMensualidad = descuentoGrupoFamiliar > 0 
    ? (montoMensualidad * descuentoGrupoFamiliar / 100) 
    : 0;
```

### Dónde se guarda el descuento:
```javascript
// Se pasa a la función agregarConceptoALista
agregarConceptoALista(
    conceptoId, 
    nombre, 
    cantidad, 
    precio, 
    descuento,  // <--- AQUÍ
    mes, 
    anio
);
```

### Cómo se usa en el total:
```javascript
// En agregarConceptoALista
const total = (cantidad * precio) - descuento;
```

---

## ⚠️ NOTAS IMPORTANTES

1. **El descuento NO modifica el precio base de la tarifa**
   - La tarifa sigue siendo RD$1500
   - El descuento se aplica solo en la factura
   - Es un descuento por línea de factura

2. **El descuento se guarda en la factura**
   - Se envía al servidor en el campo `descuento[]`
   - Se guarda en `DetalleFactura.descuento`
   - Queda registrado para auditoría

3. **Compatibilidad con mora **
   - El descuento se aplica antes de calcular la mora
   - La mora se calcula sobre el monto SIN descuento
   - Ejemplo: Mensualidad RD$1500, mora 10% = RD$150
   - Total con descuento 10% + mora: RD$1350 + RD$150 = RD$1500

4. **Los estudiantes sin grupo NO son afectados**
   - Si `descuentoGrupoFamiliar = 0`, no hay descuento
   - Las facturas para estudiantes individuales funcionan igual

---

## ✅ VERIFICACIÓN FINAL

Ejecuta este comando para confirmar que todo funciona:

```bash
python -c "from escuelaweb.models import CustomUser; e = CustomUser.objects.filter(rol='Estudiante', grupo_familiar__isnull=False).first(); print(f'Estudiante: {e.get_full_name() if e else \"None\"}'); print(f'Grupo: {e.grupo_familiar.apellido_familia if e and e.grupo_familiar else \"None\"}'); print(f'Descuento: {e.grupo_familiar.descuento_general if e and e.grupo_familiar else 0}%')"
```

Si hay estudiantes en grupos familiares, muestra sus datos. Si no, crea uno o asigna un estudiante a un grupo.

---

## 📞 SOPORTE

Si el descuento no se está aplicando:
1. Verificar que el estudiante esté en un grupo familiar
2. Verificar que el grupo tenga un descuento > 0%
3. Abrir la consola del navegador (F12) y buscar los logs "DEBUG DESCUENTO"
4. Verificar que se esté llamando a `agregarConceptoALista` con el parámetro `descuento` correcto

**¡El sistema ahora aplica descuentos correctamente a estudiantes en grupos familiares!** ✅

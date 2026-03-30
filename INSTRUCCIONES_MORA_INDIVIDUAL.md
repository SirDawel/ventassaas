# Configuración de Mora para Estudiantes Individuales

## ¿Cómo funciona el sistema de mora?

El sistema de mora tiene dos niveles de configuración:

### 1. **Mora por Grupo Familiar** (Prioridad Alta)
- Se aplica cuando el estudiante **pertenece a un grupo familiar**
- Se configura en el grupo familiar
- Todos los estudiantes del grupo usan la misma configuración de mora
- **Prevalece sobre la configuración individual**

### 2. **Mora Individual** (Para estudiantes sin grupo)
- Se aplica cuando el estudiante **NO está en un grupo familiar**
- Se configura directamente en el perfil del estudiante
- Cada estudiante puede tener su propia mora
- **Solo se usa si el estudiante no tiene grupo familiar**

---

## ¿Dónde configurar la mora para estudiantes individuales?

### Opción 1: Desde la Interfaz Web (Recomendado)

1. **Ir a la lista de usuarios**
   - Menu → Usuarios → Listar Usuarios

2. **Seleccionar el estudiante**
   - Buscar el estudiante que NO está en un grupo familiar
   - Click en el botón "Editar" (✏️)

3. **Buscar la sección "Configuración de Mora Individual"**
   - Esta sección tiene un icono de advertencia amarillo ⚠️
   - Aparece solo cuando se edita un estudiante

4. **Configurar los campos:**
   
   - **Día del mes (1-31) en que vencen las mensualidades:**
     - Ejemplo: Si pones `10`, las mensualidades vencen el día 10 de cada mes
     - Rango válido: 1 a 31
   
   - **Porcentaje de recargo por pagos vencidos (0-100%):**
     - Ejemplo: Si pones `15`, se cobrará un 15% adicional sobre el monto vencido
     - Rango válido: 0 a 100
     - Se pueden usar decimales: `15.50` = 15.50%

5. **Guardar los cambios**
   - Click en "Guardar Cambios"

6. **Verificación**
   - El sistema mostrará una nota indicando que esta configuración solo aplica si el estudiante NO está en un grupo familiar

---

### Opción 2: Desde el Admin de Django

1. Acceder al panel de administración: `/admin`
2. Ir a **Usuarios** (CustomUser)
3. Seleccionar el estudiante a editar
4. Buscar la sección **"Configuración de Mora Individual"**
5. Configurar:
   - `Porcentaje de Mora Individual (%)`
   - `Día de Vencimiento Individual`
6. Guardar

---

### Opción 3: Por Código (Para operaciones masivas)

```python
from escuelaweb.models import CustomUser

# Configurar mora para un estudiante específico
estudiante = CustomUser.objects.get(id=497)  # Reemplazar con el ID correcto
estudiante.porcentaje_mora_individual = 15.00  # 15% de mora
estudiante.dia_vencimiento_individual = 10      # Vence el día 10
estudiante.save()

print(f"✅ Configuración guardada para {estudiante.get_full_name()}")
```

Para configurar mora para varios estudiantes sin grupo familiar:

```python
from escuelaweb.models import CustomUser

# Configurar mora para todos los estudiantes sin grupo familiar
estudiantes_sin_grupo = CustomUser.objects.filter(
    rol='Estudiante',
    grupo_familiar__isnull=True
)

for estudiante in estudiantes_sin_grupo:
    estudiante.porcentaje_mora_individual = 15.00
    estudiante.dia_vencimiento_individual = 10
    estudiante.save()
    print(f"✅ {estudiante.get_full_name()}: Mora configurada")
```

---

## Ejemplos de uso

### Ejemplo 1: Estudiante sin grupo familiar
```
Estudiante: Juan Pérez
Grupo Familiar: NO
Mora Individual: 15%
Día Vencimiento Individual: 10

Resultado: Se aplica 15% de mora si paga después del día 10
```

### Ejemplo 2: Estudiante en grupo familiar
```
Estudiante: María García
Grupo Familiar: SÍ (Familia García)
Mora del Grupo: 20%
Mora Individual: 15% (ignorada)

Resultado: Se aplica 20% de mora del grupo familiar
```

### Ejemplo 3: Estudiante sale de un grupo familiar
```
Estudiante: Pedro López
Inicialmente: Grupo Familiar con 20% mora
Se retira del grupo: Ahora usa su mora individual de 10%

Acción requerida: Configurar mora individual antes de retirarlo del grupo
```

---

## Campos del formulario

### Día del mes (1-31) en que vencen las mensualidades
- **Tipo:** Número entero
- **Rango:** 1 a 31
- **Predeterminado:** 10
- **Descripción:** Día del mes en que vence el pago de la mensualidad
- **Ejemplo:** Si es `15`, todas las mensualidades vencen el día 15 de cada mes

### Porcentaje de recargo por pagos vencidos (0-100%)
- **Tipo:** Número decimal
- **Rango:** 0.00 a 100.00
- **Predeterminado:** 0.00
- **Descripción:** Porcentaje de mora que se aplicará sobre el monto vencido
- **Ejemplo:** Si es `15.00`, se cobrará un 15% adicional sobre cada pago vencido

---

## ⚠️ Notas importantes

1. **La configuración individual solo se usa si el estudiante NO está en un grupo familiar**
   
2. **Si un estudiante está en un grupo familiar, se ignora su configuración individual**
   
3. **Si asignas un estudiante a un grupo familiar después, automáticamente usará la mora del grupo**
   
4. **Si retiras un estudiante de un grupo familiar, empezará a usar su mora individual**
   
5. **Para cambiar la mora de todos los estudiantes de un grupo, edita el grupo familiar**

---

## Verificar configuración actual

Puedes verificar qué configuración está usando cada estudiante ejecutando:

```bash
python scripts/ver_mora_individual.py
```

Este script muestra:
- Qué estudiantes están en grupos familiares
- Qué estudiantes usan mora individual
- Los valores efectivos de mora para cada estudiante

---

## Preguntas frecuentes

**P: ¿Cómo saber si un estudiante usa mora del grupo o individual?**
R: Si el estudiante tiene un grupo familiar asignado, usa la mora del grupo. Si no, usa su mora individual.

**P: ¿Puedo tener diferentes moras para estudiantes del mismo grupo?**
R: No, todos los estudiantes de un grupo familiar usan la misma mora configurada en el grupo.

**P: ¿Qué pasa si pongo 0% de mora?**
R: No se cobrará ningún recargo por pagos vencidos.

**P: ¿Puedo usar decimales en el porcentaje?**
R: Sí, puedes usar hasta 2 decimales (ejemplo: 15.50%).

**P: ¿Dónde se refleja la mora en las facturas?**
R: La mora se calcula automáticamente en las facturas cuando hay pagos vencidos y aparece como un campo adicional en la factura.

---

## Script de ayuda

Para ver ejemplos y configuraciones actuales, ejecuta:

```bash
python scripts/ver_mora_individual.py
```

Para configurar mora individual para un estudiante específico:

```bash
python manage.py shell
```

Luego ejecuta:

```python
from escuelaweb.models import CustomUser

# Buscar estudiante por ID
estudiante = CustomUser.objects.get(id=TU_ID_AQUI)

# Ver configuración actual
print(f"Grupo familiar: {estudiante.grupo_familiar}")
print(f"Mora individual: {estudiante.porcentaje_mora_individual}%")
print(f"Día vencimiento: {estudiante.dia_vencimiento_individual}")

# Cambiar configuración
estudiante.porcentaje_mora_individual = 15.00
estudiante.dia_vencimiento_individual = 10
estudiante.save()

print("✅ Configuración actualizada")
```

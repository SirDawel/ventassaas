# 📋 INSTRUCCIONES: Descuento Individual para Estudiantes

## 🎯 ¿Qué es el Descuento Individual?

El **descuento individual** es un porcentaje de descuento (0-100%) que se puede configurar para cada estudiante de manera independiente. Este descuento se aplica a:

- ✅ **Mensualidades**
- ✅ **Inscripción**
- ✅ **Transporte**

## 🔄 ¿Cómo funciona la prioridad de descuentos?

El sistema aplica descuentos según la siguiente lógica:

### 1. **Estudiante en Grupo Familiar**
   - Se usa el **descuento del grupo familiar**
   - El descuento individual del estudiante es **ignorado**
   
   ```
   Ejemplo: Lucy Aquino está en "Familia Mateo" con 25% de descuento
   → Se aplica: 25% del grupo familiar
   → Se ignora: descuento individual de Lucy (si existe)
   ```

### 2. **Estudiante SIN Grupo Familiar**
   - Se usa el **descuento individual del estudiante**
   - Si no tiene descuento individual configurado, es 0%
   
   ```
   Ejemplo: Rihanna Dotel no está en grupo familiar, descuento individual: 10%
   → Se aplica: 10% descuento individual
   ```

## 📝 ¿Cómo configurar el Descuento Individual?

### Opción 1: Interfaz Web

1. Ir a **Usuarios** → **Editar Usuario**
2. Buscar la sección **"Configuración de Descuento Individual"** (recuadro verde)
3. Ingresar el porcentaje de descuento (0-100)
4. Guardar cambios

**Nota:** Esta sección solo aparece si el rol del usuario es "Estudiante"

### Opción 2: Admin de Django

1. Ir al **Panel de Administración**
2. Seleccionar **Usuarios** → Editar el estudiante
3. En la sección **"Configuración de Descuento Individual"**
4. Ingresar el valor en el campo **Descuento Individual (%)**
5. Guardar

### Opción 3: Script Python (Avanzado)

```python
from escuelaweb.models import CustomUser

# Obtener el estudiante
estudiante = CustomUser.objects.get(id=497)

# Asignar descuento individual de 15%
estudiante.descuento_individual = 15.00
estudiante.save()

print(f"✅ Descuento configurado para {estudiante.get_full_name()}")
print(f"   Descuento efectivo: {estudiante.get_descuento()}%")
```

## 🧪 ¿Cómo verificar el descuento de un estudiante?

### Script de Verificación

Ejecutar el script de verificación:

```bash
python scripts\ver_descuento_individual.py
```

Este script muestra:
- 📚 Nombre y email del estudiante
- 👨‍👩‍👧‍👦 Si está en grupo familiar y el descuento del grupo
- 👤 Si NO está en grupo familiar y su descuento individual
- ✅ **Descuento efectivo aplicable** (el que realmente se usará)

### Método Python

```python
from escuelaweb.models import CustomUser

estudiante = CustomUser.objects.get(id=497)

# Obtener el descuento efectivo (usa grupo familiar o individual)
descuento_efectivo = estudiante.get_descuento()

print(f"Descuento aplicable: {descuento_efectivo}%")
```

## 💼 Aplicación en Facturas

El descuento se aplica **automáticamente** al crear facturas para el estudiante:

1. El sistema detecta si el estudiante tiene grupo familiar
2. Si tiene grupo → usa descuento del grupo
3. Si NO tiene grupo → usa descuento individual del estudiante
4. Aplica el descuento a mensualidades, inscripción y transporte

### Ver en el Log de Consola

Al crear una factura, en la **Consola del Navegador** (F12) se muestra:

```javascript
// Si está en grupo familiar:
Descuento del grupo familiar: 25 %

// Si NO está en grupo familiar:
Descuento individual del estudiante: 10 %
```

## 📊 Ejemplos Prácticos

### Ejemplo 1: Estudiante con 10% de descuento individual

```
Estudiante: JOHANGEL SANCHEZ SANCHEZ
Grupo Familiar: NO
Descuento Individual: 10%

Mensualidad: RD$5,000
Descuento: RD$500 (10%)
Total a pagar: RD$4,500
```

### Ejemplo 2: Estudiante en grupo familiar

```
Estudiante: Lucy Aquino
Grupo Familiar: Familia Mateo (25% descuento)
Descuento Individual: 5% (ignorado ❌)

Mensualidad: RD$5,000
Descuento: RD$1,250 (25% del grupo)
Total a pagar: RD$3,750
```

## 🔧 Archivos Modificados

Los siguientes archivos fueron modificados para implementar esta funcionalidad:

1. **escuelaweb/models.py**
   - Campo `descuento_individual` añadido
   - Método `get_descuento()` para obtener descuento efectivo

2. **escuelaweb/forms.py**
   - `UserRegistrationForm` con campo descuento_individual
   - `UserUpdateForm` con campo descuento_individual

3. **escuelaweb/templates/users/user_form.html**
   - Sección "Configuración de Descuento Individual"

4. **escuelaweb/templates/cobros/factura_crear_nueva.html**
   - Lógica JavaScript para aplicar descuento individual

5. **escuelaweb/admin.py**
   - Fieldset para descuento individual en admin

6. **escuelaweb/migrations/0041_add_descuento_individual.py**
   - Migración de base de datos

## ⚠️ Importante

- El descuento es **acumulativo**: si el estudiante tiene descuento individual del 10% y se agrega a un grupo con 25%, se aplicará el del grupo (25%), NO la suma (35%)
- Los descuentos se aplican **solo** a mensualidades, inscripción y transporte
- Otros conceptos (libros, uniformes, etc.) **NO** reciben descuento automático
- El valor del descuento debe estar entre **0 y 100**
- Se permiten decimales: 10.50%, 5.25%, etc.

## 📞 Soporte

Si tienes dudas o problemas con el descuento individual:

1. Verifica con el script: `python scripts\ver_descuento_individual.py`
2. Revisa la consola del navegador (F12) al crear facturas
3. Verifica que la migración esté aplicada: `python manage.py showmigrations escuelaweb`

# ✅ Configuración de Mora Individual - GUÍA COMPLETA

## 🎯 CAMBIOS REALIZADOS

### 1. ✅ Formulario de Editar Usuario Mejorado
- **Ubicación:** Templates → users → user_form.html
- **Cambios:** 
  - Sección "Configuración de Mora Individual" con diseño mejorado
  - Card con borde amarillo para mayor visibilidad
  - Iconos coloridos para cada campo
  - Validación HTML5 incorporada

### 2. ✅ Botón de Editar Usuario en Búsqueda de Estudiantes
- **Ubicación:** http://127.0.0.1:8000/cobros/buscar-estudiante/
- **Cambios:** 
  - Nuevo botón "Editar" en la tabla de estudiantes
  - Acceso directo al formulario de edición con mora individual
  - Tooltip informativo sobre configuración de mora

### 3. ✅ Formularios Actualizados
- **UserUpdateForm:** Ahora incluye campos de mora individual
- **Widgets mejorados:** Validación de rango en cliente (HTML5)

---

## 📍 DÓNDE ENCONTRAR LA CONFIGURACIÓN DE MORA INDIVIDUAL

### Opción 1: Desde Búsqueda de Estudiantes (MÁS RÁPIDO) ⚡
1. Ve a: **http://127.0.0.1:8000/cobros/buscar-estudiante/**
2. Busca el estudiante (por nombre, código de barras, cédula, etc.)
3. Haz clic en el botón **"Editar"** (botón azul con icono 👤✏️)
4. Desplázate hasta la sección **"Configuración de Mora Individual"** (con borde amarillo)
5. Configura:
   - **Día del mes (1-31):** Cuándo vence cada mes
   - **Porcentaje de mora (0-100):** Recargo por pago vencido
6. Click en **"Guardar Cambios"**

### Opción 2: Desde Lista de Usuarios
1. Ve a: **Usuarios → Listar Usuarios**
2. Busca el estudiante
3. Click en el botón **"Editar"** (✏️)
4. Busca la sección **"Configuración de Mora Individual"**
5. Configura y guarda

### Opción 3: Desde Admin de Django
1. Ve a: **http://127.0.0.1:8000/admin/**
2. Click en **Usuarios** (CustomUser)
3. Selecciona un estudiante
4. Busca la sección **"Configuración de Mora Individual"**
5. Configura y guarda

---

## 🎨 CÓMO SE VE LA SECCIÓN DE MORA INDIVIDUAL

La sección se ve así cuando editas un estudiante:

```
┌────────────────────────────────────────────────────────────────┐
│ ⚠️ Configuración de Mora Individual                            │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ℹ️ Nota: Esta configuración solo aplica si el estudiante     │
│     NO está en un grupo familiar. Si está en un grupo, se      │
│     usará la configuración del grupo.                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📅 Día de Vencimiento Individual                       │   │
│  │  [  10  ] ▼                                             │   │
│  │  Día del mes (1-31) en que vencen las mensualidades    │   │
│  │                                                          │   │
│  │  💯 Porcentaje de Mora Individual (%)                   │   │
│  │  [  15.00  ] %                                          │   │
│  │  Porcentaje de recargo por pagos vencidos (0-100%)     │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔍 VERIFICAR CONFIGURACIÓN ACTUAL

Para ver qué estudiantes tienen mora individual configurada:

```bash
python scripts/ver_mora_individual.py
```

Este script te mostrará:
- Estudiantes en grupos familiares (usan mora del grupo)
- Estudiantes individuales (usan mora individual)
- Valores efectivos de mora para cada estudiante

---

## 💡 EJEMPLOS DE USO

### Ejemplo 1: Configurar mora para estudiante nuevo sin grupo
```
Estudiante: María López
Situación: No está en grupo familiar

Pasos:
1. Buscar estudiante en /cobros/buscar-estudiante/
2. Click en "Editar"
3. En "Configuración de Mora Individual":
   - Día: 10
   - Porcentaje: 15.00
4. Guardar

Resultado: A partir del día 10 de cada mes, si no ha pagado, 
           se le cobrará un 15% adicional.
```

### Ejemplo 2: Estudiante que sale de un grupo familiar
```
Estudiante: Pedro García
Situación: Estaba en grupo familiar, ahora es individual

Pasos:
1. ANTES de sacarlo del grupo, configura su mora individual
2. Editar estudiante → Mora Individual:
   - Día: 15
   - Porcentaje: 10.00
3. Guardar
4. Luego quitar del grupo familiar

Resultado: Ahora usa su configuración individual (10% mora, día 15)
```

---

## ⚠️ PREGUNTAS FRECUENTES

**P: No veo la sección de mora individual al editar un estudiante**
R: La sección solo aparece cuando el rol es "Estudiante". Verifica:
   - Que el usuario tenga rol "Estudiante"
   - Que estés en modo edición (no creación)
   - Puede estar oculta si el rol no es estudiante (usa JavaScript dinámico)

**P: Configuré la mora pero no se aplica**
R: Verifica:
   - ¿El estudiante está en un grupo familiar? → Usa la mora del grupo
   - ¿El porcentaje es mayor a 0? → Si es 0%, no hay mora
   - ¿Estás facturando después de la fecha de vencimiento?

**P: ¿Cómo saber si está usando mora del grupo o individual?**
R: Ejecuta: `python scripts/ver_mora_individual.py`
   - Si tiene grupo familiar → Usa mora del grupo
   - Si NO tiene grupo familiar → Usa mora individual

**P: ¿Puedo tener mora 0%?**
R: Sí, si pones 0% significa que NO se cobrará recargo por mora.

---

## 📚 ARCHIVOS MODIFICADOS

✅ **escuelaweb/forms.py**
   - UserUpdateForm: Agregados campos de mora individual
   - Validación de rango mejorada

✅ **escuelaweb/templates/users/user_form.html**
   - Diseño mejorado para sección de mora individual
   - Card con borde amarillo y iconos coloridos
   - Mejor visibilidad

✅ **escuelaweb/templates/cobros/buscar_estudiante.html**
   - Botón "Editar" agregado en tabla de estudiantes
   - Acceso rápido a configuración de mora

✅ **escuelaweb/admin.py**
   - Admin personalizado con sección de mora individual

---

## 🚀 FLUJO RECOMENDADO

### Para estudiantes nuevos SIN grupo familiar:
1. Crear estudiante
2. Ir a Búsqueda de Estudiantes → Buscar → Editar
3. Configurar mora individual
4. Guardar

### Para estudiantes que SALEN de un grupo familiar:
1. Editar estudiante ANTES de quitarlo del grupo
2. Configurar mora individual
3. Guardar
4. Quitar del grupo familiar
5. Ahora usará su mora individual

### Para estudiantes EN grupo familiar:
1. Los campos de mora individual se pueden editar
2. PERO no se usarán mientras esté en el grupo
3. Solo se activarán si sale del grupo
4. Puedes configurarlos "por si acaso" sale del grupo

---

## ✅ TODO LISTO

Ahora puedes:
- ✅ Ver el botón "Editar" en /cobros/buscar-estudiante/
- ✅ Configurar mora individual desde edición de usuario
- ✅ Los campos tienen validación de rango
- ✅ Diseño visual mejorado y más visible
- ✅ Sistema funciona para estudiantes con/sin grupo familiar

**¡Ya está todo implementado y funcionando!** 🎉

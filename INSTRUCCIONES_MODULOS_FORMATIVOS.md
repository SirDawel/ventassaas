# Sistema de Calificaciones para Módulos Formativos

## Descripción General

El sistema de módulos formativos utiliza un enfoque de **Resultados de Aprendizaje (RA)** en lugar del sistema tradicional de competencias y períodos.

## Características del Sistema Modular

### 1. Resultados de Aprendizaje (RA)
- **Total de RA:** 10 por materia
- **Valor de cada RA:** 10% (0-10 puntos)
- **Total posible:** 100% (suma de los 10 RA)

### 2. Diferencias con el Sistema Tradicional

| Aspecto | Sistema Tradicional | Sistema Modular |
|---------|-------------------|-----------------|
| Evaluación | 4 Competencias × 4 Períodos | 10 Resultados de Aprendizaje |
| Recuperaciones | Sí (RP por competencia) | No |
| Exámenes Extraordinarios | Sí (Completivo, Extraordinario, Especial) | No |
| Calificación Final | Promedio de 4 competencias | Suma de 10 RA (total 100%) |

### 3. Configuración de Materias

Para que una materia use el sistema modular:

1. Ir a la lista de materias
2. Editar la materia deseada
3. En el campo **"Categoría"**, seleccionar **"Modular"**
4. Guardar los cambios

### 4. Ingreso de Calificaciones

Cuando un profesor o administrador accede a "Agregar Notas" para una materia modular:

1. El sistema detecta automáticamente que es modular
2. Redirige a la interfaz de **"Calificaciones del Módulo Formativo"**
3. Muestra 10 columnas (RA 1 a RA 10)
4. Cada campo acepta valores de **0 a 10** (representa porcentajes)

### 5. Cálculo de la Calificación Final

```
Nota Final = RA_1 + RA_2 + RA_3 + RA_4 + RA_5 + RA_6 + RA_7 + RA_8 + RA_9 + RA_10
```

**Ejemplo:**
- RA 1: 8.5%
- RA 2: 9.0%
- RA 3: 7.5%
- RA 4: 9.5%
- RA 5: 8.0%
- RA 6: 9.0%
- RA 7: 8.5%
- RA 8: 9.5%
- RA 9: 8.0%
- RA 10: 9.0%

**Nota Final = 86.5** (sobre 100)

### 6. Estructura de la Base de Datos

Los campos RA se almacenan en el modelo `Matricula`:

```python
ra_1 = FloatField(null=True, blank=True)  # RA 1 (%)
ra_2 = FloatField(null=True, blank=True)  # RA 2 (%)
ra_3 = FloatField(null=True, blank=True)  # RA 3 (%)
ra_4 = FloatField(null=True, blank=True)  # RA 4 (%)
ra_5 = FloatField(null=True, blank=True)  # RA 5 (%)
ra_6 = FloatField(null=True, blank=True)  # RA 6 (%)
ra_7 = FloatField(null=True, blank=True)  # RA 7 (%)
ra_8 = FloatField(null=True, blank=True)  # RA 8 (%)
ra_9 = FloatField(null=True, blank=True)  # RA 9 (%)
ra_10 = FloatField(null=True, blank=True) # RA 10 (%)
```

### 7. Plantilla del Formato

El formato de calificaciones sigue el estándar de "CALIFICACIONES DEL MÓDULO FORMATIVO":

```
┌────────────────────────────────────────────────────────────────────┐
│               CALIFICACIONES DEL MÓDULO FORMATIVO                  │
├──────┬──────────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┼───────┤
│  #   │ ALUMNO   │RA1 │RA2 │RA3 │RA4 │RA5 │RA6 │RA7 │RA8 │RA9 │RA10│ TOTAL │
├──────┼──────────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼───────┤
│  1   │ Juan P.  │ 8.5│ 9.0│ 7.5│ 9.5│ 8.0│ 9.0│ 8.5│ 9.5│ 8.0│ 9.0│ 86.5  │
└──────┴──────────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴───────┘
```

### 8. Validaciones

- Cada RA acepta valores de **0 a 10**
- Los valores pueden tener hasta 2 decimales
- La nota final se calcula solo cuando **todos los 10 RA** están completos
- No se requieren todas las RA para guardar (se pueden ir completando progresivamente)

### 9. Archivos Modificados

- **Modelo:** `escuelaweb/models.py` - Agregados campos ra_1 a ra_10
- **Vista:** `escuelaweb/views.py` - Función `agregar_notas_modular()`
- **Template:** `escuelaweb/templates/est_forder/agregar_notas_modular.html`
- **Migración:** `0029_matricula_ra_1_matricula_ra_10_matricula_ra_2_and_more.py`

### 10. Roles con Acceso

- **Administrador:** Acceso completo a todas las materias modulares
- **Profesor:** Acceso solo a las materias modulares que imparte

## Notas Importantes

⚠️ **Una materia no puede cambiar de categoría si ya tiene calificaciones registradas**

ℹ️ **Las materias modulares no utilizan los campos de competencias (COM, LOG, CIE, ETI)**

✅ **La calificación final se actualiza automáticamente al guardar los RA**

# Hojas de Calificaciones Imprimibles

## Descripción
Sistema para generar hojas de calificaciones en blanco que pueden imprimirse, llenarse a mano, y luego las notas se ingresan al sistema.

## Características

### Para Materias por Períodos
- **Columnas de Competencias:**
  - Com (Comunicativa)
  - Mat (Lógico-Matemática)
  - Cie (Científica)
  - Eti (Ética y Ciudadana)
  - Promedio
  - Observaciones

- **Períodos Disponibles:**
  - Período 1
  - Período 2
  - Período 3
  - Período 4

### Para Materias Modulares
- **Columnas de Resultados de Aprendizaje (RA):**
  - Se generan según la configuración de la materia
  - Cada RA muestra su porcentaje de ponderación
  - Columna de Total
  - Observaciones

## Cómo Usar

### Acceso
1. Ir a **Materias** (`/materias/?curso=XX`)
2. En cada materia, hacer clic en el botón **"Hoja Imprimible"** (ícono de impresora)

### Opciones
- **Seleccionar Período/Tipo:** Elegir qué período se va a evaluar
- **Imprimir:** Genera la hoja optimizada para papel tamaño carta en orientación horizontal
- **Cerrar:** Vuelve a la vista anterior

### Proceso Recomendado
1. **Generar la Hoja:** Seleccionar el período deseado
2. **Imprimir:** Usar el botón de imprimir del navegador o el botón en pantalla
3. **Llenar a Mano:** Escribir las calificaciones durante la clase con lápiz/bolígrafo
4. **Ingresar al Sistema:** Posteriormente, usar la opción "Gestionar Notas" para transcribir las calificaciones al sistema

## Detalles Técnicos

### Formato de Impresión
- **Tamaño:** Carta (Letter)
- **Orientación:** Vertical (Portrait)
- **Márgenes:** 0.5cm

### Información Incluida
- Nombre de la materia y código
- Curso y año escolar
- Nombre del profesor
- Fecha (para llenar manualmente)
- Lista numerada de estudiantes ordenados alfabéticamente
- Cuadros para firmas

### Permisos
Pueden acceder a esta funcionalidad:
- Administradores
- Directores
- Coordinadores
- Secretarias
- Profesores (solo sus materias)

## Ventajas
- ✅ Permite tomar notas en clase sin necesidad de dispositivos electrónicos
- ✅ Formato estandarizado y profesional
- ✅ Fácil de archivar como respaldo físico
- ✅ Estudiantes aparecen ordenados alfabéticamente
- ✅ Espacio para observaciones adicionales
- ✅ Compatible con diferentes sistemas de evaluación

## URL de Acceso
```
/materias/<materia_id>/hoja-calificaciones/?tipo=<periodo>
```

Donde:
- `<materia_id>`: ID de la materia
- `<periodo>`: periodo1, periodo2, periodo3, periodo4, o modular

## Ejemplo de Uso
```
http://127.0.0.1:8000/materias/45/hoja-calificaciones/?tipo=periodo1
```

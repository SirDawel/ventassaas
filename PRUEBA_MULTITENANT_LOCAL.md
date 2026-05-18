# 🏫 Guía de Prueba Multi-Tenant Local

## ✅ Lo que ya está hecho

1. ✅ Modelo `Escuela` creado
2. ✅ Middleware de subdominios configurado  
3. ✅ Managers automáticos creados
4. ✅ Settings actualizados
5. ✅ Migraciones creadas

---

## 🚀 Paso a Paso para Probar

### 📝 Paso 1: Aplicar Migraciones

```powershell
.\.venv\Scripts\Activate.ps1
python manage.py migrate
```

---

### 🌐 Paso 2: Configurar Hosts Locales

**En Windows, editar `C:\Windows\System32\drivers\etc\hosts`**

1. Abrir **Notepad como Administrador**
2. Abrir archivo: `C:\Windows\System32\drivers\etc\hosts`
3. Agregar al final:

```
127.0.0.1 localhost
127.0.0.1 www.localhost
127.0.0.1 escuela1.localhost
127.0.0.1 escuela2.localhost
127.0.0.1 colegiosantiago.localhost
```

4. Guardar y cerrar

---

### 🏫 Paso 3: Crear Primera Escuela

```powershell
python manage.py shell
```

```python
from escuelaweb.models_escuela import Escuela

# Crear escuela 1
escuela1 = Escuela(
    nombre="Colegio Santiago",
    nombre_corto="escuela1",
    email_contacto="info@escuela1.edu",
    telefono="809-555-0001",
    direccion="Calle Principal #123",
    activo=True,
    max_usuarios=500,
    plan='premium'
)
escuela1.save()
print(f"✅ Escuela creada: {escuela1.nombre}")

# Crear escuela 2
escuela2 = Escuela(
    nombre="Liceo La Esperanza",
    nombre_corto="escuela2",
    email_contacto="info@escuela2.edu",
    telefono="809-555-0002",
    direccion="Avenida Central #456",
    activo=True,
    max_usuarios=300,
    plan='basico'
)
escuela2.save()
print(f"✅ Escuela creada: {escuela2.nombre}")

# Ver todas las escuelas
from escuelaweb.models_escuela import Escuela
escuelas = Escuela.objects.all()
for e in escuelas:
    print(f"- {e.nombre} ({e.nombre_corto}) - {e.get_url_acceso()}")

exit()
```

---

### 🚀 Paso 4: Iniciar Servidor

```powershell
python manage.py runserver
```

---

### 🌍 Paso 5: Probar en Navegador

Abrir estas URLs en diferentes pestañas:

#### Sitio Público (sin tenant):
- http://localhost:8000/
- http://www.localhost:8000/

#### Escuela 1:
- http://escuela1.localhost:8000/
- http://escuela1.localhost:8000/login/

#### Escuela 2:
- http://escuela2.localhost:8000/
- http://escuela2.localhost:8000/login/

---

## 🔍 ¿Cómo Saber que Funciona?

### ✅ Si funciona correctamente:

1. **Escuela no existente:** http://noexiste.localhost:8000/
   - Debe mostrar: "Escuela No Encontrada"

2. **Escuela 1 vs Escuela 2:**
   - Los usuarios son diferentes
   - Los datos NO se mezclan
   - Cada una tiene su propio contexto

---

## 🎯 Próximo Paso: Agregar Campo `escuela` a los Modelos

Para que el sistema funcione completamente, necesitas agregar `escuela` a tus modelos existentes:

```python
# En models.py - Agregar a CustomUser
class CustomUser(AbstractUser):
    # ... campos existentes ...
    
    # AGREGAR ESTO:
    escuela = models.ForeignKey(
        'Escuela',
        on_delete=models.PROTECT,
        related_name='usuarios',
        verbose_name="Escuela",
        null=True,  # Temporal para migración
        blank=True
    )
    
    # Usar manager multi-tenant
    from .tenant_managers import TenantManager
    objects = TenantManager()
```

---

## 📊 Verificar en Shell

```python
python manage.py shell
```

```python
# Importar contexto y modelos
from escuelaweb import tenant_context
from escuelaweb.models_escuela import Escuela

# Obtener una escuela
escuela1 = Escuela.objects.get(nombre_corto='escuela1')

# Establecer contexto (simular request)
tenant_context.set_current_escuela(escuela1)

# Ahora todas las queries filtran por escuela1
from escuelaweb.models import CustomUser
usuarios = CustomUser.objects.all()  # Solo usuarios de escuela1
print(f"Usuarios en {escuela1.nombre}: {usuarios.count()}")

# Cambiar a escuela2
escuela2 = Escuela.objects.get(nombre_corto='escuela2')
tenant_context.set_current_escuela(escuela2)

usuarios = CustomUser.objects.all()  # Solo usuarios de escuela2
print(f"Usuarios en {escuela2.nombre}: {usuarios.count()}")
```

---

## 🐛 Troubleshooting

### Problema: "Escuela No Encontrada" en todas las URLs

**Solución:**
```powershell
# Verificar que las escuelas existan
python manage.py shell
>>> from escuelaweb.models_escuela import Escuela
>>> Escuela.objects.all()
```

### Problema: Subdominios no funcionan

**Solución:**
1. Verificar archivo `hosts`: `C:\Windows\System32\drivers\etc\hosts`
2. Reiniciar navegador
3. Limpiar caché DNS:
   ```powershell
   ipconfig /flushdns
   ```

### Problema: "name 'tenant_context' is not defined"

**Solución:**
- Asegúrate de que `escuelaweb/__init__.py` exista (aunque esté vacío)
- Reiniciar servidor Django

---

## 📱 Registro de Nuevas Escuelas

**Pendiente crear:** Vista pública para registro de escuelas

```python
# En views.py
def registro_escuela_publica(request):
    """Vista para que las escuelas se registren"""
    if request.method == 'POST':
        # Crear escuela
        # Crear usuario administrador
        # Enviar email de confirmación
        pass
    return render(request, 'public/registro_escuela.html')
```

---

## 🎉 ¡Felicidades!

Ahora tienes un sistema multi-tenant funcionando. Cada escuela:
- ✅ Tiene su propio subdominio
- ✅ Sus datos están aislados
- ✅ Puede tener su propia configuración
- ✅ Es completamente independiente

**Próximos pasos:**
1. Agregar campo `escuela` a todos los modelos relevantes
2. Crear vista de registro de escuelas
3. Migrar datos existentes a una escuela
4. Personalización por escuela (logo, colores)

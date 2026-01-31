# Sistema de Gestión Escolar

Sistema web completo para gestión de escuelas desarrollado con Django.

## 🌟 Características

- ✅ Gestión de estudiantes, profesores y personal
- ✅ Control de asistencia
- ✅ Facturación y pagos (mensualidades, inscripciones, servicios)
- ✅ Inventario de artículos y servicios
- ✅ Generación de reportes y recibos
- ✅ Gestión de materias y grupos
- ✅ Panel administrativo completo

## 🚀 Instalación Local

### Pre-requisitos

- Python 3.10 o superior
- pip
- virtualenv

### Pasos

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repo>
   cd escuela
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   # Copiar archivo de ejemplo
   cp .env.example .env
   
   # Editar .env con tus valores
   ```

5. **Aplicar migraciones**
   ```bash
   python manage.py migrate
   ```

6. **Crear superusuario**
   ```bash
   python manage.py createsuperuser
   ```

7. **Ejecutar servidor de desarrollo**
   ```bash
   python manage.py runserver
   ```

8. **Acceder a la aplicación**
   - Aplicación: http://127.0.0.1:8000
   - Admin: http://127.0.0.1:8000/admin

## 📦 Estructura del Proyecto

```
Escuela/
├── Escuela/              # Configuración principal
│   ├── settings.py       # Configuración (usa variables de entorno)
│   ├── urls.py           # URLs principales
│   └── wsgi.py           # WSGI para producción
├── escuelaweb/           # Aplicación principal
│   ├── models.py         # Modelos de datos
│   ├── views.py          # Vistas
│   ├── forms.py          # Formularios
│   ├── admin.py          # Admin personalizado
│   └── templates/        # Plantillas HTML
├── scripts/              # Scripts de utilidad y mantenimiento
├── static/               # Archivos estáticos (CSS, JS, img)
├── media/                # Archivos subidos por usuarios
├── .env.example          # Ejemplo de variables de entorno
├── requirements.txt      # Dependencias Python
├── DEPLOY.md            # Guía de despliegue
└── manage.py            # Comando de Django
```

## 🛠️ Scripts de Utilidad

En la carpeta `scripts/` hay herramientas para mantenimiento:

```bash
# Activar año escolar
python scripts/activar_anho_2025.py

# Corregir saldos
python scripts/corregir_saldos_negativos.py

# Ver más en scripts/README.md
```

## 🔒 Seguridad

### Variables de Entorno

El proyecto usa variables de entorno para configuración sensible:
- `SECRET_KEY`: Clave secreta de Django
- `DEBUG`: Modo debug (False en producción)
- `DATABASE_URL`: URL de la base de datos
- `EMAIL_*`: Configuración de email

**IMPORTANTE:** Nunca subas el archivo `.env` al repositorio.

### Producción

Para despliegue en producción:
1. Leer `DEPLOY.md` con instrucciones detalladas
2. Configurar `.env` con valores de producción
3. Usar PostgreSQL (no SQLite)
4. Configurar HTTPS
5. Ejecutar `collectstatic`

## 🐛 Problemas Comunes

### Error: "No module named 'dotenv'"
```bash
pip install python-dotenv
```

### Error de migraciones
```bash
python manage.py migrate --run-syncdb
```

### Archivos estáticos no cargan
```bash
python manage.py collectstatic --noinput
```

## 📝 Desarrollo

### Crear nueva migración
```bash
python manage.py makemigrations
python manage.py migrate
```

### Ejecutar shell de Django
```bash
python manage.py shell
```

### Ver usuarios
```bash
python manage.py shell
>>> from escuelaweb.models import CustomUser
>>> CustomUser.objects.all()
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es privado y confidencial.

## 👥 Contacto

Para soporte o consultas, contactar al administrador del sistema.

---

**Nota:** Este es un sistema en producción. Manejar con cuidado los datos sensibles.

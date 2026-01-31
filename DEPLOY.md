# Guía de Despliegue - Sistema Escolar

## 📋 Pre-requisitos

### En el servidor:
- Ubuntu 20.04+ / Debian 11+
- Python 3.10+
- PostgreSQL 13+
- Nginx
- Git

## 🚀 Pasos de Despliegue

### 1. Preparar el Servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install python3-pip python3-venv postgresql postgresql-contrib nginx git -y
```

### 2. Configurar PostgreSQL

```bash
# Conectar a PostgreSQL
sudo -u postgres psql

# Crear base de datos y usuario
CREATE DATABASE escuela_db;
CREATE USER escuela_user WITH PASSWORD 'tu_password_seguro';
ALTER ROLE escuela_user SET client_encoding TO 'utf8';
ALTER ROLE escuela_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE escuela_user SET timezone TO 'America/Santo_Domingo';
GRANT ALL PRIVILEGES ON DATABASE escuela_db TO escuela_user;
\q
```

### 3. Clonar el Proyecto

```bash
# Ir al directorio de aplicaciones
cd /home/usuario

# Clonar repositorio
git clone https://github.com/tu-usuario/escuela.git
cd escuela
```

### 4. Configurar Entorno Virtual

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 5. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.production.example .env

# Editar con tus valores
nano .env
```

**Configurar estos valores obligatoriamente:**
- `SECRET_KEY`: Generar una nueva con: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DEBUG=False`
- `ALLOWED_HOSTS`: Tu dominio
- `DB_*`: Credenciales de PostgreSQL
- `EMAIL_*`: Configuración de email

### 6. Migraciones y Archivos Estáticos

```bash
# Aplicar migraciones
python manage.py migrate

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Crear superusuario
python manage.py createsuperuser
```

### 7. Configurar Gunicorn

```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/escuela.service
```

**Contenido del archivo:**
```ini
[Unit]
Description=Escuela Gunicorn daemon
After=network.target

[Service]
User=usuario
Group=www-data
WorkingDirectory=/home/usuario/escuela
Environment="PATH=/home/usuario/escuela/venv/bin"
ExecStart=/home/usuario/escuela/venv/bin/gunicorn --workers 3 --bind unix:/home/usuario/escuela/escuela.sock Escuela.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Iniciar y habilitar servicio
sudo systemctl start escuela
sudo systemctl enable escuela
```

### 8. Configurar Nginx

```bash
# Crear configuración del sitio
sudo nano /etc/nginx/sites-available/escuela
```

**Contenido del archivo:**
```nginx
server {
    listen 80;
    server_name tudominio.com www.tudominio.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /home/usuario/escuela/staticfiles/;
    }

    location /media/ {
        alias /home/usuario/escuela/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/usuario/escuela/escuela.sock;
    }
}
```

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/escuela /etc/nginx/sites-enabled

# Verificar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

### 9. Configurar SSL (Opcional pero Recomendado)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtener certificado
sudo certbot --nginx -d tudominio.com -d www.tudominio.com
```

### 10. Verificar Funcionamiento

```bash
# Ver logs de Gunicorn
sudo journalctl -u escuela

# Ver logs de Nginx
sudo tail -f /var/log/nginx/error.log
```

## 🔧 Mantenimiento

### Actualizar la Aplicación

```bash
cd /home/usuario/escuela
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart escuela
```

### Backup de Base de Datos

```bash
# Crear backup
pg_dump -U escuela_user escuela_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
psql -U escuela_user escuela_db < backup_YYYYMMDD_HHMMSS.sql
```

### Monitoreo

```bash
# Ver estado del servicio
sudo systemctl status escuela

# Ver logs en tiempo real
sudo journalctl -u escuela -f
```

## ⚠️ Problemas Comunes

### Error de permisos en archivos estáticos
```bash
sudo chown -R usuario:www-data /home/usuario/escuela
sudo chmod -R 755 /home/usuario/escuela
```

### Error de conexión a PostgreSQL
- Verificar que PostgreSQL está corriendo: `sudo systemctl status postgresql`
- Verificar credenciales en `.env`
- Verificar permisos del usuario en la base de datos

### Error 502 Bad Gateway
- Verificar que Gunicorn está corriendo: `sudo systemctl status escuela`
- Verificar el socket: `ls -l /home/usuario/escuela/escuela.sock`
- Revisar logs: `sudo journalctl -u escuela -n 50`

## 📞 Soporte

Para problemas específicos, revisar los logs y consultar la documentación de Django.

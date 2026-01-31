# ✅ Checklist de Seguridad para Producción

## 🔴 CRÍTICO - Antes de Desplegar

- [ ] **SECRET_KEY única generada**
  ```bash
  python scripts/generar_secret_key.py
  ```
  
- [ ] **DEBUG=False** en `.env` de producción
  
- [ ] **ALLOWED_HOSTS configurado** con tu dominio real
  
- [ ] **Credenciales de email actualizadas** (sin exponer en código)
  
- [ ] **Base de datos PostgreSQL** configurada (no SQLite)
  
- [ ] **Contraseñas seguras** para DB_PASSWORD

## 🟡 IMPORTANTE - Configuración

- [ ] **Archivo .env NO está en Git**
  ```bash
  # Verificar que .env está ignorado
  git status
  ```
  
- [ ] **Backups automáticos** de base de datos configurados
  
- [ ] **HTTPS habilitado** (Certbot/Let's Encrypt)
  
- [ ] **Archivos estáticos recolectados**
  ```bash
  python manage.py collectstatic --noinput
  ```
  
- [ ] **Permisos de archivos correctos**
  ```bash
  sudo chown -R usuario:www-data /path/to/escuela
  sudo chmod -R 755 /path/to/escuela
  ```

## 🟢 RECOMENDADO - Seguridad Adicional

- [ ] **Firewall configurado** (ufw)
  ```bash
  sudo ufw allow 'Nginx Full'
  sudo ufw allow OpenSSH
  sudo ufw enable
  ```
  
- [ ] **Fail2ban instalado** para proteger contra ataques
  ```bash
  sudo apt install fail2ban
  ```
  
- [ ] **Monitoreo de logs** configurado
  
- [ ] **Backup de media/ configurado**
  
- [ ] **Rate limiting** en endpoints críticos

## 🔐 Verificaciones Post-Despliegue

```bash
# 1. Verificar que DEBUG está False
python manage.py shell
>>> from django.conf import settings
>>> settings.DEBUG  # Debe ser False

# 2. Verificar SECRET_KEY es diferente
>>> settings.SECRET_KEY  # NO debe ser la de desarrollo

# 3. Verificar ALLOWED_HOSTS
>>> settings.ALLOWED_HOSTS  # Debe incluir tu dominio

# 4. Verificar base de datos
>>> settings.DATABASES['default']['ENGINE']  # Debe ser postgresql

# 5. Verificar HTTPS
curl -I https://tudominio.com  # Debe responder con 200 OK
```

## ⚠️ NUNCA Hacer en Producción

- ❌ Usar DEBUG=True
- ❌ Exponer SECRET_KEY en el código
- ❌ Usar contraseñas débiles
- ❌ Correr como root
- ❌ Permitir listado de directorios
- ❌ Usar SQLite en producción con tráfico alto
- ❌ Commit de archivos .env al repositorio
- ❌ Permitir acceso directo a la base de datos desde internet

## 📝 Archivo .env de Producción - Ejemplo

```env
SECRET_KEY=nueva-clave-super-segura-generada-aleatoriamente
ENVIRONMENT=production
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com

DB_ENGINE=django.db.backends.postgresql
DB_NAME=escuela_db
DB_USER=escuela_user
DB_PASSWORD=password_super_seguro_y_largo_123
DB_HOST=localhost
DB_PORT=5432

EMAIL_HOST_USER=noreply@tudominio.com
EMAIL_HOST_PASSWORD=app_password_de_gmail_o_smtp
```

## 🚨 En Caso de Exposición de Credenciales

Si accidentalmente expusiste credenciales:

1. **Inmediatamente cambiar:**
   - SECRET_KEY (generar nueva)
   - Contraseñas de base de datos
   - Tokens de email
   
2. **Rotar credenciales:**
   ```bash
   # Generar nueva SECRET_KEY
   python scripts/generar_secret_key.py
   
   # Cambiar password de PostgreSQL
   sudo -u postgres psql
   ALTER USER escuela_user WITH PASSWORD 'nueva_password';
   ```

3. **Revisar logs** por accesos no autorizados

4. **Actualizar .env** y reiniciar servicios
   ```bash
   sudo systemctl restart escuela
   ```

## 📞 Contacto de Emergencia

En caso de incidente de seguridad, contactar inmediatamente al administrador del sistema.

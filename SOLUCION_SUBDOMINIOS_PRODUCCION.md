# 🔧 Solución: Subdominios no funcionan en Producción EC2

## 🎯 Problema
El subdominio `boutique.misventasflash.com` devuelve error 404 en producción (EC2).

---

## 🔍 Diagnóstico Rápido

### 1. Ejecutar script de diagnóstico (local o producción):
```powershell
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Ejecutar diagnóstico
python diagnosticar_subdominios.py
```

Esto te mostrará:
- ✅ Configuración de ALLOWED_HOSTS
- ✅ Tenants registrados
- ✅ Dominios configurados
- ✅ Schema de PostgreSQL
- ✅ Estado del tenant específico

---

## 🛠️ Soluciones por Problema

### Problema 1: Tenant no existe en base de datos de producción

**Síntoma:**
- Diagnóstico muestra "Dominio NO ENCONTRADO"
- No aparece en lista de tenants

**Solución:**
```powershell
# En tu máquina local (conectado a BD de producción)
python crear_tenant_boutique.py
```

O conectándote a tu EC2:
```bash
# Conectar a EC2
ssh -i tu-clave.pem ubuntu@tu-ip-ec2

# Activar entorno
cd /home/ubuntu/Ventas
source venv/bin/activate

# Crear tenant
python crear_tenant_boutique.py
```

---

### Problema 2: ALLOWED_HOSTS no permite subdominios

**Síntoma:**
- Diagnóstico muestra "ALLOWED_HOSTS NO permite subdominios"

**Solución en EC2:**
```bash
# Editar .env en producción
nano /home/ubuntu/Ventas/.env

# Asegúrate que tenga (con el punto al inicio):
ALLOWED_HOSTS=misventasflash.com,.misventasflash.com
# O con wildcard:
ALLOWED_HOSTS=misventasflash.com,*.misventasflash.com

# También CSRF:
CSRF_TRUSTED_ORIGINS=https://misventasflash.com,https://*.misventasflash.com

# Guardar (Ctrl+O, Enter, Ctrl+X)

# Reiniciar gunicorn
sudo systemctl restart gunicorn
```

---

### Problema 3: Dominio no asociado al tenant

**Síntoma:**
- Tenant existe pero dominio no está asociado
- Diagnóstico muestra "Sin dominios configurados"

**Solución:**
```python
# En shell de Django (producción)
python manage.py shell

# Ejecutar:
from ventasweb.tenant_models import Client, Domain

tenant = Client.objects.get(schema_name='boutique')
Domain.objects.create(
    domain='boutique.misventasflash.com',
    tenant=tenant,
    is_primary=True
)
exit()
```

---

### Problema 4: Tenant inactivo

**Síntoma:**
- Diagnóstico muestra "Tenant activo: ❌ No"

**Solución:**
```python
# En shell de Django (producción)
python manage.py shell

# Ejecutar:
from ventasweb.tenant_models import Client
tenant = Client.objects.get(schema_name='boutique')
tenant.activo = True
tenant.save()
exit()
```

---

### Problema 5: DNS no configurado

**Síntoma:**
- `nslookup boutique.misventasflash.com` no resuelve a tu IP

**Solución:**

#### Si usas Route 53 (AWS):
1. Ve a Route 53 en AWS Console
2. Selecciona tu zona hosteada `misventasflash.com`
3. Crea un registro:
   - **Tipo:** A o CNAME
   - **Nombre:** `*.misventasflash.com` (wildcard)
   - **Valor:** IP de tu EC2 o dominio
   - **TTL:** 300

#### Si usas otro proveedor DNS:
- Crea un registro wildcard: `*.misventasflash.com` → IP de EC2

#### Verificar DNS:
```powershell
# En tu máquina local
nslookup boutique.misventasflash.com

# Debe devolver la IP de tu EC2
```

---

### Problema 6: Certificado SSL no soporta wildcard

**Síntoma:**
- HTTPS muestra error de certificado

**Solución con Certbot (Let's Encrypt):**
```bash
# Conectar a EC2
sudo certbot --nginx -d misventasflash.com -d *.misventasflash.com

# Nota: Para wildcard necesitas validación DNS
# Certbot te dará instrucciones para crear registro TXT en DNS
```

**Alternativa - Certificado por subdominio:**
```bash
# Si wildcard no funciona, agregar cada subdominio:
sudo certbot --nginx -d misventasflash.com -d boutique.misventasflash.com
```

---

### Problema 7: Nginx no pasa el header Host

**Síntoma:**
- Logs muestran que Django recibe dominio incorrecto

**Solución:**

Editar configuración de Nginx:
```bash
sudo nano /etc/nginx/sites-available/ventasflash
```

Verificar que tenga:
```nginx
server {
    listen 80;
    server_name misventasflash.com *.misventasflash.com;

    location / {
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header Host $host;              # ← IMPORTANTE
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Reiniciar Nginx:
```bash
sudo nginx -t
sudo systemctl restart nginx
```

---

## ✅ Checklist Completo para Subdominios en Producción

- [ ] **1. Tenant creado en BD**
  ```bash
  python diagnosticar_subdominios.py
  # Debe aparecer tenant 'boutique'
  ```

- [ ] **2. Dominio asociado al tenant**
  ```bash
  python diagnosticar_subdominios.py
  # Debe mostrar: boutique.misventasflash.com → tenant boutique
  ```

- [ ] **3. Tenant activo**
  ```bash
  # activo=True en base de datos
  ```

- [ ] **4. ALLOWED_HOSTS correcto**
  ```bash
  # En .env de producción:
  ALLOWED_HOSTS=misventasflash.com,.misventasflash.com
  ```

- [ ] **5. DNS configurado**
  ```bash
  nslookup boutique.misventasflash.com
  # Debe resolver a IP de EC2
  ```

- [ ] **6. Nginx configurado**
  ```bash
  # server_name debe incluir *.misventasflash.com
  # proxy_set_header Host $host;
  ```

- [ ] **7. SSL con wildcard o por subdominio**
  ```bash
  sudo certbot certificates
  # Debe incluir *.misventasflash.com o boutique.misventasflash.com
  ```

- [ ] **8. Servicios reiniciados**
  ```bash
  sudo systemctl restart gunicorn
  sudo systemctl restart nginx
  ```

---

## 🧪 Probar Localmente (antes de producción)

```powershell
# 1. Agregar en C:\Windows\System32\drivers\etc\hosts
127.0.0.1 boutique.localhost
127.0.0.1 boutique.misventasflash.com

# 2. Activar venv y correr servidor
.\.venv\Scripts\Activate.ps1
python manage.py runserver

# 3. Probar en navegador
http://boutique.localhost:8000
```

---

## 📞 Comandos Útiles en EC2

```bash
# Ver logs de gunicorn
sudo journalctl -u gunicorn -f

# Ver logs de nginx
sudo tail -f /var/log/nginx/error.log

# Reiniciar servicios
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Verificar estado
sudo systemctl status gunicorn
sudo systemctl status nginx

# Ver variables de entorno
cd /home/ubuntu/Ventas
cat .env | grep ALLOWED_HOSTS
```

---

## 🎯 Proceso Recomendado

### Desde tu máquina Windows (con acceso a BD de producción):

1. **Diagnosticar:**
   ```powershell
   python diagnosticar_subdominios.py
   ```

2. **Crear tenant si no existe:**
   ```powershell
   python crear_tenant_boutique.py
   ```

3. **Conectar a EC2 y verificar configuración:**
   ```bash
   ssh -i tu-clave.pem ubuntu@tu-ip-ec2
   cd /home/ubuntu/Ventas
   cat .env | grep ALLOWED_HOSTS
   ```

4. **Si ALLOWED_HOSTS está mal, corregir:**
   ```bash
   nano .env
   # Cambiar a: ALLOWED_HOSTS=misventasflash.com,.misventasflash.com
   sudo systemctl restart gunicorn
   ```

5. **Verificar DNS:**
   ```powershell
   nslookup boutique.misventasflash.com
   ```

6. **Probar acceso:**
   ```
   https://boutique.misventasflash.com
   ```

---

## 🆘 Si Nada Funciona

1. **Ver logs en tiempo real:**
   ```bash
   # Terminal 1: Logs de Django/Gunicorn
   sudo journalctl -u gunicorn -f
   
   # Terminal 2: Logs de Nginx
   sudo tail -f /var/log/nginx/error.log
   ```

2. **Intentar acceso y observar logs**

3. **Revisar qué dominio recibe Django:**
   ```python
   # Agregar temporalmente en settings.py o middleware
   print(f"HOST RECIBIDO: {request.get_host()}")
   ```

---

## 📚 Archivos Importantes

- **Producción EC2:**
  - `/home/ubuntu/Ventas/.env` - Variables de entorno
  - `/etc/nginx/sites-available/ventasflash` - Config Nginx
  - `/etc/systemd/system/gunicorn.service` - Servicio gunicorn

- **Local:**
  - `VentasSys/settings.py` - Configuración Django
  - `diagnosticar_subdominios.py` - Script diagnóstico
  - `crear_tenant_boutique.py` - Script creación tenant

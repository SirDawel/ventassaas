#!/bin/bash
# Script de despliegue para Django en EC2

echo "🚀 Iniciando despliegue..."

# 1. Ir al directorio del proyecto
cd /home/ubuntu/Escuela  # Ajusta esta ruta según tu EC2

# 2. Activar entorno virtual
source venv/bin/activate  # o .venv/bin/activate según tu configuración

# 3. Hacer pull de los últimos cambios
echo "📥 Descargando cambios..."
git pull origin main

# 4. Instalar/actualizar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# 5. Aplicar migraciones
echo "🗄️  Aplicando migraciones..."
python manage.py migrate

# 6. Recolectar archivos estáticos (CRÍTICO para cambios en templates con CSS/JS)
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# 7. Reiniciar servicio de aplicación (gunicorn/uwsgi)
echo "🔄 Reiniciando aplicación..."
# Opción A: Si usas gunicorn con systemd
sudo systemctl restart gunicorn

# Opción B: Si usas supervisor
# sudo supervisorctl restart escuela

# Opción C: Si usas uwsgi
# sudo systemctl restart uwsgi

# 8. Reiniciar nginx
echo "🔄 Reiniciando nginx..."
sudo systemctl restart nginx

# 9. Limpiar caché de Python
echo "🧹 Limpiando caché..."
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "✅ ¡Despliegue completado!"
echo "💡 Si los cambios aún no aparecen, intenta:"
echo "   - Ctrl + Shift + R (forzar recarga sin caché en navegador)"
echo "   - Abrir en ventana privada/incógnito"

#!/bin/bash
# Script para instalar y configurar servicios de Celery en systemd
# Ejecutar como: sudo bash instalar_celery_services.sh

set -e  # Salir si hay error

echo "=============================================="
echo "INSTALACIÓN DE SERVICIOS CELERY"
echo "=============================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Este script debe ejecutarse como root (usa sudo)${NC}"
    exit 1
fi

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Error: No se encuentra manage.py${NC}"
    echo "Ejecuta este script desde /var/www/ventas"
    exit 1
fi

# Paso 1: Crear directorios necesarios
echo -e "${YELLOW}[1/6] Creando directorios para logs y PIDs...${NC}"
mkdir -p /var/log/celery
mkdir -p /var/run/celery
chown -R ubuntu:ubuntu /var/log/celery
chown -R ubuntu:ubuntu /var/run/celery
echo -e "${GREEN}✅ Directorios creados${NC}"

# Paso 2: Copiar archivos de servicio
echo ""
echo -e "${YELLOW}[2/6] Copiando archivos de servicio a systemd...${NC}"
cp celery-worker.service /etc/systemd/system/
cp celery-beat.service /etc/systemd/system/
echo -e "${GREEN}✅ Archivos copiados${NC}"

# Paso 3: Recargar systemd
echo ""
echo -e "${YELLOW}[3/6] Recargando systemd daemon...${NC}"
systemctl daemon-reload
echo -e "${GREEN}✅ Systemd recargado${NC}"

# Paso 4: Habilitar servicios para inicio automático
echo ""
echo -e "${YELLOW}[4/6] Habilitando servicios para inicio automático...${NC}"
systemctl enable celery-worker.service
systemctl enable celery-beat.service
echo -e "${GREEN}✅ Servicios habilitados${NC}"

# Paso 5: Iniciar servicios
echo ""
echo -e "${YELLOW}[5/6] Iniciando servicios...${NC}"
systemctl start celery-worker.service
sleep 2
systemctl start celery-beat.service
sleep 2
echo -e "${GREEN}✅ Servicios iniciados${NC}"

# Paso 6: Verificar estado
echo ""
echo -e "${YELLOW}[6/6] Verificando estado de los servicios...${NC}"
echo ""

if systemctl is-active --quiet celery-worker; then
    echo -e "${GREEN}✅ celery-worker: ACTIVO${NC}"
else
    echo -e "${RED}❌ celery-worker: INACTIVO${NC}"
    systemctl status celery-worker --no-pager -l
fi

if systemctl is-active --quiet celery-beat; then
    echo -e "${GREEN}✅ celery-beat: ACTIVO${NC}"
else
    echo -e "${RED}❌ celery-beat: INACTIVO${NC}"
    systemctl status celery-beat --no-pager -l
fi

echo ""
echo "=============================================="
echo -e "${GREEN}✅ INSTALACIÓN COMPLETADA${NC}"
echo "=============================================="
echo ""
echo "Comandos útiles:"
echo "  sudo systemctl status celery-worker"
echo "  sudo systemctl status celery-beat"
echo "  sudo systemctl restart celery-worker"
echo "  sudo systemctl restart celery-beat"
echo "  sudo journalctl -u celery-worker -f"
echo "  sudo journalctl -u celery-beat -f"
echo ""
echo "Logs:"
echo "  /var/log/celery/worker.log"
echo "  /var/log/celery/beat.log"
echo ""

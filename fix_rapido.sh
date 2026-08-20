#!/bin/bash
# Script de solución rápida para ejecutar en el servidor EC2
# Uso: bash fix_rapido.sh

echo "=============================================="
echo "SOLUCIÓN RÁPIDA - SISTEMA DE VENTAS"
echo "=============================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Error: No se encuentra manage.py${NC}"
    echo "Ejecuta este script desde /var/www/ventas"
    exit 1
fi

# Paso 1: Activar entorno virtual
echo -e "${YELLOW}[1/5] Activando entorno virtual...${NC}"
source .venv/bin/activate
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Entorno virtual activado${NC}"
else
    echo -e "${RED}❌ Error al activar entorno virtual${NC}"
    exit 1
fi

# Paso 2: Limpiar tenants corruptos
echo ""
echo -e "${YELLOW}[2/5] Detectando tenants corruptos...${NC}"
python limpiar_tenants_corruptos.py <<EOF
ELIMINAR
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Tenants corruptos limpiados${NC}"
else
    echo -e "${RED}❌ Error al limpiar tenants${NC}"
    echo "Intenta ejecutar manualmente: python limpiar_tenants_corruptos.py"
    exit 1
fi

# Paso 3: Ejecutar migraciones
echo ""
echo -e "${YELLOW}[3/5] Ejecutando migraciones...${NC}"
python manage.py migrate_schemas
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migraciones completadas${NC}"
else
    echo -e "${RED}❌ Error en migraciones${NC}"
    exit 1
fi

# Paso 4: Reiniciar servicios
echo ""
echo -e "${YELLOW}[4/5] Reiniciando servicios...${NC}"
sudo systemctl restart gunicorn
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
sudo systemctl restart nginx

sleep 2

# Verificar estado
if systemctl is-active --quiet gunicorn; then
    echo -e "${GREEN}✅ Gunicorn: Activo${NC}"
else
    echo -e "${RED}❌ Gunicorn: Inactivo${NC}"
fi

if systemctl is-active --quiet celery-worker; then
    echo -e "${GREEN}✅ Celery Worker: Activo${NC}"
else
    echo -e "${RED}❌ Celery Worker: Inactivo${NC}"
fi

if systemctl is-active --quiet celery-beat; then
    echo -e "${GREEN}✅ Celery Beat: Activo${NC}"
else
    echo -e "${RED}❌ Celery Beat: Inactivo${NC}"
fi

# Paso 5: Verificación final
echo ""
echo -e "${YELLOW}[5/5] Verificación final...${NC}"
python listar_tenants.py

echo ""
echo "=============================================="
echo -e "${GREEN}✅ SOLUCIÓN COMPLETADA${NC}"
echo "=============================================="
echo ""
echo "Próximos pasos:"
echo "1. Configura Gmail SMTP en el archivo .env"
echo "2. Prueba el registro de empresa en:"
echo "   https://misventasflash.com/registrar-empresa/"
echo ""
echo "Para ver logs en tiempo real:"
echo "  sudo journalctl -u gunicorn -f"
echo "  sudo journalctl -u celery-worker -f"
echo ""

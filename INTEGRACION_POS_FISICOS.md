# Sistema de Pagos POS Físicos - Integración Cardnet/Azul

Este documento explica cómo integrar tu sistema escolar con dispositivos POS físicos (Verifone, PAX, etc.) para recibir pagos con tarjeta de manera automática.

## 📋 ¿Qué hace este sistema?

Cuando un estudiante pasa su tarjeta en un POS físico:

1. **El POS procesa el pago** con Cardnet, Azul u otro proveedor
2. **El proveedor envía una notificación (webhook)** a tu sistema
3. **El sistema identifica automáticamente** al estudiante
4. **Busca facturas pendientes** del estudiante
5. **Aplica el pago** a las facturas más antiguas primero
6. **Marca la factura como pagada** en la base de datos
7. **Imprime el recibo** en la impresora térmica (opcional)
8. **Envía la factura por email** al estudiante (opcional)

---

## 🚀 Configuración Paso a Paso

### 1. Obtener Credenciales del Proveedor

#### Cardnet
1. Contacta a Cardnet: https://www.cardnet.com.do/comercios
2. Solicita acceso a su API REST
3. Te darán:
   - `API_KEY`
   - `MERCHANT_ID`
   - `WEBHOOK_SECRET`
   - Acceso a un terminal de pruebas

#### Azul
1. Contacta a Azul: https://www.azul.com.do/comercios
2. Solicita acceso a su API
3. Te darán:
   - `USER` (usuario)
   - `PASSWORD`
   - `STORE_ID`
   - `WEBHOOK_SECRET`
   - Acceso a un terminal de pruebas

---

### 2. Configurar Variables de Entorno

Copia el archivo `.env.pos.example` a tu archivo `.env`:

```bash
# Copiar configuración de ejemplo
cat .env.pos.example >> .env
```

Edita el archivo `.env` con tus credenciales reales:

```bash
# Proveedor principal
PAYMENT_PROVIDER=cardnet

# Credenciales Cardnet
CARDNET_API_KEY=sk_live_ABC123XYZ
CARDNET_MERCHANT_ID=12345
CARDNET_WEBHOOK_SECRET=whsec_ABC123XYZ
CARDNET_API_URL=https://api.cardnet.com.do/api

# (O para Azul)
AZUL_USER=mi_usuario
AZUL_PASSWORD=mi_password_secreto
AZUL_STORE_ID=my_store_123
AZUL_WEBHOOK_SECRET=whsec_XYZ789
AZUL_API_URL=https://pagos.azul.com.do

# Habilitar impresión automática
AUTO_PRINT_INVOICES=True
POS_PRINTER_ENABLED=True

# Habilitar envío por email
AUTO_EMAIL_INVOICES=True
```

---

### 3. Ejecutar Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

Esto creará dos nuevas tablas en la base de datos:
- `TransaccionPOS`: Registra todas las transacciones del POS
- `TerminalEstudiante`: Asocia terminales con estudiantes

---

### 4. Configurar Webhooks en el Proveedor

#### URL del Webhook

Tu sistema necesita estar accesible desde Internet con **HTTPS** (no HTTP).

- **Para Cardnet:** `https://tu-dominio.com/webhooks/pos/cardnet/`
- **Para Azul:** `https://tu-dominio.com/webhooks/pos/azul/`

Ejemplos:
```
https://escuela.edu.do/webhooks/pos/cardnet/
https://www.misistemasescolar.com/webhooks/pos/azul/
```

#### Pasos en el Portal del Proveedor

1. Inicia sesión en el portal de Cardnet/Azul
2. Ve a **Configuración > Webhooks** (o similar)
3. Añade un nuevo webhook
4. Pega la URL de arriba
5. Selecciona eventos: `transaction.approved`, `payment.successful`, etc.
6. Guarda y copia el `WEBHOOK_SECRET`
7. Pega el `WEBHOOK_SECRET` en tu archivo `.env`

---

### 5. Asociar Terminales con Estudiantes

Hay **dos formas** de identificar al estudiante cuando paga:

#### Opción A: Enviar la cédula desde el POS (Recomendado)

Configura en el portal de Cardnet/Azul que el terminal envíe la cédula del estudiante  
en un campo personalizado (`custom_field_1` o `metadata`).

El cajero deberá:
1. Preguntarle la cédula al estudiante
2. Ingresarla en el POS antes de procesar el pago
3. El POS envía la cédula al webhook automáticamente

#### Opción B: Asociar cada terminal a un estudiante específico

Si cada estudiante tiene su propio terminal (ej. cafetería escolar), puedes asociar  
el `terminal_id` con el estudiante en Django Admin:

1. Ve a `/admin/escuelaweb/terminalestudiante/`
2. Click en "Añadir Terminal-Estudiante"
3. Ingresa:
   - `Terminal ID`: Ej. `VF-001`, `PAX-123`
   - `Estudiante`: Selecciona el estudiante
   - `Proveedor`: Cardnet o Azul
   - `Activo`: ✓
4. Guardar

Cuando ese terminal procese un pago, se asociará automáticamente a ese estudiante.

---

### 6. Configurar Impresora Térmica (Opcional)

#### Instalar librería

```bash
pip install python-escpos
pip install reportlab  # Para PDFs
```

#### Configurar en .env

**Impresora en red (Ethernet):**
```bash
POS_PRINTER_TYPE=network
POS_PRINTER_IP=192.168.1.100
POS_PRINTER_PORT=9100
```

**Impresora USB:**
```bash
POS_PRINTER_TYPE=usb
POS_PRINTER_VENDOR_ID=0x04b8   # Epson: 0x04b8
POS_PRINTER_PRODUCT_ID=0x0e15  # Modelo TM-T88V
```

Para encontrar tu `vendor_id` y `product_id`:
```bash
# Linux/Mac
lsusb

# Windows (PowerShell)
Get-PnpDevice -Class Printer
```

**Impresión a archivo (para pruebas):**
```bash
POS_PRINTER_TYPE=file
POS_PRINTER_PATH=C:/tmp/receipt.txt
```

---

## 🧪 Probar el Sistema

### 1. Prueba con Terminal de Sandbox

1. Usa el terminal de pruebas que te dio Cardnet/Azul
2. Procesa un pago con tarjeta de prueba
3. Verifica en Django Admin que se creó una `TransaccionPOS`
4. Verifica que la factura del estudiante se marcó como pagada

### 2. Probar el Webhook Manualmente

Puedes probar enviando un POST manual:

```bash
curl -X POST https://tu-dominio.com/webhooks/pos/cardnet/ \
  -H "Content-Type: application/json" \
  -H "X-Cardnet-Signature: tu_firma_aqui" \
  -d '{
    "transaction_id": "TXN123456",
    "terminal_id": "VF-001",
    "amount": 5000.00,
    "status": "approved",
    "reference_number": "REF789",
    "card_last_4": "1234",
    "card_type": "Visa",
    "transaction_date": "2026-04-12T10:30:00",
    "custom_field_1": "402-1234567-8"
  }'
```

### 3. Verificar Logs

```bash
# Ver logs de transacciones
tail -f logs/security.log

# O en Django shell
python manage.py shell
>>> from escuelaweb.models import TransaccionPOS
>>> TransaccionPOS.objects.all()
```

---

## 📊 Monitoreo y Administración

### Panel de Admin

Ve a `/admin/escuelaweb/transaccionpos/` para ver todas las transacciones POS.

Ahí puedes:
- Ver transacciones procesadas exitosamente
- Revisar transacciones pendientes (sin estudiante identificado)
- Asociar manualmente transacciones a estudiantes
- Ver detalles completos del webhook

### Estados de Transacciones

- **procesado**: Pago aplicado exitosamente a la factura
- **pendiente_revision**: No se pudo identificar al estudiante automáticamente
- **sin_factura**: Estudiante identificado pero no tiene facturas pendientes
- **error**: Ocurrió un error al procesar
- **rechazado**: El pago fue rechazado por el banco

---

## 🔒 Seguridad

### Validación de Webhooks

El sistema valida que los webhooks realmente vienen de Cardnet/Azul verificando la firma HMAC.

**NUNCA** compartas tu `WEBHOOK_SECRET` públicamente.

### HTTPS Obligatorio

Los proveedores **solo envían webhooks a URLs HTTPS**, no HTTP.

Para desarrollo local, usa:
- **ngrok**: `ngrok http 8000`
- **localtunnel**: `lt --port 8000`

---

## 🛠️ Solución de Problemas

### "Webhook con firma inválida"

- Verifica que el `WEBHOOK_SECRET` en `.env` sea correcto
- Asegúrate de que el proveedor esté enviando el header `X-Cardnet-Signature` o `X-Azul-Signature`

### "Transacción duplicada"

- El sistema previene duplicados automáticamente
- Si recibes esta respuesta, el pago ya fue procesado

### "Estudiante no identificado"

- Verifica que la cédula enviada exista en la base de datos
- Revisa `custom_field_1` en el webhook
- O configura una asociación `TerminalEstudiante`

### "Error imprimiendo factura"

- Verifica que la impresora esté conectada y encendida
- Comprueba la IP/puerto o USB vendor/product ID
- Prueba con `POS_PRINTER_TYPE=file` primero

---

## 📞 Soporte

Para problemas técnicos:
1. Revisa los logs en `logs/security.log`
2. Consulta la documentación del proveedor (Cardnet/Azul)
3. Verifica la tabla `TransaccionPOS` en el admin

---

## 🎯 Flujo Completo

```
┌─────────────────┐
│  Estudiante     │
│  pasa tarjeta   │
│  en POS         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Terminal POS   │
│  (Verifone)     │
│  procesa pago   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Cardnet/Azul   │
│  aprueba pago   │
└────────┬────────┘
         │
         ▼ (webhook)
┌─────────────────┐
│  TU SISTEMA     │
│  recibe         │
│  notificación   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Identifica     │
│  estudiante     │
│  por cédula     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Busca facturas │
│  pendientes     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Aplica pago    │
│  marca factura  │
│  como pagada    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Imprime recibo │
│  y envía email  │
└─────────────────┘
```

---

## ✅ Checklist de Implementación

- [ ] Obtener credenciales de Cardnet/Azul
- [ ] Configurar `.env` con credenciales
- [ ] Ejecutar migraciones (`makemigrations` + `migrate`)
- [ ] Configurar webhook en portal de Cardnet/Azul
- [ ] Probar con terminal de sandbox
- [ ] Asociar terminales con estudiantes (si aplica)
- [ ] Configurar impresora térmica (opcional)
- [ ] Configurar email automático (opcional)
- [ ] Probar en producción con pago real
- [ ] Monitorear logs y transacciones

---

Con esta integración, tu sistema podrá recibir pagos físicos con tarjeta  
y registrarlos automáticamente sin intervención manual. 🎉

# 🎯 GUÍA DE CONFIGURACIÓN PASO A PASO

## ✅ ESTADO ACTUAL

**YA HECHO:**
- ✅ Código backend implementado
- ✅ Modelos creados y migrados
- ✅ Webhooks configurados en Django
- ✅ Configuración añadida a tu `.env`

**PENDIENTE:**
- ⏳ Obtener credenciales de Cardnet o Azul
- ⏳ Configurar webhook en el portal del proveedor
- ⏳ Probar el sistema

---

## 📞 PASO 1: Decidir qué proveedor usar

### ¿Cardnet o Azul?

**Ambos son bancos dominicanos** que ofrecen servicios de POS y pagos en línea.

#### CARDNET
- **Contacto:** (809) 566-3636
- **Web:** https://www.cardnet.com.do/comercios
- **Email:** comercios@cardnet.com.do
- **Terminales:** Verifone, PAX
- **Ventajas:** Amplia red, buen soporte

#### AZUL
- **Contacto:** (809) 563-2985
- **Web:** https://www.azul.com.do/comercios
- **Email:** comercios@azul.com.do
- **Terminales:** Verifone, PAX, Ingenico
- **Ventajas:** Rápida integración, buena API

### ¿Cuál elegir?

1. **¿Ya tienes un terminal POS?** → Usa el proveedor de ese terminal
2. **¿Estás empezando?** → Contacta a ambos y compara:
   - Comisiones por transacción
   - Costo de los terminales
   - Tiempo de activación
   - Calidad del soporte técnico

---

## 📋 PASO 2: Solicitar acceso a la API

### ¿Qué pedir cuando contactes?

Llama o envía email diciendo:

> "Hola, somos una institución educativa y queremos integrar pagos con tarjeta  
> en nuestro sistema escolar. Necesitamos:
> 
> 1. **Acceso a su API REST** para integración web
> 2. **Credenciales de sandbox/pruebas** para desarrollo
> 3. **Terminal de pruebas** (si es posible)
> 4. **Documentación de su API**
> 5. **Configuración de webhooks**
> 
> Nuestro lenguaje de desarrollo es Python/Django."

### ¿Qué te van a dar?

Para **Cardnet**, te darán:
```
CARDNET_API_KEY=sk_test_ABC123XYZ...
CARDNET_MERCHANT_ID=12345
CARDNET_WEBHOOK_SECRET=whsec_ABC123...
URL API Sandbox: https://sandbox.cardnet.com.do/api
```

Para **Azul**, te darán:
```
AZUL_USER=mi_usuario_comercio
AZUL_PASSWORD=mi_password_secreto
AZUL_STORE_ID=STORE12345
AZUL_WEBHOOK_SECRET=whsec_XYZ789...
URL API Sandbox: https://sandbox.azul.com.do
```

---

## 🔧 PASO 3: Configurar credenciales en tu `.env`

Una vez que tengas las credenciales, edita el archivo `.env`:

### Para Cardnet:

```bash
PAYMENT_PROVIDER=cardnet

CARDNET_API_KEY=sk_test_ABC123XYZ...      # ← Pega aquí tu API Key
CARDNET_MERCHANT_ID=12345                 # ← Pega aquí tu Merchant ID
CARDNET_WEBHOOK_SECRET=whsec_ABC123...    # ← Pega aquí tu Webhook Secret
CARDNET_API_URL=https://sandbox.cardnet.com.do/api   # ← Sandbox para pruebas
```

### Para Azul:

```bash
PAYMENT_PROVIDER=azul

AZUL_USER=mi_usuario_comercio             # ← Pega aquí tu usuario
AZUL_PASSWORD=mi_password_secreto         # ← Pega aquí tu password
AZUL_STORE_ID=STORE12345                  # ← Pega aquí tu Store ID
AZUL_WEBHOOK_SECRET=whsec_XYZ789...       # ← Pega aquí tu Webhook Secret
AZUL_API_URL=https://sandbox.azul.com.do  # ← Sandbox para pruebas
```

---

## 🌐 PASO 4: Configurar el webhook en el portal del proveedor

### ¿Qué es un webhook?

Es una URL donde Cardnet/Azul **envía una notificación automática** cuando  
se procesa un pago en el POS físico.

### ¿Cuál es tu URL de webhook?

Para desarrollo local (usando **ngrok** o **localtunnel**):
```
https://tu-subdominio.ngrok.io/webhooks/pos/cardnet/
```

Para producción (tu dominio real):
```
https://www.tuescuela.edu.do/webhooks/pos/cardnet/
```

### Pasos para configurar:

#### Si usas **Cardnet**:
1. Inicia sesión en: https://portal.cardnet.com.do
2. Ve a **Configuración → Webhooks** (o similar)
3. Haz clic en **Añadir nuevo webhook**
4. Pega tu URL: `https://tu-dominio.com/webhooks/pos/cardnet/`
5. Selecciona eventos:
   - ✅ `transaction.approved`
   - ✅ `transaction.completed`
   - ✅ `payment.successful`
6. Guarda
7. **Copia el WEBHOOK_SECRET** que te den y pégalo en tu `.env`

#### Si usas **Azul**:
1. Inicia sesión en: https://portal.azul.com.do
2. Ve a **Integraciones → Webhooks**
3. Haz clic en **Crear webhook**
4. Pega tu URL: `https://tu-dominio.com/webhooks/pos/azul/`
5. Selecciona eventos:
   - ✅ `Payment Successful`
   - ✅ `Transaction Approved`
6. Guarda
7. **Copia el WEBHOOK_SECRET** y pégalo en tu `.env`

---

## 🧪 PASO 5: Probar ANTES de tener credenciales reales

### Opción 1: Probar con el script de prueba

Mientras esperas las credenciales, puedes probar localmente:

```bash
# 1. Edita el script
notepad scripts\test_webhook_pos.py

# 2. Cambia estas líneas:
WEBHOOK_SECRET = "test_secret_123"  # Un secreto de prueba
"custom_field_1": "402-1234567-8"   # Cédula de un estudiante REAL de tu BD

# 3. Cambia en tu .env temporalmente:
CARDNET_WEBHOOK_SECRET=test_secret_123

# 4. Inicia el servidor
.\.venv\Scripts\Activate.ps1
python manage.py runserver

# 5. En otra terminal, ejecuta el script
python scripts\test_webhook_pos.py cardnet
```

### Opción 2: Probar con terminales de sandbox

Cuando tengas las credenciales sandbox, el proveedor te dará:
- Un **terminal de pruebas** (físico o simulador)
- **Tarjetas de prueba** (números específicos que siempre aprueban)

Ejemplo de tarjeta de prueba Cardnet:
```
Número: 4111 1111 1111 1111
Fecha: 12/28
CVV: 123
```

---

## 🖨️ PASO 6: Configurar impresora (OPCIONAL)

Si NO tienes impresora térmica, déjalo así en `.env`:
```bash
AUTO_PRINT_INVOICES=False
POS_PRINTER_ENABLED=False
POS_PRINTER_TYPE=file
POS_PRINTER_PATH=E:/Escuela_backup/Escuela/logs/test_receipt.txt
```

Los recibos se guardarán en `logs/test_receipt.txt` para que los veas.

### Si SÍ tienes impresora térmica:

#### Para impresora USB:

1. Encuentra los IDs en PowerShell:
```powershell
Get-PnpDevice -Class Printer | Format-List
```

Busca `VendorID` y `ProductID`, ejemplo:
```
VID_04B8&PID_0E15  →  Vendor: 0x04b8, Product: 0x0e15
```

2. Configura en `.env`:
```bash
POS_PRINTER_ENABLED=True
POS_PRINTER_TYPE=usb
POS_PRINTER_VENDOR_ID=0x04b8
POS_PRINTER_PRODUCT_ID=0x0e15
```

3. Instala librería:
```bash
pip install python-escpos
```

#### Para impresora en red (Ethernet):

1. Encuentra la IP de la impresora (imprime página de configuración)

2. Configura en `.env`:
```bash
POS_PRINTER_ENABLED=True
POS_PRINTER_TYPE=network
POS_PRINTER_IP=192.168.1.100
POS_PRINTER_PORT=9100
```

---

## 👥 PASO 7: Asociar terminales con estudiantes

Hay **dos formas** de identificar al estudiante cuando paga:

### Opción A: El cajero pregunta la cédula (RECOMENDADO)

1. Configura en el portal de Cardnet/Azul que el terminal envíe la cédula  
   en el campo `custom_field_1` o `metadata`

2. El flujo será:
   - Cajero pregunta: "¿Cuál es tu cédula?"
   - Estudiante: "402-1234567-8"
   - Cajero ingresa la cédula en el POS antes de procesar
   - El POS la envía al webhook automáticamente
   - Tu sistema identifica al estudiante

### Opción B: Cada estudiante tiene su propio terminal

Si cada estudiante tiene su propio terminal (ej. cafetería escolar):

1. Ve al Admin: http://127.0.0.1:8000/admin/escuelaweb/terminalestudiante/
2. Click **"Añadir Terminal-Estudiante"**
3. Configura:
   - **Terminal ID:** `VF-001` (el ID del terminal físico)
   - **Estudiante:** Selecciona el estudiante
   - **Proveedor:** Cardnet o Azul
   - **Activo:** ✅
4. Guardar

Ahora cuando el terminal `VF-001` procese un pago, se asociará automáticamente  
a ese estudiante.

---

## ✅ PASO 8: Verificar que todo funciona

### 1. Verificar configuración:
```bash
.\.venv\Scripts\Activate.ps1
python manage.py check
```

Debería decir: `System check identified no issues`

### 2. Verificar que las URLs están activas:
```bash
python manage.py show_urls | Select-String "webhook"
```

Debería mostrar:
```
/webhooks/pos/cardnet/
/webhooks/pos/azul/
```

### 3. Ver los modelos en el admin:
```
http://127.0.0.1:8000/admin/escuelaweb/transaccionpos/
http://127.0.0.1:8000/admin/escuelaweb/terminalestudiante/
```

---

## 🚨 TROUBLESHOOTING

### "No tengo HTTPS para el webhook"

**Para desarrollo local**, usa ngrok:

```bash
# 1. Descarga ngrok: https://ngrok.com/download

# 2. Ejecuta:
ngrok http 8000

# 3. Te dará una URL como:
https://abc123.ngrok.io

# 4. Tu webhook será:
https://abc123.ngrok.io/webhooks/pos/cardnet/
```

### "No sé qué credenciales poner"

Mientras no tengas credenciales reales, deja en `.env`:
```bash
CARDNET_API_KEY=PENDIENTE_SOLICITAR
CARDNET_MERCHANT_ID=PENDIENTE_SOLICITAR
CARDNET_WEBHOOK_SECRET=test_secret_123  # Para pruebas locales
```

Y usa el script `test_webhook_pos.py` para simular pagos.

### "Error: Webhook con firma inválida"

Verifica que el `WEBHOOK_SECRET` en `.env` sea exactamente el mismo  
que configuraste en el portal de Cardnet/Azul.

---

## 📞 NECESITAS MÁS AYUDA?

1. **Documentación completa:** Lee `INTEGRACION_POS_FISICOS.md`
2. **Logs:** Revisa `logs/security.log`
3. **Admin:** Verifica transacciones en `/admin/escuelaweb/transaccionpos/`

---

## 🎯 RESUMEN DE PRÓXIMOS PASOS

1. [ ] Decidir si usar Cardnet o Azul
2. [ ] Contactar al proveedor (teléfono/email)
3. [ ] Solicitar acceso a API + credenciales sandbox
4. [ ] Configurar credenciales en `.env`
5. [ ] Configurar webhook en portal del proveedor
6. [ ] Probar con terminal de sandbox
7. [ ] Asociar terminales con estudiantes (si aplica)
8. [ ] Configurar impresora (opcional)
9. [ ] Pasar a producción (credenciales reales)

---

**¡Estás a solo unos pasos de recibir pagos automáticamente!** 🎉

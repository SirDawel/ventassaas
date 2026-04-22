# 🚀 INICIO RÁPIDO - POS Físico

## Para empezar YA con el sistema POS:

### 1️⃣ Copia las configuraciones a tu `.env`

```bash
# En Windows PowerShell:
Get-Content .env.pos.example | Add-Content .env

# O manualmente abre .env.pos.example y copia todo al final de tu .env
```

### 2️⃣ Edita `.env` con tus credenciales

```bash
# Proveedor principal
PAYMENT_PROVIDER=cardnet

# Cardnet (obtén estas credenciales contactando a Cardnet)
CARDNET_API_KEY=aqui_tu_api_key_real
CARDNET_MERCHANT_ID=aqui_tu_merchant_id_real
CARDNET_WEBHOOK_SECRET=aqui_tu_webhook_secret_real
CARDNET_API_URL=https://sandbox.cardnet.com.do/api

# Habilitar funciones opcionales
AUTO_PRINT_INVOICES=False  # Cambia a True si tienes impresora
AUTO_EMAIL_INVOICES=True   # True para enviar emails automáticamente
```

### 3️⃣ Ya está listo (las migraciones ya se aplicaron)

Los modelos ya fueron creados y migrados. Solo falta la configuración del webhook.

---

## 🌐 Configurar Webhook en Cardnet/Azul

### URL del Webhook (debe ser HTTPS):

```
https://tu-dominio.com/webhooks/pos/cardnet/
```

O para Azul:
```
https://tu-dominio.com/webhooks/pos/azul/
```

### Pasos:

1. Inicia sesión en el portal de Cardnet/Azul
2. Ve a **Configuración → Webhooks**
3. Añade nuevo webhook
4. Pega la URL de arriba
5. Selecciona eventos: `transaction.approved`, `payment.successful`
6. Copia el `WEBHOOK_SECRET` y pégalo en tu `.env`

---

## 🧪 Probar el Sistema (Sin Terminal Real)

### Opción 1: Script de Prueba

```bash
# Edita scripts/test_webhook_pos.py
# Cambia "custom_field_1" por la cédula de un estudiante real
# Cambia WEBHOOK_SECRET por el de tu .env

# Luego ejecuta:
python scripts/test_webhook_pos.py cardnet
```

### Opción 2: Probar Manualmente con cURL

```bash
curl -X POST http://127.0.0.1:8000/webhooks/pos/cardnet/ \
  -H "Content-Type: application/json" \
  -H "X-Cardnet-Signature: tu_firma" \
  -d '{
    "transaction_id": "TEST-001",
    "terminal_id": "VF-001",
    "amount": 5000.00,
    "status": "approved",
    "reference_number": "REF-001",
    "card_last_4": "1234",
    "card_type": "Visa",
    "transaction_date": "2026-04-12T10:30:00",
    "custom_field_1": "402-1234567-8"
  }'
```

---

## 👀 Verificar Resultados

### 1. Ver transacciones en el Admin:
```
http://127.0.0.1:8000/admin/escuelaweb/transaccionpos/
```

### 2. Ver facturas actualizadas:
```
http://127.0.0.1:8000/admin/escuelaweb/factura/
```

### 3. Consultar una transacción específica:
```
http://127.0.0.1:8000/webhooks/pos/consultar/TEST-001/
```

---

## 🔧 Asociar Terminales con Estudiantes

Si cada estudiante tiene su propio terminal (ej. cafetería):

1. Ve al Admin: http://127.0.0.1:8000/admin/escuelaweb/terminalestudiante/
2. Click "Añadir Terminal-Estudiante"
3. Ingresa:
   - **Terminal ID**: `VF-001` (el ID real del terminal)
   - **Estudiante**: Selecciona el estudiante
   - **Proveedor**: Cardnet o Azul
   - **Activo**: ✓
4. Guardar

Ahora cuando ese terminal procese un pago, se asociará automáticamente a ese estudiante.

---

## 📄 Documentación Completa

- **`INTEGRACION_POS_FISICOS.md`**: Guía completa paso a paso
- **`RESUMEN_POS_IMPLEMENTADO.md`**: Resumen de lo implementado
- **`.env.pos.example`**: Template de configuración

---

## ❓ Troubleshooting

### "No se pudo identificar al estudiante"

- ✅ Verifica que la cédula enviada en `custom_field_1` exista en la BD
- ✅ O configura un `TerminalEstudiante` en el admin

### "Webhook con firma inválida"

- ✅ Verifica que `WEBHOOK_SECRET` en `.env` sea correcto
- ✅ Asegúrate de que coincida con el del portal de Cardnet/Azul

### "Estudiante sin facturas pendientes"

- ✅ Verifica que el estudiante tenga facturas con estado `pendiente`, `vencida` o `parcial`
- ✅ Genera facturas mensuales si es necesario

---

## 📞 ¿Necesitas Ayuda?

1. Revisa los logs: `logs/security.log`
2. Consulta la documentación completa: `INTEGRACION_POS_FISICOS.md`
3. Verifica las transacciones en el admin de Django

---

**¡Todo listo para recibir pagos de POS físicos!** 🎉

Solo necesitas:
1. Credenciales reales de Cardnet/Azul
2. Configurar el webhook en su portal
3. ¡Empezar a recibir pagos!

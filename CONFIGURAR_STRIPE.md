# 🔑 Configurar Stripe para Sistema de Suscripciones

## 📋 Problema Actual

Los campos de tarjeta no están activos porque **STRIPE_PUBLIC_KEY no está configurada**.

Cuando abres la consola del navegador (F12), verás un mensaje indicando que Stripe no está configurado.

---

## ✅ Solución Rápida (5 minutos)

### Paso 1: Crear Cuenta en Stripe (GRATIS)

1. Ve a: https://stripe.com
2. Click en **"Start now"** o **"Sign up"**
3. Completa el registro (no necesitas tarjeta de crédito)
4. Confirma tu email

### Paso 2: Obtener las Claves de API

1. Una vez logueado, ve a: https://dashboard.stripe.com/apikeys
2. Verás dos tipos de claves:
   - **Publishable key** (comienza con `pk_test_...`)
   - **Secret key** (comienza con `sk_test_...`)
3. Haz click en **"Reveal test key"** para ver la clave secreta
4. **Copia ambas claves**

### Paso 3: Agregar las Claves al Archivo .env

1. Abre el archivo `.env` en la raíz del proyecto
2. Busca la sección de **STRIPE** (al final del archivo)
3. Pega tus claves:

```env
# STRIPE - SISTEMA DE SUSCRIPCIONES
STRIPE_PUBLIC_KEY=pk_test_51XXXXXXXXXXXXXXXXXXXXX
STRIPE_SECRET_KEY=sk_test_51XXXXXXXXXXXXXXXXXXXXX
STRIPE_WEBHOOK_SECRET=
STRIPE_TEST_MODE=True
```

> ⚠️ **IMPORTANTE**: Las claves deben empezar con `pk_test_` y `sk_test_` respectivamente

### Paso 4: Reiniciar el Servidor

1. Detén el servidor Django (Ctrl + C en la terminal)
2. Vuelve a iniciarlo:

```powershell
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

### Paso 5: Probar el Formulario

1. Ve a: http://evangelico.localhost:8000/suscripcion/
2. Click en **"Ver Planes Disponibles"**
3. Selecciona cualquier plan → **"Activar Ahora"**
4. Los campos de tarjeta deberían estar **activos y editables**
5. Usa una tarjeta de prueba:

   - **Número**: `4242 4242 4242 4242`
   - **Fecha**: `12/28` (cualquier fecha futura)
   - **CVV**: `123` (cualquier 3 dígitos)
   - **Nombre**: Cualquier nombre

---

## 🧪 Tarjetas de Prueba de Stripe

| Número | Resultado |
|--------|-----------|
| `4242 4242 4242 4242` | ✅ Pago exitoso |
| `4000 0025 0000 3155` | 🔐 Requiere 3D Secure (autenticación) |
| `4000 0000 0000 9995` | ❌ Pago rechazado |
| `4000 0000 0000 0002` | ❌ Tarjeta rechazada (código genérico) |

> Fecha: Cualquier fecha futura (ej: 12/28)  
> CVV: Cualquier 3 dígitos (ej: 123)

---

## 🔍 Verificar que Funciona

### En el Navegador

1. Abre la **Consola del Navegador** (F12 → Console)
2. Deberías ver mensajes como:

```
Inicializando Stripe con clave: pk_test_51...
Creando elementos de Stripe...
✓ cardNumberElement creado
✓ cardExpiryElement creado
✓ cardCvcElement creado
Montando elementos en el DOM...
✓ cardNumberElement montado en #card-number-element
✓ cardExpiryElement montado en #card-expiry-element
✓ cardCvcElement montado en #card-cvc-element
✓ Todos los elementos montados exitosamente. Los campos deberían estar activos.
cardNumber está listo
cardExpiry está listo
cardCvc está listo
```

### En los Campos de Pago

- ✅ Los campos deberían cambiar de color cuando haces click (borde azul)
- ✅ Deberías poder escribir números en el campo de tarjeta
- ✅ El campo de fecha debería auto-formatear: `12` → `12 / `
- ✅ El CVV solo acepta números

---

## ❌ Errores Comunes

### Error: "Stripe no está configurado correctamente"

**Causa**: La clave pública está vacía o mal configurada

**Solución**:
1. Verifica que copiaste la clave completa (incluye `pk_test_`)
2. No debe haber espacios antes o después de la clave
3. La clave debe estar entre comillas solo si tiene espacios

### Error: "Invalid API Key provided"

**Causa**: La clave es incorrecta o de producción

**Solución**:
1. Verifica que la clave empiece con `pk_test_` (no `pk_live_`)
2. Copia nuevamente desde el dashboard de Stripe
3. Verifica que no haya caracteres extraños

### Los campos siguen sin activarse

**Solución**:
1. Reinicia el servidor Django
2. Limpia la caché del navegador (Ctrl + Shift + R)
3. Abre la consola del navegador (F12) para ver errores
4. Verifica que el archivo `.env` se guardó correctamente

---

## 🔐 Seguridad

- ✅ **Nunca compartas** tu `STRIPE_SECRET_KEY` públicamente
- ✅ El archivo `.env` está en `.gitignore` (no se sube a GitHub)
- ✅ Usa claves de **prueba** (`test`) para desarrollo
- ✅ Usa claves de **producción** (`live`) solo en el servidor real

---

## 📞 Soporte

Si los campos siguen sin funcionar después de configurar Stripe:

1. Revisa la **consola del navegador** (F12 → Console)
2. Busca mensajes en **rojo** (errores)
3. Copia el mensaje de error completo
4. El error te dirá exactamente qué está mal

---

## ✨ ¿Todo Funciona?

Si los campos están activos y puedes escribir en ellos:

1. Usa la tarjeta de prueba: `4242 4242 4242 4242`
2. Completa el formulario
3. Click en **"Proceder al Pago Seguro"**
4. Deberías ver un mensaje de **"¡Pago Procesado Exitosamente!"**
5. Tu suscripción cambiará de estado **TRIAL** → **ACTIVA**

¡Sistema de pagos completamente funcional! 🎉

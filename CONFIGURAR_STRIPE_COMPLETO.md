# Configuración de Stripe para Sistema de Pagos

## Paso 1: Instalar Stripe

```bash
pip install stripe
```

## Paso 2: Obtener Credenciales de Stripe

1. Crear cuenta en https://stripe.com
2. Ir a Dashboard → Developers → API keys
3. Copiar:
   - **Publishable key** (pk_test_...)
   - **Secret key** (sk_test_...)
4. Ir a Webhooks → Add endpoint
   - URL: `https://misventasflash.com/webhooks/stripe/`
   - Events: `checkout.session.completed`, `invoice.payment_succeeded`, `invoice.payment_failed`
   - Copiar **Webhook signing secret** (whsec_...)

## Paso 3: Agregar Variables de Entorno

Agregar al archivo `.env`:

```env
# Stripe Configuration
STRIPE_PUBLIC_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

## Paso 4: Configurar settings.py

```python
# Stripe Configuration
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
```

## Paso 5: Crear Productos en Stripe Dashboard

1. Products → Create product
2. Crear 3 productos (Básico, Plus, Pro):

### Básico - $5/mes
- Name: Plan Básico MisVentasFlash
- Price: $5 USD
- Billing: Monthly
- Product ID: prod_XXXXX (guardar para configuración)

### Plus - $12/mes
- Name: Plan Plus MisVentasFlash
- Price: $12 USD
- Billing: Monthly
- Product ID: prod_YYYYY (guardar para configuración)

### Pro - $25/mes
- Name: Plan Pro MisVentasFlash
- Price: $25 USD
- Billing: Monthly
- Product ID: prod_ZZZZZ (guardar para configuración)

## Paso 6: Mapeo de Planes a Price IDs

Agregar al settings.py:

```python
STRIPE_PRICE_IDS = {
    'basico': 'price_XXXXXXXXXXXXXXXXXXXXX',  # ID del price de $5
    'plus': 'price_YYYYYYYYYYYYYYYYYYYYY',    # ID del price de $12
    'pro': 'price_ZZZZZZZZZZZZZZZZZZZZZ',     # ID del price de $25
}
```

## URLs de Referencia

- Dashboard de Stripe: https://dashboard.stripe.com/
- Documentación: https://stripe.com/docs/api
- Testing: Usar tarjeta `4242 4242 4242 4242` con cualquier fecha futura

## Webhooks a Manejar

1. **checkout.session.completed**: Pago exitoso inicial
2. **invoice.payment_succeeded**: Renovación automática exitosa
3. **invoice.payment_failed**: Fallo en el pago
4. **customer.subscription.deleted**: Cancelación de suscripción

## Modo de Prueba vs Producción

### Prueba (Test Mode):
- Claves empiezan con `pk_test_` y `sk_test_`
- Usar tarjetas de prueba
- No se cobran pagos reales

### Producción (Live Mode):
- Claves empiezan con `pk_live_` y `sk_live_`
- Pagos reales
- Requiere activación de cuenta Stripe

## Seguridad

⚠️ **NUNCA** exponer la Secret Key en código frontend
⚠️ **SIEMPRE** validar webhooks con el signing secret
⚠️ Usar HTTPS en producción para webhooks

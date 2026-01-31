# Scripts de Utilidades

Colección de scripts de mantenimiento y administración para el sistema escolar.

## Scripts de Activación

- **activar_anho_2025.py** - Activa el año escolar 2025-2026

## Scripts de Corrección

- **corregir_saldos_negativos.py** - Corrige facturas con pagos excedidos
- **recalcular_facturas.py** - Recalcula totales de todas las facturas
- **fix_articulos.py** - Repara problemas en artículos del inventario

## Scripts de Actualización

- **actualizar_articulos.py** - Actualiza información de artículos
- **actualizar_emails_vacios.py** - Corrige registros con emails vacíos

## Scripts de Verificación

- **check_materia_71.py** - Verifica una materia específica
- **check_materias.py** - Revisa todas las materias
- **ver_articulos.py** - Lista todos los artículos del inventario
- **verificar_facturas.py** - Revisa el estado de las facturas

## Scripts de Creación

- **crear_concepto_transporte.py** - Crea el concepto de pago de transporte

## Uso

Ejecutar desde la raíz del proyecto:

```bash
python scripts/nombre_del_script.py
```

**Nota:** Estos scripts configuran Django automáticamente, por lo que no es necesario usar `python manage.py shell`.

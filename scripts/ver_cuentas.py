from escuelaweb.models import PlanCuentas

print('Total cuentas:', PlanCuentas.objects.count())
print('\nCuentas de detalle por código:')
for c in PlanCuentas.objects.filter(es_detalle=True).order_by('codigo')[:20]:
    print(f'{c.codigo} - {c.nombre} - {c.get_tipo_cuenta_display()}')

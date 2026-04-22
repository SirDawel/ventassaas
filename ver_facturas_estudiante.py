from escuelaweb.models import Factura, DetalleFactura, CustomUser, AnhoEscolar

# Buscar estudiante "jame Doe"
estudiante = CustomUser.objects.filter(first_name__icontains='jame').first()
if estudiante:
    print(f"Estudiante: {estudiante.get_full_name()} (ID: {estudiante.id})")
    
    anho_escolar = AnhoEscolar.objects.get(activo=True)
    facturas = Factura.objects.filter(
        cliente=estudiante,
        anho_escolar=anho_escolar
    ).order_by('fecha_emision')
    
    print(f"\nTotal facturas: {facturas.count()}")
    
    for f in facturas:
        detalle = DetalleFactura.objects.filter(factura=f).first()
        desc = detalle.descripcion if detalle else "Sin detalle"
        mes = detalle.mes if detalle and detalle.mes else "?"
        print(f"  {f.numero_factura} | Emisión: {f.fecha_emision} | Mes: {mes} | {desc} | Estado: {f.estado}")
else:
    print("Estudiante no encontrado")

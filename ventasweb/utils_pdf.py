"""
Utilidades para generar PDFs de cotizaciones
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.conf import settings
import qrcode
from datetime import datetime


def generar_pdf_cotizacion(cotizacion, request=None):
    """
    Genera un PDF profesional de una cotización
    
    Args:
        cotizacion: Objeto Cotizacion
        request: Request object para generar URL absoluta del QR
    
    Returns:
        BytesIO con el contenido del PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    
    # Estilos
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='CenterBold',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=18,
        textColor=colors.HexColor('#2c3e50')
    ))
    styles.add(ParagraphStyle(
        name='RightAlign',
        parent=styles['Normal'],
        alignment=TA_RIGHT
    ))
    
    # Contenido
    elementos = []
    
    # Encabezado con logo y título
    titulo = Paragraph("COTIZACIÓN", styles['CenterBold'])
    elementos.append(titulo)
    elementos.append(Spacer(1, 0.3*inch))
    
    # Información de la empresa
    config = cotizacion.cliente.tenant.configuracion_escuela.first() if hasattr(cotizacion.cliente, 'tenant') else None
    nombre_empresa = config.nombre_escuela if config else "Mis Ventas Flash"
    
    empresa_data = [
        [Paragraph(f"<b>{nombre_empresa}</b>", styles['Normal']), ''],
        [Paragraph(f"Cotización N°: <b>{cotizacion.numero_cotizacion}</b>", styles['Normal']), '']
    ]
    
    empresa_table = Table(empresa_data, colWidths=[4*inch, 3*inch])
    empresa_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elementos.append(empresa_table)
    elementos.append(Spacer(1, 0.2*inch))
    
    # Información del cliente y fechas
    info_data = [
        ['Cliente:', cotizacion.cliente.get_full_name(), 'Fecha Emisión:', cotizacion.fecha_emision.strftime('%d/%m/%Y')],
        ['Email:', cotizacion.cliente.email, 'Válida Hasta:', cotizacion.fecha_vencimiento.strftime('%d/%m/%Y')],
    ]
    
    if cotizacion.vendedor:
        info_data.append(['Vendedor:', cotizacion.vendedor.get_full_name(), 'Estado:', cotizacion.get_estado_display()])
    else:
        info_data.append(['Vendedor:', 'No asignado', 'Estado:', cotizacion.get_estado_display()])
    
    info_table = Table(info_data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 2*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elementos.append(info_table)
    elementos.append(Spacer(1, 0.3*inch))
    
    # Tabla de detalles
    detalle_data = [['#', 'Descripción', 'Cant.', 'Precio Unit.', 'Subtotal', 'Desc.', 'Total']]
    
    for idx, detalle in enumerate(cotizacion.detalles.all(), 1):
        detalle_data.append([
            str(idx),
            detalle.descripcion,
            f"{detalle.cantidad:,.2f}",
            f"RD$ {detalle.precio_unitario:,.2f}",
            f"RD$ {detalle.get_subtotal():,.2f}",
            f"RD$ {detalle.descuento:,.2f}",
            f"RD$ {detalle.get_total():,.2f}"
        ])
    
    detalle_table = Table(detalle_data, colWidths=[0.4*inch, 2.8*inch, 0.7*inch, 1*inch, 1*inch, 0.8*inch, 1*inch])
    detalle_table.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        # Contenido
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elementos.append(detalle_table)
    elementos.append(Spacer(1, 0.2*inch))
    
    # Totales
    totales_data = [
        ['', '', '', '', '', 'Subtotal:', f"RD$ {cotizacion.subtotal:,.2f}"],
        ['', '', '', '', '', 'Descuento:', f"RD$ {cotizacion.descuento:,.2f}"],
        ['', '', '', '', '', f'ITBIS ({(cotizacion.impuesto/cotizacion.subtotal*100 if cotizacion.subtotal > 0 else 0):.0f}%):', f"RD$ {cotizacion.impuesto:,.2f}"],
        ['', '', '', '', '', 'TOTAL:', f"RD$ {cotizacion.total:,.2f}"],
    ]
    
    totales_table = Table(totales_data, colWidths=[0.4*inch, 2.8*inch, 0.7*inch, 1*inch, 1*inch, 0.8*inch, 1*inch])
    totales_table.setStyle(TableStyle([
        ('ALIGN', (5, 0), (5, -1), 'RIGHT'),
        ('ALIGN', (6, 0), (6, -1), 'RIGHT'),
        ('FONTNAME', (5, 0), (5, -1), 'Helvetica-Bold'),
        ('FONTNAME', (6, 0), (6, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (5, 0), (6, -1), 10),
        ('LINEABOVE', (5, -1), (6, -1), 2, colors.HexColor('#3498db')),
        ('BACKGROUND', (5, -1), (6, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (5, -1), (6, -1), colors.HexColor('#2c3e50')),
    ]))
    elementos.append(totales_table)
    elementos.append(Spacer(1, 0.3*inch))
    
    # Observaciones
    if cotizacion.observaciones:
        elementos.append(Paragraph("<b>Observaciones:</b>", styles['Normal']))
        elementos.append(Spacer(1, 0.1*inch))
        elementos.append(Paragraph(cotizacion.observaciones.replace('\n', '<br/>'), styles['Normal']))
        elementos.append(Spacer(1, 0.2*inch))
    
    # Términos y condiciones
    if cotizacion.terminos_condiciones:
        elementos.append(Paragraph("<b>Términos y Condiciones:</b>", styles['Normal']))
        elementos.append(Spacer(1, 0.1*inch))
        elementos.append(Paragraph(cotizacion.terminos_condiciones.replace('\n', '<br/>'), styles['Normal']))
        elementos.append(Spacer(1, 0.2*inch))
    
    # QR Code con URL pública (si existe request)
    if request:
        try:
            url_publica = cotizacion.get_url_publica(request)
            qr = qrcode.QRCode(version=1, box_size=3, border=1)
            qr.add_data(url_publica)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Guardar QR en buffer
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            # Agregar al PDF
            qr_image = Image(qr_buffer, width=1.5*inch, height=1.5*inch)
            elementos.append(Spacer(1, 0.2*inch))
            elementos.append(Paragraph("<b>Escanea para ver en línea:</b>", styles['Normal']))
            elementos.append(qr_image)
        except Exception as e:
            pass  # Si falla el QR, continuamos sin él
    
    # Firma del cliente (si existe)
    if cotizacion.firma_cliente:
        elementos.append(Spacer(1, 0.3*inch))
        elementos.append(Paragraph("<b>Firma del Cliente:</b>", styles['Normal']))
        elementos.append(Spacer(1, 0.1*inch))
        try:
            import base64
            firma_data = base64.b64decode(cotizacion.firma_cliente.split(',')[1] if ',' in cotizacion.firma_cliente else cotizacion.firma_cliente)
            firma_buffer = BytesIO(firma_data)
            firma_img = Image(firma_buffer, width=2*inch, height=1*inch)
            elementos.append(firma_img)
            if cotizacion.firma_fecha:
                elementos.append(Paragraph(f"Firmado el: {cotizacion.firma_fecha.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        except Exception as e:
            elementos.append(Paragraph("Error al cargar firma", styles['Normal']))
    
    # Pie de página
    elementos.append(Spacer(1, 0.3*inch))
    elementos.append(Paragraph(
        f"<i>Documento generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}</i>",
        ParagraphStyle(name='Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    # Construir PDF
    doc.build(elementos)
    buffer.seek(0)
    return buffer

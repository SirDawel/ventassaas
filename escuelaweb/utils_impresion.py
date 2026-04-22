"""
Utilidades para impresión de facturas
Soporta impresión térmica, PDF y envío por email
"""

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from decimal import Decimal
import logging
import os

logger = logging.getLogger(__name__)


def imprimir_factura_pos(factura, transaccion_pos=None):
    """
    Imprime una factura en impresora térmica (POS)
    
    Args:
        factura: Instancia de Factura
        transaccion_pos: Instancia de TransaccionPOS (opcional)
        
    Esta función envía comandos ESC/POS a la impresora térmica
    para imprimir el recibo de la factura.
    """
    try:
        # Verificar si está habilitada la impresión
        if not getattr(settings, 'POS_PRINTER_ENABLED', False):
            logger.info("Impresión POS deshabilitada en configuración")
            return False
        
        printer_name = getattr(settings, 'POS_PRINTER_NAME', None)
        if not printer_name:
            logger.warning("No hay impresora POS configurada")
            return False
        
        # Generar contenido del recibo
        contenido = generar_contenido_recibo(factura, transaccion_pos)
        
        # OPCIÓN 1: Usar python-escpos (recomendado)
        try:
            from escpos.printer import Network, Usb, File
            
            # Determinar tipo de conexión
            printer_type = getattr(settings, 'POS_PRINTER_TYPE', 'network')
            
            if printer_type == 'network':
                # Impresora en red
                printer_ip = getattr(settings, 'POS_PRINTER_IP', '192.168.1.100')
                printer_port = getattr(settings, 'POS_PRINTER_PORT', 9100)
                printer = Network(printer_ip, port=printer_port)
                
            elif printer_type == 'usb':
                # Impresora USB
                vendor_id = getattr(settings, 'POS_PRINTER_VENDOR_ID', 0x04b8)
                product_id = getattr(settings, 'POS_PRINTER_PRODUCT_ID', 0x0e15)
                printer = Usb(vendor_id, product_id)
                
            elif printer_type == 'file':
                # Para pruebas: imprime a archivo
                printer_path = getattr(settings, 'POS_PRINTER_PATH', '/tmp/receipt.txt')
                printer = File(printer_path)
            
            # Configurar impresora
            printer.set('CENTER', 'A', 'NORMAL', 1, 1)
            
            # Imprimir contenido
            for linea in contenido:
                if linea.get('tipo') == 'titulo':
                    printer.set('CENTER', 'B', 'NORMAL', 2, 2)
                    printer.text(linea['texto'] + '\n')
                    printer.set('CENTER', 'A', 'NORMAL', 1, 1)
                    
                elif linea.get('tipo') == 'separador':
                    printer.text('-' * 32 + '\n')
                    
                elif linea.get('tipo') == 'texto':
                    printer.set('LEFT', 'A', 'NORMAL', 1, 1)
                    printer.text(linea['texto'] + '\n')
                    
                elif linea.get('tipo') == 'total':
                    printer.set('CENTER', 'B', 'NORMAL', 2, 1)
                    printer.text(linea['texto'] + '\n')
                    printer.set('CENTER', 'A', 'NORMAL', 1, 1)
            
            # Cortar papel
            printer.cut()
            printer.close()
            
            logger.info(f"Factura {factura.numero_factura} impresa exitosamente")
            return True
            
        except ImportError:
            logger.warning("python-escpos no instalado. Instala con: pip install python-escpos")
            # Fallback: imprimir usando comandos del sistema
            return imprimir_con_sistema(contenido, printer_name)
            
    except Exception as e:
        logger.error(f"Error imprimiendo factura: {str(e)}", exc_info=True)
        return False


def generar_contenido_recibo(factura, transaccion_pos=None):
    """
    Genera el contenido del recibo para imprimir
    
    Returns:
        list: Lista de diccionarios con líneas del recibo
    """
    lineas = []
    
    # Obtener configuración de la escuela
    from .models import ConfiguracionEscuela
    try:
        config = ConfiguracionEscuela.objects.first()
        nombre_escuela = config.nombre if config else "ESCUELA"
        rnc = config.rnc if config else ""
        direccion = config.direccion if config else ""
        telefono = config.telefono if config else ""
    except:
        nombre_escuela = "ESCUELA"
        rnc = ""
        direccion = ""
        telefono = ""
    
    # Encabezado
    lineas.append({'tipo': 'titulo', 'texto': nombre_escuela})
    if rnc:
        lineas.append({'tipo': 'texto', 'texto': f'RNC: {rnc}'})
    if direccion:
        lineas.append({'tipo': 'texto', 'texto': direccion})
    if telefono:
        lineas.append({'tipo': 'texto', 'texto': f'Tel: {telefono}'})
    
    lineas.append({'tipo': 'separador'})
    
    # Información de la factura
    lineas.append({'tipo': 'texto', 'texto': f'FACTURA: {factura.numero_factura}'})
    lineas.append({'tipo': 'texto', 'texto': f'Fecha: {factura.fecha_emision.strftime("%d/%m/%Y %H:%M")}'})
    
    lineas.append({'tipo': 'separador'})
    
    # Cliente
    estudiante = factura.estudiante
    lineas.append({'tipo': 'texto', 'texto': f'Cliente: {estudiante.get_full_name()}'})
    if estudiante.cedula:
        lineas.append({'tipo': 'texto', 'texto': f'Cedula: {estudiante.cedula}'})
    
    lineas.append({'tipo': 'separador'})
    
    # Detalles
    lineas.append({'tipo': 'texto', 'texto': 'CONCEPTO               MONTO'})
    lineas.append({'tipo': 'separador'})
    
    for detalle in factura.detalles.all():
        concepto = detalle.articulo.nombre[:20]
        monto = f'RD$ {detalle.total:.2f}'
        linea = f'{concepto:<20} {monto:>10}'
        lineas.append({'tipo': 'texto', 'texto': linea})
    
    lineas.append({'tipo': 'separador'})
    
    # Totales
    lineas.append({'tipo': 'texto', 'texto': f'Subtotal:      RD$ {factura.subtotal:.2f}'})
    if factura.descuento > 0:
        lineas.append({'tipo': 'texto', 'texto': f'Descuento:     RD$ {factura.descuento:.2f}'})
    if factura.itbis > 0:
        lineas.append({'tipo': 'texto', 'texto': f'ITBIS:         RD$ {factura.itbis:.2f}'})
    
    lineas.append({'tipo': 'separador'})
    lineas.append({'tipo': 'total', 'texto': f'TOTAL: RD$ {factura.total:.2f}'})
    
    # Información de pago
    if transaccion_pos:
        lineas.append({'tipo': 'separador'})
        lineas.append({'tipo': 'texto', 'texto': 'FORMA DE PAGO: TARJETA'})
        lineas.append({'tipo': 'texto', 'texto': f'{transaccion_pos.tipo_tarjeta} ****{transaccion_pos.tarjeta_ultimos_4}'})
        lineas.append({'tipo': 'texto', 'texto': f'Ref: {transaccion_pos.transaction_id}'})
    
    lineas.append({'tipo': 'separador'})
    lineas.append({'tipo': 'texto', 'texto': ''})
    lineas.append({'tipo': 'texto', 'texto': 'GRACIAS POR SU PAGO'})
    lineas.append({'tipo': 'texto', 'texto': ''})
    
    return lineas


def imprimir_con_sistema(contenido, printer_name):
    """
    Imprime usando comandos del sistema operativo
    Fallback cuando python-escpos no está disponible
    """
    try:
        import tempfile
        import subprocess
        import platform
        
        # Crear archivo temporal con el contenido
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            for linea in contenido:
                f.write(linea.get('texto', '') + '\n')
            temp_file = f.name
        
        # Comando según el sistema operativo
        if platform.system() == 'Windows':
            # En Windows
            subprocess.run(['print', '/D:' + printer_name, temp_file], check=True)
        else:
            # En Linux/Mac
            subprocess.run(['lp', '-d', printer_name, temp_file], check=True)
        
        # Eliminar archivo temporal
        os.unlink(temp_file)
        
        return True
        
    except Exception as e:
        logger.error(f"Error imprimiendo con sistema: {str(e)}")
        return False


def enviar_factura_email(factura, estudiante):
    """
    Envía la factura por email al estudiante
    
    Args:
        factura: Instancia de Factura
        estudiante: Instancia de CustomUser
    """
    try:
        if not estudiante.email:
            logger.warning(f"Estudiante {estudiante.get_full_name()} no tiene email")
            return False
        
        # Generar PDF de la factura
        pdf_content = generar_pdf_factura(factura)
        
        # Preparar email
        subject = f'Factura {factura.numero_factura} - Pago Recibido'
        
        # Renderizar template de email
        mensaje = f"""
Estimado/a {estudiante.get_full_name()},

Hemos recibido su pago exitosamente.

Detalles de la factura:
- Número: {factura.numero_factura}
- Fecha: {factura.fecha_emision.strftime('%d/%m/%Y')}
- Monto: RD$ {factura.total:.2f}
- Estado: {factura.get_estado_display()}

Adjunto encontrará su factura en formato PDF.

Gracias por su pago.

---
Sistema de Gestión Escolar
        """
        
        # Crear email
        email = EmailMessage(
            subject=subject,
            body=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[estudiante.email]
        )
        
        # Adjuntar PDF
        if pdf_content:
            email.attach(
                f'factura_{factura.numero_factura}.pdf',
                pdf_content,
                'application/pdf'
            )
        
        # Enviar
        email.send(fail_silently=False)
        
        logger.info(f"Factura {factura.numero_factura} enviada por email a {estudiante.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando factura por email: {str(e)}", exc_info=True)
        return False


def generar_pdf_factura(factura):
    """
    Genera un PDF de la factura
    
    Returns:
        bytes: Contenido del PDF
    """
    try:
        # OPCIÓN 1: Usar ReportLab
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from io import BytesIO
            
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # Título
            p.setFont("Helvetica-Bold", 16)
            p.drawCentredString(width / 2, height - 50, "FACTURA")
            
            # Información de la factura
            p.setFont("Helvetica", 12)
            y = height - 100
            
            p.drawString(50, y, f"Número: {factura.numero_factura}")
            y -= 20
            p.drawString(50, y, f"Fecha: {factura.fecha_emision.strftime('%d/%m/%Y')}")
            y -= 20
            p.drawString(50, y, f"Cliente: {factura.estudiante.get_full_name()}")
            y -= 40
            
            # Detalles
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, y, "CONCEPTO")
            p.drawString(400, y, "MONTO")
            y -= 5
            p.line(50, y, width - 50, y)
            y -= 20
            
            p.setFont("Helvetica", 10)
            for detalle in factura.detalles.all():
                p.drawString(50, y, detalle.articulo.nombre[:40])
                p.drawString(400, y, f"RD$ {detalle.total:.2f}")
                y -= 20
            
            # Totales
            y -= 10
            p.line(50, y, width - 50, y)
            y -= 20
            
            p.setFont("Helvetica-Bold", 12)
            p.drawString(300, y, "TOTAL:")
            p.drawString(400, y, f"RD$ {factura.total:.2f}")
            
            p.showPage()
            p.save()
            
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except ImportError:
            logger.warning("ReportLab no instalado. Instala con: pip install reportlab")
            return None
            
    except Exception as e:
        logger.error(f"Error generando PDF: {str(e)}")
        return None

import os
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.shortcuts import get_object_or_404
from .models import Albaran

def link_callback(uri, rel):
    """Convierte rutas de static en rutas reales del contenedor /app/staticfiles/"""
    if uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
    else:
        path = os.path.join(settings.BASE_DIR, uri)
    return path

def exportar_albaran_pdf(request, albaran_id):
    albaran = get_object_or_404(Albaran, id=albaran_id)
    pedido = albaran.pedido
    punto_recogida = pedido.usuario

    # Lógica para determinar el Operador
    if punto_recogida.subcliente:
        operador = punto_recogida.subcliente
        datos_operador = {
            'nombre': operador.razon_social,
            'cif': operador.cif,
            'direccion': f"{operador.direccion}, {operador.numero}",
            'localidad': f"{operador.cp} {operador.localidad} ({operador.provincia})"
        }
    else:
        operador = punto_recogida.cliente
        datos_operador = {
            'nombre': operador.razon_social,
            'cif': operador.cif,
            'direccion': f"{operador.direccion_fiscal}, {operador.numero_fiscal}",
            'localidad': f"{operador.cp_fiscal} {operador.localidad_fiscal} ({operador.provincia_fiscal})"
        }

    gestor = punto_recogida.gestor
    transportista = punto_recogida.transportista
    
    context = {
        'albaran': albaran,
        'pedido': albaran.pedido,
        'punto': punto_recogida,
        'operador': datos_operador,
        'lineas': albaran.lineas_albaran.filter(concepto__tipo_concepto__iexact='Residuo'),
        'vehiculo': albaran.vehiculo,
        'gestor': gestor,
        'transportista': transportista,
        # Ya no necesitamos pasar logo_path manualmente si usamos {% static %} en el HTML
    }

    # Crear el PDF
    template = get_template('pdf/albaran_template.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Albaran_{albaran.codigo}.pdf"'

    # Convertir HTML a PDF con el link_callback
    pisa_status = pisa.CreatePDF(
        html, 
        dest=response, 
        link_callback=link_callback # <--- ESTO ES LA CLAVE
    )
    
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF', status=500)
    
    return response

def exportar_di_pdf(request, albaran_id):
    # 1. Reutilizas la lógica de obtención del objeto
    albaran = get_object_or_404(Albaran, id=albaran_id)

    pedido = albaran.pedido
    punto_recogida = pedido.usuario

    # Lógica para determinar el Operador
    if punto_recogida.subcliente:
        operador = punto_recogida.subcliente
        datos_operador = {
            'nombre': operador.razon_social,
            'cif': operador.cif,
            'direccion': f"{operador.direccion}, {operador.numero}",
            'localidad': f"{operador.cp} {operador.localidad} ({operador.provincia})"
        }
    else:
        operador = punto_recogida.cliente
        datos_operador = {
            'nombre': operador.razon_social,
            'cif': operador.cif,
            'direccion': f"{operador.direccion_fiscal}, {operador.numero_fiscal}",
            'localidad': f"{operador.cp_fiscal} {operador.localidad_fiscal} ({operador.provincia_fiscal})"
        }

    gestor = punto_recogida.gestor
    transportista = punto_recogida.transportista
    
    context = {
        'albaran': albaran,
        'pedido': albaran.pedido,
        'punto': punto_recogida,
        'operador': datos_operador,
        'lineas': albaran.lineas_albaran.filter(concepto__tipo_concepto__iexact='Residuo'),
        'vehiculo': albaran.vehiculo,
        'gestor': gestor,
        'transportista': transportista,
        # Ya no necesitamos pasar logo_path manualmente si usamos {% static %} en el HTML
    }
    
    # 2. Aquí es donde apuntas a la nueva plantilla que vas a retocar
    template = get_template('pdf/di_template.html')
    
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="DI_{albaran.codigo}.pdf"'

    # Convertir HTML a PDF con el link_callback
    pisa_status = pisa.CreatePDF(
        html, 
        dest=response, 
        link_callback=link_callback # <--- ESTO ES LA CLAVE
    )
    
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF', status=500)
    
    return response
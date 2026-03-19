from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from ajustes.models import TipoEnvase, TipoResiduo, ConceptoFacturable

@staff_member_required
def obtener_precio_ajax(request):
    tipo = request.GET.get('tipo')
    id_obj = request.GET.get('id')
    precio = 0

    try:
        if tipo == 'Envase' and id_obj:
            precio = TipoEnvase.objects.get(pk=id_obj).precio
        elif tipo == 'Residuo' and id_obj:
            precio = TipoResiduo.objects.get(pk=id_obj).precio_kg
        elif tipo == 'Concepto' and id_obj:
            # Nueva lógica para LineaServicio
            precio = ConceptoFacturable.objects.get(pk=id_obj).precio_base
    except Exception:
        precio = 0

    return JsonResponse({'precio': float(precio)})
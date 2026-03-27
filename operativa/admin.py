from datetime import date

from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from import_export.admin import ImportExportModelAdmin
from django.utils.html import format_html
from gestion_residuos.models import Perfil
from logistica.models import Vehiculo
from .models import LineaPedido, Pedido, Servicio, LineaServicio, Albaran
from utils import BaseAdmin, BaseInline, FiltroFechaProgramada, FiltroFechaInicio
from django.template.response import TemplateResponse

class LineaServicioInline(BaseInline):
    model = LineaServicio
    extra = 1
    # Campos que se verán en la edición en línea
    fields = ('concepto', 'cantidad', 'precio', 'notas')

@admin.register(Servicio)
class ServicioAdmin(BaseAdmin, ImportExportModelAdmin):
    list_display = ('id', 'nombre', 'usuario', 'periodicidad', 'fecha_inicio', 'activo')
    list_display_links = ('id', 'nombre')
    ordering = ('-id',)
    search_fields = (
        'nombre', 
        'usuario__razon_social', 
        'usuario__codigo', 
        'periodicidad__nombre'
    )
    list_filter = ('activo', 'periodicidad', FiltroFechaInicio, 'usuario__nombre')
    
    readonly_fields = ('nombre',)
    
    # Inserción de las líneas de servicio en la misma pantalla
    inlines = [LineaServicioInline]

    # Organizar el formulario por secciones (opcional, pero profesional)
    fieldsets = (
        ('Datos Base', {
            'fields': ('nombre', 'usuario', 'periodicidad', 'activo')
        }),
        ('Planificación', {
            'fields': ('fecha_inicio',)
        }),
    )

    change_form_template = "admin/operativa/servicio/change_form.html" # Para añadir el botón

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        # Pasamos el estado del objeto a la plantilla
        context['servicio_activo'] = obj.activo if obj else False
        return super().render_change_form(request, context, add, change, form_url, obj)

    class Media:
        js = (
            'admin/js/lineas_servicio.js', 
        )

    def save_model(self, request, obj, form, change):
        # 1. Guardamos los cambios del servicio SIEMPRE
        super().save_model(request, obj, form, change)

        # 2. Después de guardar, comprobamos si debe saltar el aviso
        if change:
            claves = ['periodicidad', 'fecha_inicio', 'activo']
            ha_cambiado = any(campo in form.changed_data for campo in claves)
            
            if ha_cambiado:
                pedidos_futuros = Pedido.objects.filter(
                    servicio=obj, 
                    estado='PENDIENTE', 
                    fecha_programada__gte=date.today()
                ).exists()
                
                if pedidos_futuros:
                    # Marcamos la sesión
                    request.session['cambio_critico_id'] = obj.pk
                    # Debug en consola
                    print(f"DEBUG: Cambio crítico detectado en Servicio {obj.pk}")
                    

    def response_change(self, request, obj):
        # 1. PRIORIDAD: Si el usuario pulsó el botón azul, lo ejecutamos primero
        if "_generar_pedido" in request.POST:
            if not obj.activo:
                self.message_user(request, "ERROR: Servicio inactivo.", level='ERROR')
            else:
                actualizados, eliminados = obj.generar_pedidos_periodicos()
                self.message_user(request, f"Sincronización manual: {actualizados} al día, {eliminados} borrados.")
            
            # Al terminar el botón azul, limpiamos cualquier marca de sesión 
            # para que no salte el aviso de confirmación dos veces
            if 'cambio_critico_id' in request.session:
                del request.session['cambio_critico_id']
                
            return HttpResponseRedirect(".")
        
        # 2. SEGUNDO: Si hubo un cambio crítico por el formulario normal, preguntamos
        if request.session.get('cambio_critico_id') == obj.pk:
            return TemplateResponse(request, "admin/operativa/servicio/confirmar_cambios.html", {
                'opts': self.model._meta,
                'obj': obj,
                'conteo': Pedido.objects.filter(servicio=obj, estado='PENDIENTE', fecha_programada__gte=date.today()).count(),
            })
            
        return super().response_change(request, obj)
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<path:object_id>/process-cambio/', 
                self.admin_site.admin_view(self.process_cambio), 
                name='operativa_servicio_process_cambio'), # <--- Este nombre
        ]
        return my_urls + urls
    
    def process_cambio(self, request, object_id):
        obj = self.get_object(request, object_id)
        accion = request.POST.get('accion')
        
        if accion == 'sincronizar':
            # Llamamos a la función potente que ya limpia y crea
            actualizados, eliminados = obj.generar_pedidos_periodicos()
            self.message_user(request, f"Sincronización completa: {actualizados} pedidos al día y {eliminados} eliminados.")
        else:
            self.message_user(request, "Se han guardado los cambios del servicio, pero se han respetado los pedidos existentes.")
        
        # Limpieza de sesión
        if 'cambio_critico_servicio_id' in request.session:
            del request.session['cambio_critico_servicio_id']
            
        return HttpResponseRedirect(reverse('admin:operativa_servicio_changelist'))

    def process_desactivacion(self, request, object_id):
        obj = self.get_object(request, object_id)
        accion = request.POST.get('accion')
        
        if accion == 'borrar':
            obj.pedidos.filter(estado='PENDIENTE', fecha_programada__gte=date.today()).delete()
            self.message_user(request, "Servicio desactivado y pedidos eliminados.")
        else:
            self.message_user(request, "Servicio desactivado. Se han mantenido los pedidos pendientes.")
        
        # Finalmente guardamos el estado "Inactivo"
        obj.activo = False
        obj.save()
        
        # Limpiamos sesión
        if 'desactivar_servicio_id' in request.session:
            del request.session['desactivar_servicio_id']
            
        return HttpResponseRedirect(reverse('admin:operativa_servicio_changelist'))

class LineaPedidoInline(BaseInline):
    model = LineaPedido
    extra = 0  # No mostrar filas vacías por defecto ya que vienen del servicio
    fields = ('concepto', 'cantidad', 'precio', 'notas')
    # Aplicamos los mismos anchos de columna que en el Servicio
    class Media:
        css = {
            'all': ('css/custom_admin.css',)
        }

@admin.register(Pedido)
class PedidoAdmin(BaseAdmin, ImportExportModelAdmin):
    list_filter = ('estado', FiltroFechaProgramada, 'usuario__nombre')
    search_fields = ('usuario__nombre', 'id')
    date_hierarchy = 'fecha_programada' # Barra de navegación temporal arriba
    
    inlines = [LineaPedidoInline]
    
    list_display = ('id', 'fecha_programada', 'fecha_ejecucion', 'usuario', 'estado')
    
    # Hacemos que la programada sea solo lectura
    readonly_fields = ('fecha_programada', 'servicio')
    
    fieldsets = (
        ('Planificación', {
            'fields': (('fecha_programada', 'fecha_ejecucion'), 'estado', 'servicio')
        }),
        ('Asignaciones', {
            'fields': ('usuario', 'transportista', 'gestor'),
        }),
    )

    class Media:
        js = ('admin/js/lineas_servicio.js',) # Reutilizamos la lógica de cálculo
        css = {
            'all': ('css/custom_admin.css',) # Para los switches y tamaños
        }

class LineaAlbaranInline(BaseInline):
    model = LineaPedido
    fields = ['concepto', 'get_ler',  'cantidad_recogida', 'notas']
    readonly_fields = ['concepto','get_ler']
    extra = 0
    max_num = 0
    has_add_permission = lambda self, req, obj: False

    verbose_name = "Material recogido"
    verbose_name_plural = "Materiales recogidos"

    def get_ler(self, obj):
        # Intentamos navegar por las relaciones: concepto -> residuo -> codigo_ler
        if obj.concepto and hasattr(obj.concepto, 'residuo') and obj.concepto.residuo:
            return obj.concepto.residuo.codigo_ler
        return "-"
    
    get_ler.short_description = "Código LER"
    
    # --- RESTRICCIONES DE ACCIÓN ---
    
    def has_add_permission(self, request, obj=None):
        # Devuelve False para que desaparezca el botón "Añadir otra Línea de Pedido"
        return False

    def has_delete_permission(self, request, obj=None):
        # Opcional: impide que el transportista borre una línea que debe gestionar
        return False

    def get_queryset(self, request):
        # Seguimos filtrando para que solo vean lo que es "Residuo"
        return super().get_queryset(request).filter(concepto__tipo_concepto__iexact='Residuo')
    
class AlbaranForm(forms.ModelForm):
    # Definimos el campo de ejecución explícitamente para que sea un calendario
    fecha_ejecucion = forms.DateField(
        widget=admin.widgets.AdminDateWidget(),
        label="Fecha de servicio",
        required=False
    )

    class Meta:
        model = Albaran
        fields = '__all__'

@admin.register(Albaran)
class AlbaranAdmin(BaseAdmin, ImportExportModelAdmin):
    form = AlbaranForm
    list_display = ('codigo', 'get_cliente', 'fecha_emision', 'get_fecha_programada', 'fecha_ejecucion', 'acciones_pdf')
    
    # 2. Añadimos el nuevo campo a readonly_fields para verlo dentro de la ficha
    # Lo incluimos en el fieldset de "Información General" o donde prefieras
    readonly_fields = (
        'codigo','display_cliente', 'display_usuario', 'display_gestor_residuos', 
        'display_transportista', 'fecha_emision', 'display_fecha_programada', 
        'display_pedido_info', 'acciones_pdf' # <--- Cambiado aquí
    )
    # list_display = ('codigo', 'get_cliente', 'fecha_emision', 'get_fecha_programada', 'fecha_ejecucion')
    exclude = ('pedido',) # Ocultamos el campo pedido para que no lo cambien
    # readonly_fields = ('codigo','display_cliente', 'display_usuario', 'display_gestor_residuos', 'display_transportista', 'fecha_emision', 'display_fecha_programada', 'display_pedido_info')
    
    # 1. ORGANIZACIÓN POR SECCIONES (Que actúan como pestañas en temas modernos)
    fieldsets = (
        ('Información General', {
            'classes': ('wide',),
            'fields': (
                'codigo',
                'display_pedido_info',
                'display_cliente',
                'display_usuario',
                'display_gestor_residuos',
                'display_transportista',
                'fecha_emision',
                'display_fecha_programada',
            )
        }),
        ('Datos de la Recogida', {
            'classes': ('wide',),
            'fields': (
                'fecha_ejecucion',
                'vehiculo',
                'observaciones',
            )
        }),
    )

    def display_fecha_programada(self, obj):
        return obj.pedido.fecha_programada # O el nombre exacto de tu campo programado
    display_fecha_programada.short_description = "Fecha Programada"

    def get_fecha_programada(self, obj):
        return obj.pedido.fecha_programada
    get_fecha_programada.short_description = "Programada"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs

        try:
            # 1. Obtenemos el perfil y la empresa de transporte
            perfil = request.user.perfil  # O perfil_usuario según cómo lo llamaras
            empresa = perfil.transportista
            
            if empresa:
                # 2. Filtramos: el Pedido tiene un Usuario, y ese Usuario tiene un Transportista
                # IMPORTANTE: El campo en PuntoRecogida se llama 'transportista'
                return qs.filter(pedido__usuario__transportista=empresa)
            
        except Exception as e:
            print(f"Error en el filtro de transportista: {e}")
        
        return qs.none()
    
    def has_import_permission(self, request):
        # Solo el superusuario puede ver el botón de Importar
        return request.user.is_superuser

    # def has_export_permission(self, request):
        # Si quieres que el transportista TAMPOCO pueda exportar a Excel:
    #    return request.user.is_superuser

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        
        inline = LineaAlbaranInline(self.model, self.admin_site)
        # 2. CAMBIO DE NOMBRE: Personalizamos el título del Inline
        inline.verbose_name_plural = "Materiales recogidos"
        inline.verbose_name = "Material recogido"
        
        inline.model = LineaPedido
        return [inline]

    def save_model(self, request, obj, form, change):
        # 1. Obtenemos la fecha de ejecución del formulario
        f_ejecucion = form.cleaned_data.get('fecha_ejecucion')
        
        if f_ejecucion:
            # 2. Sincronizamos con el pedido vinculado
            obj.pedido.fecha_ejecucion = f_ejecucion
            obj.pedido.save()
            
            # 3. La fecha de emisión siempre se recalcula al día 1 del mes de EJECUCIÓN
            obj.fecha_emision = date(f_ejecucion.year, f_ejecucion.month, 1)
        
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Corregimos la firma del método para evitar el TypeError.
        El objeto actual (Albarán) se encuentra en kwargs['obj']
        """
        if db_field.name == "vehiculo":
            # Extraemos el objeto albarán de los kwargs
            obj = kwargs.get('obj')
            
            if obj and hasattr(obj, 'pedido') and obj.pedido.usuario:
                punto_recogida = obj.pedido.usuario
                # Buscamos al transportista asignado al punto de recogida
                transportista_obj = getattr(punto_recogida, 'transportista', None)
                
                if transportista_obj:
                    # Filtramos los vehículos de Logística que pertenecen al transportista
                    # Y nos aseguramos de que estén activos
                    kwargs["queryset"] = Vehiculo.objects.filter(
                        transportista=transportista_obj, 
                        activo=True
                    )
            else:
                # Si no hay contexto, podemos mostrar todos o ninguno
                kwargs["queryset"] = Vehiculo.objects.filter(activo=True)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def display_pedido_info(self, obj):
        return f"Pedido ID: {obj.pedido.id} - Fecha: {obj.pedido.fecha_programada}"
    display_pedido_info.short_description = "Información del Pedido"

    def display_cliente(self, obj):
        # Buscamos el cliente principal a través del pedido -> usuario
        punto = obj.pedido.usuario
        cliente = punto.cliente or (punto.subcliente.cliente if punto.subcliente else None)
        if cliente:
            return format_html("<strong>{}</strong> (CIF: {})", cliente.razon_social, cliente.cif)
        return "-"
    display_cliente.short_description = "Cliente / Subcliente"

    def display_usuario(self, obj):
        # El usuario es el Punto de Recogida
        punto = obj.pedido.usuario
        return format_html("<strong>{}</strong><br>{} {}, {} - {} ({})", punto.nombre, punto.direccion, punto.numero, punto.cp, punto.localidad, punto.provincia)
    display_usuario.short_description = "Usuario / Punto de recogida"

    def display_gestor_residuos(self, obj):
        # El gestor asignado al punto de recogida
        gestor = obj.pedido.usuario.gestor
        if gestor:
            return format_html("<strong>{}</strong><br>{} {}, {} - {} ({})", gestor.nombre, gestor.direccion, gestor.numero, gestor.cp, gestor.localidad, gestor.provincia)
        return format_html("<span style='color: orange;'>⚠️ No asignado</span>")
    display_gestor_residuos.short_description = "Gestor de Residuos"

    def display_transportista(self, obj):
        # El transportista habitual configurado en el Punto de Recogida
        transp = obj.pedido.usuario.transportista
        if transp:
            return format_html("<strong>{}</strong><br>{} {}, {} - {} ({})", transp.nombre, transp.direccion, transp.numero, transp.cp, transp.localidad, transp.provincia)
        return format_html("<span style='color: red;'>⚠️ Sin transportista asignado</span>")
    
    display_transportista.short_description = "Transportista"

    def acciones_pdf(self, obj):
        if not obj.id:
            return "-"
        
        url_pdf = reverse('albaran_pdf_download', kwargs={'albaran_id': obj.id})
        url_di = reverse('albaran_di_download', kwargs={'albaran_id': obj.id})

        return format_html(
            '<a class="button" href="{}" target="_blank" style="background-color:#447e9b; color:white; padding:5px 10px; border-radius:4px; margin-right:5px;">🖨️ Albarán</a>'
            '<a class="button" href="{}" target="_blank" style="background-color:#28a745; color:white; padding:5px 10px; border-radius:4px;">📄 DI</a>',
            url_pdf, url_di
        )
    
    acciones_pdf.short_description = "Documentos"
    
    def imprimir_pdf(self, obj):
        if obj.id:
            url = reverse('albaran_pdf_download', args=[obj.id])
            return format_html(
                '<a class="button" href="{}" target="_blank" style="background-color:#447e9b; color:white; padding:5px 10px; border-radius:4px;">🖨️ PDF</a>', 
                url
            )
        return "-"
    
    imprimir_pdf.short_description = "Acciones"

    def imprimir_di(self, obj):
        if obj.id:
            url = reverse('albaran_di_download', args=[obj.id])
            return format_html(
                '<a class="button" href="{}" target="_blank" style="background-color:#28a745; color:white; padding:5px 10px; border-radius:4px;">📄 DI</a>', 
                url
            )
        return "-"
    
    imprimir_di.short_description = "Acciones"


    def has_add_permission(self, request):
        # Solo los superusuarios podrían crear un albarán a mano
        return False

    def get_inline_instances(self, request, obj=None):
        # Si no hay objeto (estamos creando), no mostramos líneas
        if not obj:
            return []
        
        # Creamos el Inline dinámicamente
        inline = LineaAlbaranInline(self.model, self.admin_site)
        
        # Le decimos al Inline que su "padre" para buscar datos es el PEDIDO, no el Albarán
        inline.model = LineaPedido
        # Forzamos que el inline use el ID del pedido vinculado al albarán
        return [inline]

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            # Aquí ocurre la magia: cambiamos la instancia de búsqueda
            if obj:
                inline.instance = obj.pedido
            yield inline.get_formset(request, obj), inline

    def get_cliente(self, obj):
        entidad = obj.pedido.usuario.cliente or obj.pedido.usuario.subcliente
        return entidad.razon_social if entidad else "N/A"
    get_cliente.short_description = 'Cliente'
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from utils import BaseAdmin
from .models import Transportista, Vehiculo, GestorResiduos, Cliente, Subcliente, PuntoRecogida

@admin.register(Transportista)
class TransportistaAdmin(ImportExportModelAdmin, BaseAdmin):
    list_display = ('id', 'codigo', 'nombre', 'localidad', 'ecoeffort', 'activo')
    list_display_links = ('id', 'codigo', 'nombre')
    list_editable = ('ecoeffort', 'activo')
    ordering = ('id',)
    search_fields = ('codigo', 'nombre', 'cif_nif', 'localidad')
    # Filtro lateral para separar rápidos los propios de los externos
    list_filter = ('ecoeffort', 'activo', 'provincia')

@admin.register(Vehiculo)
class VehiculoAdmin(ImportExportModelAdmin, BaseAdmin):
    list_display = ('id', 'matricula', 'get_transportista_status', 'activo')
    list_filter = ('activo', 'transportista')
    search_fields = ('matricula',)
    list_editable = ('activo',)
    ordering = ('id',)

    @admin.display(description="Transportista Asociado") # Esto es lo que se muestra como cabecera de la columna
    def get_transportista_status(self, obj):
        if obj.transportista:
            return obj.transportista.nombre
        return "⚠️ Sin Transportista"
    
@admin.register(GestorResiduos)
class GestorResiduosAdmin(ImportExportModelAdmin, BaseAdmin):
    list_display = ('id', 'codigo', 'nombre', 'localidad', 'activo')
    list_display_links = ('id', 'codigo', 'nombre')
    list_editable = ('activo',)
    search_fields = ('codigo', 'nombre', 'cif_nif', 'nima')
    list_filter = ('activo', 'provincia')
    ordering = ('id',)

@admin.register(Cliente)
class ClienteAdmin(ImportExportModelAdmin, BaseAdmin):
    list_display = ('id', 'codigo', 'razon_social', 'cif', 'localidad_fiscal', 'activo')
    list_display_links = ('id', 'codigo', 'razon_social')
    list_editable = ('activo',)
    list_filter = ('activo', 'provincia_fiscal', 'fecha_pago')
    search_fields = ('codigo', 'razon_social', 'cif')

    fieldsets = (
        ("Identificación", {
            'fields': ('codigo', 'razon_social', 'cif', 'activo')
        }),
        ("Información Fiscal", {
            'fields': (
                'email_fiscal', 'direccion_fiscal', 'numero_fiscal', 
                'localidad_fiscal', 'cp_fiscal', 'provincia_fiscal', 
                'observaciones_fiscal'
            ),
        }),
        # Todo esto irá en UNA SOLA pestaña llamada "Facturación"
        ("Información de Facturación", {
            'fields': (
                'mismos_datos', # El check va el primero dentro de la pestaña
                'email_facturacion', 'direccion_facturacion', 'numero_facturacion', 
                'localidad_facturacion', 'cp_facturacion', 'provincia_facturacion', 
                'observaciones_facturacion'
            ),
        }),
        ("Finanzas", {
            'fields': ('iban', 'fecha_pago')
        }),
    )

    class Media:
        js = ('js/cliente_admin.js',)
    
@admin.register(Subcliente)
class SubclienteAdmin(ImportExportModelAdmin, BaseAdmin):
    list_display = ('id', 'codigo', 'razon_social', 'cliente', 'localidad', 'activo')
    list_filter = ('cliente', 'provincia', 'activo')
    search_fields = ('codigo', 'razon_social', 'cif', 'email')
    list_display_links = ('id', 'codigo', 'razon_social')

    fieldsets = (
        ("Relación Comercial", {
            'fields': ('cliente', 'activo')
        }),
        ("Datos Identificativos", {
            'fields': ('codigo', 'cif', 'razon_social')
        }),
        ("Dirección", {
            'fields': ('direccion', 'numero', 'localidad', 'cp', 'provincia')
        }),
        ("Contacto", {
            'fields': ('contacto', 'telefono1', 'telefono2', 'email')
        }),
    )

@admin.register(PuntoRecogida)
class PuntoRecogidaAdmin(ImportExportModelAdmin, BaseAdmin):
    list_display = ('codigo', 'nombre', 'get_asignacion', 'localidad', 'zona', 'activo')
    list_filter = ('zona', 'provincia', 'activo', 'cliente')
    search_fields = ('codigo', 'nombre', 'cif', 'localidad')
    
    fieldsets = (
        ("Asignación y Logística", {
            'fields': (
                'cliente', 
                'subcliente', 
                'zona', 
                'transportista', # Nuevo
                'gestor',        # Nuevo
                'activo'
            ),
            'description': "Configure aquí los actores principales para este punto de recogida."
        }),
        ("Datos del Punto", {
            'fields': ('codigo', 'cif', 'nombre')
        }),
        ("Localización", {
            'fields': ('direccion', 'numero', 'localidad', 'cp', 'provincia')
        }),
        ("Contacto", {
            'fields': ('contacto', 'telefono1', 'telefono2', 'email')
        }),
    )

    def get_asignacion(self, obj):
        if obj.cliente and obj.subcliente:
            return f"{obj.cliente} / {obj.subcliente}"
        return obj.cliente or obj.subcliente
    get_asignacion.short_description = "Asignado a"
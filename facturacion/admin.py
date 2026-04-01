from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from utils import BaseAdmin, BaseInline
from .models import Factura, LineaFactura


class LineaFacturaInline(BaseInline):
    model = LineaFactura
    extra = 1
    fields = ('descripcion', 'cantidad', 'precio_unitario', 'importe')
    readonly_fields = ('importe',)


@admin.register(Factura)
class FacturaAdmin(BaseAdmin, ImportExportModelAdmin):
    list_display = ('numero', 'cliente', 'fecha_emision', 'fecha_vencimiento', 'estado', 'base_imponible', 'cuota_impuesto', 'total')
    list_display_links = ('numero', 'cliente')
    list_filter = ('estado', 'serie', 'impuesto', 'fecha_emision')
    search_fields = ('numero', 'cliente__razon_social', 'cliente__codigo', 'cliente__cif')
    ordering = ('-fecha_emision', '-numero')
    readonly_fields = ('numero', 'base_imponible', 'cuota_impuesto', 'total')
    inlines = [LineaFacturaInline]
    date_hierarchy = 'fecha_emision'

    fieldsets = (
        ("Identificación", {
            'fields': ('numero', 'serie', 'estado'),
        }),
        ("Cliente y Albaranes", {
            'fields': ('cliente', 'albaranes'),
        }),
        ("Fechas", {
            'fields': ('fecha_emision', 'fecha_vencimiento'),
        }),
        ("Importes", {
            'fields': ('impuesto', 'base_imponible', 'cuota_impuesto', 'total'),
        }),
        ("Observaciones", {
            'fields': ('observaciones',),
            'classes': ('collapse',),
        }),
    )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        obj.recalcular_totales()
        obj.save()

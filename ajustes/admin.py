from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Zona, FechaPago, Impuesto, Periodicidad, ConceptoFacturable, TipoEnvase, TipoResiduo, DatosConfigurables

@admin.register(Zona)
class ZonaAdmin(ImportExportModelAdmin):
    list_display = ('id', 'nombre', 'activo')
    list_editable = ('activo',)
    list_display_links = ('id', 'nombre')
    sortable_by = ('id', 'nombre', 'activo')
    list_per_page = 10
    search_fields = ('nombre',)
    ordering = ('id',)

@admin.register(FechaPago)
class FechaPagoAdmin(ImportExportModelAdmin):
    list_display = ('id', 'nombre', 'activo')
    list_display_links = ('id', 'nombre')
    list_editable = ('activo',)
    sortable_by = ('id', 'nombre', 'activo')
    list_per_page = 10
    search_fields = ('nombre',)
    ordering = ('id',)

@admin.register(Impuesto)
class ImpuestoAdmin(ImportExportModelAdmin):
    list_display = ('id', 'nombre', 'valor', 'activo')
    list_display_links = ('id', 'nombre')
    list_editable = ('valor', 'activo') # ¡También puedes editar el valor desde la tabla!
    sortable_by = ('id', 'nombre', 'valor', 'activo')
    list_per_page = 10
    search_fields = ('nombre',)
    ordering = ('id',)

@admin.register(Periodicidad)
class PeriodicidadAdmin(ImportExportModelAdmin):
    list_display = ('id', 'nombre', 'activo')
    list_display_links = ('id', 'nombre')
    list_editable = ('activo',)
    sortable_by = ('id', 'nombre', 'activo')
    list_per_page = 10
    search_fields = ('nombre',)
    ordering = ('id',)

@admin.register(ConceptoFacturable)
class ConceptoFacturableAdmin(ImportExportModelAdmin):
    list_display = ('id', 'nombre', 'precio_base', 'precio_adicional', 'activo')
    list_display_links = ('id', 'nombre')
    list_editable = ('precio_base', 'precio_adicional', 'activo')
    # Ordenamos por ID de forma descendente para ver los nuevos arriba
    ordering = ('id',)
    search_fields = ('nombre',)
    list_per_page = 10

@admin.register(TipoEnvase)
class TipoEnvaseAdmin(ImportExportModelAdmin):
    list_display = ('id', 'nombre', 'capacidad', 'precio', 'tipo', 'activo')
    list_display_links = ('id', 'nombre')
    list_editable = ('precio', 'tipo', 'activo') # Permite cambiar tipo y precio rápido
    ordering = ('id',)
    search_fields = ('nombre', 'capacidad')
    list_filter = ('tipo', 'activo') # Añadimos filtros laterales para organizar mejor
    list_per_page = 10

@admin.register(TipoResiduo)
class TipoResiduoAdmin(ImportExportModelAdmin):
    list_display = ('id', 'codigo_ler', 'nombre', 'precio_kg', 'activo')
    list_display_links = ('id', 'codigo_ler', 'nombre')
    list_editable = ('precio_kg', 'activo')
    ordering = ('-id',)
    # Permitimos buscar tanto por el código LER como por el nombre común
    search_fields = ('codigo_ler', 'nombre')
    list_per_page = 20

@admin.register(DatosConfigurables)
class DatosConfigurablesAdmin(ImportExportModelAdmin):
    list_display = ('clave', 'valor')
    list_editable = ('valor',) # Permite cambiar el valor rápido desde la tabla
    search_fields = ('clave', 'valor')
    # Aquí no ordenamos por ID porque no existe, ordenamos por clave (A-Z)
    ordering = ('clave',)
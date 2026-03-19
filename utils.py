from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from datetime import date, timedelta

class BaseAdmin(admin.ModelAdmin):
    """Clase base para eliminar botones de relación en Modelos"""
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        for field_name, field in form.base_fields.items():
            if hasattr(field.widget, 'can_add_related'):
                field.widget.can_add_related = False
                field.widget.can_change_related = False
                field.widget.can_delete_related = False
                field.widget.can_view_related = False
        return form
    
    actions = ['duplicar_registro']

    @admin.action(description="Duplicar seleccionado/s")
    def duplicar_registro(modeladmin, request, queryset):
        for objeto in queryset:
            # Guardamos la PK original para saber si es manual
            old_pk = objeto.pk
            
            # 1. Caso especial para modelos con PK manual (como tu CharField)
            if isinstance(old_pk, str):
                nuevo_valor_pk = f"{old_pk}_copia"
                # Verificamos que no exista ya esa copia para evitar errores
                contador = 1
                while objeto.__class__.objects.filter(pk=nuevo_valor_pk).exists():
                    nuevo_valor_pk = f"{old_pk}_copia_{contador}"
                    contador += 1
                objeto.pk = nuevo_valor_pk
            else:
                # 2. Caso estándar para IDs numéricos
                objeto.pk = None

            # Intentamos dar un nombre amigable al valor si existe
            if hasattr(objeto, 'valor') and isinstance(objeto.valor, str):
                objeto.valor = f"{objeto.valor} (Copia)"
            
            objeto.save()

class BaseInline(admin.TabularInline):
    """Clase base para eliminar botones de relación en Inlines"""
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        for field_name, field in formset.form.base_fields.items():
            if hasattr(field.widget, 'can_add_related'):
                field.widget.can_add_related = False
                field.widget.can_change_related = False
                field.widget.can_delete_related = False
                field.widget.can_view_related = False
        return formset
    
class FechaRangoFilter(SimpleListFilter):
    """
    Filtro genérico para rangos de fecha utilizable en cualquier modelo.
    Debes definir 'parameter_name' y 'title' al heredar.
    """
    def lookups(self, request, model_admin):
        return (
            ('hoy', 'Hoy'),
            ('7_dias', 'Últimos 7 días'),
            ('este_mes', 'Este mes'),
            ('futuros', 'Próximos (Futuros)'),
        )

    def queryset(self, request, queryset):
        hoy = date.today()
        # Usamos self.parameter_name para que funcione con cualquier nombre de campo
        campo = self.parameter_name
        
        if self.value() == 'hoy':
            return queryset.filter(**{campo: hoy})
            
        if self.value() == '7_dias':
            hace_una_semana = hoy - timedelta(days=7)
            return queryset.filter(**{f"{campo}__range": [hace_una_semana, hoy]})
            
        if self.value() == 'este_mes':
            return queryset.filter(**{f"{campo}__year": hoy.year, f"{campo}__month": hoy.month})
            
        if self.value() == 'futuros':
            return queryset.filter(**{f"{campo}__gt": hoy})
            
        return queryset
    
class FiltroFechaProgramada(FechaRangoFilter):
    title = 'Fecha programada'
    parameter_name = 'fecha_programada'

class FiltroFechaEjecucion(FechaRangoFilter):
    title = 'Fecha de ejecución'
    parameter_name = 'fecha_ejecucion'
    
class FiltroFechaCreacion(FechaRangoFilter):
    title = 'Fecha de registro'
    parameter_name = 'created_at'

class FiltroFechaInicio(FechaRangoFilter):
    title = 'Fecha de inicio'
    parameter_name = 'fecha_inicio'
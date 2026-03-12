from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Perfil

# 1. Definimos cómo se ve el perfil dentro del usuario
class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Información Adicional'

# 2. Personalizamos el UserAdmin original
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilInline, )

# 3. Reinyectamos la configuración: quitamos el original y ponemos el nuestro
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
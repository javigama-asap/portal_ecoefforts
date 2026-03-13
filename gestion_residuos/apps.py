from django.apps import AppConfig

class GestionResiduosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_residuos'
    verbose_name = "OPERATIVA" # Esto es lo que verá el usuario

    def ready(self):
        from django.contrib.auth.models import User, Group

        # Nomenclatura para Usuarios
        User._meta.verbose_name = "Usuario del Panel"
        User._meta.verbose_name_plural = "Usuarios del Panel"
        
        # Nomenclatura para Grupos -> Roles
        Group._meta.verbose_name = "Rol"
        Group._meta.verbose_name_plural = "Roles"

        from django.apps import apps

        # Aquí sí es seguro porque el registro ya está cargado
        if apps.is_installed('django.contrib.auth'):
            apps.get_app_config('auth').verbose_name = "SEGURIDAD Y ACCESOS"
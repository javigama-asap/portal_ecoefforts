from django.db import models
from django.contrib.auth.models import User

class Perfil(models.Model):
    # Relacionamos este perfil con un Usuario del Panel
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    
    # Campo extra que me pediste
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles"

    def __str__(self):
        return f"Perfil de {self.user.username}"

from django.db import models
from django.core.exceptions import ValidationError
from configuracion.constantes import PROVINCIAS_CHOICES # Importación limpia

class Zona(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Zona")
    activo = models.BooleanField(default=True, verbose_name="¿Zona activa?")

    class Meta:
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"

    def __str__(self):
        return self.nombre

class FechaPago(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Fecha de pago")
    activo = models.BooleanField(default=True, verbose_name="¿Opción activa?")

    class Meta:
        verbose_name = "Fecha de pago"
        verbose_name_plural = "Fechas de pago"

    def __str__(self):
        return self.nombre

class Impuesto(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Detalle del Impuesto")
    # max_digits=5 y decimal_places=3 permite números hasta 99.999 (ej: 21.000) con tres decimales para mayor precisión
    valor = models.DecimalField(max_digits=5, decimal_places=3, verbose_name="Valor (%)")
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")

    class Meta:
        verbose_name = "Impuesto"
        verbose_name_plural = "Impuestos"

    def __str__(self):
        return f"{self.nombre} ({self.valor}%)"

class Periodicidad(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Denominación")
    activo = models.BooleanField(default=True, verbose_name="¿Activa?")

    class Meta:
        verbose_name = "Periodicidad"
        verbose_name_plural = "Periodicidades"

    def __str__(self):
        return self.nombre
    
class ConceptoFacturable(models.Model):
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Concepto")
    precio_base = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Precio Base (€)")
    
    # Estos campos siguen permitiendo null/blank a nivel de base de datos para que el clean() gestione la lógica
    texto_adicional = models.CharField(max_length=255, verbose_name="Texto Adicional", null=True, blank=True)
    precio_adicional = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Precio Adicional (€)", null=True, blank=True)
    
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")

    class Meta:
        verbose_name = "Concepto Facturable"
        verbose_name_plural = "Conceptos Facturables"

    def clean(self):
        # Ejecutamos la validación base
        super().clean()

        # Lógica: Si hay texto, el precio es obligatorio. Si hay precio, el texto es obligatorio.
        if self.texto_adicional and self.precio_adicional is None:
            raise ValidationError({
                'precio_adicional': 'Si defines un texto adicional, debes asignar un precio adicional (aunque sea 0).'
            })
        
        if self.precio_adicional is not None and not self.texto_adicional:
            raise ValidationError({
                'texto_adicional': 'Si defines un precio adicional, debes explicar qué es en el texto adicional.'
            })

    def __str__(self):
        return self.nombre
    
class TipoEnvase(models.Model):
    # Definimos las opciones para el desplegable
    OPCIONES_TIPO = [
        ('normal', 'Normal'),
        ('especial', 'Especial'),
    ]

    nombre = models.CharField(max_length=100, verbose_name="Nombre del Envase")
    capacidad = models.CharField(max_length=10, null=True, blank=True, verbose_name="Capacidad en litros")
    precio = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Precio Alquiler/Venta (€)", default=0.000)
    tipo = models.CharField(
        max_length=10, 
        choices=OPCIONES_TIPO, 
        default='normal', 
        verbose_name="Tipo de Envase"
    )
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")

    class Meta:
        verbose_name = "Tipo de Envase"
        verbose_name_plural = "Tipos de Envases"

    def __str__(self):
        return f"{self.nombre} ({self.capacidad})"

class TipoResiduo(models.Model):
    codigo_ler = models.CharField(max_length=20, verbose_name="Código LER")
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Residuo")
    # Usamos DecimalField para el precio por kilo para evitar errores de redondeo
    precio_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        verbose_name="Precio por Kg (€)"
    )
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")

    class Meta:
        verbose_name = "Tipo de Residuo"
        verbose_name_plural = "Tipos de Residuos"

    def __str__(self):
        return f"{self.codigo_ler} - {self.nombre}"
    
class DatosConfigurables(models.Model):
    # Definimos 'clave' como clave primaria para que no cree el ID automático
    clave = models.CharField(
        max_length=100, 
        primary_key=True, 
        verbose_name="Nombre de la Variable"
    )
    valor = models.CharField(max_length=150, verbose_name="Valor / Contenido")

    class Meta:
        verbose_name = "Dato Configurable"
        verbose_name_plural = "Datos Configurables"

    def __str__(self):
        return f"{self.clave}: {self.valor[:30]}..."
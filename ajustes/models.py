from django import forms
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
    
class ConceptoFacturable(models.Model):
    TIPO_CHOICES = [
        ('General', 'General'),
        ('Envase', 'Envase'),
        ('Residuo', 'Residuo'),
    ]

    nombre = models.CharField(max_length=150)
    tipo_concepto = models.CharField(max_length=10, choices=TIPO_CHOICES, default='General')
    
    # Relaciones para los selectores (flexibles)
    envase = models.ForeignKey(TipoEnvase, on_delete=models.SET_NULL, null=True, blank=True)
    residuo = models.ForeignKey(TipoResiduo, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Datos base
    cantidad_base_incluida = models.IntegerField(default=1, verbose_name="Cantidad incluida en el precio base (kg, envases, etc.)")
    precio_base = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Precio del servicio base (€)")
    
    # Bloque Adicional
    info_adicional = models.BooleanField(default=False, verbose_name="¿Tiene tarificación adicional?")
    descripcion_adicional = models.CharField(max_length=255, null=True, blank=True, verbose_name="Descripción de la tarificación adicional")
    cantidad_adicional = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Unidades por bloque adicional (kg, envases, etc.)")
    precio_adicional = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Precio bloque adicional (€)")
    
    activo = models.BooleanField(default=True)

    @property
    def selector_concepto(self):
        """Devuelve el objeto vinculado (Envase o Residuo) o None"""
        if self.tipo_concepto == 'Envase':
            return self.envase
        if self.tipo_concepto == 'Residuo':
            return self.residuo
        return None

    def clean(self):
        super().clean()
        
        # Validación de Info Adicional
        if self.info_adicional:
            if not self.descripcion_adicional or self.cantidad_adicional is None or self.precio_adicional is None:
                raise ValidationError("Si 'Info Adicional' es SÍ, los campos de descripción, cantidad y precio adicional son obligatorios.")
        
        # Validación de Selectores según tipo
        if self.tipo_concepto == 'Envase' and not self.envase:
            raise ValidationError({'envase': 'Debe seleccionar un envase para este tipo de concepto.'})
        if self.tipo_concepto == 'Residuo' and not self.residuo:
            raise ValidationError({'residuo': 'Debe seleccionar un residuo para este tipo de concepto.'})

    def __str__(self):
        return self.nombre
    
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
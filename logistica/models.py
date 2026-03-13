from django.db import models
from configuracion.constantes import PROVINCIAS_CHOICES # Importación limpia
from django.core.exceptions import ValidationError
from ajustes.models import Zona, FechaPago # Importación directa para evitar dependencias circulares

class Transportista(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    nombre = models.CharField(max_length=150, verbose_name="Identificación del Transportista")
    cif_nif = models.CharField(max_length=20, verbose_name="CIF/NIF")
    
    # Dirección detallada
    direccion = models.CharField(max_length=200, verbose_name="Dirección")
    numero = models.CharField(max_length=10, verbose_name="Número")
    localidad = models.CharField(max_length=100, verbose_name="Localidad")
    cp = models.CharField(max_length=10, verbose_name="C.P.")
    provincia = models.CharField(
        max_length=100, 
        choices=PROVINCIAS_CHOICES, 
        default='Madrid', 
        verbose_name="Provincia"
    )
    
    # Contacto
    email = models.EmailField(verbose_name="Correo Electrónico")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    
    # Datos Legales / Residuos
    nima = models.CharField(max_length=30, verbose_name="NIMA", help_text="Número de Identificación Medioambiental")
    reg = models.CharField(max_length=50, verbose_name="Nº Registro", help_text="Registro de transportista de residuos")
    
    # Control Interno
    ecoeffort = models.BooleanField(default=True, verbose_name="¿Es EcoEffort?")
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")

    class Meta:
        verbose_name = "Transportista"
        verbose_name_plural = "Transportistas"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class Vehiculo(models.Model):
    matricula = models.CharField(
        max_length=15, 
        unique=True, 
        verbose_name="Matrícula"
    )
    
    # Relación opcional: si el transportista se borra, el campo queda en NULL
    transportista = models.ForeignKey(
        'Transportista', 
        on_delete=models.SET_NULL, # <--- Cambiado a SET_NULL
        null=True,                 # <--- Permite valor nulo en DB
        blank=True,                # <--- Permite dejarlo vacío en el formulario
        related_name='vehiculos',
        verbose_name="Transportista"
    )
    
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")

    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"

    def __str__(self):
        nombre_transp = self.transportista.nombre if self.transportista else "SIN ASIGNAR"
        return f"{self.matricula} ({nombre_transp})"

class GestorResiduos(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    nombre = models.CharField(max_length=150, verbose_name="Nombre / Razón Social")
    cif_nif = models.CharField(max_length=20, verbose_name="CIF/NIF")
    
    # Dirección granular
    direccion = models.CharField(max_length=200, verbose_name="Dirección")
    numero = models.CharField(max_length=10, verbose_name="Número")
    localidad = models.CharField(max_length=100, verbose_name="Localidad")
    cp = models.CharField(max_length=10, verbose_name="C.P.")
    provincia = models.CharField(
        max_length=100, 
        choices=PROVINCIAS_CHOICES, 
        default='Madrid', 
        verbose_name="Provincia"
    )
    
    # Contacto
    email = models.EmailField(verbose_name="Correo Electrónico")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    
    # Datos Legales
    nima = models.CharField(max_length=30, verbose_name="NIMA", help_text="Número de Identificación Medioambiental")
    reg = models.CharField(max_length=50, verbose_name="Nº Registro / Autorización")
    
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")

    class Meta:
        verbose_name = "Gestor de Residuos"
        verbose_name_plural = "Gestores de Residuos"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class Cliente(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    razon_social = models.CharField(max_length=150, verbose_name="Razón Social")
    cif = models.CharField(max_length=20, verbose_name="CIF")
    
    # DATOS FISCALES
    email_fiscal = models.EmailField(verbose_name="Email Fiscal")
    direccion_fiscal = models.CharField(max_length=200, verbose_name="Dirección Fiscal")
    numero_fiscal = models.CharField(max_length=10, verbose_name="Número Fiscal")
    localidad_fiscal = models.CharField(max_length=100, verbose_name="Localidad Fiscal")
    cp_fiscal = models.CharField(max_length=10, verbose_name="C.P. Fiscal")
    provincia_fiscal = models.CharField(
        max_length=100, 
        choices=PROVINCIAS_CHOICES, 
        verbose_name="Provincia Fiscal"
    )
    observaciones_fiscal = models.TextField(blank=True, null=True, verbose_name="Observaciones Fiscales")

    mismos_datos = models.BooleanField(
        default=True, # Marcado por defecto
        verbose_name="¿Usar mismos datos que los fiscales?"
    )

    # DATOS FACTURACIÓN
    email_facturacion = models.EmailField(verbose_name="Email Facturación")
    direccion_facturacion = models.CharField(max_length=200, verbose_name="Dirección Facturación")
    numero_facturacion = models.CharField(max_length=10, verbose_name="Número Facturación")
    localidad_facturacion = models.CharField(max_length=100, verbose_name="Localidad Facturación")
    cp_facturacion = models.CharField(max_length=10, verbose_name="C.P. Facturación")
    provincia_facturacion = models.CharField(
        max_length=100, 
        choices=PROVINCIAS_CHOICES, 
        verbose_name="Provincia Facturación"
    )
    observaciones_facturacion = models.TextField(blank=True, null=True, verbose_name="Observaciones Facturación")

    # DATOS BANCARIOS Y PAGO
    iban = models.CharField(max_length=34, verbose_name="IBAN")
    fecha_pago = models.ForeignKey(
        'ajustes.FechaPago', 
        on_delete=models.SET_NULL, # Si se borra la fecha, el cliente queda con NULL
        null=True,                 # Permite nulo en la base de datos
        blank=True,                # Permite dejarlo vacío en el panel admin
        verbose_name="Día de Pago"
    )
    
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"{self.codigo} - {self.razon_social}"
    
    def save(self, *args, **kwargs):
        # El bloque debe estar indentado con 4 espacios respecto al 'def'
        if self.mismos_datos:
            self.email_facturacion = self.email_fiscal
            self.direccion_facturacion = self.direccion_fiscal
            self.numero_facturacion = self.numero_fiscal
            self.localidad_facturacion = self.localidad_fiscal
            self.cp_facturacion = self.cp_fiscal
            self.provincia_facturacion = self.provincia_fiscal
            self.observaciones_facturacion = self.observaciones_fiscal
        
        # Llamada obligatoria al método save original de Django
        super().save(*args, **kwargs)

class Subcliente(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    cliente = models.ForeignKey(
        'Cliente', 
        on_delete=models.SET_NULL, # Si el cliente desaparece, queda nulo
        null=True, 
        blank=False, # Pero es requerido al crearlo
        related_name='subclientes',
        verbose_name="Cliente Principal"
    )
    razon_social = models.CharField(max_length=200, verbose_name="Razón Social")
    cif = models.CharField(max_length=20, verbose_name="CIF/NIF", blank=True, null=True)
    
    # Ubicación
    direccion = models.CharField(max_length=200, verbose_name="Dirección")
    numero = models.CharField(max_length=10, verbose_name="Número")
    localidad = models.CharField(max_length=100, verbose_name="Localidad")
    cp = models.CharField(max_length=10, verbose_name="C.P.")
    provincia = models.CharField(max_length=100, choices=PROVINCIAS_CHOICES, verbose_name="Provincia")
    
    # Contacto
    contacto = models.CharField(max_length=100, verbose_name="Persona de Contacto", blank=True, null=True)
    telefono1 = models.CharField(max_length=20, verbose_name="Teléfono 1", blank=True, null=True)
    telefono2 = models.CharField(max_length=20, verbose_name="Teléfono 2", blank=True, null=True)
    email = models.EmailField(verbose_name="Email", blank=True, null=True)
    
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")

    class Meta:
        verbose_name = "Subcliente"
        verbose_name_plural = "Subclientes"

    def __str__(self):
        return f"{self.codigo} - {self.razon_social}"
    
class PuntoRecogida(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    nombre = models.CharField(max_length=200, verbose_name="Nombre / Razón Social")
    cif = models.CharField(max_length=20, verbose_name="CIF/NIF")
    
    # Relaciones nulables pero con lógica de validación
    cliente = models.ForeignKey(
        'Cliente', on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='puntos_recogida', verbose_name="Cliente"
    )
    subcliente = models.ForeignKey(
        'Subcliente', on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='puntos_recogida', verbose_name="Subcliente"
    )

    transportista = models.ForeignKey(
        'Transportista', # Ajusta el nombre de la app si es necesario
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Transportista Habitual"
    )
    gestor = models.ForeignKey(
        'GestorResiduos', # Ajusta el nombre de la app si es necesario
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Gestor de Residuos Destino"
    )
    
    # Ubicación y Zona
    direccion = models.CharField(max_length=200, verbose_name="Dirección")
    numero = models.CharField(max_length=10, verbose_name="Número")
    localidad = models.CharField(max_length=100, verbose_name="Localidad")
    cp = models.CharField(max_length=10, verbose_name="C.P.")
    provincia = models.CharField(max_length=100, choices=PROVINCIAS_CHOICES, verbose_name="Provincia")
    zona = models.ForeignKey('ajustes.Zona', on_delete=models.PROTECT, verbose_name="Zona Logística")
    
    # Contacto
    contacto = models.CharField(max_length=100, verbose_name="Persona de Contacto", blank=True, null=True)
    telefono1 = models.CharField(max_length=20, verbose_name="Teléfono 1", blank=True, null=True)
    telefono2 = models.CharField(max_length=20, verbose_name="Teléfono 2", blank=True, null=True)
    email = models.EmailField(verbose_name="Email", blank=True, null=True)
    
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")

    def clean(self):
        # Validación obligatoria: Debe tener Cliente O Subcliente
        if not self.cliente and not self.subcliente:
            raise ValidationError("Debe asignar este punto de recogida a un Cliente o a un Subcliente.")

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
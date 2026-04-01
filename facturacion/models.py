from django.db import models
from django.forms import ValidationError
from logistica.models import Cliente
from ajustes.models import Impuesto
from operativa.models import Albaran


ESTADO_FACTURA_CHOICES = [
    ('BORRADOR', 'Borrador'),
    ('EMITIDA', 'Emitida'),
    ('PAGADA', 'Pagada'),
    ('CANCELADA', 'Cancelada'),
]


class Factura(models.Model):
    serie = models.CharField(
        max_length=10,
        default='FAC',
        verbose_name="Serie",
    )
    numero = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name="Número de factura",
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        verbose_name="Cliente",
        related_name='facturas',
    )
    albaranes = models.ManyToManyField(
        Albaran,
        blank=True,
        verbose_name="Albaranes",
        related_name='facturas',
    )
    fecha_emision = models.DateField(verbose_name="Fecha de emisión")
    fecha_vencimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de vencimiento",
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_FACTURA_CHOICES,
        default='BORRADOR',
        verbose_name="Estado",
    )
    impuesto = models.ForeignKey(
        Impuesto,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Impuesto",
    )
    base_imponible = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Base imponible",
    )
    cuota_impuesto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Cuota de impuesto",
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Total",
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
    )

    def _calcular_siguiente_numero(self):
        ultima = Factura.objects.filter(
            serie=self.serie,
        ).order_by('-id').first()
        if ultima:
            try:
                partes = ultima.numero.split('-')
                ultimo_numero = int(partes[-1])
                nuevo_numero = ultimo_numero + 1
            except (ValueError, IndexError):
                nuevo_numero = 1
        else:
            nuevo_numero = 1
        return f"{self.serie}-{nuevo_numero:06d}"

    def recalcular_totales(self):
        base = sum(linea.importe for linea in self.lineas.all())
        self.base_imponible = base
        if self.impuesto:
            self.cuota_impuesto = round(base * self.impuesto.valor / 100, 2)
        else:
            self.cuota_impuesto = 0
        self.total = self.base_imponible + self.cuota_impuesto

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._calcular_siguiente_numero()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.fecha_vencimiento and self.fecha_emision:
            if self.fecha_vencimiento < self.fecha_emision:
                raise ValidationError({
                    'fecha_vencimiento': 'La fecha de vencimiento no puede ser anterior a la fecha de emisión.'
                })

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['-fecha_emision', '-numero']

    def __str__(self):
        return f"{self.numero} — {self.cliente}"


class LineaFactura(models.Model):
    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name='lineas',
        verbose_name="Factura",
    )
    descripcion = models.CharField(max_length=255, verbose_name="Descripción")
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=1,
        verbose_name="Cantidad",
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio unitario",
    )
    importe = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False,
        default=0,
        verbose_name="Importe",
    )

    def save(self, *args, **kwargs):
        self.importe = round(self.cantidad * self.precio_unitario, 2)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Línea de Factura"
        verbose_name_plural = "Líneas de Factura"

    def __str__(self):
        return f"{self.descripcion} ({self.factura.numero})"

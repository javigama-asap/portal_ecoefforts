from django.db import models
from django.dispatch import receiver
from django.forms import ValidationError
from ajustes.models import Periodicidad, ConceptoFacturable
from logistica.models import GestorResiduos, PuntoRecogida, Transportista # O Subcliente/PuntoRecogida según necesites
from datetime import date, timedelta
import calendar
from django.db.models.signals import post_save

class Servicio(models.Model):
    nombre = models.CharField(max_length=200, editable=False)
    usuario = models.ForeignKey(PuntoRecogida, on_delete=models.CASCADE, verbose_name="Usuario/Punto de Recogida")
    
    # CAMBIO: Ahora es una relación al modelo de ajustes, no un DateField
    periodicidad = models.ForeignKey(
        Periodicidad, 
        on_delete=models.PROTECT, 
        verbose_name="Periodicidad"
    )
    
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    activo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Al ser un objeto, accedemos al nombre o descripción de la periodicidad
        # Suponiendo que el modelo Periodicidad tiene un campo 'nombre'
        self.nombre = f"{self.periodicidad.nombre} - {self.usuario.codigo}"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    def __str__(self):
        return self.nombre

    def generar_pedidos_periodicos(self, fecha_limite_manual=None):

        if not self.activo: # O self.activo == 'NO' según tu modelo
            return 0, 0 # No genera ni borra nada

        hoy = date.today()

        if fecha_limite_manual:
            fecha_limite = fecha_limite_manual
        else:
            _, ultimo_dia = calendar.monthrange(hoy.year, hoy.month)
            fecha_limite = date(hoy.year, hoy.month, ultimo_dia)

        fechas_validas = []
        fecha_cursor = self.fecha_inicio
    
        # --- 1. CÁLCULO DE FECHAS VÁLIDAS ---

        # --- LOGICA DE PERIODICIDAD "A DEMANDA" ---
        if self.periodicidad.nombre == "A demanda":
            fechas_validas.append(self.fecha_inicio)
        
        # --- LOGICA RECURRENTE ---
        else:
            # Iteramos desde la fecha de inicio hasta la fecha límite
            while fecha_cursor <= fecha_limite:
                es_valida = False
                nombre_p = self.periodicidad.nombre.lower()

                if "diario" in nombre_p:
                    es_valida = True
                elif "2 veces por semana" in nombre_p:
                    es_valida = fecha_cursor.weekday() in [0, 3] # Lunes=0, Jueves=3
                elif "3 veces por semana" in nombre_p:
                    es_valida = fecha_cursor.weekday() in [0, 2, 4] # L, M, V
                elif "semanal" in nombre_p:
                    es_valida = fecha_cursor.weekday() == 0 # Lunes
                elif "decenal" in nombre_p:
                    # Cada 10 días exactos desde el inicio
                    diferencia = (fecha_cursor - self.fecha_inicio).days
                    es_valida = (diferencia % 10 == 0)
                elif "quincenal" in nombre_p:
                    # Lunes de cada 2 semanas (contando semanas ISO)
                    es_valida = (fecha_cursor.weekday() == 0 and 
                                ((fecha_cursor - self.fecha_inicio).days // 7) % 2 == 0)
                elif "bimensual" in nombre_p:
                    es_valida = fecha_cursor.day in [1, 15]
                elif "mensual" in nombre_p:
                    es_valida = fecha_cursor.day == 1
                # Para periodicidades mayores, saltamos de mes en mes para optimizar
                elif "bimestral" in nombre_p:
                    es_valida = (fecha_cursor.day == 1 and 
                                (fecha_cursor.month - self.fecha_inicio.month) % 2 == 0)
                elif "trimestral" in nombre_p:
                    es_valida = (fecha_cursor.day == 1 and 
                                (fecha_cursor.month - self.fecha_inicio.month) % 3 == 0)
                elif "semestral" in nombre_p:
                    es_valida = (fecha_cursor.day == 1 and 
                                (fecha_cursor.month - self.fecha_inicio.month) % 6 == 0)
                elif "anual" in nombre_p:
                    es_valida = (fecha_cursor.day == 1 and fecha_cursor.month == self.fecha_inicio.month)

                # Comprobar si la fecha es hoy o futura Y no es anterior a la fecha de inicio
                if es_valida and fecha_cursor >= date.today() and fecha_cursor >= self.fecha_inicio:
                    fechas_validas.append(fecha_cursor)
                
                fecha_cursor += timedelta(days=1)

        # --- 2. ELIMINACIÓN DE PEDIDOS OBSOLETOS ---
        # Buscamos pedidos PENDIENTES de hoy en adelante que NO estén en las fechas válidas
        pedidos_a_eliminar = Pedido.objects.filter(
            servicio=self,
            estado='PENDIENTE',
            fecha_programada__range=[hoy, fecha_limite]
        ).exclude(fecha_programada__in=fechas_validas)
        
        cantidad_eliminados = pedidos_a_eliminar.count()
        pedidos_a_eliminar.delete()

        # --- 3. SINCRONIZACIÓN / CREACIÓN ---
        for f in fechas_validas:

            pedido, creado = Pedido.objects.get_or_create(
                servicio=self, 
                fecha_programada=f,
                defaults={
                    'usuario': self.usuario,
                    'transportista': self.usuario.transportista,
                    'gestor': self.usuario.gestor,
                    'estado': 'PENDIENTE'
                }
            )

            # Solo sincronizamos líneas si el pedido es nuevo o está PENDIENTE
            if creado or pedido.estado == 'PENDIENTE':
                if not creado:
                    # Si ya existía, actualizamos los actores por si han cambiado en el servicio
                    pedido.usuario = self.usuario
                    pedido.transportista = self.usuario.transportista
                    pedido.gestor = self.usuario.gestor
                    pedido.save()

                # --- SINCRONIZACIÓN DE LÍNEAS ---
                # 1. Mapeamos los conceptos que vienen del Servicio (la fuente de verdad)
                conceptos_en_servicio = {l.concepto.id: l for l in self.lineas.all()}

                # 2. Eliminamos líneas del pedido cuyos conceptos ya no estén en el servicio
                pedido.lineas.exclude(concepto_id__in=conceptos_en_servicio.keys()).delete()

                # 3. Actualizamos o creamos las líneas necesarias
                for concepto_id, linea_srv in conceptos_en_servicio.items():
                    # update_or_create busca por pedido y concepto. 
                    # Si existe, actualiza cantidad y precio. Si no, crea.
                    # Esto preserva los campos 'cantidad_recogida' y 'observaciones_recogida'
                    LineaPedido.objects.update_or_create(
                        pedido=pedido,
                        concepto_id=concepto_id,
                        defaults={
                            'cantidad': linea_srv.cantidad, # Tu campo original del modelo
                            'precio': linea_srv.precio,
                            'notas': linea_srv.notas
                        }
                    )

                # --- GESTIÓN AUTOMÁTICA DEL ALBARÁN ---
                # Comprobamos si, tras la sincronización, el pedido tiene residuos
                # Asegúrate de que el campo en Concepto sea 'tipo' y el valor 'RESIDUO'
                tiene_residuos = pedido.lineas.filter(concepto__tipo_concepto='Residuo').exists()

                if tiene_residuos:
                    from operativa.models import Albaran
                    albaran, _ = Albaran.objects.get_or_create(pedido=pedido)
                    
                    # Sincronización forzada: vinculamos todas las líneas de residuo actuales
                    pedido.lineas.filter(
                        concepto__tipo_concepto__iexact='Residuo'
                    ).update(albaran=albaran)
                else:
                    # Si ya no hay residuos, eliminamos el albarán
                    if hasattr(pedido, 'albaran'):
                        pedido.albaran.delete()
                    
        return len(fechas_validas), cantidad_eliminados

    def crear_instancia_pedido(self, fecha):
        """Helper para crear el pedido y sus líneas"""
        from .models import Pedido, LineaPedido
        
        pedido = Pedido.objects.create(
            servicio=self,
            fecha_programada=fecha,
            usuario=self.usuario,
            transportista=self.usuario.transportista,
            gestor=self.usuario.gestor
        )
        
        for l in self.lineas.all():
            LineaPedido.objects.create(
                pedido=pedido,
                concepto=l.concepto,
                cantidad=l.cantidad,
                precio=l.precio,
                notas=l.notas
            )

class LineaServicio(models.Model):
    servicio = models.ForeignKey(Servicio, related_name='lineas', on_delete=models.CASCADE)
    concepto = models.ForeignKey(ConceptoFacturable, on_delete=models.PROTECT)
    cantidad = models.IntegerField(default=1)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    # Puedes añadir notas por línea si lo ves necesario
    notas = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Línea de Servicio"
        verbose_name_plural = "Líneas de Servicio"

class Pedido(models.Model):
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='pedidos') # <-- Mira esto
    fecha_programada = models.DateField(editable=False)
    fecha_ejecucion = models.DateField(null=True, blank=True, verbose_name="Fecha de ejecución")
    usuario = models.ForeignKey(PuntoRecogida, on_delete=models.CASCADE)
    
    # Estos se copian del usuario/cliente por defecto pero son editables
    transportista = models.ForeignKey(Transportista, on_delete=models.PROTECT)
    gestor = models.ForeignKey(GestorResiduos, on_delete=models.PROTECT)
    
    estado = models.CharField(max_length=20, choices=[
        ('PENDIENTE', 'Pendiente'),
        ('REALIZADO', 'Realizado'),
        ('CANCELADO', 'Cancelado')
    ], default='PENDIENTE')

    def clean(self):
        super().clean()
        # Validación lógica: Si está realizado, exige fecha de ejecución
        if self.estado == 'REALIZADO' and not self.fecha_ejecucion:
            raise ValidationError({
                'fecha_ejecucion': 'Es obligatorio indicar la fecha de ejecución para marcar el pedido como REALIZADO.'
            })

    def save(self, *args, **kwargs):
        self.full_clean() # Forzamos la ejecución de clean() antes de guardar
        if not self.pk:
            if hasattr(self.usuario, 'transportista'):
                self.transportista = self.usuario.transportista
            if hasattr(self.usuario, 'gestor'):
                self.gestor = self.usuario.gestor
        super().save(*args, **kwargs)

class LineaPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='lineas', on_delete=models.CASCADE)
    albaran = models.ForeignKey('Albaran', related_name='lineas_albaran', on_delete=models.SET_NULL, null=True, blank=True)
    concepto = models.ForeignKey(ConceptoFacturable, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    notas = models.CharField(max_length=255, blank=True, null=True, verbose_name="Incidencias/Notas de recogida")

    # --- Campos para el Albarán ---
    cantidad_recogida = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)

    def __str__(self):
        return f"{self.concepto} - {self.pedido.pk}"
    
class Albaran(models.Model):
    pedido = models.OneToOneField('Pedido', on_delete=models.CASCADE, related_name='albaran')
    codigo = models.CharField(max_length=30, unique=True, editable=False)
    fecha_emision = models.DateField(verbose_name="Fecha de emisión")
    fecha_ejecucion = models.DateField(null=True, blank=True, verbose_name="Fecha de ejecución")
    observaciones = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Observaciones del Servicio"
    )
    vehiculo = models.ForeignKey(
        'logistica.Vehiculo', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Vehículo de recogida"
    )

    def save(self, *args, **kwargs):
        if not self.codigo:
            # 1. Identificar la entidad (Cliente o Subcliente)
            usuario = self.pedido.usuario
            entidad = usuario.cliente or usuario.subcliente
            prefijo = entidad.codigo if entidad and entidad.codigo else "GEN"
            
            # 2. Buscar el último albarán para esta entidad específica
            # Filtramos por códigos que empiecen por "PREFIJO-"
            ultimo = Albaran.objects.filter(
                codigo__startswith=f"{prefijo}-"
            ).order_by('codigo').last()
            
            if ultimo:
                try:
                    # Dividimos por el guion y tomamos la última parte (el número)
                    # Ejemplo: "CL-000005" -> ["CL", "000005"] -> "000005"
                    partes = ultimo.codigo.split('-')
                    ultimo_numero = int(partes[-1])
                    nuevo_numero = ultimo_numero + 1
                except (ValueError, IndexError):
                    nuevo_numero = 1
            else:
                nuevo_numero = 1
            
            # 3. Construir el código final: Prefijo + Guion + 6 dígitos
            self.codigo = f"{prefijo}-{nuevo_numero:06d}"

        if self.pedido and self.pedido.fecha_programada:
            self.fecha_emision = date(
                self.pedido.fecha_programada.year, 
                self.pedido.fecha_programada.month, 
                1
            )
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Albarán"
        verbose_name_plural = "Albaranes"

class LineaAlbaranProxy(LineaPedido):
    class Meta:
        proxy = True
        verbose_name = "Línea de Albarán"
        verbose_name_plural = "Líneas de Albarán"

@receiver(post_save, sender=LineaPedido)
def vincular_linea_albaran(sender, instance, created, **kwargs):
    """
    Cada vez que se crea o actualiza una línea, si el pedido tiene albarán
    y la línea es un residuo, aseguramos la vinculación.
    """
    pedido = instance.pedido
    # Comprobamos si el pedido tiene albarán asociado
    if hasattr(pedido, 'albaran'):
        albaran = pedido.albaran
        # Si la línea es residuo y no está vinculada, la vinculamos
        if instance.concepto.tipo_concepto.lower() == 'residuo' and instance.albaran != albaran:
            instance.albaran = albaran
            # Usamos update para evitar que esta señal se dispare infinitamente
            LineaPedido.objects.filter(pk=instance.pk).update(albaran=albaran)
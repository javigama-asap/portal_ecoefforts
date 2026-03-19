from django.core.management.base import BaseCommand
from django.utils import timezone
import calendar
from datetime import date
from operativa.models import Servicio, Pedido
from ajustes.models import DatosConfigurables

class Command(BaseCommand):
    help = 'Genera automáticamente los pedidos del mes siguiente según configuración'

    def handle(self, *args, **options):
        hoy = timezone.localdate()
        
        # 1. Obtener día de ejecución con valor por defecto 25
        config = DatosConfigurables.objects.filter(clave="Día del mes generación de Pedidos").first()
        dia_ejecucion = int(config.valor) if config and config.valor.isdigit() else 25

        # 2. Verificar si es el día de ejecución
        if hoy.day != dia_ejecucion:
            self.stdout.write(f"Hoy es {hoy.day}. Ejecución programada para el día {dia_ejecucion}. Omitiendo...")
            return

        # 3. Filtrar servicios según tus reglas:
        # - Activos
        # - NO "A demanda"
        # - Fecha de inicio <= último día del mes siguiente (para asegurar que entran en planificación)
        # 1. Calculamos el mes y año siguiente
        if hoy.month == 12:
            mes_siguiente = 1
            anio_siguiente = hoy.year + 1
        else:
            mes_siguiente = hoy.month + 1
            anio_siguiente = hoy.year

        # 2. Obtenemos el último día exacto de ese mes (ej: 28, 29, 30 o 31)
        # calendar.monthrange devuelve (dia_semana_donde_empieza, ultimo_dia)
        _, ultimo_dia_mes_prox = calendar.monthrange(anio_siguiente, mes_siguiente)

        # 3. Filtramos con la fecha exacta del último segundo del mes siguiente
        fecha_limite_planificacion = date(anio_siguiente, mes_siguiente, ultimo_dia_mes_prox)

        servicios = Servicio.objects.filter(
            activo=True,
            fecha_inicio__lte=fecha_limite_planificacion # Ahora sí incluye hasta el día 31
        ).exclude(
            periodicidad__iexact='A DEMANDA'
        )

        self.stdout.write(self.style.NOTICE(f"Procesando {servicios.count()} servicios activos..."))

        creados_totales = 0
        for servicio in servicios:
            try:
                # Llamamos a la función de sincronización que ya tenemos
                creados, _ = servicio.generar_pedidos_periodicos(fecha_limite_manual=fecha_limite_planificacion)
                creados_totales += creados
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error en servicio {servicio.id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Éxito: Se han procesado/generado {creados_totales} pedidos."))
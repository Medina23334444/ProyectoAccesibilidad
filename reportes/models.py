from django.db import models
from conversion.models import ConversorFormato


class ReporteTecnico(models.Model):
    conversor = models.OneToOneField(
        ConversorFormato,
        on_delete=models.CASCADE,
        related_name='reporte_resultado'
    )

    fecha_generacion = models.DateTimeField(auto_now_add=True)
    tasa_exito_elementos = models.FloatField(
        help_text="Porcentaje de objetos identificables convertidos con éxito"
    )
    puntuacion_accesibilidad = models.IntegerField(default=0)
    cumple_estandar_unl = models.BooleanField(default=False)
    conclusiones_tecnicas = models.TextField(blank=True)

    def __str__(self):
        return f"Reporte Técnico - Doc ID: {self.conversor.documento_origen.id}"


class ObjetivoIdentificable(models.Model):
    reporte = models.ForeignKey(
        ReporteTecnico,
        on_delete=models.CASCADE,
        related_name='objetivos_calidad'
    )

    descripcion_objetivo = models.CharField(max_length=255)
    logrado = models.BooleanField(default=False)
    referencia_objeto_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        estado = "Logrado" if self.logrado else "Fallo"
        return f"Objetivo: {self.descripcion_objetivo} [{estado}]"


class ResumenEjecucion(models.Model):
    reporte = models.OneToOneField(ReporteTecnico, on_delete=models.CASCADE)
    total_fenomenos_detectados = models.IntegerField(default=0)
    total_acciones_mitigacion_ejecutadas = models.IntegerField(default=0)
    tiempo_procesamiento_segundos = models.FloatField()
    memoria_utilizada = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name_plural = "Resúmenes de Ejecución"

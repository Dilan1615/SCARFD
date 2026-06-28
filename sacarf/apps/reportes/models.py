from django.db import models
from django.utils import timezone


class TipoReporte(models.TextChoices):
    POR_ESTUDIANTE = 'POR_ESTUDIANTE', 'Por Estudiante'
    POR_MATERIA = 'POR_MATERIA', 'Por Materia'
    POR_CICLO = 'POR_CICLO', 'Por Ciclo'
    GENERAL = 'GENERAL', 'General'


class FormatoReporte(models.TextChoices):
    PDF = 'PDF', 'PDF'
    EXCEL = 'EXCEL', 'Excel'
    DASHBOARD = 'DASHBOARD', 'Dashboard'


class Reporte(models.Model):
    tipo = models.CharField(max_length=15, choices=TipoReporte.choices)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    parametros = models.JSONField(default=dict)
    formato = models.CharField(max_length=10, choices=FormatoReporte.choices, default='PDF')
    archivo_url = models.URLField(blank=True, null=True)
    generado_por_id = models.IntegerField(null=True, blank=True)
    nombre = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'reporte'
        ordering = ['-fecha_generacion']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha_generacion}"

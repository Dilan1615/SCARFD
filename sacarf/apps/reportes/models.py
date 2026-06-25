from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()

# Modelo para definir los tipos de reportes disponibles
class TipoReporte(models.TextChoices):
    POR_ESTUDIANTE = 'POR_ESTUDIANTE', 'Por Estudiante' # Tipo de reporte que se genera por estudiante
    POR_MATERIA = 'POR_MATERIA', 'Por Materia' # Tipo de reporte que se genera por materia
    POR_CICLO = 'POR_CICLO', 'Por Ciclo' # Tipo de reporte que se genera por ciclo académico
    GENERAL = 'GENERAL', 'General' # Tipo de reporte que se genera de manera general, sin filtrar por estudiante, materia o ciclo


# Modelo para definir los formatos de reportes disponibles
class FormatoReporte(models.TextChoices):
    PDF = 'PDF', 'PDF' # Formato de reporte en PDF
    EXCEL = 'EXCEL', 'Excel'  # Formato de reporte en Excel
    DASHBOARD = 'DASHBOARD', 'Dashboard' # Formato de reporte en Dashboard (visualización interactiva)

class Reporte(models.Model):
    tipo = models.CharField(max_length=15, choices=TipoReporte.choices)
    fecha_generacion = models.DateTimeField(auto_now_add=True) # Fecha y hora en que se generó el reporte
    parametros = models.JSONField(default=dict) # Parámetros utilizados para generar el reporte, almacenados en formato JSON
    formato = models.CharField(max_length=10, choices=FormatoReporte.choices, default='PDF') # Formato del reporte generado
    archivo_url = models.URLField(blank=True, null=True) # URL del archivo generado (PDF, Excel, etc.), puede estar vacío si el reporte aún no se ha generado
    generado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, # Relación con el modelo User, representando al usuario que generó el reporte
                                     related_name='reportes_generados')
    nombre = models.CharField(max_length=200, blank=True) # Nombre del reporte, puede ser generado automáticamente o proporcionado por el usuario

    class Meta:
        db_table = 'reporte'
        ordering = ['-fecha_generacion']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha_generacion}"

    def generar_pdf(self):
        # Implementar con reportlab
        pass

    def generar_excel(self):
        # Implementar con openpyxl
        pass
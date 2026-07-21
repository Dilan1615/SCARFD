from django.contrib import admin
from .models import Asistencia, RegistroFacial, Reconocimiento, Justificacion


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('id', 'estudiante_id', 'horario_id', 'fecha', 'hora_registro', 'estado', 'confianza')
    list_filter = ('estado', 'fecha')


@admin.register(Justificacion)
class JustificacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'estudiante_id', 'estado', 'fecha_solicitud')


admin.site.register(RegistroFacial)
admin.site.register(Reconocimiento)
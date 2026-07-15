from rest_framework import serializers
from .models import RegistroAuditoria


class RegistroAuditoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroAuditoria
        fields = [
            'id', 'usuario_id', 'usuario_nombre', 'accion', 'servicio',
            'modelo', 'registro_id', 'descripcion', 'datos_modificados',
            'ip_origen', 'fecha_hora',
        ]
        read_only_fields = fields

from rest_framework import serializers
from .models import Reporte, TipoReporte, FormatoReporte
from shared.models import Usuario


class ReporteSerializer(serializers.ModelSerializer):
    tipo_display = serializers.SerializerMethodField()
    formato_display = serializers.SerializerMethodField()
    generado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Reporte
        fields = ['id', 'tipo', 'tipo_display', 'fecha_generacion', 'parametros',
                  'formato', 'formato_display', 'archivo_url', 'nombre',
                  'generado_por_id', 'generado_por_nombre']
        read_only_fields = ['id', 'fecha_generacion']

    def get_tipo_display(self, obj):
        return obj.get_tipo_display()

    def get_formato_display(self, obj):
        return obj.get_formato_display()

    def get_generado_por_nombre(self, obj):
        if obj.generado_por_id:
            try:
                user = Usuario.objects.get(id=obj.generado_por_id)
                return f"{user.first_name} {user.last_name}"
            except Usuario.DoesNotExist:
                return None
        return None


class GenerarReporteSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=TipoReporte.choices)
    formato = serializers.ChoiceField(choices=FormatoReporte.choices, default='PDF')
    estudiante_id = serializers.IntegerField(required=False)
    materia_id = serializers.IntegerField(required=False)
    ciclo_id = serializers.IntegerField(required=False)
    fecha_desde = serializers.DateField(required=False)
    fecha_hasta = serializers.DateField(required=False)

    def validate(self, data):
        tipo = data.get('tipo')

        if tipo == 'POR_ESTUDIANTE' and not data.get('estudiante_id'):
            raise serializers.ValidationError("Se requiere estudiante_id para reporte por estudiante")

        if tipo == 'POR_MATERIA' and not data.get('materia_id'):
            raise serializers.ValidationError("Se requiere materia_id para reporte por materia")

        if tipo == 'POR_CICLO' and not data.get('ciclo_id'):
            raise serializers.ValidationError("Se requiere ciclo_id para reporte por ciclo")

        return data

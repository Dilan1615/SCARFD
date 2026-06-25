from rest_framework import serializers
from .models import Carrera, Ciclo, Materia, Horario
from apps.usuario.models import Usuario

class CarreraSerializer(serializers.ModelSerializer):
    modalidad_display = serializers.SerializerMethodField()

    class Meta:
        model = Carrera
        fields = '__all__'
        read_only_fields = ['id']

    def get_modalidad_display(self, obj):
        return obj.get_modalidad_display()

class CicloSerializer(serializers.ModelSerializer):
    estado_display = serializers.SerializerMethodField()
    carrera_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Ciclo
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Ciclo.objects.all(),
                fields=['num', 'carrera'],
                message='Ya existe un ciclo con este número para la carrera seleccionada',
            )
        ]

    def get_estado_display(self, obj):
        return obj.get_estado_display()

    def get_carrera_nombre(self, obj):
        return obj.carrera.nombre

    def validate(self, data):
        if data.get('fecha_inicio') and data.get('fecha_fin') and data['fecha_fin'] <= data['fecha_inicio']:
            raise serializers.ValidationError('La fecha de fin debe ser posterior a la fecha de inicio')
        return data

class MateriaSerializer(serializers.ModelSerializer):
    carrera_nombre = serializers.SerializerMethodField()
    ciclo_info = serializers.SerializerMethodField()
    docente_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Materia
        fields = '__all__'
        read_only_fields = ['id']

    def get_carrera_nombre(self, obj):
        return obj.carrera.nombre

    def get_ciclo_info(self, obj):
        return f"Ciclo {obj.ciclo.num}"

    def get_docente_nombre(self, obj):
        if obj.docente:
            return f"{obj.docente.first_name} {obj.docente.last_name}"
        return None

class HorarioSerializer(serializers.ModelSerializer):
    dia_display = serializers.SerializerMethodField()
    materia_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Horario
        fields = '__all__'
        read_only_fields = ['id']

    def get_dia_display(self, obj):
        return obj.get_dia_semana_display()

    def get_materia_nombre(self, obj):
        return obj.materia.nombre

    def validate(self, data):
        if data.get('hora_inicio') and data.get('hora_fin') and data['hora_fin'] <= data['hora_inicio']:
            raise serializers.ValidationError('La hora de fin debe ser posterior a la hora de inicio')
        return data

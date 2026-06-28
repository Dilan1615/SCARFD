from rest_framework import serializers
from .models import Carrera, Ciclo, Materia, Horario, Matricula
from shared.models import Usuario
from datetime import datetime


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
        if obj.docente_id:
            try:
                user = Usuario.objects.get(id=obj.docente_id)
                return f"{user.first_name} {user.last_name}"
            except Usuario.DoesNotExist:
                return None
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


class MatriculaSerializer(serializers.ModelSerializer):
    estudiante_nombre = serializers.SerializerMethodField()
    carrera_nombre = serializers.SerializerMethodField()
    ciclo_info = serializers.SerializerMethodField()
    estado_display = serializers.SerializerMethodField()

    class Meta:
        model = Matricula
        fields = '__all__'
        read_only_fields = ['id', 'fecha_matricula']

    def get_estudiante_nombre(self, obj):
        try:
            user = Usuario.objects.get(id=obj.estudiante_id)
            return f"{user.first_name} {user.last_name}"
        except Usuario.DoesNotExist:
            return None

    def get_carrera_nombre(self, obj):
        return obj.carrera.nombre

    def get_ciclo_info(self, obj):
        return f"Ciclo {obj.ciclo.num}"

    def get_estado_display(self, obj):
        return obj.get_estado_display()


class HorarioConAsistenciaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    dia_semana = serializers.CharField()
    dia_display = serializers.CharField()
    hora_inicio = serializers.TimeField()
    hora_fin = serializers.TimeField()
    minutos_tolerancia = serializers.IntegerField()
    aula = serializers.CharField()
    ya_registro = serializers.BooleanField()
    asistencia_id = serializers.IntegerField(allow_null=True)
    estado_asistencia = serializers.CharField(allow_null=True)


class MateriaConHorariosSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    docente_nombre = serializers.CharField(allow_null=True)
    horarios_hoy = serializers.ListField(child=HorarioConAsistenciaSerializer())


class MisMateriasSerializer(serializers.Serializer):
    matricula_id = serializers.IntegerField()
    carrera = serializers.CharField()
    ciclo = serializers.CharField()
    materias = serializers.ListField(child=MateriaConHorariosSerializer())

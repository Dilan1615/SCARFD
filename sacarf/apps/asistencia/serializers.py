from rest_framework import serializers
from .models import (
    Asistencia, Justificacion, Reconocimiento, 
    RegistroFacial, EstadoAsistencia, EstadoJustificacion
)
from apps.academico.models import Horario
from apps.usuario.models import Usuario
from datetime import datetime, timedelta


# Manera de serializar los modelos para la API REST
class RegistroFacialSerializer(serializers.ModelSerializer):
    estudiante_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = RegistroFacial
        fields = ['id', 'face_id', 'collection_id', 'fecha_registro', 'estado', 'estudiante', 'estudiante_nombre']
        read_only_fields = ['id', 'face_id', 'fecha_registro']
    
    def get_estudiante_nombre(self, obj):
        return f"{obj.estudiante.first_name} {obj.estudiante.last_name}"


# Este serializer se utiliza para mostrar la información de los reconocimientos faciales en la API REST
class ReconocimientoSerializer(serializers.ModelSerializer):
    estudiante_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Reconocimiento
        fields = ['id', 'fecha_hora', 'resultado', 'confianza', 'ubicacion', 
                  'imagen_url', 'estudiante', 'estudiante_nombre', 'registro_facial']
        read_only_fields = ['id', 'fecha_hora']
    
    def get_estudiante_nombre(self, obj):
        return f"{obj.estudiante.first_name} {obj.estudiante.last_name}"


# Este serializer se utiliza para mostrar la información de las asistencias en la API REST
class AsistenciaSerializer(serializers.ModelSerializer):
    estudiante_nombre = serializers.SerializerMethodField()
    horario_info = serializers.SerializerMethodField()
    estado_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Asistencia
        fields = ['id', 'fecha', 'hora_registro', 'estado', 'estado_display', 
                  'confianza', 'estudiante', 'estudiante_nombre', 'horario', 
                  'horario_info', 'reconocimiento']
        read_only_fields = ['id', 'fecha', 'hora_registro']
    
    def get_estudiante_nombre(self, obj):
        return f"{obj.estudiante.first_name} {obj.estudiante.last_name}"
    
    def get_horario_info(self, obj):
        return {
            'materia': obj.horario.materia.nombre,
            'dia': obj.horario.get_dia_semana_display(),
            'hora_inicio': obj.horario.hora_inicio.strftime('%H:%M'),
            'hora_fin': obj.horario.hora_fin.strftime('%H:%M'),
            'aula': obj.horario.aula
        }
    
    def get_estado_display(self, obj):
        return obj.get_estado_display()

# Este serializer se utiliza para registrar asistencias a través de la API REST
class RegistrarAsistenciaSerializer(serializers.Serializer):
    estudiante_id = serializers.IntegerField()
    horario_id = serializers.IntegerField()
    imagen_base64 = serializers.CharField()
    ubicacion = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        # Validar que el estudiante existe
        try:
            estudiante = Usuario.objects.get(id=data['estudiante_id'], rol='ESTUDIANTE')
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("Estudiante no encontrado o no es estudiante")
        
        # Validar que el horario existe
        try:
            horario = Horario.objects.get(id=data['horario_id'])
        except Horario.DoesNotExist:
            raise serializers.ValidationError("Horario no encontrado")
        
        # Validar que es el día correcto
        from datetime import datetime
        dia_semana_actual = datetime.now().strftime('%A').upper()
        dias_map = {
            'MONDAY': 'LUNES',
            'TUESDAY': 'MARTES',
            'WEDNESDAY': 'MIERCOLES',
            'THURSDAY': 'JUEVES',
            'FRIDAY': 'VIERNES',
            'SATURDAY': 'SABADO',
            'SUNDAY': 'DOMINGO'
        }
        dia_actual = dias_map.get(dia_semana_actual)
        if dia_actual != horario.dia_semana:
            raise serializers.ValidationError(f"Hoy no es día de clase. La clase es {horario.get_dia_semana_display()}")
        
        # Validar que no haya pasado el límite de tiempo
        hora_actual = datetime.now().time()
        hora_limite = (datetime.combine(datetime.today(), horario.hora_inicio) + 
                      timedelta(minutes=horario.minutos_tolerancia * 2)).time()
        if hora_actual > hora_limite:
            raise serializers.ValidationError(f"Fuera del tiempo permitido para registrar asistencia. Límite: {hora_limite.strftime('%H:%M')}")
        
        # Validar que no tenga asistencia hoy
        if Asistencia.objects.filter(estudiante=estudiante, horario=horario, fecha=datetime.now().date()).exists():
            raise serializers.ValidationError("Ya registró asistencia para esta clase hoy")
        
        data['estudiante'] = estudiante
        data['horario'] = horario
        return data

# Este serializer se utiliza para mostrar la información de las justificaciones en la API REST
class JustificacionSerializer(serializers.ModelSerializer):
    estudiante_nombre = serializers.SerializerMethodField()
    docente_aprueba_nombre = serializers.SerializerMethodField()
    estado_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Justificacion
        fields = ['id', 'motivo', 'fecha_solicitud', 'documento_url', 'estado', 
                  'estado_display', 'asistencia', 'estudiante', 'estudiante_nombre',
                  'docente_aprueba', 'docente_aprueba_nombre', 'fecha_respuesta', 
                  'comentario_docente']
        read_only_fields = ['id', 'fecha_solicitud', 'fecha_respuesta']
    
    def get_estudiante_nombre(self, obj):
        return f"{obj.estudiante.first_name} {obj.estudiante.last_name}"
    
    def get_docente_aprueba_nombre(self, obj):
        if obj.docente_aprueba:
            return f"{obj.docente_aprueba.first_name} {obj.docente_aprueba.last_name}"
        return None
    
    def get_estado_display(self, obj):
        return obj.get_estado_display()

# Este serializer se utiliza para aprobar o rechazar justificaciones a través de la API REST
class AprobarJustificacionSerializer(serializers.Serializer):
    justificacion_id = serializers.IntegerField()
    aprobar = serializers.BooleanField()
    comentario = serializers.CharField(required=False, allow_blank=True)      
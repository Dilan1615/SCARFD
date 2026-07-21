from rest_framework import serializers
from .models import (
    Asistencia, Justificacion, Reconocimiento,
    RegistroFacial, EstadoAsistencia, EstadoJustificacion
)
from shared.models import Usuario, HorarioModel
from datetime import datetime, timedelta
import os


def _get_usuario_nombre(user_id):
    try:
        user = Usuario.objects.get(id=user_id)
        return f"{user.first_name} {user.last_name}"
    except Usuario.DoesNotExist:
        return None


class RegistroFacialSerializer(serializers.ModelSerializer):
    estudiante_nombre = serializers.SerializerMethodField()

    class Meta:
        model = RegistroFacial
        fields = ['id', 'face_id', 'collection_id', 'fecha_registro', 'estado',
                  'estudiante_id', 'estudiante_nombre']
        read_only_fields = ['id', 'face_id', 'fecha_registro']

    def get_estudiante_nombre(self, obj):
        return _get_usuario_nombre(obj.estudiante_id)


class ReconocimientoSerializer(serializers.ModelSerializer):
    estudiante_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Reconocimiento
        fields = ['id', 'fecha_hora', 'resultado', 'confianza', 'ubicacion',
                  'imagen_url', 'estudiante_id', 'estudiante_nombre', 'registro_facial']
        read_only_fields = ['id', 'fecha_hora']

    def get_estudiante_nombre(self, obj):
        return _get_usuario_nombre(obj.estudiante_id)


class AsistenciaSerializer(serializers.ModelSerializer):
    estudiante_nombre = serializers.SerializerMethodField()
    horario_info = serializers.SerializerMethodField()
    estado_display = serializers.SerializerMethodField()
    justificacion_info = serializers.SerializerMethodField()

    class Meta:
        model = Asistencia
        fields = ['id', 'fecha', 'hora_registro', 'estado', 'estado_display',
                  'confianza', 'estudiante_id', 'estudiante_nombre', 'horario_id',
                  'horario_info', 'reconocimiento', 'justificacion_info']
        read_only_fields = ['id', 'fecha', 'hora_registro']

    def get_estudiante_nombre(self, obj):
        return _get_usuario_nombre(obj.estudiante_id)

    def get_justificacion_info(self, obj):
        try:
            j = obj.justificacion
        except Justificacion.DoesNotExist:
            return None
        return {'estado': j.estado, 'comentario_docente': j.comentario_docente}

    def get_horario_info(self, obj):
        try:
            horario = HorarioModel.objects.select_related('materia').get(id=obj.horario_id)
            return {
                'materia': horario.materia.nombre,
                'dia': horario.get_dia_semana_display(),
                'hora_inicio': horario.hora_inicio.strftime('%H:%M'),
                'hora_fin': horario.hora_fin.strftime('%H:%M'),
                'aula': horario.aula
            }
        except HorarioModel.DoesNotExist:
            return None

    def get_estado_display(self, obj):
        return obj.get_estado_display()


class RegistrarAsistenciaSerializer(serializers.Serializer):
    estudiante_id = serializers.IntegerField()
    horario_id = serializers.IntegerField()
    imagen_base64 = serializers.CharField()
    ubicacion = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        try:
            estudiante = Usuario.objects.get(id=data['estudiante_id'], rol='ESTUDIANTE')
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("Estudiante no encontrado o no es estudiante")

        try:
            horario = HorarioModel.objects.get(id=data['horario_id'])
        except HorarioModel.DoesNotExist:
            raise serializers.ValidationError("Horario no encontrado")

        dia_semana_actual = datetime.now().strftime('%A').upper()
        dias_map = {
            'MONDAY': 'LUNES', 'TUESDAY': 'MARTES',
            'WEDNESDAY': 'MIERCOLES', 'THURSDAY': 'JUEVES',
            'FRIDAY': 'VIERNES', 'SATURDAY': 'SABADO', 'SUNDAY': 'DOMINGO'
        }
        dia_actual = dias_map.get(dia_semana_actual)
        if dia_actual != horario.dia_semana:
            raise serializers.ValidationError(
                f"Hoy no es día de clase. La clase es {horario.get_dia_semana_display()}"
            )

        hora_actual = datetime.now().time()
        hora_limite = (datetime.combine(datetime.today(), horario.hora_inicio) +
                      timedelta(minutes=horario.minutos_tolerancia * 2)).time()
        if hora_actual > hora_limite:
            raise serializers.ValidationError(
                f"Fuera del tiempo permitido para registrar asistencia. "
                f"Límite: {hora_limite.strftime('%H:%M')}"
            )

        if Asistencia.objects.filter(
            estudiante_id=data['estudiante_id'],
            horario_id=data['horario_id'],
            fecha=datetime.now().date()
        ).exists():
            raise serializers.ValidationError("Ya registró asistencia para esta clase hoy")

        data['horario_data'] = {
            'hora_inicio': horario.hora_inicio.strftime('%H:%M:%S'),
            'minutos_tolerancia': horario.minutos_tolerancia,
        }
        return data


class JustificacionSerializer(serializers.ModelSerializer):
    estudiante_nombre = serializers.SerializerMethodField()
    docente_aprueba_nombre = serializers.SerializerMethodField()
    estado_display = serializers.SerializerMethodField()

    class Meta:
        model = Justificacion
        fields = ['id', 'motivo', 'fecha_solicitud', 'documento', 'estado',
                  'estado_display', 'asistencia', 'estudiante_id', 'estudiante_nombre',
                  'docente_aprueba_id', 'docente_aprueba_nombre', 'fecha_respuesta',
                  'comentario_docente']
        read_only_fields = ['id', 'fecha_solicitud', 'fecha_respuesta', 'estado',
                             'docente_aprueba_id', 'comentario_docente', 'estudiante_id']
        extra_kwargs = {'documento': {'required': True}}

    def get_estudiante_nombre(self, obj):
        return _get_usuario_nombre(obj.estudiante_id)

    def get_docente_aprueba_nombre(self, obj):
        if obj.docente_aprueba_id:
            return _get_usuario_nombre(obj.docente_aprueba_id)
        return None

    def get_estado_display(self, obj):
        return obj.get_estado_display()

    def validate_documento(self, value):
        content_type = getattr(value, 'content_type', '') or ''
        ext = os.path.splitext(value.name)[1].lower()
        if content_type not in ('image/png', 'image/jpeg', 'image/jpg') and ext not in ('.png', '.jpg', '.jpeg'):
            raise serializers.ValidationError("El comprobante médico debe ser una imagen en formato PNG o JPG.")

        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("El comprobante médico no debe superar 5 MB.")

        # Verifica que el contenido sea realmente una imagen válida, no solo la extensión/mimetype declarados
        try:
            from PIL import Image
            value.seek(0)
            imagen = Image.open(value)
            imagen.verify()
            if imagen.format not in ('PNG', 'JPEG'):
                raise serializers.ValidationError("El comprobante médico debe ser una imagen PNG o JPG válida.")
        except serializers.ValidationError:
            raise
        except Exception:
            raise serializers.ValidationError("El archivo no es una imagen válida.")
        finally:
            value.seek(0)

        return value


class AprobarJustificacionSerializer(serializers.Serializer):
    justificacion_id = serializers.IntegerField()
    aprobar = serializers.BooleanField()
    comentario = serializers.CharField(required=False, allow_blank=True)

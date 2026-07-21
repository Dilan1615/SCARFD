from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from datetime import date, datetime, time, timedelta
import uuid


def ruta_comprobante_medico(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
    return f'justificaciones/{instance.estudiante_id}/{uuid.uuid4()}.{ext}'


class EstadoAsistencia(models.TextChoices):
    PRESENTE = 'PRESENTE', 'Presente'
    AUSENTE = 'AUSENTE', 'Ausente'
    TARDE = 'TARDE', 'Tarde'
    JUSTIFICADO = 'JUSTIFICADO', 'Justificado'


class EstadoJustificacion(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    APROBADA = 'APROBADA', 'Aprobada'
    RECHAZADA = 'RECHAZADA', 'Rechazada'


class EstadoRegistro(models.TextChoices):
    ACTIVO = 'ACTIVO', 'Activo'
    INACTIVO = 'INACTIVO', 'Inactivo'


class RegistroFacial(models.Model):
    face_id = models.CharField(max_length=100, unique=True)
    collection_id = models.CharField(max_length=100, default='sacarf_faces')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=EstadoRegistro.choices, default='ACTIVO')
    estudiante_id = models.IntegerField(unique=True)

    class Meta:
        db_table = 'registro_facial'

    def __str__(self):
        return f"Registro facial de estudiante #{self.estudiante_id}"


class Reconocimiento(models.Model):
    fecha_hora = models.DateTimeField(auto_now_add=True)
    resultado = models.BooleanField(default=False)
    confianza = models.FloatField(default=0.0)
    ubicacion = models.CharField(max_length=100, blank=True)
    imagen_url = models.URLField(blank=True, null=True)
    estudiante_id = models.IntegerField()
    registro_facial = models.ForeignKey(RegistroFacial, on_delete=models.SET_NULL,
                                        null=True, related_name='reconocimientos')

    class Meta:
        db_table = 'reconocimiento'
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"Reconocimiento estudiante #{self.estudiante_id} - {self.fecha_hora}"


class Asistencia(models.Model):
    fecha = models.DateField(auto_now_add=True)
    hora_registro = models.TimeField(auto_now_add=True)
    estado = models.CharField(max_length=12, choices=EstadoAsistencia.choices)
    confianza = models.FloatField(default=0.0)
    estudiante_id = models.IntegerField()
    horario_id = models.IntegerField()
    reconocimiento = models.OneToOneField(Reconocimiento, on_delete=models.SET_NULL,
                                          null=True, related_name='asistencia')

    class Meta:
        db_table = 'asistencia'
        ordering = ['-fecha', '-hora_registro']
        unique_together = ['estudiante_id', 'horario_id', 'fecha']

    def __str__(self):
        return f"Estudiante #{self.estudiante_id} - {self.get_estado_display()} - {self.fecha}"

    @classmethod
    def registrar_asistencia(cls, estudiante_id, horario_id, confianza,
                             hora_inicio, minutos_tolerancia,
                             imagen_url=None, ubicacion=None):
        now = datetime.now()
        fecha_actual = now.date()
        hora_actual = now.time()

        if cls.objects.filter(estudiante_id=estudiante_id, horario_id=horario_id,
                              fecha=fecha_actual).exists():
            raise ValidationError("Ya se registró asistencia para este estudiante en esta clase")

        hora_limite_presente = (datetime.combine(fecha_actual, hora_inicio) +
                                timedelta(minutes=minutos_tolerancia)).time()
        hora_limite_tardanza = (datetime.combine(fecha_actual, hora_inicio) +
                                timedelta(minutes=minutos_tolerancia * 2)).time()

        if hora_actual > hora_limite_tardanza:
            raise ValidationError("Fuera del tiempo permitido para registrar asistencia")

        if hora_actual <= hora_limite_presente:
            estado = EstadoAsistencia.PRESENTE
        else:
            estado = EstadoAsistencia.TARDE

        reconocimiento = Reconocimiento.objects.create(
            estudiante_id=estudiante_id,
            resultado=confianza >= 85.0,
            confianza=confianza,
            ubicacion=ubicacion or '',
            imagen_url=imagen_url,
            registro_facial=RegistroFacial.objects.filter(estudiante_id=estudiante_id).first()
        )

        asistencia = cls.objects.create(
            estudiante_id=estudiante_id,
            horario_id=horario_id,
            fecha=fecha_actual,
            hora_registro=hora_actual,
            estado=estado,
            confianza=confianza,
            reconocimiento=reconocimiento
        )

        return asistencia


class Justificacion(models.Model):
    motivo = models.TextField()
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    documento = models.FileField(
        upload_to=ruta_comprobante_medico,
        validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])],
        help_text='Comprobante médico en formato PNG o JPG'
    )
    estado = models.CharField(max_length=10, choices=EstadoJustificacion.choices, default='PENDIENTE')
    asistencia = models.OneToOneField(Asistencia, on_delete=models.CASCADE, related_name='justificacion')
    estudiante_id = models.IntegerField()
    docente_aprueba_id = models.IntegerField(null=True, blank=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    comentario_docente = models.TextField(blank=True)

    class Meta:
        db_table = 'justificacion'
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"Justificación estudiante #{self.estudiante_id} - {self.asistencia.fecha}"

    def aprobar(self, docente_id, comentario=''):
        self.estado = EstadoJustificacion.APROBADA
        self.docente_aprueba_id = docente_id
        self.fecha_respuesta = datetime.now()
        self.comentario_docente = comentario
        self.asistencia.estado = EstadoAsistencia.JUSTIFICADO
        self.asistencia.save()
        self.save()

    def rechazar(self, docente_id, comentario=''):
        self.estado = EstadoJustificacion.RECHAZADA
        self.docente_aprueba_id = docente_id
        self.fecha_respuesta = datetime.now()
        self.comentario_docente = comentario
        self.save()

from django.db import models
from django.core.exceptions import ValidationError
from datetime import date, datetime, time, timedelta

# Clase para definir los posibles estados de asistencia
class EstadoAsistencia(models.TextChoices): 
    PRESENTE = 'PRESENTE', 'Presente'
    AUSENTE = 'AUSENTE', 'Ausente'
    TARDE = 'TARDE', 'Tarde'
    JUSTIFICADO = 'JUSTIFICADO', 'Justificado'


# Clase para definir los posibles estados de justificación
class EstadoJustificacion(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    APROBADA = 'APROBADA', 'Aprobada'
    RECHAZADA = 'RECHAZADA', 'Rechazada'

# Clase para definir los posibles estados de registro facial
class EstadoRegistro(models.TextChoices):
    ACTIVO = 'ACTIVO', 'Activo'
    INACTIVO = 'INACTIVO', 'Inactivo'

# Modelo para almacenar el registro facial de un estudiante
class RegistroFacial(models.Model):
    face_id = models.CharField(max_length=100, unique=True) # ID único del rostro en la base de datos de reconocimiento facial
    collection_id = models.CharField(max_length=100, default='sacarf_faces') # ID de la colección de rostros en el sistema de reconocimiento facial
    fecha_registro = models.DateTimeField(auto_now_add=True) # Fecha y hora en que se registró el rostro
    estado = models.CharField(max_length=10, choices=EstadoRegistro.choices, default='ACTIVO') # Estado del registro facial (activo o inactivo)
    estudiante = models.OneToOneField('usuario.Usuario', on_delete=models.CASCADE, # Relación uno a uno con el modelo Usuario, representando al estudiante al que pertenece el registro facial
                                      related_name='registro_facial',
                                      limit_choices_to={'rol': 'ESTUDIANTE'})

    class Meta:
        db_table = 'registro_facial'

    def __str__(self):
        return f"Registro facial de {self.estudiante.email}"


# Modelo para almacenar los resultados de los reconocimientos faciales realizados 
class Reconocimiento(models.Model):
    fecha_hora = models.DateTimeField(auto_now_add=True) # Fecha y hora del reconocimiento
    resultado = models.BooleanField(default=False) # Resultado del reconocimiento (True: éxito, False: fracaso)
    confianza = models.FloatField(default=0.0) # Nivel de confianza en el resultado del reconocimiento
    ubicacion = models.CharField(max_length=100, blank=True) # Ubicación donde se realizó el reconocimiento
    imagen_url = models.URLField(blank=True, null=True) # URL de la imagen capturada durante el reconocimiento
    estudiante = models.ForeignKey('usuario.Usuario', on_delete=models.CASCADE, # Relación con el modelo Usuario, representando al estudiante que fue reconocido
                                   related_name='reconocimientos',
                                   limit_choices_to={'rol': 'ESTUDIANTE'})
    registro_facial = models.ForeignKey(RegistroFacial, on_delete=models.SET_NULL, # Relación con el modelo RegistroFacial, representando el registro facial asociado al reconocimiento
                                        null=True, related_name='reconocimientos')

    class Meta:
        db_table = 'reconocimiento'
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"Reconocimiento {self.estudiante.email} - {self.fecha_hora}"

# Modelo para almacenar la asistencia de los estudiantes a las clases
class Asistencia(models.Model):
    fecha = models.DateField(auto_now_add=True) # Fecha de la asistencia
    hora_registro = models.TimeField(auto_now_add=True) # Hora en que se registró la asistencia
    estado = models.CharField(max_length=12, choices=EstadoAsistencia.choices) # Estado de la asistencia (presente, ausente, retrasado)
    confianza = models.FloatField(default=0.0) # Nivel de confianza en el resultado del reconocimiento
    estudiante = models.ForeignKey('usuario.Usuario', on_delete=models.CASCADE, # Relación con el modelo Usuario, representando al estudiante que asistió a la clase
                                   related_name='asistencias',
                                   limit_choices_to={'rol': 'ESTUDIANTE'})
    horario = models.ForeignKey('academico.Horario', on_delete=models.CASCADE, # Relación con el modelo Horario, representando la clase a la que asistió el estudiante
                                related_name='asistencias')
    reconocimiento = models.OneToOneField(Reconocimiento, on_delete=models.SET_NULL, # Relación uno a uno con el modelo Reconocimiento, representando el reconocimiento facial asociado a la asistencia
                                          null=True, related_name='asistencia')

    class Meta:
        db_table = 'asistencia'
        ordering = ['-fecha', '-hora_registro']
        unique_together = ['estudiante', 'horario', 'fecha']

    def __str__(self):
        return f"{self.estudiante.email} - {self.get_estado_display()} - {self.fecha}"


    # Método de clase para registrar la asistencia de un estudiante a una clase
    @classmethod
    def registrar_asistencia(cls, estudiante, horario, confianza, imagen_url=None, ubicacion=None):
        from datetime import datetime, time
        now = datetime.now()
        fecha_actual = now.date()
        hora_actual = now.time()

        # Verificar si ya existe asistencia para este estudiante y horario hoy
        if cls.objects.filter(estudiante=estudiante, horario=horario, fecha=fecha_actual).exists():
            raise ValidationError("Ya se registró asistencia para este estudiante en esta clase")

        # Calcular estado basado en la hora, considerando la tolerancia del horario
        # Se obtiene la hora de inicio del horario y se calculan los límites de tiempo para determinar si el estudiante está presente, tarde o ausente
        # Se definio que 5 minutos de tolerancia es para estar presente y luego de otros 5 minutos esta tarde y después de eso se considera ausente y se bloquea el registro de asistencia
        hora_inicio = horario.hora_inicio
        hora_limite_presente = (datetime.combine(fecha_actual, hora_inicio) + 
                               timedelta(minutes=horario.minutos_tolerancia)).time()
        hora_limite_tardanza = (datetime.combine(fecha_actual, hora_inicio) + 
                               timedelta(minutes=horario.minutos_tolerancia * 2)).time()

        # Validar que no pase el límite de tardanza
        if hora_actual > hora_limite_tardanza:
            raise ValidationError("Fuera del tiempo permitido para registrar asistencia")

        # Determinar estado
        if hora_actual <= hora_limite_presente:
            estado = EstadoAsistencia.PRESENTE
        else:
            estado = EstadoAsistencia.TARDE

        # Crear reconocimiento
        reconocimiento = Reconocimiento.objects.create(
            estudiante=estudiante,
            resultado=confianza >= 85.0,
            confianza=confianza,
            ubicacion=ubicacion or '',
            imagen_url=imagen_url,
            registro_facial=getattr(estudiante, 'registro_facial', None)
        )

        # Crear asistencia
        asistencia = cls.objects.create(
            estudiante=estudiante,
            horario=horario,
            fecha=fecha_actual,
            hora_registro=hora_actual,
            estado=estado,
            confianza=confianza,
            reconocimiento=reconocimiento
        )

        return asistencia
    

# Modelo para almacenar las justificaciones de inasistencia de los estudiantes
class Justificacion(models.Model):
    motivo = models.TextField() # Motivo de la justificación de inasistencia
    fecha_solicitud = models.DateTimeField(auto_now_add=True) # Fecha y hora en que se solicitó la justificación
    documento_url = models.URLField(blank=True, null=True) # URL del documento que respalda la justificación (opcional)
    estado = models.CharField(max_length=10, choices=EstadoJustificacion.choices, default='PENDIENTE') # Estado de la justificación (pendiente, aprobada, rechazada)
    asistencia = models.OneToOneField(Asistencia, on_delete=models.CASCADE, related_name='justificacion') # Relación uno a uno con el modelo Asistencia, representando la asistencia que se está justificando
    estudiante = models.ForeignKey('usuario.Usuario', on_delete=models.CASCADE, # Relación con el modelo Usuario, representando al estudiante que solicita la justificación
                                   related_name='justificaciones',
                                   limit_choices_to={'rol': 'ESTUDIANTE'})
    docente_aprueba = models.ForeignKey('usuario.Usuario', on_delete=models.SET_NULL, # Relación con el modelo Usuario, representando al docente que aprueba o rechaza la justificación
                                        null=True, related_name='justificaciones_aprobadas',
                                        limit_choices_to={'rol': 'DOCENTE'})
    fecha_respuesta = models.DateTimeField(null=True, blank=True) # Fecha y hora en que se respondió la justificación (aprobada o rechazada)
    comentario_docente = models.TextField(blank=True) # Comentario del docente al aprobar o rechazar la justificación

    class Meta:
        db_table = 'justificacion'
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"Justificación {self.estudiante.email} - {self.asistencia.fecha}"

    # Método para aprobar la justificación de inasistencia
    def aprobar(self, docente, comentario=''):
        self.estado = EstadoJustificacion.APROBADA # Cambiar el estado a aprobada
        self.docente_aprueba = docente # Asignar el docente que aprueba la justificación
        self.fecha_respuesta = datetime.now() # Registrar la fecha y hora de la respuesta
        self.comentario_docente = comentario # Registrar el comentario del docente
        self.asistencia.estado = EstadoAsistencia.JUSTIFICADO # Cambiar el estado de la asistencia a justificado
        self.asistencia.save() # Guardar los cambios en la asistencia
        self.save() # Guardar los cambios en la justificación

    # Método para rechazar la justificación de inasistencia
    def rechazar(self, docente, comentario=''):
        self.estado = EstadoJustificacion.RECHAZADA # Cambiar el estado a rechazada
        self.docente_aprueba = docente # Asignar el docente que rechaza la justificación
        self.fecha_respuesta = datetime.now() # Registrar la fecha y hora de la respuesta
        self.comentario_docente = comentario # Registrar el comentario del docente
        self.save() # Guardar los cambios en la justificación   
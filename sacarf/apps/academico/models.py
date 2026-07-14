from django.db import models
from django.core.exceptions import ValidationError
from datetime import time, timedelta


class Modalidad(models.TextChoices):
    VIRTUAL = 'VIRTUAL', 'Virtual'
    PRESENCIAL = 'PRESENCIAL', 'Presencial'
    HIBRIDA = 'HIBRIDA', 'Híbrida'


class DiaSemana(models.TextChoices):
    LUNES = 'LUNES', 'Lunes'
    MARTES = 'MARTES', 'Martes'
    MIERCOLES = 'MIERCOLES', 'Miércoles'
    JUEVES = 'JUEVES', 'Jueves'
    VIERNES = 'VIERNES', 'Viernes'


class EstadoCiclo(models.TextChoices):
    ACTIVO = 'ACTIVO', 'Activo'
    FINALIZADO = 'FINALIZADO', 'Finalizado'


class EstadoMatricula(models.TextChoices):
    ACTIVA = 'ACTIVA', 'Activa'
    FINALIZADA = 'FINALIZADA', 'Finalizada'


class Carrera(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    duracion = models.PositiveIntegerField(help_text='Duración en semestres')
    modalidad = models.CharField(max_length=10, choices=Modalidad.choices)

    class Meta:
        db_table = 'carrera'

    def __str__(self):
        return self.nombre


class Ciclo(models.Model):
    num = models.PositiveIntegerField(help_text='Número del ciclo (1, 2, 3, ...)')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=10, choices=EstadoCiclo.choices, default='ACTIVO')
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, related_name='ciclos')

    class Meta:
        db_table = 'ciclo'
        unique_together = ['num', 'carrera']

    def __str__(self):
        return f"{self.carrera.nombre} - Ciclo {self.num}"

    def esta_activo(self):
        from datetime import date
        return self.estado == 'ACTIVO' and self.fecha_inicio <= date.today() <= self.fecha_fin


class Materia(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    creditos = models.PositiveIntegerField()
    horas_semanales = models.PositiveIntegerField()
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, related_name='materias')
    ciclo = models.ForeignKey(Ciclo, on_delete=models.CASCADE, related_name='materias')
    docente_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'materia'

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Horario(models.Model):
    dia_semana = models.CharField(max_length=10, choices=DiaSemana.choices)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    minutos_tolerancia = models.PositiveIntegerField(default=10, help_text='Minutos de tolerancia para tardanza')
    aula = models.CharField(max_length=50, blank=True)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='horarios')

    class Meta:
        db_table = 'horario'
        ordering = ['dia_semana', 'hora_inicio']

    def __str__(self):
        return f"{self.materia.nombre} - {self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}"

    def es_hora_valida(self):
        return self.hora_inicio < self.hora_fin

    def clean(self):
        hora_inicio = self._to_time(self.hora_inicio)
        hora_fin = self._to_time(self.hora_fin)

        if hora_inicio >= hora_fin:
            raise ValidationError("La hora de inicio debe ser menor que la hora de fin")

        overlapping = Horario.objects.filter(
            materia=self.materia,
            dia_semana=self.dia_semana
        ).exclude(id=self.id)
        for h in overlapping:
            h_inicio = self._to_time(h.hora_inicio)
            h_fin = self._to_time(h.hora_fin)
            if not (hora_fin <= h_inicio or hora_inicio >= h_fin):
                raise ValidationError("El horario se solapa con otro existente")

    @staticmethod
    def _to_time(value):
        if isinstance(value, str):
            from datetime import datetime
            return datetime.strptime(value, "%H:%M").time()
        return value


class Matricula(models.Model):
    estudiante_id = models.IntegerField()
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, related_name='matriculas')
    ciclo = models.ForeignKey(Ciclo, on_delete=models.CASCADE, related_name='matriculas')
    fecha_matricula = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=EstadoMatricula.choices, default='ACTIVA')

    class Meta:
        db_table = 'matricula'
        unique_together = ['estudiante_id', 'ciclo']
        ordering = ['-fecha_matricula']

    def __str__(self):
        return f"Matrícula #{self.id} - Estudiante #{self.estudiante_id}"

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class Modalidad (models.TextChoices):
    VIRTUAL = "VIRTUAL", " Virtual"
    PRESENCIAL ="PRESENCIAL", "Presencial"
    HIBRIDA = "HIBRIDA","Hibrida"


class Carrera (models.Model):
    codigo = models.CharField(max_length=5, unique=True)
    nombre = models.CharField(max_length=100, blank= False, verbose_name="Carrera")
    descripcion = models.TextField(blank=False, verbose_name="Descripcion")
    duracion = models.IntegerField(default=5,validators=[MinValueValidator(1),MaxValueValidator(20)])
    modalidad = models.CharField(choices=Modalidad.choices, default=Modalidad.PRESENCIAL)


class Ciclo (models.Model):
    numero_ciclo = models.IntegerField(default=1, blank= False,verbose_name="Numero del ciclo", help_text="Cuantos ciclo tiene la carrera")
    fecha_inicio = models.DateField(verbose_name="Inicio del ciclo")
    fecha_fin = models.DateField(verbose_name="Fin del ciclo")
    estado = models.BooleanField(default=True)

    carrera = models.ForeignKey(Carrera,on_delete=models.CASCADE,related_name="ciclos")


class Materia (models.Model):
    codigo = models.CharField(max_length=5, unique=True)
    nombre = models.CharField(max_length=100, blank= False, verbose_name="Materia")
    descripcion = models.TextField(blank=False, verbose_name="Descripcion")
    horasSemanales = models.IntegerField(blank= False,validators=[MinValueValidator(1),MaxValueValidator(6)])
    
    carrera = models.ForeignKey(Carrera,on_delete=models.CASCADE,related_name="materias_carrera")
    ciclo = models.ForeignKey(Ciclo,on_delete=models.CASCADE,related_name="materias")


class Curso(models.Model):
    paralelo = models.CharField(max_length=5)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    docente = models.ForeignKey("usuario.Docente",on_delete=models.PROTECT)


class Horario (models.Model):

    class DiaSemana(models.TextChoices):
        LUNES = "LUNES", "Lunes"
        MARTES = "MARTES", "Martes"
        MIERCOLES = "MIERCOLES", "Miercoles"
        JUEVES = "JUEVES", "Jueves"
        VIERNES = "VIERNES", "Viernes"

    dia_semana = models.CharField(choices=DiaSemana.choices)        
    hora_inicio = models.TimeField(blank= False, verbose_name="Hora de inicio")
    hora_fin = models.TimeField(blank= False, verbose_name="Hora de fin")
    tolerancia_minutos = models.PositiveIntegerField(default=10)

    curso = models.ForeignKey(Curso,on_delete=models.CASCADE,related_name="horarios")

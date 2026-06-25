from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Usuario(AbstractUser):
    cedula = models.CharField(max_length= 10, unique=True,verbose_name="Cédula") 
    telefono = models.CharField(max_length= 10, blank=True, null=False,verbose_name="Telefono") 

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Docente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete= models.CASCADE, related_name="docente")

    def __str__(self):
        return f"{self.usuario.first_name} {self.usuario.last_name}"

class Estudiante(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete= models.CASCADE)
    carrera = models.ForeignKey("academico.Carrera", on_delete=models.PROTECT, related_name="estudiantes")

    def __str__(self):
        return f"{self.usuario.first_name} {self.usuario.last_name}"

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UsuarioManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractUser):
    ROL_CHOICES = (
        ("ADMIN", "Administrador"),
        ("DOCENTE", "Docente"),
        ("ESTUDIANTE", "Estudiante"),
    )

    username = None
    email = models.EmailField(unique=True)
    cedula = models.CharField(max_length=10, unique=True)
    telefono = models.CharField(max_length=15, blank=True)
    rol = models.CharField(max_length=12, choices=ROL_CHOICES, default="ESTUDIANTE")
    foto_referencia_url = models.URLField(blank=True, null=True)
    intentos_fallidos = models.PositiveIntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    objects = UsuarioManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["cedula"]

    class Meta:
        db_table = "usuario"
        managed = False
        app_label = 'shared'

    def esta_bloqueado(self):
        from django.utils import timezone
        from datetime import timedelta
        if self.bloqueado_hasta and timezone.now() < self.bloqueado_hasta:
            return True
        if self.intentos_fallidos >= 5:
            self.bloqueado_hasta = timezone.now() + timedelta(minutes=30)
            self.save()
            return True
        return False

    def __str__(self):
        return f"{self.email} - {self.get_rol_display()}"


class CarreraModel(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    duracion = models.PositiveIntegerField()
    modalidad = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'carrera'
        app_label = 'shared'

    def __str__(self):
        return self.nombre


class CicloModel(models.Model):
    num = models.PositiveIntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=10)
    carrera = models.ForeignKey(CarreraModel, on_delete=models.DO_NOTHING, db_constraint=False)

    class Meta:
        managed = False
        db_table = 'ciclo'
        app_label = 'shared'


class MateriaModel(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    creditos = models.PositiveIntegerField()
    horas_semanales = models.PositiveIntegerField()
    carrera = models.ForeignKey(CarreraModel, on_delete=models.DO_NOTHING, db_constraint=False)
    docente_id = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'materia'
        app_label = 'shared'

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class HorarioModel(models.Model):
    dia_semana = models.CharField(max_length=10)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    minutos_tolerancia = models.PositiveIntegerField(default=10)
    aula = models.CharField(max_length=50, blank=True)
    materia = models.ForeignKey(MateriaModel, on_delete=models.DO_NOTHING, db_constraint=False)

    class Meta:
        managed = False
        db_table = 'horario'
        app_label = 'shared'


class AsistenciaModel(models.Model):
    fecha = models.DateField()
    hora_registro = models.TimeField()
    estado = models.CharField(max_length=12)
    confianza = models.FloatField(default=0.0)
    estudiante_id = models.IntegerField()
    horario_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'asistencia'
        app_label = 'shared'


class JustificacionModel(models.Model):
    motivo = models.TextField()
    fecha_solicitud = models.DateTimeField()
    estado = models.CharField(max_length=10)
    estudiante_id = models.IntegerField()
    asistencia_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'justificacion'
        app_label = 'shared'


class RegistroFacialModel(models.Model):
    estado = models.CharField(max_length=10)
    fecha_registro = models.DateTimeField()
    face_id = models.CharField(max_length=100)
    estudiante_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'registro_facial'
        app_label = 'shared'


class ReporteModel(models.Model):
    tipo = models.CharField(max_length=15)
    fecha_generacion = models.DateTimeField()
    parametros = models.JSONField(default=dict)
    formato = models.CharField(max_length=10)
    archivo_url = models.URLField(blank=True, null=True)
    generado_por_id = models.IntegerField(null=True, blank=True)
    nombre = models.CharField(max_length=200, blank=True)

    class Meta:
        managed = False
        db_table = 'reporte'
        app_label = 'shared'

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser
from django.db import models


class DiaSemana(models.TextChoices):
    LUNES = 'LUNES', 'Lunes'
    MARTES = 'MARTES', 'Martes'
    MIERCOLES = 'MIERCOLES', 'Miércoles'
    JUEVES = 'JUEVES', 'Jueves'
    VIERNES = 'VIERNES', 'Viernes'
    SABADO = 'SABADO', 'Sábado'
    DOMINGO = 'DOMINGO', 'Domingo'


class SharedUsuarioManager(BaseUserManager):
    """
    Manager del espejo. Solo lectura — nunca crea usuarios.
    """

    def get_by_natural_key(self, email):
        return self.get(email=email)

    def create_user(self, email, password=None, **extra_fields):
        raise NotImplementedError(
            "shared.Usuario es de solo lectura. Cree usuarios en usuario-service."
        )

    def create_superuser(self, email, password=None, **extra_fields):
        raise NotImplementedError(
            "shared.Usuario es de solo lectura. Cree superusuarios en usuario-service."
        )


class Usuario(AbstractBaseUser):
    """
    Espejo managed=False de apps.usuario.Usuario.

    Se usa como AUTH_USER_MODEL en los microservicios que NO son
    usuario-service (academico, asistencia, reportes, monitoring).

    Hereda SOLO AbstractBaseUser (sin PermissionsMixin) para evitar
    el choque de reverse accessors con usuario.Usuario cuando ambas
    apps están cargadas en el monolito. Este modelo NUNCA necesita
    groups ni user_permissions — esos los gestiona usuario-service.
    """
    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    cedula = models.CharField(max_length=10, unique=True)
    telefono = models.CharField(max_length=15, blank=True)
    rol = models.CharField(max_length=12)
    foto_referencia_url = models.URLField(blank=True, null=True)
    intentos_fallidos = models.PositiveIntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = SharedUsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["cedula"]

    class Meta:
        managed = False
        db_table = "usuario"
        app_label = "shared"

    def __str__(self):
        return self.email


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
    dia_semana = models.CharField(max_length=10, choices=DiaSemana.choices)
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

class RegistroAuditoriaModel(models.Model):
    """
    Espejo managed=False de apps.monitoring.models.RegistroAuditoria.
    Los 4 microservicios (usuario/academico/asistencia/reportes) usan ESTE
    modelo para ESCRIBIR filas de auditoría (vía shared.audit.registrar_auditoria),
    ya que ninguno tiene instalada la app `apps.monitoring`. El dueño real de
    la tabla y sus migraciones es monitoring-service.
    """
    usuario_id = models.IntegerField(null=True, blank=True)
    usuario_nombre = models.CharField(max_length=150, default='desconocido')
    accion = models.CharField(max_length=10)
    servicio = models.CharField(max_length=20)
    modelo = models.CharField(max_length=100)
    registro_id = models.CharField(max_length=50, null=True, blank=True)
    descripcion = models.CharField(max_length=500)
    datos_modificados = models.JSONField(null=True, blank=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'monitoring_registroauditoria'
        app_label = 'shared'

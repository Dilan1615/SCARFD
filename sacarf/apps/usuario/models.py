import secrets

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


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

    # Eliminar username
    username = None

    # El email se utilziara para iniciar sesion
    email = models.EmailField(unique=True)
    cedula = models.CharField(max_length=10, unique=True)
    telefono = models.CharField(max_length=15, blank=True)

    rol = models.CharField(
        max_length=12,
        choices=ROL_CHOICES,
        default="ESTUDIANTE"
    )

    foto_referencia_url = models.URLField(blank=True, null=True)

    # Manager personalizado
    objects = UsuarioManager()

    # Campo usado para login
    USERNAME_FIELD = "email"

    # Campos obligatorios al crear un superusuario
    REQUIRED_FIELDS = ["cedula"]

    class Meta:
        db_table = "usuario"

    def __str__(self):
        return f"{self.email} - {self.get_rol_display()}"


class PasswordResetToken(models.Model):

    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = "password_reset_token"

    @staticmethod
    def generar_token():
        return secrets.token_urlsafe(32)

    def is_valid(self):
        timeout = getattr(settings, "PASSWORD_RESET_TIMEOUT", 3600)

        return (
            not self.is_used
            and (timezone.now() - self.created_at).total_seconds() < timeout
        )

    def __str__(self):
        return f"Token para {self.email}"
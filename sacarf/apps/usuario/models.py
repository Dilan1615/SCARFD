import secrets
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class Usuario(AbstractUser):
    ROL_CHOICES = (
        ('ADMIN', 'Administrador'),
        ('DOCENTE', 'Docente'),
        ('ESTUDIANTE', 'Estudiante'),
    )
    
    # Campos adicionales
    cedula = models.CharField(max_length=10, unique=True)
    telefono = models.CharField(max_length=15, blank=True)
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='ESTUDIANTE')
    foto_referencia_url = models.URLField(blank=True, null=True)
    
    # Sobrescribir grupos y permisos con related_name únicos
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='usuario_set',  # ← Cambiado para evitar conflicto
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='usuario_permissions_set',  # ← Cambiado para evitar conflicto
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
    )

    class Meta:
        db_table = 'usuario'
        # IMPORTANTE: No crear la tabla auth_user
        swappable = 'AUTH_USER_MODEL'

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"

class PasswordResetToken(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'password_reset_token'

    @staticmethod
    def generar_token():
        return secrets.token_urlsafe(32)

    def is_valid(self):
        timeout = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 3600)
        return not self.is_used and (timezone.now() - self.created_at).total_seconds() < timeout

    def __str__(self):
        return f"Token for {self.email}"
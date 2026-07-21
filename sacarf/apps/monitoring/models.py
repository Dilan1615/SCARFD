from django.db import models


class AccionAuditoria(models.TextChoices):
    CREATE = 'CREATE', 'Creación'
    UPDATE = 'UPDATE', 'Actualización'
    DELETE = 'DELETE', 'Eliminación'


class RegistroAuditoria(models.Model):
    """
    Log centralizado de acciones CRUD realizadas en cualquier microservicio
    de SACARF. Esta tabla es propiedad de monitoring-service (managed=True,
    con sus propias migraciones). Los demás microservicios NO importan este
    modelo directamente: escriben a través de `shared.audit.registrar_auditoria`,
    que usa el espejo `shared.models.RegistroAuditoriaModel` (managed=False)
    apuntando a la misma tabla física — mismo patrón que el resto de modelos
    `shared` del proyecto, pero en sentido de escritura en vez de lectura.
    """
    usuario_id = models.IntegerField(null=True, blank=True)
    usuario_nombre = models.CharField(max_length=150, default='desconocido')
    accion = models.CharField(max_length=10, choices=AccionAuditoria.choices)
    servicio = models.CharField(max_length=20)
    modelo = models.CharField(max_length=100)
    registro_id = models.CharField(max_length=50, null=True, blank=True)
    descripcion = models.CharField(max_length=500)
    datos_modificados = models.JSONField(null=True, blank=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'monitoring_registroauditoria'
        ordering = ['-fecha_hora']
        indexes = [
            models.Index(fields=['-fecha_hora']),
            models.Index(fields=['servicio']),
            models.Index(fields=['modelo']),
            models.Index(fields=['usuario_id']),
            models.Index(fields=['accion']),
        ]

    def __str__(self):
        return f"[{self.servicio}] {self.accion} {self.modelo} #{self.registro_id} por {self.usuario_nombre}"

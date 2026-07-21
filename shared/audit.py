"""
shared/audit.py

Mecanismo de auditoría centralizada. Los microservicios (usuario, academico,
asistencia, reportes) NO tienen instalada la app `apps.monitoring`, así que
no pueden importar `apps.monitoring.models.RegistroAuditoria` directamente.

En su lugar escriben a través de `registrar_auditoria()`, que usa
`shared.models.RegistroAuditoriaModel`: un espejo managed=False que apunta a
la misma tabla física `monitoring_registroauditoria` (dueña real:
monitoring-service, que corre las migraciones). Es el mismo patrón que ya
usa el proyecto para leer modelos de otros servicios vía `shared/`, aplicado
ahora también para escritura de un log transversal.

No lanza excepciones hacia la vista que lo llama: un fallo al auditar nunca
debe romper la operación de negocio real (crear/actualizar/eliminar).
"""
import datetime
import decimal
import logging

logger = logging.getLogger('sacarf.auditoria')


def _a_serializable(valor):
    """Convierte valores comunes de Django a algo JSON-serializable."""
    if isinstance(valor, (str, int, float, bool)) or valor is None:
        return valor
    if isinstance(valor, (datetime.date, datetime.datetime)):
        return valor.isoformat()
    if isinstance(valor, decimal.Decimal):
        return float(valor)
    if isinstance(valor, dict):
        return {k: _a_serializable(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple, set)):
        return [_a_serializable(v) for v in valor]
    # Instancias de modelo, archivos, etc. -> representación en texto
    return str(valor)


def registrar_auditoria(
    *,
    usuario_id,
    usuario_nombre,
    accion,
    servicio,
    modelo,
    registro_id,
    descripcion,
    datos_modificados=None,
    ip_origen=None,
):
    """
    Inserta una fila en el log de auditoría centralizado.

    accion: 'CREATE' | 'UPDATE' | 'DELETE'
    servicio: 'usuario' | 'academico' | 'asistencia' | 'reportes'
    """
    try:
        from shared.models import RegistroAuditoriaModel

        RegistroAuditoriaModel.objects.create(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre or 'desconocido',
            accion=accion,
            servicio=servicio,
            modelo=modelo,
            registro_id=str(registro_id) if registro_id is not None else None,
            descripcion=descripcion[:500],
            datos_modificados=_a_serializable(datos_modificados) if datos_modificados else None,
            ip_origen=ip_origen,
        )
    except Exception:
        # La auditoría nunca debe tumbar la operación de negocio real.
        logger.exception(
            "No se pudo registrar auditoría: servicio=%s modelo=%s accion=%s",
            servicio, modelo, accion,
        )


def _obtener_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _datos_usuario(request):
    user = getattr(request, 'user', None)
    if user is None or not getattr(user, 'is_authenticated', False):
        return None, 'anonimo'
    nombre = getattr(user, 'username', None) or getattr(user, 'email', None) or f"usuario #{user.id}"
    return getattr(user, 'id', None), nombre


class AuditoriaMixin:
    """
    Mixin para ModelViewSet de DRF: registra automáticamente CREATE/UPDATE
    en `perform_create` / `perform_update`, y DELETE en `perform_destroy`.

    Uso en cualquier viewset de cualquier microservicio:

        class MateriaViewSet(AuditoriaMixin, viewsets.ModelViewSet):
            auditoria_servicio = 'academico'
            auditoria_modelo = 'Materia'
            ...

    Para acciones personalizadas (`@action`) que no pasan por perform_create/
    update/destroy (ej. un `registrar()` o `aprobar()` manual), llamar
    directamente a `self.auditar(...)` o a `registrar_auditoria(...)`.
    """
    auditoria_servicio = None
    auditoria_modelo = None

    def auditoria_descripcion(self, instance, accion):
        return f"{accion.title()} en {self._nombre_modelo()} #{instance.pk}"

    def _nombre_modelo(self):
        return self.auditoria_modelo or self.queryset.model.__name__

    def _nombre_servicio(self):
        if self.auditoria_servicio:
            return self.auditoria_servicio
        from django.conf import settings
        return getattr(settings, 'SERVICE_NAME', 'desconocido')

    def auditar(self, instance, accion, descripcion=None, datos_modificados=None):
        usuario_id, usuario_nombre = _datos_usuario(self.request)
        registrar_auditoria(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion=accion,
            servicio=self._nombre_servicio(),
            modelo=self._nombre_modelo(),
            registro_id=getattr(instance, 'pk', None),
            descripcion=descripcion or self.auditoria_descripcion(instance, accion),
            datos_modificados=datos_modificados,
            ip_origen=_obtener_ip(self.request),
        )

    def perform_create(self, serializer):
        instance = serializer.save()
        self.auditar(instance, 'CREATE', datos_modificados=dict(serializer.validated_data))

    def perform_update(self, serializer):
        campos = list(serializer.validated_data.keys())
        antes = {campo: getattr(serializer.instance, campo, None) for campo in campos}
        instance = serializer.save()
        despues = {campo: getattr(instance, campo, None) for campo in campos}
        self.auditar(
            instance, 'UPDATE',
            datos_modificados={'antes': antes, 'despues': despues},
        )

    def perform_destroy(self, instance):
        pk = instance.pk
        descripcion = self.auditoria_descripcion(instance, 'DELETE')
        # Capturamos los datos ANTES de borrar: tras instance.delete() Django
        # pone pk=None y el objeto deja de ser confiable para leer campos.
        snapshot = {
            f.name: getattr(instance, f.name, None)
            for f in instance._meta.fields
        }
        instance.delete()
        usuario_id, usuario_nombre = _datos_usuario(self.request)
        registrar_auditoria(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion='DELETE',
            servicio=self._nombre_servicio(),
            modelo=self._nombre_modelo(),
            registro_id=pk,
            descripcion=descripcion,
            datos_modificados=snapshot,
            ip_origen=_obtener_ip(self.request),
        )

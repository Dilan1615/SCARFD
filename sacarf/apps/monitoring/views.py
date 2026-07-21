<<<<<<< HEAD
from datetime import datetime, timedelta

from django.utils.dateparse import parse_datetime
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import services
from .models import RegistroAuditoria
from .serializers import RegistroAuditoriaSerializer
=======
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from . import services
>>>>>>> moduloJustificacion


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estado_servicios(request):
    """Estado de cada microservicio SACARF: activo / caído + tiempo de respuesta."""
    return Response(services.obtener_estado_servicios())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def infraestructura(request):
<<<<<<< HEAD
    """CPU, RAM, disco (psutil) y estado de contenedores Docker (SDK)."""
=======
    """CPU, RAM, disco (node-exporter) y estado de contenedores Docker (cAdvisor)."""
>>>>>>> moduloJustificacion
    return Response(services.obtener_infraestructura())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def backend_metrics(request):
<<<<<<< HEAD
    """Registros de auditoría recientes por servicio y acción."""
=======
    """Peticiones/min, tiempo de respuesta, errores 4xx/5xx y desglose por microservicio."""
>>>>>>> moduloJustificacion
    rango = int(request.query_params.get('rango_minutos', 30))
    rango = max(5, min(rango, 180))
    return Response(services.obtener_metricas_backend(rango_minutos=rango))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def base_datos(request):
<<<<<<< HEAD
    """Conexiones activas, transacciones y almacenamiento de PostgreSQL (SQL directa)."""
=======
    """Conexiones activas, consultas por segundo y almacenamiento de PostgreSQL."""
>>>>>>> moduloJustificacion
    return Response(services.obtener_metricas_bd())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def negocio(request):
    """Indicadores de negocio SACARF: usuarios, asistencias, reconocimientos, reportes."""
    return Response(services.obtener_metricas_negocio())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resumen(request):
    """
    Un solo endpoint con todo lo necesario para pintar el dashboard completo
    en una sola petición (útil para el primer render / polling simple).
    """
    data = {
        'servicios': services.obtener_estado_servicios(),
        'infraestructura': services.obtener_infraestructura(),
        'backend': services.obtener_metricas_backend(rango_minutos=30),
        'base_datos': services.obtener_metricas_bd(),
        'negocio': services.obtener_metricas_negocio(),
    }
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
def health(request):
    """Sin autenticación: usado por el propio monitoring para su self-check."""
    return Response({'status': 'ok', 'service': 'monitoring'})
<<<<<<< HEAD


# ──────────────────────────────────────────────────────────────────────────
# Auditoría — Logs de actividad del sistema
# ──────────────────────────────────────────────────────────────────────────
class PaginacionAuditoria(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class RegistroAuditoriaListView(generics.ListAPIView):
    """
    GET /api/monitoring/auditoria/

    Filtros por query param (todos opcionales, combinables):
      - usuario     -> coincidencia parcial en usuario_nombre
      - accion      -> CREATE | UPDATE | DELETE
      - servicio    -> usuario | academico | asistencia | reportes
      - modelo      -> coincidencia parcial en el nombre del modelo
      - fecha_desde -> ISO 8601, ej. 2026-07-01T00:00:00
      - fecha_hasta -> ISO 8601
      - buscar      -> coincidencia parcial en la descripción
    """
    serializer_class = RegistroAuditoriaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PaginacionAuditoria

    def get_queryset(self):
        qs = RegistroAuditoria.objects.all()
        params = self.request.query_params

        usuario = params.get('usuario')
        if usuario:
            qs = qs.filter(usuario_nombre__icontains=usuario)

        accion = params.get('accion')
        if accion:
            qs = qs.filter(accion=accion.upper())

        servicio = params.get('servicio')
        if servicio:
            qs = qs.filter(servicio=servicio.lower())

        modelo = params.get('modelo')
        if modelo:
            qs = qs.filter(modelo__icontains=modelo)

        buscar = params.get('buscar')
        if buscar:
            qs = qs.filter(descripcion__icontains=buscar)

        fecha_desde = parse_datetime(params.get('fecha_desde', '') or '')
        if fecha_desde:
            qs = qs.filter(fecha_hora__gte=fecha_desde)

        fecha_hasta = parse_datetime(params.get('fecha_hasta', '') or '')
        if fecha_hasta:
            qs = qs.filter(fecha_hora__lte=fecha_hasta)

        return qs


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auditoria_resumen(request):
    """
    Conteos rápidos de las últimas 24h, para una franja de estadísticas
    encima de la tabla de logs (ej. "12 creaciones, 3 eliminaciones...").
    """
    desde = datetime.now() - timedelta(hours=24)
    base = RegistroAuditoria.objects.filter(fecha_hora__gte=desde)

    por_accion = {
        accion: base.filter(accion=accion).count()
        for accion in ['CREATE', 'UPDATE', 'DELETE']
    }
    por_servicio = {
        servicio: base.filter(servicio=servicio).count()
        for servicio in ['usuario', 'academico', 'asistencia', 'reportes']
    }

    return Response({
        'total_ultimas_24h': base.count(),
        'por_accion': por_accion,
        'por_servicio': por_servicio,
    }, status=status.HTTP_200_OK)
=======
>>>>>>> moduloJustificacion

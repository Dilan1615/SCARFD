from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from . import services


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estado_servicios(request):
    """Estado de cada microservicio SACARF: activo / caído + tiempo de respuesta."""
    return Response(services.obtener_estado_servicios())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def infraestructura(request):
    """CPU, RAM, disco (node-exporter) y estado de contenedores Docker (cAdvisor)."""
    return Response(services.obtener_infraestructura())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def backend_metrics(request):
    """Peticiones/min, tiempo de respuesta, errores 4xx/5xx y desglose por microservicio."""
    rango = int(request.query_params.get('rango_minutos', 30))
    rango = max(5, min(rango, 180))
    return Response(services.obtener_metricas_backend(rango_minutos=rango))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def base_datos(request):
    """Conexiones activas, consultas por segundo y almacenamiento de PostgreSQL."""
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

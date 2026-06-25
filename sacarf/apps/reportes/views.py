from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from datetime import datetime
import uuid

from .models import Reporte, TipoReporte, FormatoReporte
from .serializers import ReporteSerializer, GenerarReporteSerializer
from .services import ReporteService
from apps.academico.models import Ciclo, Materia
from apps.usuario.models import Usuario

class ReporteViewSet(viewsets.ModelViewSet):
    queryset = Reporte.objects.all()
    serializer_class = ReporteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.rol == 'ADMIN':
            return self.queryset
        elif user.rol == 'DOCENTE':
            # Docentes ven reportes de sus materias
            return self.queryset.filter(
                parametros__materia_id__in=user.materias_dictadas.values_list('id', flat=True)
            )
        return self.queryset.none()
    
    @action(detail=False, methods=['post'])
    def generar(self, request):
        """Genera un nuevo reporte"""
        if request.user.rol not in ['ADMIN', 'DOCENTE']:
            return Response({'error': 'No tienes permiso para generar reportes'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        serializer = GenerarReporteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        tipo = data['tipo']
        formato = data.get('formato', 'PDF')
        
        # Obtener datos para el reporte
        reporte_service = ReporteService()
        datos = reporte_service.obtener_datos_asistencia(tipo, data)
        
        if not datos:
            return Response({
                'error': 'No hay datos para generar el reporte con los filtros seleccionados'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Preparar título
        titulo = f"Reporte {dict(TipoReporte.choices).get(tipo, '')}"
        subtitulo = None
        
        if tipo == 'POR_ESTUDIANTE' and data.get('estudiante_id'):
            estudiante = Usuario.objects.get(id=data['estudiante_id'])
            subtitulo = f"Estudiante: {estudiante.first_name} {estudiante.last_name}"
        elif tipo == 'POR_MATERIA' and data.get('materia_id'):
            materia = Materia.objects.get(id=data['materia_id'])
            subtitulo = f"Materia: {materia.nombre}"
        elif tipo == 'POR_CICLO' and data.get('ciclo_id'):
            ciclo = Ciclo.objects.get(id=data['ciclo_id'])
            subtitulo = f"Ciclo: {ciclo.num} - {ciclo.carrera.nombre}"
        
        # Generar archivo según formato
        if formato == 'PDF':
            file_buffer = reporte_service.generar_reporte_pdf(datos, titulo, subtitulo)
            extension = 'pdf'
            content_type = 'application/pdf'
        else:  # EXCEL
            file_buffer = reporte_service.generar_reporte_excel(datos, titulo)
            extension = 'xlsx'
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        # Guardar el reporte en la base de datos
        nombre = f"{titulo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        reporte = Reporte.objects.create(
            tipo=tipo,
            formato=formato,
            parametros=data,
            generado_por=request.user,
            nombre=nombre
        )
        
        # Guardar archivo (aquí podremos subirlo a S3 o almacenarlo localmente)
        # Por ahora, lo dejamos en memoria y retornamos la descarga directa
        
        return Response({
            'success': True,
            'message': 'Reporte generado exitosamente',
            'reporte_id': reporte.id,
            'nombre': nombre,
            'formato': formato,
            'tipo': tipo,
            'total_registros': len(datos)
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def descargar(self, request, pk=None):
        """Descarga un reporte generado"""
        reporte = self.get_object()
        
        # Verificar permisos
        if request.user.rol not in ['ADMIN']:
            if request.user.rol == 'DOCENTE':
                # Verificar que el docente tiene acceso
                materia_ids = request.user.materias_dictadas.values_list('id', flat=True)
                if reporte.parametros.get('materia_id') not in materia_ids:
                    return Response({'error': 'No tienes permiso para descargar este reporte'}, 
                                  status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'No tienes permiso para descargar reportes'}, 
                              status=status.HTTP_403_FORBIDDEN)
        
        # Regenerar el reporte si no tiene archivo
        if not reporte.archivo_url:
            return Response({'error': 'El archivo del reporte no está disponible'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # Aquí se implementaría la descarga desde S3 o archivo local
        return Response({
            'message': 'Descarga disponible',
            'url': reporte.archivo_url
        })
    
    @action(detail=False, methods=['get'])
    def tipos(self, request):
        """Lista los tipos de reporte disponibles"""
        return Response({
            'tipos': [
                {'value': code, 'label': label} 
                for code, label in TipoReporte.choices
            ],
            'formatos': [
                {'value': code, 'label': label} 
                for code, label in FormatoReporte.choices
            ]
        })
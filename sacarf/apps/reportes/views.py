from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import IntegerField
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from datetime import datetime

from .models import Reporte, TipoReporte, FormatoReporte
from .serializers import ReporteSerializer, GenerarReporteSerializer
from .services import ReporteService
from shared.models import Usuario, MateriaModel, CicloModel, HorarioModel
from shared.audit import AuditoriaMixin, registrar_auditoria, _datos_usuario, _obtener_ip



class ReporteViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    queryset = Reporte.objects.all()
    serializer_class = ReporteSerializer
    permission_classes = [permissions.IsAuthenticated]
    auditoria_servicio = 'reportes'
    auditoria_modelo = 'Reporte'

    def get_queryset(self):
        user = self.request.user
        if user.rol == 'ADMIN':
            return self.queryset
        elif user.rol == 'DOCENTE':
            materia_ids = list(MateriaModel.objects.filter(docente_id=user.id).values_list('id', flat=True))
            if not materia_ids:
                return self.queryset.none()
            return self.queryset.annotate(
                materia_id_int=Cast(KeyTextTransform('materia_id', 'parametros'), IntegerField())
            ).filter(materia_id_int__in=materia_ids)
        return self.queryset.none()

    @action(detail=False, methods=['post'])
    def generar(self, request):
        if request.user.rol not in ['ADMIN', 'DOCENTE']:
            return Response({'error': 'No tienes permiso para generar reportes'},
                          status=status.HTTP_403_FORBIDDEN)

        serializer = GenerarReporteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        tipo = data['tipo']
        formato = data.get('formato', 'PDF')

        reporte_service = ReporteService()
        datos = reporte_service.obtener_datos_asistencia(tipo, data)

        if not datos:
            return Response({
                'error': 'No hay datos para generar el reporte con los filtros seleccionados'
            }, status=status.HTTP_404_NOT_FOUND)

        titulo = f"Reporte {dict(TipoReporte.choices).get(tipo, '')}"
        subtitulo = None

        if tipo == 'POR_ESTUDIANTE' and data.get('estudiante_id'):
            try:
                estudiante = Usuario.objects.get(id=data['estudiante_id'])
                subtitulo = f"Estudiante: {estudiante.first_name} {estudiante.last_name}"
            except Usuario.DoesNotExist:
                pass
        elif tipo == 'POR_MATERIA' and data.get('materia_id'):
            try:
                materia = MateriaModel.objects.get(id=data['materia_id'])
                subtitulo = f"Materia: {materia.nombre}"
            except MateriaModel.DoesNotExist:
                pass
        elif tipo == 'POR_CICLO' and data.get('ciclo_id'):
            try:
                ciclo = CicloModel.objects.select_related('carrera').get(id=data['ciclo_id'])
                subtitulo = f"Ciclo: {ciclo.num} - {ciclo.carrera.nombre}"
            except CicloModel.DoesNotExist:
                pass

        if formato == 'PDF':
            file_buffer = reporte_service.generar_reporte_pdf(datos, titulo, subtitulo)
            extension = 'pdf'
            content_type = 'application/pdf'
        else:
            file_buffer = reporte_service.generar_reporte_excel(datos, titulo)
            extension = 'xlsx'
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        nombre = f"{titulo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        reporte = Reporte.objects.create(
            tipo=tipo,
            formato=formato,
            parametros=data,
            generado_por_id=request.user.id,
            nombre=nombre
        )

        usuario_id, usuario_nombre = _datos_usuario(request)
        registrar_auditoria(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion='CREATE',
            servicio='reportes',
            modelo='Reporte',
            registro_id=reporte.id,
            descripcion=f"Generó reporte {titulo} en formato {formato}",
            datos_modificados={'tipo': tipo, 'formato': formato, 'total_registros': len(datos)},
            ip_origen=_obtener_ip(request),
        )

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
        reporte = self.get_object()

        if request.user.rol not in ['ADMIN']:
            if request.user.rol == 'DOCENTE':
                materia_ids = list(MateriaModel.objects.filter(docente_id=request.user.id).values_list('id', flat=True))
                if reporte.parametros.get('materia_id') not in materia_ids:
                    return Response({'error': 'No tienes permiso para descargar este reporte'},
                                  status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'No tienes permiso para descargar reportes'},
                              status=status.HTTP_403_FORBIDDEN)

        if not reporte.archivo_url:
            return Response({'error': 'El archivo del reporte no está disponible'},
                          status=status.HTTP_404_NOT_FOUND)

        return Response({
            'message': 'Descarga disponible',
            'url': reporte.archivo_url
        })

    @action(detail=False, methods=['get'])
    def tipos(self, request):
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

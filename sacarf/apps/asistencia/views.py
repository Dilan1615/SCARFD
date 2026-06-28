from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from datetime import datetime, timedelta
import uuid

from .models import (
    Asistencia, Justificacion, Reconocimiento, 
    RegistroFacial, EstadoAsistencia
)
from .serializers import (
    AsistenciaSerializer, JustificacionSerializer, 
    ReconocimientoSerializer, RegistroFacialSerializer,
    RegistrarAsistenciaSerializer, AprobarJustificacionSerializer
)
from .services import AwsRekognitionService
from apps.usuario.models import Usuario
from apps.academico.models import Horario

class AsistenciaViewSet(viewsets.ModelViewSet):
    queryset = Asistencia.objects.all()
    serializer_class = AsistenciaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Estudiantes solo ven sus propias asistencias
        if user.rol == 'ESTUDIANTE':
            return self.queryset.filter(estudiante=user)
        # Docentes ven las asistencias de sus materias
        elif user.rol == 'DOCENTE':
            materias_ids = user.materias_dictadas.values_list('id', flat=True)
            horarios_ids = Horario.objects.filter(materia__in=materias_ids).values_list('id', flat=True)
            return self.queryset.filter(horario__in=horarios_ids)
        # Admin ve todo
        return self.queryset
    
    @action(detail=False, methods=['post'])
    def registrar(self, request):
        """Registra asistencia mediante reconocimiento facial"""
        serializer = RegistrarAsistenciaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        estudiante = serializer.validated_data['estudiante']
        horario = serializer.validated_data['horario']
        imagen_base64 = serializer.validated_data['imagen_base64']
        ubicacion = serializer.validated_data.get('ubicacion', '')
        
        # Procesar imagen
        aws_service = AwsRekognitionService()
        try:
            image_bytes = aws_service.decode_base64_image(imagen_base64)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Buscar rostro en AWS Rekognition
        resultado = aws_service.buscar_rostro(image_bytes)
        
        if not resultado or float(resultado['confidence']) < 85.0:
            return Response({
                'success': False,
                'message': 'No se pudo reconocer el rostro o confianza baja',
                'confidence': resultado['confidence'] if resultado else 0
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que el rostro pertenece al estudiante
        if int(resultado['external_id']) != estudiante.id:
            return Response({
                'success': False,
                'message': 'El rostro no coincide con el estudiante registrado'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Subir imagen a S3
        filename = f"asistencias/{datetime.now().strftime('%Y/%m/%d')}/{uuid.uuid4()}.jpg"
        imagen_url = aws_service.subir_imagen_s3(image_bytes, filename)
        
        # Registrar asistencia
        with transaction.atomic():
            # Crear reconocimiento
            reconocimiento = Reconocimiento.objects.create(
                estudiante=estudiante,
                resultado=True,
                confianza=resultado['confidence'],
                ubicacion=ubicacion,
                imagen_url=imagen_url,
                registro_facial=getattr(estudiante, 'registro_facial', None)
            )
            
            # Calcular estado
            hora_actual = datetime.now().time()
            hora_limite_presente = (datetime.combine(datetime.today(), horario.hora_inicio) + 
                                   timedelta(minutes=horario.minutos_tolerancia)).time()
            
            if hora_actual <= hora_limite_presente:
                estado = EstadoAsistencia.PRESENTE
            else:
                estado = EstadoAsistencia.TARDE
            
            # Crear asistencia
            asistencia = Asistencia.objects.create(
                estudiante=estudiante,
                horario=horario,
                estado=estado,
                confianza=resultado['confidence'],
                reconocimiento=reconocimiento
            )
        
        return Response({
            'success': True,
            'message': 'Asistencia registrada exitosamente',
            'estado': estado,
            'confianza': resultado['confidence'],
            'asistencia_id': asistencia.id
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def por_estudiante(self, request):
        """Obtiene asistencias por estudiante"""
        estudiante_id = request.query_params.get('estudiante_id')
        if not estudiante_id:
            return Response({'error': 'Se requiere estudiante_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        asistencias = self.get_queryset().filter(estudiante_id=estudiante_id)
        serializer = self.get_serializer(asistencias, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_materia(self, request):
        """Obtiene asistencias por materia"""
        materia_id = request.query_params.get('materia_id')
        if not materia_id:
            return Response({'error': 'Se requiere materia_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        horarios = Horario.objects.filter(materia_id=materia_id)
        asistencias = self.get_queryset().filter(horario__in=horarios)
        serializer = self.get_serializer(asistencias, many=True)
        return Response(serializer.data)

class JustificacionViewSet(viewsets.ModelViewSet):
    queryset = Justificacion.objects.all()
    serializer_class = JustificacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.rol == 'ESTUDIANTE':
            return self.queryset.filter(estudiante=user)
        elif user.rol == 'DOCENTE':
            # Docentes ven justificaciones de sus estudiantes
            materias_ids = user.materias_dictadas.values_list('id', flat=True)
            horarios_ids = Horario.objects.filter(materia__in=materias_ids).values_list('id', flat=True)
            asistencias_ids = Asistencia.objects.filter(horario__in=horarios_ids).values_list('id', flat=True)
            return self.queryset.filter(asistencia__in=asistencias_ids)
        return self.queryset
    
    def create(self, request, *args, **kwargs):
        """Crear una solicitud de justificación"""
        data = request.data
        data['estudiante'] = request.user.id
        
        # Verificar que la asistencia pertenece al estudiante
        asistencia_id = data.get('asistencia')
        if asistencia_id:
            asistencia = get_object_or_404(Asistencia, id=asistencia_id, estudiante=request.user)
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def aprobar(self, request):
        """Aprobar o rechazar una justificación (solo docentes)"""
        if request.user.rol != 'DOCENTE':
            return Response({'error': 'Solo docentes pueden aprobar justificaciones'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        serializer = AprobarJustificacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        justificacion = get_object_or_404(Justificacion, id=serializer.validated_data['justificacion_id'])
        
        # Verificar que el docente es el de la materia
        materia_ids = request.user.materias_dictadas.values_list('id', flat=True)
        horarios_ids = Horario.objects.filter(materia__in=materia_ids).values_list('id', flat=True)
        if justificacion.asistencia.horario_id not in horarios_ids:
            return Response({'error': 'No tienes permiso para aprobar esta justificación'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if serializer.validated_data['aprobar']:
            justificacion.aprobar(
                request.user, 
                serializer.validated_data.get('comentario', '')
            )
            message = 'Justificación aprobada'
        else:
            justificacion.rechazar(
                request.user, 
                serializer.validated_data.get('comentario', '')
            )
            message = 'Justificación rechazada'
        
        return Response({
            'success': True,
            'message': message,
            'estado': justificacion.estado
        })

class ReconocimientoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Reconocimiento.objects.all()
    serializer_class = ReconocimientoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.rol == 'ESTUDIANTE':
            return self.queryset.filter(estudiante=user)
        return self.queryset

class RegistroFacialViewSet(viewsets.ModelViewSet):
    queryset = RegistroFacial.objects.all()
    serializer_class = RegistroFacialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.rol == 'ESTUDIANTE':
            return self.queryset.filter(estudiante=user)
        return self.queryset
    
    @action(detail=False, methods=['post'])
    def registrar_rostro(self, request):
        """Registra el rostro de un estudiante"""
        if request.user.rol != 'ESTUDIANTE':
            return Response({'error': 'Solo estudiantes pueden registrar su rostro'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        imagen_base64 = request.data.get('imagen_base64')
        if not imagen_base64:
            return Response({'error': 'Se requiere imagen_base64'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si ya tiene registro facial
        if RegistroFacial.objects.filter(estudiante=request.user).exists():
            return Response({'error': 'Ya tienes un registro facial activo'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Procesar imagen
        aws_service = AwsRekognitionService()
        try:
            image_bytes = aws_service.decode_base64_image(imagen_base64)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Indexar rostro en AWS
        resultado = aws_service.indexar_rostro(image_bytes, str(request.user.id))
        
        if not resultado:
            return Response({
                'success': False,
                'message': 'No se pudo indexar el rostro. Intenta con otra imagen.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear registro facial
        registro = RegistroFacial.objects.create(
            estudiante=request.user,
            face_id=resultado['face_id']
        )
        
        # Subir imagen de referencia a S3
        filename = f"referencias/{request.user.id}/{uuid.uuid4()}.jpg"
        imagen_url = aws_service.subir_imagen_s3(image_bytes, filename)
        if imagen_url:
            request.user.foto_referencia_url = imagen_url
            request.user.save()
        
        return Response({
            'success': True,
            'message': 'Rostro registrado exitosamente',
            'face_id': resultado['face_id'],
            'confidence': resultado['confidence']
        })
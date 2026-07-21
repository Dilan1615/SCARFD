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
from shared.models import HorarioModel, MateriaModel
# ── Auditoría (nuevo) ────────────────────────────────────────────────────
from shared.audit import AuditoriaMixin, registrar_auditoria, _datos_usuario, _obtener_ip


class AsistenciaViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    queryset = Asistencia.objects.all()
    serializer_class = AsistenciaSerializer
    permission_classes = [permissions.IsAuthenticated]
    auditoria_servicio = 'asistencia'
    auditoria_modelo = 'Asistencia'

    def get_queryset(self):
        user = self.request.user
        if user.rol == 'ESTUDIANTE':
            return self.queryset.filter(estudiante_id=user.id)
        elif user.rol == 'DOCENTE':
            horario_ids = HorarioModel.objects.filter(
                materia__docente_id=user.id
            ).values_list('id', flat=True)
            return self.queryset.filter(horario_id__in=horario_ids)
        return self.queryset

    @action(detail=False, methods=['post'])
    def registrar(self, request):
        serializer = RegistrarAsistenciaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        estudiante_id = serializer.validated_data['estudiante_id']
        horario_id = serializer.validated_data['horario_id']
        imagen_base64 = serializer.validated_data['imagen_base64']
        ubicacion = serializer.validated_data.get('ubicacion', '')
        horario = serializer.validated_data['horario_data']

        aws_service = AwsRekognitionService()
        try:
            image_bytes = aws_service.decode_base64_image(imagen_base64)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        resultado = aws_service.buscar_rostro(image_bytes)

        if not resultado or float(resultado['confidence']) < 85.0:
            return Response({
                'success': False,
                'message': 'No se pudo reconocer el rostro o confianza baja',
                'confidence': resultado['confidence'] if resultado else 0
            }, status=status.HTTP_400_BAD_REQUEST)

        if int(resultado['external_id']) != estudiante_id:
            return Response({
                'success': False,
                'message': 'El rostro no coincide con el estudiante registrado'
            }, status=status.HTTP_400_BAD_REQUEST)

        filename = f"asistencias/{datetime.now().strftime('%Y/%m/%d')}/{uuid.uuid4()}.jpg"
        imagen_url = aws_service.subir_imagen_s3(image_bytes, filename)

        with transaction.atomic():
            reconocimiento = Reconocimiento.objects.create(
                estudiante_id=estudiante_id,
                resultado=True,
                confianza=resultado['confidence'],
                ubicacion=ubicacion,
                imagen_url=imagen_url,
                registro_facial=RegistroFacial.objects.filter(
                    estudiante_id=estudiante_id
                ).first()
            )

            hora_actual = datetime.now().time()
            hora_inicio = datetime.strptime(horario['hora_inicio'], '%H:%M:%S').time()
            hora_limite_presente = (datetime.combine(datetime.today(), hora_inicio) +
                                   timedelta(minutes=horario['minutos_tolerancia'])).time()

            if hora_actual <= hora_limite_presente:
                estado = EstadoAsistencia.PRESENTE
            else:
                estado = EstadoAsistencia.TARDE

            asistencia = Asistencia.objects.create(
                estudiante_id=estudiante_id,
                horario_id=horario_id,
                estado=estado,
                confianza=resultado['confidence'],
                reconocimiento=reconocimiento
            )

        # ── Auditoría (nuevo) ──────────────────────────────────────────
        # Esta acción no pasa por perform_create (es un @action manual),
        # así que se audita explícitamente.
        usuario_id, usuario_nombre = _datos_usuario(request)
        registrar_auditoria(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion='CREATE',
            servicio='asistencia',
            modelo='Asistencia',
            registro_id=asistencia.id,
            descripcion=f"Registró asistencia (estado {estado}) mediante reconocimiento facial",
            datos_modificados={'estudiante_id': estudiante_id, 'horario_id': horario_id, 'estado': estado},
            ip_origen=_obtener_ip(request),
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
        estudiante_id = request.query_params.get('estudiante_id')
        if not estudiante_id:
            return Response({'error': 'Se requiere estudiante_id'}, status=status.HTTP_400_BAD_REQUEST)
        asistencias = self.get_queryset().filter(estudiante_id=estudiante_id)
        serializer = self.get_serializer(asistencias, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def por_materia(self, request):
        materia_id = request.query_params.get('materia_id')
        if not materia_id:
            return Response({'error': 'Se requiere materia_id'}, status=status.HTTP_400_BAD_REQUEST)
        horario_ids = HorarioModel.objects.filter(materia_id=materia_id).values_list('id', flat=True)
        asistencias = self.get_queryset().filter(horario_id__in=horario_ids)
        serializer = self.get_serializer(asistencias, many=True)
        return Response(serializer.data)


class JustificacionViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    queryset = Justificacion.objects.all()
    serializer_class = JustificacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    auditoria_servicio = 'asistencia'
    auditoria_modelo = 'Justificacion'

    def get_queryset(self):
        user = self.request.user
        if user.rol == 'ESTUDIANTE':
            return self.queryset.filter(estudiante_id=user.id)
        elif user.rol == 'DOCENTE':
            horario_ids = HorarioModel.objects.filter(
                materia__docente_id=user.id
            ).values_list('id', flat=True)
            asistencia_ids = Asistencia.objects.filter(
                horario_id__in=horario_ids
            ).values_list('id', flat=True)
            return self.queryset.filter(asistencia_id__in=asistencia_ids)
        return self.queryset

    def create(self, request, *args, **kwargs):
<<<<<<< HEAD
        # perform_create ya queda cubierto por AuditoriaMixin (registra CREATE
        # automáticamente), no se necesita ningún cambio adicional aquí.
=======
        if request.user.rol != 'ESTUDIANTE':
            return Response({'error': 'Solo los estudiantes pueden solicitar una justificación'},
                          status=status.HTTP_403_FORBIDDEN)

>>>>>>> moduloJustificacion
        data = request.data.copy()
        asistencia_id = data.get('asistencia')
        existente = None
        if asistencia_id:
            get_object_or_404(Asistencia, id=asistencia_id, estudiante_id=request.user.id)
            existente = Justificacion.objects.filter(asistencia_id=asistencia_id).first()

        if existente:
            if existente.estado != 'RECHAZADA':
                return Response(
                    {'error': 'Ya existe una justificación para esta falta que no fue rechazada'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Reenvío tras rechazo: se actualiza el mismo registro y vuelve a quedar PENDIENTE
            serializer = self.get_serializer(existente, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(
                estudiante_id=request.user.id,
                estado='PENDIENTE',
                docente_aprueba_id=None,
                fecha_respuesta=None,
                comentario_docente=''
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(estudiante_id=request.user.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def aprobar(self, request):
        if request.user.rol != 'DOCENTE':
            return Response({'error': 'Solo docentes pueden aprobar justificaciones'},
                          status=status.HTTP_403_FORBIDDEN)

        serializer = AprobarJustificacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        justificacion = get_object_or_404(Justificacion, id=serializer.validated_data['justificacion_id'])

        horario_ids = HorarioModel.objects.filter(
            materia__docente_id=request.user.id
        ).values_list('id', flat=True)

        if justificacion.asistencia.horario_id not in horario_ids:
            return Response({'error': 'No tienes permiso para aprobar esta justificación'},
                          status=status.HTTP_403_FORBIDDEN)

        comentario = serializer.validated_data.get('comentario', '')
        if serializer.validated_data['aprobar']:
            justificacion.aprobar(request.user.id, comentario)
            message = 'Justificación aprobada'
            accion_auditoria = 'aprobó'
        else:
            justificacion.rechazar(request.user.id, comentario)
            message = 'Justificación rechazada'
            accion_auditoria = 'rechazó'

        # ── Auditoría (nuevo) ──────────────────────────────────────────
        # `aprobar()`/`rechazar()` mutan el estado fuera de perform_update,
        # así que se audita explícitamente.
        usuario_id, usuario_nombre = _datos_usuario(request)
        registrar_auditoria(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion='UPDATE',
            servicio='asistencia',
            modelo='Justificacion',
            registro_id=justificacion.id,
            descripcion=f"{usuario_nombre} {accion_auditoria} la justificación #{justificacion.id}",
            datos_modificados={'estado': justificacion.estado, 'comentario': comentario},
            ip_origen=_obtener_ip(request),
        )

        return Response({
            'success': True,
            'message': message,
            'estado': justificacion.estado
        })


class ReconocimientoViewSet(viewsets.ReadOnlyModelViewSet):
    # Solo lectura: no requiere auditoría (no muta datos).
    queryset = Reconocimiento.objects.all()
    serializer_class = ReconocimientoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.rol == 'ESTUDIANTE':
            return self.queryset.filter(estudiante_id=user.id)
        return self.queryset


class RegistroFacialViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    queryset = RegistroFacial.objects.all()
    serializer_class = RegistroFacialSerializer
    permission_classes = [permissions.IsAuthenticated]
    auditoria_servicio = 'asistencia'
    auditoria_modelo = 'RegistroFacial'

    def get_queryset(self):
        user = self.request.user
        if user.rol == 'ESTUDIANTE':
            return self.queryset.filter(estudiante_id=user.id)
        return self.queryset

    @action(detail=False, methods=['post'])
    def registrar_rostro(self, request):
        if request.user.rol != 'ESTUDIANTE':
            return Response({'error': 'Solo estudiantes pueden registrar su rostro'},
                          status=status.HTTP_403_FORBIDDEN)

        imagen_base64 = request.data.get('imagen_base64')
        if not imagen_base64:
            return Response({'error': 'Se requiere imagen_base64'},
                          status=status.HTTP_400_BAD_REQUEST)

        if RegistroFacial.objects.filter(estudiante_id=request.user.id).exists():
            return Response({'error': 'Ya tienes un registro facial activo'},
                          status=status.HTTP_400_BAD_REQUEST)

        aws_service = AwsRekognitionService()
        try:
            image_bytes = aws_service.decode_base64_image(imagen_base64)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        resultado = aws_service.indexar_rostro(image_bytes, str(request.user.id))

        if not resultado:
            return Response({
                'success': False,
                'message': 'No se pudo indexar el rostro. Intenta con otra imagen.'
            }, status=status.HTTP_400_BAD_REQUEST)

        registro = RegistroFacial.objects.create(
            estudiante_id=request.user.id,
            face_id=resultado['face_id']
        )

        filename = f"referencias/{request.user.id}/{uuid.uuid4()}.jpg"
        imagen_url = aws_service.subir_imagen_s3(image_bytes, filename)
        if imagen_url:
            request.user.foto_referencia_url = imagen_url
            request.user.save()

        # ── Auditoría (nuevo) ──────────────────────────────────────────
        usuario_id, usuario_nombre = _datos_usuario(request)
        registrar_auditoria(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion='CREATE',
            servicio='asistencia',
            modelo='RegistroFacial',
            registro_id=registro.id,
            descripcion=f"{usuario_nombre} registró su rostro para reconocimiento facial",
            datos_modificados={'face_id': resultado['face_id']},
            ip_origen=_obtener_ip(request),
        )

        return Response({
            'success': True,
            'message': 'Rostro registrado exitosamente',
            'face_id': resultado['face_id'],
            'confidence': resultado['confidence']
        })

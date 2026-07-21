import io
import os
import threading
import uuid
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image
from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import update_session_auth_hash

from .models import Usuario, PasswordResetToken
from .serializers import (
    UsuarioSerializer, RegisterSerializer, ChangePasswordSerializer,
    SolicitarRestablecimientoSerializer, RestablecerPasswordSerializer,
)
from .permissions import IsAdminForMutation
from shared.audit import AuditoriaMixin, registrar_auditoria, _datos_usuario, _obtener_ip


class UsuarioViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdminForMutation]
    filterset_fields = ['rol']
    auditoria_servicio = 'usuario'
    auditoria_modelo = 'Usuario'

    def get_queryset(self):
        user = self.request.user
        if user.rol == 'ADMIN':
            return self.queryset
        return self.queryset.filter(id=user.id, is_active=True)

    def get_permissions(self):
        if self.action in ['register', 'solicitar_restablecimiento', 'restablecer_password']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    def perform_destroy(self, instance):
        usuario_id, usuario_nombre = _datos_usuario(self.request)
        instance.is_active = False
        instance.save()
        registrar_auditoria(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion='DELETE',
            servicio='usuario',
            modelo='Usuario',
            registro_id=instance.id,
            descripcion=f"{usuario_nombre} desactivó usuario {instance.email}",
            datos_modificados={'is_active': False},
            ip_origen=_obtener_ip(self.request),
        )

    ALLOWED_IMAGE_TYPES = {
        'image/jpeg': '.jpg', 'image/png': '.png',
        'image/webp': '.webp', 'image/gif': '.gif',
    }

    def _handle_foto_upload(self, request):
        if 'foto' not in request.FILES:
            return None
        foto_file = request.FILES['foto']

        content_type = foto_file.content_type or ''
        if content_type not in self.ALLOWED_IMAGE_TYPES:
            raise serializers.ValidationError(
                'Formato de imagen no soportado. Use JPG, PNG, WEBP o GIF.'
            )

        image = Image.open(foto_file)
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')

        filename = f'fotos/{uuid.uuid4()}.jpg'
        buf = io.BytesIO()
        image.save(buf, format='JPEG', quality=85)
        buf.seek(0)
        return default_storage.save(filename, ContentFile(buf.read()))

    def perform_update(self, serializer):
        foto_url = self._handle_foto_upload(self.request)
        if foto_url:
            serializer.save(foto_referencia_url=foto_url)
        else:
            serializer.save()
        self.auditar(serializer.instance, 'UPDATE')

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        foto_url = self._handle_foto_upload(request)
        usuario = serializer.save(foto_referencia_url=foto_url or serializer.validated_data.get('foto_referencia_url', ''))

        usuario_id, usuario_nombre = _datos_usuario(request)
        registrar_auditoria(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion='CREATE',
            servicio='usuario',
            modelo='Usuario',
            registro_id=usuario.id,
            descripcion=f"Registro nuevo usuario {usuario.email} (rol {usuario.rol})",
            datos_modificados={'email': usuario.email, 'rol': usuario.rol},
            ip_origen=_obtener_ip(request),
        )

        return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def perfil(self, request):
        usuario = request.user
        serializer = self.get_serializer(usuario, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        foto_url = self._handle_foto_upload(request)
        if foto_url:
            serializer.save(foto_referencia_url=foto_url)
        else:
            serializer.save()

        usuario_id, usuario_nombre = _datos_usuario(request)
        registrar_auditoria(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion='UPDATE',
            servicio='usuario',
            modelo='Usuario',
            registro_id=usuario.id,
            descripcion=f"{usuario_nombre} actualizó su perfil",
            datos_modificados={k: v for k, v in serializer.validated_data.items() if k != 'foto'},
            ip_origen=_obtener_ip(request),
        )

        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def cambiar_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = request.user
        if not usuario.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Contraseña actual incorrecta'}, status=status.HTTP_400_BAD_REQUEST)
        usuario.set_password(serializer.validated_data['new_password'])
        usuario.save()
        update_session_auth_hash(request, usuario)

        usuario_id, usuario_nombre = _datos_usuario(request)
        registrar_auditoria(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion='UPDATE',
            servicio='usuario',
            modelo='Usuario',
            registro_id=usuario.id,
            descripcion=f"{usuario_nombre} cambió su contraseña",
            ip_origen=_obtener_ip(request),
        )

        return Response({'message': 'Contraseña actualizada exitosamente'})

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def solicitar_restablecimiento(self, request):
        serializer = SolicitarRestablecimientoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        token = PasswordResetToken.generar_token()
        PasswordResetToken.objects.create(email=email, token=token)

        from .email_service import enviar_email_brevo

        reset_link = f"{settings.FRONTEND_URL}/recuperar-password?token={token}"

        def enviar_email():
            try:
                enviar_email_brevo(
                    subject='Restablece tu contraseña — SACARF',
                    message=f'Para restablecer tu contraseña, haz clic en este enlace (válido por 30 segundos):\n\n{reset_link}\n\n'
                            f'Si no solicitaste este cambio, ignora este mensaje.\n\n'
                            f'SACARF — Sistema de Asistencia con Reconocimiento Facial',
                    recipient=email,
                )
                print(f'EMAIL ENVIADO a {email} via Brevo')
            except Exception as e:
                print(f'ERROR AL ENVIAR EMAIL: {e}')

        threading.Thread(target=enviar_email, daemon=True).start()

        return Response({
            'mensaje': 'Se ha enviado un código de verificación a tu correo'
        })

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def restablecer_password(self, request):
        serializer = RestablecerPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            reset_token = PasswordResetToken.objects.get(
                token=serializer.validated_data['token'],
                is_used=False,
            )
        except PasswordResetToken.DoesNotExist:
            return Response({'error': 'Token inválido o expirado'}, status=status.HTTP_400_BAD_REQUEST)
        if not reset_token.is_valid():
            return Response({'error': 'El token ha expirado'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            usuario = Usuario.objects.get(email=reset_token.email)
        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        usuario.set_password(serializer.validated_data['password'])
        usuario.save()
        reset_token.is_used = True
        reset_token.save()
        return Response({'mensaje': 'Contraseña restablecida exitosamente'})

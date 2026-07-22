from datetime import timedelta
from unittest.mock import patch, Mock
import json

from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Usuario, PasswordResetToken
from .serializers import (
    validar_password_segura, RegisterSerializer,
    SolicitarRestablecimientoSerializer, RestablecerPasswordSerializer,
    ChangePasswordSerializer, UsuarioSerializer,
)
from .authentication import EmailOrUsernameModelBackend, CustomJWTAuthentication
from .permissions import IsAdminForMutation
from .email_service import enviar_email_brevo
from .login_view import login_view

User = get_user_model()


class UsuarioModelTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            email='test@example.com',
            password='Abcd1234!',
            cedula='1234567890',
            first_name='Test',
            rol='ESTUDIANTE',
        )

    def test_esta_bloqueado_futuro(self):
        """Valida que esta_bloqueado() retorne True si bloqueado_hasta está en el futuro"""
        self.usuario.bloqueado_hasta = timezone.now() + timedelta(hours=1)
        self.usuario.intentos_fallidos = 0
        self.usuario.save()
        self.assertTrue(self.usuario.esta_bloqueado())

    def test_esta_bloqueado_pasado(self):
        """Valida que esta_bloqueado() retorne False si bloqueado_hasta ya expiró"""
        self.usuario.bloqueado_hasta = timezone.now() - timedelta(hours=1)
        self.usuario.intentos_fallidos = 0
        self.usuario.save()
        self.assertFalse(self.usuario.esta_bloqueado())

    def test_esta_bloqueado_auto_por_intentos(self):
        """Valida que 5+ intentos fallidos automaticamente bloqueen la cuenta (seteen bloqueado_hasta)"""
        self.usuario.bloqueado_hasta = None
        self.usuario.intentos_fallidos = 5
        self.usuario.save()
        self.assertTrue(self.usuario.esta_bloqueado())
        self.usuario.refresh_from_db()
        self.assertIsNotNone(self.usuario.bloqueado_hasta)

    def test_esta_bloqueado_sin_bloqueo(self):
        """Valida que esta_bloqueado() retorne False sin bloqueo ni intentos"""
        self.usuario.bloqueado_hasta = None
        self.usuario.intentos_fallidos = 0
        self.usuario.save()
        self.assertFalse(self.usuario.esta_bloqueado())

    def test_create_user_sin_email(self):
        """Valida que crear usuario sin email lance ValueError"""
        with self.assertRaises(ValueError) as ctx:
            User.objects.create_user(email='', password='Abcd1234!')
        self.assertIn('correo es obligatorio', str(ctx.exception))

    def test_create_user_normaliza_email(self):
        """Valida que el email se normalice a minúsculas (dominio)"""
        user = User.objects.create_user(
            email='Test@Example.Com', password='Abcd1234!', cedula='9999'
        )
        self.assertEqual(user.email, 'Test@example.com')

    def test_create_superuser_sin_is_staff(self):
        """Valida que crear superuser sin is_staff=True lance ValueError"""
        with self.assertRaises(ValueError) as ctx:
            User.objects.create_superuser(
                email='admin@test.com', password='Abcd1234!',
                cedula='admin1', is_staff=False,
            )
        self.assertIn('is_staff=True', str(ctx.exception))

    def test_create_superuser_sin_is_superuser(self):
        """Valida que crear superuser sin is_superuser=True lance ValueError"""
        with self.assertRaises(ValueError) as ctx:
            User.objects.create_superuser(
                email='admin2@test.com', password='Abcd1234!',
                cedula='admin2', is_superuser=False,
            )
        self.assertIn('is_superuser=True', str(ctx.exception))

    def test_create_superuser_correcto(self):
        """Valida que crear superuser correctamente setee is_staff, is_superuser e is_active"""
        user = User.objects.create_superuser(
            email='super@test.com', password='Abcd1234!', cedula='super01',
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_str_representation(self):
        """Valida que str(Usuario) incluya email y rol legible"""
        self.assertIn('test@example.com', str(self.usuario))
        self.assertIn('Estudiante', str(self.usuario))

    def test_email_unique(self):
        """Valida que el campo email tenga constraint UNIQUE"""
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='test@example.com', password='Other1234!', cedula='other01',
            )

    def test_cedula_unique(self):
        """Valida que el campo cedula tenga constraint UNIQUE"""
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='other@test.com', password='Other1234!', cedula='1234567890',
            )


class PasswordResetTokenModelTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            email='test@example.com', password='Abcd1234!', cedula='1234567890',
        )

    def test_generar_token_es_url_safe(self):
        """Valida que generar_token() produzca un string url-safe de 43 caracteres"""
        token = PasswordResetToken.generar_token()
        self.assertEqual(len(token), 43)
        self.assertNotIn('/', token)
        self.assertNotIn('+', token)

    def test_is_valid_no_usado_y_vigente(self):
        """Valida que is_valid() retorne True para token no usado y vigente"""
        token_obj = PasswordResetToken.objects.create(
            email='test@example.com',
            token=PasswordResetToken.generar_token(),
        )
        self.assertTrue(token_obj.is_valid())

    def test_is_valid_token_usado(self):
        """Valida que is_valid() retorne False para token ya usado"""
        token_obj = PasswordResetToken.objects.create(
            email='test@example.com',
            token=PasswordResetToken.generar_token(),
            is_used=True,
        )
        self.assertFalse(token_obj.is_valid())

    @override_settings(PASSWORD_RESET_TIMEOUT=1)
    def test_is_valid_token_expirado(self):
        """Valida que is_valid() retorne False para token expirado (mayor a PASSWORD_RESET_TIMEOUT)"""
        token_obj = PasswordResetToken.objects.create(
            email='test@example.com',
            token=PasswordResetToken.generar_token(),
        )
        token_obj.created_at = timezone.now() - timedelta(seconds=2)
        token_obj.save()
        self.assertFalse(token_obj.is_valid())

    def test_str_representation(self):
        """Valida que str(PasswordResetToken) incluya el email"""
        token_obj = PasswordResetToken.objects.create(
            email='test@example.com',
            token='sometokenvalue',
        )
        self.assertIn('test@example.com', str(token_obj))


class ValidarPasswordSeguraTest(TestCase):
    def test_sin_mayuscula(self):
        """Valida que password sin mayúscula lance excepción"""
        with self.assertRaises(Exception):
            validar_password_segura('abc123!.')

    def test_sin_numero(self):
        """Valida que password sin número lance excepción"""
        with self.assertRaises(Exception):
            validar_password_segura('Abcdefg!.')

    def test_sin_simbolo(self):
        """Valida que password sin símbolo especial lance excepción"""
        with self.assertRaises(Exception):
            validar_password_segura('Abcdefg1')

    def test_password_valida(self):
        """Valida que password con mayúscula, número y símbolo sea aceptada"""
        try:
            validar_password_segura('Abcd1234!.')
        except Exception:
            self.fail('validar_password_segura lanzó excepción para password válida')


class RegisterSerializerTest(TestCase):
    def setUp(self):
        self.valid_data = {
            'email': 'nuevo@test.com',
            'password': 'Abcd1234!.',
            'first_name': 'Nuevo',
            'last_name': 'Usuario',
            'cedula': '0987654321',
            'telefono': '0999999999',
            'rol': 'ESTUDIANTE',
        }

    def test_create_crea_usuario_con_hash(self):
        """Valida que RegisterSerializer cree usuario con password hasheado"""
        serializer = RegisterSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.email, 'nuevo@test.com')
        self.assertNotEqual(user.password, 'Abcd1234!.')
        self.assertTrue(user.check_password('Abcd1234!.'))

    def test_validate_password_debil(self):
        """Valida que password débil (<8 chars) sea rechazada"""
        data = self.valid_data.copy()
        data['password'] = '1234'
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_validate_password_sin_mayuscula(self):
        """Valida que password sin mayúscula sea rechazada"""
        data = self.valid_data.copy()
        data['password'] = 'abc1234!.'
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_campos_requeridos(self):
        """Valida que email, password y cedula sean campos obligatorios"""
        serializer = RegisterSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertIn('password', serializer.errors)
        self.assertIn('cedula', serializer.errors)


class ChangePasswordSerializerTest(TestCase):
    def test_new_password_debil(self):
        """Valida que new_password débil (<8 chars) sea rechazada"""
        serializer = ChangePasswordSerializer(data={
            'old_password': 'Abcd1234!.',
            'new_password': '123',
        })
        self.assertFalse(serializer.is_valid())

    def test_new_password_sin_mayuscula(self):
        """Valida que new_password sin mayúscula sea rechazada"""
        serializer = ChangePasswordSerializer(data={
            'old_password': 'Abcd1234!.',
            'new_password': 'abcdef1!.',
        })
        self.assertFalse(serializer.is_valid())

    def test_new_password_valida(self):
        """Valida que new_password que cumple requisitos sea aceptada"""
        serializer = ChangePasswordSerializer(data={
            'old_password': 'Abcd1234!.',
            'new_password': 'NuevaPass123!.',
        })
        self.assertTrue(serializer.is_valid())


class SolicitarRestablecimientoSerializerTest(TestCase):
    def setUp(self):
        User.objects.create_user(
            email='existente@test.com', password='Abcd1234!', cedula='1111111111',
        )

    def test_email_existente(self):
        """Valida que email registrado sea aceptado (con normalización)"""
        serializer = SolicitarRestablecimientoSerializer(data={'email': '  EXISTENTE@test.com  '})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['email'], 'existente@test.com')

    def test_email_no_existente(self):
        """Valida que email no registrado sea rechazado"""
        serializer = SolicitarRestablecimientoSerializer(data={'email': 'noexiste@test.com'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


class RestablecerPasswordSerializerTest(TestCase):
    def test_passwords_no_coinciden(self):
        """Valida que password y confirm_password distintos sea rechazado"""
        serializer = RestablecerPasswordSerializer(data={
            'token': 'abc', 'password': 'Abcd1234!.', 'confirm_password': 'otra12345@',
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('confirm_password', serializer.errors)

    def test_passwords_coinciden(self):
        """Valida que password y confirm_password iguales sea aceptado"""
        serializer = RestablecerPasswordSerializer(data={
            'token': 'abc', 'password': 'Abcd1234!.', 'confirm_password': 'Abcd1234!.',
        })
        self.assertTrue(serializer.is_valid())

    def test_token_requerido(self):
        """Valida que token sea campo obligatorio"""
        serializer = RestablecerPasswordSerializer(data={
            'password': 'Abcd1234!.', 'confirm_password': 'Abcd1234!.',
        })
        self.assertFalse(serializer.is_valid())

    def test_password_debil(self):
        """Valida que password débil sea rechazada incluso si coinciden"""
        serializer = RestablecerPasswordSerializer(data={
            'token': 'abc', 'password': '123', 'confirm_password': '123',
        })
        self.assertFalse(serializer.is_valid())


class UsuarioSerializerTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            email='test@serializer.com', password='Abcd1234!',
            cedula='ser001', first_name='Test', rol='DOCENTE',
        )

    def test_serializa_campos(self):
        """Valida que UsuarioSerializer serialice email, rol, first_name e id"""
        serializer = UsuarioSerializer(self.usuario)
        self.assertEqual(serializer.data['email'], 'test@serializer.com')
        self.assertEqual(serializer.data['rol'], 'DOCENTE')
        self.assertEqual(serializer.data['first_name'], 'Test')
        self.assertIn('id', serializer.data)

    def test_foto_url_none(self):
        """Valida que foto_referencia_url sea None por defecto"""
        serializer = UsuarioSerializer(self.usuario)
        self.assertIsNone(serializer.data['foto_referencia_url'])


class EmailOrUsernameModelBackendTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='auth@test.com', password='Abcd1234!', cedula='2222222222',
        )
        self.backend = EmailOrUsernameModelBackend()

    def test_authenticate_email_correcto(self):
        """Valida que autenticar con email y password correctos devuelva el usuario"""
        result = self.backend.authenticate(request=None, username='auth@test.com', password='Abcd1234!')
        self.assertEqual(result, self.user)

    def test_authenticate_email_incorrecto(self):
        """Valida que autenticar con email inexistente devuelva None"""
        result = self.backend.authenticate(request=None, username='noexiste@test.com', password='Abcd1234!')
        self.assertIsNone(result)

    def test_authenticate_password_incorrecto(self):
        """Valida que autenticar con password incorrecto devuelva None"""
        result = self.backend.authenticate(request=None, username='auth@test.com', password='wrong')
        self.assertIsNone(result)

    def test_authenticate_sin_username(self):
        """Valida que authenticate() sin username devuelva None"""
        result = self.backend.authenticate(request=None, password='Abcd1234!')
        self.assertIsNone(result)

    def test_authenticate_usuario_inactivo(self):
        """Valida que usuario inactivo (is_active=False) no pueda autenticarse"""
        self.user.is_active = False
        self.user.save()
        result = self.backend.authenticate(request=None, username='auth@test.com', password='Abcd1234!')
        self.assertIsNone(result)


class CustomJWTAuthenticationTest(TestCase):
    def test_authenticate_token_invalido_retorna_none(self):
        """Valida que un token JWT inválido no autentique"""
        from rest_framework.request import Request
        from django.http import HttpRequest
        http_req = HttpRequest()
        http_req.META['HTTP_AUTHORIZATION'] = 'Bearer invalidtoken'
        drf_request = Request(http_req)
        auth = CustomJWTAuthentication()
        result = auth.authenticate(drf_request)
        self.assertIsNone(result)

    def test_authenticate_sin_header(self):
        """Valida que request sin cabecera Authorization no autentique"""
        from rest_framework.request import Request
        from django.http import HttpRequest
        http_req = HttpRequest()
        drf_request = Request(http_req)
        auth = CustomJWTAuthentication()
        result = auth.authenticate(drf_request)
        self.assertIsNone(result)


class IsAdminForMutationTest(TestCase):
    def setUp(self):
        self.permission = IsAdminForMutation()
        self.admin_user = User.objects.create_user(
            email='admin@test.com', password='Admin1234!',
            cedula='adm01', rol='ADMIN',
        )
        self.estudiante_user = User.objects.create_user(
            email='est@test.com', password='Est1234!',
            cedula='est01', rol='ESTUDIANTE',
        )

    def _make_request(self, user, action='list'):
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request
        from collections import namedtuple
        factory = APIRequestFactory()
        http_request = factory.get('/')
        http_request.user = user
        drf_request = Request(http_request)
        drf_request._user = user
        view = namedtuple('View', ['action'])(action)
        return drf_request, view

    def test_admin_puede_crear(self):
        """Valida que ADMIN tenga permiso para crear"""
        req, view = self._make_request(self.admin_user, 'create')
        self.assertTrue(self.permission.has_permission(req, view))

    def test_admin_puede_actualizar(self):
        """Valida que ADMIN tenga permiso para actualizar"""
        req, view = self._make_request(self.admin_user, 'update')
        self.assertTrue(self.permission.has_permission(req, view))

    def test_admin_puede_eliminar(self):
        """Valida que ADMIN tenga permiso para eliminar"""
        req, view = self._make_request(self.admin_user, 'destroy')
        self.assertTrue(self.permission.has_permission(req, view))

    def test_estudiante_no_puede_crear(self):
        """Valida que ESTUDIANTE no tenga permiso para crear"""
        req, view = self._make_request(self.estudiante_user, 'create')
        self.assertFalse(self.permission.has_permission(req, view))

    def test_lectura_autenticado_ok(self):
        """Valida que cualquier autenticado tenga permiso de lectura"""
        req, view = self._make_request(self.estudiante_user, 'list')
        self.assertTrue(self.permission.has_permission(req, view))

    def test_sin_autenticacion_falla(self):
        """Valida que request sin autenticación no tenga permiso de lectura"""
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request
        from collections import namedtuple
        factory = APIRequestFactory()
        http_request = factory.get('/')
        drf_request = Request(http_request)
        view = namedtuple('View', ['action'])('list')
        self.assertFalse(self.permission.has_permission(drf_request, view))


# =============================================================================
# VIEW / API TESTS
# =============================================================================

class UsuarioAPIBase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@test.com', password='Admin1234!',
            cedula='0000000001', rol='ADMIN',
        )
        self.estudiante = User.objects.create_user(
            email='estudiante@test.com', password='Est1234!',
            cedula='0000000002', rol='ESTUDIANTE',
            first_name='Juan', last_name='Perez',
        )
        self.admin_token = str(RefreshToken.for_user(self.admin).access_token)
        self.estudiante_token = str(RefreshToken.for_user(self.estudiante).access_token)
        self.admin_client = APIClient()
        self.estudiante_client = APIClient()
        self.admin_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        self.estudiante_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.estudiante_token}')
        self.base_url = '/api/usuario/'


class UsuarioViewSetListTest(UsuarioAPIBase):
    def test_listar_como_admin(self):
        """Valida que ADMIN pueda listar todos los usuarios (200 OK)"""
        response = self.admin_client.get(f'{self.base_url}usuarios/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_listar_como_estudiante_solo_su_registro(self):
        """Valida que ESTUDIANTE solo vea su propio registro al listar"""
        response = self.estudiante_client.get(f'{self.base_url}usuarios/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', [response.data])
        ids = [u['id'] for u in results]
        self.assertIn(self.estudiante.id, ids)
        self.assertNotIn(self.admin.id, ids)

    def test_listar_sin_auth(self):
        """Valida que listar sin autenticación devuelva 401"""
        response = self.client.get(f'{self.base_url}usuarios/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filtrar_por_rol_admin(self):
        """Valida que el filtro por rol funcione correctamente"""
        User.objects.create_user(
            email='doc@test.com', password='Doc1234!',
            cedula='0000000003', rol='DOCENTE',
        )
        response = self.admin_client.get(f'{self.base_url}usuarios/?rol=DOCENTE')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', [response.data])
        for u in results:
            self.assertEqual(u['rol'], 'DOCENTE')


class UsuarioViewSetCRUDTest(UsuarioAPIBase):
    def test_retrieve_usuario_admin(self):
        """Valida que ADMIN pueda obtener detalle de cualquier usuario"""
        response = self.admin_client.get(f'{self.base_url}usuarios/{self.estudiante.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'estudiante@test.com')

    def test_create_usuario_admin(self):
        """Valida que ADMIN pueda crear un nuevo usuario (201)"""
        response = self.admin_client.post(f'{self.base_url}usuarios/', {
            'email': 'nuevo@test.com', 'password': 'Abcd1234!.',
            'first_name': 'Nuevo', 'cedula': 'new001', 'rol': 'ESTUDIANTE',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_usuario_estudiante_no_puede(self):
        """Valida que ESTUDIANTE no pueda crear usuarios (403)"""
        response = self.estudiante_client.post(f'{self.base_url}usuarios/', {
            'email': 'nuevo2@test.com', 'password': 'Abcd1234!.',
            'first_name': 'Nuevo', 'cedula': 'new002', 'rol': 'ESTUDIANTE',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_usuario_admin(self):
        """Valida que ADMIN pueda actualizar datos de un usuario"""
        response = self.admin_client.patch(
            f'{self.base_url}usuarios/{self.estudiante.id}/',
            {'first_name': 'Juanito'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Juanito')

    def test_destroy_usuario_admin_soft_delete(self):
        """Valida que ADMIN pueda eliminar (soft delete: is_active=False) un usuario"""
        response = self.admin_client.delete(f'{self.base_url}usuarios/{self.estudiante.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.estudiante.refresh_from_db()
        self.assertFalse(self.estudiante.is_active)


class UsuarioViewSetActionsTest(UsuarioAPIBase):
    def test_me_sin_auth(self):
        """Valida que GET /me/ sin auth devuelva 401"""
        response = self.client.get(f'{self.base_url}usuarios/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_autenticado(self):
        """Valida que GET /me/ devuelva los datos del usuario autenticado"""
        response = self.estudiante_client.get(f'{self.base_url}usuarios/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'estudiante@test.com')
        self.assertEqual(response.data['first_name'], 'Juan')

    def test_register_datos_validos(self):
        """Valida que POST /register/ cree un nuevo usuario (201)"""
        response = self.client.post(f'{self.base_url}usuarios/register/', {
            'email': 'nuevo@test.com', 'password': 'Abcd1234!.',
            'first_name': 'Nuevo', 'last_name': 'User',
            'cedula': '3333333333', 'rol': 'ESTUDIANTE',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'nuevo@test.com')
        self.assertIn('id', response.data)

    def test_register_email_duplicado(self):
        """Valida que POST /register/ con email existente devuelva 400"""
        response = self.client.post(f'{self.base_url}usuarios/register/', {
            'email': 'estudiante@test.com', 'password': 'Abcd1234!.',
            'first_name': 'Dup', 'last_name': 'User',
            'cedula': '4444444444', 'rol': 'ESTUDIANTE',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_debil(self):
        """Valida que POST /register/ con password débil devuelva 400"""
        response = self.client.post(f'{self.base_url}usuarios/register/', {
            'email': 'otro@test.com', 'password': '123',
            'first_name': 'Otro', 'cedula': '5555555555', 'rol': 'ESTUDIANTE',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_perfil_get(self):
        """Valida que GET /perfil/ devuelva los datos del usuario autenticado"""
        response = self.estudiante_client.get(f'{self.base_url}usuarios/perfil/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'estudiante@test.com')

    def test_perfil_actualizar_datos(self):
        """Valida que PATCH /perfil/ actualice los datos del usuario autenticado"""
        response = self.estudiante_client.patch(
            f'{self.base_url}usuarios/perfil/',
            {'first_name': 'Juanito'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Juanito')

    def test_perfil_sin_auth(self):
        """Valida que PATCH /perfil/ sin auth devuelva 401"""
        response = self.client.patch(f'{self.base_url}usuarios/perfil/',
            {'first_name': 'X'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cambiar_password_incorrecta(self):
        """Valida que POST /cambiar-password/ con old_password incorrecto devuelva 400"""
        response = self.estudiante_client.post(
            f'{self.base_url}usuarios/cambiar-password/',
            {'old_password': 'wrong', 'new_password': 'Nueva1234!.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_cambiar_password_correcto(self):
        """Valida que POST /cambiar-password/ con datos correctos cambie el password"""
        response = self.estudiante_client.post(
            f'{self.base_url}usuarios/cambiar-password/',
            {'old_password': 'Est1234!', 'new_password': 'Nueva1234!.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', str(response.data))
        self.estudiante.refresh_from_db()
        self.assertTrue(self.estudiante.check_password('Nueva1234!.'))

    def test_cambiar_password_sin_auth(self):
        """Valida que POST /cambiar-password/ sin auth devuelva 401"""
        response = self.client.post(f'{self.base_url}usuarios/cambiar-password/',
            {'old_password': 'x', 'new_password': 'Nueva1234!.'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_solicitar_restablecimiento_email_existe(self):
        """Valida que solicitar restablecimiento con email existente cree un token (200)"""
        response = self.client.post(
            f'{self.base_url}usuarios/solicitar-restablecimiento/',
            {'email': 'estudiante@test.com'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(PasswordResetToken.objects.count(), 1)

    def test_solicitar_restablecimiento_email_no_existe(self):
        """Valida que solicitar restablecimiento con email inexistente devuelva 400"""
        response = self.client.post(
            f'{self.base_url}usuarios/solicitar-restablecimiento/',
            {'email': 'noexiste@test.com'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_restablecer_password_token_valido(self):
        """Valida que restablecer password con token válido cambie el password (200)"""
        PasswordResetToken.objects.create(
            email='estudiante@test.com', token='valid-token-123',
        )
        response = self.client.post(
            f'{self.base_url}usuarios/restablecer-password/',
            {'token': 'valid-token-123', 'password': 'Nueva1234!.',
             'confirm_password': 'Nueva1234!.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('mensaje', response.data)
        self.estudiante.refresh_from_db()
        self.assertTrue(self.estudiante.check_password('Nueva1234!.'))

    def test_restablecer_password_token_invalido(self):
        """Valida que restablecer password con token inválido devuelva 400"""
        response = self.client.post(
            f'{self.base_url}usuarios/restablecer-password/',
            {'token': 'token-invalido', 'password': 'Nueva1234!.',
             'confirm_password': 'Nueva1234!.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_restablecer_password_token_expirado(self):
        """Valida que restablecer password con token expirado devuelva 400"""
        token = PasswordResetToken.objects.create(
            email='estudiante@test.com', token='expirado-token',
        )
        token.created_at = timezone.now() - timedelta(hours=2)
        token.save()
        response = self.client.post(
            f'{self.base_url}usuarios/restablecer-password/',
            {'token': 'expirado-token', 'password': 'Nueva1234!.',
             'confirm_password': 'Nueva1234!.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_restablecer_password_passwords_no_coinciden(self):
        """Valida que restablecer password con passwords distintos devuelva 400"""
        PasswordResetToken.objects.create(
            email='estudiante@test.com', token='token-abc',
        )
        response = self.client.post(
            f'{self.base_url}usuarios/restablecer-password/',
            {'token': 'token-abc', 'password': 'Nueva1234!.',
             'confirm_password': 'Otra1234!.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='login@test.com', password='Login1234!',
            cedula='5555555555', rol='ESTUDIANTE',
        )
        self.url = '/api/usuario/token/'

    def test_login_exitoso(self):
        """Valida que login con credenciales correctas devuelva access + refresh tokens"""
        response = self.client.post(self.url, {
            'email': 'login@test.com', 'password': 'Login1234!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_credenciales_invalidas(self):
        """Valida que login con password incorrecto devuelva 401 con intentos_restantes"""
        response = self.client.post(self.url, {
            'email': 'login@test.com', 'password': 'wrong',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('intentos_restantes', response.data)

    def test_login_incrementa_intentos(self):
        """Valida que cada intento fallido incremente intentos_fallidos"""
        for _ in range(3):
            self.client.post(self.url, {
                'email': 'login@test.com', 'password': 'wrong',
            }, format='json')
        self.user.refresh_from_db()
        self.assertEqual(self.user.intentos_fallidos, 3)

    def test_login_bloqueo_tras_5_intentos(self):
        """Valida que tras 5 intentos fallidos la cuenta se bloquee"""
        for _ in range(5):
            self.client.post(self.url, {
                'email': 'login@test.com', 'password': 'wrong',
            }, format='json')
        response = self.client.post(self.url, {
            'email': 'login@test.com', 'password': 'Login1234!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(response.data.get('bloqueado', False))

    def test_login_exitoso_resetea_intentos(self):
        """Valida que un login exitoso reseteé intentos_fallidos y bloqueado_hasta"""
        for _ in range(3):
            self.client.post(self.url, {
                'email': 'login@test.com', 'password': 'wrong',
            }, format='json')
        response = self.client.post(self.url, {
            'email': 'login@test.com', 'password': 'Login1234!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.intentos_fallidos, 0)
        self.assertIsNone(self.user.bloqueado_hasta)

    def test_login_cuenta_bloqueada(self):
        """Valida que intentar login con cuenta bloqueada devuelva 401 con bloqueado=True"""
        self.user.intentos_fallidos = 5
        self.user.bloqueado_hasta = timezone.now() + timedelta(minutes=30)
        self.user.save()
        response = self.client.post(self.url, {
            'email': 'login@test.com', 'password': 'Login1234!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(response.data.get('bloqueado', False))

    def test_login_email_no_existe(self):
        """Valida que login con email no registrado devuelva 401"""
        response = self.client.post(self.url, {
            'email': 'noexiste@test.com', 'password': 'Login1234!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenRefreshViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='refresh@test.com', password='Abcd1234!',
            cedula='6666666666', rol='ADMIN',
        )

    def test_refresh_token_valido(self):
        """Valida que refresh de token válido devuelva un nuevo access token"""
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post('/api/usuario/token/refresh/', {
            'refresh': str(refresh),
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_token_invalido(self):
        """Valida que refresh de token inválido devuelva 401"""
        response = self.client.post('/api/usuario/token/refresh/', {
            'refresh': 'token-invalido',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EmailServiceTest(TestCase):
    @patch('apps.usuario.email_service.os.getenv')
    def test_enviar_email_sin_api_key(self, mock_getenv):
        """Valida que enviar_email_brevo lance excepción si falta BREVO_API_KEY"""
        mock_getenv.return_value = ''
        with self.assertRaises(Exception) as ctx:
            enviar_email_brevo('Subj', 'Msg', 'test@test.com')
        self.assertIn('BREVO_API_KEY', str(ctx.exception))

    @patch('apps.usuario.email_service.os.getenv')
    @patch('apps.usuario.email_service.urllib.request.urlopen')
    def test_enviar_email_exitoso(self, mock_urlopen, mock_getenv):
        """Valida que enviar_email_brevo funcione correctamente con API key válida"""
        def getenv_side_effect(key, default=None):
            env = {
                'BREVO_API_KEY': 'fake-api-key',
                'BREVO_FROM_EMAIL': 'from@test.com',
                'BREVO_FROM_NAME': 'SACARF',
                'DEFAULT_FROM_EMAIL': 'fallback@test.com',
            }
            return env.get(key, default or '')
        mock_getenv.side_effect = getenv_side_effect
        mock_resp = Mock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'OK'
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        try:
            enviar_email_brevo('Subject', 'Message body', 'to@test.com')
        except Exception:
            self.fail('enviar_email_brevo lanzó excepción')

    @patch('apps.usuario.email_service.os.getenv')
    @patch('apps.usuario.email_service.urllib.request.urlopen')
    def test_enviar_email_http_error(self, mock_urlopen, mock_getenv):
        """Valida que enviar_email_brevo lance excepción ante error HTTP de Brevo"""
        import urllib.error
        mock_getenv.return_value = 'fake-key'
        mock_urlopen.side_effect = urllib.error.HTTPError(
            'https://api.brevo.com/v3/smtp/email',
            400, 'Bad Request', {}, None,
        )
        with self.assertRaises(Exception):
            enviar_email_brevo('Subj', 'Msg', 'test@test.com')

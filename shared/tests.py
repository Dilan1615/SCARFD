import json
from datetime import datetime, date, timedelta
from unittest.mock import patch, Mock
import requests

from django.test import TestCase
from django.test.utils import override_settings
from django.http import HttpRequest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

from shared.auth import EmailOrUsernameModelBackend, CustomJWTAuthentication
from shared.permissions import IsAdminForMutation
from shared.audit import _a_serializable, _obtener_ip, _datos_usuario, registrar_auditoria, AuditoriaMixin
from shared.clients import UsuarioServiceClient, AcademicoServiceClient, AsistenciaServiceClient

User = get_user_model()


class EmailOrUsernameModelBackendTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='auth.shared@test.com', password='AuthShared1234!',
            cedula='7777777777', rol='ADMIN',
        )
        self.backend = EmailOrUsernameModelBackend()

    def test_authenticate_email_correcto(self):
        """Valida que autenticar con email y password correctos devuelva el usuario"""
        result = self.backend.authenticate(
            request=None, username='auth.shared@test.com', password='AuthShared1234!'
        )
        self.assertEqual(result, self.user)

    def test_authenticate_email_incorrecto(self):
        """Valida que autenticar con email inexistente devuelva None"""
        result = self.backend.authenticate(
            request=None, username='noexiste@test.com', password='AuthShared1234!'
        )
        self.assertIsNone(result)

    def test_authenticate_password_incorrecto(self):
        """Valida que autenticar con password incorrecto devuelva None"""
        result = self.backend.authenticate(
            request=None, username='auth.shared@test.com', password='wrongpassword'
        )
        self.assertIsNone(result)

    def test_authenticate_sin_username(self):
        """Valida que llamar a authenticate() sin username devuelva None"""
        result = self.backend.authenticate(request=None, password='AuthShared1234!')
        self.assertIsNone(result)

    def test_authenticate_usuario_inactivo(self):
        """Valida que un usuario con is_active=False no pueda autenticarse"""
        self.user.is_active = False
        self.user.save()
        result = self.backend.authenticate(
            request=None, username='auth.shared@test.com', password='AuthShared1234!'
        )
        self.assertIsNone(result)


class CustomJWTAuthenticationTest(TestCase):
    def test_authenticate_token_invalido_retorna_none(self):
        """Valida que un token JWT inválido no autentique (retorna None)"""
        http_req = HttpRequest()
        http_req.META['HTTP_AUTHORIZATION'] = 'Bearer invalidtoken1234'
        drf_request = Request(http_req)
        auth = CustomJWTAuthentication()
        result = auth.authenticate(drf_request)
        self.assertIsNone(result)

    def test_authenticate_sin_header(self):
        """Valida que un request sin cabecera Authorization no autentique (retorna None)"""
        http_req = HttpRequest()
        drf_request = Request(http_req)
        auth = CustomJWTAuthentication()
        result = auth.authenticate(drf_request)
        self.assertIsNone(result)


class IsAdminForMutationTest(TestCase):
    def setUp(self):
        self.permission = IsAdminForMutation()
        self.admin_user = User.objects.create_user(
            email='admin.test@test.com', password='AdminTest1234!',
            cedula='admin001', rol='ADMIN',
        )
        self.estudiante_user = User.objects.create_user(
            email='est.test@test.com', password='EstTest1234!',
            cedula='est001', rol='ESTUDIANTE',
        )

    def _make_request(self, user, action='list'):
        from collections import namedtuple
        factory = APIRequestFactory()
        http_request = factory.get('/')
        http_request.user = user
        drf_request = Request(http_request)
        drf_request._user = user
        view = namedtuple('View', ['action'])(action)
        return drf_request, view

    def test_admin_puede_crear(self):
        """Valida que un usuario ADMIN tenga permiso para crear (CREATE)"""
        req, view = self._make_request(self.admin_user, 'create')
        self.assertTrue(self.permission.has_permission(req, view))

    def test_admin_puede_actualizar(self):
        """Valida que un usuario ADMIN tenga permiso para actualizar (UPDATE)"""
        req, view = self._make_request(self.admin_user, 'update')
        self.assertTrue(self.permission.has_permission(req, view))

    def test_admin_puede_eliminar(self):
        """Valida que un usuario ADMIN tenga permiso para eliminar (DELETE)"""
        req, view = self._make_request(self.admin_user, 'destroy')
        self.assertTrue(self.permission.has_permission(req, view))

    def test_estudiante_no_puede_crear(self):
        """Valida que un ESTUDIANTE NO tenga permiso para crear"""
        req, view = self._make_request(self.estudiante_user, 'create')
        self.assertFalse(self.permission.has_permission(req, view))

    def test_estudiante_no_puede_actualizar(self):
        """Valida que un ESTUDIANTE NO tenga permiso para actualizar"""
        req, view = self._make_request(self.estudiante_user, 'update')
        self.assertFalse(self.permission.has_permission(req, view))

    def test_estudiante_no_puede_eliminar(self):
        """Valida que un ESTUDIANTE NO tenga permiso para eliminar"""
        req, view = self._make_request(self.estudiante_user, 'destroy')
        self.assertFalse(self.permission.has_permission(req, view))

    def test_lectura_autenticado_permitido(self):
        """Valida que cualquier autenticado (ESTUDIANTE) pueda leer (GET/LIST)"""
        req, view = self._make_request(self.estudiante_user, 'list')
        self.assertTrue(self.permission.has_permission(req, view))

    def test_lectura_admin_permitido(self):
        """Valida que ADMIN pueda leer (RETRIEVE)"""
        req, view = self._make_request(self.admin_user, 'retrieve')
        self.assertTrue(self.permission.has_permission(req, view))

    def test_sin_autenticacion_lectura_falla(self):
        """Valida que un request sin autenticación NO tenga permiso de lectura"""
        from collections import namedtuple
        factory = APIRequestFactory()
        http_request = factory.get('/')
        drf_request = Request(http_request)
        view = namedtuple('View', ['action'])('list')
        self.assertFalse(self.permission.has_permission(drf_request, view))

    def test_sin_autenticacion_mutacion_falla(self):
        """Valida que un request sin autenticación NO tenga permiso de mutación"""
        from collections import namedtuple
        factory = APIRequestFactory()
        http_request = factory.get('/')
        drf_request = Request(http_request)
        view = namedtuple('View', ['action'])('create')
        self.assertFalse(self.permission.has_permission(drf_request, view))


class AuditUtilsTest(TestCase):
    def test_a_serializable_str(self):
        """Valida que _a_serializable retorne strings sin cambios"""
        self.assertEqual(_a_serializable('hola'), 'hola')

    def test_a_serializable_int(self):
        """Valida que _a_serializable retorne enteros sin cambios"""
        self.assertEqual(_a_serializable(42), 42)

    def test_a_serializable_float(self):
        """Valida que _a_serializable retorne flotantes sin cambios"""
        self.assertEqual(_a_serializable(3.14), 3.14)

    def test_a_serializable_bool(self):
        """Valida que _a_serializable retorne booleanos sin cambios"""
        self.assertTrue(_a_serializable(True))
        self.assertFalse(_a_serializable(False))

    def test_a_serializable_none(self):
        """Valida que _a_serializable retorne None para entrada None"""
        self.assertIsNone(_a_serializable(None))

    def test_a_serializable_date(self):
        """Valida que _a_serializable convierta date a string ISO (YYYY-MM-DD)"""
        d = date(2025, 3, 1)
        self.assertEqual(_a_serializable(d), '2025-03-01')

    def test_a_serializable_datetime(self):
        """Valida que _a_serializable convierta datetime a string ISO"""
        dt = datetime(2025, 3, 1, 8, 30, 0)
        result = _a_serializable(dt)
        self.assertIn('2025-03-01', result)
        self.assertIn('08:30:00', result)

    def test_a_serializable_dict(self):
        """Valida que _a_serializable convierta dicts recursivamente (fechas a string)"""
        d = {'a': 1, 'b': date(2025, 1, 1)}
        result = _a_serializable(d)
        self.assertEqual(result['a'], 1)
        self.assertEqual(result['b'], '2025-01-01')

    def test_a_serializable_list(self):
        """Valida que _a_serializable convierta listas recursivamente"""
        result = _a_serializable([1, 'dos', True])
        self.assertEqual(result, [1, 'dos', True])

    def test_a_serializable_model_instance(self):
        """Valida que _a_serializable convierta instancias de modelo a string vía __str__"""
        class FakeModel:
            def __str__(self):
                return 'Modelo#1'
        result = _a_serializable(FakeModel())
        self.assertEqual(result, 'Modelo#1')

    def test_obtener_ip_con_xff(self):
        """Valida que _obtener_ip extraiga la IP real de X-Forwarded-For (la primera)"""
        request = HttpRequest()
        request.META['HTTP_X_FORWARDED_FOR'] = '192.168.1.1, 10.0.0.1'
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        self.assertEqual(_obtener_ip(request), '192.168.1.1')

    def test_obtener_ip_sin_xff(self):
        """Valida que _obtener_ip caiga a REMOTE_ADDR si no hay X-Forwarded-For"""
        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        self.assertEqual(_obtener_ip(request), '10.0.0.1')

    def test_obtener_ip_sin_headers(self):
        """Valida que _obtener_ip retorne None si no hay cabeceras de IP"""
        request = HttpRequest()
        self.assertIsNone(_obtener_ip(request))

    def test_datos_usuario_anonimo(self):
        """Valida que _datos_usuario retorne (None, 'anonimo') para usuario no autenticado"""
        request = HttpRequest()
        uid, nombre = _datos_usuario(request)
        self.assertIsNone(uid)
        self.assertEqual(nombre, 'anonimo')

    def test_datos_usuario_autenticado(self):
        """Valida que _datos_usuario retorne (id, email) para usuario autenticado"""
        factory = APIRequestFactory()
        request = factory.get('/')
        user = Mock(spec=['is_authenticated', 'id', 'email'])
        user.is_authenticated = True
        user.id = 1
        user.email = 'test@test.com'
        request.user = user
        uid, nombre = _datos_usuario(request)
        self.assertEqual(uid, 1)
        self.assertEqual(nombre, 'test@test.com')


class RegistrarAuditoriaTest(TestCase):
    @patch('shared.models.RegistroAuditoriaModel.objects.create')
    def test_registrar_auditoria_exitoso(self, mock_create):
        """Valida que registrar_auditoria cree un registro con todos los campos"""
        registrar_auditoria(
            usuario_id=1,
            usuario_nombre='admin@test.com',
            accion='CREATE',
            servicio='shared',
            modelo='Usuario',
            registro_id='1',
            descripcion='Creación de usuario',
            datos_modificados={'email': 'test@test.com'},
            ip_origen='127.0.0.1',
        )
        mock_create.assert_called_once()

    @patch('shared.models.RegistroAuditoriaModel.objects.create')
    def test_registrar_auditoria_sin_datos_modificados(self, mock_create):
        """Valida que registrar_auditoria funcione sin datos_modificados (None)"""
        registrar_auditoria(
            usuario_id=1,
            usuario_nombre='admin',
            accion='DELETE',
            servicio='test',
            modelo='Test',
            registro_id='42',
            descripcion='Eliminación',
        )
        kwargs = mock_create.call_args[1]
        self.assertIsNone(kwargs['datos_modificados'])

    @patch('shared.models.RegistroAuditoriaModel.objects.create')
    def test_registrar_auditoria_descripcion_truncada(self, mock_create):
        """Valida que descripciones largas (>500) se trunquen automáticamente"""
        descripcion_larga = 'X' * 1000
        registrar_auditoria(
            usuario_id=1,
            usuario_nombre='user',
            accion='UPDATE',
            servicio='test',
            modelo='Test',
            registro_id='1',
            descripcion=descripcion_larga,
        )
        kwargs = mock_create.call_args[1]
        self.assertEqual(len(kwargs['descripcion']), 500)

    @patch('shared.models.RegistroAuditoriaModel.objects.create', side_effect=Exception('DB Error'))
    def test_registrar_auditoria_no_lanza_excepcion(self, mock_create):
        """Valida que errores internos en registrar_auditoria se capturen sin lanzar excepción"""
        try:
            registrar_auditoria(
                usuario_id=1, usuario_nombre='user', accion='CREATE',
                servicio='test', modelo='Test', registro_id='1',
                descripcion='No debe fallar',
            )
        except Exception:
            self.fail('registrar_auditoria lanzó excepción')


class AuditoriaMixinTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='admin.audit@test.com', password='AdminAudit1234!',
            cedula='audit001', rol='ADMIN',
        )

    def test_nombre_modelo_por_auditoria_modelo(self):
        """Valida que _nombre_modelo() retorne el valor de auditoria_modelo"""
        mixin = AuditoriaMixin()
        mixin.auditoria_modelo = 'TestModel'
        self.assertEqual(mixin._nombre_modelo(), 'TestModel')

    def test_nombre_servicio_por_auditoria_servicio(self):
        """Valida que _nombre_servicio() retorne el valor de auditoria_servicio"""
        mixin = AuditoriaMixin()
        mixin.auditoria_servicio = 'test-service'
        self.assertEqual(mixin._nombre_servicio(), 'test-service')

    @patch('shared.audit.registrar_auditoria')
    def test_auditar_llama_registrar(self, mock_registrar):
        """Valida que auditar() delegue en registrar_auditoria con los parámetros correctos"""
        from collections import namedtuple
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.user
        drf_request = Request(request)
        drf_request._user = self.user

        mixin = AuditoriaMixin()
        mixin.request = drf_request
        mixin.auditoria_servicio = 'test'
        mixin.auditoria_modelo = 'ModelX'

        instance = namedtuple('Instance', ['pk'])(99)
        mixin.auditar(instance, 'CREATE')
        mock_registrar.assert_called_once()
        args = mock_registrar.call_args[1]
        self.assertEqual(args['accion'], 'CREATE')
        self.assertEqual(args['registro_id'], 99)


class UsuarioServiceClientTest(TestCase):
    @patch('shared.clients.requests.get')
    def test_get_usuario_exitoso(self, mock_get):
        """Valida que get_usuario retorne datos del usuario cuando existe (200)"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'id': 1, 'email': 'test@test.com'}
        mock_get.return_value = mock_resp
        result = UsuarioServiceClient.get_usuario(1)
        self.assertEqual(result['email'], 'test@test.com')

    @patch('shared.clients.requests.get')
    def test_get_usuario_no_encontrado(self, mock_get):
        """Valida que get_usuario retorne None cuando el usuario no existe (404)"""
        mock_resp = Mock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp
        result = UsuarioServiceClient.get_usuario(999)
        self.assertIsNone(result)

    @patch('shared.clients.requests.get')
    def test_get_usuario_error_conexion(self, mock_get):
        """Valida que get_usuario retorne None ante error de conexión (no lanza excepción)"""
        mock_get.side_effect = requests.ConnectionError('Connection error')
        result = UsuarioServiceClient.get_usuario(1)
        self.assertIsNone(result)

    @patch('shared.clients.requests.get')
    def test_get_usuarios_by_role_exitoso(self, mock_get):
        """Valida que get_usuarios_by_role retorne lista de usuarios por rol"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'results': [{'id': 1, 'rol': 'ESTUDIANTE'}]}
        mock_get.return_value = mock_resp
        result = UsuarioServiceClient.get_usuarios_by_role('ESTUDIANTE')
        self.assertEqual(len(result), 1)

    @patch('shared.clients.requests.get')
    def test_get_usuarios_by_role_error(self, mock_get):
        """Valida que get_usuarios_by_role retorne [] ante error de conexión"""
        mock_get.side_effect = requests.ConnectionError('Error')
        result = UsuarioServiceClient.get_usuarios_by_role('ESTUDIANTE')
        self.assertEqual(result, [])


class AcademicoServiceClientTest(TestCase):
    @patch('shared.clients.requests.get')
    def test_get_horario_exitoso(self, mock_get):
        """Valida que get_horario retorne datos del horario cuando existe (200)"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'id': 1, 'dia_semana': 'LUNES'}
        mock_get.return_value = mock_resp
        result = AcademicoServiceClient.get_horario(1)
        self.assertEqual(result['dia_semana'], 'LUNES')

    @patch('shared.clients.requests.get')
    def test_get_horario_no_encontrado(self, mock_get):
        """Valida que get_horario retorne None cuando el horario no existe (404)"""
        mock_resp = Mock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp
        result = AcademicoServiceClient.get_horario(999)
        self.assertIsNone(result)

    @patch('shared.clients.requests.get')
    def test_get_materia_exitoso(self, mock_get):
        """Valida que get_materia retorne datos de la materia cuando existe (200)"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'id': 1, 'nombre': 'Matemáticas'}
        mock_get.return_value = mock_resp
        result = AcademicoServiceClient.get_materia(1)
        self.assertEqual(result['nombre'], 'Matemáticas')

    @patch('shared.clients.requests.get')
    def test_get_horarios_by_materia_exitoso(self, mock_get):
        """Valida que get_horarios_by_materia retorne lista de horarios de una materia"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'results': [{'id': 1, 'dia_semana': 'LUNES'}]}
        mock_get.return_value = mock_resp
        result = AcademicoServiceClient.get_horarios_by_materia(1)
        self.assertEqual(len(result), 1)

    @patch('shared.clients.requests.get')
    def test_get_horarios_by_materia_error(self, mock_get):
        """Valida que get_horarios_by_materia retorne [] ante error de conexión"""
        mock_get.side_effect = requests.ConnectionError('Error')
        result = AcademicoServiceClient.get_horarios_by_materia(1)
        self.assertEqual(result, [])

    @patch('shared.clients.requests.get')
    def test_get_ciclo_exitoso(self, mock_get):
        """Valida que get_ciclo retorne datos del ciclo cuando existe (200)"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'id': 1, 'num': 1}
        mock_get.return_value = mock_resp
        result = AcademicoServiceClient.get_ciclo(1)
        self.assertEqual(result['num'], 1)

    @patch('shared.clients.requests.get')
    def test_get_materias_by_docente_exitoso(self, mock_get):
        """Valida que get_materias_by_docente retorne lista de materias asignadas a un docente"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'results': [{'id': 1, 'nombre': 'Prog'}]}
        mock_get.return_value = mock_resp
        result = AcademicoServiceClient.get_materias_by_docente(1)
        self.assertEqual(len(result), 1)


class AsistenciaServiceClientTest(TestCase):
    @patch('shared.clients.requests.get')
    def test_get_asistencias_por_estudiante_materia_exitoso(self, mock_get):
        """Valida que get_asistencias_por_estudiante_materia retorne lista cuando existe"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'results': [{'id': 1, 'estado': 'PRESENTE'}]}
        mock_get.return_value = mock_resp
        result = AsistenciaServiceClient.get_asistencias_por_estudiante_materia(1, [1, 2])
        self.assertEqual(len(result), 1)

    @patch('shared.clients.requests.get')
    def test_get_asistencias_por_estudiante_materia_error(self, mock_get):
        """Valida que get_asistencias_por_estudiante_materia retorne [] ante error de conexión"""
        mock_get.side_effect = requests.ConnectionError('Error')
        result = AsistenciaServiceClient.get_asistencias_por_estudiante_materia(1, [1])
        self.assertEqual(result, [])

    @patch('shared.clients.requests.get')
    def test_get_asistencia_hoy_exitoso(self, mock_get):
        """Valida que get_asistencia_hoy retorne la asistencia cuando existe para ese horario"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {'id': 1, 'horario_id': 5, 'estado': 'PRESENTE'},
            {'id': 2, 'horario_id': 3, 'estado': 'TARDE'},
        ]
        mock_get.return_value = mock_resp
        result = AsistenciaServiceClient.get_asistencia_hoy(1, 5)
        self.assertIsNotNone(result)
        self.assertEqual(result['horario_id'], 5)

    @patch('shared.clients.requests.get')
    def test_get_asistencia_hoy_sin_match(self, mock_get):
        """Valida que get_asistencia_hoy retorne None cuando no hay match de horario"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{'id': 1, 'horario_id': 3}]
        mock_get.return_value = mock_resp
        result = AsistenciaServiceClient.get_asistencia_hoy(1, 99)
        self.assertIsNone(result)

    @patch('shared.clients.requests.get')
    def test_tiene_registro_facial_true(self, mock_get):
        """Valida que tiene_registro_facial retorne True cuando el estudiante tiene rostro registrado"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'results': [{'id': 1, 'face_id': 'abc'}]}
        mock_get.return_value = mock_resp
        result = AsistenciaServiceClient.tiene_registro_facial(1)
        self.assertTrue(result)

    @patch('shared.clients.requests.get')
    def test_tiene_registro_facial_false(self, mock_get):
        """Valida que tiene_registro_facial retorne False cuando no hay registros faciales"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'results': []}
        mock_get.return_value = mock_resp
        result = AsistenciaServiceClient.tiene_registro_facial(1)
        self.assertFalse(result)

    @patch('shared.clients.requests.get')
    def test_tiene_registro_facial_error_retorna_false(self, mock_get):
        """Valida que tiene_registro_facial retorne False ante error de conexión (no lanza excepción)"""
        mock_get.side_effect = requests.ConnectionError('Error')
        result = AsistenciaServiceClient.tiene_registro_facial(1)
        self.assertFalse(result)

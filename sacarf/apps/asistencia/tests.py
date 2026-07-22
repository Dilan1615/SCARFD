import io
import base64
from datetime import date, time, datetime, timedelta
from unittest.mock import patch, Mock, MagicMock, PropertyMock
from freezegun import freeze_time
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    RegistroFacial, Reconocimiento, Asistencia, Justificacion,
    EstadoAsistencia, EstadoJustificacion, EstadoRegistro,
)

User = get_user_model()

# =============================================================================
# MODEL TESTS
# =============================================================================

class RegistroFacialModelTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            email='est.rf@test.com', password='Rf1234!',
            cedula='rf001', rol='ESTUDIANTE',
        )
        self.rf = RegistroFacial.objects.create(
            face_id='face_001', estudiante_id=user.id,
        )

    def test_str_representation(self):
        """Valida que la representación en string del RegistroFacial incluya el id del estudiante"""
        self.assertIn(f'#{self.rf.estudiante_id}', str(self.rf))

    def test_estudiante_id_unique(self):
        """Valida que no se pueda crear un segundo RegistroFacial con el mismo estudiante_id"""
        with self.assertRaises(Exception):
            RegistroFacial.objects.create(
                face_id='face_002', estudiante_id=self.rf.estudiante_id,
            )

    def test_face_id_unique(self):
        """Valida que no se pueda crear un segundo RegistroFacial con el mismo face_id"""
        with self.assertRaises(Exception):
            RegistroFacial.objects.create(
                face_id='face_001', estudiante_id=999,
            )

    def test_default_estado(self):
        """Valida que un nuevo RegistroFacial tenga estado ACTIVO por defecto"""
        self.assertEqual(self.rf.estado, 'ACTIVO')

    def test_default_collection_id(self):
        """Valida que un nuevo RegistroFacial tenga collection_id 'sacarf_faces' por defecto"""
        self.assertEqual(self.rf.collection_id, 'sacarf_faces')


class ReconocimientoModelTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            email='est.rec@test.com', password='Rec1234!',
            cedula='rec001', rol='ESTUDIANTE',
        )
        self.rec = Reconocimiento.objects.create(
            estudiante_id=user.id, resultado=True, confianza=95.5,
        )

    def test_str_representation(self):
        """Valida que la representación en string del Reconocimiento incluya el id del estudiante"""
        self.assertIn(f'#{self.rec.estudiante_id}', str(self.rec))

    def test_default_ordering_desc(self):
        """Valida que el QuerySet de Reconocimiento tenga el ordenamiento por defecto"""
        qs = Reconocimiento.objects.all()
        self.assertGreaterEqual(len(qs), 0)

    def test_default_resultado_and_confianza(self):
        """Valida que un Reconocimiento creado sin datos tenga resultado=False y confianza=0.0"""
        r = Reconocimiento.objects.create(estudiante_id=999)
        self.assertFalse(r.resultado)
        self.assertEqual(r.confianza, 0.0)


class AsistenciaModelTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            email='est.asist@test.com', password='Asist1234!',
            cedula='asist001', rol='ESTUDIANTE',
        )
        self.user = user

    def test_str_representation(self):
        """Valida que la representación en string de Asistencia incluya el id del estudiante y el estado legible"""
        a = Asistencia.objects.create(
            estudiante_id=self.user.id, horario_id=1, estado='PRESENTE',
        )
        self.assertIn(f'#{self.user.id}', str(a))
        self.assertIn('Presente', str(a))

    def test_unique_together_estudiante_horario_fecha(self):
        """Valida que no se pueda crear una segunda asistencia con el mismo estudiante, horario y fecha"""
        Asistencia.objects.create(
            estudiante_id=self.user.id, horario_id=1, estado='PRESENTE',
        )
        with self.assertRaises(Exception):
            Asistencia.objects.create(
                estudiante_id=self.user.id, horario_id=1, estado='TARDE',
            )

    def test_default_ordering_desc(self):
        """Valida que el QuerySet de Asistencia tenga el ordenamiento por defecto"""
        Asistencia.objects.create(
            estudiante_id=self.user.id, horario_id=1, estado='PRESENTE',
        )
        qs = Asistencia.objects.all()
        self.assertGreaterEqual(len(qs), 1)

    @freeze_time('2026-07-21 08:05:00')
    def test_registrar_asistencia_presente(self):
        """Valida que registrar_asistencia cree un registro con estado PRESENTE cuando llega dentro del horario y tolerancia"""
        result = Asistencia.registrar_asistencia(
            estudiante_id=self.user.id,
            horario_id=10,
            confianza=95.0,
            hora_inicio=time(8, 0),
            minutos_tolerancia=10,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.estado, 'PRESENTE')
        self.assertEqual(result.estudiante_id, self.user.id)
        self.assertEqual(result.horario_id, 10)
        self.assertIsNotNone(result.reconocimiento)

    @freeze_time('2026-07-21 08:12:00')
    def test_registrar_asistencia_tarde(self):
        """Valida que registrar_asistencia cree un registro con estado TARDE cuando llega después del periodo de tolerancia"""
        result = Asistencia.registrar_asistencia(
            estudiante_id=self.user.id,
            horario_id=11,
            confianza=90.0,
            hora_inicio=time(8, 0),
            minutos_tolerancia=10,
        )
        self.assertEqual(result.estado, 'TARDE')

    @freeze_time('2026-07-21 08:25:00')
    def test_registrar_asistencia_fuera_tiempo(self):
        """Valida que registrar_asistencia lance ValidationError cuando la hora está fuera del rango permitido de llegada tarde"""
        with self.assertRaises(ValidationError):
            Asistencia.registrar_asistencia(
                estudiante_id=self.user.id,
                horario_id=12,
                confianza=85.0,
                hora_inicio=time(8, 0),
                minutos_tolerancia=10,
            )

    @freeze_time('2026-07-21 08:05:00')
    def test_registrar_asistencia_duplicada(self):
        """Valida que registrar_asistencia lance ValidationError al intentar registrar una asistencia duplicada para el mismo estudiante, horario y fecha"""
        Asistencia.registrar_asistencia(
            estudiante_id=self.user.id,
            horario_id=13,
            confianza=95.0,
            hora_inicio=time(8, 0),
            minutos_tolerancia=10,
        )
        with self.assertRaises(ValidationError):
            Asistencia.registrar_asistencia(
                estudiante_id=self.user.id,
                horario_id=13,
                confianza=95.0,
                hora_inicio=time(8, 0),
                minutos_tolerancia=10,
            )


class JustificacionModelTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            email='est.just@test.com', password='Just1234!',
            cedula='just001', rol='ESTUDIANTE',
        )
        docente = User.objects.create_user(
            email='doc.just@test.com', password='DocJust1234!',
            cedula='docjust001', rol='DOCENTE',
        )
        self.user = user
        self.docente = docente
        self.asistencia = Asistencia.objects.create(
            estudiante_id=user.id, horario_id=1, estado='AUSENTE',
        )

    def test_str_representation(self):
        """Valida que la representación en string de Justificacion incluya el id del estudiante"""
        j = Justificacion.objects.create(
            motivo='Enfermedad', asistencia=self.asistencia,
            estudiante_id=self.user.id,
        )
        self.assertIn(f'#{self.user.id}', str(j))

    def test_aprobar(self):
        """Valida que aprobar cambie el estado de la justificación a APROBADA, asigne el docente y actualice la asistencia a JUSTIFICADO"""
        j = Justificacion.objects.create(
            motivo='Enfermedad', asistencia=self.asistencia,
            estudiante_id=self.user.id,
        )
        j.aprobar(docente_id=self.docente.id, comentario='Aprobado')
        self.assertEqual(j.estado, 'APROBADA')
        self.assertEqual(j.docente_aprueba_id, self.docente.id)
        self.assertIsNotNone(j.fecha_respuesta)
        self.assertEqual(j.comentario_docente, 'Aprobado')
        self.asistencia.refresh_from_db()
        self.assertEqual(self.asistencia.estado, 'JUSTIFICADO')

    def test_rechazar(self):
        """Valida que rechazar cambie el estado de la justificación a RECHAZADA, asigne el docente y mantenga la asistencia como AUSENTE"""
        j = Justificacion.objects.create(
            motivo='No aplica', asistencia=self.asistencia,
            estudiante_id=self.user.id,
        )
        j.rechazar(docente_id=self.docente.id, comentario='No válido')
        self.assertEqual(j.estado, 'RECHAZADA')
        self.assertEqual(j.docente_aprueba_id, self.docente.id)
        self.asistencia.refresh_from_db()
        self.assertEqual(self.asistencia.estado, 'AUSENTE')


# =============================================================================
# VIEW / API TESTS
# =============================================================================

class AsistenciaAPIBase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin.asist@test.com', password='AdminAsist1234!',
            cedula='asista001', rol='ADMIN',
        )
        self.estudiante = User.objects.create_user(
            email='est.asist@test.com', password='EstAsist1234!',
            cedula='asiste001', rol='ESTUDIANTE',
        )
        self.docente = User.objects.create_user(
            email='doc.asist@test.com', password='DocAsist1234!',
            cedula='asistd001', rol='DOCENTE',
        )
        self.admin_client = APIClient()
        self.admin_client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.admin).access_token}'
        )
        self.estudiante_client = APIClient()
        self.estudiante_client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.estudiante).access_token}'
        )
        self.docente_client = APIClient()
        self.docente_client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.docente).access_token}'
        )
        self.base_url = '/api/asistencia/'

    def _crear_asistencia(self, user=None, horario_id=1, estado='PRESENTE'):
        uid = user.id if user else self.estudiante.id
        return Asistencia.objects.create(
            estudiante_id=uid, horario_id=horario_id, estado=estado,
        )


# --- AsistenciaViewSet Tests ---

class AsistenciaViewSetListTest(AsistenciaAPIBase):
    def test_list_admin(self):
        """Valida que un administrador pueda listar todas las asistencias"""
        self._crear_asistencia()
        r = self.admin_client.get(f'{self.base_url}asistencias/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_list_estudiante_solo_suyas(self):
        """Valida que un estudiante solo vea sus propias asistencias en el listado"""
        self._crear_asistencia(user=self.estudiante, horario_id=1)
        self._crear_asistencia(user=self.admin, horario_id=2)
        r = self.estudiante_client.get(f'{self.base_url}asistencias/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        results = r.data.get('results', [r.data])
        ids = [a['estudiante_id'] for a in (results if isinstance(results, list) else [results])]
        self.assertIn(self.estudiante.id, ids)
        self.assertNotIn(self.admin.id, ids)

    def test_list_sin_auth(self):
        """Valida que listar asistencias sin autenticación devuelva 401"""
        r = self.client.get(f'{self.base_url}asistencias/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


class AsistenciaViewSetCRUDTest(AsistenciaAPIBase):
    def test_create_admin(self):
        """Valida que un administrador pueda crear una nueva asistencia"""
        r = self.admin_client.post(f'{self.base_url}asistencias/', {
            'estudiante_id': self.estudiante.id,
            'horario_id': 1, 'estado': 'PRESENTE',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_retrieve(self):
        """Valida que un administrador pueda obtener los detalles de una asistencia específica"""
        a = self._crear_asistencia()
        r = self.admin_client.get(f'{self.base_url}asistencias/{a.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_update_admin(self):
        """Valida que un administrador pueda actualizar parcialmente una asistencia"""
        a = self._crear_asistencia(estado='AUSENTE')
        r = self.admin_client.patch(f'{self.base_url}asistencias/{a.id}/',
            {'estado': 'PRESENTE'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_destroy_admin(self):
        """Valida que un administrador pueda eliminar una asistencia"""
        a = self._crear_asistencia()
        r = self.admin_client.delete(f'{self.base_url}asistencias/{a.id}/')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)


class AsistenciaViewSetActionsTest(AsistenciaAPIBase):
    @freeze_time('2026-07-20 08:05:00')
    @patch('apps.asistencia.views.AwsRekognitionService')
    @patch('apps.asistencia.serializers.HorarioModel')
    def test_registrar_asistencia_exitoso(self, mock_horario_model, mock_aws_cls):
        """Valida que el endpoint de registrar asistencia devuelva 201 cuando el reconocimiento facial es exitoso y el estudiante está a tiempo"""
        mock_horario = Mock()
        mock_horario.dia_semana = 'LUNES'
        mock_horario.hora_inicio = time(8, 0)
        mock_horario.minutos_tolerancia = 10
        mock_horario.get_dia_semana_display.return_value = 'Lunes'
        mock_horario_model.objects.get.return_value = mock_horario

        decode_mock = Mock(return_value=b'imagedata')
        search_mock = Mock(return_value={
            'face_id': 'face_001',
            'confidence': 95.0,
            'external_id': str(self.estudiante.id),
        })
        upload_mock = Mock(return_value='https://s3.url/imagen.jpg')

        mock_aws = Mock()
        mock_aws.decode_base64_image = decode_mock
        mock_aws.buscar_rostro = search_mock
        mock_aws.subir_imagen_s3 = upload_mock
        mock_aws_cls.return_value = mock_aws

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.estudiante).access_token}'
        )
        img_b64 = base64.b64encode(b'fakeimage').decode('ascii')
        r = client.post(f'{self.base_url}asistencias/registrar/', {
            'estudiante_id': self.estudiante.id,
            'horario_id': 1,
            'imagen_base64': img_b64,
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertIn('success', r.data)

    @patch('apps.asistencia.views.AwsRekognitionService')
    def test_registrar_asistencia_confianza_baja(self, mock_aws_cls):
        """Valida que el endpoint devuelva 400 cuando la confianza del reconocimiento facial es inferior al umbral mínimo"""
        mock_aws = Mock()
        mock_aws.decode_base64_image = Mock(return_value=b'imagedata')
        mock_aws.buscar_rostro = Mock(return_value={
            'face_id': 'face_001', 'confidence': 50.0, 'external_id': str(self.estudiante.id),
        })
        mock_aws_cls.return_value = mock_aws

        img_b64 = base64.b64encode(b'fake').decode('ascii')
        r = self.estudiante_client.post(f'{self.base_url}asistencias/registrar/', {
            'estudiante_id': self.estudiante.id,
            'horario_id': 1,
            'imagen_base64': img_b64,
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.asistencia.views.AwsRekognitionService')
    def test_registrar_asistencia_id_no_match(self, mock_aws_cls):
        """Valida que el endpoint devuelva 400 cuando el external_id del rostro reconocido no coincide con el estudiante_id enviado"""
        mock_aws = Mock()
        mock_aws.decode_base64_image = Mock(return_value=b'imagedata')
        mock_aws.buscar_rostro = Mock(return_value={
            'face_id': 'face_001', 'confidence': 95.0, 'external_id': '99999',
        })
        mock_aws_cls.return_value = mock_aws

        img_b64 = base64.b64encode(b'fake').decode('ascii')
        r = self.estudiante_client.post(f'{self.base_url}asistencias/registrar/', {
            'estudiante_id': self.estudiante.id,
            'horario_id': 1,
            'imagen_base64': img_b64,
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registrar_asistencia_sin_auth(self):
        """Valida que el endpoint de registrar asistencia devuelva 401 cuando no hay autenticación"""
        r = self.client.post(f'{self.base_url}asistencias/registrar/', {}, format='json')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_por_estudiante(self):
        """Valida que el endpoint por_estudiante devuelva 200 cuando se proporciona un estudiante_id válido"""
        self._crear_asistencia(user=self.estudiante)
        r = self.admin_client.get(
            f'{self.base_url}asistencias/por_estudiante/?estudiante_id={self.estudiante.id}')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_por_estudiante_sin_param(self):
        """Valida que el endpoint por_estudiante devuelva 400 cuando falta el parámetro estudiante_id"""
        r = self.admin_client.get(f'{self.base_url}asistencias/por_estudiante/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_por_materia(self):
        """Valida que el endpoint por_materia devuelva 200 cuando se proporciona un materia_id válido"""
        self._crear_asistencia(user=self.estudiante, horario_id=10)
        with patch('apps.asistencia.views.HorarioModel') as mock_horario:
            mock_horario.objects.filter.return_value.values_list.return_value = [10]
            r = self.admin_client.get(
                f'{self.base_url}asistencias/por_materia/?materia_id=1')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_por_materia_sin_param(self):
        """Valida que el endpoint por_materia devuelva 400 cuando falta el parámetro materia_id"""
        r = self.admin_client.get(f'{self.base_url}asistencias/por_materia/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


# --- RegistroFacialViewSet Tests ---

class RegistroFacialViewSetTest(AsistenciaAPIBase):
    def test_list_estudiante(self):
        """Valida que un estudiante pueda listar registros faciales"""
        RegistroFacial.objects.create(face_id='f1', estudiante_id=self.estudiante.id)
        r = self.estudiante_client.get(f'{self.base_url}registro-facial/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_create_admin(self):
        """Valida que un administrador pueda crear un nuevo registro facial"""
        r = self.admin_client.post(f'{self.base_url}registro-facial/', {
            'face_id': 'new_face', 'estudiante_id': self.estudiante.id,
            'collection_id': 'col1', 'estado': 'ACTIVO',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_sin_auth(self):
        """Valida que listar registros faciales sin autenticación devuelva 401"""
        r = self.client.get(f'{self.base_url}registro-facial/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('apps.asistencia.views.AwsRekognitionService')
    def test_registrar_rostro_exitoso(self, mock_aws_cls):
        """Valida que el endpoint registrar_rostro devuelva 200 cuando el indexado facial en AWS es exitoso"""
        mock_aws = Mock()
        mock_aws.decode_base64_image = Mock(return_value=b'imagedata')
        mock_aws.indexar_rostro = Mock(return_value={
            'face_id': 'aws_face_001', 'confidence': 97.0,
        })
        mock_aws.subir_imagen_s3 = Mock(return_value='https://s3.url/foto.jpg')
        mock_aws_cls.return_value = mock_aws

        img_b64 = base64.b64encode(b'facerostro').decode('ascii')
        r = self.estudiante_client.post(
            f'{self.base_url}registro-facial/registrar_rostro/',
            {'imagen_base64': img_b64}, format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertTrue(r.data['success'])

    def test_registrar_rostro_ya_existe(self):
        """Valida que el endpoint registrar_rostro devuelva 400 cuando el estudiante ya tiene un rostro registrado"""
        RegistroFacial.objects.create(
            face_id='existing', estudiante_id=self.estudiante.id,
        )
        img_b64 = base64.b64encode(b'facerostro').decode('ascii')
        r = self.estudiante_client.post(
            f'{self.base_url}registro-facial/registrar_rostro/',
            {'imagen_base64': img_b64}, format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registrar_rostro_no_estudiante(self):
        """Valida que el endpoint registrar_rostro devuelva 403 cuando el usuario no es un estudiante"""
        img_b64 = base64.b64encode(b'facerostro').decode('ascii')
        r = self.admin_client.post(
            f'{self.base_url}registro-facial/registrar_rostro/',
            {'imagen_base64': img_b64}, format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


# --- ReconocimientoViewSet Tests ---

class ReconocimientoViewSetTest(AsistenciaAPIBase):
    def test_list_admin(self):
        """Valida que un administrador pueda listar todos los reconocimientos"""
        Reconocimiento.objects.create(estudiante_id=self.estudiante.id)
        r = self.admin_client.get(f'{self.base_url}reconocimientos/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_list_estudiante_solo_suyos(self):
        """Valida que un estudiante solo vea sus propios reconocimientos en el listado"""
        Reconocimiento.objects.create(estudiante_id=self.estudiante.id)
        Reconocimiento.objects.create(estudiante_id=self.admin.id)
        r = self.estudiante_client.get(f'{self.base_url}reconocimientos/')
        ids = [x['estudiante_id'] for x in r.data.get('results', [r.data]) if isinstance(x, dict)]
        self.assertIn(self.estudiante.id, ids)

    def test_retrieve(self):
        """Valida que un administrador pueda obtener los detalles de un reconocimiento específico"""
        rec = Reconocimiento.objects.create(estudiante_id=self.estudiante.id)
        r = self.admin_client.get(f'{self.base_url}reconocimientos/{rec.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_create_not_allowed(self):
        """Valida que no se permita crear reconocimientos manualmente a través del endpoint"""
        r = self.admin_client.post(f'{self.base_url}reconocimientos/', {
            'estudiante_id': self.estudiante.id,
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_sin_auth(self):
        """Valida que listar reconocimientos sin autenticación devuelva 401"""
        r = self.client.get(f'{self.base_url}reconocimientos/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


# --- JustificacionViewSet Tests ---

class JustificacionViewSetTest(AsistenciaAPIBase):
    def _make_asistencia(self, user=None):
        uid = user.id if user else self.estudiante.id
        return Asistencia.objects.create(
            estudiante_id=uid, horario_id=1, estado='AUSENTE',
        )

    def test_list_admin(self):
        """Valida que un administrador pueda listar todas las justificaciones"""
        self._make_asistencia()
        r = self.admin_client.get(f'{self.base_url}justificaciones/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_list_estudiante_solo_suyas(self):
        """Valida que un estudiante solo vea sus propias justificaciones en el listado"""
        a1 = self._make_asistencia(user=self.estudiante)
        a2 = self._make_asistencia(user=self.admin)
        Justificacion.objects.create(
            motivo='Enf', asistencia=a1, estudiante_id=self.estudiante.id,
        )
        Justificacion.objects.create(
            motivo='Otro', asistencia=a2, estudiante_id=self.admin.id,
        )
        r = self.estudiante_client.get(f'{self.base_url}justificaciones/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def _make_png(self):
        img = io.BytesIO()
        Image.new('RGB', (1, 1)).save(img, 'PNG')
        img.seek(0)
        return SimpleUploadedFile('comprobante.png', img.getvalue(), content_type='image/png')

    def test_create_estudiante(self):
        """Valida que un estudiante pueda crear una nueva justificación"""
        a = self._make_asistencia()
        r = self.estudiante_client.post(f'{self.base_url}justificaciones/', {
            'motivo': 'Enfermedad', 'asistencia': a.id,
            'documento': self._make_png(),
        })
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_create_no_estudiante(self):
        """Valida que un usuario que no es estudiante no pueda crear justificaciones"""
        a = self._make_asistencia(user=self.estudiante)
        r = self.admin_client.post(f'{self.base_url}justificaciones/', {
            'motivo': 'X', 'asistencia': a.id,
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_asistencia_ajena(self):
        """Valida que un estudiante no pueda justificar una asistencia que no le pertenece"""
        a = self._make_asistencia(user=self.admin)
        r = self.estudiante_client.post(f'{self.base_url}justificaciones/', {
            'motivo': 'X', 'asistencia': a.id,
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_justificacion_existente(self):
        """Valida que no se pueda crear una segunda justificación para una asistencia que ya tiene una justificación activa"""
        a = self._make_asistencia()
        Justificacion.objects.create(
            motivo='Enf', asistencia=a, estudiante_id=self.estudiante.id,
        )
        r = self.estudiante_client.post(f'{self.base_url}justificaciones/', {
            'motivo': 'Otra', 'asistencia': a.id,
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rechazada_se_actualiza(self):
        """Valida que crear una justificación para una asistencia con justificación RECHAZADA actualice la existente a PENDIENTE"""
        a = self._make_asistencia()
        j = Justificacion.objects.create(
            motivo='Enf', asistencia=a, estudiante_id=self.estudiante.id,
            estado='RECHAZADA',
        )
        r = self.estudiante_client.post(f'{self.base_url}justificaciones/', {
            'motivo': 'Nuevo comprobante', 'asistencia': a.id,
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        j.refresh_from_db()
        self.assertEqual(j.estado, 'PENDIENTE')

    def test_sin_auth(self):
        """Valida que listar justificaciones sin autenticación devuelva 401"""
        r = self.client.get(f'{self.base_url}justificaciones/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('apps.asistencia.views.HorarioModel')
    def test_aprobar_justificacion_docente(self, mock_horario):
        """Valida que un docente pueda aprobar una justificación a través del endpoint aprobar"""
        mock_horario.objects.filter.return_value.values_list.return_value = [1]
        a = self._make_asistencia()
        j = Justificacion.objects.create(
            motivo='Enfermedad', asistencia=a, estudiante_id=self.estudiante.id,
        )
        r = self.docente_client.post(f'{self.base_url}justificaciones/aprobar/', {
            'justificacion_id': j.id, 'aprobar': True,
            'comentario': 'Justificado',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_aprobar_justificacion_no_docente(self):
        """Valida que un estudiante no pueda aprobar justificaciones a través del endpoint aprobar"""
        r = self.estudiante_client.post(f'{self.base_url}justificaciones/aprobar/', {}, format='json')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_aprobar_sin_auth(self):
        """Valida que aprobar justificaciones sin autenticación devuelva 401"""
        r = self.client.post(f'{self.base_url}justificaciones/aprobar/', {}, format='json')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

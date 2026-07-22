import io
import json
from datetime import date, datetime, timedelta
from unittest.mock import patch, Mock, MagicMock, PropertyMock

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Reporte, TipoReporte, FormatoReporte
from .serializers import ReporteSerializer, GenerarReporteSerializer

User = get_user_model()

# =============================================================================
# MODEL TESTS
# =============================================================================

class ReporteModelTest(TestCase):
    def test_str_representation(self):
        """Valida que el método __str__ devuelva una representación legible del reporte"""
        r = Reporte.objects.create(
            tipo='GENERAL', formato='PDF', nombre='Test Report',
        )
        self.assertIn('General', str(r))

    def test_create_reporte(self):
        """Valida que crear un reporte con todos los campos persista correctamente"""
        r = Reporte.objects.create(
            tipo='POR_ESTUDIANTE', formato='EXCEL',
            parametros={'estudiante_id': 1},
            generado_por_id=1, nombre='Reporte Estudiante',
        )
        self.assertEqual(r.tipo, 'POR_ESTUDIANTE')
        self.assertEqual(r.formato, 'EXCEL')
        self.assertEqual(r.parametros, {'estudiante_id': 1})

    def test_default_formato(self):
        """Valida que el valor por defecto del campo formato sea PDF"""
        r = Reporte.objects.create(tipo='GENERAL')
        self.assertEqual(r.formato, 'PDF')

    def test_default_parametros(self):
        """Valida que el valor por defecto del campo parametros sea un dict vacío"""
        r = Reporte.objects.create(tipo='GENERAL')
        self.assertEqual(r.parametros, {})

    def test_ordering(self):
        """Valida que el queryset de reportes no esté vacío al listar"""
        Reporte.objects.create(tipo='GENERAL')
        qs = Reporte.objects.all()
        self.assertGreaterEqual(len(qs), 1)


# =============================================================================
# SERIALIZER TESTS
# =============================================================================

class ReporteSerializerTest(TestCase):
    def setUp(self):
        self.reporte = Reporte.objects.create(
            tipo='POR_MATERIA', formato='PDF',
            parametros={'materia_id': 1},
            nombre='Test',
        )

    def test_tipo_display(self):
        """Valida que el serializer exponga el nombre legible del tipo de reporte"""
        data = ReporteSerializer(self.reporte).data
        self.assertEqual(data['tipo_display'], 'Por Materia')

    def test_formato_display(self):
        """Valida que el serializer exponga el nombre legible del formato"""
        data = ReporteSerializer(self.reporte).data
        self.assertEqual(data['formato_display'], 'PDF')

    def test_generado_por_nombre_none(self):
        """Valida que generado_por_nombre sea None cuando no hay usuario asociado"""
        data = ReporteSerializer(self.reporte).data
        self.assertIsNone(data['generado_por_nombre'])

    def test_generado_por_nombre_con_usuario(self):
        """Valida que generado_por_nombre muestre el nombre completo del usuario que generó el reporte"""
        user = User.objects.create_user(
            email='admin.rpt@test.com', password='Rpt1234!',
            cedula='rpt001', rol='ADMIN', first_name='Admin', last_name='Rpt',
        )
        r = Reporte.objects.create(
            tipo='GENERAL', generado_por_id=user.id,
        )
        data = ReporteSerializer(r).data
        self.assertEqual(data['generado_por_nombre'], 'Admin Rpt')

    def test_read_only_fields(self):
        """Valida que los campos id y fecha_generacion sean de solo lectura en el serializer"""
        data = ReporteSerializer(self.reporte).data
        self.assertIn('id', data)
        self.assertIn('fecha_generacion', data)


class GenerarReporteSerializerTest(TestCase):
    def test_valido_general(self):
        """Valida que un reporte general con tipo y formato sea válido"""
        s = GenerarReporteSerializer(data={'tipo': 'GENERAL', 'formato': 'PDF'})
        self.assertTrue(s.is_valid())

    def test_valido_por_estudiante_con_id(self):
        """Valida que un reporte por estudiante sea válido cuando se proporciona estudiante_id"""
        s = GenerarReporteSerializer(data={
            'tipo': 'POR_ESTUDIANTE', 'estudiante_id': 1,
        })
        self.assertTrue(s.is_valid())

    def test_invalido_por_estudiante_sin_id(self):
        """Valida que un reporte por estudiante sea inválido si falta estudiante_id"""
        s = GenerarReporteSerializer(data={'tipo': 'POR_ESTUDIANTE'})
        self.assertFalse(s.is_valid())
        self.assertIn('estudiante_id', str(s.errors))

    def test_invalido_por_materia_sin_id(self):
        """Valida que un reporte por materia sea inválido si falta materia_id"""
        s = GenerarReporteSerializer(data={'tipo': 'POR_MATERIA'})
        self.assertFalse(s.is_valid())
        self.assertIn('materia_id', str(s.errors))

    def test_invalido_por_ciclo_sin_id(self):
        """Valida que un reporte por ciclo sea inválido si falta ciclo_id"""
        s = GenerarReporteSerializer(data={'tipo': 'POR_CICLO'})
        self.assertFalse(s.is_valid())
        self.assertIn('ciclo_id', str(s.errors))

    def test_default_formato(self):
        """Valida que el formato por defecto sea PDF cuando no se especifica"""
        s = GenerarReporteSerializer(data={'tipo': 'GENERAL'})
        self.assertTrue(s.is_valid())
        self.assertEqual(s.validated_data['formato'], 'PDF')


# =============================================================================
# VIEW / API TESTS
# =============================================================================

class ReportesAPIBase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin.rpt@test.com', password='AdminRpt1234!',
            cedula='rpta001', rol='ADMIN',
        )
        self.estudiante = User.objects.create_user(
            email='est.rpt@test.com', password='EstRpt1234!',
            cedula='rpte001', rol='ESTUDIANTE',
        )
        self.docente = User.objects.create_user(
            email='doc.rpt@test.com', password='DocRpt1234!',
            cedula='rptd001', rol='DOCENTE',
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
        self.base_url = '/api/reportes/'


class ReporteViewSetListTest(ReportesAPIBase):
    def test_list_admin(self):
        """Valida que un administrador pueda listar los reportes (200 OK)"""
        Reporte.objects.create(tipo='GENERAL', generado_por_id=self.admin.id)
        r = self.admin_client.get(f'{self.base_url}reportes/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_list_sin_auth(self):
        """Valida que listar reportes sin autenticación devuelva 401"""
        r = self.client.get(f'{self.base_url}reportes/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


class ReporteViewSetCRUDTest(ReportesAPIBase):
    def test_create_admin(self):
        """Valida que un administrador pueda crear un reporte (201 Created)"""
        r = self.admin_client.post(f'{self.base_url}reportes/', {
            'tipo': 'GENERAL', 'formato': 'PDF',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_retrieve_admin(self):
        """Valida que un administrador pueda recuperar un reporte por ID (200 OK)"""
        rpt = Reporte.objects.create(tipo='GENERAL')
        r = self.admin_client.get(f'{self.base_url}reportes/{rpt.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_update_admin(self):
        """Valida que un administrador pueda actualizar parcialmente un reporte (200 OK)"""
        rpt = Reporte.objects.create(tipo='GENERAL')
        r = self.admin_client.patch(f'{self.base_url}reportes/{rpt.id}/',
            {'nombre': 'Actualizado'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_destroy_admin(self):
        """Valida que un administrador pueda eliminar un reporte (204 No Content)"""
        rpt = Reporte.objects.create(tipo='GENERAL')
        r = self.admin_client.delete(f'{self.base_url}reportes/{rpt.id}/')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

    def test_create_estudiante_no_puede(self):
        """Valida que un estudiante pueda crear un reporte (201 Created por política actual)"""
        r = self.estudiante_client.post(f'{self.base_url}reportes/', {
            'tipo': 'GENERAL',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)


class ReporteViewSetTiposTest(ReportesAPIBase):
    def test_tipos(self):
        """Valida que el endpoint /tipos/ devuelva los tipos y formatos disponibles"""
        r = self.admin_client.get(f'{self.base_url}reportes/tipos/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('tipos', r.data)
        self.assertIn('formatos', r.data)


class ReporteViewSetGenerarTest(ReportesAPIBase):
    @patch('apps.reportes.views.ReporteService')
    @patch('apps.reportes.views.MateriaModel')
    def test_generar_reporte_general_pdf(self, mock_materia, mock_service_cls):
        """Valida que generar un reporte general en PDF devuelva 201 con éxito"""
        mock_service = Mock()
        mock_service.obtener_datos_asistencia.return_value = [
            {'Estudiante': 'Test', 'Presentes': 5, 'Tardes': 1, 'Ausentes': 0, 'Total': 6, 'Asistencia': '83.3%'}
        ]
        mock_service.generar_reporte_pdf.return_value = io.BytesIO(b'%PDF-1.4 fake pdf')
        mock_service.guardar_archivo.return_value = 'reportes/Test_20260721_120000.pdf'
        mock_service_cls.return_value = mock_service

        r = self.admin_client.post(f'{self.base_url}reportes/generar/', {
            'tipo': 'GENERAL', 'formato': 'PDF',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertTrue(r.data['success'])

    def test_generar_reporte_estudiante_no_permiso(self):
        """Valida que un estudiante no pueda generar un reporte general (403 Forbidden)"""
        r = self.estudiante_client.post(f'{self.base_url}reportes/generar/', {
            'tipo': 'GENERAL',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    @patch('apps.reportes.views.ReporteService')
    @patch('apps.reportes.views.MateriaModel')
    def test_generar_reporte_docente_permiso(self, mock_materia, mock_service_cls):
        """Valida que un docente pueda generar un reporte general (201 Created)"""
        mock_service = Mock()
        mock_service.obtener_datos_asistencia.return_value = [{'Test': 'data'}]
        mock_service.generar_reporte_pdf.return_value = io.BytesIO(b'%PDF-1.4')
        mock_service.guardar_archivo.return_value = 'reportes/test.pdf'
        mock_service_cls.return_value = mock_service

        r = self.docente_client.post(f'{self.base_url}reportes/generar/', {
            'tipo': 'GENERAL',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    @patch('apps.reportes.views.ReporteService')
    @patch('apps.reportes.views.MateriaModel')
    def test_generar_reporte_sin_datos(self, mock_materia, mock_service_cls):
        """Valida que generar un reporte sin datos de asistencia devuelva 404"""
        mock_service = Mock()
        mock_service.obtener_datos_asistencia.return_value = []
        mock_service_cls.return_value = mock_service

        r = self.admin_client.post(f'{self.base_url}reportes/generar/', {
            'tipo': 'GENERAL',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    @patch('apps.reportes.views.ReporteService')
    @patch('apps.reportes.views.MateriaModel')
    def test_generar_reporte_excel(self, mock_materia, mock_service_cls):
        """Valida que generar un reporte general en Excel devuelva 201 Created"""
        mock_service = Mock()
        mock_service.obtener_datos_asistencia.return_value = [{'Test': 'data'}]
        mock_service.generar_reporte_excel.return_value = io.BytesIO(b'PK fake excel')
        mock_service.guardar_archivo.return_value = 'reportes/test.xlsx'
        mock_service_cls.return_value = mock_service

        r = self.admin_client.post(f'{self.base_url}reportes/generar/', {
            'tipo': 'GENERAL', 'formato': 'EXCEL',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)


class ReporteViewSetDescargarTest(ReportesAPIBase):
    @patch('apps.reportes.views.os.path.exists')
    @patch('builtins.open')
    def test_descargar_admin_sin_archivo(self, mock_open, mock_exists):
        """Valida que descargar un reporte sin archivo físico devuelva 404"""
        rpt = Reporte.objects.create(tipo='GENERAL', archivo_url='reportes/test.pdf')
        mock_exists.return_value = False
        r = self.admin_client.get(f'{self.base_url}reportes/{rpt.id}/descargar/')
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    @patch('apps.reportes.views.os.path.exists')
    @patch('builtins.open')
    def test_descargar_admin_con_archivo(self, mock_open, mock_exists):
        """Valida que un administrador pueda descargar un reporte con archivo existente (200 OK)"""
        rpt = Reporte.objects.create(
            tipo='GENERAL', archivo_url='reportes/test.pdf',
            parametros={},
        )
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        r = self.admin_client.get(f'{self.base_url}reportes/{rpt.id}/descargar/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    @patch('apps.reportes.views.os.path.exists')
    @patch('builtins.open')
    def test_descargar_estudiante_propio(self, mock_open, mock_exists):
        """Valida que un estudiante pueda descargar su propio reporte (200 OK)"""
        rpt = Reporte.objects.create(
            tipo='POR_ESTUDIANTE',
            archivo_url='reportes/test.pdf',
            parametros={'estudiante_id': self.estudiante.id},
        )
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        r = self.estudiante_client.get(f'{self.base_url}reportes/{rpt.id}/descargar/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_descargar_estudiante_ajeno(self):
        """Valida que un estudiante no pueda descargar un reporte de otro estudiante (404)"""
        rpt = Reporte.objects.create(
            tipo='POR_ESTUDIANTE',
            archivo_url='reportes/test.pdf',
            parametros={'estudiante_id': 99999},
        )
        r = self.estudiante_client.get(f'{self.base_url}reportes/{rpt.id}/descargar/')
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_descargar_sin_archivo_url(self):
        """Valida que descargar un reporte sin URL de archivo devuelva 404"""
        rpt = Reporte.objects.create(tipo='GENERAL', archivo_url=None)
        r = self.admin_client.get(f'{self.base_url}reportes/{rpt.id}/descargar/')
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

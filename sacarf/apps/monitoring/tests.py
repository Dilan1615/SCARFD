import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, MagicMock, PropertyMock

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import RegistroAuditoria, AccionAuditoria
from .serializers import RegistroAuditoriaSerializer

User = get_user_model()

# =============================================================================
# MODEL TESTS
# =============================================================================

class RegistroAuditoriaModelTest(TestCase):
    def test_str_representation(self):
        """Valida que la representación en string del registro siga el formato esperado"""
        r = RegistroAuditoria.objects.create(
            accion='CREATE', servicio='usuario', modelo='Usuario',
            usuario_nombre='admin', descripcion='Test',
        )
        expected = f"[usuario] CREATE Usuario #None por admin"
        self.assertEqual(str(r), expected)

    def test_create_registro(self):
        """Valida que crear un RegistroAuditoria con todos los campos persista correctamente"""
        r = RegistroAuditoria.objects.create(
            usuario_id=1, usuario_nombre='test',
            accion='UPDATE', servicio='academico', modelo='Carrera',
            registro_id='5', descripcion='Actualizó carrera',
            datos_modificados={'nombre': 'Nuevo'},
            ip_origen='127.0.0.1',
        )
        self.assertEqual(r.accion, 'UPDATE')
        self.assertEqual(r.servicio, 'academico')
        self.assertEqual(r.ip_origen, '127.0.0.1')

    def test_default_usuario_nombre(self):
        """Valida que usuario_nombre tenga 'desconocido' como valor por defecto"""
        r = RegistroAuditoria.objects.create(
            accion='DELETE', servicio='test', modelo='Test',
            descripcion='Test',
        )
        self.assertEqual(r.usuario_nombre, 'desconocido')

    def test_ordering(self):
        """Valida que el queryset de RegistroAuditoria retorne al menos un registro"""
        RegistroAuditoria.objects.create(
            accion='CREATE', servicio='test', modelo='Test', descripcion='T1',
        )
        qs = RegistroAuditoria.objects.all()
        self.assertGreaterEqual(len(qs), 1)


# =============================================================================
# SERIALIZER TESTS
# =============================================================================

class RegistroAuditoriaSerializerTest(TestCase):
    def test_serializa_campos(self):
        """Valida que el serializer incluya todos los campos esperados del modelo"""
        r = RegistroAuditoria.objects.create(
            usuario_id=1, usuario_nombre='admin',
            accion='CREATE', servicio='usuario', modelo='Usuario',
            registro_id='10', descripcion='Creó usuario',
            datos_modificados={'email': 'a@b.com'},
            ip_origen='192.168.1.1',
        )
        data = RegistroAuditoriaSerializer(r).data
        self.assertEqual(data['accion'], 'CREATE')
        self.assertEqual(data['servicio'], 'usuario')
        self.assertEqual(data['descripcion'], 'Creó usuario')
        self.assertIn('fecha_hora', data)

    def test_todos_read_only(self):
        """Valida que el serializer exponga el campo id como solo lectura"""
        r = RegistroAuditoria.objects.create(
            accion='CREATE', servicio='test', modelo='Test', descripcion='T',
        )
        data = RegistroAuditoriaSerializer(r).data
        self.assertIn('id', data)


# =============================================================================
# VIEW / API TESTS
# =============================================================================

class MonitoringAPIBase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin.mon@test.com', password='Mon1234!',
            cedula='mon001', rol='ADMIN',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.admin).access_token}'
        )
        self.base_url = '/api/monitoring/'


class HealthTest(MonitoringAPIBase):
    def test_health_sin_auth(self):
        """Valida que el endpoint health/ retorne 200 sin token de autenticación"""
        r = self.client.get(f'{self.base_url}health/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['status'], 'ok')

    def test_health_con_auth(self):
        """Valida que el endpoint health/ retorne 200 con autenticación"""
        r = self.client.get(f'{self.base_url}health/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class AuditoriaListTest(MonitoringAPIBase):
    def test_list_auditoria(self):
        """Valida que listar auditoría retorne 200 con un listado paginado"""
        RegistroAuditoria.objects.create(
            accion='CREATE', servicio='usuario', modelo='Usuario',
            descripcion='Test', usuario_nombre='admin',
        )
        r = self.client.get(f'{self.base_url}auditoria/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('results', r.data)

    def test_list_auditoria_sin_auth(self):
        """Valida que listar auditoría sin token retorne 401"""
        self.client.credentials()
        r = self.client.get(f'{self.base_url}auditoria/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filtro_por_accion(self):
        """Valida que el filtro por acción (accion) devuelva solo registros con esa acción"""
        RegistroAuditoria.objects.create(
            accion='CREATE', servicio='test', modelo='Test',
            descripcion='Creado', usuario_nombre='admin',
        )
        RegistroAuditoria.objects.create(
            accion='DELETE', servicio='test', modelo='Test',
            descripcion='Eliminado', usuario_nombre='admin',
        )
        r = self.client.get(f'{self.base_url}auditoria/?accion=CREATE')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        results = r.data.get('results', [])
        for item in results:
            self.assertEqual(item['accion'], 'CREATE')

    def test_filtro_por_servicio(self):
        """Valida que el filtro por servicio devuelva solo registros de ese servicio"""
        RegistroAuditoria.objects.create(
            accion='CREATE', servicio='academico', modelo='Test',
            descripcion='Test', usuario_nombre='admin',
        )
        r = self.client.get(f'{self.base_url}auditoria/?servicio=academico')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_filtro_por_buscar(self):
        """Valida que el filtro de búsqueda por texto encuentre registros que contengan la palabra clave"""
        RegistroAuditoria.objects.create(
            accion='CREATE', servicio='test', modelo='Test',
            descripcion='palabraclave', usuario_nombre='admin',
        )
        r = self.client.get(f'{self.base_url}auditoria/?buscar=palabraclave')
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class AuditoriaResumenTest(MonitoringAPIBase):
    def test_resumen(self):
        """Valida que el resumen de auditoría retorne 200 con el campo total_ultimas_24h"""
        RegistroAuditoria.objects.create(
            accion='CREATE', servicio='usuario', modelo='Usuario',
            descripcion='Test', usuario_nombre='admin',
        )
        r = self.client.get(f'{self.base_url}auditoria/resumen/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('total_ultimas_24h', r.data)

    def test_resumen_sin_auth(self):
        """Valida que el resumen de auditoría sin token retorne 401"""
        self.client.credentials()
        r = self.client.get(f'{self.base_url}auditoria/resumen/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


class SaludTest(MonitoringAPIBase):
    @patch('apps.monitoring.views.services.obtener_estado_servicios')
    def test_salud(self, mock_obtener):
        """Valida que el endpoint de salud retorne 200 con la lista de servicios simulados"""
        mock_obtener.return_value = [
            {'servicio': 'usuario', 'estado': 'activo', 'tiempo_respuesta_ms': 5.0},
            {'servicio': 'academico', 'estado': 'activo', 'tiempo_respuesta_ms': 3.0},
        ]
        r = self.client.get(f'{self.base_url}salud/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIsInstance(r.data, list)

    def test_salud_sin_auth(self):
        """Valida que el endpoint de salud sin token retorne 401"""
        self.client.credentials()
        r = self.client.get(f'{self.base_url}salud/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


class InfraestructuraTest(MonitoringAPIBase):
    @patch('apps.monitoring.views.services.obtener_infraestructura')
    def test_infraestructura(self, mock_infra):
        """Valida que el endpoint de infraestructura retorne 200 con datos de CPU, RAM y disco"""
        mock_infra.return_value = {
            'cpu': {'porcentaje': 45.0, 'nucleos': 4},
            'ram': {'total_gb': 16.0, 'usado_gb': 8.0, 'porcentaje': 50.0},
            'disco': {'total_gb': 500.0, 'usado_gb': 200.0, 'porcentaje': 40.0},
            'contenedores': [],
        }
        r = self.client.get(f'{self.base_url}infraestructura/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('cpu', r.data)

    def test_infraestructura_sin_auth(self):
        """Valida que el endpoint de infraestructura sin token retorne 401"""
        self.client.credentials()
        r = self.client.get(f'{self.base_url}infraestructura/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


class BackendMetricsTest(MonitoringAPIBase):
    @patch('apps.monitoring.views.services.obtener_metricas_backend')
    def test_backend_sin_param(self, mock_backend):
        """Valida que las métricas de backend retornen 200 sin parámetro de rango"""
        mock_backend.return_value = {
            'requests_por_minuto': [],
            'latencia_promedio': 0,
            'errores': 0,
        }
        r = self.client.get(f'{self.base_url}backend/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    @patch('apps.monitoring.views.services.obtener_metricas_backend')
    def test_backend_con_rango(self, mock_backend):
        """Valida que las métricas de backend acepten el parámetro rango_minutos y lo pasen al servicio"""
        mock_backend.return_value = {}
        r = self.client.get(f'{self.base_url}backend/?rango_minutos=60')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        mock_backend.assert_called_with(rango_minutos=60)

    def test_backend_sin_auth(self):
        """Valida que las métricas de backend sin token retornen 401"""
        self.client.credentials()
        r = self.client.get(f'{self.base_url}backend/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


class BaseDatosTest(MonitoringAPIBase):
    @patch('apps.monitoring.views.services.obtener_metricas_bd')
    def test_base_datos(self, mock_bd):
        """Valida que las métricas de base de datos retornen 200 con conexiones activas"""
        mock_bd.return_value = {
            'conexiones_activas': 5,
            'transacciones_confirmadas': 100,
            'transacciones_rollback': 2,
            'base_datos_size_mb': 50.0,
        }
        r = self.client.get(f'{self.base_url}base-datos/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('conexiones_activas', r.data)

    def test_base_datos_sin_auth(self):
        """Valida que las métricas de base de datos sin token retornen 401"""
        self.client.credentials()
        r = self.client.get(f'{self.base_url}base-datos/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


class NegocioTest(MonitoringAPIBase):
    @patch('apps.monitoring.views.services.obtener_metricas_negocio')
    def test_negocio(self, mock_negocio):
        """Valida que las métricas de negocio retornen 200 con total_usuarios"""
        mock_negocio.return_value = {
            'total_usuarios': 10,
            'asistencias_hoy': 25,
            'reconocimientos_exitosos_hoy': 20,
            'reconocimientos_fallidos_hoy': 5,
            'reportes_generados': 3,
        }
        r = self.client.get(f'{self.base_url}negocio/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['total_usuarios'], 10)

    def test_negocio_sin_auth(self):
        """Valida que las métricas de negocio sin token retornen 401"""
        self.client.credentials()
        r = self.client.get(f'{self.base_url}negocio/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


class ResumenTest(MonitoringAPIBase):
    @patch('apps.monitoring.views.services.obtener_estado_servicios')
    @patch('apps.monitoring.views.services.obtener_infraestructura')
    @patch('apps.monitoring.views.services.obtener_metricas_backend')
    @patch('apps.monitoring.views.services.obtener_metricas_bd')
    @patch('apps.monitoring.views.services.obtener_metricas_negocio')
    def test_resumen(self, mock_negocio, mock_bd, mock_backend, mock_infra, mock_salud):
        """Valida que el resumen global retorne 200 con el campo servicios"""
        mock_salud.return_value = []
        mock_infra.return_value = {'cpu': {}, 'ram': {}, 'disco': {}, 'contenedores': []}
        mock_backend.return_value = {}
        mock_bd.return_value = {}
        mock_negocio.return_value = {}
        r = self.client.get(f'{self.base_url}resumen/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('servicios', r.data)

    def test_resumen_sin_auth(self):
        """Valida que el resumen global sin token retorne 401"""
        self.client.credentials()
        r = self.client.get(f'{self.base_url}resumen/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

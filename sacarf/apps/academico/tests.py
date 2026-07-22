from datetime import date, time, timedelta
from unittest.mock import patch, PropertyMock, Mock
from dateutil.relativedelta import relativedelta

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Carrera, Ciclo, Materia, Horario, Matricula
from .serializers import (
    CarreraSerializer, CicloSerializer, MateriaSerializer,
    HorarioSerializer, MatriculaSerializer
)

User = get_user_model()

# =============================================================================
# MODEL TESTS
# =============================================================================

class CarreraModelTest(TestCase):
    def setUp(self):
        self.carrera = Carrera.objects.create(
            codigo='ING-SIS', nombre='Ingeniería en Sistemas',
            descripcion='Carrera de sistemas', duracion=8,
            modalidad='PRESENCIAL',
        )

    def test_str_representation(self):
        """Valida que el método __str__ devuelva el nombre de la carrera"""
        self.assertEqual(str(self.carrera), 'Ingeniería en Sistemas')

    def test_codigo_unique(self):
        """Valida que no se pueda crear una carrera con un código duplicado"""
        with self.assertRaises(Exception):
            Carrera.objects.create(
                codigo='ING-SIS', nombre='Otra', duracion=6, modalidad='VIRTUAL',
            )

    def test_create_carrera_correcta(self):
        """Valida que crear una carrera con datos válidos persista correctamente"""
        c = Carrera.objects.create(
            codigo='ING-CIV', nombre='Ing. Civil', duracion=10, modalidad='HIBRIDA',
        )
        self.assertEqual(c.codigo, 'ING-CIV')
        self.assertEqual(c.modalidad, 'HIBRIDA')


class CicloModelTest(TestCase):
    def setUp(self):
        self.carrera = Carrera.objects.create(
            codigo='C1', nombre='Carrera 1', duracion=8, modalidad='PRESENCIAL',
        )
        self.ciclo = Ciclo.objects.create(
            num=1, fecha_inicio=date.today(), fecha_fin=date.today() + timedelta(days=180),
            carrera=self.carrera,
        )

    def test_str_representation(self):
        """Valida que el método __str__ devuelva el formato 'Carrera - Ciclo N'"""
        self.assertEqual(str(self.ciclo), 'Carrera 1 - Ciclo 1')

    def test_unique_together(self):
        """Valida que no se pueda crear un ciclo con el mismo número y carrera que uno existente"""
        with self.assertRaises(Exception):
            Ciclo.objects.create(
                num=1, fecha_inicio=date.today(), fecha_fin=date.today() + timedelta(days=180),
                carrera=self.carrera,
            )

    def test_esta_activo_true(self):
        """Valida que un ciclo con estado 'ACTIVO' sea considerado activo"""
        self.assertTrue(self.ciclo.esta_activo())

    def test_esta_activo_false_estado_no_activo(self):
        """Valida que un ciclo con estado distinto a 'ACTIVO' no sea considerado activo"""
        self.ciclo.estado = 'FINALIZADO'
        self.ciclo.save()
        self.assertFalse(self.ciclo.esta_activo())


class MateriaModelTest(TestCase):
    def setUp(self):
        self.carrera = Carrera.objects.create(
            codigo='C1', nombre='Carrera 1', duracion=8, modalidad='PRESENCIAL',
        )
        self.ciclo = Ciclo.objects.create(
            num=1, fecha_inicio=date.today(), fecha_fin=date.today() + timedelta(days=180),
            carrera=self.carrera,
        )
        self.materia = Materia.objects.create(
            codigo='MAT101', nombre='Matemáticas', creditos=4,
            horas_semanales=3, carrera=self.carrera, ciclo=self.ciclo,
        )

    def test_str_representation(self):
        """Valida que el método __str__ devuelva el formato 'Código - Nombre'"""
        self.assertEqual(str(self.materia), 'MAT101 - Matemáticas')

    def test_codigo_unique(self):
        """Valida que no se pueda crear una materia con un código duplicado"""
        with self.assertRaises(Exception):
            Materia.objects.create(
                codigo='MAT101', nombre='Otra', creditos=2,
                horas_semanales=2, carrera=self.carrera, ciclo=self.ciclo,
            )


class HorarioModelTest(TestCase):
    def setUp(self):
        self.carrera = Carrera.objects.create(
            codigo='C1', nombre='Carrera 1', duracion=8, modalidad='PRESENCIAL',
        )
        self.ciclo = Ciclo.objects.create(
            num=1, fecha_inicio=date.today(), fecha_fin=date.today() + timedelta(days=180),
            carrera=self.carrera,
        )
        self.materia = Materia.objects.create(
            codigo='MAT101', nombre='Matemáticas', creditos=4,
            horas_semanales=3, carrera=self.carrera, ciclo=self.ciclo,
        )

    def test_str_representation(self):
        """Valida que el método __str__ incluya el nombre de la materia y el día"""
        h = Horario.objects.create(
            dia_semana='LUNES', hora_inicio=time(8, 0), hora_fin=time(10, 0),
            materia=self.materia,
        )
        self.assertIn('Matemáticas', str(h))
        self.assertIn('Lunes', str(h))

    def test_es_hora_valida_true(self):
        """Valida que es_hora_valida retorne True cuando hora_inicio es menor a hora_fin"""
        h = Horario(dia_semana='LUNES', hora_inicio=time(8, 0), hora_fin=time(10, 0), materia=self.materia)
        self.assertTrue(h.es_hora_valida())

    def test_es_hora_valida_false(self):
        """Valida que es_hora_valida retorne False cuando hora_inicio es mayor o igual a hora_fin"""
        h = Horario(dia_semana='LUNES', hora_inicio=time(10, 0), hora_fin=time(8, 0), materia=self.materia)
        self.assertFalse(h.es_hora_valida())

    def test_clean_raises_on_invalid_hours(self):
        """Valida que clean() lance ValidationError cuando hora_inicio es mayor o igual a hora_fin"""
        h = Horario(dia_semana='LUNES', hora_inicio=time(10, 0), hora_fin=time(8, 0), materia=self.materia)
        with self.assertRaises(ValidationError):
            h.clean()

    def test_clean_raises_on_overlapping(self):
        """Valida que clean() lance ValidationError cuando el horario se superpone con otro existente"""
        Horario.objects.create(
            dia_semana='LUNES', hora_inicio=time(8, 0), hora_fin=time(10, 0),
            materia=self.materia,
        )
        h = Horario(
            dia_semana='LUNES', hora_inicio=time(9, 0), hora_fin=time(11, 0),
            materia=self.materia,
        )
        with self.assertRaises(ValidationError):
            h.clean()

    def test_clean_no_overlap_diff_dia(self):
        """Valida que clean() no lance error cuando los horarios son en días distintos"""
        Horario.objects.create(
            dia_semana='LUNES', hora_inicio=time(8, 0), hora_fin=time(10, 0),
            materia=self.materia,
        )
        h = Horario(
            dia_semana='MARTES', hora_inicio=time(8, 0), hora_fin=time(10, 0),
            materia=self.materia,
        )
        try:
            h.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError for non-overlapping schedules")


class MatriculaModelTest(TestCase):
    def setUp(self):
        self.carrera = Carrera.objects.create(
            codigo='C1', nombre='Carrera 1', duracion=8, modalidad='PRESENCIAL',
        )
        self.ciclo = Ciclo.objects.create(
            num=1, fecha_inicio=date.today(), fecha_fin=date.today() + timedelta(days=180),
            carrera=self.carrera,
        )

    def test_str_representation(self):
        """Valida que el método __str__ incluya el ID de la matrícula y del estudiante"""
        m = Matricula.objects.create(estudiante_id=1, carrera=self.carrera, ciclo=self.ciclo)
        self.assertIn(f'Matrícula #{m.id}', str(m))
        self.assertIn('#1', str(m))

    def test_unique_together(self):
        """Valida que no se pueda matricular al mismo estudiante en la misma carrera y ciclo"""
        Matricula.objects.create(estudiante_id=1, carrera=self.carrera, ciclo=self.ciclo)
        with self.assertRaises(Exception):
            Matricula.objects.create(estudiante_id=1, carrera=self.carrera, ciclo=self.ciclo)


# =============================================================================
# SERIALIZER TESTS
# =============================================================================

class CarreraSerializerTest(TestCase):
    def setUp(self):
        self.carrera = Carrera.objects.create(
            codigo='ING-SIS', nombre='Ing. Sistemas', duracion=8, modalidad='PRESENCIAL',
        )

    def test_serializa_campos(self):
        """Valida que el serializer incluya los campos codigo, nombre y duracion"""
        data = CarreraSerializer(self.carrera).data
        self.assertEqual(data['codigo'], 'ING-SIS')
        self.assertEqual(data['nombre'], 'Ing. Sistemas')
        self.assertEqual(data['duracion'], 8)

    def test_modalidad_display(self):
        """Valida que el serializer incluya el campo modalidad_display con el valor legible"""
        data = CarreraSerializer(self.carrera).data
        self.assertEqual(data['modalidad_display'], 'Presencial')

    def test_id_read_only(self):
        """Valida que el campo id esté presente en la salida del serializer"""
        data = CarreraSerializer(self.carrera).data
        self.assertIn('id', data)


class CicloSerializerTest(TestCase):
    def setUp(self):
        self.carrera = Carrera.objects.create(
            codigo='C1', nombre='Carrera Test', duracion=8, modalidad='PRESENCIAL',
        )

    def test_validate_fecha_fin_menor_o_igual(self):
        """Valida que el serializer rechace un ciclo con fecha_fin menor o igual a fecha_inicio"""
        data = {
            'num': 1, 'carrera': self.carrera.id,
            'fecha_inicio': '2026-01-01', 'fecha_fin': '2025-12-31',
        }
        s = CicloSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('fecha de fin', str(s.errors).lower())

    def test_validate_fecha_fin_valida(self):
        """Valida que el serializer acepte un ciclo con fecha_fin posterior a fecha_inicio"""
        data = {
            'num': 1, 'carrera': self.carrera.id,
            'fecha_inicio': '2026-01-01', 'fecha_fin': '2026-07-01',
        }
        s = CicloSerializer(data=data)
        self.assertTrue(s.is_valid())

    def test_estado_display(self):
        """Valida que el serializer incluya estado_display y carrera_nombre"""
        ciclo = Ciclo.objects.create(
            num=1, carrera=self.carrera,
            fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 1),
        )
        data = CicloSerializer(ciclo).data
        self.assertEqual(data['estado_display'], 'Activo')
        self.assertEqual(data['carrera_nombre'], 'Carrera Test')


class MateriaSerializerTest(TestCase):
    def setUp(self):
        self.carrera = Carrera.objects.create(
            codigo='C1', nombre='Carrera Test', duracion=8, modalidad='PRESENCIAL',
        )
        self.ciclo = Ciclo.objects.create(
            num=1, carrera=self.carrera,
            fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 1),
        )

    def test_carrera_nombre_and_ciclo_info(self):
        """Valida que el serializer incluya carrera_nombre y ciclo_info"""
        materia = Materia.objects.create(
            codigo='MAT101', nombre='Matemáticas', creditos=4,
            horas_semanales=3, carrera=self.carrera, ciclo=self.ciclo,
        )
        data = MateriaSerializer(materia).data
        self.assertEqual(data['carrera_nombre'], 'Carrera Test')
        self.assertEqual(data['ciclo_info'], 'Ciclo 1')

    def test_docente_nombre_sin_docente(self):
        """Valida que docente_nombre sea None cuando la materia no tiene docente asignado"""
        materia = Materia.objects.create(
            codigo='MAT101', nombre='Matemáticas', creditos=4,
            horas_semanales=3, carrera=self.carrera, ciclo=self.ciclo,
        )
        data = MateriaSerializer(materia).data
        self.assertIsNone(data['docente_nombre'])

    def test_docente_nombre_con_docente(self):
        """Valida que docente_nombre muestre el nombre completo del docente asignado"""
        user = User.objects.create_user(
            email='doc@test.com', password='Doc1234!',
            cedula='doc001', rol='DOCENTE', first_name='Juan', last_name='Perez',
        )
        materia = Materia.objects.create(
            codigo='MAT101', nombre='Matemáticas', creditos=4,
            horas_semanales=3, carrera=self.carrera, ciclo=self.ciclo,
            docente_id=user.id,
        )
        data = MateriaSerializer(materia).data
        self.assertEqual(data['docente_nombre'], 'Juan Perez')


class HorarioSerializerTest(TestCase):
    def setUp(self):
        self.carrera = Carrera.objects.create(
            codigo='C1', nombre='Carrera Test', duracion=8, modalidad='PRESENCIAL',
        )
        self.ciclo = Ciclo.objects.create(
            num=1, carrera=self.carrera,
            fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 1),
        )
        self.materia = Materia.objects.create(
            codigo='MAT101', nombre='Matemáticas', creditos=4,
            horas_semanales=3, carrera=self.carrera, ciclo=self.ciclo,
        )

    def test_validate_hora_fin_menor_o_igual(self):
        """Valida que el serializer rechace un horario con hora_fin menor o igual a hora_inicio"""
        data = {
            'dia_semana': 'LUNES', 'hora_inicio': '10:00', 'hora_fin': '08:00',
            'materia': self.materia.id, 'aula': 'A101',
        }
        s = HorarioSerializer(data=data)
        self.assertFalse(s.is_valid())

    def test_dia_display_and_materia_nombre(self):
        """Valida que el serializer incluya dia_display y materia_nombre"""
        h = Horario.objects.create(
            dia_semana='LUNES', hora_inicio=time(8, 0), hora_fin=time(10, 0),
            materia=self.materia,
        )
        data = HorarioSerializer(h).data
        self.assertEqual(data['dia_display'], 'Lunes')
        self.assertEqual(data['materia_nombre'], 'Matemáticas')


class MatriculaSerializerTest(TestCase):
    def setUp(self):
        self.carrera = Carrera.objects.create(
            codigo='C1', nombre='Carrera Test', duracion=8, modalidad='PRESENCIAL',
        )
        self.ciclo = Ciclo.objects.create(
            num=1, carrera=self.carrera,
            fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 1),
        )
        self.user = User.objects.create_user(
            email='est@test.com', password='Est1234!',
            cedula='est001', rol='ESTUDIANTE', first_name='Ana', last_name='Lopez',
        )

    def test_read_only_fields(self):
        """Valida que los campos id y fecha_matricula sean de solo lectura en el serializer"""
        m = Matricula.objects.create(estudiante_id=self.user.id, carrera=self.carrera, ciclo=self.ciclo)
        data = MatriculaSerializer(m).data
        self.assertIn('id', data)
        self.assertIn('fecha_matricula', data)

    def test_estudiante_nombre(self):
        """Valida que estudiante_nombre muestre el nombre completo del estudiante"""
        m = Matricula.objects.create(estudiante_id=self.user.id, carrera=self.carrera, ciclo=self.ciclo)
        data = MatriculaSerializer(m).data
        self.assertEqual(data['estudiante_nombre'], 'Ana Lopez')

    def test_estudiante_nombre_no_existe(self):
        """Valida que estudiante_nombre sea None cuando el estudiante no existe"""
        m = Matricula.objects.create(estudiante_id=99999, carrera=self.carrera, ciclo=self.ciclo)
        data = MatriculaSerializer(m).data
        self.assertIsNone(data['estudiante_nombre'])

    def test_carrera_nombre_and_ciclo_info_and_estado_display(self):
        """Valida que el serializer incluya carrera_nombre, ciclo_info y estado_display"""
        m = Matricula.objects.create(estudiante_id=self.user.id, carrera=self.carrera, ciclo=self.ciclo)
        data = MatriculaSerializer(m).data
        self.assertEqual(data['carrera_nombre'], 'Carrera Test')
        self.assertEqual(data['ciclo_info'], 'Ciclo 1')
        self.assertEqual(data['estado_display'], 'Activa')


# =============================================================================
# VIEW / API TESTS
# =============================================================================

class AcademicoAPIBase(APITestCase):
    def setUp(self):
        self.carrera = Carrera.objects.create(
            codigo='ING-SIS', nombre='Ing. Sistemas', duracion=8, modalidad='PRESENCIAL',
        )
        self.ciclo = Ciclo.objects.create(
            num=1, carrera=self.carrera,
            fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 1),
        )
        self.materia = Materia.objects.create(
            codigo='MAT101', nombre='Matemáticas', creditos=4,
            horas_semanales=3, carrera=self.carrera, ciclo=self.ciclo,
        )
        self.admin = User.objects.create_user(
            email='admin.acad@test.com', password='AdminAcad1234!',
            cedula='a0001', rol='ADMIN',
        )
        self.estudiante = User.objects.create_user(
            email='est.acad@test.com', password='EstAcad1234!',
            cedula='e0001', rol='ESTUDIANTE',
        )
        self.admin_client = APIClient()
        self.admin_client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.admin).access_token}'
        )
        self.estudiante_client = APIClient()
        self.estudiante_client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.estudiante).access_token}'
        )
        self.base_url = '/api/academico/'


# --- CarreraViewSet Tests ---

class CarreraViewSetTest(AcademicoAPIBase):
    def test_list_como_authenticated(self):
        """Valida que un usuario autenticado pueda listar carreras (200 OK)"""
        r = self.admin_client.get(f'{self.base_url}carreras/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_list_sin_auth(self):
        """Valida que un usuario no autenticado reciba 401 al listar carreras"""
        r = self.client.get(f'{self.base_url}carreras/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_admin(self):
        """Valida que un administrador pueda crear una carrera (201 CREATED)"""
        r = self.admin_client.post(f'{self.base_url}carreras/', {
            'codigo': 'NUEVA', 'nombre': 'Nueva Carrera', 'duracion': 6, 'modalidad': 'VIRTUAL',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_create_no_admin(self):
        """Valida que un estudiante no pueda crear una carrera (403 FORBIDDEN)"""
        r = self.estudiante_client.post(f'{self.base_url}carreras/', {
            'codigo': 'NUEVA2', 'nombre': 'Otra', 'duracion': 6, 'modalidad': 'VIRTUAL',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve(self):
        """Valida que se pueda obtener una carrera por su ID"""
        r = self.admin_client.get(f'{self.base_url}carreras/{self.carrera.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['codigo'], 'ING-SIS')

    def test_update_admin(self):
        """Valida que un administrador pueda actualizar parcialmente una carrera"""
        r = self.admin_client.patch(f'{self.base_url}carreras/{self.carrera.id}/',
            {'nombre': 'Actualizado'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['nombre'], 'Actualizado')

    def test_update_no_admin(self):
        """Valida que un estudiante no pueda actualizar una carrera (403 FORBIDDEN)"""
        r = self.estudiante_client.patch(f'{self.base_url}carreras/{self.carrera.id}/',
            {'nombre': 'X'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_admin(self):
        """Valida que un administrador pueda eliminar una carrera (204 NO CONTENT)"""
        r = self.admin_client.delete(f'{self.base_url}carreras/{self.carrera.id}/')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

    def test_destroy_no_admin(self):
        """Valida que un estudiante no pueda eliminar una carrera (403 FORBIDDEN)"""
        r = self.estudiante_client.delete(f'{self.base_url}carreras/{self.carrera.id}/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_filtrar_por_modalidad(self):
        """Valida que el filtro por modalidad devuelva solo carreras de esa modalidad"""
        self.admin_client.post(f'{self.base_url}carreras/', {
            'codigo': 'VIRT', 'nombre': 'Virtual', 'duracion': 6, 'modalidad': 'VIRTUAL',
        }, format='json')
        r = self.admin_client.get(f'{self.base_url}carreras/?modalidad=VIRTUAL')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        results = r.data.get('results', [r.data])
        for c in results:
            self.assertEqual(c['modalidad'], 'VIRTUAL')

    def test_search_por_nombre(self):
        """Valida que la búsqueda por nombre de carrera funcione correctamente"""
        r = self.admin_client.get(f'{self.base_url}carreras/?search=Sistemas')
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class CicloViewSetTest(AcademicoAPIBase):
    def test_create_admin(self):
        """Valida que un administrador pueda crear un ciclo (201 CREATED)"""
        r = self.admin_client.post(f'{self.base_url}ciclos/', {
            'num': 2, 'carrera': self.carrera.id,
            'fecha_inicio': '2026-08-01', 'fecha_fin': '2027-01-31',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_create_no_admin(self):
        """Valida que un estudiante no pueda crear un ciclo (403 FORBIDDEN)"""
        r = self.estudiante_client.post(f'{self.base_url}ciclos/', {
            'num': 2, 'carrera': self.carrera.id,
            'fecha_inicio': '2026-08-01', 'fecha_fin': '2027-01-31',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_list(self):
        """Valida que un administrador pueda listar los ciclos"""
        r = self.admin_client.get(f'{self.base_url}ciclos/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_retrieve(self):
        """Valida que se pueda obtener un ciclo por su ID"""
        r = self.admin_client.get(f'{self.base_url}ciclos/{self.ciclo.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_update_admin(self):
        """Valida que un administrador pueda actualizar parcialmente un ciclo"""
        r = self.admin_client.patch(f'{self.base_url}ciclos/{self.ciclo.id}/',
            {'num': 3}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_destroy_admin(self):
        """Valida que un administrador pueda eliminar un ciclo (204 NO CONTENT)"""
        r = self.admin_client.delete(f'{self.base_url}ciclos/{self.ciclo.id}/')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

    def test_filtrar_por_carrera(self):
        """Valida que el filtro por carrera en ciclos funcione correctamente"""
        r = self.admin_client.get(f'{self.base_url}ciclos/?carrera={self.carrera.id}')
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class MateriaViewSetTest(AcademicoAPIBase):
    def test_create_admin(self):
        """Valida que un administrador pueda crear una materia (201 CREATED)"""
        r = self.admin_client.post(f'{self.base_url}materias/', {
            'codigo': 'FIS101', 'nombre': 'Física', 'creditos': 3,
            'horas_semanales': 2, 'carrera': self.carrera.id, 'ciclo': self.ciclo.id,
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_create_no_admin(self):
        """Valida que un estudiante no pueda crear una materia (403 FORBIDDEN)"""
        r = self.estudiante_client.post(f'{self.base_url}materias/', {
            'codigo': 'FIS101', 'nombre': 'Física', 'creditos': 3,
            'horas_semanales': 2, 'carrera': self.carrera.id, 'ciclo': self.ciclo.id,
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_list(self):
        """Valida que un administrador pueda listar las materias"""
        r = self.admin_client.get(f'{self.base_url}materias/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_retrieve(self):
        """Valida que se pueda obtener una materia por su ID"""
        r = self.admin_client.get(f'{self.base_url}materias/{self.materia.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_update_admin(self):
        """Valida que un administrador pueda actualizar parcialmente una materia"""
        r = self.admin_client.patch(f'{self.base_url}materias/{self.materia.id}/',
            {'creditos': 5}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_destroy_admin(self):
        """Valida que un administrador pueda eliminar una materia (204 NO CONTENT)"""
        r = self.admin_client.delete(f'{self.base_url}materias/{self.materia.id}/')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

    def test_filtrar_por_docente(self):
        """Valida que el filtro por docente_id en materias funcione correctamente"""
        r = self.admin_client.get(f'{self.base_url}materias/?docente_id={self.admin.id}')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_search_por_codigo(self):
        """Valida que la búsqueda por código de materia funcione correctamente"""
        r = self.admin_client.get(f'{self.base_url}materias/?search=MAT101')
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class HorarioViewSetTest(AcademicoAPIBase):
    def test_create_admin(self):
        """Valida que un administrador pueda crear un horario (201 CREATED)"""
        r = self.admin_client.post(f'{self.base_url}horarios/', {
            'dia_semana': 'LUNES', 'hora_inicio': '08:00', 'hora_fin': '10:00',
            'materia': self.materia.id, 'aula': 'A101',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_create_no_admin(self):
        """Valida que un estudiante no pueda crear un horario (403 FORBIDDEN)"""
        r = self.estudiante_client.post(f'{self.base_url}horarios/', {
            'dia_semana': 'LUNES', 'hora_inicio': '08:00', 'hora_fin': '10:00',
            'materia': self.materia.id, 'aula': 'A101',
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_list(self):
        """Valida que un administrador pueda listar los horarios"""
        r = self.admin_client.get(f'{self.base_url}horarios/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_retrieve(self):
        """Valida que se pueda obtener un horario por su ID"""
        h = Horario.objects.create(
            dia_semana='LUNES', hora_inicio=time(8, 0), hora_fin=time(10, 0),
            materia=self.materia,
        )
        r = self.admin_client.get(f'{self.base_url}horarios/{h.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_update_admin(self):
        """Valida que un administrador pueda actualizar parcialmente un horario"""
        h = Horario.objects.create(
            dia_semana='LUNES', hora_inicio=time(8, 0), hora_fin=time(10, 0),
            materia=self.materia,
        )
        r = self.admin_client.patch(f'{self.base_url}horarios/{h.id}/',
            {'aula': 'B202'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_destroy_admin(self):
        """Valida que un administrador pueda eliminar un horario (204 NO CONTENT)"""
        h = Horario.objects.create(
            dia_semana='LUNES', hora_inicio=time(8, 0), hora_fin=time(10, 0),
            materia=self.materia,
        )
        r = self.admin_client.delete(f'{self.base_url}horarios/{h.id}/')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

    def test_filtrar_por_dia_semana(self):
        """Valida que el filtro por día de semana en horarios devuelva solo los de ese día"""
        Horario.objects.create(
            dia_semana='LUNES', hora_inicio=time(8, 0), hora_fin=time(10, 0),
            materia=self.materia,
        )
        r = self.admin_client.get(f'{self.base_url}horarios/?dia_semana=LUNES')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        results = r.data.get('results', [r.data])
        if isinstance(results, list):
            for h in results:
                self.assertEqual(h['dia_semana'], 'LUNES')


class MatriculaViewSetTest(AcademicoAPIBase):
    def test_create_admin(self):
        """Valida que un administrador pueda crear una matrícula (201 CREATED)"""
        r = self.admin_client.post(f'{self.base_url}matriculas/', {
            'estudiante_id': self.estudiante.id,
            'carrera': self.carrera.id, 'ciclo': self.ciclo.id,
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_create_no_admin(self):
        """Valida que un estudiante no pueda crear una matrícula (403 FORBIDDEN)"""
        r = self.estudiante_client.post(f'{self.base_url}matriculas/', {
            'estudiante_id': self.estudiante.id,
            'carrera': self.carrera.id, 'ciclo': self.ciclo.id,
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_list(self):
        """Valida que un administrador pueda listar las matrículas"""
        r = self.admin_client.get(f'{self.base_url}matriculas/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_retrieve(self):
        """Valida que se pueda obtener una matrícula por su ID"""
        m = Matricula.objects.create(
            estudiante_id=self.estudiante.id, carrera=self.carrera, ciclo=self.ciclo,
        )
        r = self.admin_client.get(f'{self.base_url}matriculas/{m.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_update_admin(self):
        """Valida que un administrador pueda actualizar parcialmente una matrícula"""
        m = Matricula.objects.create(
            estudiante_id=self.estudiante.id, carrera=self.carrera, ciclo=self.ciclo,
        )
        r = self.admin_client.patch(f'{self.base_url}matriculas/{m.id}/',
            {'estado': 'FINALIZADA'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_destroy_admin(self):
        """Valida que un administrador pueda eliminar una matrícula (204 NO CONTENT)"""
        m = Matricula.objects.create(
            estudiante_id=self.estudiante.id, carrera=self.carrera, ciclo=self.ciclo,
        )
        r = self.admin_client.delete(f'{self.base_url}matriculas/{m.id}/')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

    def test_filtrar_por_estudiante(self):
        """Valida que el filtro por estudiante_id en matrículas funcione correctamente"""
        r = self.admin_client.get(f'{self.base_url}matriculas/?estudiante_id={self.estudiante.id}')
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class MisMateriasTest(AcademicoAPIBase):
    def test_mis_materias_estudiante_sin_matricula(self):
        """Valida que un estudiante sin matrícula reciba 404 al consultar sus materias"""
        r = self.estudiante_client.get(f'{self.base_url}matriculas/mis_materias/')
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    @patch('apps.academico.views.AsistenciaModel')
    @patch('apps.academico.views.RegistroFacialModel')
    def test_mis_materias_estudiante_con_matricula(self, mock_rostro, mock_asistencia):
        """Valida que un estudiante con matrícula activa pueda ver sus materias y estado facial"""
        mock_asistencia.objects.filter.return_value.first.return_value = None
        mock_rostro.objects.filter.return_value.exists.return_value = True

        Matricula.objects.create(
            estudiante_id=self.estudiante.id, carrera=self.carrera, ciclo=self.ciclo,
        )
        h = Horario.objects.create(
            dia_semana='LUNES', hora_inicio=time(8, 0), hora_fin=time(10, 0),
            materia=self.materia,
        )

        with patch('apps.academico.views.datetime') as mock_dt:
            mock_dt.now.return_value.weekday.return_value = 0
            mock_dt.now.return_value.date.return_value = date.today()
            r = self.estudiante_client.get(f'{self.base_url}matriculas/mis_materias/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('matriculas', r.data)
        self.assertIn('tiene_registro_facial', r.data)
        self.assertTrue(r.data['tiene_registro_facial'])

    def test_mis_materias_admin(self):
        """Valida que un administrador no pueda acceder al endpoint mis_materias (403 FORBIDDEN)"""
        r = self.admin_client.get(f'{self.base_url}matriculas/mis_materias/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_mis_materias_sin_auth(self):
        """Valida que un usuario no autenticado reciba 401 al consultar mis_materias"""
        r = self.client.get(f'{self.base_url}matriculas/mis_materias/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('apps.academico.views.AsistenciaModel')
    @patch('apps.academico.views.RegistroFacialModel')
    def test_mis_materias_con_asistencia_registrada(self, mock_rostro, mock_asistencia):
        """Valida que la respuesta incluya ya_registro y asistencia_id cuando ya se registró asistencia"""
        mock_asistencia_obj = Mock()
        mock_asistencia_obj.id = 1
        mock_asistencia_obj.estado = 'PRESENTE'
        mock_asistencia.objects.filter.return_value.first.return_value = mock_asistencia_obj
        mock_rostro.objects.filter.return_value.exists.return_value = False

        Matricula.objects.create(
            estudiante_id=self.estudiante.id, carrera=self.carrera, ciclo=self.ciclo,
        )
        Horario.objects.create(
            dia_semana='LUNES', hora_inicio=time(8, 0), hora_fin=time(10, 0),
            materia=self.materia,
        )

        with patch('apps.academico.views.datetime') as mock_dt:
            mock_dt.now.return_value.weekday.return_value = 0
            mock_dt.now.return_value.date.return_value = date.today()
            r = self.estudiante_client.get(f'{self.base_url}matriculas/mis_materias/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        matricula_data = r.data['matriculas'][0]
        materia_data = matricula_data['materias'][0]
        horario_data = materia_data['horarios_hoy'][0]
        self.assertTrue(horario_data['ya_registro'])
        self.assertEqual(horario_data['asistencia_id'], 1)
        self.assertEqual(horario_data['estado_asistencia'], 'PRESENTE')

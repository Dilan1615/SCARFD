from datetime import date, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError

from .models import Carrera, Ciclo, Materia, Horario, Matricula


class CarreraModelTest(TestCase):
    def test_creacion_carrera(self):
        carrera = Carrera.objects.create(
            codigo="ISW",
            nombre="Ingeniería de Software",
            duracion=9,
            modalidad="PRESENCIAL",
        )
        self.assertEqual(str(carrera), "Ingeniería de Software")


class CicloModelTest(TestCase):
    def setUp(self):
        self.carrera = Carrera.objects.create(
            codigo="ISW", nombre="Ing. Software", duracion=9, modalidad="PRESENCIAL"
        )

    def test_ciclo_activo(self):
        ciclo = Ciclo.objects.create(
            num=1,
            fecha_inicio=date.today() - timedelta(days=5),
            fecha_fin=date.today() + timedelta(days=90),
            estado="ACTIVO",
            carrera=self.carrera,
        )
        self.assertTrue(ciclo.esta_activo())

    def test_ciclo_no_activo_por_fechas(self):
        ciclo = Ciclo.objects.create(
            num=2,
            fecha_inicio=date.today() - timedelta(days=200),
            fecha_fin=date.today() - timedelta(days=100),
            estado="ACTIVO",
            carrera=self.carrera,
        )
        self.assertFalse(ciclo.esta_activo())


class HorarioModelTest(TestCase):
    def setUp(self):
        carrera = Carrera.objects.create(
            codigo="ISW", nombre="Ing. Software", duracion=9, modalidad="PRESENCIAL"
        )
        ciclo = Ciclo.objects.create(
            num=1, fecha_inicio=date.today(), fecha_fin=date.today() + timedelta(days=90),
            carrera=carrera,
        )
        self.materia = Materia.objects.create(
            codigo="MAT101", nombre="Programación I", creditos=4,
            horas_semanales=4, carrera=carrera, ciclo=ciclo,
        )

    def test_hora_valida(self):
        horario = Horario(
            dia_semana="LUNES", hora_inicio="08:00", hora_fin="10:00",
            materia=self.materia,
        )
        self.assertTrue(horario.es_hora_valida())

    def test_hora_invalida(self):
        horario = Horario(
            dia_semana="LUNES", hora_inicio="10:00", hora_fin="08:00",
            materia=self.materia,
        )
        self.assertFalse(horario.es_hora_valida())

    def test_horario_solapado_lanza_error(self):
        Horario.objects.create(
            dia_semana="MARTES", hora_inicio="08:00", hora_fin="10:00",
            materia=self.materia,
        )
        solapado = Horario(
            dia_semana="MARTES", hora_inicio="09:00", hora_fin="11:00",
            materia=self.materia,
        )
        with self.assertRaises(ValidationError):
            solapado.clean()


class MatriculaModelTest(TestCase):
    def test_matricula_unica_por_ciclo(self):
        carrera = Carrera.objects.create(
            codigo="ISW", nombre="Ing. Software", duracion=9, modalidad="PRESENCIAL"
        )
        ciclo = Ciclo.objects.create(
            num=1, fecha_inicio=date.today(), fecha_fin=date.today() + timedelta(days=90),
            carrera=carrera,
        )
        Matricula.objects.create(estudiante_id=1, carrera=carrera, ciclo=ciclo)
        with self.assertRaises(Exception):
            Matricula.objects.create(estudiante_id=1, carrera=carrera, ciclo=ciclo)
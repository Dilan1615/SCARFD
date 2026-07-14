from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from .models import Usuario, PasswordResetToken


class UsuarioModelTest(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email="estudiante@unl.edu.ec",
            password="ClaveSegura1!",
            cedula="1103456789",
            first_name="Ana",
            last_name="Torres",
        )

    def test_usuario_creado_correctamente(self):
        self.assertEqual(self.usuario.email, "estudiante@unl.edu.ec")
        self.assertEqual(self.usuario.rol, "ESTUDIANTE")
        self.assertTrue(self.usuario.check_password("ClaveSegura1!"))

    def test_str_representation(self):
        self.assertIn(self.usuario.email, str(self.usuario))

    def test_bloqueo_por_intentos_fallidos(self):
        self.usuario.intentos_fallidos = 5
        self.usuario.save()
        self.assertTrue(self.usuario.esta_bloqueado())
        self.assertIsNotNone(self.usuario.bloqueado_hasta)


class RegistroAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/usuario/usuarios/register/"

    def test_registro_exitoso(self):
        data = {
            "email": "nuevo@unl.edu.ec",
            "password": "Segura123!",
            "cedula": "1104567890",
            "first_name": "Luis",
            "last_name": "Pardo",
            "rol": "ESTUDIANTE",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Usuario.objects.filter(email="nuevo@unl.edu.ec").exists())

    def test_registro_password_debil_falla(self):
        data = {
            "email": "otro@unl.edu.ec",
            "password": "clavesimple",
            "cedula": "1105678901",
            "first_name": "Maria",
            "last_name": "Diaz",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/usuario/token/"
        self.usuario = Usuario.objects.create_user(
            email="login@unl.edu.ec",
            password="ClaveSegura1!",
            cedula="1106789012",
        )

    def test_login_exitoso(self):
        response = self.client.post(
            self.url,
            {"email": "login@unl.edu.ec", "password": "ClaveSegura1!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_login_credenciales_invalidas(self):
        response = self.client.post(
            self.url,
            {"email": "login@unl.edu.ec", "password": "incorrecta"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.intentos_fallidos, 1)
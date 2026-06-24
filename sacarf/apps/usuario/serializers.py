from rest_framework import serializers
from .models import Usuario, Estudiante, Docente


class UsuarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "cedula",
            "telefono"
        ]


class EstudianteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Estudiante
        fields = "__all__"


class DocenteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Docente
        fields = "__all__"
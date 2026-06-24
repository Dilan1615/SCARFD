# serializers.py

from rest_framework import serializers
from .models import Carrera, Ciclo, Materia, Curso, Horario


class CarreraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrera
        fields = "__all__"


class CicloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ciclo
        fields = "__all__"


class MateriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materia
        fields = "__all__"


class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = "__all__"


class HorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Horario
        fields = "__all__"
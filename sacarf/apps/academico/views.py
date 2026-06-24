# views.py

from rest_framework.viewsets import ModelViewSet

from .models import (Carrera,Ciclo,Materia,Curso,Horario)

from .serializers import (CarreraSerializer,CicloSerializer,MateriaSerializer,CursoSerializer,HorarioSerializer)


class CarreraViewSet(ModelViewSet):
    queryset = Carrera.objects.all()
    serializer_class = CarreraSerializer


class CicloViewSet(ModelViewSet):
    queryset = Ciclo.objects.all()
    serializer_class = CicloSerializer


class MateriaViewSet(ModelViewSet):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer


class CursoViewSet(ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer


class HorarioViewSet(ModelViewSet):
    queryset = Horario.objects.all()
    serializer_class = HorarioSerializer
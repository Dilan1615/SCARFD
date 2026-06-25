from rest_framework import viewsets, filters

from .models import Carrera, Ciclo, Materia, Horario
from .serializers import CarreraSerializer, CicloSerializer, MateriaSerializer, HorarioSerializer
from apps.usuario.permissions import IsAdminForMutation


class CarreraViewSet(viewsets.ModelViewSet):
    queryset = Carrera.objects.all()
    serializer_class = CarreraSerializer
    permission_classes = [IsAdminForMutation]
    search_fields = ['nombre', 'codigo']
    filterset_fields = ['modalidad']


class CicloViewSet(viewsets.ModelViewSet):
    queryset = Ciclo.objects.all()
    serializer_class = CicloSerializer
    permission_classes = [IsAdminForMutation]
    filterset_fields = ['carrera', 'estado']


class MateriaViewSet(viewsets.ModelViewSet):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer
    permission_classes = [IsAdminForMutation]
    search_fields = ['nombre', 'codigo']
    filterset_fields = ['carrera', 'ciclo', 'docente']


class HorarioViewSet(viewsets.ModelViewSet):
    queryset = Horario.objects.all()
    serializer_class = HorarioSerializer
    permission_classes = [IsAdminForMutation]
    filterset_fields = ['materia', 'dia_semana']

from rest_framework.viewsets import ModelViewSet
from .models import Estudiante, Docente
from .serializers import (
    EstudianteSerializer,
    DocenteSerializer
)


class EstudianteViewSet(ModelViewSet):

    queryset = Estudiante.objects.all()
    serializer_class = EstudianteSerializer



class DocenteViewSet(ModelViewSet):

    queryset = Docente.objects.all()
    serializer_class = DocenteSerializer
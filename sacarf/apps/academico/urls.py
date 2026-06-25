from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CarreraViewSet, CicloViewSet, MateriaViewSet, HorarioViewSet

router = DefaultRouter()
router.register(r'carreras', CarreraViewSet, basename='carrera')
router.register(r'ciclos', CicloViewSet, basename='ciclo')
router.register(r'materias', MateriaViewSet, basename='materia')
router.register(r'horarios', HorarioViewSet, basename='horario')

urlpatterns = [
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AsistenciaViewSet, JustificacionViewSet, 
    ReconocimientoViewSet, RegistroFacialViewSet
)

router = DefaultRouter()
router.register(r'asistencias', AsistenciaViewSet, basename='asistencia')
router.register(r'justificaciones', JustificacionViewSet, basename='justificacion')
router.register(r'reconocimientos', ReconocimientoViewSet, basename='reconocimiento')
router.register(r'registro-facial', RegistroFacialViewSet, basename='registro-facial')

urlpatterns = [
    path('', include(router.urls)),
]
from rest_framework.routers import DefaultRouter
from .views import (
    CarreraViewSet,
    CicloViewSet,
    MateriaViewSet,
    CursoViewSet,
    HorarioViewSet
)

router = DefaultRouter()

router.register(r"carreras", CarreraViewSet)
router.register(r"ciclos", CicloViewSet)
router.register(r"materias", MateriaViewSet)
router.register(r"cursos", CursoViewSet)
router.register(r"horarios", HorarioViewSet)

urlpatterns = router.urls
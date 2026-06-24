from rest_framework.routers import DefaultRouter
from .views import (EstudianteViewSet,DocenteViewSet)


router = DefaultRouter()

router.register("estudiantes",EstudianteViewSet)

router.register("docentes",DocenteViewSet)


urlpatterns = router.urls
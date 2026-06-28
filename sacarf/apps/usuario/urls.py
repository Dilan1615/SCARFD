from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UsuarioViewSet
from .login_view import login_view

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')

urlpatterns = [
    path('token/', login_view, name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('usuarios/solicitar-restablecimiento/', UsuarioViewSet.as_view({'post': 'solicitar_restablecimiento'}), name='solicitar-restablecimiento'),
    path('usuarios/restablecer-password/', UsuarioViewSet.as_view({'post': 'restablecer_password'}), name='restablecer-password'),
    path('', include(router.urls)),
]

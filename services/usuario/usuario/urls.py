from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="SACARF API - Usuario",
        default_version='v1',
        description="Sistema de Asistencia con Reconocimiento Facial - Servicio de Usuario",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/usuario/', include('apps.usuario.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # ── Monitoreo (nuevo) ────────────────────────────────────────────
    path('health/', lambda request: JsonResponse({'status': 'ok', 'service': 'usuario'})),

    path('', include('django_prometheus.urls')),  # expone /metrics

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

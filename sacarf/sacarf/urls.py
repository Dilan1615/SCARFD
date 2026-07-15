import os
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

SERVICE_NAME = os.environ.get('SERVICE_NAME', 'all')

schema_view = get_schema_view(
    openapi.Info(
        title="SACARF API",
        default_version='v1',
        description="Sistema de Asistencia con Reconocimiento Facial",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
]

if SERVICE_NAME in ('all', 'usuario'):
    urlpatterns += [
        path('api/usuario/', include('apps.usuario.urls')),
    ]

if SERVICE_NAME in ('all', 'academico'):
    urlpatterns += [
        path('api/academico/', include('apps.academico.urls')),
    ]

if SERVICE_NAME in ('all', 'asistencia'):
    urlpatterns += [
        path('api/asistencia/', include('apps.asistencia.urls')),
    ]

if SERVICE_NAME in ('all', 'reportes'):
    urlpatterns += [
        path('api/reportes/', include('apps.reportes.urls')),
    ]

if SERVICE_NAME in ('all', 'monitoring'):
    urlpatterns += [
        path('api/monitoring/', include('apps.monitoring.urls')),
    ]

if SERVICE_NAME in ('all', 'usuario'):
    urlpatterns += [
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

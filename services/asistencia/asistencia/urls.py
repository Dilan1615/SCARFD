from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/asistencia/', include('apps.asistencia.urls')),
    path('health/', lambda request: JsonResponse({'status': 'ok', 'service': 'asistencia'})),
    path('', include('django_prometheus.urls')),  # expone /metrics
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

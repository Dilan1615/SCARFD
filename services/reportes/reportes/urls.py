from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/reportes/', include('apps.reportes.urls')),
    # ── Monitoreo (nuevo) ────────────────────────────────────────────
    path('health/', lambda request: JsonResponse({'status': 'ok', 'service': 'reportes'})),
<<<<<<< HEAD
=======
    path('', include('django_prometheus.urls')),  # expone /metrics
>>>>>>> moduloJustificacion
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

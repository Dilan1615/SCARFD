from django.urls import include, path

urlpatterns = [
    path('api/monitoring/', include('apps.monitoring.urls')),
<<<<<<< HEAD
=======
    # Métricas nativas de este mismo servicio (para que Prometheus también
    # se auto-monitoree si se desea)
    path('', include('django_prometheus.urls')),
>>>>>>> moduloJustificacion
]

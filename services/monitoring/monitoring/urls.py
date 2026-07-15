from django.urls import include, path

urlpatterns = [
    path('api/monitoring/', include('apps.monitoring.urls')),
]

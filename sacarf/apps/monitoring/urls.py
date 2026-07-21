from django.urls import path
from . import views

urlpatterns = [
    path('salud/', views.estado_servicios, name='monitoring-salud'),
    path('infraestructura/', views.infraestructura, name='monitoring-infra'),
    path('backend/', views.backend_metrics, name='monitoring-backend'),
    path('base-datos/', views.base_datos, name='monitoring-bd'),
    path('negocio/', views.negocio, name='monitoring-negocio'),
    path('resumen/', views.resumen, name='monitoring-resumen'),
    path('health/', views.health, name='monitoring-health'),

    # ── Auditoría ────────────────────────────────────────────────────
    path('auditoria/', views.RegistroAuditoriaListView.as_view(), name='monitoring-auditoria'),
    path('auditoria/resumen/', views.auditoria_resumen, name='monitoring-auditoria-resumen'),

]

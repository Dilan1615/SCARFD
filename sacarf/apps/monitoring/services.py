"""
Capa de servicios del monitoring-service.

Este microservicio NO tiene modelos propios "de negocio": su trabajo es
1) consultar Prometheus (infraestructura + backend HTTP + Postgres exporter)
2) hacer ping directo a los otros microservicios (estado activo/caído)
3) leer los modelos `shared` (misma base de datos, managed=False) para las
   métricas de negocio de SACARF (usuarios, asistencias, reconocimientos, reportes)

Todo queda expuesto como JSON simple para que el frontend React no tenga que
hablar PromQL en ningún momento.
"""
import os
import time
import requests
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

PROMETHEUS_URL = os.getenv('PROMETHEUS_URL', 'http://prometheus:9090')
PROM_TIMEOUT = float(os.getenv('PROMETHEUS_TIMEOUT', '4'))
HEALTHCHECK_TIMEOUT = float(os.getenv('MONITORING_HEALTHCHECK_TIMEOUT', '3'))

# Microservicios registrados de SACARF: nombre visible -> (host docker, puerto, path de salud)
SERVICIOS = {
    'usuario': {'host': 'usuario-service', 'port': 8001, 'health_path': '/health/'},
    'academico': {'host': 'academico-service', 'port': 8002, 'health_path': '/health/'},
    'asistencia': {'host': 'asistencia-service', 'port': 8003, 'health_path': '/health/'},
    'reportes': {'host': 'reportes-service', 'port': 8004, 'health_path': '/health/'},
}


# ──────────────────────────────────────────────────────────────────────────
# Cliente Prometheus (HTTP API nativo, sin dependencias extra)
# ──────────────────────────────────────────────────────────────────────────
class PrometheusClient:
    def __init__(self, base_url=PROMETHEUS_URL, timeout=PROM_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout

    def query(self, promql):
        """Consulta instantánea. Retorna lista de resultados crudos de Prometheus."""
        try:
            resp = requests.get(
                f'{self.base_url}/api/v1/query',
                params={'query': promql},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get('status') != 'success':
                return []
            return data['data']['result']
        except requests.RequestException:
            return []

    def query_scalar(self, promql, default=0.0):
        """Devuelve el primer valor numérico de una query, o `default` si no hay datos."""
        result = self.query(promql)
        if not result:
            return default
        try:
            return round(float(result[0]['value'][1]), 2)
        except (KeyError, IndexError, ValueError, TypeError):
            return default

    def query_vector(self, promql, label_key='instance'):
        """Devuelve {label: valor} para queries con múltiples series (ej. por servicio)."""
        result = self.query(promql)
        out = {}
        for item in result:
            label = item.get('metric', {}).get(label_key, 'desconocido')
            try:
                out[label] = round(float(item['value'][1]), 2)
            except (KeyError, IndexError, ValueError, TypeError):
                continue
        return out

    def query_range(self, promql, minutes=30, step='30s'):
        """Serie temporal para gráficos de línea. Retorna lista de {timestamp, value}."""
        end = time.time()
        start = end - minutes * 60
        try:
            resp = requests.get(
                f'{self.base_url}/api/v1/query_range',
                params={'query': promql, 'start': start, 'end': end, 'step': step},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get('status') != 'success' or not data['data']['result']:
                return []
            values = data['data']['result'][0]['values']
            return [{'timestamp': int(ts), 'valor': round(float(v), 2)} for ts, v in values]
        except (requests.RequestException, KeyError, IndexError, ValueError):
            return []


prom = PrometheusClient()


# ──────────────────────────────────────────────────────────────────────────
# Estado de los microservicios (activo / caído / tiempo de respuesta)
# ──────────────────────────────────────────────────────────────────────────
def _check_one(nombre, cfg):
    url = f"http://{cfg['host']}:{cfg['port']}{cfg['health_path']}"
    inicio = time.perf_counter()
    try:
        resp = requests.get(url, timeout=HEALTHCHECK_TIMEOUT)
        tiempo_ms = round((time.perf_counter() - inicio) * 1000, 1)
        estado = 'activo' if resp.status_code < 500 else 'caido'
    except requests.RequestException:
        tiempo_ms = round((time.perf_counter() - inicio) * 1000, 1)
        estado = 'caido'
    return {
        'servicio': nombre,
        'estado': estado,
        'tiempo_respuesta_ms': tiempo_ms,
        'puerto': cfg['port'],
    }


def obtener_estado_servicios():
    resultados = []
    with ThreadPoolExecutor(max_workers=len(SERVICIOS)) as pool:
        futuros = [pool.submit(_check_one, nombre, cfg) for nombre, cfg in SERVICIOS.items()]
        for f in as_completed(futuros):
            resultados.append(f.result())
    orden = {n: i for i, n in enumerate(SERVICIOS)}
    resultados.sort(key=lambda r: orden.get(r['servicio'], 99))
    return resultados


# ──────────────────────────────────────────────────────────────────────────
# Infraestructura: CPU, RAM, disco (node-exporter) + contenedores (cAdvisor)
# ──────────────────────────────────────────────────────────────────────────
def obtener_infraestructura():
    cpu_percent = prom.query_scalar(
        '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'
    )
    ram_percent = prom.query_scalar(
        '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
    )
    disk_percent = prom.query_scalar(
        '(1 - (node_filesystem_avail_bytes{mountpoint="/"} '
        '/ node_filesystem_size_bytes{mountpoint="/"})) * 100'
    )

    # Contenedores "sacarf_*" vistos por cAdvisor en los últimos 30s => corriendo
    contenedores_raw = prom.query(
        'time() - container_last_seen{name=~"sacarf_.*"} < 30'
    )
    contenedores = []
    nombres_vistos = set()
    for item in contenedores_raw:
        nombre = item.get('metric', {}).get('name', 'desconocido')
        if nombre in nombres_vistos:
            continue
        nombres_vistos.add(nombre)
        contenedores.append({'nombre': nombre, 'estado': 'corriendo'})

    for nombre_esperado in [
        'sacarf_db', 'sacarf_usuario', 'sacarf_academico', 'sacarf_asistencia',
        'sacarf_reportes', 'sacarf_gateway', 'sacarf_monitoring',
        'sacarf_prometheus', 'sacarf_node_exporter', 'sacarf_cadvisor',
        'sacarf_postgres_exporter',
    ]:
        if nombre_esperado not in nombres_vistos:
            contenedores.append({'nombre': nombre_esperado, 'estado': 'detenido'})

    return {
        'cpu_percent': cpu_percent,
        'ram_percent': ram_percent,
        'disco_percent': disk_percent,
        'contenedores': contenedores,
    }


# ──────────────────────────────────────────────────────────────────────────
# Backend: peticiones/min, tiempo de respuesta, errores 4xx/5xx, por servicio
# (usa las métricas expuestas por django-prometheus en cada microservicio)
# ──────────────────────────────────────────────────────────────────────────
def obtener_metricas_backend(rango_minutos=30):
    peticiones_por_minuto = prom.query_scalar(
        'sum(rate(django_http_requests_total_by_view_transport_method_total[1m])) * 60'
    )

    suma_latencia = prom.query_scalar(
        'sum(rate(django_http_requests_latency_seconds_by_view_method_sum[5m]))'
    )
    conteo_latencia = prom.query_scalar(
        'sum(rate(django_http_requests_latency_seconds_by_view_method_count[5m]))'
    )
    tiempo_promedio_ms = round((suma_latencia / conteo_latencia) * 1000, 1) if conteo_latencia else 0.0

    errores_4xx = prom.query_scalar(
        'sum(rate(django_http_responses_total_by_status_total{status=~"4.."}[5m])) * 60'
    )
    errores_5xx = prom.query_scalar(
        'sum(rate(django_http_responses_total_by_status_total{status=~"5.."}[5m])) * 60'
    )

    peticiones_por_servicio_raw = prom.query_vector(
        'sum by (job) (rate(django_http_requests_total_by_view_transport_method_total[5m])) * 60',
        label_key='job',
    )
    peticiones_por_servicio = [
        {'servicio': job, 'peticiones_por_minuto': valor}
        for job, valor in peticiones_por_servicio_raw.items()
    ]

    serie_peticiones = prom.query_range(
        'sum(rate(django_http_requests_total_by_view_transport_method_total[1m])) * 60',
        minutes=rango_minutos,
    )
    serie_tiempo_respuesta = prom.query_range(
        '(sum(rate(django_http_requests_latency_seconds_by_view_method_sum[5m])) '
        '/ sum(rate(django_http_requests_latency_seconds_by_view_method_count[5m]))) * 1000',
        minutes=rango_minutos,
    )

    return {
        'peticiones_por_minuto': peticiones_por_minuto,
        'tiempo_promedio_respuesta_ms': tiempo_promedio_ms,
        'errores_4xx_por_minuto': errores_4xx,
        'errores_5xx_por_minuto': errores_5xx,
        'peticiones_por_microservicio': peticiones_por_servicio,
        'serie_peticiones_por_minuto': serie_peticiones,
        'serie_tiempo_respuesta_ms': serie_tiempo_respuesta,
    }


# ──────────────────────────────────────────────────────────────────────────
# Base de datos: conexiones activas, consultas, almacenamiento (postgres_exporter)
# ──────────────────────────────────────────────────────────────────────────
def obtener_metricas_bd():
    conexiones_activas = prom.query_scalar(
        'sum(pg_stat_activity_count{datname="sacarf_db"})'
    )
    consultas_por_segundo = prom.query_scalar(
        'sum(rate(pg_stat_database_xact_commit{datname="sacarf_db"}[5m])) '
        '+ sum(rate(pg_stat_database_xact_rollback{datname="sacarf_db"}[5m]))'
    )
    tamano_bytes = prom.query_scalar(
        'pg_database_size_bytes{datname="sacarf_db"}'
    )
    tamano_mb = round(tamano_bytes / (1024 * 1024), 2) if tamano_bytes else 0.0

    return {
        'conexiones_activas': conexiones_activas,
        'consultas_por_segundo': round(consultas_por_segundo, 2),
        'almacenamiento_mb': tamano_mb,
    }


# ──────────────────────────────────────────────────────────────────────────
# Métricas de negocio SACARF (consulta directa a modelos `shared`, misma BD)
# ──────────────────────────────────────────────────────────────────────────
def obtener_metricas_negocio():
    from shared.models import Usuario, AsistenciaModel, ReporteModel
    try:
        from shared.models import ReconocimientoModel
    except ImportError:
        ReconocimientoModel = None

    hoy = date.today()

    total_usuarios = Usuario.objects.count()
    asistencias_hoy = AsistenciaModel.objects.filter(fecha=hoy).count()
    reportes_generados = ReporteModel.objects.count()

    if ReconocimientoModel is not None:
        reconocimientos_exitosos = ReconocimientoModel.objects.filter(
            resultado=True, fecha_hora__date=hoy
        ).count()
        reconocimientos_fallidos = ReconocimientoModel.objects.filter(
            resultado=False, fecha_hora__date=hoy
        ).count()
    else:
        # shared.models aún no tiene ReconocimientoModel — ver docs/GUIA_IMPLEMENTACION.md
        reconocimientos_exitosos = None
        reconocimientos_fallidos = None

    return {
        'total_usuarios': total_usuarios,
        'asistencias_hoy': asistencias_hoy,
        'reconocimientos_exitosos_hoy': reconocimientos_exitosos,
        'reconocimientos_fallidos_hoy': reconocimientos_fallidos,
        'reportes_generados': reportes_generados,
    }

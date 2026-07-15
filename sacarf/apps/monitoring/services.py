"""
Capa de servicios del monitoring-service.

Reemplaza a prometheus + node-exporter + cadvisor + postgres-exporter:

  - CPU / RAM / disco  → psutil (monta /proc, /sys, / del host)
  - Contenedores Docker → SDK oficial (monta docker.sock)
  - PostgreSQL          → SQL directa vía psycopg2
  - Salud de servicios  → HTTP ping a /health/ de cada microservicio
  - Métricas de negocio → ORM Django (misma base de datos)
"""
import os
import time
import logging
import requests
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import psutil
import docker
import psycopg2

logger = logging.getLogger('sacarf.monitoring')

HEALTHCHECK_TIMEOUT = float(os.getenv('MONITORING_HEALTHCHECK_TIMEOUT', '3'))

SERVICIOS = {
    'usuario':   {'host': 'usuario-service',   'port': 8001, 'health_path': '/health/'},
    'academico': {'host': 'academico-service',  'port': 8002, 'health_path': '/health/'},
    'asistencia':{'host': 'asistencia-service', 'port': 8003, 'health_path': '/health/'},
    'reportes':  {'host': 'reportes-service',   'port': 8004, 'health_path': '/health/'},
}


# ── Health-check paralelo ─────────────────────────────────────────────
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
        futuros = [pool.submit(_check_one, n, c) for n, c in SERVICIOS.items()]
        for f in as_completed(futuros):
            resultados.append(f.result())
    orden = {n: i for i, n in enumerate(SERVICIOS)}
    resultados.sort(key=lambda r: orden.get(r['servicio'], 99))
    return resultados


# ── Infraestructura: psutil + Docker SDK ───────────────────────────────
def _docker_client():
    try:
        return docker.from_env()
    except docker.errors.DockerException:
        return None


def obtener_infraestructura():
    cpu_percent = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    ram_percent = round(mem.percent, 1)
    disk = psutil.disk_usage('/')
    disco_percent = round(disk.percent, 1)

    # Solo contenedores SACARF (que empiecen con "sacarf_")
    contenedores = []
    client = _docker_client()
    if client is not None:
        try:
            for c in client.containers.list(all=True):
                if c.name.startswith('sacarf_'):
                    contenedores.append({
                        'nombre': c.name,
                        'estado': 'corriendo' if c.status == 'running' else 'detenido',
                    })
        except docker.errors.DockerException as e:
            logger.warning("No se pudieron listar contenedores Docker: %s", e)

    if not contenedores:
        contenedores.append({'nombre': 'sacarf_monitoring', 'estado': 'corriendo'})

    return {
        'cpu_percent': cpu_percent,
        'ram_percent': ram_percent,
        'disco_percent': disco_percent,
        'contenedores': contenedores,
    }


# ── Conexión directa a PostgreSQL ─────────────────────────────────────
def _db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'sacarf_db'),
        user=os.getenv('DB_USER', 'sacarf_user'),
        password=os.getenv('DB_PASSWORD', ''),
        host=os.getenv('DB_HOST', 'db'),
        port=os.getenv('DB_PORT', '5432'),
    )


# ── Backend: métricas desde tabla de auditoría ────────────────────────
def obtener_metricas_backend(rango_minutos=30):
    try:
        conn = _db_connection()
        cur = conn.cursor()

        # Conteo por servicio (para bar chart)
        cur.execute("""
            SELECT servicio, COUNT(*) AS registros
            FROM monitoring_registroauditoria
            GROUP BY servicio
        """)
        peticiones_por_microservicio = [
            {'servicio': row[0], 'peticiones_por_minuto': row[1]}
            for row in cur.fetchall()
        ]

        # Conteo reciente por minuto (para line chart)
        cur.execute("""
            SELECT
                date_trunc('minute', fecha_hora) AS minuto,
                COUNT(*) AS cantidad
            FROM monitoring_registroauditoria
            WHERE fecha_hora >= NOW() - INTERVAL %s
            GROUP BY minuto
            ORDER BY minuto
        """, (f'{rango_minutos} minutes',))
        serie_registros = [
            {'timestamp': int(row[0].timestamp()), 'valor': row[1]}
            for row in cur.fetchall()
        ]

        # Total reciente y tasa por minuto
        total_reciente = sum(item['valor'] for item in serie_registros)
        peticiones_por_minuto = round(total_reciente / max(rango_minutos, 1), 1)

        # Errores 4xx/5xx — sin middleware no tenemos datos reales
        cur.close()
        conn.close()

        return {
            'peticiones_por_minuto': peticiones_por_minuto,
            'tiempo_promedio_respuesta_ms': 0.0,
            'errores_4xx_por_minuto': 0,
            'errores_5xx_por_minuto': 0,
            'peticiones_por_microservicio': peticiones_por_microservicio,
            'serie_peticiones_por_minuto': serie_registros,
            'serie_tiempo_respuesta_ms': [],
        }
    except Exception as e:
        logger.exception("Error obteniendo métricas de backend")
        return {
            'peticiones_por_minuto': 0,
            'tiempo_promedio_respuesta_ms': 0.0,
            'errores_4xx_por_minuto': 0,
            'errores_5xx_por_minuto': 0,
            'peticiones_por_microservicio': [],
            'serie_peticiones_por_minuto': [],
            'serie_tiempo_respuesta_ms': [],
        }


# ── Base de datos: SQL directa ────────────────────────────────────────
def obtener_metricas_bd():
    try:
        conn = _db_connection()
        cur = conn.cursor()
        db_name = os.getenv('DB_NAME', 'sacarf_db')

        # Conexiones activas
        cur.execute("""
            SELECT COUNT(*)
            FROM pg_stat_activity
            WHERE datname = %s AND state = 'active'
        """, (db_name,))
        conexiones_activas = cur.fetchone()[0]

        # Tasa de transacciones (diferencia de contadores)
        cur.execute("""
            SELECT xact_commit + xact_rollback
            FROM pg_stat_database
            WHERE datname = %s
        """, (db_name,))
        row = cur.fetchone()
        total_transacciones = row[0] if row else 0

        # Guardar snapshot y calcular tasa en la segunda consulta
        # Para simplificar, tomamos una instantánea
        cur.execute("SELECT pg_postmaster_start_time()")
        inicio = cur.fetchone()[0]
        cur.execute("SELECT NOW()")
        ahora = cur.fetchone()[0]
        segundos_activos = max((ahora - inicio).total_seconds(), 1)
        consultas_por_segundo = round(total_transacciones / segundos_activos, 2)

        # Tamaño de la base de datos
        cur.execute("SELECT pg_database_size(%s)", (db_name,))
        tamano_bytes = cur.fetchone()[0]
        tamano_mb = round(tamano_bytes / (1024 * 1024), 2) if tamano_bytes else 0.0

        cur.close()
        conn.close()

        return {
            'conexiones_activas': conexiones_activas,
            'consultas_por_segundo': consultas_por_segundo,
            'almacenamiento_mb': tamano_mb,
        }
    except Exception as e:
        logger.exception("Error obteniendo métricas de base de datos")
        return {
            'conexiones_activas': 0,
            'consultas_por_segundo': 0,
            'almacenamiento_mb': 0.0,
        }


# ── Métricas de negocio (ORM Django) ──────────────────────────────────
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
        reconocimientos_exitosos = None
        reconocimientos_fallidos = None

    return {
        'total_usuarios': total_usuarios,
        'asistencias_hoy': asistencias_hoy,
        'reconocimientos_exitosos_hoy': reconocimientos_exitosos,
        'reconocimientos_fallidos_hoy': reconocimientos_fallidos,
        'reportes_generados': reportes_generados,
    }

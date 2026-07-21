#!/bin/bash
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-all}"
SERVICE_PORT="${SERVICE_PORT:-8000}"
DEBUG="${DEBUG:-True}"

# ── Colores para logs ──────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()   { echo -e "${GREEN}[INIT]${NC} $1"; }
warn()  { echo -e "${YELLOW}[INIT]${NC} $1"; }
error() { echo -e "${RED}[INIT]${NC} $1" >&2; }

# ── Utilidad: esperar a que PostgreSQL esté listo ──────────────────────
wait_for_db() {
    log "Verificando conexión a PostgreSQL..."
    local retries=30
    while [ $retries -gt 0 ]; do
        if python -c "
import os, sys
import psycopg2
try:
    psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'sacarf_db'),
        user=os.getenv('DB_USER', 'sacarf_user'),
        password=os.getenv('DB_PASSWORD', ''),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
    ).close()
except Exception:
    sys.exit(1)
" 2>/dev/null; then
            log "PostgreSQL listo."
            return 0
        fi
        retries=$((retries - 1))
        sleep 1
    done
    error "PostgreSQL no respondió tras 30 intentos."
    exit 1
}

# ═══════════════════════════════════════════════════════════════════════
#  CONTENEDOR init: Migraciones + superusuario + collectstatic
# ═══════════════════════════════════════════════════════════════════════
if [ "$SERVICE_NAME" = "init" ]; then
    log "=== MODO INIT ==="
    log "SERVICE_NAME=$SERVICE_NAME  DEBUG=$DEBUG"

    wait_for_db

    # ── 1. Migraciones ────────────────────────────────────────────────
    log "Aplicando migraciones..."
    python sacarf/manage.py migrate --noinput 2>&1
    log "Migraciones completadas."

    # ── 2. makemigrations solo en modo DEBUG (desarrollo) ─────────────
    if [ "$DEBUG" = "True" ]; then
        log "Modo DEBUG: verificando migraciones pendientes..."
        python sacarf/manage.py makemigrations --check --noinput 2>&1 || {
            warn "Hay cambios de modelo sin migración. Generando..."
            python sacarf/manage.py makemigrations --noinput 2>&1
            log "Migraciones generadas. Re-aplicando..."
            python sacarf/manage.py migrate --noinput 2>&1
        }
    else
        log "Modo PRODUCCIÓN: makemigrations omitido (las migraciones deben estar en el repo)."
    fi

    # ── 3. Superusuario por defecto ───────────────────────────────────
    log "Verificando superusuario admin..."
    python sacarf/manage.py shell -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sacarf.settings')
django.setup()

from apps.usuario.models import Usuario
email = 'admin@sacarf.com'
if not Usuario.objects.filter(email=email).exists():
    Usuario.objects.create_superuser(
        email=email,
        password='admin123',
        cedula='0000000000',
        rol='ADMIN',
    )
    print(f'Superusuario {email} creado.')
else:

    print(f'Superusuario {email} ya existe.')
" 2>&1

    # ── 4. Collectstatic (producción) ─────────────────────────────────
    if [ "$DEBUG" != "True" ]; then
        log "Recolectando archivos estáticos..."
        python sacarf/manage.py collectstatic --noinput 2>&1
        log "Archivos estáticos recolectados."
    fi

    # ── 5. Verificar que la tabla de auditoría existe ──────────────────
    log "Verificando tabla de auditoría..."
    python sacarf/manage.py shell -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sacarf.settings')
django.setup()

from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(\"\"\"
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'monitoring_registroauditoria'
        )
    \"\"\")
    exists = cursor.fetchone()[0]
    if exists:
        cursor.execute('SELECT COUNT(*) FROM monitoring_registroauditoria')
        count = cursor.fetchone()[0]
        print(f'Tabla monitoring_registroauditoria existe ({count} registros).')
    else:
        print('ADVERTENCIA: tabla monitoring_registroauditoria NO existe.')
" 2>&1

    log "=== INIT COMPLETADO ==="

    echo "Creando datos de demostración (docente, estudiante, materia y falta de ejemplo)..."
    python sacarf/manage.py shell -c "
from datetime import date, timedelta
from apps.usuario.models import Usuario
from apps.academico.models import Carrera, Ciclo, Materia, Horario, Matricula
from apps.asistencia.models import Asistencia

docente, creado = Usuario.objects.get_or_create(
    email='docente@sacarf.com',
    defaults=dict(cedula='1111111111', rol='DOCENTE', first_name='Carlos', last_name='Mendoza', is_active=True)
)
if creado:
    docente.set_password('docente123')
    docente.save()
    print('Docente demo creado: docente@sacarf.com / docente123')

estudiante, creado = Usuario.objects.get_or_create(
    email='estudiante@sacarf.com',
    defaults=dict(cedula='2222222222', rol='ESTUDIANTE', first_name='Ana', last_name='Torres', is_active=True)
)
if creado:
    estudiante.set_password('estudiante123')
    estudiante.save()
    print('Estudiante demo creado: estudiante@sacarf.com / estudiante123')

carrera, _ = Carrera.objects.get_or_create(
    codigo='SIS', defaults=dict(nombre='Ingeniería en Sistemas', duracion=9, modalidad='PRESENCIAL')
)
ciclo, _ = Ciclo.objects.get_or_create(
    num=1, carrera=carrera,
    defaults=dict(fecha_inicio=date.today(), fecha_fin=date.today() + timedelta(days=180), estado='ACTIVO')
)
materia, _ = Materia.objects.get_or_create(
    codigo='SIS101',
    defaults=dict(nombre='Programación I', creditos=4, horas_semanales=4,
                  carrera=carrera, ciclo=ciclo, docente_id=docente.id)
)
if materia.docente_id != docente.id:
    materia.docente_id = docente.id
    materia.save()

horario, _ = Horario.objects.get_or_create(
    materia=materia, dia_semana='LUNES',
    defaults=dict(hora_inicio='08:00', hora_fin='10:00', aula='Lab 1')
)
Matricula.objects.get_or_create(estudiante_id=estudiante.id, ciclo=ciclo, defaults=dict(carrera=carrera))

_, creada = Asistencia.objects.get_or_create(
    estudiante_id=estudiante.id, horario_id=horario.id, fecha=date.today(),
    defaults=dict(estado='AUSENTE', confianza=0.0)
)
if creada:
    print('Falta de ejemplo (AUSENTE) creada para subir el comprobante')
print('Datos de demostración listos')
"
    echo "Inicialización completada."
    exit 0
fi

# ═══════════════════════════════════════════════════════════════════════
#  MICROSERVICIOS: Iniciar servidor
# ═══════════════════════════════════════════════════════════════════════
log "=== INICIANDO SERVICIO: $SERVICE_NAME ==="
log "Puerto: $SERVICE_PORT  DEBUG: $DEBUG"

# Verificar que el manage.py del microservicio existe
MANAGE_PY="services/$SERVICE_NAME/manage.py"
if [ ! -f "$MANAGE_PY" ]; then
    error "No se encontró $MANAGE_PY"
    exit 1
fi

# ── Desarrollo: runserver ──────────────────────────────────────────────
if [ "$DEBUG" = "True" ]; then
    log "Modo DESARROLLO: Django runserver"
    exec python "$MANAGE_PY" runserver 0.0.0.0:"$SERVICE_PORT"
fi

# ── Producción: gunicorn ──────────────────────────────────────────────
log "Modo PRODUCCIÓN: gunicorn"

# Cada manage.py agrega /app y /app/sacarf al sys.path.
# Gunicorn necesita lo mismo vía PYTHONPATH.
# El wsgi.py de cada microservicio está en services/$SERVICE_NAME/$SERVICE_NAME/wsgi.py
export PYTHONPATH="/app:/app/sacarf:/app/services/$SERVICE_NAME"
export DJANGO_SETTINGS_MODULE="${SERVICE_NAME}.settings"
WSGI_MODULE="${SERVICE_NAME}.wsgi"

exec gunicorn "${WSGI_MODULE}:application" \
    --bind 0.0.0.0:"$SERVICE_PORT" \
    --workers "${GUNICORN_WORKERS:-3}" \
    --threads "${GUNICORN_THREADS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile - \
    --log-level info

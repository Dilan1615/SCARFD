#!/bin/bash
set -e

SERVICE_NAME=${SERVICE_NAME:-all}
SERVICE_PORT=${SERVICE_PORT:-8000}

if [ "$SERVICE_NAME" = "init" ]; then
    echo "Ejecutando migraciones..."
    python sacarf/manage.py makemigrations --noinput
    python sacarf/manage.py migrate --noinput

    echo "Creando superusuario por defecto (si no existe)..."
    python sacarf/manage.py shell -c "
from apps.usuario.models import Usuario
if not Usuario.objects.filter(email='admin@sacarf.com').exists():
    Usuario.objects.create_superuser(
        email='admin@sacarf.com',
        password='admin123',
        cedula='0000000000',
        rol='ADMIN'
    )
    print('Superusuario admin creado')
else:
    print('Superusuario admin ya existe')
"

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

echo "Iniciando servicio: $SERVICE_NAME en puerto $SERVICE_PORT..."
exec python "services/$SERVICE_NAME/manage.py" runserver 0.0.0.0:"$SERVICE_PORT"

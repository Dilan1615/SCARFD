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
    echo "Inicialización completada."
    exit 0
fi

echo "Iniciando servicio: $SERVICE_NAME en puerto $SERVICE_PORT..."
exec python "services/$SERVICE_NAME/manage.py" runserver 0.0.0.0:"$SERVICE_PORT"

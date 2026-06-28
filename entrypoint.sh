#!/bin/bash
set -e

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

echo "Iniciando servidor..."
exec python sacarf/manage.py runserver 0.0.0.0:8000
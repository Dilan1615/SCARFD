#!/bin/bash
set -e

echo "Ejecutando migraciones..."
python sacarf/manage.py migrate --noinput

echo "Creando superusuario por defecto (si no existe)..."
python sacarf/manage.py shell -c "
from apps.usuario.models import Usuario
if not Usuario.objects.filter(username='admin').exists():
    Usuario.objects.create_superuser('admin', 'admin@sacarf.com', 'admin123', cedula='0000000000', rol='ADMIN')
    print('Superusuario admin creado')
else:
    print('Superusuario admin ya existe')
"

echo "Iniciando servidor..."
exec python sacarf/manage.py runserver 0.0.0.0:8000

#!/usr/bin/env python
"""manage.py del microservicio monitoring-service (puerto 8005)."""
import os
import sys
from pathlib import Path

if __name__ == '__main__':
    BASE = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(BASE))
    sys.path.insert(0, str(BASE / 'sacarf'))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monitoring.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Está activado el entorno virtual?"
        ) from exc
    execute_from_command_line(sys.argv)

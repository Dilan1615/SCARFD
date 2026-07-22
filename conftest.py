import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / 'sacarf'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sacarf.settings')
os.environ.setdefault('DB_ENGINE', 'django.db.backends.sqlite3')
os.environ.setdefault('DB_NAME', ':memory:')
os.environ.setdefault('SERVICE_NAME', 'all')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-not-for-production')
os.environ.setdefault('PASSWORD_RESET_TIMEOUT', '30')
os.environ.setdefault('FRONTEND_URL', 'http://localhost:5173')
os.environ.setdefault('GATEWAY_URL', 'http://test-gateway:80')
os.environ.setdefault('BREVO_API_KEY', 'test-brevo-key')
os.environ.setdefault('BREVO_FROM_EMAIL', 'test@example.com')
os.environ.setdefault('BREVO_FROM_NAME', 'Test SACARF')
os.environ.setdefault('AWS_ACCESS_KEY_ID', 'test-aws-key')
os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'test-aws-secret')
os.environ.setdefault('AWS_REGION', 'us-east-1')
os.environ.setdefault('AWS_STORAGE_BUCKET_NAME', 'test-bucket')
os.environ.setdefault('PROMETHEUS_URL', 'http://test-prometheus:9090')

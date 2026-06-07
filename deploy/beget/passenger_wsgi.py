# Точка входа Passenger на Beget. Лежит в ~/c99631u8.beget.tech/passenger_wsgi.py
import os
import sys

SITE_ROOT = os.path.dirname(os.path.abspath(__file__))
DJANGO_DIR = os.path.join(SITE_ROOT, 'source', 'mysite')
VENV_DIR = os.path.join(SITE_ROOT, 'venv')

# site-packages выбранного Python в venv
for py in ('python3.12', 'python3.11', 'python3.10'):
    candidate = os.path.join(VENV_DIR, 'lib', py, 'site-packages')
    if os.path.isdir(candidate):
        sys.path.insert(1, candidate)
        break

sys.path.insert(0, DJANGO_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
os.environ.setdefault('DJANGO_DEBUG', 'False')
os.environ.setdefault('ALLOWED_HOSTS', 'c99631u8.beget.tech,localhost,127.0.0.1')
os.environ.setdefault('CSRF_TRUSTED_ORIGINS', 'https://c99631u8.beget.tech,http://c99631u8.beget.tech')
os.environ.setdefault('SERVE_MEDIA', 'True')
os.environ.setdefault('BEGET_DEPLOY', 'True')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

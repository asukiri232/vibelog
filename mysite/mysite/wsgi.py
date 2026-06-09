"""
WSGI config for mysite project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

_django_app = get_wsgi_application()


def application(environ, start_response):
    # Healthcheck Railway до Django (без ALLOWED_HOSTS / БД / сессий).
    path = environ.get('PATH_INFO') or ''
    if path in ('/health', '/health/'):
        start_response(
            '200 OK',
            [('Content-Type', 'text/plain'), ('Cache-Control', 'no-store')],
        )
        return [b'ok']
    return _django_app(environ, start_response)

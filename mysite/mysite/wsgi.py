"""
WSGI config for mysite project.
"""

import os
import sys
import traceback

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

_django_app = get_wsgi_application()


def application(environ, start_response):
    path = environ.get('PATH_INFO') or ''
    if path in ('/health', '/health/'):
        start_response(
            '200 OK',
            [('Content-Type', 'text/plain'), ('Cache-Control', 'no-store')],
        )
        return [b'ok']
    try:
        return _django_app(environ, start_response)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        return [b'error']

"""
Точка входа WSGI для Vercel: ./mysite/wsgi.py
(внутренний модуль остаётся в mysite/mysite/wsgi.py)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

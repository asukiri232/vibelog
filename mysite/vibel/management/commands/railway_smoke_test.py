import sys

from django.core.management.base import BaseCommand
from django.test import Client


class Command(BaseCommand):
    help = 'Проверка ответов /ready/ и / до запуска gunicorn.'

    def handle(self, *args, **options):
        from django.conf import settings

        self.stdout.write(f'ALLOWED_HOSTS={settings.ALLOWED_HOSTS!r}')
        self.stdout.write(f'DEBUG={settings.DEBUG}')
        self.stdout.write(f'DB={settings.DATABASES["default"].get("ENGINE")}')

        host = 'healthcheck.railway.app'
        public = __import__('os').environ.get('RAILWAY_PUBLIC_DOMAIN', '').strip()
        if public:
            host = public

        client = Client(HTTP_HOST=host)
        for path in ('/ready/', '/'):
            response = client.get(path)
            self.stdout.write(f'{path} -> {response.status_code} ({len(response.content)} bytes)')
            if response.status_code >= 500:
                body = response.content[:500].decode('utf-8', errors='replace')
                self.stderr.write(body)
                sys.exit(1)

        self.stdout.write(self.style.SUCCESS('Smoke test OK'))

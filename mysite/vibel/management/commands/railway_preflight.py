import os
import sys

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Проверка окружения Railway перед migrate/gunicorn.'

    def handle(self, *args, **options):
        db_url = os.environ.get('DATABASE_URL', '').strip()
        if not db_url:
            self.stderr.write(self.style.ERROR(
                'DATABASE_URL не задан. Web-сервис → Variables → Add Reference → Postgres → DATABASE_URL'
            ))
            sys.exit(1)
        if '${{' in db_url or '}}' in db_url:
            self.stderr.write(self.style.ERROR(
                'DATABASE_URL содержит ${{...}} — это шаблон Postgres, не готовая строка.\n'
                'Удалите ручной DATABASE_URL на web-сервисе и добавьте Reference на Postgres → DATABASE_URL.'
            ))
            sys.exit(1)
        if not db_url.startswith(('postgres://', 'postgresql://')):
            self.stderr.write(self.style.ERROR('DATABASE_URL должен начинаться с postgresql://'))
            sys.exit(1)

        engine = connection.settings_dict.get('ENGINE', '')
        if 'postgresql' not in engine:
            self.stderr.write(self.style.ERROR(
                f'Ожидался PostgreSQL, получен {engine}. Проверьте Reference DATABASE_URL на web-сервисе.'
            ))
            sys.exit(1)

        connection.ensure_connection()
        self.stdout.write(self.style.SUCCESS(f'DB OK ({engine})'))

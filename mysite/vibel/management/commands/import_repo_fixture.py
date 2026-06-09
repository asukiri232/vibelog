from pathlib import Path

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand

FIXTURE = Path(__file__).resolve().parents[3] / 'fixtures' / 'vibel_data.json'


class Command(BaseCommand):
    help = 'Один раз загружает данные из mysite/fixtures/vibel_data.json (при пустой PostgreSQL на Railway).'

    def handle(self, *args, **options):
        if not FIXTURE.is_file():
            self.stdout.write('Fixture not found, skip.')
            return
        if User.objects.exists():
            self.stdout.write('Database already has users, skip fixture import.')
            return
        self.stdout.write(f'Loading {FIXTURE.name}...')
        call_command('loaddata', str(FIXTURE), verbosity=1)
        self.stdout.write(self.style.SUCCESS('Fixture imported.'))

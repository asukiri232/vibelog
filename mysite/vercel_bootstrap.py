"""Один раз при cold start на Vercel: миграции и базовые категории."""
import os

_bootstrapped = False


def ensure_vercel_database() -> None:
    global _bootstrapped
    if _bootstrapped or not os.environ.get('VERCEL'):
        return

    from django.core.management import call_command

    call_command('migrate', '--noinput', verbosity=0)

    from vibel.models import Category

    if Category.objects.count() == 0:
        call_command('seed_vibel', verbosity=0)

    _bootstrapped = True

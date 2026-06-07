"""Подготовка Vercel: миграции, категории, папки для загрузок в /tmp."""
import os
from pathlib import Path

_db_ready = False
_media_ready = False

_MEDIA_SUBDIRS = (
    'avatars',
    'covers',
    'posts',
    'posts/extra',
    'posts/video',
    'comments',
    'dm',
    'messages',
)


def ensure_vercel_database() -> None:
    global _db_ready
    if _db_ready or not os.environ.get('VERCEL'):
        return

    from django.core.management import call_command

    call_command('migrate', '--noinput', verbosity=0)

    from vibel.models import Category

    # Идемпотентно: категории нужны для формы нового поста.
    call_command('seed_vibel', verbosity=0)

    _db_ready = True


def ensure_media_dirs() -> None:
    global _media_ready
    if not os.environ.get('VERCEL'):
        return
    if _media_ready:
        return

    from django.conf import settings

    root = Path(settings.MEDIA_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    for sub in _MEDIA_SUBDIRS:
        (root / sub).mkdir(parents=True, exist_ok=True)
    _media_ready = True


def ensure_vercel_runtime() -> None:
    ensure_vercel_database()
    ensure_media_dirs()

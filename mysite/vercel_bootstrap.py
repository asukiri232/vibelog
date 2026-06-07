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

_DEMO_USERNAME = 'demo_ru_01'
_DEMO_PASSWORD = 'DemoSeed2026!'


def _using_ephemeral_db() -> bool:
    return bool(os.environ.get('VERCEL')) and not os.environ.get('DATABASE_URL', '').strip()


def seed_minimal_demo_if_empty() -> None:
    """Быстрый демо-аккаунт без загрузки картинок — только для пустой ephemeral БД."""
    if not _using_ephemeral_db():
        return

    from django.contrib.auth.models import User

    from vibel.models import Category, Post, Profile

    if User.objects.exists():
        return

    user = User.objects.create_user(
        username=_DEMO_USERNAME,
        email=f'{_DEMO_USERNAME}@demo.vibel.local',
        password=_DEMO_PASSWORD,
    )
    profile = Profile.objects.get(user=user)
    profile.display_name = 'Демо VibeLog'
    profile.bio = 'Тестовый аккаунт. Для постоянного входа подключите Neon (см. VERCEL.md).'
    profile.save(update_fields=['display_name', 'bio'])

    category = Category.objects.order_by('order').first()
    if category:
        Post.objects.create(
            author=user,
            category=category,
            caption='Добро пожаловать в VibeLog! Лента настроений.',
        )


def ensure_vercel_database() -> None:
    global _db_ready
    if _db_ready or not os.environ.get('VERCEL'):
        return

    from django.core.management import call_command

    call_command('migrate', '--noinput', verbosity=0)
    call_command('seed_vibel', verbosity=0)
    seed_minimal_demo_if_empty()

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

from django.apps import AppConfig


class VibelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vibel'
    verbose_name = 'Контент VibeLog'

    def ready(self):
        import vibel.signals  # noqa: F401

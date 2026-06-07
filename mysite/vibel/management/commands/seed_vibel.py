from django.core.management.base import BaseCommand

from vibel.models import Category

ROWS = [
    ('Лайфстайл', 'lifestyle', 1),
    ('Спорт', 'sport', 2),
    ('Стрит', 'street', 3),
    ('Путешествия', 'travel', 4),
    ('Арт', 'art', 5),
    ('Музыка', 'music', 6),
]


class Command(BaseCommand):
    help = 'Создаёт критерии (типы постов) для VibeLog'

    def handle(self, *args, **options):
        for name, slug, order in ROWS:
            Category.objects.update_or_create(
                slug=slug, defaults={'name': name, 'order': order}
            )
        self.stdout.write(self.style.SUCCESS('Критерии обновлены.'))

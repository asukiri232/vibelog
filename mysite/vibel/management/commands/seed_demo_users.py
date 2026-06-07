"""
Заполняет БД демо-пользователями и постами.
Пользователи: username demo_ru_01 … demo_ru_20 (латиница), имя в ленте — кириллица.
Изображения: CDN Unsplash (бесплатно, без водяных знаков; см. https://unsplash.com/license).
"""
import random
import time
import urllib.error
import urllib.request

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from vibel.models import Category, Post, Profile

# Портреты (квадрат crop) — Unsplash
AVATAR_URLS = [
    'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1539578705166-4a6d31875b16?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1488426862026-3ee34a7d66df?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1502378735452-bc7d86632803?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1599566150163-38294d011cc7?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1554151228-14d9def656e4?w=400&h=400&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?w=400&h=400&fit=crop&auto=format&q=80',
]

# Жизнь, города, еда, люди — Unsplash
POST_IMAGE_URLS = [
    'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1514565131-fce0801e5785?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1528605248644-14dd04022da1?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1511632761676-022781e92629?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1528164344705-47542687000d?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1551218808-94e220e084d2?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1559339352-11d035aa65de?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1483721310020-03333e577078?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?w=900&fit=crop&auto=format&q=80',
    'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=900&fit=crop&auto=format&q=80',
]

RUSSIAN_DISPLAY_NAMES = [
    'Анна Смирнова',
    'Дмитрий Волков',
    'Елена Козлова',
    'Игорь Новиков',
    'Мария Павлова',
    'Сергей Орлов',
    'Ольга Морозова',
    'Алексей Соколов',
    'Наталья Лебедева',
    'Павел Кузнецов',
    'Татьяна Васильева',
    'Андрей Попов',
    'Екатерина Семёнова',
    'Николай Виноградов',
    'Ирина Белова',
    'Максим Жуков',
    'Светлана Никифорова',
    'Роман Степанов',
    'Юлия Фёдорова',
    'Константин Давыдов',
]

CAPTIONS_RU = [
    'Утро и чашка кофе — уже маленький праздник.',
    'Город в огнях, а я просто гуляю и дышу.',
    'Такое небо бывает раз в сезон, сфоткала на память.',
    'Обед с друзьями затянулся — и ни капли не жаль.',
    'Люблю эти улицы, когда почти никого нет.',
    'Закат, ветер, музыка в наушниках — идеально.',
    'Пробовала новое кафе: атмосфера топ, вернусь ещё.',
    'Выходные = сон + прогулка + что-нибудь вкусное.',
    'Сегодня только я, камера и хорошее настроение.',
    'Маленький ресторанчик с большим сердцем.',
    'Архитектура здесь будто из фильма.',
    'После дождя асфальт блестит — красота.',
    'Завтрак, который хочется повторять каждый день.',
    'Собрались компанией — смех до слёз.',
    'Этот вид стоил подъёма на рассвете.',
    'Просто день из жизни, без фильтров.',
    'Улыбка случайного прохожего сделала кадр.',
    'Тёплый свет, тихая музыка, хочется остаться.',
    'Пицца была огонь, делиться не хотелось.',
    'Город, в котором каждый угол — открытие.',
    'Погуляла, отдохнула душой.',
    'Кофе горький, настроение — сладкое.',
    'Вечер с книгой и чаем — мой формат.',
    'Фото не передаёт, насколько здесь уютно.',
    'Лето в одном кадре.',
    'С детства люблю такие дворы.',
    'Еда как искусство, жалко трогать вилкой.',
    'Свет фонарей, лужи, отражения — магия.',
    'Ничего особенного, просто хороший день.',
    'Нашла место, куда хочется возвращаться.',
    'Друзья + закат = идеальная формула.',
    'Шумный рынок, ароматы, жизнь кипит.',
    'Тихий парк посреди бетона — спасение.',
    'Первый снег в городе, все как дети.',
    'Бранч затянулся до обеда, и это нормально.',
    'Люди вокруг — главный декор любого города.',
    'Сегодня гуляла без маршрута — и нашла красоту.',
    'Запах свежей выпечки решает всё.',
    'Ночной город другой, почти кино.',
    'Момент, когда хочется нажать «стоп» у времени.',
    'Просто поела и стало легче на душе.',
    'Окно в поезде — лучший кинозал.',
    'Солнечный день и мороженое — классика.',
    'Улица, о которой раньше не знала — теперь любимая.',
]

USER_AGENT = 'VibeLogDemoSeed/1.0 (Django; +https://github.com/)'


def _download(url: str, timeout: int = 50, retries: int = 4) -> bytes:
    """Несколько попыток и пауза — меньше срывов (WinError 10054 и т.п.)."""
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            time.sleep(0.4)
            return data
        except (urllib.error.URLError, OSError, TimeoutError, ValueError) as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(1.5 * (2**attempt))
    raise last_err


class Command(BaseCommand):
    help = (
        'Создаёт 20 демо-пользователей demo_ru_01…20 с русскими именами в профиле, '
        'аватарами и 1–5 постами (картинки с Unsplash). Уже существующие пользователи '
        'не пересоздаются, но в конце выполняется дозаполнение: пустой аватар и посты, '
        'если их ещё нет. Перед первым запуском: python manage.py seed_vibel'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--purge',
            action='store_true',
            help='Удалить всех пользователей demo_ru_XX и связанные данные, затем создать заново.',
        )
        parser.add_argument(
            '--password',
            default='DemoSeed2026!',
            help='Пароль для всех демо-аккаунтов (только для разработки).',
        )
        parser.add_argument(
            '--no-reconcile',
            action='store_true',
            help='Не дозаполнять аватары/посты у уже существующих demo_ru_XX.',
        )

    def handle(self, *args, **options):
        if Category.objects.count() == 0:
            raise CommandError(
                'В БД нет категорий. Сначала: python manage.py seed_vibel'
            )

        if options['purge']:
            demo_names = [f'demo_ru_{k:02d}' for k in range(1, 21)]
            qs = User.objects.filter(username__in=demo_names)
            n, _ = qs.delete()
            self.stdout.write(self.style.WARNING(f'Удалено записей (включая каскад): {n}'))

        categories = list(Category.objects.all())
        post_urls = list(POST_IMAGE_URLS)
        captions = list(CAPTIONS_RU)

        created_users = 0
        created_posts = 0

        for i in range(20):
            username = f'demo_ru_{i + 1:02d}'
            display_name = RUSSIAN_DISPLAY_NAMES[i]

            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'Пропуск — уже есть: {username}'))
                continue

            self.stdout.write(f'[{i + 1}/20] новый: {username} — {display_name}')

            user = User.objects.create_user(
                username=username,
                email=f'{username}@demo.vibel.local',
                password=options['password'],
            )
            created_users += 1
            profile = Profile.objects.get(user=user)
            profile.display_name = display_name
            profile.save()

            av_url = AVATAR_URLS[i % len(AVATAR_URLS)]
            try:
                self.stdout.write('  аватар…')
                raw = _download(av_url)
                profile.avatar.save(
                    f'{username}_avatar.jpg',
                    ContentFile(raw),
                    save=True,
                )
            except (urllib.error.URLError, OSError, ValueError) as e:
                self.stdout.write(
                    self.style.ERROR(f'  аватар: ошибка ({e})')
                )

            n_posts = random.randint(1, 5)
            self.stdout.write(f'  постов: {n_posts}')
            created_posts += self._create_posts(
                user,
                username,
                n_posts,
                categories,
                post_urls,
                captions,
                start_index=0,
            )

        reconciled_avatars = 0
        reconciled_posts = 0
        if not options['no_reconcile']:
            self.stdout.write('--- Дозаполнение существующих demo_ru_XX (аватар / посты) ---')
            reconciled_avatars, reconciled_posts = self._reconcile_existing(
                categories, post_urls, captions
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Готово: новых пользователей {created_users}, новых постов при создании {created_posts}. '
                f'Дозаполнено: аватаров {reconciled_avatars}, постов {reconciled_posts}. '
                f'Логин: demo_ru_01 … demo_ru_20, пароль: {options["password"]!r}'
            )
        )

    def _create_posts(self, user, username, n_posts, categories, post_urls, captions, start_index):
        """Создаёт n_posts; имена файлов с суффиксом start_index+j. Возвращает число созданных."""
        if n_posts <= 0:
            return 0
        used_captions = random.sample(captions, min(n_posts, len(captions)))
        created = 0
        for j in range(n_posts):
            url = random.choice(post_urls)
            try:
                img = _download(url)
            except (urllib.error.URLError, OSError, ValueError) as e:
                self.stdout.write(
                    self.style.ERROR(f'  пост {username}/{start_index + j}: не загрузилось ({e})')
                )
                continue

            post = Post(
                author=user,
                category=random.choice(categories),
                caption=used_captions[j] if j < len(used_captions) else random.choice(captions),
            )
            post.image.save(
                f'{username}_post_{start_index + j}.jpg',
                ContentFile(img),
                save=True,
            )
            created += 1
        return created

    def _reconcile_existing(self, categories, post_urls, captions):
        """Аватар, если пусто; 1–5 постов, если у пользователя 0 постов."""
        filled_av = 0
        filled_posts = 0
        for i in range(20):
            username = f'demo_ru_{i + 1:02d}'
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                continue

            profile = Profile.objects.get(user=user)
            if not (profile.display_name or '').strip():
                profile.display_name = RUSSIAN_DISPLAY_NAMES[i]
                profile.save()

            av_url = AVATAR_URLS[i % len(AVATAR_URLS)]
            if not profile.avatar:
                try:
                    self.stdout.write(f'  {username}: аватар…')
                    raw = _download(av_url)
                    profile.avatar.save(
                        f'{username}_avatar.jpg',
                        ContentFile(raw),
                        save=True,
                    )
                    filled_av += 1
                except (urllib.error.URLError, OSError, ValueError) as e:
                    self.stdout.write(
                        self.style.ERROR(f'  {username}: аватар не загрузился ({e})')
                    )

            existing_n = Post.objects.filter(author=user).count()
            if existing_n == 0:
                n_posts = random.randint(1, 5)
                self.stdout.write(f'  {username}: добавляю {n_posts} пост(ов)…')
                filled_posts += self._create_posts(
                    user,
                    username,
                    n_posts,
                    categories,
                    post_urls,
                    captions,
                    start_index=0,
                )
        return filled_av, filled_posts

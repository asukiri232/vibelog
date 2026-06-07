# VibeLog на Vercel — постоянный аккаунт (Neon)

## Почему вылетает из аккаунта

На Vercel без внешней базы данных приложение использует **SQLite в `/tmp`**. Эта память:

- **обнуляется** после простоя (cold start);
- **не общая** между разными инстансами сервера.

Поэтому пользователи, посты и сессии «пропадают» — сайт как будто сбрасывается.

**Решение:** подключить бесплатную PostgreSQL в [Neon](https://neon.tech) (5 минут).

---

## Шаг 1 — база Neon

1. Зарегистрируйтесь на https://neon.tech  
2. **New Project** → регион ближе к вам → Create  
3. На вкладке **Connection string** скопируйте URI вида:  
   `postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`

---

## Шаг 2 — переменные в Vercel

1. https://vercel.com → ваш проект **vibelog** → **Settings** → **Environment Variables**
2. Добавьте:

| Имя | Значение |
|-----|----------|
| `DATABASE_URL` | строка подключения Neon (целиком) |
| `DJANGO_SECRET_KEY` | случайная строка 50+ символов |
| `DJANGO_DEBUG` | `false` |

3. **Save** → **Deployments** → последний деплой → **⋯** → **Redeploy**

После redeploy аккаунты и посты **сохраняются** между визитами.

---

## Шаг 3 — демо-контент (по желанию)

В Neon данные пустые. Для наполненной ленты локально:

```powershell
cd C:\Users\user\Desktop\VibeLog\mysite
$env:DATABASE_URL="postgresql://..."
py manage.py migrate
py manage.py seed_vibel
py manage.py seed_demo_users
```

Либо зарегистрируйтесь на сайте вручную.

**Демо без Neon (временно):** `demo_ru_01` / `DemoSeed2026!` — появляется после сброса, но снова пропадёт при cold start.

---

## Production URL

Для преподавателя используйте постоянную ссылку, не preview:

`https://vibelog-kappa.vercel.app`

Preview-ссылки (`vibelog-xxxxx.vercel.app`) могут давать **401** на статику из-за Deployment Protection.

---

## Размер деплоя (лимит 245 МБ)

В `requirements.txt` только пакеты для Vercel (без Pillow и gunicorn). Локально:

```powershell
pip install -r requirements-local.txt
```

Не коммитьте папку `mysite/media/` — она в `.gitignore` и `.vercelignore`.

---

## Медиа (фото в постах)

Файлы по-прежнему в `/tmp` — после долгого простоя картинки могут пропасть. Для диплома обычно достаточно; для продакшена нужен S3/Cloudinary.

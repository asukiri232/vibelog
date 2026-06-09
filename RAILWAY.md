# VibeLog на Railway (с PostgreSQL)

Постоянная база данных + аккаунты не сбрасываются. Подходит для диплома лучше, чем Vercel без БД.

Сайт: [railway.com](https://railway.com/)

---

## 1. Залить код на GitHub

Репозиторий должен быть на GitHub (у вас: `asukiri232/vibelog`).

---

## 2. Новый проект на Railway

1. [railway.com](https://railway.com/) → войти через GitHub  
2. **New Project** → **Deploy from GitHub repo** → выбрать **vibelog**  
3. Railway подхватит `railway.toml` и `build-railway.sh`

---

## 3. PostgreSQL (база данных)

1. В проекте: **+ New** → **Database** → **PostgreSQL**  
2. Откройте сервис **Postgres** → вкладка **Variables**  
3. Скопируйте **`DATABASE_URL`** (или `DATABASE_PRIVATE_URL` для внутренней сети)

### Подключить БД к сайту

1. Откройте сервис **vibelog** (web)  
2. **Variables** → **+ New Variable** → **Add Reference**  
3. Выберите Postgres → **`DATABASE_URL`**

Railway сам прокинет строку подключения — Django уже настроен на `DATABASE_URL`.

---

## 4. Переменные окружения (web-сервис)

| Переменная | Значение |
|------------|----------|
| `DATABASE_URL` | Reference → Postgres (см. выше) |
| `DJANGO_SECRET_KEY` | случайная строка 50+ символов |
| `DJANGO_DEBUG` | `false` |
| `SEED_DEMO` | `1` — заполнить демо при первой сборке; потом `0` |
| `SERVE_MEDIA` | `true` |

`ALLOWED_HOSTS` и CSRF для домена `*.railway.app` подставляются из `RAILWAY_PUBLIC_DOMAIN` автоматически.

---

## 5. Домен

1. Web-сервис → **Settings** → **Networking** → **Generate Domain**  
2. Получите ссылку вида `https://vibelog-production.up.railway.app`  
3. Эту ссылку можно дать преподавателю

---

## 6. Медиа (фото и видео) — Volume

Без Volume загруженные файлы могут пропасть после redeploy.

1. Web-сервис → **Volumes** → **Add Volume**  
2. Mount Path: `/app/mysite/media`  
3. Redeploy

---

## 7. Первый деплой

После push в `main` Railway:

**Сборка** (`build-railway.sh` или `build.sh`):
- `pip install -r requirements-railway.txt`
- `collectstatic`

**Старт** (`deploy/railway/start.sh`):
- `migrate`, `seed_vibel`
- при `SEED_DEMO=1` — `seed_demo_users`
- gunicorn

Если в **Settings → Build** указана своя команда `build.sh` — это нормально: на Railway `build.sh` не вызывает migrate.

Обязательно: **Postgres** + **Reference `DATABASE_URL`** на web-сервисе до деплоя.

Демо-аккаунт: **`demo_ru_01`** / **`DemoSeed2026!`**

---

## 8. Локальная БД ≠ Railway

Файл `mysite/db.sqlite3` на ПК **не переносится** автоматически.

На Railway создаётся **новая PostgreSQL**. Ваши локальные пользователи останутся только в SQLite — на Railway зарегистрируйтесь заново или включите `SEED_DEMO=1`.

---

## 9. Обновление после правок в коде

Push в `main` → Railway пересоберёт автоматически.

Вручную: проект → сервис → **Deployments** → **Redeploy**.

---

## 10. Полезные команды (Railway CLI, по желанию)

```bash
npm i -g @railway/cli
railway login
railway link
railway run python mysite/manage.py createsuperuser
```

---

## Файлы деплоя в репозитории

| Файл | Назначение |
|------|------------|
| `railway.toml` | Сборка и старт для Railway |
| `build-railway.sh` | migrate, static, seed |
| `deploy/railway/start.sh` | gunicorn |
| `requirements-railway.txt` | Django + Postgres + gunicorn |
| `Procfile` | запасной старт |

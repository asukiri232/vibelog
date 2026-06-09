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
| `IMPORT_REPO_DATA` | `1` (по умолчанию) — загрузить пользователей и посты из `mysite/fixtures/vibel_data.json` в пустую PostgreSQL |
| `SEED_DEMO` | `0` — не нужен, если данные уже в fixture; `1` только для пустого проекта без fixture |
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

## 9. Ошибка 502 при успешном healthcheck

Если в логах есть `GET /health/ 200`, но в браузере 502 — **приложение живое**, проблема в **маршрутизации Railway** или **не том URL**.

### Чеклист (по порядку)

1. **Открываете URL web-сервиса, не Postgres**  
   В проекте два сервиса. Домен нужен у **vibelog / web** → Settings → Networking → **Public URL** (`*.up.railway.app`).  
   URL Postgres (`DATABASE_PUBLIC_URL`) в браузере даст 502.

2. **Networking → Target Port**  
   Должен совпадать с `PORT` из логов (обычно **8080**). Если вручную стоит `8000` — будет 502 при рабочем healthcheck.

3. **Удалите с web-сервиса** `ALLOWED_HOSTS`, `DATABASE_PUBLIC_URL`, все `PG*` переменные.  
   Оставьте только **Reference** `DATABASE_URL` → Postgres.

4. **Start Command** на web: `bash deploy/railway/start.sh`

5. После redeploy в **Deploy Logs** должно быть:
   ```
   Smoke test OK
   GET /ready/ -> 200
   GET / -> 200
   ```

6. Проверка в браузере:
   - `/health/` → `ok`
   - `/ready/` → `ok users=...`
   - `/` → лента

7. **HTTP Logs** (вкладка у web-сервиса): при открытии сайта должна появиться строка `GET / host=... status=200`.  
   Если строк нет — вы открываете не тот домен.

---

## 10. Ошибка 502 / «Application failed to respond» (БД)

Gunicorn не стартует или падает до healthcheck — чаще всего **неверный `DATABASE_URL` на web-сервисе**.

**Неправильно** (шаблон Postgres, вставленный вручную на web):
```
DATABASE_URL="postgresql://${{PGUSER}}:${{POSTGRES_PASSWORD}}@..."
```

**Правильно:**
1. Удалите на **web-сервисе** переменные `DATABASE_URL`, `DATABASE_PUBLIC_URL`, `PGUSER`, `PGPASSWORD` и т.п.
2. **+ New Variable** → **Add Reference** → сервис **Postgres** → поле **`DATABASE_URL`**
3. Значение будет вида `postgresql://postgres:реальный_пароль@containers-....railway.app:12345/railway`

Также **удалите** `ALLOWED_HOSTS` с web-сервиса (там не должно быть `.onrender.com`).

После push с `railway_preflight` в логах будет явная ошибка, если Reference не настроен.

Проверка: `/health/` → `ok` (работает даже до полной настройки Django).

---

## 11. «Application failed to respond» (другое)

Чаще всего одна из причин ниже. Откройте **Deployments → последний деплой → Deploy Logs** (не Build Logs).

| Симптом в логах | Решение |
|-----------------|--------|
| `ERROR: DATABASE_URL is not set` | Web-сервис → **Variables** → **Add Reference** → Postgres → `DATABASE_URL` → Redeploy |
| `gunicorn: not found` / `python: command not found` | Обновите код (исправлен `start.sh` с `.venv/bin/python`) |
| `$'\r': command not found` | CRLF в `.sh` — обновите репозиторий (есть `.gitattributes`) |
| `migrate` / `connection refused` / SSL | Убедитесь, что Postgres **Running**; reference на тот же проект |
| Сборка OK, старт падает сразу | **Settings → Deploy → Start Command:** `bash deploy/railway/start.sh` |

Минимальные переменные web-сервиса:

| Переменная | Значение |
|------------|----------|
| `DATABASE_URL` | Reference → Postgres |
| `DJANGO_SECRET_KEY` | любая длинная случайная строка |
| `DJANGO_DEBUG` | `false` |
| `IMPORT_REPO_DATA` | `1` |
| `SEED_DEMO` | `0` (данные уже в репозитории) |

Проверка после деплоя: `https://ВАШ-ДОМЕН.up.railway.app/health/` → должно быть `ok`.

---

## 10. Обновление после правок в коде

Push в `main` → Railway пересоберёт автоматически.

Вручную: проект → сервис → **Deployments** → **Redeploy**.

---

## 12. Полезные команды (Railway CLI, по желанию)

```bash
npm i -g @railway/cli
railway login
railway link
railway run python mysite/manage.py createsuperuser
```

---

## Данные из локальной БД

В репозитории:

| Путь | Содержимое |
|------|------------|
| `mysite/db.sqlite3` | локальная SQLite (для разработки) |
| `mysite/fixtures/vibel_data.json` | дамп пользователей, постов, лайков и т.д. |
| `mysite/media/` | фото и видео постов |

На Railway при первом старте (пустая PostgreSQL) команда `import_repo_fixture` загружает fixture. Медиа уже в образе из git; для постоянства подключите **Volume** на `/app/mysite/media`.

---

## Файлы деплоя в репозитории

| Файл | Назначение |
|------|------------|
| `railway.toml` | Сборка и старт для Railway |
| `build-railway.sh` | pip, collectstatic |
| `deploy/railway/start.sh` | migrate, seed, gunicorn |
| `requirements-railway.txt` | Django + Postgres + gunicorn |
| `Procfile` | запасной старт |

# Быстрый деплой VibeLog (Render, бесплатно)

## 1. Залить код на GitHub

```powershell
cd C:\Users\user\Desktop\VibeLog
git init
git add .
git commit -m "Prepare VibeLog for Render deploy"
```

Создайте пустой репозиторий на https://github.com/new (без README), затем:

```powershell
git remote add origin https://github.com/ВАШ_ЛОГИН/vibelog.git
git branch -M main
git push -u origin main
```

## 2. Создать сервис на Render

1. https://dashboard.render.com → **New +** → **Blueprint**
2. Подключите GitHub-репозиторий
3. Render подхватит `render.yaml` и создаст Web Service
4. Дождитесь зелёного статуса **Live** (5–10 минут)

Публичная ссылка будет вида: `https://vibelog-xxxx.onrender.com`

## 3. Первый запуск на сервере (опционально — демо-данные)

В Render → **Shell**:

```bash
cd mysite
python manage.py seed_demo_users
```

Демо-аккаунты: `demo_ru_01` … `demo_ru_20`, пароль `DemoSeed2026!`

## 4. Админка

```bash
cd mysite
python manage.py createsuperuser
```

Админка: `/admin/`

## Важно

- На бесплатном Render сервис «засыпает» после ~15 мин без посещений; первый заход после сна — 30–60 сек.
- Загруженные на сервере фото/видео хранятся на диске инстанса (для диплома достаточно).
- Локальная БД с постами **не переносится** автоматически — на сервере нужен `seed_demo_users` или ручная регистрация.

## Временная ссылка без деплоя (пока ПК включён)

```powershell
$env:ALLOWED_HOSTS="localhost,127.0.0.1,.trycloudflare.com,.loca.lt"
cd C:\Users\user\Desktop\VibeLog\mysite
..\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

В другом терминале:

```powershell
npx cloudflared tunnel --url http://127.0.0.1:8000
```

Скопируйте URL вида `https://....trycloudflare.com` и отправьте преподу.

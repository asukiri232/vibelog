# VibeLog без Neon — как сохранить аккаунт

На **Vercel** без внешней базы аккаунты **всегда** будут пропадать. Neon не единственный выход.

## Вариант 1 — Beget (лучше для диплома)

У вас уже есть техдомен: **https://c99631u8.beget.tech**

Там SQLite и медиа лежат на **диске хостинга** — логин не сбрасывается.

Пошагово: файл **BEGET.md** в репозитории.

Кратко:
1. Панель Beget → включить SSH
2. `ssh c99631u8@c99631u8.beget.tech` → `ssh localhost -p222`
3. Запустить `deploy/beget/setup.sh` из репозитория
4. Открыть https://c99631u8.beget.tech и зарегистрироваться

Эту ссылку можно дать преподавателю вместо Vercel.

---

## Вариант 2 — Supabase + Vercel

Если нужен именно домен Vercel, но Neon нельзя:

1. https://supabase.com → регистрация → **New project**
2. **Project Settings → Database → Connection string → URI**
3. Vercel → **Settings → Environment Variables**:
   - `DATABASE_URL` = строка Supabase (с `?sslmode=require`)
   - `DJANGO_DEBUG` = `false`
4. **Redeploy**, зарегистрироваться ещё раз

---

## Вариант 3 — Показ с вашего ПК

Пока компьютер включён:

```powershell
cd C:\Users\user\Desktop\VibeLog\mysite
pip install -r requirements-local.txt
py manage.py runserver 0.0.0.0:8000
```

В другом терминале:

```powershell
npx cloudflared tunnel --url http://127.0.0.1:8000
```

Ссылку из cloudflared отправить преподу. Локальная `db.sqlite3` сохраняет всё.

---

## Вариант 4 — Только Vercel (демо)

Можно оставить как есть для краткого показа, но после 5–15 минут простоя снова нужна регистрация. Для защиты диплома **не подходит** как единственный хостинг.

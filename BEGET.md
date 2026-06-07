# Деплой VibeLog на Beget (c99631u8.beget.tech)

## Куда «пихать» домен

Домен **c99631u8.beget.tech** привязывается **не в коде**, а в панели Beget:

1. https://cp.beget.com/sites
2. Создайте сайт (или откройте существующий) с доменом **c99631u8.beget.tech**
3. Включите редирект **HTTP → HTTPS** (по желанию)

Код проекта лежит на сервере в папке:

```
~/c99631u8.beget.tech/
  passenger_wsgi.py   ← точка входа Django
  .htaccess           ← Passenger + Python
  venv/               ← виртуальное окружение
  public_html/        ← сюда отдаёт Apache (static, media)
  source/             ← git-клон VibeLog
```

---

## Быстрая установка (один раз)

### 1. Включите SSH в панели Beget

https://cp.beget.com/ssh — включить доступ, запомнить пароль.

### 2. Подключитесь (PowerShell на вашем ПК)

```powershell
ssh c99631u8@c99631u8.beget.tech
```

Введите пароль SSH. Затем войдите в окружение сайта:

```bash
ssh localhost -p222
```

### 3. Запустите автоустановку

```bash
curl -fsSL https://raw.githubusercontent.com/asukiri232/vibelog/main/deploy/beget/setup.sh -o setup.sh
bash setup.sh
```

Если `curl` недоступен — вручную:

```bash
cd ~
git clone https://github.com/asukiri232/vibelog.git c99631u8.beget.tech/source
bash c99631u8.beget.tech/source/deploy/beget/setup.sh
```

### 4. Проверка

Откройте: **https://c99631u8.beget.tech**

Демо-аккаунт (после seed):
- логин: `demo_ru_01`
- пароль: `DemoSeed2026!`

---

## Обновление после правок в коде

На сервере:

```bash
ssh c99631u8@c99631u8.beget.tech
ssh localhost -p222
bash ~/c99631u8.beget.tech/source/deploy/beget/setup.sh
```

Или короче:

```bash
touch ~/c99631u8.beget.tech/tmp/restart.txt
```

---

## Если сайт не открывается

1. Панель → Сайты → домен привязан к аккаунту
2. В `~/c99631u8.beget.tech/` есть `passenger_wsgi.py` и `.htaccess`
3. Перезапуск: `touch ~/c99631u8.beget.tech/tmp/restart.txt`
4. Логи: панель Beget → «Журнал ошибок»

---

## Важно

- Обычный виртуальный хостинг Beget + Passenger — **бесплатный техдомен** подходит для диплома.
- Render не обязателен.
- Локальная БД с ПК **не переносится** автоматически; на сервере создаётся новая через `migrate` + `seed_demo_users`.

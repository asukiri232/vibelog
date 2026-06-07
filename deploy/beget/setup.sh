#!/usr/bin/env bash
# Запускать НА СЕРВЕРЕ Beget после: ssh c99631u8@c99631u8.beget.tech  →  ssh localhost -p222
set -euo pipefail

BEGET_LOGIN="${BEGET_LOGIN:-c99631u8}"
DOMAIN="${DOMAIN:-c99631u8.beget.tech}"
SITE_HOME="$HOME/$DOMAIN"
REPO="${REPO:-https://github.com/asukiri232/vibelog.git}"

echo "==> Домашняя папка сайта: $SITE_HOME"
mkdir -p "$SITE_HOME/public_html/static" "$SITE_HOME/public_html/media" "$SITE_HOME/tmp"

cd "$SITE_HOME"

if [ ! -d source/.git ]; then
  echo "==> Клонируем репозиторий"
  rm -rf source
  git clone "$REPO" source
else
  echo "==> Обновляем репозиторий"
  git -C source pull --ff-only
fi

if [ ! -d venv ]; then
  echo "==> Создаём venv"
  python3 -m venv venv
fi

# shellcheck disable=SC1091
source venv/bin/activate
pip install -U pip
pip install -r source/requirements.txt

cp -f source/deploy/beget/passenger_wsgi.py "$SITE_HOME/passenger_wsgi.py"
cp -f source/deploy/beget/htaccess "$SITE_HOME/.htaccess"

DJANGO_DIR="$SITE_HOME/source/mysite"
cd "$DJANGO_DIR"

ln -sfn "$SITE_HOME/public_html/static" "$DJANGO_DIR/staticfiles"
ln -sfn "$SITE_HOME/public_html/media" "$DJANGO_DIR/media"

export DJANGO_DEBUG=False
export ALLOWED_HOSTS="$DOMAIN,localhost,127.0.0.1"
export CSRF_TRUSTED_ORIGINS="https://$DOMAIN,http://$DOMAIN"
export SERVE_MEDIA=True
export BEGET_DEPLOY=True

python manage.py migrate --no-input
python manage.py collectstatic --no-input
python manage.py seed_vibel
python manage.py seed_demo_users --no-reconcile || true

mkdir -p "$SITE_HOME/tmp"
touch "$SITE_HOME/tmp/restart.txt"

echo ""
echo "Готово. Откройте: https://$DOMAIN"
echo "Демо: demo_ru_01 / DemoSeed2026!"

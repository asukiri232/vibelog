#!/usr/bin/env bash
# Railway build: зависимости и статика. migrate/seed — в deploy/railway/start.sh.
set -euo pipefail

chmod +x deploy/railway/start.sh deploy/railway/ensure_media.sh build-railway.sh build.sh 2>/dev/null || true

pip install -r requirements-railway.txt

if [ -d mysite/media ]; then
  echo "Backing up media to deploy/media_seed..."
  rm -rf deploy/media_seed
  mkdir -p deploy/media_seed
  cp -a mysite/media/. deploy/media_seed/
fi

cd mysite
python manage.py collectstatic --no-input

echo "Railway build OK"

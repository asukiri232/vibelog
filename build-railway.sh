#!/usr/bin/env bash
# Railway build: зависимости и статика. migrate/seed — в deploy/railway/start.sh.
set -euo pipefail

chmod +x deploy/railway/start.sh build-railway.sh build.sh 2>/dev/null || true

pip install -r requirements-railway.txt

cd mysite
python manage.py collectstatic --no-input

echo "Railway build OK"

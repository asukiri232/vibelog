#!/usr/bin/env bash
# Railway build: зависимости и статика. migrate/seed — в deploy/railway/start.sh (БД доступна при старте).
set -euo pipefail

pip install -r requirements-railway.txt

cd mysite
python manage.py collectstatic --no-input

echo "Railway build OK"

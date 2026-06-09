#!/usr/bin/env bash
set -o errexit

if [ -n "${RAILWAY_ENVIRONMENT:-}${RAILWAY_PROJECT_ID:-}" ]; then
  pip install -r requirements-railway.txt
else
  pip install -r requirements-local.txt
fi

cd mysite
python manage.py collectstatic --no-input

# На Railway DATABASE_URL часто недоступен или неразрешён на этапе build — migrate при старте.
if [ -z "${RAILWAY_ENVIRONMENT:-}${RAILWAY_PROJECT_ID:-}" ]; then
  python manage.py migrate --no-input
  python manage.py seed_vibel

  if [ "${SEED_DEMO:-1}" = "1" ]; then
    python manage.py seed_demo_users --no-reconcile || true
  fi
fi

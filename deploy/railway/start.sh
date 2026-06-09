#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "${ROOT}/mysite"

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: DATABASE_URL is not set."
  echo "Add PostgreSQL to the project and link DATABASE_URL (Reference) on the web service."
  exit 1
fi

python manage.py migrate --no-input
python manage.py seed_vibel

if [ "${SEED_DEMO:-1}" = "1" ]; then
  python manage.py seed_demo_users --no-reconcile || true
fi

exec gunicorn mysite.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -

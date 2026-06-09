#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "${ROOT}/mysite"

if [ -x "${ROOT}/.venv/bin/python" ]; then
  PYTHON="${ROOT}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
else
  PYTHON=python
fi

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: DATABASE_URL is not set."
  echo "Railway: Postgres service -> Variables -> Add Reference -> DATABASE_URL on the web service."
  exit 1
fi

echo "Using Python: $($PYTHON --version 2>&1)"
echo "PORT=${PORT:-8000}"

"$PYTHON" manage.py migrate --no-input
"$PYTHON" manage.py seed_vibel

if [ "${SEED_DEMO:-1}" = "1" ]; then
  "$PYTHON" manage.py seed_demo_users --no-reconcile || true
fi

echo "Starting gunicorn..."
exec "$PYTHON" -m gunicorn mysite.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -

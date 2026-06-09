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

echo "Using Python: $($PYTHON --version 2>&1)"
echo "PORT=${PORT:-8000}"

"$PYTHON" manage.py railway_preflight

"$PYTHON" manage.py migrate --no-input
"$PYTHON" manage.py seed_vibel

if [ "${IMPORT_REPO_DATA:-1}" = "1" ]; then
  "$PYTHON" manage.py import_repo_fixture
fi

if [ "${SEED_DEMO:-0}" = "1" ]; then
  "$PYTHON" manage.py seed_demo_users --no-reconcile || true
fi

echo "Starting gunicorn on 0.0.0.0:${PORT:-8000}..."
exec "$PYTHON" -m gunicorn mysite.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-1}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -

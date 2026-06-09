#!/usr/bin/env bash
# Volume на /app/mysite/media затирает файлы из git — копируем резерв из deploy/media_seed.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SEED="${ROOT}/deploy/media_seed"
TARGET="${ROOT}/mysite/media"

mkdir -p "${TARGET}"

seed_count=0
target_count=0
if [ -d "${SEED}" ]; then
  seed_count="$(find "${SEED}" -type f 2>/dev/null | wc -l | tr -d ' ')"
fi
target_count="$(find "${TARGET}" -type f 2>/dev/null | wc -l | tr -d ' ')"

echo "Media seed files: ${seed_count}, media dir files: ${target_count}"

if [ "${seed_count}" -gt 0 ] && [ "${target_count}" -lt 10 ]; then
  echo "Copying media from ${SEED} to ${TARGET}..."
  cp -a "${SEED}/." "${TARGET}/"
  target_count="$(find "${TARGET}" -type f 2>/dev/null | wc -l | tr -d ' ')"
fi

echo "Media ready: ${target_count} files in ${TARGET}"

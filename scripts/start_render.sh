#!/bin/sh
set -eu

cd /opt/render/project/src

if [ -z "${DEMO_PASSWORD:-}" ]; then
  echo "ERROR: DEMO_PASSWORD is required."
  exit 1
fi

mkdir -p data

python -m alembic upgrade head

exec python -m uvicorn backend.app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-10000}"

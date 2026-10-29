#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ -z "${DEMO_PASSWORD:-}" ]; then
  echo 'Set DEMO_PASSWORD to a strong local pilot password before starting.' >&2
  exit 1
fi
mkdir -p data
.venv/bin/alembic upgrade head
exec .venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

#!/bin/sh
set -eu
python -m alembic upgrade head
exec python -m uvicorn backend.app:create_app --factory --host 0.0.0.0 --port "${PORT:-8000}" --no-access-log --proxy-headers --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1}"

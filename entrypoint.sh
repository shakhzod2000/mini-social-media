#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

# If arguments are passed (e.g. celery command), run them.
# Otherwise, start Uvicorn (the default for the app service).
if [ $# -gt 0 ]; then
    echo "Running command: $@"
    exec "$@"
else
    echo "Starting application..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi

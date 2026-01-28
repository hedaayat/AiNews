#!/bin/bash
set -e

# Run migrations only if explicitly requested (handled by migrate service in compose)
if [ "${RUN_MIGRATIONS}" = "true" ]; then
    echo "Running Alembic migrations..."
    cd /app && alembic upgrade head
fi

echo "Starting AiNews application..."
exec uvicorn ainews.web.app:app --host 0.0.0.0 --port 8000

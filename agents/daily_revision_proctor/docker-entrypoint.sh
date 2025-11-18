#!/bin/sh
set -e

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h db -U postgres > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - running migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload


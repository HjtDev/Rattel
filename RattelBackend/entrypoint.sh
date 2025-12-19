#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

if [ "$RUN_TESTS" = "1" ]; then
  echo "Running tests..."
  pytest -v
fi

echo "Starting Django server..."
exec python manage.py runserver 0.0.0.0:8000

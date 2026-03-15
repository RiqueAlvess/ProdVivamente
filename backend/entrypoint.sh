#!/bin/sh
set -e

echo "Running database migrations..."
python manage.py migrate_schemas --shared
python manage.py migrate_schemas

echo "Starting server..."
exec "$@"

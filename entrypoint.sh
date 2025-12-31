#!/bin/bash

# Exit on error
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser if none exists..."
python manage.py create_superuser_if_none

echo "Starting Daphne server..."
exec daphne -b 0.0.0.0 -p 8000 cardsnchaos.asgi:application

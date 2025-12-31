#!/bin/bash

echo "======================================"
echo "Starting Django application..."
echo "======================================"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "WARNING: DATABASE_URL not set, using SQLite"
else
    echo "Using PostgreSQL database"
    echo "Testing database connection..."
    if ! python manage.py check --database default 2>&1 | head -20; then
        echo "WARNING: Database check showed issues, but continuing..."
    fi
fi

echo ""
echo "Running database migrations..."
if ! python manage.py migrate --noinput; then
    echo "ERROR: Database migrations failed!"
    exit 1
fi

echo ""
echo "Collecting static files..."
if ! python manage.py collectstatic --noinput; then
    echo "ERROR: Collecting static files failed!"
    exit 1
fi

echo ""
echo "Creating superuser if none exists..."
if ! python manage.py create_superuser_if_none; then
    echo "ERROR: Superuser creation failed!"
    exit 1
fi

echo ""
echo "======================================"
echo "Starting Daphne server on 0.0.0.0:8000..."
echo "======================================"
exec daphne -b 0.0.0.0 -p 8000 cardsnchaos.asgi:application

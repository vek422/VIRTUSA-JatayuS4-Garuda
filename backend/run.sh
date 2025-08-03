#!/bin/bash

echo "Waiting for PostgreSQL to be available..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL is available!"


echo "Creating enum types..."
python3 create_enums.py


echo "Running database migrations..."
alembic stamp head --purge || true
alembic upgrade head


echo "Starting supervisor daemon..."
/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

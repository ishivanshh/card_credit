#!/usr/bin/env bash
set -e

if [ "$DATABASE_WAIT" != "false" ]; then
  echo "Waiting a few seconds for DB and redis..."
  sleep 5
fi

python manage.py migrate --noinput

if [[ "$1" == "manage" ]]; then
  shift
  exec python manage.py "$@"
fi

exec "$@"

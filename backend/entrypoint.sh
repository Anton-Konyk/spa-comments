#!/bin/sh
set -e

# ---- wait MySQL only when used ----
if [ "${DB_ENGINE:-sqlite}" = "mysql" ] && [ -n "${DB_HOST:-}" ]; then
  DB_PORT="${DB_PORT:-3306}"
  echo "Waiting for MySQL at $DB_HOST:$DB_PORT..."
  until nc -z "$DB_HOST" "$DB_PORT"; do
    echo "Waiting for MySQL at $DB_HOST:$DB_PORT..."
    sleep 1
  done
fi

# ---- wait Redis only if REDIS_URL set ----
#if [ -n "$REDIS_URL" ]; then
#  REDIS_HOST=$(echo "$REDIS_URL" | sed -E 's#redis://([^:/]+).*#\1#')
#  REDIS_PORT=$(echo "$REDIS_URL" | sed -E 's#redis://[^:/]+:([0-9]+).*#\1#')
#  REDIS_HOST=${REDIS_HOST:-redis}
#  REDIS_PORT=${REDIS_PORT:-6379}
#  echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
#  until nc -z "$REDIS_HOST" "$REDIS_PORT"; do
#    echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
#    sleep 1
#  done
#fi
if [ -n "$REDIS_URL" ]; then
  URL_NO_SCHEME="${REDIS_URL#*://}"
  HOSTPORT="${URL_NO_SCHEME#*@}"
  if [ "$HOSTPORT" = "$URL_NO_SCHEME" ]; then
    HOSTPORT="$URL_NO_SCHEME"
  fi
  HOSTPORT="${HOSTPORT%%/*}"
  REDIS_HOST="${HOSTPORT%%:*}"
  REDIS_PORT="${HOSTPORT##*:}"
  [ "$REDIS_PORT" = "$REDIS_HOST" ] && REDIS_PORT=6379

  echo "Waiting for Redis at ${REDIS_HOST}:${REDIS_PORT}..."
  until nc -z "$REDIS_HOST" "$REDIS_PORT"; do
    echo "Waiting for Redis at ${REDIS_HOST}:${REDIS_PORT}..."
    sleep 1
  done
fi

# ---- collectstatic (prod-only, opt-in) ----
if [ "${RUN_COLLECTSTATIC:-0}" = "1" ] && [ "${DEBUG}" != "True" ]; then
  echo "Running collectstatic..."
  python manage.py collectstatic --noinput
fi

python manage.py migrate --noinput

# create Superuser
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
  python manage.py createsuperuser --noinput || true
fi

# run Daphne (ASGI)
exec daphne -b 0.0.0.0 -p ${PORT:-8000} spa_comments.asgi:application
